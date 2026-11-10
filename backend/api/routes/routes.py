"""
Routes and stops exploration endpoints.
"""

from typing import List
from fastapi import APIRouter, HTTPException
from backend.collectors.gtfs_loader import GTFSLoader
from backend.api.schemas.common import RouteInfo, StopInfo

router = APIRouter(tags=["Network"])
loader = GTFSLoader()

@router.get("/routes", response_model=List[RouteInfo])
def get_all_routes():
    routes_df, stops_df, trips_df, stop_times_df = loader.load_or_generate()
    results = []
    route_ids = routes_df["route_id"].astype(str).drop_duplicates().tolist()
    for r_id in route_ids:
        route_trips = trips_df[trips_df["route_id"].astype(str) == r_id]
        total_stops = 0
        if not route_trips.empty:
            trip_id = route_trips.iloc[0]["trip_id"]
            total_stops = int((stop_times_df["trip_id"] == trip_id).sum())
        results.append(RouteInfo(
            route_id=r_id,
            route_name=f"MTC Route {r_id}",
            origin="Broadway Terminus" if r_id.startswith("1") or r_id.startswith("2") else "Anna Square",
            destination="Tambaram" if "G" in r_id else "CMBT Koyambedu",
            total_stops=total_stops,
            key_stops=["Central", "Teynampet", "Guindy", "Destination"]
        ))
    return results

@router.get("/routes/{route_id}/stops", response_model=List[StopInfo])
def get_route_stops(route_id: str):
    routes_df, stops_df, trips_df, stop_times_df = loader.load_or_generate()
    # Find trips for route
    route_trips = trips_df[trips_df["route_id"] == route_id]
    if route_trips.empty:
        raise HTTPException(status_code=404, detail=f"Route {route_id} not found")

    sample_trip = route_trips.iloc[0]["trip_id"]
    st = stop_times_df[stop_times_df["trip_id"] == sample_trip].sort_values("stop_sequence")
    merged = st.merge(stops_df, on="stop_id")

    results = []
    for _, row in merged.iterrows():
        results.append(StopInfo(
            stop_id=row["stop_id"],
            stop_name=row["stop_name"],
            stop_lat=row["stop_lat"],
            stop_lon=row["stop_lon"],
            sequence=int(row["stop_sequence"])
        ))
    return results
