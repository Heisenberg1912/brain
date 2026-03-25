"""Structured tool helpers for the AI layer."""
from __future__ import annotations

import json

from sqlalchemy.orm import Session

from brain.data_bank import service as data_svc
from brain.valuation import service as valuation_service


def _dump(payload: dict | list) -> str:
    return json.dumps(payload, indent=2, ensure_ascii=True, default=str)


def build_location_tool_context(session: Session, location_id: int) -> str:
    record = data_svc.build_location_intelligence_record(session, location_id)
    valuation_inputs = valuation_service.build_valuation_inputs(session, location_id)
    favorability = valuation_service.build_favorability_profile(session, location_id)
    summary = data_svc.get_location_summary(session, location_id)
    if not record or not summary:
        return ""

    location = summary["location"]
    payload = {
        "location": {
            "id": location.id,
            "name": location.name,
            "country_code": getattr(location, "country_code", "IN"),
            "state": getattr(location, "state", None),
            "city": location.city,
            "locality": location.locality,
            "ward": location.ward,
            "pin_code": location.pin_code,
        },
        "intelligence_record": record,
        "valuation_inputs": valuation_inputs,
        "favorability_profile": favorability,
    }
    return _dump(payload)


def build_market_tool_context(session: Session, *, top_n: int = 8) -> str:
    valuation_service.score_all_locations(session)
    rankings = valuation_service.get_rankings(session, top_n=top_n, sort_by="future_appreciation_index")
    favorability = valuation_service.get_favorability_rankings(session, top_n=top_n, use_case="overall")
    hotspots = valuation_service.detect_hotspots(session, n_clusters=4)
    locations = data_svc.get_all_locations(session)
    states = sorted({location.state for location in locations if getattr(location, "state", None)})

    payload = {
        "coverage": {
            "locations": len(locations),
            "states": states,
            "state_count": len(states),
        },
        "future_appreciation_rankings": rankings,
        "overall_favorability_rankings": favorability,
        "hotspots": [
            {
                "cluster_id": hotspot.cluster_id,
                "label": hotspot.label,
                "avg_land_value": hotspot.avg_land_value,
                "avg_appreciation": hotspot.avg_appreciation,
                "avg_price": hotspot.avg_price,
                "members": hotspot.locations,
            }
            for hotspot in hotspots
        ],
    }
    return _dump(payload)


def build_compare_tool_context(session: Session, location_ids: list[int]) -> str:
    payload = []
    for location_id in location_ids:
        detail = data_svc.get_location_summary(session, location_id)
        if not detail:
            continue
        location = detail["location"]
        payload.append({
            "location": {
                "id": location.id,
                "name": location.name,
                "state": getattr(location, "state", None),
                "city": location.city,
            },
            "score": valuation_service.get_or_compute_score(session, location_id),
            "valuation_inputs": valuation_service.build_valuation_inputs(session, location_id),
            "favorability_profile": valuation_service.build_favorability_profile(session, location_id),
        })
    return _dump(payload)
