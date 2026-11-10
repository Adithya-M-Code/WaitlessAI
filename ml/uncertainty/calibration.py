"""
Probability calibration for crowding classification.
Applies Isotonic / Temperature scaling to raw class probabilities.
"""

from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression

class CrowdingCalibrator:
    def __init__(self):
        self.regressors = [IsotonicRegression(out_of_bounds="clip") for _ in range(3)]
        self.fitted = False

    def fit(self, probas: np.ndarray, y_true_idx: np.ndarray):
        """Fits isotonic calibrator for each class (one-vs-rest)."""
        if len(probas) == 0:
            return
        for c in range(3):
            binary_target = (y_true_idx == c).astype(float)
            self.regressors[c].fit(probas[:, c], binary_target)
        self.fitted = True

    def calibrate(self, probas: np.ndarray) -> np.ndarray:
        if not self.fitted:
            return probas
        calibrated = np.zeros_like(probas)
        for c in range(3):
            calibrated[:, c] = self.regressors[c].predict(probas[:, c])
        # Renormalize rows to sum to 1.0
        row_sums = calibrated.sum(axis=1, keepdims=True)
        row_sums[row_sums == 0] = 1.0
        return calibrated / row_sums

