"""Gemini-assisted web enrichment for structured data extraction."""
from __future__ import annotations

import json
import logging
import re
import ssl
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from sqlalchemy import select
from sqlalchemy.orm import Session

from brain.ai.adapters.gemini import GeminiAdapter
from brain.data_bank.ingestion.base import IngestResult
from brain.data_bank.ingestion.csv_ingestor import CSVIngestor
from brain.data_bank.models import Location

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "BuiltAtticBrainBot/1.0 (+https://builtattic.local)"
DEFAULT_MAX_PAGE_CHARS = 24000
DEFAULT_TIMEOUT_SECONDS = 20
PLACEHOLDER_HOSTS = {
    "example.com",
    "example.org",
    "example.net",
    "example.gov",
    "localhost",
}

RECORD_FIELD_GUIDE = {
    "location": [
        "name",
        "country_code",
        "state",
        "city",
        "locality",
        "ward",
        "pin_code",
        "lat",
        "lng",
    ],
    "zoning": [
        "location_name",
        "version",
        "dataset_version",
        "zoning_type",
        "fsi",
        "ground_coverage_pct",
        "max_height_m",
        "setback_front_m",
        "setback_side_m",
        "effective_from",
        "effective_to",
        "approval_status",
        "source_url",
        "tags",
    ],
    "price": [
        "location_name",
        "price_per_sqft",
        "property_type",
        "recorded_date",
        "source",
        "tags",
    ],
    "infrastructure": [
        "name",
        "infra_type",
        "country_code",
        "state",
        "city",
        "lat",
        "lng",
        "status",
        "source",
        "tags",
    ],
    "census": [
        "location_name",
        "year",
        "population",
        "density_per_sqkm",
        "growth_rate_pct",
        "households",
        "source",
        "tags",
    ],
    "gis": [
        "location_name",
        "dataset_version",
        "terrain_class",
        "terrain_slope_pct",
        "flood_risk_score",
        "heat_risk_score",
        "climate_risk_score",
        "road_proximity_km",
        "transit_proximity_km",
        "source",
        "tags",
    ],
    "standard": [
        "standard_type",
        "country_code",
        "admin_area",
        "region_name",
        "code",
        "title",
        "version_tag",
        "source_url",
        "tags",
        "rules",
    ],
}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip_depth += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._skip_depth:
            self._skip_depth -= 1

    def handle_data(self, data):
        if self._skip_depth:
            return
        text = data.strip()
        if text:
            self._chunks.append(text)

    def get_text(self) -> str:
        return " ".join(self._chunks)


@dataclass
class GeminiEnrichmentJob:
    record_type: str
    urls: list[str]
    defaults: dict[str, Any] = field(default_factory=dict)
    context: str | None = None
    max_page_chars: int = DEFAULT_MAX_PAGE_CHARS
    timeout: int = DEFAULT_TIMEOUT_SECONDS
    verify_ssl: bool = True


def _is_placeholder_url(url: str) -> bool:
    hostname = (urlparse(url).hostname or "").lower()
    return hostname in PLACEHOLDER_HOSTS or hostname.startswith("example.")


def fetch_url_text(
    url: str,
    *,
    user_agent: str = DEFAULT_USER_AGENT,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    verify_ssl: bool = True,
) -> str:
    request = Request(url, headers={"User-Agent": user_agent})
    ssl_context = ssl.create_default_context() if verify_ssl else ssl._create_unverified_context()
    with urlopen(request, timeout=timeout, context=ssl_context) as response:
        payload = response.read()
        content_type = response.headers.get("Content-Type", "")
        charset_match = re.search(r"charset=([\\w-]+)", content_type)
        encoding = charset_match.group(1) if charset_match else "utf-8"
        html = payload.decode(encoding, errors="replace")

    parser = _HTMLTextExtractor()
    parser.feed(html)
    text = parser.get_text()
    return re.sub(r"\\s+", " ", text).strip()


