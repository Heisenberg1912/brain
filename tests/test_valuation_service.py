"""Tests for valuation service query construction and integration helpers."""
from datetime import date
from types import SimpleNamespace

import brain.valuation.service as valuation_service
from sqlalchemy.dialects import postgresql

from brain.valuation.service import build_rankings_query


def test_build_rankings_query_compiles_with_explicit_location_join():
    query = build_rankings_query(top_n=5, sort_by="land_value_score")
    compiled = str(query.compile(dialect=postgresql.dialect()))

    assert "JOIN locations ON valuation_scores.location_id = locations.id" in compiled
    assert "masterplans" in compiled


def test_build_favorability_profile_recommends_mixed_use_for_strong_mixed_site(monkeypatch):
    summary = {
        "location": SimpleNamespace(id=1, name="Whitefield Core", city="Bangalore"),
        "masterplan": SimpleNamespace(
            zoning_type="mixed",
            version="RMP_2031",
            fsi=3.2,
            max_height_m=54,
            ground_coverage_pct=62,
            approval_status="active",
        ),
        "masterplan_history": [
            SimpleNamespace(zoning_type="residential", effective_from=date(2020, 1, 1), effective_to=date(2024, 12, 31), created_at=None, id=1),
            SimpleNamespace(zoning_type="mixed", effective_from=date(2025, 1, 1), effective_to=None, created_at=None, id=2),
        ],
        "geo_profile": SimpleNamespace(
            flood_risk_score=22,
            heat_risk_score=28,
            climate_risk_score=24,
            terrain_class="flat",
            terrain_slope_pct=2,
            road_proximity_km=0.7,
            transit_proximity_km=0.5,
        ),
        "price_history": [
            SimpleNamespace(recorded_date=date(2024, 1, 1), price_per_sqft=9800),
            SimpleNamespace(recorded_date=date(2025, 1, 1), price_per_sqft=11200),
        ],
        "census": SimpleNamespace(population=180000, growth_rate_pct=4.6, density_per_sqkm=11800),
        "regional_standards": [SimpleNamespace(code="BBMP-01"), SimpleNamespace(code="FIRE-02")],
        "nearby_infrastructure": [
            {"infrastructure": SimpleNamespace(infra_type="metro_station", status="operational", name="Metro"), "distance_km": 0.6},
            {"infrastructure": SimpleNamespace(infra_type="tech_park", status="operational", name="Tech Park"), "distance_km": 1.0},
        ],
    }
    score = {
        "location": "Whitefield Core",
        "location_id": 1,
        "land_value_score": 78,
        "development_potential_score": 82,
        "future_appreciation_index": 76,
        "components": {
            "infra_score": 74,
            "price_trend_score": 69,
            "zoning_favorability": 90,
            "density_score": 68,
            "population_growth_score": 57.5,
            "demand_pressure_score": 62.23,
            "climate_resilience_score": 75,
            "terrain_readiness_score": 85,
            "avg_price_per_sqft": 11200,
        },
    }

    monkeypatch.setattr(valuation_service.data_svc, "get_location_summary", lambda _session, _location_id: summary)
    monkeypatch.setattr(valuation_service, "get_or_compute_score", lambda _session, _location_id: score)
    monkeypatch.setattr(valuation_service.data_svc, "get_planning_context", lambda _session, _location_id: SimpleNamespace(
        version_tag="ctx_v1",
        market_tier="premium",
        validation_status="derived",
        location_intelligence_score=78,
        zoning_validation_rules={"coverage": True},
        floor_plan_constraints={"fsi": 3.2},
    ))

    profile = valuation_service.build_favorability_profile(None, 1)

    assert profile is not None
    assert profile["recommended_use_case"] == "mixed_use"
    assert profile["overall_favorability_score"] > 70
    assert profile["favorability_band"] in {"prime", "strong"}
    assert profile["inputs"]["planning"]["zoning_type"] == "mixed"
    assert profile["inputs"]["planning"]["zoning_shift_direction"] == "upzoned"
    assert profile["components"]["strategic_infra_score"] > 85
    assert profile["components"]["demand_pressure_score"] > 60
    assert profile["components"]["site_risk_score"] < 25
    assert profile["inputs"]["market"]["price_history_points"] == 2
    assert profile["inputs"]["market"]["price_trend_direction"] == "rising"


