"""CSV-based data ingestor — handles structured intelligence datasets."""
from __future__ import annotations

import csv
import logging
from datetime import date
from pathlib import Path

from geoalchemy2 import WKTElement
from sqlalchemy import select
from sqlalchemy.orm import Session

from brain.data_bank.ingestion.base import BaseIngestor, IngestResult
from brain.data_bank.ingestion.normalizer import normalize_record, validate_record
from brain.data_bank.ingestion.provenance import assign_raw_data, build_provenance_payload
from brain.data_bank.models import (
    CensusData,
    Infrastructure,
    Location,
    LocationGeoProfile,
    Masterplan,
    PropertyPrice,
    RegionalStandard,
)

logger = logging.getLogger(__name__)


def _point(lat: float, lng: float) -> WKTElement:
    return WKTElement(f"POINT({lng} {lat})", srid=4326)


def _parse_date(value):
    return date.fromisoformat(value) if value else None


class CSVIngestor(BaseIngestor):
    """Ingest data from CSV files with normalize → validate → tag → store pipeline."""

    def __init__(
        self,
        session: Session,
        record_type: str,
        location_map: dict[str, int] | None = None,
        *,
        dataset_version_default: str = "ingest_v1",
        pipeline_name: str = "csv_ingestor",
    ):
        super().__init__(session)
        self.record_type = record_type
        self.location_map = location_map or {}
        self.dataset_version_default = dataset_version_default
        self.pipeline_name = pipeline_name

    def extract(self, source_path: str) -> list[dict]:
        path = Path(source_path)
        if not path.exists():
            logger.error("File not found: %s", source_path)
            return []
        with open(path, newline="", encoding="utf-8") as f:
            rows = []
            for row_number, row in enumerate(csv.DictReader(f), start=2):
                rows.append({
                    **row,
                    "__source_path": str(path),
                    "__row_number": row_number,
                })
            return rows

    def transform(self, raw_records: list[dict]) -> list:
        models = []
        seen_models: dict[tuple, object] = {}
        appended: set[int] = set()
        for raw in raw_records:
            source_path = raw.get("__source_path") or ""
            row_number = raw.get("__row_number")
            rec = normalize_record(raw, self.record_type)
            errors = validate_record(rec, self.record_type)
            if errors:
                logger.warning("Skipping invalid record: %s — %s", rec, errors)
                continue
            identity_key = self._identity_key(rec)
            existing_model = seen_models.get(identity_key)
            if existing_model is None:
                existing_model = self._find_existing(rec)
            model = self._to_model(
                rec,
                raw_record=raw,
                source_path=source_path,
                row_number=int(row_number) if row_number is not None else None,
                existing_model=existing_model,
            )
            if model is not None:
                if identity_key is not None:
                    seen_models[identity_key] = model
                if id(model) not in appended:
                    appended.add(id(model))
                    models.append(model)
        return models

    def _eq_filter(self, column, value):
        return column.is_(None) if value is None else column == value

    def _location_id_for_record(self, rec: dict) -> int | None:
        return self.location_map.get(rec.get("location_name"))

    def _identity_key(self, rec: dict) -> tuple | None:
        if self.record_type == "location":
            return (
                "location",
                rec.get("name"),
                rec.get("city") or "Unknown",
                rec.get("state"),
                rec.get("pin_code"),
            )
        if self.record_type == "zoning":
            return (
                "zoning",
                self._location_id_for_record(rec),
                rec.get("version", "BDA_RMP_2031"),
                rec.get("dataset_version", self.dataset_version_default),
                rec.get("effective_from"),
            )
        if self.record_type == "price":
            return (
                "price",
                self._location_id_for_record(rec),
                rec.get("property_type"),
                rec.get("recorded_date"),
                rec.get("source"),
            )
        if self.record_type == "infrastructure":
            return (
                "infrastructure",
                rec.get("name"),
                rec.get("infra_type"),
                rec.get("city") or "Unknown",
                rec.get("state"),
            )
        if self.record_type == "census":
            return (
                "census",
                self._location_id_for_record(rec),
                rec.get("year"),
                rec.get("source"),
            )
        if self.record_type == "gis":
            return (
                "gis",
                self._location_id_for_record(rec),
                rec.get("dataset_version", self.dataset_version_default),
                rec.get("source"),
            )
        if self.record_type == "standard":
            return (
                "standard",
                rec.get("country_code", "IN"),
                rec.get("admin_area"),
                rec.get("standard_type"),
                rec.get("code"),
                rec.get("version_tag", "v1"),
            )
        return None

    def _find_existing(self, rec: dict):
        if self.record_type == "location":
            return self.session.scalar(
                select(Location).where(
                    Location.name == rec["name"],
                    Location.city == (rec.get("city") or "Unknown"),
                    self._eq_filter(Location.state, rec.get("state")),
                    self._eq_filter(Location.pin_code, rec.get("pin_code")),
                )
            )
        if self.record_type == "zoning":
            loc_id = self._location_id_for_record(rec)
            if not loc_id:
                return None
            return self.session.scalar(
                select(Masterplan).where(
                    Masterplan.location_id == loc_id,
                    Masterplan.version == rec.get("version", "BDA_RMP_2031"),
                    Masterplan.dataset_version == rec.get("dataset_version", self.dataset_version_default),
                    self._eq_filter(Masterplan.effective_from, _parse_date(rec.get("effective_from"))),
                )
            )
        if self.record_type == "price":
            loc_id = self._location_id_for_record(rec)
            if not loc_id:
                return None
            return self.session.scalar(
                select(PropertyPrice).where(
                    PropertyPrice.location_id == loc_id,
                    self._eq_filter(PropertyPrice.property_type, rec.get("property_type")),
                    PropertyPrice.recorded_date == date.fromisoformat(rec["recorded_date"]),
                    self._eq_filter(PropertyPrice.source, rec.get("source")),
                )
            )
        if self.record_type == "infrastructure":
            return self.session.scalar(
                select(Infrastructure).where(
                    Infrastructure.name == rec["name"],
                    self._eq_filter(Infrastructure.infra_type, rec.get("infra_type")),
                    Infrastructure.city == (rec.get("city") or "Unknown"),
                    self._eq_filter(Infrastructure.state, rec.get("state")),
                )
            )
        if self.record_type == "census":
            loc_id = self._location_id_for_record(rec)
            if not loc_id:
                return None
            return self.session.scalar(
                select(CensusData).where(
                    CensusData.location_id == loc_id,
                    CensusData.year == rec.get("year"),
                    self._eq_filter(CensusData.source, rec.get("source")),
                )
            )
        if self.record_type == "gis":
            loc_id = self._location_id_for_record(rec)
            if not loc_id:
                return None
            return self.session.scalar(
                select(LocationGeoProfile).where(
                    LocationGeoProfile.location_id == loc_id,
                    LocationGeoProfile.dataset_version == rec.get("dataset_version", self.dataset_version_default),
                    self._eq_filter(LocationGeoProfile.source, rec.get("source")),
                )
            )
        if self.record_type == "standard":
            return self.session.scalar(
                select(RegionalStandard).where(
                    RegionalStandard.standard_type == rec["standard_type"],
                    RegionalStandard.country_code == rec.get("country_code", "IN"),
                    self._eq_filter(RegionalStandard.admin_area, rec.get("admin_area")),
                    RegionalStandard.code == rec["code"],
                    RegionalStandard.version_tag == rec.get("version_tag", "v1"),
                )
            )
        return None

    def _apply_provenance(self, model, rec: dict, raw_record: dict, source_path: str, row_number: int | None):
        provenance = build_provenance_payload(
            record_type=self.record_type,
            raw_record=raw_record,
            source_path=source_path,
            row_number=row_number,
            normalized_record=rec,
            dataset_version=rec.get("dataset_version", self.dataset_version_default),
            pipeline=self.pipeline_name,
        )
        assign_raw_data(model, provenance)
        return model

    def _to_model(self, rec: dict, *, raw_record: dict, source_path: str, row_number: int | None, existing_model=None):
        if self.record_type == "location":
            return self._to_location(rec, raw_record=raw_record, source_path=source_path, row_number=row_number, existing_model=existing_model)
        if self.record_type == "zoning":
            return self._to_masterplan(rec, raw_record=raw_record, source_path=source_path, row_number=row_number, existing_model=existing_model)
        if self.record_type == "price":
            return self._to_price(rec, raw_record=raw_record, source_path=source_path, row_number=row_number, existing_model=existing_model)
        if self.record_type == "infrastructure":
            return self._to_infrastructure(rec, raw_record=raw_record, source_path=source_path, row_number=row_number, existing_model=existing_model)
        if self.record_type == "census":
            return self._to_census(rec, raw_record=raw_record, source_path=source_path, row_number=row_number, existing_model=existing_model)
        if self.record_type == "gis":
            return self._to_geo_profile(rec, raw_record=raw_record, source_path=source_path, row_number=row_number, existing_model=existing_model)
        if self.record_type == "standard":
            return self._to_standard(rec, raw_record=raw_record, source_path=source_path, row_number=row_number, existing_model=existing_model)
        return None

    def _to_location(self, rec: dict, *, raw_record: dict, source_path: str, row_number: int | None, existing_model=None) -> Location:
        loc = existing_model or Location()
        loc.name = rec["name"]
        loc.country_code = (rec.get("country_code") or "IN").upper()
        loc.state = rec.get("state")
        loc.city = rec.get("city") or "Unknown"
        loc.locality = rec.get("locality")
        loc.ward = rec.get("ward")
        loc.pin_code = rec.get("pin_code")
        if rec.get("lat") is not None and rec.get("lng") is not None:
            loc.geom = _point(rec["lat"], rec["lng"])
        return self._apply_provenance(loc, rec, raw_record, source_path, row_number)

    def _to_masterplan(self, rec: dict, *, raw_record: dict, source_path: str, row_number: int | None, existing_model=None) -> Masterplan | None:
        loc_id = self._location_id_for_record(rec)
        if not loc_id:
            logger.warning("Unknown location: %s", rec.get("location_name"))
            return None
        model = existing_model or Masterplan()
        model.location_id = loc_id
        model.version = rec.get("version", "BDA_RMP_2031")
        model.dataset_version = rec.get("dataset_version", self.dataset_version_default)
        model.zoning_type = rec.get("zoning_type")
        model.fsi = rec.get("fsi")
        model.ground_coverage_pct = rec.get("ground_coverage_pct")
        model.max_height_m = rec.get("max_height_m")
        model.setback_front_m = rec.get("setback_front_m")
        model.setback_side_m = rec.get("setback_side_m")
        model.effective_from = _parse_date(rec.get("effective_from"))
        model.effective_to = _parse_date(rec.get("effective_to"))
        model.approval_status = rec.get("approval_status", "active")
        model.source_url = rec.get("source_url")
        model.tags = rec.get("tags") or ["masterplan"]
        return self._apply_provenance(model, rec, raw_record, source_path, row_number)

    def _to_price(self, rec: dict, *, raw_record: dict, source_path: str, row_number: int | None, existing_model=None) -> PropertyPrice | None:
        loc_id = self._location_id_for_record(rec)
        if not loc_id:
            logger.warning("Unknown location: %s", rec.get("location_name"))
            return None
        model = existing_model or PropertyPrice()
        model.location_id = loc_id
        model.price_per_sqft = rec["price_per_sqft"]
        model.property_type = rec.get("property_type")
        model.recorded_date = date.fromisoformat(rec["recorded_date"])
        model.source = rec.get("source")
        model.tags = rec.get("tags") or ["pricing"]
        return self._apply_provenance(model, rec, raw_record, source_path, row_number)

    def _to_infrastructure(self, rec: dict, *, raw_record: dict, source_path: str, row_number: int | None, existing_model=None) -> Infrastructure:
        infra = existing_model or Infrastructure()
        infra.name = rec["name"]
        infra.infra_type = rec.get("infra_type")
        infra.country_code = (rec.get("country_code") or "IN").upper()
        infra.state = rec.get("state")
        infra.city = rec.get("city") or "Unknown"
        infra.status = rec.get("status")
        infra.source = rec.get("source")
        infra.tags = rec.get("tags") or ["infrastructure"]
        if rec.get("lat") is not None and rec.get("lng") is not None:
            infra.geom = _point(rec["lat"], rec["lng"])
        return self._apply_provenance(infra, rec, raw_record, source_path, row_number)

    def _to_census(self, rec: dict, *, raw_record: dict, source_path: str, row_number: int | None, existing_model=None) -> CensusData | None:
        loc_id = self._location_id_for_record(rec)
        if not loc_id:
            logger.warning("Unknown location: %s", rec.get("location_name"))
            return None
        model = existing_model or CensusData()
        model.location_id = loc_id
        model.year = rec.get("year")
        model.population = rec.get("population")
        model.density_per_sqkm = rec.get("density_per_sqkm")
        model.growth_rate_pct = rec.get("growth_rate_pct")
        model.households = rec.get("households")
        model.source = rec.get("source")
        model.tags = rec.get("tags") or ["census"]
        return self._apply_provenance(model, rec, raw_record, source_path, row_number)

    def _to_geo_profile(self, rec: dict, *, raw_record: dict, source_path: str, row_number: int | None, existing_model=None) -> LocationGeoProfile | None:
        loc_id = self._location_id_for_record(rec)
        if not loc_id:
            logger.warning("Unknown location: %s", rec.get("location_name"))
            return None
        model = existing_model or LocationGeoProfile()
        model.location_id = loc_id
        model.dataset_version = rec.get("dataset_version", self.dataset_version_default)
        model.terrain_class = rec.get("terrain_class")
        model.terrain_slope_pct = rec.get("terrain_slope_pct")
        model.flood_risk_score = rec.get("flood_risk_score")
        model.heat_risk_score = rec.get("heat_risk_score")
        model.climate_risk_score = rec.get("climate_risk_score")
        model.road_proximity_km = rec.get("road_proximity_km")
        model.transit_proximity_km = rec.get("transit_proximity_km")
        model.source = rec.get("source")
        model.tags = rec.get("tags") or ["gis"]
        return self._apply_provenance(model, rec, raw_record, source_path, row_number)

    def _to_standard(self, rec: dict, *, raw_record: dict, source_path: str, row_number: int | None, existing_model=None) -> RegionalStandard:
        model = existing_model or RegionalStandard()
        model.standard_type = rec["standard_type"]
        model.country_code = rec.get("country_code", "IN")
        model.admin_area = rec.get("admin_area")
        model.region_name = rec.get("region_name")
        model.code = rec["code"]
        model.title = rec["title"]
        model.version_tag = rec.get("version_tag", "v1")
        model.source_url = rec.get("source_url")
        model.tags = rec.get("tags") or ["standard"]
        model.rules = rec.get("rules") or {}
        return self._apply_provenance(model, rec, raw_record, source_path, row_number)


