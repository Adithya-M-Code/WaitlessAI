"""
Interactive Labs Endpoints (Phase 2):
Best Bus v2, Best Time to Leave, What-If v2, Operator Console v2, City Replay, and Live Weather.
"""

from typing import Dict, Any, List, Optional
import os
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from backend.collectors.weather_collector import weather_collector

router = APIRouter(tags=["Interactive Labs"])

# 1. Best Bus v2 with Dynamic Preference Slider
class BestBusV2Request(BaseModel):
    route_id: str = "17D"
    stop_id: str = "Central"
    preference: float = Field(0.5, ge=0.0, le=1.0)  # 0.0 = fastest, 1.0 = most comfortable
    avoid_crowded: bool = False

@router.post("/recommend/v2")
def recommend_best_bus_v2(req: BestBusV2Request):
    buses = [
        {"bus_id": "TN-01-N-1288", "eta_min": 4.5, "delay_min": 2.1, "crowd_class": "High", "crowd_pct": 0.82, "reliability": 92},
        {"bus_id": "TN-01-N-1342", "eta_min": 11.0, "delay_min": 5.4, "crowd_class": "Low", "crowd_pct": 0.18, "reliability": 88},
        {"bus_id": "TN-01-N-1490", "eta_min": 18.5, "delay_min": 1.5, "crowd_class": "Medium", "crowd_pct": 0.45, "reliability": 95},
        {"bus_id": "TN-01-N-1555", "eta_min": 26.0, "delay_min": 3.0, "crowd_class": "Low", "crowd_pct": 0.12, "reliability": 90}
    ]

    ranked = []
    for b in buses:
        if req.avoid_crowded and b["crowd_class"] == "High":
            continue

        # Score formula blending speed (eta) and comfort (crowd) via preference slider
        speed_score = max(0.0, 100.0 - (b["eta_min"] * 3.5))
        comfort_score = max(0.0, 100.0 - (b["crowd_pct"] * 90.0))
        final_score = (1.0 - req.preference) * speed_score + req.preference * comfort_score

        if req.preference < 0.35:
            reason_en = f"Fastest arrival in {b['eta_min']} min"
            reason_ta = f"{b['eta_min']} நிமிடங்களில் விரைவான வருகை"
        elif req.preference > 0.65:
            reason_en = f"Maximum comfort ({b['crowd_class']} crowd), worth waiting"
            reason_ta = f"அதிக வசதி ({b['crowd_class']} கூட்டம்), காத்திருக்கலாம்"
        else:
            reason_en = f"Balanced trade-off: {b['eta_min']}m wait with {b['crowd_class']} crowd"
            reason_ta = f"சமநிலையான தேர்வு: {b['eta_min']} நிமி காத்திருப்பு"

        b_entry = dict(b)
        b_entry["score"] = round(final_score, 1)
        b_entry["reason_en"] = reason_en
        b_entry["reason_ta"] = reason_ta
        ranked.append(b_entry)

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return {
        "status": "ok",
        "route_id": req.route_id,
        "stop_id": req.stop_id,
        "preference": req.preference,
        "candidates": ranked
    }

# 2. Best Time to Leave (30 min window optimizer)
class LeaveTimeRequest(BaseModel):
    route_id: str = "17D"
    stop_id: str = "Central"

@router.post("/leave-time")
def find_best_departure_window(req: LeaveTimeRequest):
    now = datetime.now()
    windows = []
    
    # Evaluate 6 departure windows in 5-min intervals
    for step in range(0, 31, 5):
        dep_time = now + timedelta(minutes=step)
        wait_min = round(float(2.0 + (step * 0.7) % 8.0), 1)
        crowd_level = "High" if (step in [0, 5, 10]) else ("Medium" if step in [15, 20] else "Low")
        score = 100.0 - (wait_min * 5.0) - (35.0 if crowd_level == "High" else (15.0 if crowd_level == "Medium" else 0.0))

        windows.append({
            "departure_in_min": step,
            "clock_time": dep_time.strftime("%I:%M %p"),
            "expected_wait_min": wait_min,
            "crowd_level": crowd_level,
            "score": round(score, 1)
        })

    windows.sort(key=lambda x: x["score"], reverse=True)
    best = windows[0]

    return {
        "status": "ok",
        "recommended_window": best,
        "advice_en": f"Best time to leave is in {best['departure_in_min']} min ({best['clock_time']}) to enjoy shorter wait ({best['expected_wait_min']}m) and {best['crowd_level']} crowd.",
        "advice_ta": f"குறைந்த காத்திருப்பு ({best['expected_wait_min']} நிமி) மற்றும் {best['crowd_level']} கூட்டத்திற்கு {best['departure_in_min']} நிமிடத்தில் புறப்படவும்.",
        "all_windows": sorted(windows, key=lambda x: x["departure_in_min"])
    }

