"""Data normalization and validation utilities."""
from __future__ import annotations

import json
import logging

logger = logging.getLogger(__name__)

VALID_ZONE_TYPES = {"residential", "commercial", "mixed", "industrial", "agricultural", "public"}
VALID_INFRA_TYPES = {"metro_station", "hospital", "school", "highway", "airport", "economic_zone", "tech_park", "railway_station"}
VALID_PROPERTY_TYPES = {"apartment", "villa", "plot", "commercial", "office"}
VALID_STANDARD_TYPES = {"architectural_standard", "construction_guideline", "bylaw"}
VALID_TERRAIN_CLASSES = {"flat", "gentle", "undulating", "steep"}


def _normalize_tags(value, *, default_tag: str) -> list[str]:
    if value is None:
        return [default_tag]
    if isinstance(value, list):
        items = value
    else:
        items = str(value).replace("|", ",").split(",")
    tags = [str(item).strip().lower() for item in items if str(item).strip()]
    return tags or [default_tag]


def normalize_record(record: dict, record_type: str) -> dict:
    cleaned = {}
    for key, value in record.items():
        if isinstance(value, str):
            value = value.strip()
        if value == "":
            value = None
        cleaned[key.strip().lower()] = value

    if record_type == "location":
        _normalize_location(cleaned)
    elif record_type == "zoning":
        _normalize_zoning(cleaned)
    elif record_type == "price":
        _normalize_price(cleaned)
    elif record_type == "infrastructure":
        _normalize_infrastructure(cleaned)
    elif record_type == "census":
        _normalize_census(cleaned)
    elif record_type == "gis":
        _normalize_gis(cleaned)
    elif record_type == "standard":
        _normalize_standard(cleaned)

    return cleaned


def _normalize_location(rec: dict):
    if rec.get("pin_code"):
        rec["pin_code"] = str(rec["pin_code"]).strip()
    for field in ("lat", "lng"):
        if rec.get(field) is not None:
            rec[field] = float(rec[field])


def _normalize_zoning(rec: dict):
    if rec.get("zoning_type"):
        rec["zoning_type"] = rec["zoning_type"].lower().strip()
    for field in ("fsi", "ground_coverage_pct", "max_height_m", "setback_front_m", "setback_side_m"):
        if rec.get(field) is not None:
            rec[field] = float(rec[field])
    rec["tags"] = _normalize_tags(rec.get("tags"), default_tag="masterplan")


def _normalize_price(rec: dict):
    if rec.get("price_per_sqft") is not None:
        rec["price_per_sqft"] = float(rec["price_per_sqft"])
    if rec.get("property_type"):
        rec["property_type"] = rec["property_type"].lower().strip()
    rec["tags"] = _normalize_tags(rec.get("tags"), default_tag="pricing")


def _normalize_infrastructure(rec: dict):
    if rec.get("infra_type"):
        rec["infra_type"] = rec["infra_type"].lower().strip()
    if rec.get("status"):
        rec["status"] = rec["status"].lower().strip()
    for field in ("lat", "lng"):
        if rec.get(field) is not None:
            rec[field] = float(rec[field])
    rec["tags"] = _normalize_tags(rec.get("tags"), default_tag="infrastructure")


def _normalize_census(rec: dict):
    for field in ("population", "households", "year"):
        if rec.get(field) is not None:
            rec[field] = int(rec[field])
    for field in ("density_per_sqkm", "growth_rate_pct"):
        if rec.get(field) is not None:
            rec[field] = float(rec[field])
    rec["tags"] = _normalize_tags(rec.get("tags"), default_tag="census")


def _normalize_gis(rec: dict):
    if rec.get("terrain_class"):
        rec["terrain_class"] = rec["terrain_class"].lower().strip()
    for field in (
        "terrain_slope_pct",
        "flood_risk_score",
        "heat_risk_score",
        "climate_risk_score",
        "road_proximity_km",
        "transit_proximity_km",
    ):
        if rec.get(field) is not None:
            rec[field] = float(rec[field])
    rec["tags"] = _normalize_tags(rec.get("tags"), default_tag="gis")


def _normalize_standard(rec: dict):
    if rec.get("standard_type"):
        rec["standard_type"] = rec["standard_type"].lower().strip()
    if rec.get("country_code"):
        rec["country_code"] = rec["country_code"].upper().strip()
    if isinstance(rec.get("rules"), str):
        rec["rules"] = json.loads(rec["rules"])
    rec["tags"] = _normalize_tags(rec.get("tags"), default_tag="standard")


def validate_record(record: dict, record_type: str) -> list[str]:
    errors = []

    if record_type == "location":
        if not record.get("name"):
            errors.append("Missing location name")
        lat = record.get("lat")
        lng = record.get("lng")
        if lat is not None and not (-90 <= lat <= 90):
            errors.append(f"Invalid latitude: {lat}")
        if lng is not None and not (-180 <= lng <= 180):
            errors.append(f"Invalid longitude: {lng}")

    elif record_type == "zoning":
        if not record.get("location_name"):
            errors.append("Missing location_name")
        if record.get("zoning_type") and record["zoning_type"] not in VALID_ZONE_TYPES:
            errors.append(f"Unsupported zoning_type: {record['zoning_type']}")
        fsi = record.get("fsi")
        if fsi is not None and fsi <= 0:
            errors.append(f"Invalid FSI: {fsi}")

    elif record_type == "price":
        if not record.get("location_name"):
            errors.append("Missing location_name")
        price = record.get("price_per_sqft")
        if price is not None and price <= 0:
            errors.append(f"Invalid price: {price}")
        if record.get("property_type") and record["property_type"] not in VALID_PROPERTY_TYPES:
            errors.append(f"Unsupported property_type: {record['property_type']}")
        if not record.get("recorded_date"):
            errors.append("Missing recorded_date")

    elif record_type == "infrastructure":
        if not record.get("name"):
            errors.append("Missing infrastructure name")
        if record.get("infra_type") and record["infra_type"] not in VALID_INFRA_TYPES:
            errors.append(f"Unsupported infra_type: {record['infra_type']}")
        lat = record.get("lat")
        lng = record.get("lng")
        if lat is not None and not (-90 <= lat <= 90):
            errors.append(f"Invalid latitude: {lat}")
        if lng is not None and not (-180 <= lng <= 180):
            errors.append(f"Invalid longitude: {lng}")

    elif record_type == "census":
        if not record.get("location_name"):
            errors.append("Missing location_name")
        pop = record.get("population")
        if pop is not None and pop < 0:
            errors.append(f"Invalid population: {pop}")

    elif record_type == "gis":
        if not record.get("location_name"):
            errors.append("Missing location_name")
        terrain_class = record.get("terrain_class")
        if terrain_class and terrain_class not in VALID_TERRAIN_CLASSES:
            errors.append(f"Unsupported terrain_class: {terrain_class}")
        for field in ("flood_risk_score", "heat_risk_score", "climate_risk_score"):
            value = record.get(field)
            if value is not None and not (0 <= value <= 100):
                errors.append(f"{field} must be between 0 and 100")

    elif record_type == "standard":
        if not record.get("standard_type"):
            errors.append("Missing standard_type")
        elif record["standard_type"] not in VALID_STANDARD_TYPES:
            errors.append(f"Unsupported standard_type: {record['standard_type']}")
        if not record.get("code"):
            errors.append("Missing code")
        if not record.get("title"):
            errors.append("Missing title")

    return errors
