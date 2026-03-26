"""AI service: API gateway -> adapter registry -> structured tools."""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from brain.ai import brain_layer
from brain.ai import llm as llm_layer
from brain.ai.adapters import LLMAdapter
from brain.ai.tools import build_compare_tool_context, build_location_tool_context, build_market_tool_context
from brain.data_bank import service as data_svc
from brain.valuation import service as valuation_service


def _get_llm() -> LLMAdapter:
    return llm_layer.get_llm()


SYSTEM_PROMPT = """You are BuiltAttic Brain, an AI real estate intelligence interface.

Rules:
- Treat structured data and valuation outputs as the source of truth.
- Use forward-looking logic: zoning shifts, infra pipeline, density, terrain, climate risk, and price direction.
- Be concise but concrete with numbers.
- If data is missing, say so plainly instead of inventing it.
- The LLM is an interface layer; do not contradict the supplied intelligence context.
"""


def _context_label(session: Session, *, location_id: int | None = None, compare_ids: list[int] | None = None) -> str | None:
    compare_ids = compare_ids or []
    if compare_ids:
        names = []
        for compare_id in compare_ids[:3]:
            location = data_svc.get_location(session, compare_id)
            if location:
                names.append(location.name)
        return " vs ".join(names) if names else None
    if location_id:
        location = data_svc.get_location(session, location_id)
        if location:
            return location.name
    return None


def _generate_json(llm: LLMAdapter, prompt: str, *, fallback: dict[str, Any], system_instruction: str) -> dict[str, Any]:
    generate_json = getattr(llm, "generate_json", None)
    if callable(generate_json):
        try:
            result = generate_json(prompt, system_instruction=system_instruction)
            if isinstance(result, dict):
                return result
        except Exception:
            pass
    return fallback


def _tone_for_score(value: float | None) -> str:
    if value is None:
        return "neutral"
    if value >= 75:
        return "strong"
    if value >= 55:
        return "watch"
    return "risk"


def _fallback_market_brief(session: Session) -> dict[str, Any]:
    valuation_service.score_all_locations(session)
    rankings = valuation_service.get_rankings(session, top_n=4, sort_by="future_appreciation_index")
    top = rankings[0] if rankings else None
    opportunities = [
        {
            "location_id": item["location_id"],
            "location_name": item["location"],
            "title": "Forward appreciation leader",
            "reason": (
                f"Future appreciation {item['future_appreciation_index']:.1f}, "
                f"development potential {item['development_potential_score']:.1f}, "
                f"land value {item['land_value_score']:.1f}."
            ),
            "score": round(float(item["future_appreciation_index"]), 2),
        }
        for item in rankings
    ]
    return {
        "summary": (
            f"{top['location']} currently leads the national sample on forward appreciation."
            if top else
            "The national sample is ready, but there is not enough ranked data yet."
        ),
        "national_thesis": "Momentum is strongest where appreciation, development headroom, and transport-linked access are all aligned.",
        "top_opportunities": opportunities,
        "watchouts": [
            "Do not treat appreciation alone as a buy signal; climate and regulatory clarity can still cap execution.",
            "Use state and city standards together, especially in coastal and high-density markets.",
        ],
        "prompt_suggestions": [
            "Which market has the cleanest 3-year upside right now?",
            "Compare Pune and Hyderabad growth corridors.",
            "Where is commercial development most defensible?",
        ],
    }


