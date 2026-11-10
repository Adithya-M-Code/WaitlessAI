"""
Route Shapes and Geometry endpoints (Phase 2).
Provides polyline coordinates, stop points, and coverage tier for rendering map route layers.
"""

from typing import List, Dict, Any
import os
from fastapi import APIRouter, HTTPException
from backend.collectors.gtfs_loader import GTFSLoader

router = APIRouter(prefix="/routes", tags=["Route Shapes"])
loader = GTFSLoader()

LIVE_TIER_ROUTES = {"17D", "21G", "27B", "29C", "45B", "570", "A1"}
RECENT_TIER_ROUTES = {"19B", "23C"}

@router.get("/{route_id}/shape")
def get_route_shape(route_id: str):
    routes_df, stops_df, trips_df, stop_times_df = loader.load_or_generate()
    route_trips = trips_df[trips_df["route_id"] == route_id]
    if route_trips.empty:
        raise HTTPException(status_code=404, detail=f"Route {route_id} not found")

    sample_trip = route_trips.iloc[0]["trip_id"]
    st = stop_times_df[stop_times_df["trip_id"] == sample_trip].sort_values("stop_sequence")
    merged = st.merge(stops_df, on="stop_id")

    polyline: List[List[float]] = []
    stops: List[Dict[str, Any]] = []

    for _, row in merged.iterrows():
        lat = float(row["stop_lat"])
        lon = float(row["stop_lon"])
        polyline.append([lat, lon])
        stops.append({
            "stop_id": row["stop_id"],
            "stop_name": row["stop_name"],
            "sequence": int(row["stop_sequence"]),
            "lat": lat,
            "lon": lon
        })

    # Configured pilot routes are eligible for live collection, but a route is
    # never advertised as live solely because it is in that list.  In offline
    # modes it is an honest schedule/demo tier.
    data_mode = os.getenv("DATA_MODE", "synthetic").lower()
    configured_tier = "live" if route_id in LIVE_TIER_ROUTES else ("recent" if route_id in RECENT_TIER_ROUTES else "schedule")
    tier = configured_tier if data_mode in {"live", "synthetic"} else (
        "recent" if data_mode == "replay" and configured_tier != "schedule" else "schedule"
    )

    return {
        "route_id": route_id,
        "route_name": f"MTC Route {route_id}",
        "tier": tier,
        "color": "#2563EB" if tier == "live" else ("#F59E0B" if tier == "recent" else "#64748B"),
        "polyline": polyline,
        "stops": stops,
        "total_stops": len(stops)
    }
