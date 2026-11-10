"""
Deep Learning training orchestrator for Waitless AI.
Trains M4 GRU and M5 Spatio-Temporal GNN across rolling folds and test split.
Also trains the no-graph ablation of ST-GNN to answer the research question:
'Does bus network graph structure genuinely improve prediction?'
"""

import json
from pathlib import Path
import pandas as pd
import numpy as np

from ml.core.io import load_dataset, save_predictions
from ml.core.seeds import set_seeds
from ml.deep.gru import GRUModelArena
from ml.deep.st_gnn import STGNNModelArena
from ml.uncertainty.conformal import ConformalWrapper

def train_deep_lineup():
    set_seeds(42)
    df, folds_info = load_dataset("v1")

    train_indices = folds_info["main"]["train"]["indices"]
    val_indices = folds_info["main"]["val"]["indices"]
    test_indices = folds_info["main"]["test"]["indices"]

    train_df = df.iloc[train_indices[0]:train_indices[1]].copy()
    val_df = df.iloc[val_indices[0]:val_indices[1]].copy()
    test_df = df.iloc[test_indices[0]:test_indices[1]].copy()

    deep_models = [
        GRUModelArena(hidden_dim=32, epochs=3),
        STGNNModelArena(hidden_dim=32, epochs=3, use_graph=True),
        STGNNModelArena(hidden_dim=32, epochs=3, use_graph=False) # Ablation: no graph
    ]

    for model in deep_models:
        if hasattr(model, "use_graph") and not model.use_graph:
            model_name = "m5_st_gnn_no_graph"
        else:
            model_name = model.model_id
        print(f"Training deep model: {model_name}...")

        # Rolling folds
        for fold in folds_info["rolling_folds"][:3]: # Train first 3 folds to conserve budget
            f_id = fold["fold"]
            f_train = df.iloc[fold["train_indices"][0]:fold["train_indices"][1]]
            f_val = df.iloc[fold["val_indices"][0]:fold["val_indices"][1]]
            model.fit(f_train, f_val)
            preds = model.predict(f_val)
            save_predictions(model_name, f"fold_{f_id}", preds)

        # Main fit
        model.fit(train_df, val_df)

        val_preds = model.predict(val_df)
        conformal = ConformalWrapper(target_coverage=0.80)
        conformal.calibrate(val_df["y_delay"].values, val_preds["y_pred_delay"].values)

        test_preds = model.predict(test_df)
        test_preds = conformal.apply_intervals(test_preds)
        save_predictions(model_name, "test", test_preds)

        artifact_dir = Path(f"models/{model_name}")
        model.save(artifact_dir)
        conformal.save(artifact_dir)

        card = model.model_card()
        card["model_id"] = model_name
        card["data_version"] = "v1"
        with open(artifact_dir / "model_card.json", "w", encoding="utf-8") as f:
            json.dump(card, f, indent=2)

    print("Deep learning lineup completed!")

