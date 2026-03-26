"""Tests for the modular AI brain layer."""
from types import SimpleNamespace

import brain.ai.brain_layer as brain_layer


def test_list_module_profiles_returns_ordered_registry():
    profiles = brain_layer.list_module_profiles()

    assert [item["key"] for item in profiles] == [
        "context",
        "valuation",
        "pricing",
        "hotspot",
        "ownership",
        "strategy",
        "risk",
    ]
    assert profiles[0]["source_system"] == "data_bank"
    assert profiles[2]["depends_on"] == ["valuation"]


def test_get_brain_approach_returns_cross_system_overview():
    payload = brain_layer.get_brain_approach()

    assert payload["objective"] == "Intelligence interface across the system."
    assert payload["interface_chain"] == ["API gateway", "LLM adapter layer", "tools"]
    assert payload["systems"] == ["data_bank", "valuation", "blockchain"]
    assert payload["modules"][0]["key"] == "context"
    assert payload["interfaces"][0]["key"] == "llm_profile"
    assert any(item["key"] == "compare_locations" for item in payload["interfaces"])


def test_get_brain_use_cases_returns_product_registry():
    payload = brain_layer.get_brain_use_cases()

    assert payload["objective"] == "Make the intelligence interface explicit about what it is for."
    assert payload["use_cases"][0]["key"] == "market_scan"
    assert any(item["key"] == "location_underwrite" for item in payload["use_cases"])
    assert any("/api/v1/ai/query" in item["endpoints"] for item in payload["use_cases"])


def test_get_brain_architecture_returns_layered_blueprint():
    payload = brain_layer.get_brain_architecture()

    assert payload["style"] == "layered_modular_orchestrator"
    assert payload["primary_path"] == ["API gateway", "LLM adapter layer", "tools"]
    assert payload["layers"][0]["key"] == "api_gateway"
    assert any(item["key"] == "llm_adapter" for item in payload["layers"])
    assert any(item["key"] == "brain_architecture" for item in payload["interfaces"])
    assert "Structured system outputs remain the source of truth." in payload["boundaries"]


def test_build_brain_profile_returns_modular_response(monkeypatch):
    monkeypatch.setattr(
        brain_layer.data_svc,
        "get_location",
        lambda _session, _location_id: SimpleNamespace(id=1, name="Whitefield Core", city="Bengaluru", state="Karnataka"),
    )
    monkeypatch.setattr(
        brain_layer.data_svc,
        "get_location_summary",
        lambda _session, _location_id: {
            "location": SimpleNamespace(id=1, name="Whitefield Core", city="Bengaluru", state="Karnataka"),
            "masterplan": SimpleNamespace(
                zoning_type="mixed_use",
                version="2030",
                dataset_version="mp_v3",
                approval_status="approved",
            ),
            "nearby_infrastructure": [{"name": "Metro"}, {"name": "Ring Road"}],
            "regional_standards": [SimpleNamespace(code="NBC-2016"), SimpleNamespace(code="KA-BLDG")],
        },
    )
    monkeypatch.setattr(
        brain_layer.data_svc,
        "get_planning_context",
        lambda _session, _location_id: SimpleNamespace(
            version_tag="brain_shadow_v1",
            validation_status="validated",
            location_intelligence_score=81.4,
            floor_plan_constraints={"fsi": 3.5, "max_height_m": 60},
            zoning_validation_rules={"approval_status": "approved"},
            massing_inputs={"coverage_pct": 45},
            source_summary="Derived from current masterplan and location profile.",
        ),
    )
    monkeypatch.setattr(
        brain_layer.valuation_service,
        "predict_price_for_location",
        lambda _session, _location_id: {
            "current_avg_price": 11200,
            "predicted_price_1yr": 12174.4,
            "predicted_price_3yr": 15652.45,
            "predicted_upside_pct": 8.7,
            "annual_growth_pct": 8.7,
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
                }
            ],
        },
    )
    monkeypatch.setattr(
        brain_layer.valuation_service,
        "detect_hotspots",
        lambda _session, n_clusters=4: [
            SimpleNamespace(
                label="emerging",
                summary="Emerging cluster across 3 locations where development potential score is high and avg price / sqft is low.",
                cluster_size=3,
                hotspot_score=76.4,
                dominant_signal="buildout_corridor",
                feature_profile=[],
                locations=[{"location_id": 1, "name": "Whitefield Core"}],
            )
        ],
    )
    monkeypatch.setattr(
        brain_layer.valuation_service,
        "build_core_outputs",
        lambda _session, _location_id, **_kwargs: {
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
                    }
                ],
            },
            "coverage": {
                "confidence_band": "high",
                "data_gaps": [],
            },
            "scores": {
                "land_value_score": 78,
                "development_potential_score": 82,
                "future_appreciation_index": 76,
                "overall_favorability_score": 74.2,
            },
            "logic": {
                "weighted_score": 78.4,
                "investment_signal": "accumulate",
                "execution_strategy": "build_now",
                "conviction": "high",
                "primary_driver": "future_upside",
                "gating_issue": None,
                "weighted_components": [],
            },
            "positioning": {
                "recommended_use_case": "mixed_use",
                "site_risk_band": "contained",
            },
            "risks": ["Regulatory clarity needs diligence."],
        },
    )
    monkeypatch.setattr(
        brain_layer.chain_service,
        "list_plans",
        lambda _session, location_id=None: [
            SimpleNamespace(id=11, title="Tower A", asset_status="minted", current_owner_wallet="0xabc", chain="polygon")
        ],
    )
    monkeypatch.setattr(
        brain_layer.chain_service,
        "list_tokenized_properties",
        lambda _session, location_id=None, status=None: [
            SimpleNamespace(id=21, asset_name="Whitefield Core Parcel", status="active", chain="polygon", fractional_enabled=True)
        ],
    )

    payload = brain_layer.build_brain_profile(None, 1)

    assert payload is not None
    assert payload["location_name"] == "Whitefield Core"
    assert payload["systems_covered"] == ["data_bank", "valuation", "blockchain"]
    assert payload["primary_recommendation"].startswith("Prioritize this parcel now")
    assert [module["key"] for module in payload["modules"]] == [
        "context",
        "valuation",
        "pricing",
        "hotspot",
        "ownership",
        "strategy",
        "risk",
    ]
    assert payload["modules"][0]["source_system"] == "data_bank"
    assert payload["modules"][2]["payload"]["predicted_upside_pct"] == 8.7
    assert payload["modules"][3]["payload"]["label"] == "emerging"
    assert payload["modules"][4]["payload"]["plan_count"] == 1
    assert payload["recommendations"][0]["label"] == "Underwrite Forward Price"


def test_build_brain_profile_returns_none_for_unknown_location(monkeypatch):
    monkeypatch.setattr(brain_layer.data_svc, "get_location", lambda _session, _location_id: None)

    assert brain_layer.build_brain_profile(None, 999) is None
