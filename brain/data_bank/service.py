from __future__ import annotations

from datetime import date
from decimal import Decimal
from statistics import mean

from geoalchemy2 import Geography, WKTElement
from sqlalchemy import cast, func, or_, select
from sqlalchemy.orm import Session

from brain.data_bank.models import (
    CensusData,
    Infrastructure,
    Location,
    LocationGeoProfile,
    Masterplan,
    PlanningContext,
    PropertyPrice,
    RegionalStandard,
)


DEFAULT_COUNTRY_CODE = "IN"
DEFAULT_PRICE_BASELINE_DATE = date(2025, 1, 1)


def _to_float(value, default: float | None = None) -> float | None:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_mean(values: list[float]) -> float:
    valid = [value for value in values if value is not None]
    return round(mean(valid), 2) if valid else 0.0


def get_location(session: Session, location_id: int) -> Location | None:
    return session.get(Location, location_id)


def get_all_locations(session: Session, city: str | None = None, state: str | None = None) -> list[Location]:
    q = select(Location)
    if state:
        q = q.where(Location.state == state)
    if city:
        q = q.where(Location.city == city)
    return list(session.scalars(q.order_by(Location.name)))


def find_nearby_locations(session: Session, lat: float, lng: float, radius_km: float) -> list[dict]:
    point = WKTElement(f"POINT({lng} {lat})", srid=4326)
    radius_m = radius_km * 1000

    q = (
        select(
            Location,
            func.ST_Distance(
                cast(Location.geom, Geography),
                cast(point, Geography),
            ).label("distance_m"),
        )
        .where(
            func.ST_DWithin(
                cast(Location.geom, Geography),
                cast(point, Geography),
                radius_m,
            )
        )
        .order_by("distance_m")
    )

    results = []
    for row in session.execute(q):
        results.append({
            "location": row[0],
            "distance_km": round(row[1] / 1000, 2),
        })
    return results


def get_masterplan(session: Session, location_id: int) -> Masterplan | None:
    return session.scalar(
        select(Masterplan)
        .where(Masterplan.location_id == location_id)
        .order_by(
            Masterplan.effective_from.desc().nullslast(),
            Masterplan.created_at.desc(),
            Masterplan.id.desc(),
        )
    )


def get_masterplan_history(session: Session, location_id: int) -> list[Masterplan]:
    return list(session.scalars(
        select(Masterplan)
        .where(Masterplan.location_id == location_id)
        .order_by(
            Masterplan.effective_from.desc().nullslast(),
            Masterplan.created_at.desc(),
            Masterplan.id.desc(),
        )
    ))


def get_price_history(session: Session, location_id: int, property_type: str | None = None) -> list[PropertyPrice]:
    q = select(PropertyPrice).where(PropertyPrice.location_id == location_id)
    if property_type:
        q = q.where(PropertyPrice.property_type == property_type)
    return list(session.scalars(q.order_by(PropertyPrice.recorded_date.desc(), PropertyPrice.id.desc())))


def get_avg_price(session: Session, location_id: int, *, since_date: date | None = DEFAULT_PRICE_BASELINE_DATE) -> Decimal | None:
    q = select(func.avg(PropertyPrice.price_per_sqft)).where(PropertyPrice.location_id == location_id)
    if since_date:
        q = q.where(PropertyPrice.recorded_date >= since_date)
    result = session.scalar(q)
    return Decimal(str(round(result, 2))) if result else None


def find_nearby_infrastructure(
    session: Session,
    lat: float,
    lng: float,
    radius_km: float,
    infra_type: str | None = None,
) -> list[dict]:
    point = WKTElement(f"POINT({lng} {lat})", srid=4326)
    radius_m = radius_km * 1000

    q = (
        select(
            Infrastructure,
            func.ST_Distance(
                cast(Infrastructure.geom, Geography),
                cast(point, Geography),
            ).label("distance_m"),
        )
        .where(
            func.ST_DWithin(
                cast(Infrastructure.geom, Geography),
                cast(point, Geography),
                radius_m,
            )
        )
        .order_by("distance_m")
    )
    if infra_type:
        q = q.where(Infrastructure.infra_type == infra_type)

    results = []
    for row in session.execute(q):
        results.append({
            "infrastructure": row[0],
            "distance_km": round(row[1] / 1000, 2),
        })
    return results


