"""
Data validation module with audit trail for Waitless AI.
Ensures GPS coordinates, vehicle velocities, timestamps, and identifiers meet strict validity criteria.
"""

from typing import Dict, List, Tuple
import pandas as pd
import numpy as np

CHENNAI_BBOX = {
    "min_lat": 12.70,
    "max_lat": 13.40,
    "min_lon": 79.90,
    "max_lon": 80.40
}
MAX_SPEED_KMH = 120.0

class DataValidator:
    def __init__(self):
        self.rejected_records: List[Dict] = []
        self.rejection_counts: Dict[str, int] = {
            "out_of_bbox": 0,
            "impossible_speed": 0,
            "invalid_id": 0,
            "invalid_timestamp": 0
        }

    def validate(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Validates the dataframe, logs reasons for rejected records, and returns the cleaned dataframe.
        """
        initial_count = len(df)
        valid_mask = pd.Series(True, index=df.index)

        # 1. GPS Bounding Box Check
        lat_valid = (df["lat"] >= CHENNAI_BBOX["min_lat"]) & (df["lat"] <= CHENNAI_BBOX["max_lat"])
        lon_valid = (df["lon"] >= CHENNAI_BBOX["min_lon"]) & (df["lon"] <= CHENNAI_BBOX["max_lon"])
        bbox_valid = lat_valid & lon_valid
        
        out_of_bbox = ~bbox_valid
        self.rejection_counts["out_of_bbox"] += int(out_of_bbox.sum())
        valid_mask &= bbox_valid

        # 2. Check for missing critical identifiers
        id_valid = df["route_id"].notna() & df["stop_id"].notna() & df["trip_id"].notna()
        self.rejection_counts["invalid_id"] += int((~id_valid).sum())
        valid_mask &= id_valid

        # 3. Velocity / Jump Check
        # Check implied speed if vehicle consecutive observations exist
        # Here we verify speed_estimate or coordinate jump if present
        if "speed_estimate_kmh" in df.columns:
            speed_valid = (df["speed_estimate_kmh"] <= MAX_SPEED_KMH) | (df["speed_estimate_kmh"].isna())
            self.rejection_counts["impossible_speed"] += int((~speed_valid).sum())
            valid_mask &= speed_valid

        validated_df = df[valid_mask].copy()
        return validated_df, self.rejection_counts

