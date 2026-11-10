"""
Data cleaner and label generator for Waitless AI.
Assigns delay targets, crowding classification, and downstream horizon targets (h1, h3, h5).
"""

from typing import Optional
import pandas as pd
import numpy as np

def assign_crowding_class(passenger_count: Optional[float]) -> Optional[str]:
    """
    Ordinal mapping: Low (0-20), Medium (21-40), High (41+).
    Missing values stay None (Rule R6: missing value is never zero).
    """
    if passenger_count is None or pd.isna(passenger_count):
        return None
    val = float(passenger_count)
    if val <= 20:
        return "Low"
    elif val <= 40:
        return "Medium"
    else:
        return "High"

def clean_and_label(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw data and computes official target labels:
    - y_delay: delay_minutes clipped to [-5, 60]
    - y_crowd_count: passenger_count
    - y_crowd_class: Low, Medium, High or None
    - y_delay_h1, y_delay_h3, y_delay_h5: downstream targets within the same trip
    """
    cleaned = df.copy()

    # 1. Delay target (clipped [-5, 60])
    cleaned["y_delay"] = cleaned["delay_minutes"].clip(lower=-5.0, upper=60.0)

    # 2. Crowding target
    cleaned["y_crowd_count"] = cleaned["passenger_count"]
    cleaned["y_crowd_class"] = cleaned["passenger_count"].apply(assign_crowding_class)
    
    class_to_idx = {"Low": 0, "Medium": 1, "High": 2}
    cleaned["y_crowd_class_idx"] = cleaned["y_crowd_class"].map(class_to_idx)

    # 3. Downstream targets (h1, h3, h5)
    # Sort strictly by trip_id and stop_sequence
    cleaned = cleaned.sort_values(by=["trip_id", "stop_sequence"]).reset_index(drop=True)
    
    # Calculate downstream delay observed at +1, +3, +5 stops along the same trip
    grouped = cleaned.groupby("trip_id")
    cleaned["y_delay_h1"] = grouped["y_delay"].shift(-1)
    cleaned["y_delay_h3"] = grouped["y_delay"].shift(-3)
    cleaned["y_delay_h5"] = grouped["y_delay"].shift(-5)

    return cleaned

