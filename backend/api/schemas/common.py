"""
Common Pydantic v2 schemas across API endpoints.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class StopInfo(BaseModel):
    stop_id: str
    stop_name: str
    stop_lat: float
    stop_lon: float
    sequence: int

class RouteInfo(BaseModel):
    route_id: str
    route_name: str
    origin: str
    destination: str
    total_stops: int
    key_stops: List[str]

class VehiclePosition(BaseModel):
    vehicle_no: str
    route_id: str
    lat: float
    lon: float
    heading: float
    speed_kmh: float
    passenger_count: Optional[int]
    crowding_class: Optional[str]
    freshness_state: str
    last_updated_utc: str

