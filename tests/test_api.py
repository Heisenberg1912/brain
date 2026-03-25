"""Tests for API endpoints — validation and error handling."""
import pytest
from unittest.mock import patch, MagicMock
from types import SimpleNamespace
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


# ── Health ─────────────────────────────────────────────────

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


# ── Data Bank Validation ──────────────────────────────────

class TestDataBankValidation:
    def test_nearby_rejects_invalid_lat(self):
        r = client.get("/api/v1/data/locations/nearby?lat=100&lng=77.5&radius_km=5")
        assert r.status_code == 422

    def test_nearby_rejects_invalid_lng(self):
        r = client.get("/api/v1/data/locations/nearby?lat=12.9&lng=200&radius_km=5")
        assert r.status_code == 422

    def test_nearby_rejects_negative_radius(self):
        r = client.get("/api/v1/data/locations/nearby?lat=12.9&lng=77.5&radius_km=-1")
        assert r.status_code == 422

    def test_nearby_rejects_excessive_radius(self):
        r = client.get("/api/v1/data/locations/nearby?lat=12.9&lng=77.5&radius_km=200")
        assert r.status_code == 422


# ── Valuation Validation ──────────────────────────────────

class TestValuationValidation:
    def test_rankings_rejects_invalid_sort(self):
        r = client.get("/api/v1/valuation/rankings?sort_by=invalid_field")
        assert r.status_code == 422

    def test_rankings_rejects_top_zero(self):
        r = client.get("/api/v1/valuation/rankings?top=0")
        assert r.status_code == 422

    def test_rankings_rejects_top_over_100(self):
        r = client.get("/api/v1/valuation/rankings?top=101")
        assert r.status_code == 422

    def test_compare_rejects_empty_list(self):
        r = client.post("/api/v1/valuation/compare", json={"location_ids": []})
        assert r.status_code == 422

    def test_compare_rejects_too_many(self):
        r = client.post("/api/v1/valuation/compare", json={"location_ids": list(range(25))})
        assert r.status_code == 422

    def test_favorability_rankings_rejects_invalid_use_case(self):
        r = client.get("/api/v1/valuation/favorability/rankings?use_case=hotel")
        assert r.status_code == 422

    def test_valuation_core_route_returns_compact_brain_payload(self):
        payload = {
            "location": "Whitefield Core",
            "location_id": 1,
            "summary": "Strong mixed use fit with high upside, positive price momentum, growing demand, strong corridor access, and contained site risk.",
            "key_insight": "Future upside is the lead signal: the parcel sits in an emerging hotspot with 8.7% projected 1Y upside and a strong mixed use fit.",
            "forward_outlook": {
                "current_avg_price": 11200,
                "predicted_price_1yr": 12174.4,
                "predicted_price_3yr": 15652.45,
                "predicted_upside_pct": 8.7,
                "annual_growth_pct": 8.7,
                "signal": "positive",
                "confidence": "medium",
                "model_version": "price_regression_v2",
                "summary": "Forward view: price is projected from 11200.00 to 12174.40 in 1Y (+8.70%), with a positive signal.",
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
            "scores": {
                "land_value_score": 78,
                "development_potential_score": 82,
                "future_appreciation_index": 76,
                "overall_favorability_score": 74.2,
                "strategic_infra_score": 89.58,
                "demand_pressure_score": 62.23,
                "site_risk_score": 17.58,
            },
            "land_value": {
                "score": 78,
                "band": "strong",
                "summary": "Strong land value with mixed zoning support, positive pricing, and strong access.",
                "drivers": [
                    {"key": "avg_price_per_sqft", "label": "Avg Price / sqft", "value": 11150},
                    {"key": "infra_score", "label": "Infra Proximity", "value": 74},
                    {"key": "zoning_favorability", "label": "Zoning Favorability", "value": 90},
                    {"key": "density_score", "label": "Density Score", "value": 68},
                    {"key": "price_trend_score", "label": "Price Trend Score", "value": 69},
                ],
            },
            "development_potential": {
                "score": 82,
                "band": "high_capacity",
                "summary": "High Capacity development potential with mixed zoning, 1 planned infra catalysts, and strong access support.",
                "drivers": [
                    {"key": "fsi", "label": "FSI", "value": 3.2},
                    {"key": "max_height_m", "label": "Max Height (m)", "value": 54},
                    {"key": "ground_coverage_pct", "label": "Ground Coverage %", "value": 62},
                    {"key": "planned_infra_count", "label": "Planned Infra Count", "value": 1},
                    {"key": "price_trend_score", "label": "Price Trend Score", "value": 69},
                ],
            },
            "future_appreciation": {
                "score": 76,
                "band": "high",
                "summary": "High appreciation outlook with rising pricing, growing demand, upzoned zoning movement, and 1 planned infra catalysts.",
                "drivers": [
                    {"key": "price_trend_score", "label": "Price Trend Score", "value": 69},
                    {"key": "annualized_growth_pct", "label": "Annualized Growth %", "value": 11.97},
                    {"key": "recent_12m_growth_pct", "label": "Recent 12M Growth %", "value": 12.0},
                    {"key": "demand_pressure_score", "label": "Demand Pressure", "value": 62.23},
                    {"key": "zoning_shift_score", "label": "Zoning Shift Score", "value": 97.9},
                    {"key": "planned_infra_count", "label": "Planned Infra Count", "value": 1},
                ],
            },
            "logic": {
                "weighted_score": 78.4,
                "weighted_band": "strong",
                "investment_signal": "accumulate",
                "execution_strategy": "build_now",
                "conviction": "high",
                "primary_driver": "future_upside",
                "gating_issue": None,
                "verdict": "Accumulate signal with high conviction. Build now is the current strategy.",
                "weighted_components": [
                    {"key": "land_value_score", "label": "Land Value Score", "value": 78, "weight": 0.30, "contribution": 23.4},
                    {"key": "development_potential_score", "label": "Development Potential Score", "value": 82, "weight": 0.30, "contribution": 24.6},
                    {"key": "future_appreciation_index", "label": "Future Appreciation Index", "value": 76, "weight": 0.40, "contribution": 30.4},
                ],
                "rule_hits": [
                    {"code": "build_ready", "effect": "positive", "detail": "Strong development headroom and execution readiness support near-term buildability."},
                    {"code": "corridor_upside", "effect": "positive", "detail": "Future upside is reinforced by strong corridor-level infrastructure access."},
                ],
            },
            "positioning": {
                "recommended_use_case": "mixed_use",
                "favorability_band": "strong",
                "market_tier": "premium",
                "price_trend_direction": "rising",
                "price_momentum_band": "positive",
                "demand_profile": "growing",
                "site_risk_band": "contained",
                "zoning_shift_direction": "upzoned",
            },
            "strengths": ["Strong market momentum supports value retention and upside."],
            "risks": ["Regulatory clarity is still weak and needs diligence before commitment."],
            "opportunities": ["Infra proximity supports corridor-led value expansion."],
        }

        with patch("api.routers.valuation.val_svc.build_core_outputs", return_value=payload):
            r = client.get("/api/v1/valuation/core/1")

        assert r.status_code == 200
        body = r.json()
        assert body["scores"]["future_appreciation_index"] == 76
        assert body["land_value"]["band"] == "strong"
        assert body["development_potential"]["band"] == "high_capacity"
        assert body["future_appreciation"]["band"] == "high"
        assert "emerging hotspot" in body["key_insight"]
        assert body["forward_outlook"]["predicted_upside_pct"] == 8.7
        assert body["forward_outlook"]["signal"] == "positive"
        assert body["logic"]["weighted_score"] == 78.4
        assert body["logic"]["weighted_band"] == "strong"
        assert body["logic"]["investment_signal"] == "accumulate"
        assert body["positioning"]["recommended_use_case"] == "mixed_use"
        assert body["positioning"]["site_risk_band"] == "contained"

    def test_valuation_logic_route_returns_decision_payload(self):
        payload = {
            "location": "Whitefield Core",
            "location_id": 1,
            "logic": {
                "weighted_score": 78.4,
                "weighted_band": "strong",
                "investment_signal": "accumulate",
                "execution_strategy": "build_now",
                "conviction": "high",
                "primary_driver": "future_upside",
                "gating_issue": None,
                "verdict": "Accumulate signal with high conviction. Build now is the current strategy.",
                "weighted_components": [
                    {"key": "land_value_score", "label": "Land Value Score", "value": 78, "weight": 0.30, "contribution": 23.4},
                    {"key": "development_potential_score", "label": "Development Potential Score", "value": 82, "weight": 0.30, "contribution": 24.6},
                    {"key": "future_appreciation_index", "label": "Future Appreciation Index", "value": 76, "weight": 0.40, "contribution": 30.4},
                ],
                "rule_hits": [
                    {"code": "build_ready", "effect": "positive", "detail": "Strong development headroom and execution readiness support near-term buildability."},
                ],
            },
        }

        with patch("api.routers.valuation.val_svc.build_logic_layer", return_value=payload):
            r = client.get("/api/v1/valuation/logic/1")

        assert r.status_code == 200
        body = r.json()
        assert body["logic"]["weighted_score"] == 78.4
        assert body["logic"]["weighted_band"] == "strong"
        assert body["logic"]["execution_strategy"] == "build_now"
        assert body["logic"]["conviction"] == "high"

    def test_valuation_logic_route_returns_404_when_missing(self):
        with patch("api.routers.valuation.val_svc.build_logic_layer", return_value=None):
            r = client.get("/api/v1/valuation/logic/999")

        assert r.status_code == 404

    def test_predict_route_returns_ml_payload(self):
        payload = {
            "location_id": 1,
            "location_name": "Whitefield Core",
            "current_avg_price": 11200,
            "predicted_price_1yr": 12174.4,
            "predicted_price_3yr": 15652.45,
            "annual_growth_pct": 8.7,
            "confidence": "medium",
            "predicted_upside_pct": 8.7,
            "signal": "positive",
            "model_version": "growth_regression_v1",
            "training_locations": 12,
            "r_squared": 0.61,
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
            "summary": "Positive ML outlook with 8.70% projected 1Y upside. Top drivers: Future Appreciation Index, Population Growth %.",
        }

        with patch("api.routers.valuation.val_svc.predict_price_for_location", return_value=payload):
            r = client.get("/api/v1/valuation/predict/1")

        assert r.status_code == 200
        body = r.json()
        assert body["signal"] == "positive"
        assert body["predicted_upside_pct"] == 8.7
        assert body["drivers"][0]["key"] == "future_appreciation_index"

    def test_predict_route_returns_404_when_missing(self):
        with patch("api.routers.valuation.val_svc.predict_price_for_location", return_value=None):
            r = client.get("/api/v1/valuation/predict/999")

        assert r.status_code == 404

    def test_hotspots_route_returns_clustered_payload(self):
        payload = [
            SimpleNamespace(
                cluster_id=0,
                label="emerging",
                summary="Emerging cluster across 3 locations where development potential score is high and avg price / sqft is low.",
                cluster_size=3,
                hotspot_score=76.4,
                dominant_signal="buildout_corridor",
                locations=[{"location_id": 1, "name": "Whitefield Core"}],
                avg_land_value=74.0,
                avg_development_potential=82.0,
                avg_appreciation=77.0,
                avg_infra_score=71.0,
                avg_price_trend=68.0,
                avg_price=9100.0,
                feature_profile=[
                    SimpleNamespace(
                        key="development_potential_score",
                        label="Development Potential Score",
                        average=82.0,
                        delta_from_baseline=14.5,
                        relative_level="high",
                    ),
                    SimpleNamespace(
                        key="avg_price",
                        label="Avg Price / sqft",
                        average=9100.0,
                        delta_from_baseline=-1800.0,
                        relative_level="low",
                    ),
                ],
            )
        ]

        with patch("api.routers.valuation.val_svc.detect_hotspots", return_value=payload):
            r = client.get("/api/v1/valuation/hotspots?n_clusters=3")

        assert r.status_code == 200
        body = r.json()
        assert body[0]["label"] == "emerging"
        assert body[0]["cluster_size"] == 3
        assert body[0]["hotspot_score"] == 76.4
        assert body[0]["feature_profile"][0]["key"] == "development_potential_score"

    def test_valuation_core_route_returns_404_when_missing(self):
        with patch("api.routers.valuation.val_svc.build_core_outputs", return_value=None):
            r = client.get("/api/v1/valuation/core/999")

        assert r.status_code == 404

    def test_valuation_inputs_route_returns_structured_payload(self):
        payload = {
            "location": "Whitefield Core",
            "location_id": 1,
            "market": {
                "avg_price_per_sqft": 11150,
                "oldest_price_per_sqft": 10000,
                "latest_price_per_sqft": 11200,
                "price_growth_pct": 12.0,
                "annualized_growth_pct": 11.97,
                "recent_12m_growth_pct": 12.0,
                "first_recorded_date": "2024-01-01",
                "latest_recorded_date": "2025-01-01",
                "price_history_span_days": 366,
                "price_history_points": 2,
                "price_trend_direction": "rising",
                "price_momentum_band": "positive",
            },
            "planning": {
                "zoning_type": "mixed",
                "approval_status": "active",
                "fsi": 3.2,
                "max_height_m": 54,
                "ground_coverage_pct": 62,
                "masterplan_version": "RMP_2031",
                "masterplan_history_count": 2,
                "previous_zoning_type": "residential",
                "zoning_shift_direction": "upzoned",
                "zoning_shift_summary": "residential -> mixed",
                "zoning_shift_effective_from": "2025-01-01",
                "zoning_shift_score": 97.9,
                "market_tier": "premium",
                "validation_status": "validated",
                "planning_context_version": "ctx_v1",
                "location_intelligence_score": 79,
                "regional_standard_codes": ["BBMP-01", "FIRE-02"],
            },
            "demand": {
                "population": 180000,
                "growth_rate_pct": 4.6,
                "density_per_sqkm": 11800,
                "density_score": 68,
                "population_growth_score": 57.5,
                "demand_pressure_score": 62.23,
                "demand_profile": "growing",
            },
            "infrastructure": {
                "nearby_infra_count": 3,
                "planned_infra_count": 1,
                "transit_node_count": 1,
                "nearest_infra_km": 0.6,
                "nearest_transit_node_km": 0.6,
                "road_proximity_km": 0.7,
                "metro_proximity_km": 0.6,
                "economic_zone_proximity_km": 1.0,
                "road_access_score": 91.25,
                "metro_access_score": 88.0,
                "economic_access_score": 90.0,
                "strategic_infra_score": 89.58,
                "metro_station_count": 1,
                "economic_zone_count": 1,
                "highway_count": 1,
                "dominant_types": ["metro_station", "tech_park", "highway"],
            },
            "site": {
                "terrain_class": "flat",
                "terrain_slope_pct": 2,
                "road_proximity_km": 0.7,
                "transit_proximity_km": 0.5,
                "flood_risk_score": 22,
                "heat_risk_score": 28,
                "climate_risk_score": 24,
                "climate_exposure_score": 24.1,
                "terrain_constraint_score": 7.8,
                "site_risk_score": 17.58,
                "site_risk_band": "contained",
            },
            "model_inputs": {
                "infra_score": 74,
                "price_trend_score": 69,
                "annualized_growth_pct": 11.97,
                "recent_12m_growth_pct": 12.0,
                "zoning_favorability": 90,
                "road_access_score": 91.25,
                "metro_access_score": 88.0,
                "economic_access_score": 90.0,
                "strategic_infra_score": 89.58,
                "density_score": 68,
                "population_growth_score": 57.5,
                "demand_pressure_score": 62.23,
                "zoning_shift_score": 97.9,
                "climate_exposure_score": 24.1,
                "climate_resilience_score": 75,
                "terrain_constraint_score": 7.8,
                "terrain_readiness_score": 85,
                "site_risk_score": 17.58,
                "planned_infra_count": 1,
            },
        }

        with patch("api.routers.valuation.val_svc.build_valuation_inputs", return_value=payload):
            r = client.get("/api/v1/valuation/inputs/1")

        assert r.status_code == 200
        body = r.json()
        assert body["planning"]["zoning_type"] == "mixed"
        assert body["planning"]["zoning_shift_direction"] == "upzoned"
        assert body["market"]["price_trend_direction"] == "rising"
        assert body["demand"]["demand_profile"] == "growing"
        assert body["infrastructure"]["strategic_infra_score"] == 89.58
        assert body["site"]["site_risk_band"] == "contained"
        assert body["infrastructure"]["planned_infra_count"] == 1

    def test_valuation_inputs_route_returns_404_when_missing(self):
        with patch("api.routers.valuation.val_svc.build_valuation_inputs", return_value=None):
            r = client.get("/api/v1/valuation/inputs/999")

        assert r.status_code == 404


# ── AI Validation ─────────────────────────────────────────

class TestAIValidation:
    def test_query_rejects_empty(self):
        r = client.post("/api/v1/ai/query", json={"question": ""})
        assert r.status_code == 422

    def test_llm_profile_route_returns_active_provider(self):
        payload = {
            "abstraction": "provider_registry",
            "active_provider": "openai",
            "active_model": "gpt-4o",
            "providers": [
                {
                    "key": "openai",
                    "label": "OpenAI",
                    "model": "gpt-4o",
                    "is_active": True,
                    "supports_text": True,
                    "supports_json": True,
                    "supports_system_instruction": True,
                    "integration_style": "openai_compatible",
                    "open_source_ready": True,
                    "positioning": "Default provider for the current AI interface, with strong general-purpose reasoning and structured generation.",
                },
                {
                    "key": "claude",
                    "label": "Claude",
                    "model": "claude-sonnet-4-5",
                    "is_active": False,
                    "supports_text": True,
                    "supports_json": True,
                    "supports_system_instruction": True,
                    "integration_style": "native",
                    "open_source_ready": False,
                    "positioning": "Alternative Anthropic provider available through the pluggable LLM registry.",
                },
                {
                    "key": "gemini",
                    "label": "Gemini",
                    "model": "gemini-2.5-pro",
                    "is_active": False,
                    "supports_text": True,
                    "supports_json": True,
                    "supports_system_instruction": True,
                    "integration_style": "native",
                    "open_source_ready": False,
                    "positioning": "Alternative provider available through the pluggable LLM registry.",
                },
            ],
        }

        with patch("api.routers.ai.ai_svc.get_llm_profile", return_value=payload):
            r = client.get("/api/v1/ai/llm/profile")

        assert r.status_code == 200
        body = r.json()
        assert body["active_provider"] == "openai"
        assert body["providers"][0]["is_active"] is True
        assert body["providers"][0]["open_source_ready"] is True
        assert any(item["key"] == "claude" for item in body["providers"])

    def test_query_rejects_missing_field(self):
        r = client.post("/api/v1/ai/query", json={})
        assert r.status_code == 422

    def test_market_brief_returns_structured_payload(self):
        payload = {
            "summary": "Hyderabad and Pune are carrying the cleanest growth balance right now.",
            "national_thesis": "The best upside is where infra timing and planning clarity overlap.",
            "top_opportunities": [
                {
                    "location_id": 1,
                    "location_name": "HITEC City",
                    "title": "Tech corridor upside",
                    "reason": "Strong appreciation and infra support.",
                    "score": 78.5,
                }
            ],
            "watchouts": ["Climate drag can still erase upside."],
            "prompt_suggestions": ["Compare Hyderabad and Pune."],
        }

        with patch("api.routers.ai.ai_svc.market_brief", return_value=payload):
            r = client.get("/api/v1/ai/market-brief")

        assert r.status_code == 200
        body = r.json()
        assert body["national_thesis"].startswith("The best upside")
        assert body["top_opportunities"][0]["location_name"] == "HITEC City"

    def test_brain_modules_route_returns_registry(self):
        payload = [
            {
                "key": "valuation",
                "title": "Valuation Core",
                "description": "Current value, use-case fit, and weighted scoring baseline.",
                "source_system": "valuation",
                "order": 1,
                "depends_on": [],
            },
            {
                "key": "pricing",
                "title": "Forward Pricing",
                "description": "Projected 1-year and 3-year price direction from the ML layer.",
                "source_system": "valuation_ml",
                "order": 2,
                "depends_on": ["valuation"],
            },
        ]

        with patch("api.routers.ai.ai_svc.list_brain_modules", return_value=payload):
            r = client.get("/api/v1/ai/brain/modules")

        assert r.status_code == 200
        body = r.json()
        assert body[0]["key"] == "valuation"
        assert body[0]["source_system"] == "valuation"
        assert body[1]["depends_on"] == ["valuation"]

    def test_brain_architecture_route_returns_overview(self):
        payload = {
            "objective": "Keep the AI brain modular, layered, and replaceable as the system grows.",
            "style": "layered_modular_orchestrator",
            "primary_path": ["API gateway", "LLM adapter layer", "tools"],
            "layers": [
                {
                    "key": "api_gateway",
                    "title": "API Gateway",
                    "role": "Receives intelligence requests through FastAPI routes and frontend entry points, then routes them into the AI stack.",
                    "components": ["api.routers.ai"],
                    "depends_on": ["llm_adapter", "tools"],
                },
                {
                    "key": "llm_adapter",
                    "title": "LLM Adapter Layer",
                    "role": "Provides a provider-agnostic boundary for OpenAI, Claude, Gemini, and future OpenAI-compatible open-source backends.",
                    "components": ["brain.ai.llm"],
                    "depends_on": [],
                },
            ],
            "request_flow": [
                "Requests enter through the API gateway.",
                "The API gateway routes AI work through the LLM adapter layer and the structured tools layer.",
            ],
            "boundaries": [
                "Structured system outputs remain the source of truth.",
                "LLM providers are swappable behind the adapter registry.",
            ],
            "extension_points": [
                "Add new AI modules without changing the provider layer.",
                "Add new providers through the LLM registry without changing orchestration code.",
            ],
            "interfaces": [
                {
                    "key": "brain_architecture",
                    "path": "/api/v1/ai/brain/architecture",
                    "method": "GET",
                    "scope": "system",
                    "description": "Layered blueprint for how the intelligence interface is composed across subsystems.",
                }
            ],
        }

        with patch("api.routers.ai.ai_svc.get_brain_architecture", return_value=payload):
            r = client.get("/api/v1/ai/brain/architecture")

        assert r.status_code == 200
        body = r.json()
        assert body["style"] == "layered_modular_orchestrator"
        assert body["primary_path"] == ["API gateway", "LLM adapter layer", "tools"]
        assert body["layers"][0]["key"] == "api_gateway"
        assert body["interfaces"][0]["key"] == "brain_architecture"

    def test_brain_approach_route_returns_overview(self):
        payload = {
            "objective": "Intelligence interface across the system.",
            "approach": "Run the intelligence interface through an API gateway, a provider-agnostic LLM adapter layer, and structured tools that pull from the data bank, valuation engine, and blockchain rails.",
            "interface_chain": ["API gateway", "LLM adapter layer", "tools"],
            "systems": ["data_bank", "valuation", "blockchain"],
            "principles": [
                "structured_context_before_generation",
                "modular_modules_not_monolith_prompts",
            ],
            "orchestration_flow": [
                "Receive requests through the API gateway.",
                "Route provider-specific generation through the LLM adapter layer.",
            ],
            "interfaces": [
                {
                    "key": "brain_approach",
                    "path": "/api/v1/ai/brain/approach",
                    "method": "GET",
                    "scope": "system",
                    "description": "System-wide AI orchestration posture, interfaces, and active module graph.",
                }
            ],
            "modules": [
                {
                    "key": "context",
                    "title": "Location Context",
                    "description": "Planning, zoning, standards, and site context from the data bank.",
                    "source_system": "data_bank",
                    "order": 1,
                    "depends_on": [],
                }
            ],
        }

        with patch("api.routers.ai.ai_svc.get_brain_approach", return_value=payload):
            r = client.get("/api/v1/ai/brain/approach")

        assert r.status_code == 200
        body = r.json()
        assert body["objective"] == "Intelligence interface across the system."
        assert body["interface_chain"] == ["API gateway", "LLM adapter layer", "tools"]
        assert body["interfaces"][0]["key"] == "brain_approach"
        assert body["modules"][0]["source_system"] == "data_bank"

    def test_brain_profile_route_returns_modular_payload(self):
        payload = {
            "location_id": 1,
            "location_name": "Whitefield Core",
            "systems_covered": ["data_bank", "valuation", "blockchain"],
            "thesis": "Future upside is the lead signal: the parcel sits in an emerging hotspot with 8.7% projected 1Y upside and a strong mixed use fit.",
            "primary_recommendation": "Prioritize this parcel now: the model expects price to move higher from here.",
            "modules": [
                {
                    "key": "valuation",
                    "title": "Valuation Core",
                    "source_system": "valuation",
                    "summary": "Strong mixed use fit with high upside, positive price momentum, growing demand, strong corridor access, and contained site risk.",
                    "status": "ready",
                    "confidence": "high",
                    "signals": [
                        {"label": "Overall Favorability", "value": "74.2", "tone": "watch"},
                    ],
                    "payload": {"recommended_use_case": "mixed_use"},
                },
                {
                    "key": "pricing",
                    "title": "Forward Pricing",
                    "source_system": "valuation_ml",
                    "summary": "Forward view: price is projected from 11200.00 to 12174.40 in 1Y (+8.70%), with a positive signal.",
                    "status": "ready",
                    "confidence": "medium",
                    "signals": [
                        {"label": "Projected Upside", "value": "+8.7%", "tone": "watch"},
                    ],
                    "payload": {"predicted_upside_pct": 8.7},
                },
            ],
            "recommendations": [
                {
                    "label": "Underwrite Forward Price",
                    "action": "Underwrite against the projected 1Y price path, not today's spot price.",
                    "reason": "The pricing model is showing +8.7% projected 1Y movement.",
                    "priority": "high",
                }
            ],
        }

        with patch("api.routers.ai.data_svc.get_location", return_value=MagicMock(id=1)):
            with patch("api.routers.ai.ai_svc.build_brain_profile", return_value=payload):
                r = client.get("/api/v1/ai/brain/1")

        assert r.status_code == 200
        body = r.json()
        assert body["location_name"] == "Whitefield Core"
        assert body["systems_covered"] == ["data_bank", "valuation", "blockchain"]
        assert body["modules"][0]["key"] == "valuation"
        assert body["modules"][0]["source_system"] == "valuation"
        assert body["recommendations"][0]["priority"] == "high"

    def test_brain_profile_route_returns_404_when_missing(self):
        with patch("api.routers.ai.data_svc.get_location", return_value=None):
            r = client.get("/api/v1/ai/brain/999")

        assert r.status_code == 404

    def test_ai_compare_rejects_too_few_locations(self):
        r = client.post("/api/v1/ai/compare", json={"location_ids": [1]})
        assert r.status_code == 422

    def test_ai_compare_returns_structured_payload(self):
        payload = {
            "summary": "Gachibowli wins on balance.",
            "winner_location_id": 7,
            "winner_location_name": "Gachibowli",
            "verdicts": [
                {"label": "Best overall", "value": "Gachibowli", "tone": "strong"},
                {"label": "Best appreciation signal", "value": "Hinjawadi", "tone": "watch"},
            ],
            "recommended_questions": ["Why does Gachibowli lead?"],
        }

        with patch("api.routers.ai.ai_svc.compare_locations", return_value=payload):
            r = client.post("/api/v1/ai/compare", json={"location_ids": [7, 8]})

        assert r.status_code == 200
        body = r.json()
        assert body["winner_location_name"] == "Gachibowli"
        assert body["verdicts"][0]["tone"] == "strong"

    def test_ai_analyze_returns_structured_payload(self):
        payload = {
            "analysis": "## Verdict\nStrong selective buy.",
            "cards": [
                {"label": "Investment stance", "value": "Selective", "tone": "watch"},
                {"label": "Best use case", "value": "Mixed Use", "tone": "strong"},
            ],
            "recommended_questions": ["What could go wrong here?"],
        }

        with patch("api.routers.ai.data_svc.get_location", return_value=MagicMock(id=1)):
            with patch("api.routers.ai.ai_svc.analyze_location", return_value=payload):
                r = client.get("/api/v1/ai/analyze/1")

        assert r.status_code == 200
        body = r.json()
        assert body["cards"][0]["label"] == "Investment stance"
        assert body["recommended_questions"][0].startswith("What could")


# ── Planning / Blockchain Validation ──────────────────────

class TestRegistryValidation:
    def test_plan_create_requires_title(self):
        r = client.post("/api/v1/chain/plans", json={
            "author_name": "Architect A",
            "author_wallet": "0xabc",
            "file_hash": "hash-12345678",
        })
        assert r.status_code == 422

    def test_rights_check_rejects_invalid_usage_type(self):
        r = client.post("/api/v1/chain/plans/1/rights/check", json={
            "wallet": "0xabc",
            "intended_use": "broadcast",
        })
        assert r.status_code == 422

    def test_planning_context_rejects_score_above_100(self):
        r = client.post("/api/v1/data/planning-contexts", json={
            "location_id": 1,
            "country_code": "IN",
            "location_intelligence_score": 150,
        })
        assert r.status_code == 422

    def test_exchange_listing_rejects_invalid_type(self):
        r = client.post("/api/v1/chain/exchange/listings", json={
            "plan_id": 1,
            "seller_wallet": "0xabc",
            "listing_type": "auction",
            "asking_price": 1000,
        })
        assert r.status_code == 422

    def test_exchange_offer_rejects_invalid_intended_use(self):
        r = client.post("/api/v1/chain/exchange/listings/1/offers", json={
            "bidder_wallet": "0xabc",
            "offer_price": 1000,
            "intended_use": "broadcast",
        })
        assert r.status_code == 422

    def test_mint_plan_rejects_unsupported_chain(self):
        r = client.post("/api/v1/chain/plans/1/mint", json={
            "chain": "solana",
            "contract_address": "0x123456",
            "token_id": "1",
        })
        assert r.status_code == 422

    def test_tokenize_property_rejects_non_fractional_multiple_units(self):
        r = client.post("/api/v1/chain/properties/tokenize", json={
            "location_id": 1,
            "asset_name": "Residency Road Asset",
            "issuer_name": "BuiltAttic SPV",
            "issuer_wallet": "0xabc",
            "fractional_enabled": False,
            "total_units": 10,
        })
        assert r.status_code == 422

    def test_tokenize_property_rejects_unsupported_chain(self):
        r = client.post("/api/v1/chain/properties/tokenize", json={
            "location_id": 1,
            "asset_name": "Residency Road Asset",
            "issuer_name": "BuiltAttic SPV",
            "issuer_wallet": "0xabc",
            "chain": "arbitrum",
        })
        assert r.status_code == 422

    def test_property_transfer_rejects_zero_units(self):
        r = client.post("/api/v1/chain/properties/1/transfer", json={
            "transferred_by_wallet": "0xabc",
            "to_wallet": "0xdef",
            "units": 0,
        })
        assert r.status_code == 422

    def test_supported_networks_lists_polygon_and_base(self):
        r = client.get("/api/v1/chain/networks")

        assert r.status_code == 200
        payload = r.json()
        keys = {item["key"] for item in payload}
        assert {"polygon", "base"}.issubset(keys)
        assert any(item["key"] == "polygon" and item["is_default"] for item in payload)

    def test_contract_profile_is_minimal_and_auditable(self):
        r = client.get("/api/v1/chain/contracts/profile")

        assert r.status_code == 200
        payload = r.json()
        assert payload["philosophy"] == "minimal_auditable"
        assert payload["default_network"] == "polygon"
        assert "no_upgradeability" in payload["principles"]
        assert len(payload["templates"]) == 2
        assert all(item["upgradable"] is False for item in payload["templates"])

    def test_storage_profile_uses_ipfs(self):
        r = client.get("/api/v1/chain/storage/profile")

        assert r.status_code == 200
        payload = r.json()
        assert payload["backend"] == "ipfs"
        assert payload["provider"] == "ipfs"

    def test_attach_plan_ipfs_storage_requires_reference(self):
        r = client.post("/api/v1/chain/plans/1/storage/ipfs", json={})
        assert r.status_code == 422