def _fallback_location_analysis(session: Session, location_id: int) -> dict[str, Any]:
    summary = data_svc.get_location_summary(session, location_id)
    valuation = valuation_service.get_or_compute_score(session, location_id)
    favorability = valuation_service.build_favorability_profile(session, location_id)
    prediction = valuation_service.predict_price_for_location(session, location_id)

    if not summary or not valuation:
        return {
            "analysis": "Location data is unavailable.",
            "cards": [],
            "recommended_questions": [],
        }

    location = summary["location"]
    best_use_case = favorability["recommended_use_case"].replace("_", " ") if favorability else "mixed use"
    overall_score = favorability["overall_favorability_score"] if favorability else None
    current_price = summary.get("avg_price_per_sqft")
    one_year = getattr(prediction, "predicted_price_1yr", None)
    three_year = getattr(prediction, "predicted_price_3yr", None)

    cards = [
        {
            "label": "Investment stance",
            "value": favorability["favorability_band"].title() if favorability else "Selective",
            "tone": _tone_for_score(overall_score),
        },
        {
            "label": "Best use case",
            "value": best_use_case.title(),
            "tone": "strong",
        },
        {
            "label": "1-year outlook",
            "value": f"Rs {round(one_year):,}/sqft" if one_year else "Insufficient data",
            "tone": _tone_for_score(valuation.get("future_appreciation_index")),
        },
        {
            "label": "3-year outlook",
            "value": f"Rs {round(three_year):,}/sqft" if three_year else "Insufficient data",
            "tone": _tone_for_score(valuation.get("development_potential_score")),
        },
    ]

    analysis = (
        f"**{location.name}** in {location.city}, {getattr(location, 'state', '') or 'India'} is currently a "
        f"**{favorability['favorability_band']}** opportunity with land value "
        f"`{valuation['land_value_score']:.1f}` and future appreciation `{valuation['future_appreciation_index']:.1f}`.\n\n"
        f"The strongest near-term fit is **{best_use_case.replace('_', ' ')}**, while the main diligence focus "
        f"should stay on regulatory clarity, infrastructure timing, and climate exposure."
    )
    return {
        "analysis": analysis,
        "cards": cards,
        "recommended_questions": [
            f"What are the biggest risks in {location.name}?",
            f"Should I prioritize {location.name} for {best_use_case.replace('_', ' ')} development?",
            f"Compare {location.name} with another leading market.",
        ],
    }


def _fallback_compare_insight(session: Session, location_ids: list[int]) -> dict[str, Any]:
    rows = valuation_service.compare_locations(session, location_ids)
    if not rows:
        return {
            "summary": "No valid locations were available for comparison.",
            "winner_location_id": None,
            "winner_location_name": None,
            "verdicts": [],
            "recommended_questions": [],
        }

    ranked = sorted(
        rows,
        key=lambda row: (
            row["land_value_score"] * 0.3
            + row["development_potential_score"] * 0.3
            + row["future_appreciation_index"] * 0.4
        ),
        reverse=True,
    )
    winner = ranked[0]
    best_land_value = max(rows, key=lambda row: row["land_value_score"])
    best_development = max(rows, key=lambda row: row["development_potential_score"])
    best_appreciation = max(rows, key=lambda row: row["future_appreciation_index"])
    return {
        "summary": (
            f"{winner['location']} is the strongest overall option in this set, with the most balanced mix of "
            "current value, development headroom, and forward appreciation."
        ),
        "winner_location_id": winner["location_id"],
        "winner_location_name": winner["location"],
        "verdicts": [
            {"label": "Best overall", "value": winner["location"], "tone": "strong"},
            {"label": "Highest land value", "value": best_land_value["location"], "tone": _tone_for_score(best_land_value["land_value_score"])},
            {"label": "Best development upside", "value": best_development["location"], "tone": _tone_for_score(best_development["development_potential_score"])},
            {"label": "Best appreciation signal", "value": best_appreciation["location"], "tone": _tone_for_score(best_appreciation["future_appreciation_index"])},
        ],
        "recommended_questions": [
            f"Why does {winner['location']} rank ahead of the others?",
            f"What could invalidate the bull case for {winner['location']}?",
            "Which comparison market has the cleanest risk-adjusted upside?",
        ],
    }


def query(
    session: Session,
    user_query: str,
    *,
    location_id: int | None = None,
    compare_ids: list[int] | None = None,
) -> dict[str, Any]:
    llm = _get_llm()
    market_context = build_market_tool_context(session, top_n=8)
    context_blocks = [market_context]
    context_label = _context_label(session, location_id=location_id, compare_ids=compare_ids)

    if compare_ids:
        compare_context = build_compare_tool_context(session, compare_ids)
        if compare_context:
            context_blocks.append(f"## Active Comparison Context\n{compare_context}")
    elif location_id:
        location_context = build_location_tool_context(session, location_id)
        if location_context:
            context_blocks.append(f"## Active Location Context\n{location_context}")

    prompt = f"""Answer the following question using the supplied structured intelligence context.

Question: {user_query}

{'\n\n'.join(context_blocks)}

Focus on the best options and explain why with scores, forecast direction, and risk tradeoffs."""

    return {
        "answer": llm.generate(prompt, system_instruction=SYSTEM_PROMPT),
        "context_label": context_label,
    }


