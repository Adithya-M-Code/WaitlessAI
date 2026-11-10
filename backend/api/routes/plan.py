"""
RAPTOR-Lite Journey Planner endpoints (Phase 2).
POST /plan returns direct and 1-transfer options without predictions.
POST /plan/predict runs button-gated predictions for selected itinerary.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.analytics.planner import JourneyPlanner

router = APIRouter(prefix="/plan", tags=["Journey Planner"])
planner = JourneyPlanner()

class Location(BaseModel):
    name: Optional[str] = "Selected Place"
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)

class PlanRequest(BaseModel):
    from_loc: Location = Field(..., alias="from")
    to_loc: Location = Field(..., alias="to")
    depart_at: Optional[str] = None
    max_transfers: Optional[int] = 1
    max_walk_m: Optional[float] = 800.0

    class Config:
        populate_by_name = True

class PredictItineraryRequest(BaseModel):
    option: Dict[str, Any]

@router.post("")
def plan_journey(req: PlanRequest):
    if req.max_transfers is not None and not 0 <= req.max_transfers <= 1:
        raise HTTPException(status_code=422, detail="max_transfers must be 0 or 1")
    if req.max_walk_m is not None and not 50 <= req.max_walk_m <= 5000:
        raise HTTPException(status_code=422, detail="max_walk_m must be between 50 and 5000 metres")
    options = planner.plan(
        from_loc=req.from_loc.model_dump(),
        to_loc=req.to_loc.model_dump(),
        max_transfers=req.max_transfers or 1,
        max_walk_m=req.max_walk_m or 800.0
    )
    if not options:
        raise HTTPException(
            status_code=404,
            detail="No bus journey found within the walking and transfer limits"
        )
    return {
        "status": "ok",
        "from": req.from_loc.name,
        "to": req.to_loc.name,
        "options_count": len(options),
        "options": options
    }

@router.post("/predict")
def predict_itinerary(req: PredictItineraryRequest):
    if not req.option.get("legs"):
        raise HTTPException(status_code=422, detail="option must contain at least one journey leg")
    try:
        prediction = planner.predict_option(req.option)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        "status": "ok",
        "itinerary_prediction": prediction
    }
