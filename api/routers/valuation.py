from dataclasses import asdict, is_dataclass
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import (
    CompareRequest,
    ValuationCoreOut,
    ValuationLogicResponseOut,
    ErrorResponse,
    FavorabilityOut,
    FavorabilityRankingItem,
    HotspotOut,
    PricePredictionOut,
    RankingItem,
    ScoreOut,
    ValuationInputsOut,
)
from brain.valuation import service as val_svc

router = APIRouter()

VALID_SORT_FIELDS = {
    "land_value_score",
    "development_potential_score",
    "future_appreciation_index",
}
VALID_FAVORABILITY_SORTS = {"overall", "residential", "commercial", "mixed_use", "industrial"}


@router.get(
    "/core/{location_id}",
    response_model=ValuationCoreOut,
    responses={404: {"model": ErrorResponse}},
)
def valuation_core(location_id: int, db: Session = Depends(get_db)):
    result = val_svc.build_core_outputs(db, location_id)
    db.commit()
    if not result:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    return result


@router.get(
    "/logic/{location_id}",
    response_model=ValuationLogicResponseOut,
    responses={404: {"model": ErrorResponse}},
)
def valuation_logic(location_id: int, db: Session = Depends(get_db)):
    result = val_svc.build_logic_layer(db, location_id)
    db.commit()
    if not result:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    return result


@router.get(
    "/inputs/{location_id}",
    response_model=ValuationInputsOut,
    responses={404: {"model": ErrorResponse}},
)
def valuation_inputs(location_id: int, db: Session = Depends(get_db)):
    result = val_svc.build_valuation_inputs(db, location_id)
    db.commit()
    if not result:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    return result


@router.get(
    "/favorability/rankings",
    response_model=list[FavorabilityRankingItem],
)
def favorability_rankings(
    top: int = Query(default=20, ge=1, le=100),
    use_case: Literal["overall", "residential", "commercial", "mixed_use", "industrial"] = Query(default="overall"),
    db: Session = Depends(get_db),
):
    if use_case not in VALID_FAVORABILITY_SORTS:
        raise HTTPException(
            status_code=422,
            detail=f"use_case must be one of: {', '.join(sorted(VALID_FAVORABILITY_SORTS))}",
        )
    results = val_svc.get_favorability_rankings(db, top_n=top, use_case=use_case)
    db.commit()
    return results


@router.get(
    "/favorability/{location_id}",
    response_model=FavorabilityOut,
    responses={404: {"model": ErrorResponse}},
)
def favorability_profile(location_id: int, db: Session = Depends(get_db)):
    result = val_svc.build_favorability_profile(db, location_id)
    db.commit()
    if not result:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    return result


@router.get(
    "/score/{location_id}",
    response_model=ScoreOut,
    responses={404: {"model": ErrorResponse}},
)
def score_location(location_id: int, db: Session = Depends(get_db)):
    result = val_svc.score_location(db, location_id, persist=True)
    db.commit()
    if not result:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    return result


@router.get("/rankings", response_model=list[RankingItem])
def rankings(
    top: int = Query(default=20, ge=1, le=100),
    sort_by: str = Query(default="land_value_score"),
    db: Session = Depends(get_db),
):
    if sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(
            status_code=422,
            detail=f"sort_by must be one of: {', '.join(sorted(VALID_SORT_FIELDS))}",
        )
    val_svc.score_all_locations(db)
    return val_svc.get_rankings(db, top_n=top, sort_by=sort_by)


@router.post("/compare", response_model=list[ScoreOut])
def compare(body: CompareRequest, db: Session = Depends(get_db)):
    results = val_svc.compare_locations(db, body.location_ids)
    if not results:
        raise HTTPException(status_code=404, detail="No valid locations found for comparison")
    return results


@router.get(
    "/predict/{location_id}",
    response_model=PricePredictionOut,
    responses={404: {"model": ErrorResponse}},
)
def predict_price(location_id: int, db: Session = Depends(get_db)):
    prediction = val_svc.predict_price_for_location(db, location_id)
    if not prediction:
        raise HTTPException(status_code=404, detail=f"Prediction unavailable for location {location_id}")
    return asdict(prediction) if is_dataclass(prediction) else prediction


@router.get("/hotspots", response_model=list[HotspotOut])
def list_hotspots(
    n_clusters: int = Query(default=4, ge=2, le=10),
    db: Session = Depends(get_db),
):
    hotspots = val_svc.detect_hotspots(db, n_clusters=n_clusters)
    return [
        {
            "cluster_id": hotspot.cluster_id,
            "label": hotspot.label,
            "summary": hotspot.summary,
            "cluster_size": hotspot.cluster_size,
            "hotspot_score": hotspot.hotspot_score,
            "dominant_signal": hotspot.dominant_signal,
            "locations": hotspot.locations,
            "avg_land_value": hotspot.avg_land_value,
            "avg_development_potential": hotspot.avg_development_potential,
            "avg_appreciation": hotspot.avg_appreciation,
            "avg_infra_score": hotspot.avg_infra_score,
            "avg_price_trend": hotspot.avg_price_trend,
            "avg_price": hotspot.avg_price,
            "feature_profile": [
                {
                    "key": feature.key,
                    "label": feature.label,
                    "average": feature.average,
                    "delta_from_baseline": feature.delta_from_baseline,
                    "relative_level": feature.relative_level,
                }
                for feature in hotspot.feature_profile
            ],
        }
        for hotspot in hotspots
    ]