def get_census(session: Session, location_id: int) -> CensusData | None:
    return session.scalar(
        select(CensusData)
        .where(CensusData.location_id == location_id)
        .order_by(CensusData.year.desc(), CensusData.id.desc())
    )


def get_geo_profile(session: Session, location_id: int) -> LocationGeoProfile | None:
    return session.scalar(
        select(LocationGeoProfile)
        .where(LocationGeoProfile.location_id == location_id)
        .order_by(LocationGeoProfile.created_at.desc(), LocationGeoProfile.id.desc())
    )


def list_regional_standards(
    session: Session,
    *,
    country_code: str = DEFAULT_COUNTRY_CODE,
    admin_area: str | None = None,
    standard_type: str | None = None,
) -> list[RegionalStandard]:
    q = select(RegionalStandard).where(RegionalStandard.country_code == country_code)
    if admin_area:
        q = q.where((RegionalStandard.admin_area == admin_area) | (RegionalStandard.admin_area.is_(None)))
    if standard_type:
        q = q.where(RegionalStandard.standard_type == standard_type)
    return list(session.scalars(
        q.order_by(
            RegionalStandard.admin_area.desc().nullslast(),
            RegionalStandard.created_at.desc(),
            RegionalStandard.id.desc(),
        )
    ))


def get_location_regional_standards(session: Session, location: Location) -> list[RegionalStandard]:
    scopes = [location.city, location.state]
    scopes = [scope for scope in scopes if scope]

    q = select(RegionalStandard).where(RegionalStandard.country_code == (location.country_code or DEFAULT_COUNTRY_CODE))
    if scopes:
        q = q.where(
            or_(
                RegionalStandard.admin_area.is_(None),
                RegionalStandard.admin_area.in_(scopes),
            )
        )
    else:
        q = q.where(RegionalStandard.admin_area.is_(None))

    standards = list(session.scalars(
        q.order_by(
            RegionalStandard.admin_area.desc().nullslast(),
            RegionalStandard.created_at.desc(),
            RegionalStandard.id.desc(),
        )
    ))

    seen: set[int] = set()
    deduped: list[RegionalStandard] = []
    for standard in standards:
        if standard.id in seen:
            continue
        seen.add(standard.id)
        deduped.append(standard)
    return deduped


def get_location_summary(session: Session, location_id: int) -> dict | None:
    loc = get_location(session, location_id)
    if not loc:
        return None

    masterplan = get_masterplan(session, location_id)
    avg_price = get_avg_price(session, location_id)
    prices = get_price_history(session, location_id)
    census = get_census(session, location_id)
    geo_profile = get_geo_profile(session, location_id)
    regional_standards = get_location_regional_standards(session, loc)

    geom_point = session.scalar(func.ST_AsText(loc.geom))
    nearby_infra = []
    if geom_point:
        coords = geom_point.replace("POINT(", "").replace(")", "").split()
        lng, lat = float(coords[0]), float(coords[1])
        nearby_infra = find_nearby_infrastructure(session, lat, lng, radius_km=5)

    return {
        "location": loc,
        "masterplan": masterplan,
        "masterplan_history": get_masterplan_history(session, location_id),
        "avg_price_per_sqft": avg_price,
        "price_history": prices,
        "census": census,
        "geo_profile": geo_profile,
        "regional_standards": regional_standards,
        "nearby_infrastructure": nearby_infra,
    }


def get_planning_context(session: Session, location_id: int) -> PlanningContext | None:
    return session.scalar(
        select(PlanningContext)
        .where(PlanningContext.location_id == location_id)
        .order_by(PlanningContext.created_at.desc(), PlanningContext.id.desc())
    )