def _parse_manifest(manifest_path: str) -> list[GeminiEnrichmentJob]:
    payload = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    jobs = payload.get("jobs", [])
    parsed: list[GeminiEnrichmentJob] = []
    for job in jobs:
        parsed.append(
            GeminiEnrichmentJob(
                record_type=job["record_type"],
                urls=list(job.get("urls") or []),
                defaults=job.get("defaults") or {},
                context=job.get("context"),
                max_page_chars=int(job.get("max_page_chars") or DEFAULT_MAX_PAGE_CHARS),
                timeout=int(job.get("timeout") or DEFAULT_TIMEOUT_SECONDS),
                verify_ssl=bool(job.get("verify_ssl", True)),
            )
        )
    return parsed


def _build_prompt(job: GeminiEnrichmentJob, url: str, page_text: str) -> str:
    fields = RECORD_FIELD_GUIDE[job.record_type]
    defaults = json.dumps(job.defaults, ensure_ascii=True, indent=2, default=str)
    field_block = "\\n".join(f"- {field}" for field in fields)
    context = job.context or "Extract only explicit facts supported by the source text."
    return f"""Extract structured {job.record_type} records from the page content below.

Return strict JSON with this shape:
{{
  "records": [{{ ... }}]
}}

Rules:
- Use only facts present in the source text.
- Do not invent numbers, dates, coordinates, or codes.
- If a field is unknown, omit it.
- Prefer one record per concrete location, standard, pricing observation, or infrastructure item.
- Apply these defaults to every record unless the page explicitly provides a stronger value:
{defaults}

Expected fields for {job.record_type}:
{field_block}

Source URL:
{url}

Extraction context:
{context}

Page text:
{page_text}
"""


class GeminiWebIngestor:
    def __init__(self, session: Session, *, adapter: GeminiAdapter | None = None):
        self.session = session
        self.adapter = adapter or GeminiAdapter()

    def _location_map(self) -> dict[str, int]:
        return {loc.name: loc.id for loc in self.session.scalars(select(Location))}

    def _extract_records_from_url(self, job: GeminiEnrichmentJob, url: str) -> list[dict]:
        page_text = fetch_url_text(url, timeout=job.timeout, verify_ssl=job.verify_ssl)
        page_text = page_text[: job.max_page_chars]
        payload = self.adapter.generate_json(
            _build_prompt(job, url, page_text),
            system_instruction=(
                "You extract high-precision structured real-estate intelligence from web content. "
                "Return only valid JSON."
            ),
        )
        if isinstance(payload, list):
            records = payload
        else:
            records = payload.get("records", [])

        prepared = []
        for record in records:
            merged = {
                **job.defaults,
                **(record or {}),
                "__source_path": url,
                "__row_number": None,
            }
            if "source_url" not in merged:
                merged["source_url"] = url
            prepared.append(merged)
        return prepared

    def run_job(self, job: GeminiEnrichmentJob) -> IngestResult:
        if job.record_type not in RECORD_FIELD_GUIDE:
            raise ValueError(f"Unsupported record_type: {job.record_type}")

        result = IngestResult(source="gemini_web")
        ingestor = CSVIngestor(
            self.session,
            job.record_type,
            location_map=self._location_map(),
            dataset_version_default=str(job.defaults.get("dataset_version") or "web_gemini_v1"),
            pipeline_name="gemini_web_ingestor",
        )

        raw_records: list[dict] = []
        for url in job.urls:
            if _is_placeholder_url(url):
                message = f"{url}: placeholder URL in manifest; replace it with a real official source"
                logger.warning("Gemini web extraction skipped: %s", message)
                result.errors.append(message)
                continue
            try:
                extracted = self._extract_records_from_url(job, url)
                raw_records.extend(extracted)
            except Exception as exc:
                message = f"{url}: {exc}"
                logger.warning("Gemini web extraction failed: %s", message)
                result.errors.append(message)

        result.records_read = len(raw_records)
        models = ingestor.transform(raw_records)
        result.records_skipped = result.records_read - len(models)
        result.records_stored = ingestor.load(models)
        self.session.commit()
        return result

    def run_manifest(self, manifest_path: str) -> dict[str, IngestResult]:
        results: dict[str, IngestResult] = {}
        for index, job in enumerate(_parse_manifest(manifest_path), start=1):
            key = f"{job.record_type}_{index}"
            results[key] = self.run_job(job)
        return results
