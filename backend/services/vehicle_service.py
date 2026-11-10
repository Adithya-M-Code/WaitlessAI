"""
Vehicle tracking and live simulation service for Chennai routes.
"""

from datetime import datetime, timezone
import os
from typing import List, Dict, Any, Optional
import numpy as np
from backend.collectors.gtfs_loader import GTFSLoader
from backend.services.freshness_service import FreshnessService

class VehicleService:
    def __init__(self):
        self.loader = GTFSLoader()
        self.routes_df, self.stops_df, self.trips_df, self.stop_times_df = self.loader.load_or_generate()
        self.stops_dict = self.stops_df.set_index("stop_id").to_dict(orient="index")
        self.freshness = FreshnessService(int(os.getenv("LIVE_STALE_SECONDS", "180")))
        self.data_mode = os.getenv("DATA_MODE", "synthetic").lower()

    def get_route_vehicles(self, route_id: str) -> List[Dict[str, Any]]:
        """Returns live or realistic simulated active vehicles for a route."""
        # Find stops along this route
        route_trips = self.trips_df[self.trips_df["route_id"] == route_id]
        if route_trips.empty:
            return []

        sample_trip = route_trips.iloc[0]["trip_id"]
        st = self.stop_times_df[self.stop_times_df["trip_id"] == sample_trip].sort_values("stop_sequence")
        stop_ids = st["stop_id"].values

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        vehicles = []
        for i in range(1, 4):
            v_no = f"TN-01-N-{1200 + i * 15}"
            # Position along route
            # A deterministic phase makes replay/synthetic streams move between
            # requests without requiring a background process or random values.
            phase = int(now.timestamp() // 20 + i * 7) % max(1, len(stop_ids))
            pos_idx = int(np.clip(phase, 0, len(stop_ids) - 1))
            stop_id = str(stop_ids[pos_idx])
            s_info = self.stops_dict.get(stop_id, {"stop_lat": 13.08, "stop_lon": 80.27})
            next_idx = min(pos_idx + 1, len(stop_ids) - 1)
            next_info = self.stops_dict.get(str(stop_ids[next_idx]), s_info)
            heading = float(np.degrees(np.arctan2(
                next_info["stop_lon"] - s_info["stop_lon"],
                next_info["stop_lat"] - s_info["stop_lat"],
            )) % 360)
            p_count = int(15 + ((phase * 13 + i * 11) % 46))
            c_class = "Low" if p_count <= 20 else ("Medium" if p_count <= 40 else "High")
            age_s = 0
            tier = self.freshness.tier_for_age(age_s, self.freshness.stale_threshold_s)

            vehicles.append({
                "vehicle_no": v_no,
                "route_id": route_id,
                "current_stop_id": stop_id,
                "lat": s_info["stop_lat"],
                "lon": s_info["stop_lon"],
                "heading": round(heading, 1),
                "heading_deg": round(heading, 1),
                "speed_kmh": round(22.0 + ((phase + i) % 12), 1),
                "passenger_count": p_count,
                "crowding_class": c_class,
                "freshness_state": "fresh",
                "observed_at": now_iso,
                "age_s": age_s,
                "tier": tier,
                "next_stop": str(self.stops_dict.get(str(stop_ids[next_idx]), {}).get("stop_name", "")),
                "last_updated_utc": now_iso
            })
        return vehicles
