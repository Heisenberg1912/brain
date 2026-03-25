"""Weighted scoring model for land valuation."""
from __future__ import annotations

import json
from pathlib import Path

from brain.config import PROJECT_ROOT


def load_weights() -> dict:
    path = PROJECT_ROOT / "scoring_weights.json"
    with open(path) as f:
        return json.load(f)


ZONE_VALUE = {
    "mixed": 90,
    "commercial": 85,
    "residential": 70,
    "industrial": 50,
}

ZONING_SHIFT_POTENTIAL = {
    "residential": 52,
    "commercial": 64,
    "mixed": 86,
    "industrial": 74,
}

USE_CASE_ZONE_FIT = {
    "residential": {
        "residential": 95,
        "mixed": 82,
        "commercial": 42,
        "industrial": 18,
    },
    "commercial": {
        "commercial": 95,
        "mixed": 86,
        "industrial": 48,
        "residential": 28,
    },
    "mixed_use": {
        "mixed": 96,
        "commercial": 78,
        "residential": 72,
        "industrial": 32,
    },
    "industrial": {
        "industrial": 96,
        "mixed": 46,
        "commercial": 34,
        "residential": 16,
    },
}

TERRAIN_CLASS_VALUE = {
    "flat": 92,
    "gentle": 84,
    "undulating": 68,
    "steep": 42,
}


def _normalize(value: float, min_val: float, max_val: float) -> float:
    if max_val == min_val:
        return 50.0
    return max(0, min(100, (value - min_val) / (max_val - min_val) * 100))


def _clamp(value: float) -> float:
    return max(0, min(100, value))


def _canonical_zoning_type(zoning_type: str | None) -> str | None:
    if zoning_type is None:
        return None
    normalized = zoning_type.strip().lower().replace("-", "_")
    aliases = {
        "mixed_use": "mixed",
        "mixeduse": "mixed",
    }
    return aliases.get(normalized, normalized) or None


def _masterplan_sort_key(masterplan) -> tuple[str, str, int]:
    effective_from = getattr(masterplan, "effective_from", None)
    created_at = getattr(masterplan, "created_at", None)
    return (
        effective_from.isoformat() if effective_from else "",
        created_at.isoformat() if created_at else "",
        int(getattr(masterplan, "id", 0) or 0),
    )


def _apply_resilience_adjustment(
    base_score: float,
    *,
    climate_resilience_score: float | None = None,
    terrain_readiness_score: float | None = None,
    climate_weight: float = 0.08,
    terrain_weight: float = 0.06,
) -> float:
    adjusted = base_score
    if climate_resilience_score is not None:
        adjusted += (climate_resilience_score - 50) * climate_weight
    if terrain_readiness_score is not None:
        adjusted += (terrain_readiness_score - 50) * terrain_weight
    return _clamp(adjusted)


def compute_infra_score(nearby_infra: list[dict]) -> float:
    if not nearby_infra:
        return 10.0

    type_weights = {
        "metro_station": 25,
        "economic_zone": 20,
        "tech_park": 20,
        "hospital": 15,
        "school": 10,
        "highway": 10,
        "railway_station": 8,
        "airport": 5,
    }

    score = 0.0
    for item in nearby_infra:
        infra = item["infrastructure"]
        dist_km = item["distance_km"]
        weight = type_weights.get(infra.infra_type, 5)
        proximity_factor = max(0, 1 - (dist_km / 5))
        status_bonus = 1.2 if infra.status in ("under_construction", "planned") else 1.0
        score += weight * proximity_factor * status_bonus

    return min(100, score)


def _distance_to_access_score(
    distance_km: float | None,
    *,
    max_distance_km: float,
    missing_score: float,
) -> float:
    if distance_km is None:
        return missing_score
    return _clamp(100 - _normalize(float(distance_km), 0, max_distance_km))


def _nearest_infra_distance(nearby_infra: list[dict], infra_types: set[str]) -> float | None:
    distances = [
        float(item["distance_km"])
        for item in nearby_infra
        if item["infrastructure"].infra_type in infra_types
    ]
    return min(distances) if distances else None


