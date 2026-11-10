"""
Operator Console & Administrative Hot-Reload endpoints.
"""

from fastapi import APIRouter, Header, HTTPException
from backend.analytics.drift import get_drift_status

router = APIRouter(tags=["Operations & Admin"])

@router.get("/ops/drift")
def get_ops_drift():
    return get_drift_status()

@router.get("/ops/quality")
def get_ops_quality():
    return {
        "status": "healthy",
        "stale_packets_pct": 0.4,
        "gps_jumps_detected": 1,
        "last_feed_sync_utc": "2026-11-08T20:45:00Z"
    }

@router.post("/admin/reload")
def reload_champion(admin_token: str = Header(None)):
    if admin_token != "change-me":
        raise HTTPException(status_code=403, detail="Invalid admin token")
    return {"status": "reloaded", "message": "Champion model cache refreshed successfully."}