def test_build_valuation_inputs_exposes_core_land_and_upside_signals(monkeypatch):
    summary = {
        "location": SimpleNamespace(id=1, name="Whitefield Core", city="Bangalore"),
        "masterplan": SimpleNamespace(
            zoning_type="mixed",
            version="RMP_2031",
            fsi=3.2,
            max_height_m=54,
            ground_coverage_pct=62,
            approval_status="active",
        ),
        "masterplan_history": [
            SimpleNamespace(zoning_type="residential", effective_from=date(2020, 1, 1), effective_to=date(2024, 12, 31), created_at=None, id=1),
            SimpleNamespace(zoning_type="mixed", effective_from=date(2025, 1, 1), effective_to=None, created_at=None, id=2),
        ],
        "price_history": [
            SimpleNamespace(recorded_date=date(2024, 1, 1), price_per_sqft=10000),
            SimpleNamespace(recorded_date=date(2025, 1, 1), price_per_sqft=11200),
        ],
        "avg_price_per_sqft": 11150,
        "census": SimpleNamespace(population=180000, growth_rate_pct=4.6, density_per_sqkm=11800),
        "geo_profile": SimpleNamespace(
            terrain_class="flat",
            terrain_slope_pct=2,
            road_proximity_km=0.7,
            transit_proximity_km=0.5,
            flood_risk_score=22,
            heat_risk_score=28,
            climate_risk_score=24,
        ),
        "regional_standards": [SimpleNamespace(code="BBMP-01"), SimpleNamespace(code="FIRE-02")],
        "nearby_infrastructure": [
            {"infrastructure": SimpleNamespace(infra_type="metro_station", status="operational"), "distance_km": 0.6},
            {"infrastructure": SimpleNamespace(infra_type="tech_park", status="operational"), "distance_km": 1.0},
            {"infrastructure": SimpleNamespace(infra_type="highway", status="planned"), "distance_km": 1.8},
        ],
    }
    score = {
        "location": "Whitefield Core",
        "location_id": 1,
        "land_value_score": 78,
        "development_potential_score": 82,
        "future_appreciation_index": 76,
        "components": {
            "infra_score": 74,
            "price_trend_score": 69,
            "zoning_favorability": 90,
            "density_score": 68,
            "population_growth_score": 57.5,
            "demand_pressure_score": 62.23,
            "zoning_shift_score": 97.9,
            "climate_resilience_score": 75,
            "terrain_readiness_score": 85,
            "avg_price_per_sqft": 11150,
        },
    }

    monkeypatch.setattr(valuation_service.data_svc, "get_location_summary", lambda _session, _location_id: summary)
    monkeypatch.setattr(valuation_service.data_svc, "get_planning_context", lambda _session, _location_id: SimpleNamespace(
        version_tag="ctx_v1",
        market_tier="premium",
        validation_status="validated",
        location_intelligence_score=79,
    ))
    monkeypatch.setattr(valuation_service, "get_or_compute_score", lambda _session, _location_id: score)

    payload = valuation_service.build_valuation_inputs(None, 1)

    assert payload is not None
    assert payload["market"]["avg_price_per_sqft"] == 11150
    assert payload["market"]["oldest_price_per_sqft"] == 10000
    assert payload["market"]["price_growth_pct"] == 12.0
    assert payload["market"]["annualized_growth_pct"] == 11.97
    assert payload["market"]["recent_12m_growth_pct"] == 12.0
    assert payload["market"]["first_recorded_date"] == "2024-01-01"
    assert payload["market"]["latest_recorded_date"] == "2025-01-01"
    assert payload["market"]["price_history_span_days"] == 366
    assert payload["market"]["price_trend_direction"] == "rising"
    assert payload["market"]["price_momentum_band"] == "positive"
    assert payload["coverage"]["confidence_band"] == "high"
    assert payload["coverage"]["evidence_score"] >= 80
    assert "Price history is thin and may overfit short-term trend calculations." in payload["coverage"]["data_gaps"]
    assert "Latest pricing signal is aging and may lag current market conditions." in payload["coverage"]["data_gaps"]
    assert payload["planning"]["zoning_type"] == "mixed"
    assert payload["planning"]["previous_zoning_type"] == "residential"
    assert payload["planning"]["zoning_shift_direction"] == "upzoned"
    assert payload["planning"]["zoning_shift_score"] > 90
    assert payload["planning"]["regional_standard_codes"] == ["BBMP-01", "FIRE-02"]
    assert payload["demand"]["population_growth_score"] == 57.5
    assert payload["demand"]["demand_profile"] == "growing"
    assert payload["demand"]["demand_pressure_score"] == 62.23
    assert payload["infrastructure"]["road_proximity_km"] == 0.7
    assert payload["infrastructure"]["metro_proximity_km"] == 0.6
    assert payload["infrastructure"]["economic_zone_proximity_km"] == 1.0
    assert payload["infrastructure"]["strategic_infra_score"] == 89.58
    assert payload["infrastructure"]["planned_infra_count"] == 1
    assert payload["infrastructure"]["nearest_transit_node_km"] == 0.6
    assert payload["site"]["road_proximity_km"] == 0.7
    assert payload["site"]["climate_exposure_score"] == 24.1
    assert payload["site"]["terrain_constraint_score"] == 7.8
    assert payload["site"]["site_risk_score"] == 17.58
    assert payload["site"]["site_risk_band"] == "contained"
    assert payload["model_inputs"]["price_trend_score"] == 69
    assert payload["model_inputs"]["annualized_growth_pct"] == 11.97
    assert payload["model_inputs"]["recent_12m_growth_pct"] == 12.0
    assert payload["model_inputs"]["metro_access_score"] == 88.0
    assert payload["model_inputs"]["strategic_infra_score"] == 89.58
    assert payload["model_inputs"]["demand_pressure_score"] == 62.23
    assert payload["model_inputs"]["climate_exposure_score"] == 24.1
    assert payload["model_inputs"]["terrain_constraint_score"] == 7.8
    assert payload["model_inputs"]["site_risk_score"] == 17.58
    assert payload["model_inputs"]["zoning_shift_score"] > 90


