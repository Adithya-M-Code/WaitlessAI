"""
Synthetic Data Generator v2 for MTC Chennai bus network.
Generates realistic observations exhibiting peak-hour congestion, rain-induced delays,
downstream delay propagation, headway bunching, service gaps, and passenger crowding.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np
import pandas as pd
try:
    import holidays
    HAS_HOLIDAYS_LIB = True
except ImportError:
    HAS_HOLIDAYS_LIB = False

from backend.collectors.gtfs_loader import GTFSLoader, ALL_ROUTES, PILOT_ROUTES

def get_tamil_nadu_holidays(years: List[int]) -> set:
    if HAS_HOLIDAYS_LIB:
        try:
            tn_holidays = holidays.India(years=years, subdiv="TN")
            return set(tn_holidays.keys())
        except Exception:
            pass
    fallback = set()
    for y in years:
        fallback.update([
            datetime(y, 1, 14).date(),
            datetime(y, 1, 15).date(),
            datetime(y, 1, 26).date(),
            datetime(y, 4, 14).date(),
            datetime(y, 5, 1).date(),
            datetime(y, 8, 15).date(),
            datetime(y, 10, 2).date(),
            datetime(y, 11, 1).date(),
            datetime(y, 12, 25).date()
        ])
    return fallback

class SyntheticDataGenerator:
    def __init__(self, seed: int = 42):
        np.random.seed(seed)
        self.loader = GTFSLoader()
        self.routes_df, self.stops_df, self.trips_df, self.stop_times_df = self.loader.load_or_generate()
        self.stops_dict = self.stops_df.set_index("stop_id").to_dict(orient="index")

    def generate(
        self,
        days: int = 90,
        start_date: str = "2026-08-01",
        output_dir: str = "data/raw/synthetic"
    ) -> pd.DataFrame:
        """
        Generates synthetic bus trajectory events over the specified timeframe.
        """
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        years = list(range(start_dt.year, (start_dt + timedelta(days=days)).year + 1))
        tn_holidays = get_tamil_nadu_holidays(years)

        # Pre-generate weather conditions per day (monsoon season in Chennai: Oct-Dec)
        rainy_days = set()
        for d in range(days):
            curr_date = (start_dt + timedelta(days=d)).date()
            prob_rain = 0.40 if curr_date.month in [10, 11, 12] else 0.12
            if np.random.rand() < prob_rain:
                rainy_days.add(curr_date)

        records = []
        obs_counter = 1

        # Build map of trips per route
        trips_by_route = self.trips_df.groupby("route_id")["trip_id"].unique().to_dict()
        st_by_trip = self.stop_times_df.groupby("trip_id")

        print(f"Generating synthetic observations for {len(ALL_ROUTES)} routes over {days} days...")

        # To keep dataset manageable yet rich, we sample daily trips
        for day_idx in range(days):
            current_day = (start_dt + timedelta(days=day_idx)).date()
            is_weekend = current_day.weekday() >= 5
            is_holiday = current_day in tn_holidays
            is_rain = current_day in rainy_days

            # Iterate over active routes
            for route_id, route_trips in trips_by_route.items():
                # Simulate vehicles running trips on this route
                # 3-6 distinct buses serving the route per day
                bus_fleet = [f"TN-01-N-{np.random.randint(1000, 9999)}" for _ in range(4)]
                
                # Sort trips to model bunching between consecutive trips
                selected_trips = np.random.choice(route_trips, size=min(len(route_trips), 8), replace=False)

                prev_bus_arrival_at_stop: Dict[str, datetime] = {}

                for trip_idx, trip_id in enumerate(selected_trips):
                    vehicle_no = bus_fleet[trip_idx % len(bus_fleet)]
                    try:
                        trip_st = st_by_trip.get_group(trip_id).sort_values("stop_sequence")
                    except KeyError:
                        continue

                    accumulated_delay = np.random.normal(1.0, 2.0)  # Initial terminal delay
                    prev_stop_id = None
                    prev_observed_time = None

                    # Inject bunching event on 8% of trips
                    force_bunching = (np.random.rand() < 0.08) and (trip_idx > 0)
                    force_gap = (np.random.rand() < 0.05) and not force_bunching

                    for _, st_row in trip_st.iterrows():
                        stop_id = st_row["stop_id"]
                        stop_seq = int(st_row["stop_sequence"])
                        scheduled_time_str = st_row["arrival_time"]
                        sched_h, sched_m, sched_s = map(int, scheduled_time_str.split(":"))

                        sched_dt = datetime.combine(
                            current_day,
                            datetime.min.time()
                        ) + timedelta(hours=sched_h, minutes=sched_m, seconds=sched_s)

                        hour = sched_dt.hour
                        is_peak = (7 <= hour <= 10) or (17 <= hour <= 20)

                        # Delay dynamics & downstream propagation
                        # Additional delta added between stops
                        step_delta = np.random.normal(0.2, 0.8)
                        if is_peak:
                            step_delta += np.random.uniform(0.5, 2.0)
                        if is_rain:
                            step_delta += np.random.uniform(0.8, 2.5)
                        if is_holiday:
                            step_delta -= 0.5  # Lighter traffic on holidays

                        accumulated_delay = max(-5.0, min(60.0, accumulated_delay + step_delta))

                        # Bunching / Gap logic
                        is_bunching_flag = 0
                        is_gap_flag = 0

                        if force_bunching and stop_seq > 3:
                            accumulated_delay = max(-3.0, accumulated_delay - 3.0)  # Catching up to front bus
                            is_bunching_flag = 1
                        elif force_gap and stop_seq > 3:
                            accumulated_delay = min(50.0, accumulated_delay + 8.0)  # Stranded behind
                            is_gap_flag = 1

                        actual_arrival_dt = sched_dt + timedelta(minutes=accumulated_delay)

                        # Detect empirical bunching relative to previous bus
                        if stop_id in prev_bus_arrival_at_stop:
                            headway_gap_s = (actual_arrival_dt - prev_bus_arrival_at_stop[stop_id]).total_seconds()
                            if 0 < headway_gap_s < 180: # Less than 3 minutes headway
                                is_bunching_flag = 1
                            elif headway_gap_s > 1800: # Over 30 minutes headway
                                is_gap_flag = 1

                        prev_bus_arrival_at_stop[stop_id] = actual_arrival_dt

                        # Crowding generation (correlated with peak, delay, and stop popularity)
                        base_crowd = 15
                        if is_peak:
                            base_crowd += 25
                        if is_rain:
                            base_crowd += 10
                        if accumulated_delay > 10:
                            base_crowd += 15 # More people accumulated at stops
                        if is_bunching_flag:
                            base_crowd = max(5, base_crowd - 18) # Second bus in bunch carries fewer passengers

                        passenger_count = int(np.clip(np.random.normal(base_crowd, 8.0), 0, 85))

                        # Missing values simulation (~4% for passenger_count, ~1% GPS noise)
                        has_missing_crowd = (np.random.rand() < 0.04)
                        recorded_passengers = None if has_missing_crowd else passenger_count

                        stop_info = self.stops_dict.get(stop_id, {"stop_lat": 13.08, "stop_lon": 80.27})
                        lat = stop_info["stop_lat"] + np.random.normal(0, 0.0001)
                        lon = stop_info["stop_lon"] + np.random.normal(0, 0.0001)

                        # Downstream horizon labels (filled later in cleaner/dataset builder)
                        records.append({
                            "obs_id": f"OBS_{obs_counter:08d}",
                            "observed_at_utc": actual_arrival_dt.isoformat(),
                            "scheduled_at_utc": sched_dt.isoformat(),
                            "route_id": route_id,
                            "stop_id": stop_id,
                            "trip_id": trip_id,
                            "vehicle_no": vehicle_no,
                            "stop_sequence": stop_seq,
                            "lat": round(lat, 5),
                            "lon": round(lon, 5),
                            "delay_minutes": round(accumulated_delay, 2),
                            "passenger_count": recorded_passengers,
                            "is_rain": int(is_rain),
                            "is_holiday": int(is_holiday),
                            "is_bunching": is_bunching_flag,
                            "is_gap": is_gap_flag,
                            "source_flag": "synthetic"
                        })
                        obs_counter += 1

        df = pd.DataFrame(records)
        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        file_path = out_path / "synthetic_raw.parquet"
        df.to_parquet(file_path, index=False)
        print(f"Generated {len(df)} synthetic observations saved to {file_path}")
        return df
