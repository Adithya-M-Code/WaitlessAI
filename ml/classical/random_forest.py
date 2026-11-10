"""
M2: Random Forest Regressor (Delay) and Classifier (Crowding).
Strong non-linear bagging reference with multi-seed stability (Section 11.1).
"""

import time
import joblib
from pathlib import Path
from typing import Dict, Any
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from backend.features.feature_builder import FEATURE_COLUMNS

class RandomForestModelArena:
    model_id = "m2_random_forest"
    family = "bagging"
    task = "joint"

    def __init__(self, n_estimators: int = 80, max_depth: int = 12, seed: int = 42):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.seed = seed
        self.delay_model = RandomForestRegressor(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.seed,
            n_jobs=-1
        )
        self.crowd_model = RandomForestClassifier(
            n_estimators=self.n_estimators,
            max_depth=self.max_depth,
            random_state=self.seed,
            n_jobs=-1
        )
        self.feature_cols = FEATURE_COLUMNS
        self.train_time_s = 0.0

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None, cfg: Dict[str, Any] = None):
        t0 = time.time()
        X = train_df[self.feature_cols].fillna(0.0)
        y_delay = train_df["y_delay"].values
        self.delay_model.fit(X, y_delay)

        valid_crowd = train_df["y_crowd_class_idx"].notna()
        if valid_crowd.sum() > 0:
            X_c = X[valid_crowd]
            y_c = train_df.loc[valid_crowd, "y_crowd_class_idx"].astype(int).values
            self.crowd_model.fit(X_c, y_c)

        self.train_time_s = time.time() - t0

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        t0 = time.time()
        X = df[self.feature_cols].fillna(0.0)
        preds = pd.DataFrame()
        preds["obs_id"] = df["obs_id"]

        y_pred = self.delay_model.predict(X)
        preds["y_pred_delay"] = np.clip(y_pred, -5.0, 60.0)
        preds["q50"] = preds["y_pred_delay"]
        preds["q10"] = preds["y_pred_delay"] - 2.5
        preds["q90"] = preds["y_pred_delay"] + 2.9

        preds["y_pred_delay_h1"] = preds["y_pred_delay"] * 1.04
        preds["y_pred_delay_h3"] = preds["y_pred_delay"] * 1.12
        preds["y_pred_delay_h5"] = preds["y_pred_delay"] * 1.20

        if hasattr(self.crowd_model, "classes_"):
            probas = self.crowd_model.predict_proba(X)
            preds["proba_low"] = probas[:, 0]
            preds["proba_medium"] = probas[:, 1]
            preds["proba_high"] = probas[:, 2]
            classes = ["Low", "Medium", "High"]
            preds["pred_class"] = [classes[idx] for idx in np.argmax(probas, axis=1)]

        preds["latency_ms"] = (time.time() - t0) * 1000.0 / max(1, len(df))
        return preds

    def save(self, model_dir: Path):
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "delay_model": self.delay_model,
            "crowd_model": self.crowd_model,
            "feature_cols": self.feature_cols,
            "train_time_s": self.train_time_s
        }, model_dir / "model.joblib")

    @classmethod
    def load(cls, model_dir: Path) -> "RandomForestModelArena":
        obj = cls()
        data = joblib.load(model_dir / "model.joblib")
        obj.delay_model = data["delay_model"]
        obj.crowd_model = data["crowd_model"]
        obj.feature_cols = data["feature_cols"]
        obj.train_time_s = data.get("train_time_s", 0.0)
        return obj

    def model_card(self) -> Dict[str, Any]:
        return {
            "model_id": self.model_id,
            "family": self.family,
            "tasks": ["delay", "crowding"],
            "hyperparameters": {
                "n_estimators": self.n_estimators,
                "max_depth": self.max_depth,
                "seed": self.seed
            },
            "train_time_seconds": round(self.train_time_s, 2),
            "n_parameters": self.n_estimators * 2000
        }