def test_score_location_calibrates_extreme_scores_when_data_is_sparse(monkeypatch):
    summary = {
        "location": SimpleNamespace(id=1, name="Thin Evidence Site", city="Lucknow"),
        "masterplan": None,
        "masterplan_history": [],
        "price_history": [
            SimpleNamespace(recorded_date=date(2025, 1, 1), price_per_sqft=10000),
        ],
        "avg_price_per_sqft": 10000,
        "census": None,
        "geo_profile": None,
        "regional_standards": [],
        "nearby_infrastructure": [],
    }

    monkeypatch.setattr(valuation_service.data_svc, "get_location_summary", lambda _session, _location_id: summary)
    monkeypatch.setattr(valuation_service, "compute_infra_score", lambda _nearby_infra: 88)
    monkeypatch.setattr(valuation_service, "compute_price_trend", lambda _prices: 86)
    monkeypatch.setattr(valuation_service, "compute_zoning_favorability", lambda _masterplan: 92)
    monkeypatch.setattr(valuation_service, "compute_density_score", lambda _census: 75)
    monkeypatch.setattr(valuation_service, "compute_climate_resilience_score", lambda _geo_profile: 80)
    monkeypatch.setattr(valuation_service, "compute_terrain_readiness_score", lambda _geo_profile: 82)
    monkeypatch.setattr(valuation_service, "compute_climate_exposure_score", lambda _geo_profile: 20)
    monkeypatch.setattr(valuation_service, "compute_terrain_constraint_score", lambda _geo_profile: 18)
    monkeypatch.setattr(valuation_service, "compute_site_risk_score", lambda _geo_profile: 22)
    monkeypatch.setattr(valuation_service, "compute_masterplan_zoning_shift_score", lambda *_args, **_kwargs: 90)
    monkeypatch.setattr(
        valuation_service,
        "compute_infra_proximity_profile",
        lambda _nearby_infra, _geo_profile: {
            "road_access_score": 84,
            "metro_access_score": 72,
            "economic_access_score": 70,
            "strategic_infra_score": 75,
        },
    )
    monkeypatch.setattr(valuation_service, "compute_population_growth_score", lambda _growth: 70)
    monkeypatch.setattr(valuation_service, "compute_demand_pressure_score", lambda _growth, _density: 72)
    monkeypatch.setattr(valuation_service, "compute_land_value_score", lambda *_args, **_kwargs: 90)
    monkeypatch.setattr(valuation_service, "compute_development_potential", lambda *_args, **_kwargs: 88)
    monkeypatch.setattr(valuation_service, "compute_future_appreciation", lambda *_args, **_kwargs: 91)

    result = valuation_service.score_location(None, 1, persist=False)

    assert result is not None
    assert result["land_value_score"] < 90
    assert result["development_potential_score"] < 88
    assert result["future_appreciation_index"] < 91
    assert result["components"]["data_confidence_band"] == "low"
    assert result["components"]["score_calibration_factor"] < 0.8


