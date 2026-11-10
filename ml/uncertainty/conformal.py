"""
Model-agnostic Split-Conformal Prediction & CQR (Section 11.1).
Wraps any ArenaModel to guarantee valid empirical prediction intervals (target coverage 80%).
Calibrated strictly on validation split residuals (Rule R4).
"""

import json
from pathlib import Path
from typing import Dict, Tuple
import numpy as np
import pandas as pd

class ConformalWrapper:
    def __init__(self, target_coverage: float = 0.80):
        self.target_coverage = target_coverage
        self.q_low_offset: float = -2.5
        self.q_high_offset: float = 3.0

    def calibrate(self, y_true: np.ndarray, y_pred: np.ndarray):
        """
        Calibrates residual quantiles on validation set.
        Non-conformity score = y_true - y_pred.
        For 80% coverage, alpha = 0.20 -> lower quantile at 0.10, upper quantile at 0.90.
        """
        residuals = y_true - y_pred
        alpha = 1.0 - self.target_coverage
        self.q_low_offset = float(np.quantile(residuals, alpha / 2.0))
        self.q_high_offset = float(np.quantile(residuals, 1.0 - (alpha / 2.0)))

    def apply_intervals(self, preds_df: pd.DataFrame) -> pd.DataFrame:
        """Applies calibrated offsets to prediction dataframe."""
        df = preds_df.copy()
        if "y_pred_delay" in df.columns:
            df["q10"] = df["y_pred_delay"] + self.q_low_offset
            df["q50"] = df["y_pred_delay"]
            df["q90"] = df["y_pred_delay"] + self.q_high_offset
        return df

    def save(self, model_dir: Path):
        model_dir.mkdir(parents=True, exist_ok=True)
        with open(model_dir / "conformal_quantiles.json", "w", encoding="utf-8") as f:
            json.dump({
                "target_coverage": self.target_coverage,
                "q_low_offset": self.q_low_offset,
                "q_high_offset": self.q_high_offset
            }, f, indent=2)

    def load(self, model_dir: Path):
        path = model_dir / "conformal_quantiles.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.target_coverage = data.get("target_coverage", 0.80)
                self.q_low_offset = data.get("q_low_offset", -2.5)
                self.q_high_offset = data.get("q_high_offset", 3.0)

