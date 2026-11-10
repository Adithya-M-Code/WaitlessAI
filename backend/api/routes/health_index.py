"""
Route Health Index & Bunching Alerts endpoints.
"""

from fastapi import APIRouter
from backend.analytics.health_index import calculate_route_health
from backend.analytics.bunching import detect_bunching_alerts

router = APIRouter(tags=["Disruptions & Health"])

@router.get("/health-index/{route_id}")
def get_health_index(route_id: str):
    return calculate_route_health(route_id)

@router.get("/alerts/bunching")
def get_bunching_alerts(route_id: str = "17D"):
    return detect_bunching_alerts(route_id)