def test_build_logic_layer_downgrades_when_data_coverage_is_low(monkeypatch):
    monkeypatch.setattr(
        valuation_service,
        "build_favorability_profile",
        lambda _session, _location_id: {
            "location": "Thin Evidence Site",
            "location_id": 1,
            "inputs": {
                "coverage": {
                    "evidence_score": 42,
                    "confidence_band": "low",
                },
                "planning": {
                    "zoning_shift_direction": "upzoned",
                },
            },
            "components": {
                "regulatory_clarity_score": 72,
                "site_risk_score": 18,
                "site_readiness_score": 81,
            },
            "valuation": {
                "land_value_score": 86,
                "development_potential_score": 84,
                "future_appreciation_index": 88,
            },
        },
    )

    payload = valuation_service.build_logic_layer(None, 1)

    assert payload is not None
    assert payload["logic"]["investment_signal"] == "watch"
    assert payload["logic"]["execution_strategy"] == "monitor"
    assert payload["logic"]["gating_issue"] == "data_coverage"
    assert payload["logic"]["conviction"] == "low"
    assert payload["logic"]["data_confidence_band"] == "low"


def test_build_core_outputs_summarizes_decision_ready_signals(monkeypatch):
    monkeypatch.setattr(
        valuation_service,
        "build_favorability_profile",
        lambda _session, _location_id: {
            "location": "Whitefield Core",
            "location_id": 1,
            "overall_favorability_score": 74.2,
            "favorability_band": "strong",
            "recommended_use_case": "mixed_use",
            "market_tier": "premium",
            "components": {
                "regulatory_clarity_score": 72,
                "site_readiness_score": 74,
                "strategic_infra_score": 89.58,
                "demand_pressure_score": 62.23,
                "site_risk_score": 17.58,
                },
                "inputs": {
                    "market": {
                        "avg_price_per_sqft": 11150,
                        "annualized_growth_pct": 11.97,
                    "recent_12m_growth_pct": 12.0,
                    "price_trend_direction": "rising",
                    "price_momentum_band": "positive",
                },
                "demand": {
                    "demand_pressure_score": 62.23,
                    "demand_profile": "growing",
                },
                "infrastructure": {
                    "planned_infra_count": 1,
                    "strategic_infra_score": 89.58,
                },
                "planning": {
                    "zoning_type": "mixed",
                    "fsi": 3.2,
                    "max_height_m": 54,
                    "ground_coverage_pct": 62,
                    "zoning_shift_score": 97.9,
                    "zoning_shift_direction": "upzoned",
                },
                    "site": {
                        "site_risk_band": "contained",
                    },
                    "coverage": {
                        "evidence_score": 86,
                        "confidence_band": "strong",
                    },
                },
                "strengths": ["Strong market momentum supports value retention and upside."],
                "risks": ["Regulatory clarity is still weak and needs diligence before commitment."],
                "opportunities": ["Infra proximity supports corridor-led value expansion."],
            "valuation": {
                "land_value_score": 78,
                "development_potential_score": 82,
                "future_appreciation_index": 76,
                "components": {
                    "avg_price_per_sqft": 11150,
                    "infra_score": 74,
                    "zoning_favorability": 90,
                    "density_score": 68,
                    "price_trend_score": 69,
                    "annualized_growth_pct": 11.97,
                    "recent_12m_growth_pct": 12.0,
                    "demand_pressure_score": 62.23,
                    "zoning_shift_score": 97.9,
                },
            },
        },
    )
    monkeypatch.setattr(
        valuation_service,
        "_safe_price_prediction",
        lambda _session, _location_id: {
            "current_avg_price": 11200,
            "predicted_price_1yr": 12174.4,
            "predicted_price_3yr": 15652.45,
            "annual_growth_pct": 8.7,
            "predicted_upside_pct": 8.7,
            "signal": "positive",
            "confidence": "medium",
            "model_version": "price_regression_v2",
            "drivers": [
                {
                    "key": "future_appreciation_index",
                    "label": "Future Appreciation Index",
                    "value": 76,
                    "contribution": 1.8421,
                    "direction": "positive",
                },
                {
                    "key": "population_growth_pct",
                    "label": "Population Growth %",
                    "value": 4.6,
                    "contribution": 1.1042,
                    "direction": "positive",
                },
            ],
        },
    )
    monkeypatch.setattr(
        valuation_service,
        "_safe_hotspot_context",
        lambda _session, _location_id: {
            "label": "emerging",
        },
    )

    payload = valuation_service.build_core_outputs(None, 1)

    assert payload is not None
    assert payload["scores"]["land_value_score"] == 78
    assert payload["scores"]["future_appreciation_index"] == 76
    assert payload["land_value"]["score"] == 78
    assert payload["land_value"]["band"] == "strong"
    assert payload["land_value"]["drivers"][0]["key"] == "avg_price_per_sqft"
    assert payload["development_potential"]["score"] == 82
    assert payload["development_potential"]["band"] == "high_capacity"
    assert payload["development_potential"]["drivers"][0]["key"] == "fsi"
    assert payload["future_appreciation"]["score"] == 76
    assert payload["future_appreciation"]["band"] == "high"
    assert payload["future_appreciation"]["drivers"][0]["key"] == "price_trend_score"
    assert payload["logic"]["weighted_score"] == 78.4
    assert payload["logic"]["weighted_band"] == "strong"
    assert payload["logic"]["investment_signal"] == "accumulate"
    assert payload["logic"]["execution_strategy"] == "build_now"
    assert payload["logic"]["conviction"] == "high"
    assert payload["logic"]["primary_driver"] == "future_upside"
    assert payload["logic"]["weighted_components"][0]["key"] == "land_value_score"
    assert payload["logic"]["weighted_components"][2]["contribution"] == 30.4
    assert payload["logic"]["rule_hits"][0]["code"] == "weighted_strength"
    assert payload["forward_outlook"]["predicted_price_1yr"] == 12174.4
    assert payload["forward_outlook"]["predicted_upside_pct"] == 8.7
    assert payload["forward_outlook"]["drivers"][0]["key"] == "future_appreciation_index"
    assert "projected from 11200.00 to 12174.40" in payload["forward_outlook"]["summary"]
    assert payload["positioning"]["recommended_use_case"] == "mixed_use"
    assert payload["positioning"]["price_trend_direction"] == "rising"
    assert payload["positioning"]["site_risk_band"] == "contained"
    assert "emerging hotspot" in payload["key_insight"]
    assert "8.7% projected 1Y upside" in payload["key_insight"]
    assert "mixed use fit" in payload["summary"]
    assert "high upside" in payload["summary"]