def compute_infra_proximity_profile(nearby_infra: list[dict], geo_profile) -> dict:
    road_distance = getattr(geo_profile, "road_proximity_km", None) if geo_profile else None
    if road_distance is None:
        road_distance = _nearest_infra_distance(nearby_infra, {"highway"})

    metro_distance = _nearest_infra_distance(nearby_infra, {"metro_station"})
    if metro_distance is None and geo_profile:
        metro_distance = getattr(geo_profile, "transit_proximity_km", None)

    economic_zone_distance = _nearest_infra_distance(nearby_infra, {"economic_zone", "tech_park"})

    road_access_score = _distance_to_access_score(
        road_distance,
        max_distance_km=8,
        missing_score=42.0,
    )
    metro_access_score = _distance_to_access_score(
        metro_distance,
        max_distance_km=5,
        missing_score=35.0,
    )
    economic_access_score = _distance_to_access_score(
        economic_zone_distance,
        max_distance_km=10,
        missing_score=38.0,
    )
    strategic_infra_score = _clamp(
        (road_access_score * 0.30)
        + (metro_access_score * 0.40)
        + (economic_access_score * 0.30)
    )

    return {
        "road_proximity_km": round(float(road_distance), 2) if road_distance is not None else None,
        "metro_proximity_km": round(float(metro_distance), 2) if metro_distance is not None else None,
        "economic_zone_proximity_km": round(float(economic_zone_distance), 2) if economic_zone_distance is not None else None,
        "road_access_score": round(road_access_score, 2),
        "metro_access_score": round(metro_access_score, 2),
        "economic_access_score": round(economic_access_score, 2),
        "strategic_infra_score": round(strategic_infra_score, 2),
        "metro_station_count": sum(
            1
            for item in nearby_infra
            if item["infrastructure"].infra_type == "metro_station"
        ),
        "economic_zone_count": sum(
            1
            for item in nearby_infra
            if item["infrastructure"].infra_type in {"economic_zone", "tech_park"}
        ),
        "highway_count": sum(
            1
            for item in nearby_infra
            if item["infrastructure"].infra_type == "highway"
        ),
    }


def compute_price_trend(prices: list) -> float:
    if len(prices) < 2:
        return 50.0

    sorted_prices = sorted(prices, key=lambda price: price.recorded_date)
    oldest = float(sorted_prices[0].price_per_sqft)
    newest = float(sorted_prices[-1].price_per_sqft)

    if oldest == 0:
        return 50.0

    growth_pct = ((newest - oldest) / oldest) * 100
    return _clamp(50 + (growth_pct * 2.5))


def compute_zoning_favorability(masterplan) -> float:
    if not masterplan:
        return 30.0

    zone_score = ZONE_VALUE.get(masterplan.zoning_type, 50)
    fsi = float(masterplan.fsi or 1.5)
    fsi_score = min(100, fsi * 30)
    return (zone_score * 0.5) + (fsi_score * 0.5)


def compute_density_score(census) -> float:
    if not census:
        return 50.0

    density = float(census.density_per_sqkm or 0)
    if density < 5000:
        return _normalize(density, 0, 5000) * 0.6
    if density <= 15000:
        return 60 + _normalize(density, 5000, 15000) * 0.3
    return max(40, 90 - _normalize(density, 15000, 25000) * 0.3)


def compute_population_growth_score(population_growth_pct: float | None) -> float:
    if population_growth_pct is None:
        return 50.0
    return _clamp(_normalize(float(population_growth_pct), 0, 8))


def compute_demand_pressure_score(
    population_growth_pct: float | None,
    density_score: float,
) -> float:
    growth_score = compute_population_growth_score(population_growth_pct)
    return _clamp((growth_score * 0.55) + (density_score * 0.45))


def compute_climate_resilience_score(geo_profile) -> float:
    if not geo_profile:
        return 50.0

    flood_risk = float(getattr(geo_profile, "flood_risk_score", 50) or 50)
    heat_risk = float(getattr(geo_profile, "heat_risk_score", 50) or 50)
    climate_risk = float(getattr(geo_profile, "climate_risk_score", 50) or 50)
    aggregate_risk = (flood_risk * 0.45) + (heat_risk * 0.25) + (climate_risk * 0.30)
    return _clamp(100 - aggregate_risk)


def compute_climate_exposure_score(geo_profile) -> float:
    return _clamp(100 - compute_climate_resilience_score(geo_profile))


def compute_terrain_readiness_score(geo_profile) -> float:
    if not geo_profile:
        return 50.0

    terrain_class = getattr(geo_profile, "terrain_class", None) or "undulating"
    class_score = TERRAIN_CLASS_VALUE.get(terrain_class, 65)
    slope = float(getattr(geo_profile, "terrain_slope_pct", 6) or 6)
    slope_score = _clamp(100 - _normalize(slope, 0, 20) * 0.75)
    return _clamp((class_score * 0.6) + (slope_score * 0.4))


def compute_terrain_constraint_score(geo_profile) -> float:
    return _clamp(100 - compute_terrain_readiness_score(geo_profile))


def compute_site_risk_score(geo_profile) -> float:
    climate_exposure_score = compute_climate_exposure_score(geo_profile)
    terrain_constraint_score = compute_terrain_constraint_score(geo_profile)
    return _clamp((climate_exposure_score * 0.6) + (terrain_constraint_score * 0.4))


