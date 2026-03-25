from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import (
    CensusOut,
    ErrorResponse,
    GeoProfileOut,
    InfrastructureOut,
    LocationIntelligenceOut,
    LocationOut,
    LocationSummary,
    LocationWithDistance,
    MasterplanOut,
    NearbyInfraGeo,
    NearbyInfraOut,
    PlanningContextCreate,
    PlanningContextOut,
    PriceOut,
    RegionalStandardOut,
)
from brain.data_bank import service as data_svc
from brain.data_bank.models import Infrastructure

router = APIRouter()


def _loc_to_dict(loc, session: Session) -> dict:
    geom_text = session.scalar(func.ST_AsText(loc.geom)) if loc.geom else None
    lat, lng = None, None
    if geom_text:
        coords = geom_text.replace("POINT(", "").replace(")", "").split()
        lng, lat = float(coords[0]), float(coords[1])

    from brain.data_bank.models import Masterplan

    zoning = session.scalar(
        select(Masterplan.zoning_type)
        .where(Masterplan.location_id == loc.id)
        .order_by(Masterplan.effective_from.desc().nullslast(), Masterplan.created_at.desc())
        .limit(1)
    )

    return {
        "id": loc.id,
        "name": loc.name,
        "country_code": getattr(loc, "country_code", "IN") or "IN",
        "state": getattr(loc, "state", None),
        "city": loc.city,
        "locality": loc.locality,
        "ward": loc.ward,
        "pin_code": loc.pin_code,
        "lat": lat,
        "lng": lng,
        "zoning_type": zoning or "residential",
    }


def _masterplan_to_dict(masterplan) -> dict | None:
    if not masterplan:
        return None
    return {
        "zoning_type": masterplan.zoning_type,
        "fsi": float(masterplan.fsi) if masterplan.fsi else None,
        "ground_coverage_pct": float(masterplan.ground_coverage_pct) if masterplan.ground_coverage_pct else None,
        "max_height_m": float(masterplan.max_height_m) if masterplan.max_height_m else None,
        "setback_front_m": float(masterplan.setback_front_m) if masterplan.setback_front_m else None,
        "setback_side_m": float(masterplan.setback_side_m) if masterplan.setback_side_m else None,
        "version": masterplan.version,
        "dataset_version": masterplan.dataset_version,
        "effective_from": masterplan.effective_from.isoformat() if masterplan.effective_from else None,
        "effective_to": masterplan.effective_to.isoformat() if masterplan.effective_to else None,
        "approval_status": masterplan.approval_status,
        "tags": masterplan.tags or [],
    }


def _price_to_dict(price_point) -> dict:
    return {
        "price_per_sqft": float(price_point.price_per_sqft),
        "property_type": price_point.property_type,
        "recorded_date": str(price_point.recorded_date),
        "source": price_point.source,
        "tags": price_point.tags or [],
    }


def _infra_to_dict(item) -> dict:
    infra = item["infrastructure"]
    return {
        "name": infra.name,
        "infra_type": infra.infra_type,
        "status": infra.status,
        "distance_km": item["distance_km"],
    }


def _census_to_dict(census) -> dict | None:
    if not census:
        return None
    return {
        "year": census.year,
        "population": census.population,
        "density_per_sqkm": float(census.density_per_sqkm) if census.density_per_sqkm else None,
        "growth_rate_pct": float(census.growth_rate_pct) if census.growth_rate_pct else None,
        "households": census.households,
        "tags": census.tags or [],
    }