def analyze_location(session: Session, location_id: int) -> dict[str, Any]:
    llm = _get_llm()
    summary = data_svc.get_location_summary(session, location_id)
    if not summary:
        return {"analysis": "Location not found.", "cards": [], "recommended_questions": []}

    context = build_location_tool_context(session, location_id)
    fallback = _fallback_location_analysis(session, location_id)

    prompt = f"""Provide a focused analysis for this location and return valid JSON.

{context}

Return this shape exactly:
{{
  "analysis": "markdown string with headings and concise bullets",
  "cards": [
    {{"label": "Investment stance", "value": "Strong / Selective / Watch", "tone": "strong|watch|risk|neutral"}},
    {{"label": "Best use case", "value": "Mixed Use", "tone": "strong"}},
    {{"label": "1-year outlook", "value": "Rs 12,300/sqft", "tone": "watch"}},
    {{"label": "3-year outlook", "value": "Rs 15,800/sqft", "tone": "strong"}}
  ],
  "recommended_questions": ["string", "string", "string"]
}}

The analysis must cover:
1. Investment stance
2. Best architectural or development use case
3. Key regulatory or climate constraints
4. 1-year and 3-year market outlook
5. Important alternatives or watch-outs"""

    result = _generate_json(llm, prompt, fallback=fallback, system_instruction=SYSTEM_PROMPT)
    return {
        "analysis": result.get("analysis") or fallback["analysis"],
        "cards": result.get("cards") or fallback["cards"],
        "recommended_questions": result.get("recommended_questions") or fallback["recommended_questions"],
    }


def market_brief(session: Session) -> dict[str, Any]:
    llm = _get_llm()
    market_context = build_market_tool_context(session, top_n=10)
    fallback = _fallback_market_brief(session)

    prompt = f"""Build a concise India market brief from the supplied data and return valid JSON.

{market_context}

Return this shape exactly:
{{
  "summary": "2-3 sentence market pulse",
  "national_thesis": "1 sentence thesis",
  "top_opportunities": [
    {{
      "location_id": 1,
      "location_name": "Example",
      "title": "short title",
      "reason": "1 sentence rationale grounded in the data",
      "score": 74.5
    }}
  ],
  "watchouts": ["string", "string"],
  "prompt_suggestions": ["string", "string", "string"]
}}

Keep it tight, practical, and decision-oriented."""

    result = _generate_json(llm, prompt, fallback=fallback, system_instruction=SYSTEM_PROMPT)
    return {
        "summary": result.get("summary") or fallback["summary"],
        "national_thesis": result.get("national_thesis") or fallback["national_thesis"],
        "top_opportunities": result.get("top_opportunities") or fallback["top_opportunities"],
        "watchouts": result.get("watchouts") or fallback["watchouts"],
        "prompt_suggestions": result.get("prompt_suggestions") or fallback["prompt_suggestions"],
    }


def compare_locations(session: Session, location_ids: list[int]) -> dict[str, Any]:
    llm = _get_llm()
    compare_context = build_compare_tool_context(session, location_ids)
    fallback = _fallback_compare_insight(session, location_ids)

    prompt = f"""Compare the selected locations using the supplied structured context and return valid JSON.

{compare_context}

Return this shape exactly:
{{
  "summary": "2-3 sentence verdict",
  "winner_location_id": 1,
  "winner_location_name": "Example",
  "verdicts": [
    {{"label": "Best overall", "value": "Example", "tone": "strong"}},
    {{"label": "Highest land value", "value": "Example", "tone": "watch"}},
    {{"label": "Best development upside", "value": "Example", "tone": "strong"}},
    {{"label": "Best appreciation signal", "value": "Example", "tone": "strong"}}
  ],
  "recommended_questions": ["string", "string", "string"]
}}

Make the verdict decisive, numerical where possible, and grounded in the supplied scores."""

    result = _generate_json(llm, prompt, fallback=fallback, system_instruction=SYSTEM_PROMPT)
    return {
        "summary": result.get("summary") or fallback["summary"],
        "winner_location_id": result.get("winner_location_id", fallback["winner_location_id"]),
        "winner_location_name": result.get("winner_location_name") or fallback["winner_location_name"],
        "verdicts": result.get("verdicts") or fallback["verdicts"],
        "recommended_questions": result.get("recommended_questions") or fallback["recommended_questions"],
    }


def list_brain_modules() -> list[dict[str, Any]]:
    return brain_layer.list_module_profiles()


def get_llm_profile() -> dict[str, Any]:
    return llm_layer.get_llm_profile()


def get_brain_use_cases() -> dict[str, Any]:
    return brain_layer.get_brain_use_cases()


def get_brain_architecture() -> dict[str, Any]:
    return brain_layer.get_brain_architecture()


def get_brain_approach() -> dict[str, Any]:
    return brain_layer.get_brain_approach()


def build_brain_profile(session: Session, location_id: int) -> dict[str, Any] | None:
    return brain_layer.build_brain_profile(session, location_id)
