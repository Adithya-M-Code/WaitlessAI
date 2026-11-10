"""
GTFS static data loader and generator for MTC Chennai.
Provides GTFS feeds for stops, routes, trips, and scheduled stop times.
"""

import os
from pathlib import Path
from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

# Coordinates boundary for Chennai Metropolitan Area
CHENNAI_BBOX = {
    "min_lat": 12.80,
    "max_lat": 13.25,
    "min_lon": 80.05,
    "max_lon": 80.32
}

PILOT_ROUTES = ["17D", "21G", "27B", "29C", "45B"]
OTHER_ROUTES = [
    "570", "A1", "19B", "23C", "5C", "M70", "102", "54", "88K", "25G",
    "11H", "47D", "12B", "154", "B29N", "114", "59", "28", "21", "18A"
]
ALL_ROUTES = PILOT_ROUTES + OTHER_ROUTES

KEY_CHENNAI_LANDMARKS = [
    ("Broadway Terminus", 13.0878, 80.2871),
    ("Chennai Central", 13.0827, 80.2755),
    ("Egmore Station", 13.0782, 80.2606),
    ("LIC Mount Road", 13.0645, 80.2650),
    ("DMS Teynampet", 13.0450, 80.2480),
    ("Saidapet", 13.0210, 80.2230),
    ("Guindy Asiad", 13.0067, 80.2025),
    ("Tambaram Sanatorium", 12.9350, 80.1280),
    ("Tambaram West", 12.9249, 80.1170),
    ("Marina Beach", 13.0500, 80.2824),
    ("Mylapore Luz", 13.0334, 80.2675),
    ("Adyar Depot", 13.0060, 80.2550),
    ("Thiruvanmiyur", 12.9830, 80.2590),
    ("Besant Nagar", 13.0001, 80.2700),
    ("Sholinganallur", 12.9010, 80.2279),
    ("Siruseri IT Park", 12.8280, 80.2180),
    ("Anna Square", 13.0650, 80.2840),
    ("Loyola College", 13.0640, 80.2330),
    ("Aminjikarai", 13.0740, 80.2190),
    ("CMBT Koyambedu", 13.0680, 80.1980),
    ("Maduravoyal", 13.0610, 80.1600),
    ("Poonamallee", 13.0480, 80.1100),
    ("Perambur", 13.1110, 80.2430),
    ("Kellys", 13.0890, 80.2440),
    ("Gemini Flyover", 13.0510, 80.2500),
    ("T. Nagar Bus Terminus", 13.0400, 80.2340),
    ("K.K. Nagar Depot", 13.0380, 80.1950),
    ("Vadapalani", 13.0500, 80.2120),
    ("Ashok Nagar", 13.0360, 80.2120),
    ("Porur Junction", 13.0350, 80.1580),
    ("Kundrathur", 12.9980, 80.0980),
    ("Pallavaram", 12.9675, 80.1491),
    ("Chromepet", 12.9516, 80.1410),
    ("Velachery Vijayanagar", 12.9750, 80.2200),
    ("Medavakkam", 12.9180, 80.1920),
    ("Kallikuppam", 13.1250, 80.1750),
    ("Ambattur OT", 13.1140, 80.1540),
    ("Avadi", 13.1190, 80.1000),
    ("Villivakkam", 13.1070, 80.2070),
    ("Kolathur", 13.1240, 80.2160),
    ("Madhavaram Milk Colony", 13.1480, 80.2350),
    ("Red Hills", 13.1950, 80.1970),
    ("Tollgate", 13.1360, 80.2940),
    ("Thiruvottiyur", 13.1600, 80.3010),
    ("Ennore", 13.2030, 80.3240)
]

