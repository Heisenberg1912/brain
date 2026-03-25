import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.deps import get_db
from api.schemas import (
    AIBrainApproachOut,
    AIBrainModuleProfileOut,
    AIBrainResponse,
    AILLMProfileOut,
    AICompareRequest,
    AICompareResponse,
    AnalysisResponse,
    ErrorResponse,
    MarketBriefResponse,
    QueryRequest,
    QueryResponse,
)
from brain.ai import service as ai_svc
from brain.data_bank import service as data_svc

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/llm/profile", response_model=AILLMProfileOut)
def llm_profile():
    return ai_svc.get_llm_profile()


@router.get("/brain/modules", response_model=list[AIBrainModuleProfileOut])
def brain_modules():
    return ai_svc.list_brain_modules()


@router.get("/brain/approach", response_model=AIBrainApproachOut)
def brain_approach():
    return ai_svc.get_brain_approach()


@router.get(
    "/brain/{location_id}",
    response_model=AIBrainResponse,
    responses={404: {"model": ErrorResponse}},
)
def brain_profile(location_id: int, db: Session = Depends(get_db)):
    loc = data_svc.get_location(db, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    try:
        result = ai_svc.build_brain_profile(db, location_id)
    except Exception as e:
        logger.exception("AI brain profile failed for location %s", location_id)
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    if not result:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    return result


@router.post("/query", response_model=QueryResponse)
def ai_query(req: QueryRequest, db: Session = Depends(get_db)):
    try:
        result = ai_svc.query(
            db,
            req.question,
            location_id=req.location_id,
            compare_ids=req.compare_ids,
        )
    except Exception as e:
        logger.exception("AI query failed")
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    return {
        "question": req.question,
        "answer": result["answer"],
        "context_label": result.get("context_label"),
    }


@router.get("/market-brief", response_model=MarketBriefResponse)
def market_brief(db: Session = Depends(get_db)):
    try:
        return ai_svc.market_brief(db)
    except Exception as e:
        logger.exception("AI market brief failed")
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")


@router.get(
    "/analyze/{location_id}",
    response_model=AnalysisResponse,
    responses={404: {"model": ErrorResponse}},
)
def analyze_location(location_id: int, db: Session = Depends(get_db)):
    # Verify location exists before calling LLM
    loc = data_svc.get_location(db, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    try:
        result = ai_svc.analyze_location(db, location_id)
    except Exception as e:
        logger.exception("AI analysis failed for location %s", location_id)
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
    return {"location_id": location_id, **result}


@router.post("/compare", response_model=AICompareResponse)
def compare_locations(body: AICompareRequest, db: Session = Depends(get_db)):
    try:
        return ai_svc.compare_locations(db, body.location_ids)
    except Exception as e:
        logger.exception("AI compare failed for %s", body.location_ids)
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
