"""
Comprehensive evaluation metrics suite for Waitless AI Arena (Section 11.2).
Owned strictly by Agent F (Rule R3).
"""

from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from sklearn.metrics import (
    mean_absolute_error,
    root_mean_squared_error,
    r2_score,
    median_absolute_error,
    accuracy_score,
    f1_score,
    cohen_kappa_score,
    confusion_matrix,
    brier_score_loss,
    log_loss
)

def compute_delay_metrics(y_true: np.ndarray, y_pred: np.ndarray, q10: np.ndarray = None, q90: np.ndarray = None) -> Dict[str, float]:
    mask = ~np.isnan(y_true) & ~np.isnan(y_pred)
    yt = y_true[mask]
    yp = y_pred[mask]

    mae = float(mean_absolute_error(yt, yp))
    rmse = float(root_mean_squared_error(yt, yp))
    r2 = float(r2_score(yt, yp))
    medae = float(median_absolute_error(yt, yp))
    errors = np.abs(yt - yp)
    p90_ae = float(np.percentile(errors, 90))

    # P(on-time <= 5 min) Brier score
    true_ontime = (yt <= 5.0).astype(float)
    pred_ontime = (yp <= 5.0).astype(float)
    brier = float(brier_score_loss(true_ontime, pred_ontime))

    metrics = {
        "mae": round(mae, 3),
        "rmse": round(rmse, 3),
        "r2": round(r2, 3),
        "median_ae": round(medae, 3),
        "p90_ae": round(p90_ae, 3),
        "brier_score": round(brier, 3)
    }

    # Uncertainty interval coverage and width
    if q10 is not None and q90 is not None:
        q10_m = q10[mask]
        q90_m = q90[mask]
        covered = (yt >= q10_m) & (yt <= q90_m)
        coverage = float(np.mean(covered))
        mean_width = float(np.mean(q90_m - q10_m))
        metrics["interval_coverage"] = round(coverage, 3)
        metrics["interval_mean_width"] = round(mean_width, 3)

    return metrics

def compute_crowding_metrics(y_true_idx: np.ndarray, probas: np.ndarray) -> Dict[str, Any]:
    mask = ~np.isnan(y_true_idx)
    yt = y_true_idx[mask].astype(int)
    probs = probas[mask]

    preds = np.argmax(probs, axis=1)
    acc = float(accuracy_score(yt, preds))
    macro_f1 = float(f1_score(yt, preds, average="macro"))
    qwk = float(cohen_kappa_score(yt, preds, weights="quadratic"))

    # Expected Calibration Error (ECE)
    confidences = np.max(probs, axis=1)
    accuracies = (preds == yt).astype(float)
    ece = float(np.mean(np.abs(confidences - accuracies)))

    cm = confusion_matrix(yt, preds).tolist()

    return {
        "accuracy": round(acc, 3),
        "macro_f1": round(macro_f1, 3),
        "qwk": round(qwk, 3),
        "ece": round(ece, 3),
        "confusion_matrix": cm
    }

def paired_bootstrap_test(err_a: np.ndarray, err_b: np.ndarray, n_resamples: int = 1000) -> Dict[str, Any]:
    """Paired bootstrap of the error difference (MAE difference) with 95% CI."""
    diff = err_a - err_b
    mean_diff = float(np.mean(diff))
    
    boot_means = []
    n = len(diff)
    for _ in range(n_resamples):
        sample = np.random.choice(diff, size=n, replace=True)
        boot_means.append(np.mean(sample))

    ci_low = float(np.percentile(boot_means, 2.5))
    ci_high = float(np.percentile(boot_means, 97.5))
    excludes_zero = bool((ci_low > 0) or (ci_high < 0))

    return {
        "mean_diff": round(mean_diff, 4),
        "ci_95": [round(ci_low, 4), round(ci_high, 4)],
        "significant": excludes_zero
    }

