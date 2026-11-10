"""
M1: Ridge Regression (Delay) and Multinomial Logistic Regression (Crowding).
Includes standard feature scaling fitted on training only (Rule R4).
"""

import time
import joblib
from pathlib import Path
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.preprocessing import StandardScaler
from backend.features.feature_builder import FEATURE_COLUMNS

class LinearModelArena:
    model_id = "m1_ridge_logistic"
    family = "linear"
    task = "joint"

    def __init__(self, alpha: float = 1.0, C: float = 1.0):
        self.alpha = alpha
        self.C = C
        self.scaler = StandardScaler()
        self.delay_model = Ridge(alpha=self.alpha)
        self.crowd_model = LogisticRegression(C=self.C, max_iter=500, multi_class="multinomial")
        self.train_time_s = 0.0
        self.feature_cols = FEATURE_COLUMNS

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None, cfg: Dict[str, Any] = None):
        t0 = time.time()
        X_train = train_df[self.feature_cols].fillna(0.0)
        X_scaled = self.scaler.fit_transform(X_train)

        # Fit delay
        y_delay = train_df["y_delay"].values
        self.delay_model.fit(X_scaled, y_delay)

        # Fit crowding
        valid_crowd = train_df["y_crowd_class_idx"].notna()
        if valid_crowd.sum() > 0:
            X_c = X_scaled[valid_crowd]
            y_c = train_df.loc[valid_crowd, "y_crowd_class_idx"].astype(int).values
            self.crowd_model.fit(X_c, y_c)

        self.train_time_s = time.time() - t0

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        t0 = time.time()
        X = df[self.feature_cols].fillna(0.0)
        X_scaled = self.scaler.transform(X)

        preds = pd.DataFrame()
        preds["obs_id"] = df["obs_id"]
        
        # Delay predictions
        y_pred = self.delay_model.predict(X_scaled)
        preds["y_pred_delay"] = np.clip(y_pred, -5.0, 60.0)
        preds["q50"] = preds["y_pred_delay"]
        # Quantile estimates will be refined by conformal wrapper
        preds["q10"] = preds["y_pred_delay"] - 2.8
        preds["q90"] = preds["y_pred_delay"] + 3.2

        # Downstream predictions
        preds["y_pred_delay_h1"] = preds["y_pred_delay"] * 1.05
        preds["y_pred_delay_h3"] = preds["y_pred_delay"] * 1.15
        preds["y_pred_delay_h5"] = preds["y_pred_delay"] * 1.25

        # Crowding probabilities
        if hasattr(self.crowd_model, "classes_"):
            probas = self.crowd_model.predict_proba(X_scaled)
            preds["proba_low"] = probas[:, 0]
            preds["proba_medium"] = probas[:, 1]
            preds["proba_high"] = probas[:, 2]
            classes = ["Low", "Medium", "High"]
            preds["pred_class"] = [classes[idx] for idx in np.argmax(probas, axis=1)]
        else:
            preds["proba_low"] = 0.33
            preds["proba_medium"] = 0.34
            preds["proba_high"] = 0.33
            preds["pred_class"] = "Medium"

        preds["latency_ms"] = (time.time() - t0) * 1000.0 / max(1, len(df))
        return preds

    def save(self, model_dir: Path):
        model_dir.mkdir(parents=True, exist_ok=True)
        joblib.dump({
            "scaler": self.scaler,
            "delay_model": self.delay_model,
            "crowd_model": self.crowd_model,
            "feature_cols": self.feature_cols,
            "train_time_s": self.train_time_s
        }, model_dir / "model.joblib")

    @classmethod
    def load(cls, model_dir: Path) -> "LinearModelArena":
        obj = cls()
        data = joblib.load(model_dir / "model.joblib")
        obj.scaler = data["scaler"]
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
            "hyperparameters": {"alpha": self.alpha, "C": self.C},
            "train_time_seconds": round(self.train_time_s, 2),
            "n_parameters": len(self.feature_cols) * 4
        }

