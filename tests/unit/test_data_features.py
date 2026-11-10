"""
Unit tests for feature builder, including strict time leakage test (Rule R4/R5).
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from backend.features.feature_builder import FeatureBuilder

def test_no_future_leakage():
    """
    Leakage test: verifies that a feature computed for observation at time t
    does NOT depend on or incorporate values from time > t.
    """
    builder = FeatureBuilder()

    records = []
    base_time = datetime(2026, 9, 1, 8, 0, 0)
    for i in range(5):
        records.append({
            "obs_id": f"O_{i}",
            "observed_at_utc": (base_time + timedelta(minutes=i * 10)).isoformat(),
            "trip_id": "TRIP_1",
            "stop_sequence": i + 1,
            "delay_minutes": float(i * 3), # 0, 3, 6, 9, 12
            "route_id": "17D",
            "stop_id": f"STP_{i}",
            "vehicle_no": "BUS_1",
            "y_crowd_class_idx": 1
        })
    df = pd.DataFrame(records)

    features = builder.build_features(df)
    
    # Check that previous_delay at step 0 is 0 (or NaN), not future delays
    assert features.iloc[0]["previous_delay"] == 0.0
    # Check that previous_delay at step 1 equals delay from step 0 (which was 0.0)
    assert features.iloc[1]["previous_delay"] == 0.0
    # Check that previous_delay at step 2 equals delay from step 1 (which was 3.0)
    assert features.iloc[2]["previous_delay"] == 3.0
    # Check that previous_delay at step 3 equals delay from step 2 (which was 6.0)
    assert features.iloc[3]["previous_delay"] == 6.0

def test_feature_columns_complete():
    builder = FeatureBuilder()
    df = pd.DataFrame([{
        "obs_id": "O_1",
        "observed_at_utc": "2026-09-01T08:30:00",
        "trip_id": "TRIP_1",
        "stop_sequence": 1,
        "delay_minutes": 5.0,
        "route_id": "17D",
        "stop_id": "STP_1",
        "vehicle_no": "BUS_1",
        "is_rain": 1,
        "y_crowd_class_idx": 2
    }])
    features = builder.build_features(df)
    for col in builder.feature_columns:
        assert col in features.columns, f"Missing feature column: {col}"

