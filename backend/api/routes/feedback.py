"""
Rider Feedback loop and Push Notification subscription.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Rider Feedback"])

class FeedbackSubmission(BaseModel):
    route_id: str
    stop_id: str
    observed_crowding: str # Low, Medium, High
    actual_delay_minutes: float

class AlertSubscription(BaseModel):
    route_id: str
    stop_id: str
    target_arrival_time: str
    delay_threshold_minutes: float = 10.0

@router.post("/feedback/crowding")
def submit_feedback(fb: FeedbackSubmission):
    return {"status": "received", "message": "Thank you for helping improve Chennai transit reliability!"}

@router.post("/alerts/subscribe")
def subscribe_alert(sub: AlertSubscription):
    return {"status": "subscribed", "route_id": sub.route_id, "threshold": sub.delay_threshold_minutes}

