"""OpenCity (data.opencity.in) CKAN-based land data ingestor.

Ingests structured land, zoning, and property datasets from the OpenCity
open data portal using its CKAN API. Supports CSV, KML, and KMZ formats.
PDF datasets should be handled via the GeminiWebIngestor.

Usage:
    ingestor = OpenCityIngestor(session)
    results = ingestor.run_manifest("seed_data/opencity_manifest.json")
    results = ingestor.run_job({"dataset_id": "bbmp-property-tax-collections", ...})
    results = ingestor.discover_and_ingest()
"""
from __future__ import annotations

import csv
import io
import json
import logging
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from brain.data_bank.ingestion.base import IngestResult
from brain.data_bank.ingestion.csv_ingestor import CSVIngestor
from brain.data_bank.models import Location

logger = logging.getLogger(__name__)

CKAN_BASE = "https://data.opencity.in/api/3/action"
FORMAT_PRIORITY = ["CSV", "JSON", "GEOJSON", "KML", "KMZ", "PDF"]

# Keywords used for auto-discovery
DISCOVERY_KEYWORDS = [
    "land use",
    "property tax",
    "masterplan",
    "master plan",
    "zoning",
    "land records",
    "guidance value",
    "occupancy certificate",
]

# Infer record_type from dataset title keywords (first match wins)
_RECORD_TYPE_HINTS: list[tuple[str, str]] = [
    ("property tax", "price"),
    ("guidance value", "price"),
    ("price", "price"),
    ("census", "census"),
    ("population", "census"),
    ("land use", "zoning"),
    ("masterplan", "zoning"),
    ("master plan", "zoning"),
    ("zoning", "zoning"),
    ("occupancy certificate", "zoning"),
    ("development plan", "zoning"),
]

# Infer city from dataset title (first match wins)
_CITY_HINTS: list[tuple[str, str, str]] = [
    ("bengaluru", "Bangalore", "Karnataka"),
    ("bangalore", "Bangalore", "Karnataka"),
    ("bbmp", "Bangalore", "Karnataka"),
    ("bda", "Bangalore", "Karnataka"),
    ("karnataka", "Bangalore", "Karnataka"),
    ("chennai", "Chennai", "Tamil Nadu"),
    ("tamil nadu", "Chennai", "Tamil Nadu"),
    ("cmda", "Chennai", "Tamil Nadu"),
    ("hyderabad", "Hyderabad", "Telangana"),
    ("hmda", "Hyderabad", "Telangana"),
    ("telangana", "Hyderabad", "Telangana"),
    ("pune", "Pune", "Maharashtra"),
    ("pmrda", "Pune", "Maharashtra"),
    ("mumbai", "Mumbai", "Maharashtra"),
    ("maharashtra", "Mumbai", "Maharashtra"),
    ("delhi", "Delhi", "Delhi"),
    ("dda", "Delhi", "Delhi"),
    ("kolkata", "Kolkata", "West Bengal"),
    ("ahmedabad", "Ahmedabad", "Gujarat"),
    ("surat", "Surat", "Gujarat"),
    ("gujarat", "Ahmedabad", "Gujarat"),
    ("chittoor", "Chittoor", "Andhra Pradesh"),
    ("andhra", "Hyderabad", "Andhra Pradesh"),
]