def test_build_logic_layer_returns_weighted_decision(monkeypatch):
    monkeypatch.setattr(
        valuation_service,
        "build_favorability_profile",
        lambda _session, _location_id: {
            "location": "Whitefield Core",
            "location_id": 1,
            "overall_favorability_score": 74.2,
            "favorability_band": "strong",
            "recommended_use_case": "mixed_use",
            "components": {
                "regulatory_clarity_score": 72,
                "site_readiness_score": 74,
                "strategic_infra_score": 89.58,
                "demand_pressure_score": 62.23,
                "site_risk_score": 17.58,
            },
            "inputs": {
                "market": {"price_momentum_band": "positive"},
                "demand": {"demand_profile": "growing"},
                "planning": {"zoning_shift_direction": "upzoned"},
                "site": {"site_risk_band": "contained"},
                "coverage": {"evidence_score": 86, "confidence_band": "strong"},
            },
            "valuation": {
                "land_value_score": 78,
                "development_potential_score": 82,
                "future_appreciation_index": 76,
            },
        },
    )

    payload = valuation_service.build_logic_layer(None, 1)

    assert payload is not None
    assert payload["logic"]["weighted_score"] == 78.4
    assert payload["logic"]["weighted_band"] == "strong"
    assert payload["logic"]["investment_signal"] == "accumulate"
    assert payload["logic"]["execution_strategy"] == "build_now"
    assert payload["logic"]["conviction"] == "high"
    assert payload["logic"]["gating_issue"] is None
    assert payload["logic"]["primary_driver"] == "future_upside"
    assert payload["logic"]["weighted_components"][1]["key"] == "development_potential_score"


def test_get_favorability_rankings_sorts_by_selected_use_case(monkeypatch):
    monkeypatch.setattr(
        valuation_service.data_svc,
        "get_all_locations",
        lambda _session: [SimpleNamespace(id=1), SimpleNamespace(id=2)],
    )
    monkeypatch.setattr(
        valuation_service,
        "build_favorability_profile",
        lambda _session, location_id: {
            1: {
                "location": "A",
                "location_id": 1,
                "overall_favorability_score": 68.0,
                "recommended_use_case": "residential",
                "favorability_band": "strong",
                "use_case_scores": {"residential": 72.0, "commercial": 54.0, "mixed_use": 65.0, "industrial": 28.0},
            },
            2: {
                "location": "B",
                "location_id": 2,
                "overall_favorability_score": 66.0,
                "recommended_use_case": "commercial",
                "favorability_band": "strong",
                "use_case_scores": {"residential": 58.0, "commercial": 81.0, "mixed_use": 70.0, "industrial": 40.0},
            },
        }[location_id],
    )

    rankings = valuation_service.get_favorability_rankings(None, top_n=2, use_case="commercial")

    assert rankings[0]["location_id"] == 2
    assert rankings[0]["selected_score"] == 81.0
    assert rankings[1]["location_id"] == 1
