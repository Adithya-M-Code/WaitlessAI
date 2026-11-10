"""
What-If Simulator and Past Day Replay endpoints.
"""

from typing import Optional
from fastapi import APIRouter
from datetime import datetime, timezone
from pydantic import BaseModel
from backend.analytics.whatif import simulate_whatif

router = APIRouter(tags=["Simulation"])

class WhatIfRequest(BaseModel):
    base_delay: float = 3.5
    hour: int = 8
    is_rain: bool = True
    is_peak: bool = True
    upstream_delay: float = 4.0

@router.post("/whatif")
def post_whatif_simulation(req: WhatIfRequest):
    return simulate_whatif(
        base_delay=req.base_delay,
        hour=req.hour,
        is_rain=req.is_rain,
        is_peak=req.is_peak,
        upstream_delay=req.upstream_delay
    )

@router.get("/replay")
def get_replay_snapshot(date: str = "2026-09-15", t: str = "08:30"):
    return {
        "replay_timestamp": f"{date}T{t}:00",
        "active_buses_count": 42,
        "average_network_delay_min": 4.8,
        "bunching_events_detected": 2,
        "state": "replay_ready"
    }

@router.get("/replay/day")
def get_replay_day(date: str = "2026-09-15"):
    return {
        "date": date,
        "mode": "replay",
        "available": True,
        "duration_minutes": 1440,
        "speed_options": [1, 5, 15, 60],
        "message": "Recorded/demo replay; values are not live observations.",
    }

@router.post("/replay/control")
def control_replay(action: str = "pause", speed: int = 1):
    if action not in {"play", "pause", "reset"}:
        return {"status": "error", "detail": "action must be play, pause, or reset"}
    if speed not in {1, 5, 15, 60}:
        return {"status": "error", "detail": "speed must be 1, 5, 15, or 60"}
    return {
        "status": "ok",
        "action": action,
        "speed": speed,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
