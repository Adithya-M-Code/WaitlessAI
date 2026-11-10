"""
I/O utilities for dataset loading and Section 10 prediction file serialization.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple
import pandas as pd
import numpy as np

PREDICTION_COLUMNS = [
    "obs_id",
    "y_pred_delay",
    "q10",
    "q50",
    "q90",
    "y_pred_delay_h1",
    "y_pred_delay_h3",
    "y_pred_delay_h5",
    "proba_low",
    "proba_medium",
    "proba_high",
    "pred_class",
    "latency_ms"
]

def load_dataset(version: str = "v1") -> Tuple[pd.DataFrame, Dict]:
    """Loads tabular dataset and folds metadata."""
    ds_path = Path(f"data/datasets/{version}")
    df = pd.read_parquet(ds_path / "tabular_dataset.parquet")
    with open(ds_path / "folds.json", "r", encoding="utf-8") as f:
        folds = json.load(f)
    return df, folds

def save_predictions(
    model_id: str,
    split_name: str,
    preds_df: pd.DataFrame,
    predictions_root: str = "ml/arena/predictions"
):
    """
    Saves predictions adhering strictly to Section 10 schema:
    ml/arena/predictions/{model_id}/{split_name}.parquet
    """
    target_dir = Path(predictions_root) / model_id
    target_dir.mkdir(parents=True, exist_ok=True)
    out_file = target_dir / f"{split_name}.parquet"

    # Ensure all required columns exist (nullable)
    clean_df = preds_df.copy()
    for col in PREDICTION_COLUMNS:
        if col not in clean_df.columns:
            clean_df[col] = np.nan

    clean_df[PREDICTION_COLUMNS].to_parquet(out_file, index=False)

def load_predictions(
    model_id: str,
    split_name: str,
    predictions_root: str = "ml/arena/predictions"
) -> pd.DataFrame:
    path = Path(predictions_root) / model_id / f"{split_name}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Prediction file not found: {path}")
    return pd.read_parquet(path)