class GTFSLoader:
    def __init__(self, gtfs_dir: str = "data/raw/gtfs"):
        self.gtfs_dir = Path(gtfs_dir)
        self.routes_df: pd.DataFrame = None
        self.stops_df: pd.DataFrame = None
        self.trips_df: pd.DataFrame = None
        self.stop_times_df: pd.DataFrame = None

    def load_or_generate(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Loads static GTFS tables if available, otherwise generates realistic Chennai network."""
        stops_file = self.gtfs_dir / "stops.txt"
        if stops_file.exists():
            self.routes_df = pd.read_csv(self.gtfs_dir / "routes.txt")
            self.stops_df = pd.read_csv(self.gtfs_dir / "stops.txt")
            self.trips_df = pd.read_csv(self.gtfs_dir / "trips.txt")
            self.stop_times_df = pd.read_csv(self.gtfs_dir / "stop_times.txt")
            return self.routes_df, self.stops_df, self.trips_df, self.stop_times_df
        
        return self.generate_synthetic_gtfs()

    def generate_synthetic_gtfs(self) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        self.gtfs_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Stops (Generate >= 320 stops spanning Chennai network)
        stops = []
        stop_id_counter = 1
        for landmark, lat, lon in KEY_CHENNAI_LANDMARKS:
            stops.append({
                "stop_id": f"STP_{stop_id_counter:04d}",
                "stop_name": landmark,
                "stop_lat": lat,
                "stop_lon": lon
            })
            stop_id_counter += 1
            # Add 6-8 intermediate radial stops around each major landmark
            for i in range(1, 8):
                delta_lat = np.random.uniform(-0.015, 0.015)
                delta_lon = np.random.uniform(-0.015, 0.015)
                stops.append({
                    "stop_id": f"STP_{stop_id_counter:04d}",
                    "stop_name": f"{landmark} Sub-Stop {i}",
                    "stop_lat": round(lat + delta_lat, 5),
                    "stop_lon": round(lon + delta_lon, 5)
                })
                stop_id_counter += 1
        
        self.stops_df = pd.DataFrame(stops)
        self.stops_df.to_csv(self.gtfs_dir / "stops.txt", index=False)

        # 2. Routes (25 routes)
        routes = []
        for r_id in ALL_ROUTES:
            routes.append({
                "route_id": r_id,
                "route_short_name": r_id,
                "route_long_name": f"MTC Route {r_id}",
                "route_type": 3  # Bus
            })
        self.routes_df = pd.DataFrame(routes)
        self.routes_df.to_csv(self.gtfs_dir / "routes.txt", index=False)

        # 3. Trips and Stop Times
        trips = []
        stop_times = []
        trip_counter = 1
        
        for r_id in ALL_ROUTES:
            # Pick 12-18 ordered stops for this route
            num_stops = np.random.randint(14, 20)
            route_stops = self.stops_df.sample(num_stops, random_state=hash(r_id) % 10000).copy()
            # Sort approximately geographically (e.g. by latitude)
            route_stops = route_stops.sort_values(by="stop_lat").reset_index(drop=True)
            
            # Generate 15 scheduled trips throughout the day for each route
            for departure_hour in range(6, 22):
                trip_id = f"TRIP_{r_id}_{departure_hour:02d}_{trip_counter:04d}"
                trips.append({
                    "route_id": r_id,
                    "service_id": "DAILY",
                    "trip_id": trip_id,
                    "trip_headsign": route_stops.iloc[-1]["stop_name"],
                    "direction_id": 0
                })
                
                accumulated_minutes = departure_hour * 60 + np.random.randint(0, 15)
                for seq, (_, stop_row) in enumerate(route_stops.iterrows(), start=1):
                    arr_hour = (accumulated_minutes // 60) % 24
                    arr_min = accumulated_minutes % 60
                    time_str = f"{arr_hour:02d}:{arr_min:02d}:00"
                    
                    stop_times.append({
                        "trip_id": trip_id,
                        "stop_id": stop_row["stop_id"],
                        "stop_sequence": seq,
                        "arrival_time": time_str,
                        "departure_time": time_str
                    })
                    accumulated_minutes += np.random.randint(3, 7)  # 3-7 mins between stops
                trip_counter += 1

        self.trips_df = pd.DataFrame(trips)
        self.trips_df.to_csv(self.gtfs_dir / "trips.txt", index=False)
        self.stop_times_df = pd.DataFrame(stop_times)
        self.stop_times_df.to_csv(self.gtfs_dir / "stop_times.txt", index=False)

        return self.routes_df, self.stops_df, self.trips_df, self.stop_times_df