def _geo_profile_to_dict(geo_profile) -> dict | None:
    if not geo_profile:
        return None
    return {
        "terrain_class": geo_profile.terrain_class,
        "terrain_slope_pct": float(geo_profile.terrain_slope_pct) if geo_profile.terrain_slope_pct is not None else None,
        "flood_risk_score": float(geo_profile.flood_risk_score) if geo_profile.flood_risk_score is not None else None,
        "heat_risk_score": float(geo_profile.heat_risk_score) if geo_profile.heat_risk_score is not None else None,
        "climate_risk_score": float(geo_profile.climate_risk_score) if geo_profile.climate_risk_score is not None else None,
        "road_proximity_km": float(geo_profile.road_proximity_km) if geo_profile.road_proximity_km is not None else None,
        "transit_proximity_km": float(geo_profile.transit_proximity_km) if geo_profile.transit_proximity_km is not None else None,
        "dataset_version": geo_profile.dataset_version,
        "source": geo_profile.source,
        "tags": geo_profile.tags or [],
    }


def _regional_standard_to_dict(standard) -> dict:
    return {
        "id": standard.id,
        "standard_type": standard.standard_type,
        "country_code": standard.country_code,
        "admin_area": standard.admin_area,
        "region_name": standard.region_name,
        "code": standard.code,
        "title": standard.title,
        "version_tag": standard.version_tag,
        "source_url": standard.source_url,
        "tags": standard.tags or [],
        "rules": standard.rules or {},
    }


def _planning_context_to_dict(context) -> dict | None:
    if not context:
        return None
    return {
        "id": context.id,
        "location_id": context.location_id,
        "version_tag": context.version_tag,
        "country_code": context.country_code,
        "admin_area": context.admin_area,
        "market_tier": context.market_tier,
        "validation_status": context.validation_status,
        "floor_plan_constraints": context.floor_plan_constraints or {},
        "zoning_validation_rules": context.zoning_validation_rules or {},
        "location_intelligence_score": float(context.location_intelligence_score) if context.location_intelligence_score is not None else None,
        "massing_inputs": context.massing_inputs or {},
        "source_summary": context.source_summary,
    }


@router.get("/locations", response_model=list[LocationOut])
def list_locations(
    city: str | None = None,
    state: str | None = None,
    db: Session = Depends(get_db),
):
    return [_loc_to_dict(loc, db) for loc in data_svc.get_all_locations(db, city=city, state=state)]


@router.get("/locations/nearby", response_model=list[LocationWithDistance])
def nearby_locations(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
    radius_km: float = Query(default=5.0, gt=0, le=100),
    db: Session = Depends(get_db),
):
    return [
        {**_loc_to_dict(item["location"], db), "distance_km": item["distance_km"]}
        for item in data_svc.find_nearby_locations(db, lat, lng, radius_km)
    ]


@router.get("/infrastructure", response_model=list[InfrastructureOut])
def list_infrastructure(db: Session = Depends(get_db)):
    items = db.query(Infrastructure).all()
    result = []
    for item in items:
        geom_text = db.scalar(func.ST_AsText(item.geom)) if item.geom else None
        lat, lng = None, None
        if geom_text:
            coords = geom_text.replace("POINT(", "").replace(")", "").split()
            lng, lat = float(coords[0]), float(coords[1])
        result.append({
            "id": item.id,
            "name": item.name,
            "infra_type": item.infra_type,
            "country_code": getattr(item, "country_code", "IN") or "IN",
            "state": getattr(item, "state", None),
            "city": getattr(item, "city", None),
            "status": item.status,
            "lat": lat,
            "lng": lng,
            "tags": item.tags or [],
        })
    return result