class OpenCityClient:
    """Thin wrapper around the data.opencity.in CKAN API."""

    def __init__(self, base_url: str = CKAN_BASE):
        self.base_url = base_url

    def _get(self, endpoint: str, params: dict) -> dict:
        query = urllib.parse.urlencode(params)
        url = f"{self.base_url}/{endpoint}?{query}"
        req = urllib.request.Request(url, headers={"User-Agent": "BuiltAtticBrain/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            logger.error("CKAN HTTP %s for %s", e.code, url)
            return {}
        except Exception as e:
            logger.error("CKAN API error for %s: %s", url, e)
            return {}

    def package_show(self, dataset_id: str) -> dict:
        """Return package metadata including resources list."""
        data = self._get("package_show", {"id": dataset_id})
        return data.get("result", {})

    def package_search(self, query: str, rows: int = 100) -> list[dict]:
        """Search datasets; returns list of package dicts."""
        data = self._get("package_search", {"q": query, "rows": rows})
        return data.get("result", {}).get("results", [])

    def best_resource(self, dataset_id: str, preferred_format: str = "CSV") -> tuple[str, str] | None:
        """Return (download_url, format) for the best resource in a dataset.

        Tries the preferred_format first, then falls back to FORMAT_PRIORITY order.
        Returns None if no downloadable resource is found.
        """
        pkg = self.package_show(dataset_id)
        resources = pkg.get("resources", [])
        if not resources:
            return None

        # Build format → first resource mapping
        fmt_map: dict[str, dict] = {}
        for res in resources:
            fmt = (res.get("format") or "").upper().strip()
            if fmt and fmt not in fmt_map:
                fmt_map[fmt] = res

        for fmt in [preferred_format.upper()] + FORMAT_PRIORITY:
            if fmt in fmt_map:
                res = fmt_map[fmt]
                url = res.get("url") or res.get("download_url") or ""
                if url:
                    return url, fmt
        return None


def _fetch_bytes(url: str, timeout: int = 60) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "BuiltAtticBrain/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def _apply_column_map(record: dict, column_map: dict) -> dict:
    """Rename keys in record according to column_map, keeping unmapped keys as-is."""
    return {column_map.get(k, k): v for k, v in record.items()}


def _apply_defaults(record: dict, defaults: dict) -> dict:
    """Fill in defaults for missing or empty fields (does not overwrite existing values)."""
    for k, v in defaults.items():
        if k not in record or record[k] is None or record[k] == "":
            record[k] = v
    return record


def parse_csv_bytes(data: bytes, column_map: dict, defaults: dict, source_url: str) -> list[dict]:
    """Parse CSV bytes into a list of raw record dicts."""
    text = data.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for i, row in enumerate(reader, start=2):
        rec = _apply_column_map(dict(row), column_map)
        _apply_defaults(rec, defaults)
        rec["__source_path"] = source_url
        rec["__row_number"] = i
        rows.append(rec)
    return rows


_KML_NS = "http://www.opengis.net/kml/2.2"


def parse_kml_bytes(data: bytes, column_map: dict, defaults: dict, source_url: str) -> list[dict]:
    """Parse KML/KMZ bytes into a list of raw record dicts.

    Each Placemark becomes one record. SimpleData attributes become fields.
    """
    content = data
    if data[:2] == b"PK":  # ZIP/KMZ magic bytes
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                kml_files = [n for n in zf.namelist() if n.lower().endswith(".kml")]
                if not kml_files:
                    logger.warning("No .kml file found in KMZ from %s", source_url)
                    return []
                content = zf.read(kml_files[0])
        except zipfile.BadZipFile as e:
            logger.error("Bad KMZ archive from %s: %s", source_url, e)
            return []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        logger.error("KML parse error from %s: %s", source_url, e)
        return []

    # Detect namespace
    ns_prefix = f"{{{_KML_NS}}}" if root.tag.startswith("{") else ""

    rows = []
    for i, placemark in enumerate(root.iter(f"{ns_prefix}Placemark"), start=1):
        rec: dict = {}

        name_el = placemark.find(f"{ns_prefix}name")
        if name_el is not None and name_el.text:
            rec["name"] = name_el.text.strip()

        # Extract SimpleData attributes from ExtendedData
        for sd in placemark.iter(f"{ns_prefix}SimpleData"):
            attr_name = sd.get("name", "")
            if attr_name:
                rec[attr_name] = (sd.text or "").strip()

        rec = _apply_column_map(rec, column_map)
        _apply_defaults(rec, defaults)
        rec["__source_path"] = source_url
        rec["__row_number"] = i
        rows.append(rec)

    logger.info("Parsed %d Placemarks from KML/KMZ: %s", len(rows), source_url)
    return rows


class OpenCityIngestor:
    """Ingests land and property datasets from data.opencity.in.

    Orchestrates download → parse → normalize → load for each job in a manifest.
    Reuses CSVIngestor's transform/load pipeline for model creation and provenance.

    Architecture mirrors GeminiWebIngestor: not a BaseIngestor subclass, but an
    orchestrator that delegates transform+load to CSVIngestor.
    """

    PIPELINE_NAME = "opencity_ingestor"
    DATASET_VERSION = "opencity_v1"

    def __init__(self, session: Session):
        self.session = session
        self.client = OpenCityClient()

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def run_manifest(self, manifest_path: str) -> dict[str, IngestResult]:
        """Run all jobs defined in a manifest JSON file."""
        path = Path(manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)

        results: dict[str, IngestResult] = {}
        for job in manifest.get("jobs", []):
            dataset_id = job.get("dataset_id", "unknown")
            logger.info("OpenCity: processing job '%s'", dataset_id)
            try:
                results[dataset_id] = self.run_job(job)
            except Exception as e:
                logger.error("OpenCity job '%s' failed: %s", dataset_id, e)
                results[dataset_id] = IngestResult(source=dataset_id, errors=[str(e)])
        return results

    def run_job(self, job: dict) -> IngestResult:
        """Download and ingest a single OpenCity dataset job."""
        dataset_id = job.get("dataset_id", "")
        record_type = job.get("record_type", "zoning")
        preferred_format = job.get("preferred_format", "CSV")
        column_map: dict = job.get("column_map", {})
        defaults: dict = dict(job.get("defaults", {}))
        city: str = job.get("city") or defaults.get("city", "")
        state: str = job.get("state") or defaults.get("state", "")

        # Ensure location_name is present in defaults so location FK resolves
        if city and "location_name" not in defaults:
            defaults["location_name"] = city
        if city:
            defaults["city"] = city
        if state:
            defaults["state"] = state

        result = IngestResult(source=dataset_id)

        resource = self.client.best_resource(dataset_id, preferred_format)
        if not resource:
            msg = f"No downloadable resource found for dataset '{dataset_id}'"
            logger.warning(msg)
            result.errors.append(msg)
            return result

        url, fmt = resource
        logger.info("Downloading %s (%s) from %s", dataset_id, fmt, url)

        try:
            data = _fetch_bytes(url)
        except Exception as e:
            msg = f"Download failed for {dataset_id}: {e}"
            logger.error(msg)
            result.errors.append(msg)
            return result

        if fmt == "CSV":
            raw_records = parse_csv_bytes(data, column_map, defaults, url)
        elif fmt in ("KML", "KMZ"):
            raw_records = parse_kml_bytes(data, column_map, defaults, url)
        else:
            msg = f"Unsupported format '{fmt}' for dataset '{dataset_id}' — use GeminiWebIngestor for PDFs"
            logger.warning(msg)
            result.errors.append(msg)
            return result

        result.records_read = len(raw_records)
        if not raw_records:
            logger.warning("No records extracted from %s", dataset_id)
            return result

        location_map = self._ensure_location(city, state)

        ingestor = CSVIngestor(
            self.session,
            record_type,
            location_map=location_map,
            dataset_version_default=self.DATASET_VERSION,
            pipeline_name=self.PIPELINE_NAME,
        )
        models = ingestor.transform(raw_records)
        result.records_skipped = result.records_read - len(models)
        result.records_stored = ingestor.load(models)
        self.session.commit()

        logger.info(
            "OpenCity job '%s': read=%d stored=%d skipped=%d",
            dataset_id, result.records_read, result.records_stored, result.records_skipped,
        )
        return result

    def discover_and_ingest(self, keywords: list[str] | None = None) -> dict[str, IngestResult]:
        """Auto-discover actionable datasets via CKAN and ingest them.

        Searches for datasets matching each keyword, filters to those with
        CSV/KML/KMZ resources, infers record_type and city, then ingests.
        Records with unmapped columns will fail validation and be skipped —
        use run_manifest() with explicit column_map for precise control.
        """
        search_terms = keywords or DISCOVERY_KEYWORDS
        seen_ids: set[str] = set()
        jobs: list[dict] = []

        for term in search_terms:
            for ds in self.client.package_search(term):
                ds_id = ds.get("name") or ds.get("id")
                if not ds_id or ds_id in seen_ids:
                    continue
                seen_ids.add(ds_id)

                # Only process datasets with actionable formats
                resources = ds.get("resources", [])
                formats = {(r.get("format") or "").upper() for r in resources}
                actionable = formats & {"CSV", "KML", "KMZ", "GEOJSON", "JSON"}
                if not actionable:
                    continue

                title = (ds.get("title") or ds.get("name") or "").lower()

                record_type = "zoning"
                for hint, rtype in _RECORD_TYPE_HINTS:
                    if hint in title:
                        record_type = rtype
                        break

                city, state = "", ""
                for hint, city_val, state_val in _CITY_HINTS:
                    if hint in title:
                        city, state = city_val, state_val
                        break

                preferred = next(
                    (f for f in ["CSV", "KML", "KMZ"] if f in actionable), "CSV"
                )
                jobs.append({
                    "dataset_id": ds_id,
                    "record_type": record_type,
                    "preferred_format": preferred,
                    "city": city,
                    "state": state,
                    "column_map": {},
                    "defaults": {
                        "source": f"OpenCity/{ds_id}",
                        "city": city,
                        "state": state,
                    },
                })

        logger.info("OpenCity discover: found %d actionable datasets", len(jobs))

        results: dict[str, IngestResult] = {}
        for job in jobs:
            ds_id = job["dataset_id"]
            try:
                results[ds_id] = self.run_job(job)
            except Exception as e:
                logger.error("Auto-ingest failed for '%s': %s", ds_id, e)
                results[ds_id] = IngestResult(source=ds_id, errors=[str(e)])
        return results

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_location(self, city: str, state: str) -> dict[str, int]:
        """Return a location_map for the given city.

        If no location exists for the city, a stub Location is created so that
        downstream FK constraints can be satisfied. Stubs can be enriched later
        via the standard seed pipeline.

        Returns dict mapping location name strings → location IDs.
        """
        if not city:
            # No city context — return all existing locations so manual column maps work
            locs = self.session.scalars(select(Location)).all()
            return {loc.name: loc.id for loc in locs}

        loc = self.session.scalar(
            select(Location).where(Location.city == city).limit(1)
        )
        if not loc:
            loc = Location()
            loc.name = city
            loc.city = city
            loc.state = state or None
            loc.country_code = "IN"
            self.session.add(loc)
            self.session.flush()
            logger.info("Created stub location: %s, %s (id=%d)", city, state, loc.id)

        # Map both the city name and the location's stored name so either works
        location_map = {loc.name: loc.id}
        if city != loc.name:
            location_map[city] = loc.id
        return location_map
