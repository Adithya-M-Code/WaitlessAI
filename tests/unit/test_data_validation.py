"""
Unit tests for data validation module.
"""

import pytest
import pandas as pd
import numpy as np
from backend.preprocessing.validator import DataValidator, CHENNAI_BBOX

def test_gps_bbox_validation():
    validator = DataValidator()
    df = pd.DataFrame([
        {"obs_id": "1", "route_id": "17D", "stop_id": "S1", "trip_id": "T1", "lat": 13.08, "lon": 80.27}, # Valid
        {"obs_id": "2", "route_id": "17D", "stop_id": "S1", "trip_id": "T1", "lat": 19.07, "lon": 72.87}, # Mumbai (Out of bbox)
        {"obs_id": "3", "route_id": "17D", "stop_id": "S1", "trip_id": "T1", "lat": 13.00, "lon": 80.20}, # Valid
    ])
    validated, rejections = validator.validate(df)
    assert len(validated) == 2
    assert rejections["out_of_bbox"] == 1

def test_missing_critical_ids():
    validator = DataValidator()
    df = pd.DataFrame([
        {"obs_id": "1", "route_id": "17D", "stop_id": "S1", "trip_id": "T1", "lat": 13.08, "lon": 80.27},
        {"obs_id": "2", "route_id": None, "stop_id": "S1", "trip_id": "T1", "lat": 13.08, "lon": 80.27},
    ])
    validated, rejections = validator.validate(df)
    assert len(validated) == 1
    assert rejections["invalid_id"] == 1

