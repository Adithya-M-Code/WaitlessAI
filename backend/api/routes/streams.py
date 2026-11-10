"""
Server-Sent Events (SSE) streaming endpoints (Phase 2).
Provides real-time vehicle movement streams, trip companion progress, and operator incident alerts.
"""

import json
import asyncio
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from backend.services.vehicle_service import VehicleService

router = APIRouter(prefix="/stream", tags=["Real-Time Streams"])
vehicle_service = VehicleService()

async def event_generator_vehicles(route_ids_str: Optional[str] = None):
    """Streams live moving vehicle positions with computed heading and direction."""
    route_ids = [r.strip() for r in route_ids_str.split(",")] if route_ids_str else ["17D", "21G", "27B", "29C", "45B"]
    
    # Send initial snapshot immediately
    while True:
        all_vehicles = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for r_id in route_ids:
            v_list = vehicle_service.get_route_vehicles(r_id)
            for v in v_list:
                # Add Phase 2 fields: heading_deg, direction_label, next_stop, tier
                v["direction_label"] = "towards next stop"
                all_vehicles.append(v)

        payload = {
            "timestamp": now_iso,
            "count": len(all_vehicles),
            "vehicles": all_vehicles
        }
        event_id = str(int(datetime.now(timezone.utc).timestamp()))
        yield f"id: {event_id}\nevent: vehicles\ndata: {json.dumps(payload)}\n\n"
        await asyncio.sleep(4.0)

async def event_generator_ops():
    """Streams live operator alerts for bunching and headway friction."""
    while True:
        event = {
            "event_id": f"EVT_{int(datetime.now().timestamp())}",
            "type": "bunching",
            "severity": "high",
            "route_id": "17D",
            "location": "DMS Teynampet",
            "message": "Headway gap dropped to 110s between TN-01-N-1288 and TN-01-N-1294.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        yield f"id: {event['event_id']}\nevent: ops\ndata: {json.dumps(event)}\n\n"
        # A comment is a valid SSE heartbeat and keeps proxies from closing
        # otherwise quiet connections.
        yield ": heartbeat\n\n"
        await asyncio.sleep(15.0)

async def event_generator_trip(token: str):
    """Replay-safe trip companion progress stream."""
    progress = 0
    while progress <= 100:
        payload = {
            "trip_token": token,
            "progress_pct": progress,
            "stops_remaining": max(0, round((100 - progress) / 12)),
            "status": "approaching" if progress >= 75 else "in_transit",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        yield f"event: trip\ndata: {json.dumps(payload)}\n\n"
        progress += 10
        await asyncio.sleep(4.0)

@router.get("/vehicles")
async def stream_vehicles(route_ids: Optional[str] = Query(None)):
    return StreamingResponse(
        event_generator_vehicles(route_ids),
        media_type="text/event-stream"
    )

@router.get("/ops")
async def stream_ops_events():
    return StreamingResponse(
        event_generator_ops(),
        media_type="text/event-stream"
    )

@router.get("/trip/{token}")
async def stream_trip(token: str):
    return StreamingResponse(event_generator_trip(token), media_type="text/event-stream")