def derive_planning_context_payload(
    session: Session,
    location_id: int,
    *,
    version_tag: str = "derived_v1",
) -> dict:
    summary = get_location_summary(session, location_id)
    if not summary:
        raise ValueError(f"Location {location_id} not found")

    from brain.valuation import service as valuation_service

    location = summary["location"]
    masterplan = summary["masterplan"]
    geo_profile = summary["geo_profile"]
    standards = summary["regional_standards"]
    score = valuation_service.get_or_compute_score(session, location_id)

    floor_plan_constraints = {
        "zoning_type": masterplan.zoning_type if masterplan else None,
        "fsi": _to_float(masterplan.fsi) if masterplan else None,
        "max_height_m": _to_float(masterplan.max_height_m) if masterplan else None,
        "ground_coverage_pct": _to_float(masterplan.ground_coverage_pct) if masterplan else None,
        "setbacks_m": {
            "front": _to_float(masterplan.setback_front_m) if masterplan else None,
            "side": _to_float(masterplan.setback_side_m) if masterplan else None,
        },
        "terrain": {
            "class": geo_profile.terrain_class if geo_profile else None,
            "slope_pct": _to_float(geo_profile.terrain_slope_pct) if geo_profile else None,
        },
        "climate_risk_score": _to_float(geo_profile.climate_risk_score) if geo_profile else None,
    }

    zoning_validation_rules = {
        "masterplan_version": masterplan.version if masterplan else None,
        "dataset_version": masterplan.dataset_version if masterplan else None,
        "approval_status": masterplan.approval_status if masterplan else None,
        "effective_from": masterplan.effective_from.isoformat() if masterplan and masterplan.effective_from else None,
        "effective_to": masterplan.effective_to.isoformat() if masterplan and masterplan.effective_to else None,
        "regional_standard_codes": [standard.code for standard in standards],
    }

    massing_inputs = {
        "max_height_m": _to_float(masterplan.max_height_m) if masterplan else None,
        "fsi": _to_float(masterplan.fsi) if masterplan else None,
        "coverage_pct": _to_float(masterplan.ground_coverage_pct) if masterplan else None,
        "terrain_slope_pct": _to_float(geo_profile.terrain_slope_pct) if geo_profile else None,
        "flood_risk_score": _to_float(geo_profile.flood_risk_score) if geo_profile else None,
        "heat_risk_score": _to_float(geo_profile.heat_risk_score) if geo_profile else None,
        "transit_proximity_km": _to_float(geo_profile.transit_proximity_km) if geo_profile else None,
    }

    market_tier = "emerging"
    if score:
        land_value = _to_float(score.get("land_value_score"), 0.0) or 0.0
        if land_value >= 75:
            market_tier = "premium"
        elif land_value >= 55:
            market_tier = "core"

    intelligence_score = _safe_mean([
        _to_float(score.get("land_value_score")) if score else None,
        _to_float(score.get("development_potential_score")) if score else None,
        _to_float(score.get("future_appreciation_index")) if score else None,
    ])

    source_summary = (
        f"Masterplan={masterplan.version if masterplan else 'na'} "
        f"({masterplan.dataset_version if masterplan else 'na'}), "
        f"GeoProfile={geo_profile.dataset_version if geo_profile else 'na'}, "
        f"Standards={', '.join(standard.code for standard in standards) or 'na'}"
    )

    return {
        "location_id": location_id,
        "version_tag": version_tag,
        "country_code": location.country_code or DEFAULT_COUNTRY_CODE,
        "admin_area": location.state or location.city,
        "market_tier": market_tier,
        "validation_status": "derived",
        "floor_plan_constraints": floor_plan_constraints,
        "zoning_validation_rules": zoning_validation_rules,
        "location_intelligence_score": intelligence_score,
        "massing_inputs": massing_inputs,
        "source_summary": source_summary,
    }


