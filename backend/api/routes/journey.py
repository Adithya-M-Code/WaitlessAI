"""
Journey Ribbon endpoint.
"""

from fastapi import APIRouter
from backend.analytics.cascade import compute_journey_ribbon

router = APIRouter(tags=["Journey Ribbon"])

@router.get("/journey/{route_id}")
def get_journey_ribbon(route_id: str, stop_id: str = "Central", vehicle_no: str = "TN-01-N-1288"):
    ribbon = compute_journey_ribbon(route_id, stop_id)
    return {
        "route_id": route_id,
        "origin_stop_id": stop_id,
        "vehicle_no": vehicle_no,
        "stops_forecast": ribbon
    }

