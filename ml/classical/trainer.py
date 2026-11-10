"""
Classical ML training orchestrator for Waitless AI.
Trains reference baselines (Persistence, Historical Mean) and candidates (M1, M2, M3)
across the 5 rolling-origin expanding folds plus final test split.
Applies Conformal prediction intervals and probability calibration.
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

from ml.core.io import load_dataset, save_predictions
from ml.core.seeds import set_seeds
from ml.classical.baselines import PersistenceBaseline, HistoricalMeanBaseline
from ml.classical.linear import LinearModelArena
from ml.classical.random_forest import RandomForestModelArena
from ml.classical.xgboost_model import XGBoostModelArena
from ml.uncertainty.conformal import ConformalWrapper
from ml.uncertainty.calibration import CrowdingCalibrator
from ml.tuning.optuna_search import tune_xgboost

def train_classical_lineup(run_tuning: bool = False):
    set_seeds(42)
    df, folds_info = load_dataset("v1")

    models_to_train = [
        PersistenceBaseline(),
        HistoricalMeanBaseline(),
        LinearModelArena(),
        RandomForestModelArena(),
        XGBoostModelArena()
    ]

    train_indices = folds_info["main"]["train"]["indices"]
    val_indices = folds_info["main"]["val"]["indices"]
    test_indices = folds_info["main"]["test"]["indices"]

    train_df = df.iloc[train_indices[0]:train_indices[1]].copy()
    val_df = df.iloc[val_indices[0]:val_indices[1]].copy()
    test_df = df.iloc[test_indices[0]:test_indices[1]].copy()

    if run_tuning:
        print("Tuning XGBoost hyperparameters with Optuna...")
        best_xgb_params = tune_xgboost(train_df, val_df, n_trials=10)

    for model in models_to_train:
        print(f"Training {model.model_id} ({model.family})...")
        
        # 1. Train on 5 rolling folds to evaluate cross-validation stability
        for fold in folds_info["rolling_folds"]:
            f_id = fold["fold"]
            f_train = df.iloc[fold["train_indices"][0]:fold["train_indices"][1]]
            f_val = df.iloc[fold["val_indices"][0]:fold["val_indices"][1]]

            model.fit(f_train, f_val)
            fold_preds = model.predict(f_val)
            save_predictions(model.model_id, f"fold_{f_id}", fold_preds)

        # 2. Main Fit: Train on Train split, calibrate on Val split, evaluate on Test split
        model.fit(train_df, val_df)

        # Calibrate Conformal intervals on Val residuals (Rule R4)
        val_preds = model.predict(val_df)
        conformal = ConformalWrapper(target_coverage=0.80)
        conformal.calibrate(val_df["y_delay"].values, val_preds["y_pred_delay"].values)

        # Calibrate Crowding probabilities
        calibrator = CrowdingCalibrator()
        val_crowd_mask = val_df["y_crowd_class_idx"].notna()
        if val_crowd_mask.sum() > 0:
            val_probas = val_preds.loc[val_crowd_mask, ["proba_low", "proba_medium", "proba_high"]].values
            calibrator.fit(val_probas, val_df.loc[val_crowd_mask, "y_crowd_class_idx"].astype(int).values)

        # Predict on Test split
        test_preds = model.predict(test_df)
        test_preds = conformal.apply_intervals(test_preds)
        save_predictions(model.model_id, "test", test_preds)

        # Save model artifacts and model card
        artifact_dir = Path(f"models/{model.model_id}")
        model.save(artifact_dir)
        conformal.save(artifact_dir)
        
        card = model.model_card()
        card["data_version"] = "v1"
        card["created_at"] = "2026-11-08T20:00:00Z"
        with open(artifact_dir / "model_card.json", "w", encoding="utf-8") as f:
            json.dump(card, f, indent=2)

    print("Classical lineup trained and predictions saved!")

