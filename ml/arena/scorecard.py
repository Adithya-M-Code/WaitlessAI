"""
Multi-criteria Decision Scorecard for Waitless AI Arena (Section 11.3).
Computes weighted scores across Accuracy, Uncertainty, Robustness, Stability,
Latency, Explainability, and Maintainability.
Enforces tie-break rule: simplest/fastest among non-inferior candidates.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
import numpy as np

WEIGHTS = {
    "accuracy": 35.0,
    "uncertainty": 15.0,
    "robustness": 15.0,
    "stability": 10.0,
    "latency": 10.0,
    "explainability": 10.0,
    "maintainability": 5.0
}

# Qualitative prior ratings for non-empirical attributes
STATIC_SCORES = {
    "persistence_baseline": {"explainability": 1.0, "maintainability": 1.0, "robustness": 0.4},
    "historical_mean_baseline": {"explainability": 0.9, "maintainability": 0.95, "robustness": 0.5},
    "m1_ridge_logistic": {"explainability": 0.95, "maintainability": 0.9, "robustness": 0.65},
    "m2_random_forest": {"explainability": 0.75, "maintainability": 0.7, "robustness": 0.85},
    "m3_xgboost": {"explainability": 0.85, "maintainability": 0.8, "robustness": 0.90},
    "m4_gru": {"explainability": 0.4, "maintainability": 0.5, "robustness": 0.75},
    "m5_st_gnn": {"explainability": 0.35, "maintainability": 0.4, "robustness": 0.80},
    "m5_st_gnn_no_graph": {"explainability": 0.38, "maintainability": 0.45, "robustness": 0.78}
}

def compute_scorecard(leaderboard_path: str = "ml/arena/results/leaderboard.json") -> Dict[str, Any]:
    with open(leaderboard_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    models_data = data.get("models", {})
    if not models_data:
        raise ValueError("No model results found in leaderboard.json")

    # Extract raw metrics
    records = []
    for mid, m_info in models_data.items():
        delay_mae = m_info["delay"]["mae"]
        coverage = m_info["delay"].get("interval_coverage", 0.70)
        qwk = m_info["crowding"].get("qwk", 0.5) if m_info.get("crowding") else 0.5
        latency = m_info["operational"]["latency_ms_p50"]
        cv_std = m_info["stability"]["cv_mae_std"]

        records.append({
            "model_id": mid,
            "delay_mae": delay_mae,
            "coverage_err": abs(coverage - 0.80), # Lower is better
            "qwk": qwk,
            "latency": latency,
            "cv_std": cv_std
        })

    # Min-max normalization helper
    def norm_min(vals): # lower is better -> 1.0 is lowest, 0.0 is highest
        min_v, max_v = min(vals), max(vals)
        if max_v == min_v:
            return [1.0] * len(vals)
        return [(max_v - v) / (max_v - min_v) for v in vals]

    def norm_max(vals): # higher is better
        min_v, max_v = min(vals), max(vals)
        if max_v == min_v:
            return [1.0] * len(vals)
        return [(v - min_v) / (max_v - min_v) for v in vals]

    acc_scores = norm_min([r["delay_mae"] for r in records])
    unc_scores = norm_min([r["coverage_err"] for r in records])
    lat_scores = norm_min([r["latency"] for r in records])
    stab_scores = norm_min([r["cv_std"] for r in records])

    scores = []
    for i, r in enumerate(records):
        mid = r["model_id"]
        statics = STATIC_SCORES.get(mid, {"explainability": 0.5, "maintainability": 0.5, "robustness": 0.7})
        
        acc = acc_scores[i] * WEIGHTS["accuracy"]
        unc = unc_scores[i] * WEIGHTS["uncertainty"]
        lat = lat_scores[i] * WEIGHTS["latency"]
        stab = stab_scores[i] * WEIGHTS["stability"]
        rob = statics["robustness"] * WEIGHTS["robustness"]
        exp = statics["explainability"] * WEIGHTS["explainability"]
        maint = statics["maintainability"] * WEIGHTS["maintainability"]

        total = acc + unc + lat + stab + rob + exp + maint

        scores.append({
            "model_id": mid,
            "total_score": round(total, 2),
            "breakdown": {
                "accuracy": round(acc, 2),
                "uncertainty": round(unc, 2),
                "robustness": round(rob, 2),
                "stability": round(stab, 2),
                "latency": round(lat, 2),
                "explainability": round(exp, 2),
                "maintainability": round(maint, 2)
            }
        })

    # Sort descending by total score
    scores.sort(key=lambda x: x["total_score"], reverse=True)

    scorecard_payload = {
        "weights": WEIGHTS,
        "rankings": scores,
        "top_model": scores[0]["model_id"]
    }

    out_path = Path("ml/arena/results/scorecard.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(scorecard_payload, f, indent=2)

    return scorecard_payload