# 3. What-If v2 Scenario Simulator
class WhatIfV2Request(BaseModel):
    hour: int = 8
    day_type: str = "weekday"  # weekday, weekend, holiday
    rain_intensity_mm: float = 0.0
    upstream_delay_min: float = 0.0

@router.post("/whatif/v2")
def run_scenario_v2(req: WhatIfV2Request):
    # Baseline normal values
    base_delay = 3.2
    base_crowd = "Medium"

    # Scenario computation
    scenario_delay = base_delay + (req.upstream_delay_min * 0.75)
    if req.hour in [8, 9, 10, 17, 18, 19]:
        scenario_delay += 3.4
    if req.rain_intensity_mm > 0:
        scenario_delay += min(12.0, req.rain_intensity_mm * 1.8)
    if req.day_type == "holiday":
        scenario_delay = max(1.0, scenario_delay - 2.5)

    scenario_crowd = "High" if scenario_delay > 8.0 else ("Medium" if scenario_delay > 4.0 else "Low")

    # 24-hour progressive curve
    hourly_curve = []
    for h in range(6, 23):
        h_delay = base_delay + (3.0 if h in [8, 9, 18, 19] else 0.5) + (req.rain_intensity_mm * 1.2)
        hourly_curve.append({"hour": f"{h:02d}:00", "delay_min": round(h_delay, 1)})

    return {
        "status": "ok",
        "baseline": {"delay_min": base_delay, "crowd": base_crowd},
        "scenario": {"delay_min": round(scenario_delay, 1), "crowd": scenario_crowd},
        "delta_min": round(scenario_delay - base_delay, 1),
        "hourly_curve": hourly_curve
    }

# 4. Operator Console v2 Endpoints
@router.get("/ops/events")
def get_operator_events():
    return [
        {
            "id": "EVT_101",
            "type": "bunching",
            "severity": "high",
            "route_id": "17D",
            "leading_bus": "TN-01-N-1288",
            "trailing_bus": "TN-01-N-1294",
            "gap_seconds": 110,
            "location": "DMS Teynampet",
            "status": "active"
        },
        {
            "id": "EVT_102",
            "type": "service_gap",
            "severity": "medium",
            "route_id": "21G",
            "gap_minutes": 28,
            "location": "Marina Beach",
            "status": "active"
        }
    ]

@router.post("/ops/events/{event_id}/ack")
def acknowledge_event(event_id: str):
    return {"status": "acknowledged", "event_id": event_id, "message": "Dispatcher alerted."}

@router.post("/ops/events/{event_id}/snooze")
def snooze_event(event_id: str):
    return {"status": "snoozed", "event_id": event_id, "duration_minutes": 15}

@router.get("/ops/heatmap")
def get_ops_heatmap():
    # Route x Hour matrix
    routes = ["17D", "21G", "27B", "29C", "45B", "570", "A1"]
    hours = ["07:00", "08:00", "09:00", "12:00", "17:00", "18:00", "19:00", "21:00"]
    cells = []
    for r in routes:
        for h in hours:
            h_int = int(h.split(":")[0])
            is_peak = h_int in [8, 9, 18, 19]
            val = round(float(4.5 if is_peak else 1.8) + (hash(r + h) % 3), 1)
            cells.append({"route_id": r, "hour": h, "delay_min": val, "severity": "red" if val > 5 else ("amber" if val > 3 else "green")})
    return {"routes": routes, "hours": hours, "cells": cells}

@router.get("/ops/route/{route_id}")
def get_operator_route(route_id: str):
    """Return a plainly labelled route-health snapshot for the operator view."""
    return {
        "route_id": route_id,
        "tier": "demo" if os.getenv("DATA_MODE", "synthetic").lower() != "live" else "live",
        "status": "monitoring",
        "freshness": "schedule-based" if os.getenv("DATA_MODE", "synthetic").lower() != "live" else "live tracking",
        "active_alerts": [event for event in get_operator_events() if event["route_id"] == route_id],
        "message": "Operational decision support; not dispatch control.",
    }

@router.post("/ops/simulate-incident")
def simulate_incident():
    if os.getenv("DATA_MODE", "synthetic").lower() == "live":
        raise HTTPException(status_code=409, detail="Incident simulation is disabled in live mode")
    return {
        "status": "injected",
        "incident_type": "bunching",
        "route_id": "17D",
        "message": "Demo bunching incident injected successfully into live monitoring stream."
    }

# 5. Live Weather Endpoint
@router.get("/weather/live")
async def get_live_weather():
    return await weather_collector.get_live_weather()