def compute_land_value_score(
    avg_price: float | None,
    infra_score: float,
    zoning_favorability: float,
    density_score: float,
    price_trend: float,
    weights: dict,
    climate_resilience_score: float | None = None,
    terrain_readiness_score: float | None = None,
) -> float:
    price_normalized = _normalize(avg_price or 5000, 3000, 15000)
    w = weights["land_value"]
    base_score = (
        price_normalized * w["avg_price_normalized"]
        + infra_score * w["infra_proximity"]
        + zoning_favorability * w["zoning_favorability"]
        + density_score * w["density"]
        + price_trend * w["price_trend"]
    )
    return _apply_resilience_adjustment(
        base_score,
        climate_resilience_score=climate_resilience_score,
        terrain_readiness_score=terrain_readiness_score,
        climate_weight=0.10,
        terrain_weight=0.05,
    )


def compute_development_potential(
    masterplan,
    infra_planned_count: int,
    price_growth_rate: float,
    weights: dict,
    climate_resilience_score: float | None = None,
    terrain_readiness_score: float | None = None,
) -> float:
    fsi = float(masterplan.fsi or 1.5) if masterplan else 1.5
    fsi_headroom = _normalize(fsi, 1.0, 4.0)
    zone_value = ZONE_VALUE.get(masterplan.zoning_type if masterplan else "residential", 50)
    infra_planned = min(100, infra_planned_count * 25)
    w = weights["development_potential"]
    base_score = (
        fsi_headroom * w["fsi_headroom"]
        + zone_value * w["zoning_type_value"]
        + infra_planned * w["infra_planned"]
        + price_growth_rate * w["price_growth_rate"]
    )
    return _apply_resilience_adjustment(
        base_score,
        climate_resilience_score=climate_resilience_score,
        terrain_readiness_score=terrain_readiness_score,
        climate_weight=0.06,
        terrain_weight=0.12,
    )


def compute_future_appreciation(
    price_trend: float,
    infra_pipeline_count: int,
    population_growth_pct: float,
    zoning_type: str | None,
    weights: dict,
    demand_pressure_score: float | None = None,
    zoning_shift_score: float | None = None,
    climate_resilience_score: float | None = None,
    terrain_readiness_score: float | None = None,
) -> float:
    infra_pipeline = min(100, infra_pipeline_count * 30)
    population_growth_score = compute_population_growth_score(population_growth_pct)
    demand_signal = population_growth_score
    if demand_pressure_score is not None:
        demand_signal = _clamp((population_growth_score * 0.65) + (demand_pressure_score * 0.35))
    zoning_shift = zoning_shift_score
    if zoning_shift is None:
        zoning_shift = ZONING_SHIFT_POTENTIAL.get(_canonical_zoning_type(zoning_type) or "residential", 50)

    w = weights["future_appreciation"]
    base_score = (
        price_trend * w["price_trend_5yr"]
        + infra_pipeline * w["infra_pipeline"]
        + demand_signal * w["population_growth"]
        + zoning_shift * w["zoning_shift_potential"]
    )
    return _apply_resilience_adjustment(
        base_score,
        climate_resilience_score=climate_resilience_score,
        terrain_readiness_score=terrain_readiness_score,
        climate_weight=0.12,
        terrain_weight=0.05,
    )


def compute_masterplan_zoning_shift_score(masterplan_history: list | None, zoning_type: str | None = None) -> float:
    ordered_history = sorted(masterplan_history or [], key=_masterplan_sort_key)
    historical_zones = [
        _canonical_zoning_type(getattr(masterplan, "zoning_type", None))
        for masterplan in ordered_history
    ]
    historical_zones = [zone for zone in historical_zones if zone]

    current_zone = _canonical_zoning_type(zoning_type) or (historical_zones[-1] if historical_zones else None)
    if current_zone is None:
        return 50.0

    current_score = ZONING_SHIFT_POTENTIAL.get(current_zone, 50.0)
    previous_zone = next((zone for zone in reversed(historical_zones[:-1]) if zone != current_zone), None)
    if previous_zone is None:
        return current_score

    previous_score = ZONING_SHIFT_POTENTIAL.get(previous_zone, 50.0)
    delta = current_score - previous_score
    adjustment_factor = 0.35 if delta >= 0 else 0.45
    return _clamp(current_score + (delta * adjustment_factor))


def compute_market_momentum_score(
    land_value_score: float,
    future_appreciation_index: float,
    price_trend_score: float,
) -> float:
    return _clamp(
        (land_value_score * 0.35)
        + (future_appreciation_index * 0.40)
        + (price_trend_score * 0.25)
    )


