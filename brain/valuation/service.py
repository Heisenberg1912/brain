"""Valuation service: score locations, rank, compare, and predict."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from brain.data_bank import service as data_svc
from brain.valuation.models import ValuationScore
from brain.valuation.scoring import (
    compute_climate_exposure_score,
    compute_climate_resilience_score,
    compute_demand_pressure_score,
    compute_density_score,
    compute_development_potential,
    compute_future_appreciation,
    compute_infra_score,
    compute_infra_proximity_profile,
    compute_land_value_score,
    compute_market_momentum_score,
    compute_masterplan_zoning_shift_score,
    compute_mobility_score,
    compute_overall_favorability_score,
    compute_population_growth_score,
    compute_regulatory_clarity_score,
    compute_site_readiness_score,
    compute_site_risk_score,
    compute_price_trend,
    compute_terrain_constraint_score,
    compute_terrain_readiness_score,
    compute_use_case_favorability,
    compute_zoning_favorability,
    load_weights,
)

FAVORABILITY_USE_CASES = ("residential", "commercial", "mixed_use", "industrial")
FAVORABILITY_SORT_FIELDS = {"overall", *FAVORABILITY_USE_CASES}
logger = logging.getLogger(__name__)
SCORING_VERSION = "coverage_calibrated_v2"


def _to_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _favorability_band(score: float) -> str:
    if score >= 75:
        return "prime"
    if score >= 60:
        return "strong"
    if score >= 45:
        return "selective"
    return "constrained"


def _demand_profile(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 75:
        return "surging"
    if score >= 60:
        return "growing"
    if score >= 45:
        return "balanced"
    return "thin"


def _site_risk_band(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 70:
        return "severe"
    if score >= 55:
        return "elevated"
    if score >= 35:
        return "managed"
    return "contained"


def _price_momentum_band(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 75:
        return "hot"
    if score >= 60:
        return "positive"
    if score >= 45:
        return "steady"
    return "soft"


def _coverage_band(score: float) -> str:
    if score >= 80:
        return "high"
    if score >= 60:
        return "medium"
    return "low"


def _confidence_calibration_factor(score: float) -> float:
    bounded = max(0.0, min(score, 100.0))
    return round(0.55 + (bounded / 100.0 * 0.45), 2)


def _calibrate_score(score: float | None, factor: float, *, baseline: float = 50.0) -> float:
    if score is None:
        return round(baseline, 2)
    bounded = max(0.0, min(score, 100.0))
    if factor >= 0.999:
        return round(bounded, 2)
    return round(baseline + ((bounded - baseline) * factor), 2)


def _build_data_coverage_snapshot(summary: dict) -> dict:
    masterplan = summary.get("masterplan")
    masterplan_history = summary.get("masterplan_history") or ([masterplan] if masterplan else [])
    prices = summary.get("price_history") or []
    census = summary.get("census")
    geo_profile = summary.get("geo_profile")
    nearby_infra = summary.get("nearby_infrastructure") or []
    regional_standards = summary.get("regional_standards") or []

    ordered_prices = sorted(
        [price for price in prices if getattr(price, "recorded_date", None)],
        key=lambda price: price.recorded_date,
    )
    price_points = len(ordered_prices)
    price_history_span_days = (
        max(0, (ordered_prices[-1].recorded_date - ordered_prices[0].recorded_date).days)
        if price_points > 1
        else 0
    )
    latest_price_age_days = (
        max(0, (datetime.now(timezone.utc).date() - ordered_prices[-1].recorded_date).days)
        if ordered_prices
        else None
    )

    evidence_score = 0.0
    data_gaps: list[str] = []

    if masterplan:
        evidence_score += 15
        if len(masterplan_history) >= 2:
            evidence_score += 5
        else:
            data_gaps.append("Limited masterplan change history constrains zoning-shift confidence.")
    else:
        data_gaps.append("Missing active masterplan record limits zoning and entitlement accuracy.")

    if price_points >= 6:
        evidence_score += 20
    elif price_points >= 3:
        evidence_score += 16
    elif price_points == 2:
        evidence_score += 11
        data_gaps.append("Price history is thin and may overfit short-term trend calculations.")
    elif price_points == 1:
        evidence_score += 5
        data_gaps.append("Only one price point is available, so trend and appreciation signals are provisional.")
    else:
        data_gaps.append("No price history is available for market trend analysis.")

    if price_history_span_days >= 365:
        evidence_score += 10
    elif price_history_span_days >= 180:
        evidence_score += 7
        data_gaps.append("Price history window is shorter than a full year, so momentum needs caution.")
    elif price_points > 1:
        evidence_score += 4
        data_gaps.append("Price history window is short, which weakens appreciation confidence.")

    if latest_price_age_days is not None:
        if latest_price_age_days <= 270:
            evidence_score += 5
        elif latest_price_age_days <= 540:
            evidence_score += 3
            data_gaps.append("Latest pricing signal is aging and may lag current market conditions.")
        elif latest_price_age_days <= 730:
            evidence_score += 1
            data_gaps.append("Latest pricing signal is stale, reducing market-timing accuracy.")
        else:
            data_gaps.append("Latest pricing signal is materially stale and should not drive strong conviction.")

    if census:
        evidence_score += 10
    else:
        data_gaps.append("Missing census coverage weakens demand and density modelling.")

    if geo_profile:
        evidence_score += 15
    else:
        data_gaps.append("Missing geo profile coverage weakens terrain, flood, and climate accuracy.")

    nearby_infra_count = len(nearby_infra)
    if nearby_infra_count >= 5:
        evidence_score += 10
    elif nearby_infra_count >= 2:
        evidence_score += 7
    elif nearby_infra_count == 1:
        evidence_score += 4
        data_gaps.append("Nearby infrastructure context is thin for corridor analysis.")
    else:
        data_gaps.append("No nearby infrastructure evidence is available for corridor analysis.")

    regional_standard_count = len(regional_standards)
    if regional_standard_count >= 2:
        evidence_score += 10
    elif regional_standard_count == 1:
        evidence_score += 5
        data_gaps.append("Regional standards coverage is partial, so bylaw certainty is limited.")
    else:
        data_gaps.append("No regional standards or bylaw coverage is attached to this location.")

    evidence_score = round(min(100.0, evidence_score), 2)
    confidence_band = _coverage_band(evidence_score)
    score_calibration_factor = _confidence_calibration_factor(evidence_score)

    deduped_gaps: list[str] = []
    for gap in data_gaps:
        if gap not in deduped_gaps:
            deduped_gaps.append(gap)
        if len(deduped_gaps) >= 5:
            break

    return {
        "evidence_score": evidence_score,
        "confidence_band": confidence_band,
        "score_calibration_factor": score_calibration_factor,
        "data_gaps": deduped_gaps,
        "masterplan_present": masterplan is not None,
        "masterplan_history_count": len(masterplan_history),
        "price_history_points": price_points,
        "price_history_span_days": price_history_span_days,
        "latest_price_age_days": latest_price_age_days,
        "census_present": census is not None,
        "geo_profile_present": geo_profile is not None,
        "nearby_infra_count": nearby_infra_count,
        "regional_standard_count": regional_standard_count,
    }


def _corridor_band(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 75:
        return "strong"
    if score >= 55:
        return "selective"
    return "limited"


def _upside_band(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 75:
        return "high"
    if score >= 60:
        return "moderate"
    if score >= 45:
        return "selective"
    return "constrained"


def _land_value_band(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 80:
        return "prime"
    if score >= 65:
        return "strong"
    if score >= 45:
        return "selective"
    return "discounted"


def _development_potential_band(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 80:
        return "high_capacity"
    if score >= 65:
        return "strong"
    if score >= 45:
        return "selective"
    return "limited"


def _build_core_summary(
    *,
    recommended_use_case: str,
    favorability_band: str,
    future_appreciation_index: float,
    price_momentum_band: str | None,
    demand_profile: str | None,
    site_risk_band: str | None,
    strategic_infra_score: float,
) -> str:
    use_case_label = recommended_use_case.replace("_", " ")
    corridor_strength = _corridor_band(strategic_infra_score)
    upside = _upside_band(future_appreciation_index)
    momentum = price_momentum_band or "steady"
    demand = demand_profile or "balanced"
    risk = site_risk_band or "managed"
    return (
        f"{favorability_band.title()} {use_case_label} fit with {upside} upside, "
        f"{momentum} price momentum, {demand} demand, {corridor_strength} corridor access, "
        f"and {risk} site risk."
    )


def _read_value(source, key: str, default=None):
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _safe_price_prediction(session: Session | None, location_id: int):
    if session is None:
        return None
    try:
        return predict_price_for_location(session, location_id)
    except Exception:
        logger.exception("Price prediction failed while building key insight for location %s", location_id)
        return None


def _safe_hotspot_context(session: Session | None, location_id: int):
    if session is None:
        return None
    try:
        from brain.valuation.ml.hotspot_detector import HotspotDetector

        for hotspot in HotspotDetector(n_clusters=4).detect(session):
            for member in _read_value(hotspot, "locations", []) or []:
                if _read_value(member, "location_id") == location_id:
                    return hotspot
    except Exception:
        logger.exception("Hotspot detection failed while building key insight for location %s", location_id)
    return None


def _build_key_insight(profile: dict, logic: dict, *, price_prediction=None, hotspot=None) -> str:
    use_case = profile.get("recommended_use_case", "residential").replace("_", " ")
    weighted_score = _to_float(logic.get("weighted_score"))
    investment_signal = logic.get("investment_signal", "watch")
    gating_issue = logic.get("gating_issue")
    primary_driver = logic.get("primary_driver", "balanced_signals").replace("_", " ")
    data_confidence_band = logic.get("data_confidence_band") or profile.get("inputs", {}).get("coverage", {}).get("confidence_band", "medium")

    upside_pct = _to_float(_read_value(price_prediction, "predicted_upside_pct"), None)
    hotspot_label = _read_value(hotspot, "label")

    if gating_issue:
        gate = gating_issue.replace("_", " ")
        if upside_pct is not None and upside_pct >= 5:
            return (
                f"{gate.title()} is the main blocker: the parcel still shows {upside_pct:.1f}% projected 1Y upside, "
                f"but that upside should not be underwritten until the gate is cleared."
            )
        return f"{gate.title()} is the main blocker before leaning into this {use_case} thesis."

    if hotspot_label == "undervalued" and upside_pct is not None and upside_pct >= 5:
        return (
            f"This parcel looks undervalued inside its cluster, with {upside_pct:.1f}% projected 1Y upside "
            f"supporting an {investment_signal} case."
        )

    if hotspot_label in {"emerging", "high_growth"} and investment_signal in {"acquire", "accumulate"}:
        if upside_pct is not None:
            return (
                f"Future upside is the lead signal: the parcel sits in an {hotspot_label.replace('_', ' ')} hotspot "
                f"with {upside_pct:.1f}% projected 1Y upside and a strong {use_case} fit."
            )
        return (
            f"Future upside is the lead signal: the parcel sits in an {hotspot_label.replace('_', ' ')} hotspot "
            f"and remains well-positioned for {use_case}."
        )

    if investment_signal in {"acquire", "accumulate"} and upside_pct is not None and upside_pct >= 8:
        return (
            f"Weighted score and ML outlook are aligned: the parcel carries a {weighted_score:.1f} weighted score "
            f"with {upside_pct:.1f}% projected 1Y upside."
        )

    if data_confidence_band == "low":
        return (
            f"The signal is directionally positive, but the evidence base is still thin, so this remains a "
            f"{investment_signal} thesis led by {primary_driver}."
        )

    return (
        f"The clearest signal is {primary_driver}, which keeps the parcel in a {investment_signal} stance "
        f"for {use_case}."
    )


def _build_forward_outlook(price_prediction) -> dict | None:
    if not price_prediction:
        return None

    signal = _read_value(price_prediction, "signal", "neutral")
    current_avg_price = round(_to_float(_read_value(price_prediction, "current_avg_price")), 2)
    predicted_price_1yr = round(_to_float(_read_value(price_prediction, "predicted_price_1yr")), 2)
    predicted_price_3yr = round(_to_float(_read_value(price_prediction, "predicted_price_3yr")), 2)
    predicted_upside_pct = round(_to_float(_read_value(price_prediction, "predicted_upside_pct")), 2)
    annual_growth_pct = round(_to_float(_read_value(price_prediction, "annual_growth_pct")), 2)
    confidence = _read_value(price_prediction, "confidence")
    model_version = _read_value(price_prediction, "model_version")
    drivers = []
    for driver in (_read_value(price_prediction, "drivers", []) or [])[:2]:
        drivers.append({
            "key": _read_value(driver, "key"),
            "label": _read_value(driver, "label"),
            "value": round(_to_float(_read_value(driver, "value")), 2),
            "contribution": round(_to_float(_read_value(driver, "contribution")), 4),
            "direction": _read_value(driver, "direction"),
        })

    return {
        "current_avg_price": current_avg_price,
        "predicted_price_1yr": predicted_price_1yr,
        "predicted_price_3yr": predicted_price_3yr,
        "predicted_upside_pct": predicted_upside_pct,
        "annual_growth_pct": annual_growth_pct,
        "signal": signal,
        "confidence": confidence,
        "model_version": model_version,
        "summary": (
            f"Forward view: price is projected from {current_avg_price:.2f} to {predicted_price_1yr:.2f} in 1Y "
            f"({predicted_upside_pct:+.2f}%), with a {signal} signal."
        ),
        "drivers": drivers,
    }


def _build_land_value_output(valuation: dict, inputs: dict) -> dict:
    components = valuation.get("components", {})
    market = inputs.get("market", {})
    planning = inputs.get("planning", {})
    infrastructure = inputs.get("infrastructure", {})

    score = round(_to_float(valuation.get("land_value_score")), 2)
    band = _land_value_band(score)
    zoning_type = planning.get("zoning_type") or "current"
    price_momentum_band = market.get("price_momentum_band") or "steady"
    corridor_band = _corridor_band(
        _to_float(
            infrastructure.get("strategic_infra_score"),
            _to_float(components.get("infra_score"), 50.0),
        )
    )

    return {
        "score": score,
        "band": band,
        "summary": (
            f"{band.title()} land value with {zoning_type} zoning support, "
            f"{price_momentum_band} pricing, and {corridor_band} access."
        ),
        "drivers": [
            {
                "key": "avg_price_per_sqft",
                "label": "Avg Price / sqft",
                "value": _to_float(components.get("avg_price_per_sqft"), _to_float(market.get("avg_price_per_sqft"), None)),
            },
            {
                "key": "infra_score",
                "label": "Infra Proximity",
                "value": _to_float(components.get("infra_score"), None),
            },
            {
                "key": "zoning_favorability",
                "label": "Zoning Favorability",
                "value": _to_float(components.get("zoning_favorability"), None),
            },
            {
                "key": "density_score",
                "label": "Density Score",
                "value": _to_float(components.get("density_score"), None),
            },
            {
                "key": "price_trend_score",
                "label": "Price Trend Score",
                "value": _to_float(components.get("price_trend_score"), None),
            },
        ],
    }


def _build_development_potential_output(valuation: dict, inputs: dict) -> dict:
    components = valuation.get("components", {})
    planning = inputs.get("planning", {})
    infrastructure = inputs.get("infrastructure", {})

    score = round(_to_float(valuation.get("development_potential_score")), 2)
    band = _development_potential_band(score)
    zoning_type = planning.get("zoning_type") or "current"
    planned_infra_count = int(_to_float(infrastructure.get("planned_infra_count"), 0) or 0)
    corridor_band = _corridor_band(
        _to_float(infrastructure.get("strategic_infra_score"), 50.0)
    )

    return {
        "score": score,
        "band": band,
        "summary": (
            f"{band.replace('_', ' ').title()} development potential with {zoning_type} zoning, "
            f"{planned_infra_count} planned infra catalysts, and {corridor_band} access support."
        ),
        "drivers": [
            {
                "key": "fsi",
                "label": "FSI",
                "value": _to_float(planning.get("fsi"), None),
            },
            {
                "key": "max_height_m",
                "label": "Max Height (m)",
                "value": _to_float(planning.get("max_height_m"), None),
            },
            {
                "key": "ground_coverage_pct",
                "label": "Ground Coverage %",
                "value": _to_float(planning.get("ground_coverage_pct"), None),
            },
            {
                "key": "planned_infra_count",
                "label": "Planned Infra Count",
                "value": _to_float(infrastructure.get("planned_infra_count"), None),
            },
            {
                "key": "price_trend_score",
                "label": "Price Trend Score",
                "value": _to_float(components.get("price_trend_score"), None),
            },
        ],
    }


def _build_future_appreciation_output(valuation: dict, inputs: dict) -> dict:
    components = valuation.get("components", {})
    market = inputs.get("market", {})
    demand = inputs.get("demand", {})
    planning = inputs.get("planning", {})
    infrastructure = inputs.get("infrastructure", {})

    score = round(_to_float(valuation.get("future_appreciation_index")), 2)
    band = _upside_band(score)
    price_trend_direction = market.get("price_trend_direction") or "flat"
    demand_profile = demand.get("demand_profile") or "balanced"
    zoning_shift_direction = planning.get("zoning_shift_direction") or "stable"
    planned_infra_count = int(_to_float(infrastructure.get("planned_infra_count"), 0) or 0)

    return {
        "score": score,
        "band": band,
        "summary": (
            f"{band.title()} appreciation outlook with {price_trend_direction} pricing, "
            f"{demand_profile} demand, {zoning_shift_direction} zoning movement, "
            f"and {planned_infra_count} planned infra catalysts."
        ),
        "drivers": [
            {
                "key": "price_trend_score",
                "label": "Price Trend Score",
                "value": _to_float(components.get("price_trend_score"), None),
            },
            {
                "key": "annualized_growth_pct",
                "label": "Annualized Growth %",
                "value": _to_float(components.get("annualized_growth_pct"), _to_float(market.get("annualized_growth_pct"), None)),
            },
            {
                "key": "recent_12m_growth_pct",
                "label": "Recent 12M Growth %",
                "value": _to_float(components.get("recent_12m_growth_pct"), _to_float(market.get("recent_12m_growth_pct"), None)),
            },
            {
                "key": "demand_pressure_score",
                "label": "Demand Pressure",
                "value": _to_float(components.get("demand_pressure_score"), _to_float(demand.get("demand_pressure_score"), None)),
            },
            {
                "key": "zoning_shift_score",
                "label": "Zoning Shift Score",
                "value": _to_float(components.get("zoning_shift_score"), _to_float(planning.get("zoning_shift_score"), None)),
            },
            {
                "key": "planned_infra_count",
                "label": "Planned Infra Count",
                "value": _to_float(infrastructure.get("planned_infra_count"), None),
            },
        ],
    }


def _logic_rule(code: str, effect: str, detail: str) -> dict:
    return {
        "code": code,
        "effect": effect,
        "detail": detail,
    }


def _logic_weighted_band(score: float) -> str:
    if score >= 80:
        return "compelling"
    if score >= 67:
        return "strong"
    if score >= 52:
        return "selective"
    return "weak"


def _logic_signal_from_weighted_score(score: float) -> str:
    if score >= 80:
        return "acquire"
    if score >= 67:
        return "accumulate"
    if score >= 52:
        return "watch"
    return "avoid"


def _downgrade_investment_signal(signal: str) -> str:
    return {
        "acquire": "accumulate",
        "accumulate": "watch",
        "watch": "avoid",
        "avoid": "avoid",
    }.get(signal, "avoid")


def _build_logic_output(profile: dict) -> dict:
    valuation = profile["valuation"]
    inputs = profile["inputs"]
    components = profile["components"]
    coverage = inputs.get("coverage", {})

    land_value_score = _to_float(valuation.get("land_value_score"))
    development_potential_score = _to_float(valuation.get("development_potential_score"))
    future_appreciation_index = _to_float(valuation.get("future_appreciation_index"))

    regulatory_clarity_score = _to_float(components.get("regulatory_clarity_score"), 50.0)
    site_risk_score = _to_float(components.get("site_risk_score"), 50.0)
    site_readiness_score = _to_float(components.get("site_readiness_score"), 50.0)
    data_confidence_score = _to_float(coverage.get("evidence_score"), 50.0)
    data_confidence_band = coverage.get("confidence_band") or _coverage_band(data_confidence_score)
    zoning_shift_direction = inputs["planning"].get("zoning_shift_direction")

    weighted_components = [
        {
            "key": "land_value_score",
            "label": "Land Value Score",
            "value": round(land_value_score, 2),
            "weight": 0.30,
            "contribution": round(land_value_score * 0.30, 2),
        },
        {
            "key": "development_potential_score",
            "label": "Development Potential Score",
            "value": round(development_potential_score, 2),
            "weight": 0.30,
            "contribution": round(development_potential_score * 0.30, 2),
        },
        {
            "key": "future_appreciation_index",
            "label": "Future Appreciation Index",
            "value": round(future_appreciation_index, 2),
            "weight": 0.40,
            "contribution": round(future_appreciation_index * 0.40, 2),
        },
    ]
    weighted_score = round(sum(item["contribution"] for item in weighted_components), 2)
    weighted_band = _logic_weighted_band(weighted_score)

    rule_hits: list[dict] = []

    def add_hit(code: str, effect: str, detail: str) -> None:
        rule_hits.append(_logic_rule(code, effect, detail))

    if weighted_score >= 80:
        add_hit("weighted_strength", "positive", "Weighted core score is strong enough to support an immediate acquisition stance.")
    elif weighted_score >= 67:
        add_hit("weighted_strength", "positive", "Weighted core score supports a qualified accumulation thesis.")
    elif weighted_score >= 52:
        add_hit("weighted_watchlist", "neutral", "Weighted core score is solid enough to stay on the watchlist, but not yet a commit.")

    if development_potential_score >= 75 and site_readiness_score >= 70:
        add_hit("build_ready", "positive", "Strong development headroom and execution readiness support near-term buildability.")
    if future_appreciation_index >= 70:
        add_hit("future_upside", "positive", "Future appreciation is strong enough to justify an upside-led thesis.")
    if land_value_score >= 70:
        add_hit("current_value_strength", "positive", "Current land value already clears a healthy baseline.")
    if zoning_shift_direction == "upzoned":
        add_hit("planning_tailwind", "positive", "Recent zoning improvement supports a stronger forward case.")

    if site_risk_score >= 60:
        add_hit("site_risk", "negative", "Terrain and climate risk are high enough to materially affect execution and returns.")
    if regulatory_clarity_score < 55:
        add_hit("regulatory_drag", "negative", "Regulatory clarity is too weak for a clean commit at current confidence.")
    if data_confidence_score < 60:
        add_hit("thin_evidence", "negative", "Underlying data coverage is too thin for a high-conviction investment call.")

    site_risk_gate = site_risk_score >= 60
    regulatory_gate = regulatory_clarity_score < 55
    data_coverage_gate = data_confidence_score < 60
    severe_site_risk = site_risk_score >= 70
    severe_regulatory_drag = regulatory_clarity_score < 45
    severe_data_gap = data_confidence_score < 45

    base_signal = _logic_signal_from_weighted_score(weighted_score)
    if severe_site_risk or severe_regulatory_drag:
        investment_signal = "avoid"
    elif severe_data_gap:
        investment_signal = _downgrade_investment_signal(_downgrade_investment_signal(base_signal))
    elif site_risk_gate or regulatory_gate or data_coverage_gate:
        investment_signal = _downgrade_investment_signal(base_signal)
    else:
        investment_signal = base_signal

    if site_risk_gate or regulatory_gate:
        execution_strategy = "de_risk_first"
    elif data_coverage_gate:
        execution_strategy = "monitor"
    elif development_potential_score >= 75 and site_readiness_score >= 70 and weighted_score >= 67:
        execution_strategy = "build_now"
    elif future_appreciation_index >= 70 and zoning_shift_direction in {"upzoned", "rebalanced"}:
        execution_strategy = "entitle_then_build"
    elif weighted_score >= 60 and future_appreciation_index >= 65:
        execution_strategy = "land_bank"
    else:
        execution_strategy = "monitor"

    gating_issue = None
    if site_risk_gate:
        gating_issue = "site_risk"
    elif regulatory_gate:
        gating_issue = "regulatory_clarity"
    elif data_coverage_gate:
        gating_issue = "data_coverage"

    primary_driver = {
        "future_appreciation_index": "future_upside",
        "development_potential_score": "development_headroom",
        "land_value_score": "current_land_value",
    }.get(
        max(weighted_components, key=lambda item: item["contribution"])["key"],
        "balanced_signals",
    )

    positive_hits = sum(1 for hit in rule_hits if hit["effect"] == "positive")

    if investment_signal == "avoid" or severe_site_risk or severe_regulatory_drag or severe_data_gap:
        conviction = "low"
    elif gating_issue is None and weighted_score >= 75 and positive_hits >= 2 and data_confidence_score >= 80:
        conviction = "high"
    else:
        conviction = "medium"

    verdict = (
        f"{investment_signal.replace('_', ' ').title()} signal on a {weighted_band} weighted score of {weighted_score:.2f} "
        f"with {conviction} conviction and {data_confidence_band} data confidence. "
        f"{execution_strategy.replace('_', ' ').title()} is the current strategy."
    )
    if gating_issue:
        verdict = f"{verdict} Gate: {gating_issue.replace('_', ' ')}."

    return {
        "weighted_score": weighted_score,
        "weighted_band": weighted_band,
        "investment_signal": investment_signal,
        "execution_strategy": execution_strategy,
        "conviction": conviction,
        "data_confidence_score": round(data_confidence_score, 2),
        "data_confidence_band": data_confidence_band,
        "primary_driver": primary_driver,
        "gating_issue": gating_issue,
        "verdict": verdict,
        "weighted_components": weighted_components,
        "rule_hits": rule_hits,
    }


def _trim_tags(values: list[str], *, limit: int = 3) -> list[str]:
    seen: list[str] = []
    for value in values:
        if value and value not in seen:
            seen.append(value)
        if len(seen) >= limit:
            break
    return seen


def _build_favorability_tags(
    *,
    recommended_use_case: str,
    overall_favorability_score: float,
    market_momentum_score: float,
    site_readiness_score: float,
    regulatory_clarity_score: float,
    mobility_score: float,
    strategic_infra_score: float,
    climate_resilience_score: float,
    terrain_readiness_score: float,
    site_risk_score: float,
    demand_pressure_score: float,
    development_potential_score: float,
    future_appreciation_index: float,
    zoning_type: str | None,
    market_tier: str | None,
) -> tuple[list[str], list[str], list[str]]:
    strengths: list[str] = []
    risks: list[str] = []
    opportunities: list[str] = []

    if market_momentum_score >= 70:
        strengths.append("Strong market momentum supports value retention and upside.")
    if site_readiness_score >= 70:
        strengths.append("Site readiness is high for near-term development execution.")
    if regulatory_clarity_score >= 70:
        strengths.append("Planning and standards context is relatively clear.")
    if mobility_score >= 70:
        strengths.append("Transport and access profile is a meaningful advantage.")
    if strategic_infra_score >= 70:
        strengths.append("Road, metro, and economic access create a strong infra corridor signal.")
    if site_risk_score <= 35:
        strengths.append("Terrain and climate exposure look relatively contained for delivery.")
    if demand_pressure_score >= 70:
        strengths.append("Population growth and density support strong demand absorption.")
    if overall_favorability_score >= 75:
        strengths.append("Overall site favorability is in the prime band.")

    if climate_resilience_score < 45:
        risks.append("Climate exposure is elevated and could pressure build economics.")
    if terrain_readiness_score < 55:
        risks.append("Terrain conditions may increase design and construction complexity.")
    if site_risk_score >= 60:
        risks.append("Combined terrain and climate risk is material enough to affect upside.")
    if regulatory_clarity_score < 55:
        risks.append("Regulatory clarity is still weak and needs diligence before commitment.")
    if mobility_score < 50:
        risks.append("Access and mobility are not yet strong enough for easy absorption.")
    if strategic_infra_score < 45:
        risks.append("Road, metro, and economic-zone access remain too weak for a strong corridor thesis.")
    if demand_pressure_score < 45:
        risks.append("Demand depth looks thin on current population-growth and density signals.")
    if zoning_type in {None, "industrial"} and recommended_use_case == "residential":
        risks.append("Current zoning signal is not naturally aligned with residential positioning.")

    if development_potential_score >= 70:
        opportunities.append("Development headroom is strong enough to support ambitious programs.")
    if future_appreciation_index >= 70:
        opportunities.append("Forward appreciation signal is above market baseline.")
    if strategic_infra_score >= 70:
        opportunities.append("Infra proximity supports corridor-led value expansion.")
    if site_risk_score <= 35:
        opportunities.append("Contained site risk supports cleaner execution economics.")
    if demand_pressure_score >= 70:
        opportunities.append("Demand pressure indicates strong absorption potential.")
    if recommended_use_case == "mixed_use":
        opportunities.append("Mixed-use appears to be the strongest fit for this site.")
    elif recommended_use_case == "commercial":
        opportunities.append("Commercial program alignment looks strongest here.")
    elif recommended_use_case == "industrial":
        opportunities.append("Industrial deployment has the cleanest fit with current signals.")
    else:
        opportunities.append("Residential delivery appears to have the clearest fit.")

    if market_tier == "premium":
        opportunities.append("Premium market tier supports higher-spec product positioning.")
    elif market_tier == "emerging":
        opportunities.append("Emerging market tier leaves room for re-rating if infra catches up.")

    return (
        _trim_tags(strengths),
        _trim_tags(risks),
        _trim_tags(opportunities),
    )


def _canonical_zoning_type(zoning_type: str | None) -> str | None:
    if zoning_type is None:
        return None
    normalized = zoning_type.strip().lower().replace("-", "_")
    aliases = {
        "mixed_use": "mixed",
        "mixeduse": "mixed",
    }
    return aliases.get(normalized, normalized) or None


def _masterplan_history_sort_key(masterplan) -> tuple[str, str, int]:
    effective_from = getattr(masterplan, "effective_from", None)
    created_at = getattr(masterplan, "created_at", None)
    return (
        effective_from.isoformat() if effective_from else "",
        created_at.isoformat() if created_at else "",
        int(getattr(masterplan, "id", 0) or 0),
    )


def _build_masterplan_shift_snapshot(masterplan, masterplan_history: list | None) -> dict:
    ordered_history = sorted(masterplan_history or [], key=_masterplan_history_sort_key)
    current_zone = _canonical_zoning_type(getattr(masterplan, "zoning_type", None) if masterplan else None)
    if current_zone is None and ordered_history:
        current_zone = _canonical_zoning_type(getattr(ordered_history[-1], "zoning_type", None))

    normalized_history: list[tuple[object, str]] = []
    for item in ordered_history:
        zone = _canonical_zoning_type(getattr(item, "zoning_type", None))
        if zone:
            normalized_history.append((item, zone))

    previous_zone = None
    latest_entry = normalized_history[-1][0] if normalized_history else None
    shift_effective_from = (
        latest_entry.effective_from.isoformat()
        if latest_entry and getattr(latest_entry, "effective_from", None)
        else None
    )
    if current_zone:
        for item, zone in reversed(normalized_history[:-1]):
            if zone != current_zone:
                previous_zone = zone
                break

    zoning_shift_score = round(
        compute_masterplan_zoning_shift_score(
            ordered_history,
            zoning_type=current_zone,
        ),
        2,
    )
    if previous_zone is None:
        direction = "stable"
    elif zoning_shift_score >= 80:
        direction = "upzoned"
    elif zoning_shift_score <= 45:
        direction = "downzoned"
    else:
        direction = "rebalanced"

    summary = f"{previous_zone} -> {current_zone}" if previous_zone and current_zone else current_zone

    return {
        "masterplan_version": getattr(masterplan, "version", None) if masterplan else None,
        "masterplan_history_count": len(ordered_history),
        "previous_zoning_type": previous_zone,
        "zoning_shift_direction": direction,
        "zoning_shift_summary": summary,
        "zoning_shift_effective_from": shift_effective_from,
        "zoning_shift_score": zoning_shift_score,
    }


def _price_history_metrics(prices: list) -> tuple[float | None, float | None, float | None, int]:
    if not prices:
        return None, None, None, 0

    ordered_prices = sorted(prices, key=lambda price: price.recorded_date)
    oldest_price = _to_float(getattr(ordered_prices[0], "price_per_sqft", None), None)
    latest_price = _to_float(getattr(ordered_prices[-1], "price_per_sqft", None), None)

    price_growth_pct = None
    if oldest_price not in {None, 0} and latest_price is not None:
        price_growth_pct = round(((latest_price - oldest_price) / oldest_price) * 100, 2)

    return oldest_price, latest_price, price_growth_pct, len(ordered_prices)


def _build_price_trend_snapshot(prices: list, *, price_trend_score: float | None = None) -> dict:
    if not prices:
        return {
            "oldest_price_per_sqft": None,
            "latest_price_per_sqft": None,
            "price_growth_pct": None,
            "annualized_growth_pct": None,
            "recent_12m_growth_pct": None,
            "first_recorded_date": None,
            "latest_recorded_date": None,
            "price_history_span_days": 0,
            "price_history_points": 0,
            "price_trend_direction": "unknown",
            "price_momentum_band": _price_momentum_band(price_trend_score),
        }

    ordered_prices = sorted(prices, key=lambda price: price.recorded_date)
    oldest = ordered_prices[0]
    latest = ordered_prices[-1]
    oldest_price = _to_float(getattr(oldest, "price_per_sqft", None), None)
    latest_price = _to_float(getattr(latest, "price_per_sqft", None), None)
    first_recorded_date = getattr(oldest, "recorded_date", None)
    latest_recorded_date = getattr(latest, "recorded_date", None)
    price_history_span_days = (
        max(0, (latest_recorded_date - first_recorded_date).days)
        if first_recorded_date and latest_recorded_date
        else 0
    )

    price_growth_pct = None
    if oldest_price not in {None, 0} and latest_price is not None:
        price_growth_pct = round(((latest_price - oldest_price) / oldest_price) * 100, 2)

    annualized_growth_pct = None
    if oldest_price not in {None, 0} and latest_price is not None and price_history_span_days > 0:
        annualized_growth_pct = round(
            (((latest_price / oldest_price) ** (365 / price_history_span_days)) - 1) * 100,
            2,
        )

    recent_12m_growth_pct = None
    if latest_recorded_date and len(ordered_prices) > 1:
        trailing_cutoff = latest_recorded_date - timedelta(days=365)
        baseline = next(
            (
                price
                for price in reversed(ordered_prices[:-1])
                if getattr(price, "recorded_date", None) and price.recorded_date <= trailing_cutoff
            ),
            None,
        )
        if baseline is not None:
            baseline_price = _to_float(getattr(baseline, "price_per_sqft", None), None)
            if baseline_price not in {None, 0} and latest_price is not None:
                recent_12m_growth_pct = round(((latest_price - baseline_price) / baseline_price) * 100, 2)

    trend_basis = recent_12m_growth_pct if recent_12m_growth_pct is not None else price_growth_pct
    if trend_basis is None:
        price_trend_direction = "unknown"
    elif trend_basis >= 18:
        price_trend_direction = "surging"
    elif trend_basis >= 5:
        price_trend_direction = "rising"
    elif trend_basis <= -8:
        price_trend_direction = "declining"
    else:
        price_trend_direction = "flat"

    return {
        "oldest_price_per_sqft": oldest_price,
        "latest_price_per_sqft": latest_price,
        "price_growth_pct": price_growth_pct,
        "annualized_growth_pct": annualized_growth_pct,
        "recent_12m_growth_pct": recent_12m_growth_pct,
        "first_recorded_date": first_recorded_date.isoformat() if first_recorded_date else None,
        "latest_recorded_date": latest_recorded_date.isoformat() if latest_recorded_date else None,
        "price_history_span_days": price_history_span_days,
        "price_history_points": len(ordered_prices),
        "price_trend_direction": price_trend_direction,
        "price_momentum_band": _price_momentum_band(price_trend_score),
    }


def _build_valuation_input_snapshot(summary: dict, *, planning_context, valuation: dict | None) -> dict:
    masterplan = summary["masterplan"]
    masterplan_history = summary.get("masterplan_history") or ([masterplan] if masterplan else [])
    prices = summary["price_history"]
    census = summary["census"]
    geo_profile = summary.get("geo_profile")
    nearby_infra = summary["nearby_infrastructure"]
    regional_standards = summary.get("regional_standards", [])

    components = valuation.get("components", {}) if valuation else {}
    coverage = _build_data_coverage_snapshot(summary)
    price_trend_score = _to_float(components.get("price_trend_score"), None)
    if price_trend_score is None:
        price_trend_score = round(compute_price_trend(prices), 2)
    price_trend = _build_price_trend_snapshot(prices, price_trend_score=price_trend_score)
    zoning_shift = _build_masterplan_shift_snapshot(masterplan, masterplan_history)
    population_growth_pct = _to_float(getattr(census, "growth_rate_pct", None), None) if census else None
    density_score = _to_float(components.get("density_score"), None)
    if density_score is None:
        density_score = round(compute_density_score(census), 2)
    population_growth_score = _to_float(components.get("population_growth_score"), None)
    if population_growth_score is None:
        population_growth_score = round(compute_population_growth_score(population_growth_pct), 2)
    demand_pressure_score = _to_float(components.get("demand_pressure_score"), None)
    if demand_pressure_score is None:
        demand_pressure_score = round(compute_demand_pressure_score(population_growth_pct, density_score), 2)
    infra_proximity = compute_infra_proximity_profile(nearby_infra, geo_profile)
    climate_exposure_score = _to_float(components.get("climate_exposure_score"), None)
    if climate_exposure_score is None:
        climate_exposure_score = round(compute_climate_exposure_score(geo_profile), 2)
    terrain_constraint_score = _to_float(components.get("terrain_constraint_score"), None)
    if terrain_constraint_score is None:
        terrain_constraint_score = round(compute_terrain_constraint_score(geo_profile), 2)
    site_risk_score = _to_float(components.get("site_risk_score"), None)
    if site_risk_score is None:
        site_risk_score = round(compute_site_risk_score(geo_profile), 2)

    planned_statuses = {"planned", "under_construction"}
    transit_node_types = {"metro_station", "railway_station"}
    planned_infra_count = sum(
        1
        for item in nearby_infra
        if item["infrastructure"].status in planned_statuses
    )
    transit_node_count = sum(
        1
        for item in nearby_infra
        if item["infrastructure"].infra_type in transit_node_types
    )
    nearest_infra_km = round(min((float(item["distance_km"]) for item in nearby_infra), default=0.0), 2) if nearby_infra else None
    nearest_transit_node_km = round(
        min(
            (
                float(item["distance_km"])
                for item in nearby_infra
                if item["infrastructure"].infra_type in transit_node_types
            ),
            default=0.0,
        ),
        2,
    ) if transit_node_count else None

    dominant_types: list[str] = []
    for item in sorted(nearby_infra, key=lambda row: float(row["distance_km"])):
        infra_type = item["infrastructure"].infra_type
        if infra_type not in dominant_types:
            dominant_types.append(infra_type)
        if len(dominant_types) >= 5:
            break

    return {
        "coverage": coverage,
        "market": {
            "avg_price_per_sqft": _to_float(summary.get("avg_price_per_sqft"), None),
            "oldest_price_per_sqft": price_trend["oldest_price_per_sqft"],
            "latest_price_per_sqft": price_trend["latest_price_per_sqft"],
            "price_growth_pct": price_trend["price_growth_pct"],
            "annualized_growth_pct": price_trend["annualized_growth_pct"],
            "recent_12m_growth_pct": price_trend["recent_12m_growth_pct"],
            "first_recorded_date": price_trend["first_recorded_date"],
            "latest_recorded_date": price_trend["latest_recorded_date"],
            "price_history_span_days": price_trend["price_history_span_days"],
            "price_history_points": price_trend["price_history_points"],
            "price_trend_direction": price_trend["price_trend_direction"],
            "price_momentum_band": price_trend["price_momentum_band"],
        },
        "planning": {
            "zoning_type": masterplan.zoning_type if masterplan else None,
            "approval_status": getattr(masterplan, "approval_status", None) if masterplan else None,
            "fsi": _to_float(getattr(masterplan, "fsi", None), None) if masterplan else None,
            "max_height_m": _to_float(getattr(masterplan, "max_height_m", None), None) if masterplan else None,
            "ground_coverage_pct": _to_float(getattr(masterplan, "ground_coverage_pct", None), None) if masterplan else None,
            "masterplan_version": zoning_shift["masterplan_version"],
            "masterplan_history_count": zoning_shift["masterplan_history_count"],
            "previous_zoning_type": zoning_shift["previous_zoning_type"],
            "zoning_shift_direction": zoning_shift["zoning_shift_direction"],
            "zoning_shift_summary": zoning_shift["zoning_shift_summary"],
            "zoning_shift_effective_from": zoning_shift["zoning_shift_effective_from"],
            "zoning_shift_score": zoning_shift["zoning_shift_score"],
            "market_tier": getattr(planning_context, "market_tier", None),
            "validation_status": getattr(planning_context, "validation_status", None),
            "planning_context_version": getattr(planning_context, "version_tag", None),
            "location_intelligence_score": _to_float(
                getattr(planning_context, "location_intelligence_score", None),
                None,
            ),
            "regional_standard_codes": [standard.code for standard in regional_standards],
        },
        "demand": {
            "population": getattr(census, "population", None) if census else None,
            "growth_rate_pct": population_growth_pct,
            "density_per_sqkm": _to_float(getattr(census, "density_per_sqkm", None), None) if census else None,
            "density_score": density_score,
            "population_growth_score": population_growth_score,
            "demand_pressure_score": demand_pressure_score,
            "demand_profile": _demand_profile(demand_pressure_score),
        },
        "infrastructure": {
            "nearby_infra_count": len(nearby_infra),
            "planned_infra_count": planned_infra_count,
            "transit_node_count": transit_node_count,
            "nearest_infra_km": nearest_infra_km,
            "nearest_transit_node_km": nearest_transit_node_km,
            "road_proximity_km": infra_proximity["road_proximity_km"],
            "metro_proximity_km": infra_proximity["metro_proximity_km"],
            "economic_zone_proximity_km": infra_proximity["economic_zone_proximity_km"],
            "road_access_score": infra_proximity["road_access_score"],
            "metro_access_score": infra_proximity["metro_access_score"],
            "economic_access_score": infra_proximity["economic_access_score"],
            "strategic_infra_score": infra_proximity["strategic_infra_score"],
            "metro_station_count": infra_proximity["metro_station_count"],
            "economic_zone_count": infra_proximity["economic_zone_count"],
            "highway_count": infra_proximity["highway_count"],
            "dominant_types": dominant_types,
        },
        "site": {
            "terrain_class": getattr(geo_profile, "terrain_class", None) if geo_profile else None,
            "terrain_slope_pct": _to_float(getattr(geo_profile, "terrain_slope_pct", None), None) if geo_profile else None,
            "road_proximity_km": _to_float(getattr(geo_profile, "road_proximity_km", None), None) if geo_profile else None,
            "transit_proximity_km": _to_float(getattr(geo_profile, "transit_proximity_km", None), None) if geo_profile else None,
            "flood_risk_score": _to_float(getattr(geo_profile, "flood_risk_score", None), None) if geo_profile else None,
            "heat_risk_score": _to_float(getattr(geo_profile, "heat_risk_score", None), None) if geo_profile else None,
            "climate_risk_score": _to_float(getattr(geo_profile, "climate_risk_score", None), None) if geo_profile else None,
            "climate_exposure_score": climate_exposure_score,
            "terrain_constraint_score": terrain_constraint_score,
            "site_risk_score": site_risk_score,
            "site_risk_band": _site_risk_band(site_risk_score),
        },
        "model_inputs": {
            "infra_score": _to_float(components.get("infra_score"), None),
            "price_trend_score": price_trend_score,
            "zoning_favorability": _to_float(components.get("zoning_favorability"), None),
            "road_access_score": infra_proximity["road_access_score"],
            "metro_access_score": infra_proximity["metro_access_score"],
            "economic_access_score": infra_proximity["economic_access_score"],
            "strategic_infra_score": infra_proximity["strategic_infra_score"],
            "annualized_growth_pct": price_trend["annualized_growth_pct"],
            "recent_12m_growth_pct": price_trend["recent_12m_growth_pct"],
            "density_score": density_score,
            "population_growth_score": population_growth_score,
            "demand_pressure_score": demand_pressure_score,
            "zoning_shift_score": _to_float(components.get("zoning_shift_score"), zoning_shift["zoning_shift_score"]),
            "climate_exposure_score": climate_exposure_score,
            "climate_resilience_score": _to_float(components.get("climate_resilience_score"), None),
            "terrain_constraint_score": terrain_constraint_score,
            "terrain_readiness_score": _to_float(components.get("terrain_readiness_score"), None),
            "site_risk_score": site_risk_score,
            "planned_infra_count": planned_infra_count,
        },
    }


def _serialize_score_row(score_row: ValuationScore, *, location_name: str | None = None, summary: dict | None = None) -> dict:
    components = {
        "infra_score": round(float(score_row.infra_score or 0), 2),
        "price_trend_score": round(float(score_row.price_trend_score or 0), 2),
        "zoning_favorability": round(float(score_row.zoning_favorability or 0), 2),
        "road_access_score": None,
        "metro_access_score": None,
        "economic_access_score": None,
        "strategic_infra_score": None,
        "density_score": round(float(score_row.density_score or 0), 2),
        "population_growth_score": None,
        "demand_pressure_score": None,
        "zoning_shift_score": None,
        "annualized_growth_pct": None,
        "recent_12m_growth_pct": None,
        "climate_exposure_score": None,
        "avg_price_per_sqft": None,
        "terrain_constraint_score": None,
        "site_risk_score": None,
        "data_confidence_score": None,
        "data_confidence_band": None,
        "score_calibration_factor": None,
    }

    if summary:
        coverage = _build_data_coverage_snapshot(summary)
        price_trend = _build_price_trend_snapshot(
            summary.get("price_history", []),
            price_trend_score=components["price_trend_score"],
        )
        components["avg_price_per_sqft"] = (
            float(summary["avg_price_per_sqft"]) if summary.get("avg_price_per_sqft") else None
        )
        components["annualized_growth_pct"] = price_trend["annualized_growth_pct"]
        components["recent_12m_growth_pct"] = price_trend["recent_12m_growth_pct"]
        masterplan = summary.get("masterplan")
        masterplan_history = summary.get("masterplan_history") or ([masterplan] if masterplan else [])
        components["zoning_shift_score"] = _build_masterplan_shift_snapshot(masterplan, masterplan_history)["zoning_shift_score"]
        census = summary.get("census")
        geo_profile = summary.get("geo_profile")
        infra_proximity = compute_infra_proximity_profile(summary.get("nearby_infrastructure", []), geo_profile)
        components["road_access_score"] = infra_proximity["road_access_score"]
        components["metro_access_score"] = infra_proximity["metro_access_score"]
        components["economic_access_score"] = infra_proximity["economic_access_score"]
        components["strategic_infra_score"] = infra_proximity["strategic_infra_score"]
        population_growth_pct = _to_float(getattr(census, "growth_rate_pct", None), None) if census else None
        components["population_growth_score"] = round(compute_population_growth_score(population_growth_pct), 2)
        components["demand_pressure_score"] = round(
            compute_demand_pressure_score(population_growth_pct, components["density_score"]),
            2,
        )
        components["climate_exposure_score"] = round(compute_climate_exposure_score(geo_profile), 2)
        components["climate_resilience_score"] = round(compute_climate_resilience_score(geo_profile), 2)
        components["terrain_constraint_score"] = round(compute_terrain_constraint_score(geo_profile), 2)
        components["terrain_readiness_score"] = round(compute_terrain_readiness_score(geo_profile), 2)
        components["site_risk_score"] = round(compute_site_risk_score(geo_profile), 2)
        components["data_confidence_score"] = coverage["evidence_score"]
        components["data_confidence_band"] = coverage["confidence_band"]
        components["score_calibration_factor"] = coverage["score_calibration_factor"]

    return {
        "location": location_name or getattr(score_row.location, "name", f"Location {score_row.location_id}"),
        "location_id": score_row.location_id,
        "land_value_score": round(float(score_row.land_value_score or 0), 2),
        "development_potential_score": round(float(score_row.development_potential_score or 0), 2),
        "future_appreciation_index": round(float(score_row.future_appreciation_index or 0), 2),
        "components": components,
    }


def get_latest_score_row(session: Session, location_id: int) -> ValuationScore | None:
    return session.scalar(
        select(ValuationScore)
        .where(ValuationScore.location_id == location_id)
        .order_by(ValuationScore.computed_at.desc(), ValuationScore.id.desc())
    )


def get_latest_score(session: Session, location_id: int) -> dict | None:
    summary = data_svc.get_location_summary(session, location_id)
    if not summary:
        return None
    latest = get_latest_score_row(session, location_id)
    if not latest:
        return None
    return _serialize_score_row(latest, location_name=summary["location"].name, summary=summary)


def score_location(session: Session, location_id: int, *, persist: bool = True) -> dict | None:
    summary = data_svc.get_location_summary(session, location_id)
    if not summary:
        return None

    coverage = _build_data_coverage_snapshot(summary)
    score_calibration_factor = coverage["score_calibration_factor"]
    weights = {
        **load_weights(),
        "scoring_version": SCORING_VERSION,
        "data_confidence_score": coverage["evidence_score"],
        "score_calibration_factor": score_calibration_factor,
    }
    loc = summary["location"]
    masterplan = summary["masterplan"]
    prices = summary["price_history"]
    census = summary["census"]
    nearby_infra = summary["nearby_infrastructure"]
    geo_profile = summary.get("geo_profile")
    masterplan_history = summary.get("masterplan_history") or ([masterplan] if masterplan else [])

    infra_score = compute_infra_score(nearby_infra)
    price_trend = compute_price_trend(prices)
    zoning_favorability = compute_zoning_favorability(masterplan)
    density_score = compute_density_score(census)
    climate_resilience_score = compute_climate_resilience_score(geo_profile)
    terrain_readiness_score = compute_terrain_readiness_score(geo_profile)
    climate_exposure_score = compute_climate_exposure_score(geo_profile)
    terrain_constraint_score = compute_terrain_constraint_score(geo_profile)
    site_risk_score = compute_site_risk_score(geo_profile)
    zoning_shift_score = compute_masterplan_zoning_shift_score(
        masterplan_history,
        zoning_type=masterplan.zoning_type if masterplan else None,
    )
    infra_proximity = compute_infra_proximity_profile(nearby_infra, geo_profile)

    avg_price = float(summary["avg_price_per_sqft"]) if summary["avg_price_per_sqft"] else None
    planned_infra = [item for item in nearby_infra if item["infrastructure"].status in ("under_construction", "planned")]
    infra_planned_count = len(planned_infra)
    pop_growth = float(census.growth_rate_pct) if census and census.growth_rate_pct else 3.0
    population_growth_score = compute_population_growth_score(pop_growth)
    demand_pressure_score = compute_demand_pressure_score(pop_growth, density_score)

    raw_land_value = compute_land_value_score(
        avg_price,
        infra_score,
        zoning_favorability,
        density_score,
        price_trend,
        weights,
        climate_resilience_score=climate_resilience_score,
        terrain_readiness_score=terrain_readiness_score,
    )
    raw_development_potential = compute_development_potential(
        masterplan,
        infra_planned_count,
        price_trend,
        weights,
        climate_resilience_score=climate_resilience_score,
        terrain_readiness_score=terrain_readiness_score,
    )
    raw_future_appreciation = compute_future_appreciation(
        price_trend,
        infra_planned_count,
        pop_growth,
        masterplan.zoning_type if masterplan else None,
        weights,
        demand_pressure_score=demand_pressure_score,
        zoning_shift_score=zoning_shift_score,
        climate_resilience_score=climate_resilience_score,
        terrain_readiness_score=terrain_readiness_score,
    )
    land_value = _calibrate_score(raw_land_value, score_calibration_factor)
    development_potential = _calibrate_score(raw_development_potential, score_calibration_factor)
    future_appreciation = _calibrate_score(raw_future_appreciation, score_calibration_factor)

    if persist:
        score_row = ValuationScore(
            location_id=location_id,
            land_value_score=round(land_value, 2),
            development_potential_score=round(development_potential, 2),
            future_appreciation_index=round(future_appreciation, 2),
            infra_score=round(infra_score, 2),
            price_trend_score=round(price_trend, 2),
            zoning_favorability=round(zoning_favorability, 2),
            density_score=round(density_score, 2),
            weights=weights,
        )
        session.add(score_row)
        session.flush()
    else:
        score_row = ValuationScore(
            location_id=location_id,
            land_value_score=round(land_value, 2),
            development_potential_score=round(development_potential, 2),
            future_appreciation_index=round(future_appreciation, 2),
            infra_score=round(infra_score, 2),
            price_trend_score=round(price_trend, 2),
            zoning_favorability=round(zoning_favorability, 2),
            density_score=round(density_score, 2),
            weights=weights,
        )

    return {
        "location": loc.name,
        "location_id": location_id,
        "land_value_score": round(land_value, 2),
        "development_potential_score": round(development_potential, 2),
        "future_appreciation_index": round(future_appreciation, 2),
        "components": {
            "infra_score": round(infra_score, 2),
            "price_trend_score": round(price_trend, 2),
            "zoning_favorability": round(zoning_favorability, 2),
            "road_access_score": infra_proximity["road_access_score"],
            "metro_access_score": infra_proximity["metro_access_score"],
            "economic_access_score": infra_proximity["economic_access_score"],
            "strategic_infra_score": infra_proximity["strategic_infra_score"],
            "density_score": round(density_score, 2),
            "population_growth_score": round(population_growth_score, 2),
            "demand_pressure_score": round(demand_pressure_score, 2),
            "zoning_shift_score": round(zoning_shift_score, 2),
            "climate_exposure_score": round(climate_exposure_score, 2),
            "climate_resilience_score": round(climate_resilience_score, 2),
            "terrain_constraint_score": round(terrain_constraint_score, 2),
            "terrain_readiness_score": round(terrain_readiness_score, 2),
            "site_risk_score": round(site_risk_score, 2),
            "avg_price_per_sqft": avg_price,
            "data_confidence_score": coverage["evidence_score"],
            "data_confidence_band": coverage["confidence_band"],
            "score_calibration_factor": score_calibration_factor,
        },
    }


def get_or_compute_score(session: Session, location_id: int, *, max_age_hours: int = 24) -> dict | None:
    summary = data_svc.get_location_summary(session, location_id)
    if not summary:
        return None

    latest = get_latest_score_row(session, location_id)
    now = datetime.now(timezone.utc)
    if latest and latest.computed_at:
        score_version = latest.weights.get("scoring_version") if isinstance(latest.weights, dict) else None
        computed_at = latest.computed_at
        if computed_at.tzinfo is None:
            computed_at = computed_at.replace(tzinfo=timezone.utc)
        if computed_at >= now - timedelta(hours=max_age_hours) and score_version == SCORING_VERSION:
            return _serialize_score_row(latest, location_name=summary["location"].name, summary=summary)

    return score_location(session, location_id, persist=True)


def score_all_locations(session: Session) -> list[dict]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    results = []
    for loc in data_svc.get_all_locations(session):
        latest = get_latest_score_row(session, loc.id)
        if latest and latest.computed_at:
            computed_at = latest.computed_at
            if computed_at.tzinfo is None:
                computed_at = computed_at.replace(tzinfo=timezone.utc)
            score_version = latest.weights.get("scoring_version") if isinstance(latest.weights, dict) else None
            if computed_at > cutoff and score_version == SCORING_VERSION:
                continue
        result = score_location(session, loc.id, persist=True)
        if result:
            results.append(result)

    session.commit()
    return results


def build_rankings_query(top_n: int = 10, sort_by: str = "land_value_score"):
    from brain.data_bank.models import Location, Masterplan

    valid_fields = {
        "land_value_score": ValuationScore.land_value_score,
        "development_potential_score": ValuationScore.development_potential_score,
        "future_appreciation_index": ValuationScore.future_appreciation_index,
    }
    sort_col = valid_fields.get(sort_by, ValuationScore.land_value_score)

    latest_score_ids = select(func.max(ValuationScore.id)).group_by(ValuationScore.location_id)

    latest_zoning = (
        select(Masterplan.zoning_type)
        .where(Masterplan.location_id == Location.id)
        .order_by(Masterplan.effective_from.desc().nullslast(), Masterplan.created_at.desc())
        .limit(1)
        .scalar_subquery()
    )

    return (
        select(ValuationScore, Location.name, latest_zoning.label("zoning_type"))
        .select_from(ValuationScore)
        .join(Location, ValuationScore.location_id == Location.id)
        .where(ValuationScore.id.in_(latest_score_ids))
        .order_by(sort_col.desc(), Location.name.asc())
        .limit(top_n)
    )


def get_rankings(session: Session, top_n: int = 10, sort_by: str = "land_value_score") -> list[dict]:
    q = build_rankings_query(top_n=top_n, sort_by=sort_by)

    results = []
    for row in session.execute(q):
        score_row = row[0]
        name = row[1]
        zoning = row[2]
        results.append({
            "rank": len(results) + 1,
            "location": name,
            "location_id": score_row.location_id,
            "land_value_score": float(score_row.land_value_score or 0),
            "development_potential_score": float(score_row.development_potential_score or 0),
            "future_appreciation_index": float(score_row.future_appreciation_index or 0),
            "zoning_type": zoning or "residential",
        })
    return results


def compare_locations(session: Session, location_ids: list[int]) -> list[dict]:
    results = []
    for location_id in location_ids:
        result = get_or_compute_score(session, location_id)
        if result:
            results.append(result)
    session.commit()
    return results


def build_valuation_inputs(session: Session, location_id: int) -> dict | None:
    summary = data_svc.get_location_summary(session, location_id)
    if not summary:
        return None

    planning_context = data_svc.get_planning_context(session, location_id)
    if planning_context is None:
        planning_context = SimpleNamespace(
            **data_svc.derive_planning_context_payload(session, location_id, version_tag="inputs_shadow_v1")
        )

    valuation = get_or_compute_score(session, location_id)
    return {
        "location": summary["location"].name,
        "location_id": location_id,
        **_build_valuation_input_snapshot(summary, planning_context=planning_context, valuation=valuation),
    }


def build_favorability_profile(session: Session, location_id: int) -> dict | None:
    summary = data_svc.get_location_summary(session, location_id)
    if not summary:
        return None

    valuation = get_or_compute_score(session, location_id)
    if not valuation:
        return None

    masterplan = summary["masterplan"]
    geo_profile = summary.get("geo_profile")
    nearby_infra = summary["nearby_infrastructure"]
    regional_standards = summary.get("regional_standards", [])
    planning_context = data_svc.get_planning_context(session, location_id)
    if planning_context is None:
        planning_context = SimpleNamespace(
            **data_svc.derive_planning_context_payload(session, location_id, version_tag="favorability_shadow_v1")
        )
    valuation_inputs = _build_valuation_input_snapshot(
        summary,
        planning_context=planning_context,
        valuation=valuation,
    )
    coverage = valuation_inputs["coverage"]

    components = valuation.get("components", {})
    land_value_score = _to_float(valuation.get("land_value_score"))
    development_potential_score = _to_float(valuation.get("development_potential_score"))
    future_appreciation_index = _to_float(valuation.get("future_appreciation_index"))
    infra_score = _to_float(components.get("infra_score"))
    price_trend_score = _to_float(components.get("price_trend_score"))
    density_score = _to_float(components.get("density_score"))
    demand_pressure_score = _to_float(
        components.get("demand_pressure_score"),
        _to_float(valuation_inputs["demand"].get("demand_pressure_score"), 50.0),
    )
    strategic_infra_score = _to_float(
        components.get("strategic_infra_score"),
        _to_float(valuation_inputs["infrastructure"].get("strategic_infra_score"), 50.0),
    )
    site_risk_score = _to_float(
        components.get("site_risk_score"),
        _to_float(valuation_inputs["site"].get("site_risk_score"), 50.0),
    )
    climate_resilience_score = _to_float(components.get("climate_resilience_score"), 50.0)
    terrain_readiness_score = _to_float(components.get("terrain_readiness_score"), 50.0)
    zoning_type = masterplan.zoning_type if masterplan else None

    market_momentum_score = round(
        compute_market_momentum_score(land_value_score, future_appreciation_index, price_trend_score),
        2,
    )
    site_readiness_score = round(compute_site_readiness_score(masterplan, geo_profile), 2)
    regulatory_clarity_score = round(
        compute_regulatory_clarity_score(masterplan, planning_context, regional_standards),
        2,
    )
    mobility_score = round(compute_mobility_score(nearby_infra, geo_profile), 2)

    use_case_scores = {
        use_case: round(
            compute_use_case_favorability(
                use_case,
                zoning_type=zoning_type,
                land_value_score=land_value_score,
                development_potential_score=development_potential_score,
                future_appreciation_index=future_appreciation_index,
                infra_score=infra_score,
                density_score=density_score,
                climate_resilience_score=climate_resilience_score,
                terrain_readiness_score=terrain_readiness_score,
            ),
            2,
        )
        for use_case in FAVORABILITY_USE_CASES
    }
    recommended_use_case = max(use_case_scores, key=use_case_scores.get)
    raw_overall_favorability_score = round(
        compute_overall_favorability_score(
            market_momentum_score=market_momentum_score,
            site_readiness_score=site_readiness_score,
            regulatory_clarity_score=regulatory_clarity_score,
            mobility_score=mobility_score,
            best_use_case_score=use_case_scores[recommended_use_case],
        ),
        2,
    )
    overall_favorability_score = _calibrate_score(
        raw_overall_favorability_score,
        _to_float(coverage.get("score_calibration_factor"), 1.0),
    )
    strengths, risks, opportunities = _build_favorability_tags(
        recommended_use_case=recommended_use_case,
        overall_favorability_score=overall_favorability_score,
        market_momentum_score=market_momentum_score,
        site_readiness_score=site_readiness_score,
        regulatory_clarity_score=regulatory_clarity_score,
        mobility_score=mobility_score,
        strategic_infra_score=strategic_infra_score,
        climate_resilience_score=climate_resilience_score,
        terrain_readiness_score=terrain_readiness_score,
        site_risk_score=site_risk_score,
        demand_pressure_score=demand_pressure_score,
        development_potential_score=development_potential_score,
        future_appreciation_index=future_appreciation_index,
        zoning_type=zoning_type,
        market_tier=getattr(planning_context, "market_tier", None),
    )
    if coverage["confidence_band"] == "medium":
        risks.append("Data coverage is moderate, so the scoring signal should be treated as directional.")
    elif coverage["confidence_band"] == "low":
        risks.append("Data coverage is thin, so upside and use-case recommendations are provisional.")
    risks = _trim_tags(risks, limit=4)

    return {
        "location": summary["location"].name,
        "location_id": location_id,
        "overall_favorability_score": overall_favorability_score,
        "favorability_band": _favorability_band(overall_favorability_score),
        "recommended_use_case": recommended_use_case,
        "market_tier": getattr(planning_context, "market_tier", None),
        "inputs": valuation_inputs,
        "components": {
            "market_momentum_score": market_momentum_score,
            "site_readiness_score": site_readiness_score,
            "regulatory_clarity_score": regulatory_clarity_score,
            "mobility_score": mobility_score,
            "strategic_infra_score": round(strategic_infra_score, 2),
            "demand_pressure_score": round(demand_pressure_score, 2),
            "site_risk_score": round(site_risk_score, 2),
            "climate_resilience_score": round(climate_resilience_score, 2),
            "terrain_readiness_score": round(terrain_readiness_score, 2),
            "data_confidence_score": coverage["evidence_score"],
            "data_confidence_band": coverage["confidence_band"],
        },
        "use_case_scores": use_case_scores,
        "strengths": strengths,
        "risks": risks,
        "opportunities": opportunities,
        "valuation": valuation,
    }


def build_core_outputs(
    session: Session,
    location_id: int,
    *,
    price_prediction=None,
    hotspot=None,
) -> dict | None:
    profile = build_favorability_profile(session, location_id)
    if not profile:
        return None

    logic = _build_logic_output(profile)
    if price_prediction is None:
        price_prediction = _safe_price_prediction(session, location_id)
    if hotspot is None:
        hotspot = _safe_hotspot_context(session, location_id)
    forward_outlook = _build_forward_outlook(price_prediction)
    valuation = profile["valuation"]
    inputs = profile["inputs"]
    scores = profile["components"]
    market = inputs["market"]
    demand = inputs["demand"]
    planning = inputs["planning"]
    site = inputs["site"]

    return {
        "location": profile["location"],
        "location_id": profile["location_id"],
        "summary": _build_core_summary(
            recommended_use_case=profile["recommended_use_case"],
            favorability_band=profile["favorability_band"],
            future_appreciation_index=_to_float(valuation.get("future_appreciation_index")),
            price_momentum_band=market.get("price_momentum_band"),
            demand_profile=demand.get("demand_profile"),
            site_risk_band=site.get("site_risk_band"),
            strategic_infra_score=_to_float(scores.get("strategic_infra_score"), 50.0),
        ),
        "key_insight": _build_key_insight(
            profile,
            logic,
            price_prediction=price_prediction,
            hotspot=hotspot,
        ),
        "forward_outlook": forward_outlook,
        "coverage": inputs.get("coverage", {}),
        "scores": {
            "land_value_score": round(_to_float(valuation.get("land_value_score")), 2),
            "development_potential_score": round(_to_float(valuation.get("development_potential_score")), 2),
            "future_appreciation_index": round(_to_float(valuation.get("future_appreciation_index")), 2),
            "overall_favorability_score": round(_to_float(profile.get("overall_favorability_score")), 2),
            "strategic_infra_score": round(_to_float(scores.get("strategic_infra_score"), 50.0), 2),
            "demand_pressure_score": round(_to_float(scores.get("demand_pressure_score"), 50.0), 2),
            "site_risk_score": round(_to_float(scores.get("site_risk_score"), 50.0), 2),
        },
        "land_value": _build_land_value_output(valuation, inputs),
        "development_potential": _build_development_potential_output(valuation, inputs),
        "future_appreciation": _build_future_appreciation_output(valuation, inputs),
        "logic": logic,
        "positioning": {
            "recommended_use_case": profile["recommended_use_case"],
            "favorability_band": profile["favorability_band"],
            "market_tier": profile.get("market_tier"),
            "price_trend_direction": market.get("price_trend_direction"),
            "price_momentum_band": market.get("price_momentum_band"),
            "demand_profile": demand.get("demand_profile"),
            "site_risk_band": site.get("site_risk_band"),
            "zoning_shift_direction": planning.get("zoning_shift_direction"),
        },
        "strengths": profile.get("strengths", []),
        "risks": profile.get("risks", []),
        "opportunities": profile.get("opportunities", []),
    }


def build_logic_layer(session: Session, location_id: int) -> dict | None:
    profile = build_favorability_profile(session, location_id)
    if not profile:
        return None

    return {
        "location": profile["location"],
        "location_id": profile["location_id"],
        "logic": _build_logic_output(profile),
    }


def get_favorability_rankings(session: Session, *, top_n: int = 10, use_case: str = "overall") -> list[dict]:
    if use_case not in FAVORABILITY_SORT_FIELDS:
        raise ValueError(f"Unsupported favorability sort: {use_case}")

    results: list[dict] = []
    for location in data_svc.get_all_locations(session):
        profile = build_favorability_profile(session, location.id)
        if not profile:
            continue

        selected_score = (
            profile["overall_favorability_score"]
            if use_case == "overall"
            else profile["use_case_scores"][use_case]
        )
        results.append({
            "location": profile["location"],
            "location_id": profile["location_id"],
            "overall_favorability_score": profile["overall_favorability_score"],
            "selected_score": round(selected_score, 2),
            "selected_use_case": use_case,
            "recommended_use_case": profile["recommended_use_case"],
            "favorability_band": profile["favorability_band"],
        })

    results.sort(key=lambda item: (-item["selected_score"], item["location"]))
    ranked = []
    for index, item in enumerate(results[:top_n], start=1):
        ranked.append({
            "rank": index,
            **item,
        })
    return ranked


def predict_price_for_location(session: Session, location_id: int):
    from brain.valuation.ml.price_predictor import PricePredictor

    predictor = PricePredictor()
    return predictor.predict(session, location_id)


def detect_hotspots(session: Session, *, n_clusters: int = 4):
    from brain.valuation.ml.hotspot_detector import HotspotDetector

    score_all_locations(session)
    detector = HotspotDetector(n_clusters=n_clusters)
    return detector.detect(session)