def ingest_directory(
    session: Session,
    data_dir: str,
    *,
    dataset_version_default: str = "ingest_v1",
    pipeline_name: str = "csv_ingestor",
) -> dict[str, IngestResult]:
    data_path = Path(data_dir)
    results = {}

    loc_file = data_path / "locations.csv"
    if loc_file.exists():
        ingestor = CSVIngestor(
            session,
            "location",
            dataset_version_default=dataset_version_default,
            pipeline_name=pipeline_name,
        )
        result = ingestor.run(str(loc_file))
        results["locations"] = result
        location_map = {loc.name: loc.id for loc in session.scalars(select(Location))}
    else:
        location_map = {loc.name: loc.id for loc in session.scalars(select(Location))}

    file_map = {
        "zoning.csv": "zoning",
        "prices.csv": "price",
        "infrastructure.csv": "infrastructure",
        "census.csv": "census",
        "gis_profiles.csv": "gis",
        "regional_standards.csv": "standard",
    }
    for filename, record_type in file_map.items():
        filepath = data_path / filename
        if filepath.exists():
            ingestor = CSVIngestor(
                session,
                record_type,
                location_map=location_map,
                dataset_version_default=dataset_version_default,
                pipeline_name=pipeline_name,
            )
            results[record_type] = ingestor.run(str(filepath))

    return results
