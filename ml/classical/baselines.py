"""
Reference Baselines (Section 11.1):
1. Persistence / Carry-Forward: delay = previous_delay; crowd = previous_crowding
2. Historical Mean/Mode: Route × Stop × Hour historical mean delay and mode crowding class
"""

import time
from pathlib import Path
from typing import Dict, Any, Literal
import pandas as pd
import numpy as np

class PersistenceBaseline:
    model_id = "persistence_baseline"
    family = "baseline"
    task: Literal["joint"] = "joint"

    def __init__(self):
        self.train_time_s = 0.0

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame, cfg: Dict[str, Any] = None):
        t0 = time.time()
        self.train_time_s = time.time() - t0

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        t0 = time.time()
        preds = pd.DataFrame()
        preds["obs_id"] = df["obs_id"]

        # Persistence prediction
        preds["y_pred_delay"] = df["previous_delay"].fillna(0.0)
        preds["q10"] = preds["y_pred_delay"] - 3.0
        preds["q50"] = preds["y_pred_delay"]
        preds["q90"] = preds["y_pred_delay"] + 5.0

        # Downstream naive carry-forward
        preds["y_pred_delay_h1"] = preds["y_pred_delay"]
        preds["y_pred_delay_h3"] = preds["y_pred_delay"]
        preds["y_pred_delay_h5"] = preds["y_pred_delay"]

        # Crowding carry-forward
        idx_to_class = {0: "Low", 1: "Medium", 2: "High"}
        preds["pred_class"] = df["previous_crowding_idx"].map(idx_to_class).fillna("Medium")
        preds["proba_low"] = (preds["pred_class"] == "Low").astype(float)
        preds["proba_medium"] = (preds["pred_class"] == "Medium").astype(float)
        preds["proba_high"] = (preds["pred_class"] == "High").astype(float)

        preds["latency_ms"] = (time.time() - t0) * 1000.0 / max(1, len(df))
        return preds

    def save(self, model_dir: Path):
        model_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load(cls, model_dir: Path):
        return cls()

    def model_card(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "family": self.family,
            "tasks": ["delay", "crowding"],
            "train_time_seconds": self.train_time_s,
            "n_parameters": 0
        }

class HistoricalMeanBaseline:
    model_id = "historical_mean_baseline"
    family = "baseline"
    task: Literal["joint"] = "joint"

    def __init__(self):
        self.lookup_delay: Dict = {}
        self.lookup_crowd: Dict = {}
        self.global_mean_delay = 0.0
        self.global_mode_crowd = "Medium"
        self.train_time_s = 0.0

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None, cfg: Dict[str, Any] = None):
        t0 = time.time()
        self.global_mean_delay = float(train_df["y_delay"].mean())
        if "y_crowd_class" in train_df.columns:
            mode_series = train_df["y_crowd_class"].mode()
            self.global_mode_crowd = str(mode_series.iloc[0]) if len(mode_series) > 0 else "Medium"

        grouped = train_df.groupby(["route_id", "stop_id", "hour"])
        self.lookup_delay = grouped["y_delay"].mean().to_dict()
        
        # Crowding mode
        for (r, s, h), sub in grouped:
            c_mode = sub["y_crowd_class"].mode()
            self.lookup_crowd[(r, s, h)] = c_mode.iloc[0] if len(c_mode) > 0 else "Medium"

        self.train_time_s = time.time() - t0

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        t0 = time.time()
        preds = pd.DataFrame()
        preds["obs_id"] = df["obs_id"]

        delays = []
        crowds = []
        for _, row in df.iterrows():
            key = (row["route_id"], row["stop_id"], row["hour"])
            delays.append(self.lookup_delay.get(key, self.global_mean_delay))
            crowds.append(self.lookup_crowd.get(key, self.global_mode_crowd))

        preds["y_pred_delay"] = delays
        preds["q10"] = preds["y_pred_delay"] - 3.5
        preds["q50"] = preds["y_pred_delay"]
        preds["q90"] = preds["y_pred_delay"] + 4.5

        preds["y_pred_delay_h1"] = preds["y_pred_delay"]
        preds["y_pred_delay_h3"] = preds["y_pred_delay"]
        preds["y_pred_delay_h5"] = preds["y_pred_delay"]

        preds["pred_class"] = crowds
        preds["proba_low"] = (preds["pred_class"] == "Low").astype(float)
        preds["proba_medium"] = (preds["pred_class"] == "Medium").astype(float)
        preds["proba_high"] = (preds["pred_class"] == "High").astype(float)

        preds["latency_ms"] = (time.time() - t0) * 1000.0 / max(1, len(df))
        return preds

    def save(self, model_dir: Path):
        model_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def load(cls, model_dir: Path):
        return cls()

    def model_card(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "family": self.family,
            "tasks": ["delay", "crowding"],
            "train_time_seconds": self.train_time_s,
            "n_parameters": len(self.lookup_delay)
        }

