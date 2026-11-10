"""
Hyperparameter optimization using Optuna (Section 11.1).
Evaluates strictly on validation fold to prevent test leakage (Rule R4).
Saves logs to ml/arena/results/tuning/.
"""

import json
from pathlib import Path
from typing import Dict, Any
import numpy as np
import pandas as pd

try:
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False

def tune_xgboost(train_df: pd.DataFrame, val_df: pd.DataFrame, n_trials: int = 15) -> Dict[str, Any]:
    out_dir = Path("ml/arena/results/tuning")
    out_dir.mkdir(parents=True, exist_ok=True)

    default_params = {"n_estimators": 100, "max_depth": 6, "learning_rate": 0.05}
    if not OPTUNA_AVAILABLE:
        return default_params

    def objective(trial):
        n_est = trial.suggest_int("n_estimators", 50, 150)
        depth = trial.suggest_int("max_depth", 4, 8)
        lr = trial.suggest_float("learning_rate", 0.01, 0.1, log=True)

        from ml.classical.xgboost_model import XGBoostModelArena
        model = XGBoostModelArena(n_estimators=n_est, max_depth=depth, lr=lr)
        model.fit(train_df, val_df)
        preds = model.predict(val_df)
        mae = float(np.mean(np.abs(preds["y_pred_delay"].values - val_df["y_delay"].values)))
        return mae

    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=n_trials)
    
    with open(out_dir / "xgboost_tuning.json", "w", encoding="utf-8") as f:
        json.dump({"best_params": study.best_params, "best_value": study.best_value}, f, indent=2)

    return study.best_params