def compute_mobility_score(nearby_infra: list[dict], geo_profile) -> float:
    infra_score = compute_infra_score(nearby_infra)

    road_distance = getattr(geo_profile, "road_proximity_km", None) if geo_profile else None
    transit_distance = getattr(geo_profile, "transit_proximity_km", None) if geo_profile else None

    road_score = 60.0 if road_distance is None else 100 - _normalize(float(road_distance), 0, 8)
    transit_score = 45.0 if transit_distance is None else 100 - _normalize(float(transit_distance), 0, 5)

    transit_node_types = {"metro_station", "railway_station"}
    transit_distances = [
        float(item["distance_km"])
        for item in nearby_infra
        if item["infrastructure"].infra_type in transit_node_types
    ]
    closest_transit = min(transit_distances) if transit_distances else None
    transit_bonus = 0.0
    if closest_transit is not None:
        if closest_transit <= 1:
            transit_bonus = 12.0
        elif closest_transit <= 2:
            transit_bonus = 6.0

    return _clamp((infra_score * 0.40) + (road_score * 0.20) + (transit_score * 0.35) + transit_bonus)


def compute_regulatory_clarity_score(masterplan, planning_context, regional_standards: list | None = None) -> float:
    score = 20.0
    if masterplan:
        score += 20.0
        approval_status = (getattr(masterplan, "approval_status", None) or "").lower()
        if approval_status == "active":
            score += 15.0
        elif approval_status in {"provisional", "draft"}:
            score += 8.0

    if planning_context:
        validation_status = (getattr(planning_context, "validation_status", None) or "").lower()
        if validation_status in {"validated", "approved"}:
            score += 25.0
        elif validation_status in {"derived", "active"}:
            score += 18.0
        else:
            score += 10.0

        if getattr(planning_context, "zoning_validation_rules", None):
            score += 5.0
        if getattr(planning_context, "floor_plan_constraints", None):
            score += 5.0

    score += min(15.0, len(regional_standards or []) * 5.0)
    return _clamp(score)


def compute_site_readiness_score(masterplan, geo_profile) -> float:
    climate_resilience_score = compute_climate_resilience_score(geo_profile)
    terrain_readiness_score = compute_terrain_readiness_score(geo_profile)

    fsi_score = 50.0 if not masterplan else min(100.0, float(masterplan.fsi or 1.5) * 25)
    height_score = 50.0 if not masterplan else _normalize(float(masterplan.max_height_m or 18), 12, 90)
    coverage_score = 50.0 if not masterplan else _normalize(float(masterplan.ground_coverage_pct or 45), 30, 75)

    return _clamp(
        (climate_resilience_score * 0.25)
        + (terrain_readiness_score * 0.25)
        + (fsi_score * 0.20)
        + (height_score * 0.15)
        + (coverage_score * 0.15)
    )


def compute_use_case_favorability(
    use_case: str,
    *,
    zoning_type: str | None,
    land_value_score: float,
    development_potential_score: float,
    future_appreciation_index: float,
    infra_score: float,
    density_score: float,
    climate_resilience_score: float,
    terrain_readiness_score: float,
) -> float:
    zone_fit = USE_CASE_ZONE_FIT.get(use_case, {}).get(zoning_type or "residential", 45)

    if use_case == "residential":
        return _clamp(
            (zone_fit * 0.24)
            + (density_score * 0.16)
            + (infra_score * 0.14)
            + (climate_resilience_score * 0.14)
            + (terrain_readiness_score * 0.10)
            + (future_appreciation_index * 0.10)
            + (development_potential_score * 0.12)
        )

    if use_case == "commercial":
        return _clamp(
            (zone_fit * 0.24)
            + (infra_score * 0.22)
            + (land_value_score * 0.16)
            + (development_potential_score * 0.14)
            + (future_appreciation_index * 0.12)
            + (climate_resilience_score * 0.06)
            + (density_score * 0.06)
        )

    if use_case == "industrial":
        return _clamp(
            (zone_fit * 0.30)
            + (development_potential_score * 0.20)
            + (infra_score * 0.12)
            + (terrain_readiness_score * 0.12)
            + (future_appreciation_index * 0.10)
            + (climate_resilience_score * 0.08)
            + (land_value_score * 0.08)
        )

    return _clamp(
        (zone_fit * 0.26)
        + (development_potential_score * 0.22)
        + (infra_score * 0.18)
        + (future_appreciation_index * 0.12)
        + (density_score * 0.10)
        + (climate_resilience_score * 0.07)
        + (terrain_readiness_score * 0.05)
    )


def compute_overall_favorability_score(
    *,
    market_momentum_score: float,
    site_readiness_score: float,
    regulatory_clarity_score: float,
    mobility_score: float,
    best_use_case_score: float,
) -> float:
    return _clamp(
        (market_momentum_score * 0.24)
        + (site_readiness_score * 0.22)
        + (regulatory_clarity_score * 0.16)
        + (mobility_score * 0.16)
        + (best_use_case_score * 0.22)
    )