def create_planning_context(session: Session, payload: dict) -> PlanningContext:
    location = get_location(session, payload["location_id"])
    if not location:
        raise ValueError(f"Location {payload['location_id']} not found")

    if payload.get("auto_derive"):
        payload = {
            **derive_planning_context_payload(
                session,
                payload["location_id"],
                version_tag=payload.get("version_tag", "derived_v1"),
            ),
            **{key: value for key, value in payload.items() if key not in {"auto_derive", "location_id"}},
        }

    context = PlanningContext(
        location_id=payload["location_id"],
        version_tag=payload.get("version_tag", "v1"),
        country_code=payload.get("country_code", DEFAULT_COUNTRY_CODE),
        admin_area=payload.get("admin_area"),
        market_tier=payload.get("market_tier"),
        validation_status=payload.get("validation_status", "draft"),
        floor_plan_constraints=payload.get("floor_plan_constraints") or {},
        zoning_validation_rules=payload.get("zoning_validation_rules") or {},
        location_intelligence_score=payload.get("location_intelligence_score"),
        massing_inputs=payload.get("massing_inputs") or {},
        source_summary=payload.get("source_summary"),
    )
    session.add(context)
    session.flush()
    return context


def derive_planning_context(session: Session, location_id: int, *, version_tag: str = "derived_v1") -> PlanningContext:
    payload = derive_planning_context_payload(session, location_id, version_tag=version_tag)
    return create_planning_context(session, payload)


def build_location_intelligence_record(session: Session, location_id: int) -> dict | None:
    summary = get_location_summary(session, location_id)
    if not summary:
        return None

    from brain.valuation import service as valuation_service

    location = summary["location"]
    masterplan = summary["masterplan"]
    census = summary["census"]
    geo_profile = summary["geo_profile"]
    score = valuation_service.get_or_compute_score(session, location_id)
    valuation_inputs = valuation_service.build_valuation_inputs(session, location_id)
    coverage = valuation_inputs.get("coverage", {}) if valuation_inputs else {}
    prediction = valuation_service.predict_price_for_location(session, location_id)
    planning_context = get_planning_context(session, location_id)

    standards = summary["regional_standards"]
    if planning_context is None:
        planning_context = derive_planning_context(session, location_id)

    return {
        "location_id": location_id,
        "location_name": location.name,
        "city": location.city,
        "zoning_type": masterplan.zoning_type if masterplan else None,
        "fsi": _to_float(masterplan.fsi) if masterplan else None,
        "avg_price_per_sqft": _to_float(summary["avg_price_per_sqft"]),
        "land_value_score": _to_float(score.get("land_value_score")) if score else None,
        "development_potential_score": _to_float(score.get("development_potential_score")) if score else None,
        "future_appreciation_index": _to_float(score.get("future_appreciation_index")) if score else None,
        "density_score": _to_float(score.get("components", {}).get("density_score")) if score else None,
        "infra_score": _to_float(score.get("components", {}).get("infra_score")) if score else None,
        "price_trend_score": _to_float(score.get("components", {}).get("price_trend_score")) if score else None,
        "climate_resilience_score": _to_float(score.get("components", {}).get("climate_resilience_score")) if score else None,
        "terrain_readiness_score": _to_float(score.get("components", {}).get("terrain_readiness_score")) if score else None,
        "population": census.population if census else None,
        "growth_rate_pct": _to_float(census.growth_rate_pct) if census else None,
        "terrain_class": geo_profile.terrain_class if geo_profile else None,
        "terrain_slope_pct": _to_float(geo_profile.terrain_slope_pct) if geo_profile else None,
        "flood_risk_score": _to_float(geo_profile.flood_risk_score) if geo_profile else None,
        "heat_risk_score": _to_float(geo_profile.heat_risk_score) if geo_profile else None,
        "climate_risk_score": _to_float(geo_profile.climate_risk_score) if geo_profile else None,
        "predicted_price_1yr": prediction.predicted_price_1yr if prediction else None,
        "predicted_price_3yr": prediction.predicted_price_3yr if prediction else None,
        "prediction_confidence": prediction.confidence if prediction else None,
        "planning_context_id": planning_context.id if planning_context else None,
        "planning_context_version": planning_context.version_tag if planning_context else None,
        "data_confidence_score": _to_float(coverage.get("evidence_score"), None),
        "data_confidence_band": coverage.get("confidence_band"),
        "data_gaps": coverage.get("data_gaps", []),
        "regional_standards": [standard.code for standard in standards],
        "masterplan_version": masterplan.version if masterplan else None,
        "masterplan_dataset_version": masterplan.dataset_version if masterplan else None,
    }
