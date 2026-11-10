"""
Prediction endpoints (Delay, Crowding, Joint).
"""

from fastapi import APIRouter
from backend.api.schemas.prediction import PredictionRequest, JointPredictionResponse
from backend.services.prediction_service import PredictionService

router = APIRouter(prefix="/predict", tags=["Predictions"])
service = PredictionService()

@router.post("/joint", response_model=JointPredictionResponse)
def predict_joint(req: PredictionRequest):
    return service.predict_joint(req)

@router.post("/delay")
def predict_delay(req: PredictionRequest):
    joint = service.predict_joint(req)
    return {"delay": joint.delay, "model": joint.model, "timestamp": joint.timestamp}

@router.post("/crowding")
def predict_crowding(req: PredictionRequest):
    joint = service.predict_joint(req)
    return {"crowding": joint.crowding, "model": joint.model, "timestamp": joint.timestamp}

