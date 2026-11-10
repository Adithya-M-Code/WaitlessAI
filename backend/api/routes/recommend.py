"""
Best-Bus Recommender endpoint.
"""

from typing import Literal
from fastapi import APIRouter
from backend.analytics.recommender import recommend_best_bus

router = APIRouter(tags=["Recommender"])

@router.get("/recommend")
def get_bus_recommendations(
    route_id: str = "17D",
    stop_id: str = "Central",
    mode: Literal["speed", "comfort", "balanced"] = "balanced"
):
    recommendations = recommend_best_bus(route_id, stop_id, mode)
    return {
        "route_id": route_id,
        "stop_id": stop_id,
        "mode": mode,
        "recommendations": recommendations,
        "disclaimer": "Decision support estimate only, not a dispatch guarantee."
    }

