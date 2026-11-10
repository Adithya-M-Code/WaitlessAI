"""
Live vehicles endpoint.
"""

from typing import List
from fastapi import APIRouter
from backend.services.vehicle_service import VehicleService

router = APIRouter(tags=["Vehicles"])
service = VehicleService()

@router.get("/vehicles")
def get_vehicles(route_id: str = "17D"):
    return service.get_route_vehicles(route_id)