@router.get("/standards", response_model=list[RegionalStandardOut])
def list_standards(
    country_code: str = Query(default="IN", min_length=2, max_length=2),
    admin_area: str | None = Query(default=None),
    standard_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return [
        _regional_standard_to_dict(item)
        for item in data_svc.list_regional_standards(
            db,
            country_code=country_code.upper(),
            admin_area=admin_area,
            standard_type=standard_type,
        )
    ]


@router.get(
    "/locations/{location_id}/geo-profile",
    response_model=GeoProfileOut,
    responses={404: {"model": ErrorResponse}},
)
def get_geo_profile(location_id: int, db: Session = Depends(get_db)):
    profile = data_svc.get_geo_profile(db, location_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Geo profile for location {location_id} not found")
    return _geo_profile_to_dict(profile)


@router.get(
    "/locations/{location_id}/planning-context",
    response_model=PlanningContextOut,
    responses={404: {"model": ErrorResponse}},
)
def get_planning_context(location_id: int, db: Session = Depends(get_db)):
    context = data_svc.get_planning_context(db, location_id)
    if not context:
        raise HTTPException(status_code=404, detail=f"Planning context for location {location_id} not found")
    return _planning_context_to_dict(context)


@router.post(
    "/locations/{location_id}/planning-context/derive",
    response_model=PlanningContextOut,
    responses={404: {"model": ErrorResponse}},
)
def derive_planning_context(location_id: int, version_tag: str = Query(default="derived_v1"), db: Session = Depends(get_db)):
    try:
        context = data_svc.derive_planning_context(db, location_id, version_tag=version_tag)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return _planning_context_to_dict(context)


@router.post(
    "/planning-contexts",
    response_model=PlanningContextOut,
    responses={404: {"model": ErrorResponse}},
)
def create_planning_context(body: PlanningContextCreate, db: Session = Depends(get_db)):
    try:
        context = data_svc.create_planning_context(db, body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    db.commit()
    return _planning_context_to_dict(context)


@router.get(
    "/locations/{location_id}/intelligence",
    response_model=LocationIntelligenceOut,
    responses={404: {"model": ErrorResponse}},
)
def get_location_intelligence(location_id: int, db: Session = Depends(get_db)):
    try:
        record = data_svc.build_location_intelligence_record(db, location_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not record:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    db.commit()
    return record


@router.get(
    "/locations/{location_id}",
    response_model=LocationSummary,
    responses={404: {"model": ErrorResponse}},
)
def get_location(location_id: int, db: Session = Depends(get_db)):
    summary = data_svc.get_location_summary(db, location_id)
    if not summary:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")

    return {
        "location": _loc_to_dict(summary["location"], db),
        "masterplan": _masterplan_to_dict(summary["masterplan"]),
        "avg_price_per_sqft": float(summary["avg_price_per_sqft"]) if summary["avg_price_per_sqft"] else None,
        "price_history": [_price_to_dict(item) for item in summary["price_history"]],
        "census": _census_to_dict(summary["census"]),
        "geo_profile": _geo_profile_to_dict(summary.get("geo_profile")),
        "regional_standards": [_regional_standard_to_dict(item) for item in summary.get("regional_standards", [])],
        "nearby_infrastructure": [_infra_to_dict(item) for item in summary["nearby_infrastructure"]],
    }


@router.get(
    "/locations/{location_id}/nearby-infra",
    response_model=list[NearbyInfraGeo],
    responses={404: {"model": ErrorResponse}},
)
def get_nearby_infra(
    location_id: int,
    radius_km: float = Query(default=5.0, gt=0, le=50),
    db: Session = Depends(get_db),
):
    location = data_svc.get_location(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")

    geom_text = db.scalar(func.ST_AsText(location.geom)) if location.geom else None
    if not geom_text:
        return []

    coords = geom_text.replace("POINT(", "").replace(")", "").split()
    lng, lat = float(coords[0]), float(coords[1])
    nearby = data_svc.find_nearby_infrastructure(db, lat, lng, radius_km)

    result = []
    for item in nearby:
        infra = item["infrastructure"]
        infra_geom = db.scalar(func.ST_AsText(infra.geom)) if infra.geom else None
        i_lat, i_lng = None, None
        if infra_geom:
            ic = infra_geom.replace("POINT(", "").replace(")", "").split()
            i_lng, i_lat = float(ic[0]), float(ic[1])
        result.append({
            "id": infra.id,
            "name": infra.name,
            "infra_type": infra.infra_type,
            "status": infra.status,
            "lat": i_lat,
            "lng": i_lng,
            "distance_km": item["distance_km"],
        })
    return result
