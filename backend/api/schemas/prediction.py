"""
Prediction schemas adhering strictly to Section 13 contract.
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field

class PredictionRequest(BaseModel):
    route_id: str
    stop_id: str
    vehicle_no: Optional[str] = None
    hour: Optional[int] = None
    day_of_week: Optional[int] = None
    is_rain: Optional[bool] = False
    previous_delay: Optional[float] = None
    previous_crowding: Optional[str] = None
    model: Optional[str] = None
    horizons: Optional[List[int]] = [1, 3, 5]

class ModelMetadata(BaseModel):
    id: str
    family: str
    data_source: Literal["real", "synthetic", "mixed"]

class DelayPrediction(BaseModel):
    status: Literal["ok", "degraded", "unavailable"]
    minutes: Optional[float]
    interval80: Optional[List[float]]
    p_on_time: Optional[float]
    label: Optional[str]

class CrowdingPrediction(BaseModel):
    status: Literal["ok", "degraded", "unavailable"]
    class_: Optional[str] = Field(None, alias="class")
    probabilities: Optional[Dict[str, float]]

    class Config:
        populate_by_name = True

class FreshnessInfo(BaseModel):
    live_age_seconds: int
    state: Literal["fresh", "aging", "stale"]

class JointPredictionResponse(BaseModel):
    route_id: str
    stop_id: str
    model: ModelMetadata
    delay: DelayPrediction
    crowding: CrowdingPrediction
    freshness: FreshnessInfo
    inputs_derived: bool
    warnings: List[str]
    timestamp: str
    status: Literal["ok", "degraded", "unavailable"]

