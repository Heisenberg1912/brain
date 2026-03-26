"""Modular AI brain orchestration layer for decision-ready parcel intelligence."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from sqlalchemy.orm import Session

from brain.blockchain import service as chain_service
from brain.data_bank import service as data_svc
from brain.valuation import service as valuation_service


MODULE_REGISTRY = (
    {
        "key": "context",
        "title": "Location Context",
        "description": "Planning, zoning, standards, and site context from the data bank.",
        "source_system": "data_bank",
        "order": 1,
        "depends_on": [],
    },
    {
        "key": "valuation",
        "title": "Valuation Core",
        "description": "Current value, use-case fit, and weighted scoring baseline.",
        "source_system": "valuation",
        "order": 2,
        "depends_on": ["context"],
    },
    {
        "key": "pricing",
        "title": "Forward Pricing",
        "description": "Projected 1-year and 3-year price direction from the ML layer.",
        "source_system": "valuation_ml",
        "order": 3,
        "depends_on": ["valuation"],
    },
    {
        "key": "hotspot",
        "title": "Cluster Context",
        "description": "How the parcel sits inside nearby growth, value, or premium clusters.",
        "source_system": "valuation_ml",
        "order": 4,
        "depends_on": ["valuation"],
    },
    {
        "key": "ownership",
        "title": "Ownership Rails",
        "description": "Plans, tokenized properties, and asset-readiness on the blockchain layer.",
        "source_system": "blockchain",
        "order": 5,
        "depends_on": ["context"],
    },
    {
        "key": "strategy",
        "title": "Execution Strategy",
        "description": "What to do next based on weighted conviction and forward price direction.",
        "source_system": "ai",
        "order": 6,
        "depends_on": ["context", "valuation", "pricing", "hotspot", "ownership"],
    },
    {
        "key": "risk",
        "title": "Risk Guardrails",
        "description": "Gating issues, data confidence, and downside watchouts.",
        "source_system": "ai",
        "order": 7,
        "depends_on": ["valuation"],
    },
)

ARCHITECTURE_LAYERS = (
    {
        "key": "api_gateway",
        "title": "API Gateway",
        "role": "Receives intelligence requests through FastAPI routes and frontend entry points, then routes them into the AI stack.",
        "components": [
            "api.routers.ai",
            "frontend/src/components/AIChat.jsx",
            "frontend/src/components/CompareView.jsx",
        ],
        "depends_on": ["llm_adapter", "tools"],
    },
    {
        "key": "llm_adapter",
        "title": "LLM Adapter Layer",
        "role": "Provides a provider-agnostic boundary for OpenAI, Claude, Gemini, and future OpenAI-compatible open-source backends.",
        "components": [
            "brain.ai.llm",
            "brain.ai.adapters.openai",
            "brain.ai.adapters.claude",
            "brain.ai.adapters.gemini",
        ],
        "depends_on": [],
    },
    {
        "key": "tools",
        "title": "Tools Layer",
        "role": "Builds structured context, composes modules, and decides when to call the LLM versus returning deterministic system outputs.",
        "components": [
            "brain.ai.service",
            "brain.ai.brain_layer",
            "brain.ai.tools",
        ],
        "depends_on": ["context", "valuation", "assets"],
    },
    {
        "key": "context",
        "title": "Context Layer",
        "role": "Supplies planning, zoning, standards, and site context from the data bank.",
        "components": [
            "brain.data_bank.service",
            "planning_contexts",
            "masterplans",
            "regional_standards",
        ],
        "depends_on": [],
    },
    {
        "key": "valuation",
        "title": "Valuation Layer",
        "role": "Owns scoring, weighted logic, price regression, hotspot detection, and forward outlook generation.",
        "components": [
            "brain.valuation.service",
            "brain.valuation.ml.price_predictor",
            "brain.valuation.ml.hotspot_detector",
        ],
        "depends_on": ["context"],
    },
    {
        "key": "assets",
        "title": "Asset Rails Layer",
        "role": "Adds ownership, licensing, and tokenization readiness from the blockchain/property layer.",
        "components": [
            "brain.blockchain.service",
            "architectural_plans",
            "tokenized_properties",
        ],
        "depends_on": ["context"],
    },
)

USE_CASE_REGISTRY = (
    {
        "key": "market_scan",
        "title": "Market Scan",
        "goal": "Surface the strongest markets and forward-looking opportunities across the active geography.",
        "audience": "Investors, strategy, acquisitions",
        "inputs": ["national rankings", "future appreciation", "development potential", "market brief context"],
        "outputs": ["market pulse", "top opportunities", "watchouts", "prompt suggestions"],
        "systems": ["valuation"],
        "endpoints": ["/api/v1/ai/market-brief"],
    },
    {
        "key": "location_underwrite",
        "title": "Location Underwrite",
        "goal": "Turn a single parcel into a decision-ready thesis with forward pricing, fit, risks, and next actions.",
        "audience": "Investment, development, architecture",
        "inputs": ["location_id", "planning context", "valuation scores", "price prediction", "hotspot context"],
        "outputs": ["brain profile", "core thesis", "recommendations", "module breakdown"],
        "systems": ["data_bank", "valuation", "blockchain"],
        "endpoints": ["/api/v1/ai/brain/{location_id}", "/api/v1/valuation/core/{location_id}"],
    },
    {
        "key": "comparative_analysis",
        "title": "Comparative Analysis",
        "goal": "Compare two or three locations and explain which option wins on balance.",
        "audience": "Investment committee, site selection, strategy",
        "inputs": ["location_ids", "valuation scores", "forward outlook", "risk tradeoffs"],
        "outputs": ["winner", "verdict cards", "comparison summary", "follow-up questions"],
        "systems": ["valuation"],
        "endpoints": ["/api/v1/ai/compare", "/api/v1/compare"],
    },
    {
        "key": "planning_feasibility",
        "title": "Planning Feasibility",
        "goal": "Explain whether a site is planning-ready by grounding floor-plan constraints, zoning rules, and location intelligence in one interface.",
        "audience": "Architecture, planning, design ops",
        "inputs": ["planning context", "masterplan", "regional standards", "massing inputs"],
        "outputs": ["context module", "planning-readiness view", "constraints and validation data"],
        "systems": ["data_bank"],
        "endpoints": ["/api/v1/ai/brain/{location_id}", "/api/v1/data/planning-contexts/{location_id}"],
    },
    {
        "key": "asset_readiness",
        "title": "Asset Readiness",
        "goal": "Show whether plans and tokenized property assets are ready for transfer, licensing, or exchange.",
        "audience": "Product ops, transactions, platform ops",
        "inputs": ["location_id", "plan registry", "tokenized property records"],
        "outputs": ["ownership module", "readiness summary", "asset counts and chain coverage"],
        "systems": ["blockchain"],
        "endpoints": ["/api/v1/ai/brain/{location_id}", "/api/v1/chain/plans", "/api/v1/chain/properties"],
    },
    {
        "key": "conversational_query",
        "title": "Conversational Query",
        "goal": "Let users ask natural-language questions while keeping structured system context as the source of truth.",
        "audience": "Anyone using the intelligence interface",
        "inputs": ["question", "optional location_id", "optional compare_ids", "tool context"],
        "outputs": ["answer", "context label"],
        "systems": ["data_bank", "valuation", "blockchain"],
        "endpoints": ["/api/v1/ai/query", "/api/v1/ai/analyze/{location_id}"],
    },
)

INTERFACE_REGISTRY = (
    {
        "key": "llm_profile",
        "path": "/api/v1/ai/llm/profile",
        "method": "GET",
        "scope": "system",
        "description": "Active LLM abstraction profile, provider capabilities, and current model selection.",
    },
    {
        "key": "brain_architecture",
        "path": "/api/v1/ai/brain/architecture",
        "method": "GET",
        "scope": "system",
        "description": "Layered blueprint for how the intelligence interface is composed across subsystems.",
    },
    {
        "key": "brain_use_cases",
        "path": "/api/v1/ai/brain/use-cases",
        "method": "GET",
        "scope": "system",
        "description": "Product-facing use-case registry for the intelligence interface.",
    },
    {
        "key": "brain_approach",
        "path": "/api/v1/ai/brain/approach",
        "method": "GET",
        "scope": "system",
        "description": "System-wide AI orchestration posture, interfaces, and active module graph.",
    },
    {
        "key": "brain_modules",
        "path": "/api/v1/ai/brain/modules",
        "method": "GET",
        "scope": "system",
        "description": "Ordered module registry for the intelligence interface.",
    },
    {
        "key": "brain_profile",
        "path": "/api/v1/ai/brain/{location_id}",
        "method": "GET",
        "scope": "location",
        "description": "Decision-ready location profile assembled across planning, valuation, pricing, hotspot, and ownership rails.",
    },
    {
        "key": "query",
        "path": "/api/v1/ai/query",
        "method": "POST",
        "scope": "query",
        "description": "Natural-language query interface grounded in the structured brain context.",
    },
    {
        "key": "analyze_location",
        "path": "/api/v1/ai/analyze/{location_id}",
        "method": "GET",
        "scope": "location",
        "description": "Narrative location analysis with cards and suggested follow-up questions.",
    },
    {
        "key": "compare_locations",
        "path": "/api/v1/ai/compare",
        "method": "POST",
        "scope": "comparison",
        "description": "Structured AI comparison across two or three selected locations.",
    },
    {
        "key": "market_brief",
        "path": "/api/v1/ai/market-brief",
        "method": "GET",
        "scope": "system",
        "description": "Top-down market pulse and opportunity scan built from the valuation layer.",
    },
)


def _read_value(source, key: str, default=None):
    if source is None:
        return default
    if isinstance(source, dict):
        return source.get(key, default)
    return getattr(source, key, default)


def _tone_for_value(value: float | None, *, high: float = 75, medium: float = 55, inverse: bool = False) -> str:
    if value is None:
        return "neutral"
    if inverse:
        if value <= medium:
            return "strong"
        if value <= high:
            return "watch"
        return "risk"
    if value >= high:
        return "strong"
    if value >= medium:
        return "watch"
    return "risk"


def _find_hotspot_for_location(session: Session, location_id: int):
    for hotspot in valuation_service.detect_hotspots(session, n_clusters=4):
        for member in _read_value(hotspot, "locations", []) or []:
            if _read_value(member, "location_id") == location_id:
                return hotspot
    return None


def _location_name(location) -> str:
    return _read_value(location, "name", "Unknown Location")


def list_module_profiles() -> list[dict[str, Any]]:
    return [dict(module) for module in MODULE_REGISTRY]


def get_brain_use_cases() -> dict[str, Any]:
    return {
        "objective": "Make the intelligence interface explicit about what it is for.",
        "use_cases": [dict(item) for item in USE_CASE_REGISTRY],
    }


def get_brain_architecture() -> dict[str, Any]:
    return {
        "objective": "Keep the AI brain modular, layered, and replaceable as the system grows.",
        "style": "layered_modular_orchestrator",
        "primary_path": ["API gateway", "LLM adapter layer", "tools"],
        "layers": [dict(layer) for layer in ARCHITECTURE_LAYERS],
        "request_flow": [
            "Requests enter through the API gateway.",
            "The API gateway routes AI work through the LLM adapter layer and the structured tools layer.",
            "The tools layer fetches context from data bank, valuation, and asset rails before any free-form generation is attempted.",
            "The LLM adapter layer optionally turns structured tool context into natural-language answers or JSON payloads.",
            "Responses return with explainable modules, recommendations, and source-system boundaries preserved.",
        ],
        "boundaries": [
            "Structured system outputs remain the source of truth.",
            "LLM providers are swappable behind the adapter registry.",
            "Valuation and asset logic stay outside prompt logic.",
            "Frontend surfaces consume AI responses without provider-specific coupling.",
        ],
        "extension_points": [
            "Add new AI modules without changing the provider layer.",
            "Add new providers through the LLM registry without changing orchestration code.",
            "Point the OpenAI-compatible slot at open-source backends later through base_url routing.",
            "Expand subsystem coverage by attaching new domain services into the orchestration layer.",
        ],
        "interfaces": [dict(item) for item in INTERFACE_REGISTRY],
    }


def get_brain_approach() -> dict[str, Any]:
    return {
        "objective": "Intelligence interface across the system.",
        "approach": "Run the intelligence interface through an API gateway, a provider-agnostic LLM adapter layer, and structured tools that pull from the data bank, valuation engine, and blockchain rails.",
        "interface_chain": ["API gateway", "LLM adapter layer", "tools"],
        "systems": ["data_bank", "valuation", "blockchain"],
        "principles": [
            "structured_context_before_generation",
            "modular_modules_not_monolith_prompts",
            "provider_agnostic_llm_boundary",
            "future_pricing_over_spot_reaction",
            "graceful_degradation_when_data_is_partial",
            "explainability_over_black_box_output",
        ],
        "orchestration_flow": [
            "Receive requests through the API gateway.",
            "Route provider-specific generation through the LLM adapter layer.",
            "Use tools to pull planning, valuation, and asset context from the core systems.",
            "Compose a decision-ready thesis, modules, and recommended next actions.",
        ],
        "interfaces": [dict(item) for item in INTERFACE_REGISTRY],
        "modules": list_module_profiles(),
    }


def _context_module(summary: dict, planning_context, core: dict) -> dict[str, Any]:
    location = summary["location"]
    masterplan = summary.get("masterplan")
    nearby_infra = summary.get("nearby_infrastructure", [])
    standards = summary.get("regional_standards", [])
    floor_plan_constraints = _read_value(planning_context, "floor_plan_constraints", {}) or {}
    location_intelligence_score = _to_float(_read_value(planning_context, "location_intelligence_score"), None)

    if masterplan:
        summary_text = (
            f"{_location_name(location)} is operating under {masterplan.zoning_type or 'current'} zoning, "
            f"with {len(nearby_infra)} nearby infra references and {len(standards)} attached standards."
        )
        status = "ready"
    else:
        summary_text = (
            f"{_location_name(location)} is missing an active masterplan record, so planning context remains partial."
        )
        status = "partial"

    return {
        "key": "context",
        "title": "Location Context",
        "source_system": "data_bank",
        "summary": summary_text,
        "status": status,
        "confidence": _read_value(core.get("coverage", {}), "confidence_band", "medium"),
        "signals": [
            {
                "label": "Zoning",
                "value": (_read_value(masterplan, "zoning_type") or "Unknown").replace("_", " ").title(),
                "tone": "strong" if masterplan else "watch",
            },
            {
                "label": "Planning Version",
                "value": _read_value(planning_context, "version_tag", "Derived"),
                "tone": "neutral",
            },
            {
                "label": "Location IQ",
                "value": f"{location_intelligence_score:.1f}" if location_intelligence_score is not None else "Unavailable",
                "tone": _tone_for_value(location_intelligence_score) if location_intelligence_score is not None else "watch",
            },
        ],
        "payload": {
            "city": _read_value(location, "city"),
            "state": _read_value(location, "state"),
            "masterplan_version": _read_value(masterplan, "version"),
            "masterplan_dataset_version": _read_value(masterplan, "dataset_version"),
            "approval_status": _read_value(masterplan, "approval_status"),
            "validation_status": _read_value(planning_context, "validation_status"),
            "nearby_infra_count": len(nearby_infra),
            "regional_standard_codes": [getattr(item, "code", None) for item in standards if getattr(item, "code", None)],
            "floor_plan_constraints": floor_plan_constraints,
            "zoning_validation_rules": _read_value(planning_context, "zoning_validation_rules", {}) or {},
            "massing_inputs": _read_value(planning_context, "massing_inputs", {}) or {},
            "source_summary": _read_value(planning_context, "source_summary"),
        },
    }


def _valuation_module(core: dict) -> dict[str, Any]:
    scores = core["scores"]
    positioning = core["positioning"]
    logic = core["logic"]
    coverage = core.get("coverage", {})
    return {
        "key": "valuation",
        "title": "Valuation Core",
        "source_system": "valuation",
        "summary": core["summary"],
        "status": "ready",
        "confidence": _read_value(coverage, "confidence_band", "medium"),
        "signals": [
            {
                "label": "Overall Favorability",
                "value": f"{scores['overall_favorability_score']:.1f}",
                "tone": _tone_for_value(scores["overall_favorability_score"]),
            },
            {
                "label": "Recommended Use",
                "value": positioning["recommended_use_case"].replace("_", " ").title(),
                "tone": "strong",
            },
            {
                "label": "Weighted Score",
                "value": f"{logic['weighted_score']:.1f}",
                "tone": _tone_for_value(logic["weighted_score"]),
            },
        ],
        "payload": {
            "key_insight": core["key_insight"],
            "land_value_score": scores["land_value_score"],
            "development_potential_score": scores["development_potential_score"],
            "future_appreciation_index": scores["future_appreciation_index"],
            "recommended_use_case": positioning["recommended_use_case"],
            "weighted_score": logic["weighted_score"],
        },
    }


def _pricing_module(core: dict) -> dict[str, Any]:
    outlook = core.get("forward_outlook")
    if not outlook:
        return {
            "key": "pricing",
            "title": "Forward Pricing",
            "source_system": "valuation_ml",
            "summary": "Forward price direction is unavailable because the prediction layer does not have enough usable data yet.",
            "status": "unavailable",
            "confidence": "low",
            "signals": [],
            "payload": {},
        }

    return {
        "key": "pricing",
        "title": "Forward Pricing",
        "source_system": "valuation_ml",
        "summary": outlook["summary"],
        "status": "ready",
        "confidence": outlook.get("confidence") or "medium",
        "signals": [
            {
                "label": "Current Price",
                "value": f"Rs {outlook['current_avg_price']:.0f}/sqft",
                "tone": "neutral",
            },
            {
                "label": "1Y Price",
                "value": f"Rs {outlook['predicted_price_1yr']:.0f}/sqft",
                "tone": _tone_for_value(outlook["predicted_upside_pct"], high=10, medium=3),
            },
            {
                "label": "Projected Upside",
                "value": f"{outlook['predicted_upside_pct']:+.1f}%",
                "tone": _tone_for_value(outlook["predicted_upside_pct"], high=10, medium=3),
            },
        ],
        "payload": outlook,
    }


def _hotspot_module(hotspot) -> dict[str, Any]:
    if not hotspot:
        return {
            "key": "hotspot",
            "title": "Cluster Context",
            "source_system": "valuation_ml",
            "summary": "The parcel is not currently sitting inside a standout hotspot cluster, so cluster context is only partial.",
            "status": "partial",
            "confidence": "low",
            "signals": [],
            "payload": {},
        }

    hotspot_score = _read_value(hotspot, "hotspot_score")
    label = _read_value(hotspot, "label", "stable")
    return {
        "key": "hotspot",
        "title": "Cluster Context",
        "source_system": "valuation_ml",
        "summary": _read_value(hotspot, "summary", "Cluster context is available."),
        "status": "ready",
        "confidence": "high" if _tone_for_value(hotspot_score, high=75, medium=60) == "strong" else "medium",
        "signals": [
            {
                "label": "Cluster Label",
                "value": label.replace("_", " ").title(),
                "tone": "strong" if label in {"undervalued", "emerging", "high_growth"} else "watch",
            },
            {
                "label": "Hotspot Score",
                "value": f"{_to_float(hotspot_score):.1f}",
                "tone": _tone_for_value(_to_float(hotspot_score)),
            },
            {
                "label": "Cluster Size",
                "value": str(_read_value(hotspot, "cluster_size", 0)),
                "tone": "neutral",
            },
        ],
        "payload": {
            "label": label,
            "hotspot_score": hotspot_score,
            "dominant_signal": _read_value(hotspot, "dominant_signal"),
            "feature_profile": _read_value(hotspot, "feature_profile", []),
        },
    }


def _ownership_module(session: Session, location_id: int) -> dict[str, Any]:
    plans = chain_service.list_plans(session, location_id=location_id)
    tokenized_properties = chain_service.list_tokenized_properties(session, location_id=location_id, status=None)
    active_properties = [item for item in tokenized_properties if _read_value(item, "status", "active") == "active"]
    fractional_properties = [item for item in active_properties if bool(_read_value(item, "fractional_enabled", False))]
    chains = sorted(
        {
            (_read_value(item, "chain") or "").lower()
            for item in [*plans, *tokenized_properties]
            if _read_value(item, "chain")
        }
    )

    if plans or tokenized_properties:
        summary_text = (
            f"The location has {len(plans)} registered plan assets and {len(tokenized_properties)} tokenized property assets "
            f"attached to it."
        )
        status = "ready"
        confidence = "high"
    else:
        summary_text = "No on-ledger plan or tokenized property assets are attached to this location yet."
        status = "partial"
        confidence = "low"

    return {
        "key": "ownership",
        "title": "Ownership Rails",
        "source_system": "blockchain",
        "summary": summary_text,
        "status": status,
        "confidence": confidence,
        "signals": [
            {
                "label": "Plan Assets",
                "value": str(len(plans)),
                "tone": "strong" if plans else "watch",
            },
            {
                "label": "Tokenized Properties",
                "value": str(len(tokenized_properties)),
                "tone": "strong" if tokenized_properties else "watch",
            },
            {
                "label": "Fractional Ready",
                "value": str(len(fractional_properties)),
                "tone": "strong" if fractional_properties else "neutral",
            },
        ],
        "payload": {
            "plan_count": len(plans),
            "tokenized_property_count": len(tokenized_properties),
            "active_tokenized_property_count": len(active_properties),
            "fractional_property_count": len(fractional_properties),
            "chains": chains,
            "plans": [
                {
                    "plan_id": _read_value(plan, "id"),
                    "title": _read_value(plan, "title"),
                    "asset_status": _read_value(plan, "asset_status"),
                    "current_owner_wallet": _read_value(plan, "current_owner_wallet"),
                }
                for plan in plans[:3]
            ],
            "properties": [
                {
                    "property_id": _read_value(item, "id"),
                    "asset_name": _read_value(item, "asset_name"),
                    "status": _read_value(item, "status"),
                    "chain": _read_value(item, "chain"),
                    "fractional_enabled": bool(_read_value(item, "fractional_enabled", False)),
                }
                for item in tokenized_properties[:3]
            ],
        },
    }


def _strategy_module(core: dict) -> dict[str, Any]:
    logic = core["logic"]
    summary = logic.get("verdict") or core.get("key_insight") or "Execution strategy is available."
    return {
        "key": "strategy",
        "title": "Execution Strategy",
        "source_system": "ai",
        "summary": summary,
        "status": "ready",
        "confidence": logic["conviction"],
        "signals": [
            {
                "label": "Investment Signal",
                "value": logic["investment_signal"].replace("_", " ").title(),
                "tone": "strong" if logic["investment_signal"] in {"acquire", "accumulate"} else "watch",
            },
            {
                "label": "Execution",
                "value": logic["execution_strategy"].replace("_", " ").title(),
                "tone": "strong" if logic["execution_strategy"] in {"build_now", "entitle_then_build"} else "watch",
            },
            {
                "label": "Primary Driver",
                "value": logic["primary_driver"].replace("_", " ").title(),
                "tone": "neutral",
            },
        ],
        "payload": {
            "key_insight": core["key_insight"],
            "gating_issue": logic.get("gating_issue"),
            "weighted_components": logic.get("weighted_components", []),
        },
    }


def _risk_module(core: dict) -> dict[str, Any]:
    logic = core["logic"]
    coverage = core.get("coverage", {})
    positioning = core["positioning"]
    risks = core.get("risks", [])
    gating_issue = logic.get("gating_issue")
    site_risk_band = positioning.get("site_risk_band")
    summary = (
        f"{gating_issue.replace('_', ' ').title()} is the active guardrail and should be cleared before leaning fully into the upside case."
        if gating_issue
        else f"Risk posture is currently {site_risk_band or 'managed'}, with {coverage.get('confidence_band', 'medium')} evidence coverage behind the signal."
    )
    return {
        "key": "risk",
        "title": "Risk Guardrails",
        "source_system": "ai",
        "summary": summary,
        "status": "partial" if gating_issue or coverage.get("confidence_band") == "low" else "ready",
        "confidence": coverage.get("confidence_band", "medium"),
        "signals": [
            {
                "label": "Data Confidence",
                "value": coverage.get("confidence_band", "medium").title(),
                "tone": "strong" if coverage.get("confidence_band") == "high" else "watch",
            },
            {
                "label": "Site Risk",
                "value": (site_risk_band or "unknown").title(),
                "tone": "risk" if site_risk_band in {"severe", "elevated"} else "watch" if site_risk_band == "managed" else "strong",
            },
            {
                "label": "Gating Issue",
                "value": gating_issue.replace("_", " ").title() if gating_issue else "None",
                "tone": "risk" if gating_issue else "neutral",
            },
        ],
        "payload": {
            "risks": risks[:3],
            "data_gaps": coverage.get("data_gaps", []),
        },
    }


def _to_float(value, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _primary_recommendation(core: dict) -> str:
    logic = core["logic"]
    outlook = core.get("forward_outlook")
    gating_issue = logic.get("gating_issue")
    if gating_issue:
        return f"Clear {gating_issue.replace('_', ' ')} before underwriting forward upside."
    if outlook and outlook["signal"] in {"bullish", "positive"} and logic["investment_signal"] in {"acquire", "accumulate"}:
        return "Prioritize this parcel now: the model expects price to move higher from here."
    if logic["investment_signal"] == "watch":
        return "Keep the parcel on an active watchlist and wait for either stronger evidence or cleaner forward pricing."
    return f"Advance selective diligence with a {logic['execution_strategy'].replace('_', ' ')} posture."


def _build_recommendations(
    core: dict,
    *,
    context_module: dict[str, Any] | None = None,
    ownership_module: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    logic = core["logic"]
    outlook = core.get("forward_outlook")
    recommendations: list[dict[str, Any]] = []

    if context_module and context_module.get("status") != "ready":
        recommendations.append({
            "label": "Backfill Planning Context",
            "action": "Attach a current masterplan and planning context record before treating the parcel as fully decision-ready.",
            "reason": "The intelligence interface is missing part of the planning layer, which weakens zoning and floor-plan confidence.",
            "priority": "high",
        })
    if logic.get("gating_issue"):
        gate = logic["gating_issue"].replace("_", " ")
        recommendations.append({
            "label": "Clear The Gate",
            "action": f"Resolve {gate} before committing design or capital.",
            "reason": "The weighted case is being capped by a live blocking issue.",
            "priority": "high",
        })
    if outlook and outlook["signal"] in {"bullish", "positive"}:
        recommendations.append({
            "label": "Underwrite Forward Price",
            "action": f"Underwrite against the projected 1Y price path, not today's spot price.",
            "reason": f"The pricing model is showing {outlook['predicted_upside_pct']:+.1f}% projected 1Y movement.",
            "priority": "high" if logic["investment_signal"] in {"acquire", "accumulate"} else "medium",
        })
    if ownership_module and ownership_module.get("status") != "ready":
        recommendations.append({
            "label": "Prepare Ownership Rails",
            "action": "Register the plan or property asset so rights, transferability, and exchange readiness are in place before go-to-market.",
            "reason": "The blockchain layer is not attached yet, so the parcel is not operationally ready for plan or property transactions.",
            "priority": "medium",
        })
    recommendations.append({
        "label": "Match Program To Fit",
        "action": f"Bias diligence toward {core['positioning']['recommended_use_case'].replace('_', ' ')} execution.",
        "reason": "That is the cleanest current use-case fit in the valuation layer.",
        "priority": "medium",
    })

    return recommendations[:4]


def build_brain_profile(session: Session, location_id: int) -> dict[str, Any] | None:
    location = data_svc.get_location(session, location_id)
    if not location:
        return None

    summary = data_svc.get_location_summary(session, location_id)
    if not summary:
        return None

    planning_context = data_svc.get_planning_context(session, location_id)
    if planning_context is None:
        planning_context = SimpleNamespace(
            **data_svc.derive_planning_context_payload(session, location_id, version_tag="brain_shadow_v1")
        )

    price_prediction = valuation_service.predict_price_for_location(session, location_id)
    hotspot = _find_hotspot_for_location(session, location_id)
    core = valuation_service.build_core_outputs(
        session,
        location_id,
        price_prediction=price_prediction,
        hotspot=hotspot,
    )
    if not core:
        return None

    context_module = _context_module(summary, planning_context, core)
    ownership_module = _ownership_module(session, location_id)
    modules = [
        context_module,
        _valuation_module(core),
        _pricing_module(core),
        _hotspot_module(hotspot),
        ownership_module,
        _strategy_module(core),
        _risk_module(core),
    ]

    return {
        "location_id": location_id,
        "location_name": _location_name(location),
        "systems_covered": ["data_bank", "valuation", "blockchain"],
        "thesis": core["key_insight"],
        "primary_recommendation": _primary_recommendation(core),
        "modules": modules,
        "recommendations": _build_recommendations(
            core,
            context_module=context_module,
            ownership_module=ownership_module,
        ),
    }
