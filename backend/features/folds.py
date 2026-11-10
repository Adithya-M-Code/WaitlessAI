"""
Time-ordered splits and 5 rolling-origin expanding window cross-validation folds.
Strictly adheres to Rule R4: Time-ordered splits only, zero random shuffle, zero lookahead.
"""

import json
from pathlib import Path
from typing import Dict, List
import pandas as pd

class TimeSplitter:
    @staticmethod
    def create_splits(
        df: pd.DataFrame,
        time_col: str = "observed_at_utc",
        output_dir: str = "data/datasets/v1"
    ) -> Dict:
        """
        Creates:
        1. 70/15/15 time split (train/val/test)
        2. 5 rolling-origin expanding window folds
        """
        sorted_df = df.sort_values(by=time_col).reset_index(drop=True)
        total_obs = len(sorted_df)

        idx_70 = int(0.70 * total_obs)
        idx_85 = int(0.85 * total_obs)

        # 70/15/15 main split
        splits_info = {
            "main": {
                "train": {
                    "start": str(sorted_df.iloc[0][time_col]),
                    "end": str(sorted_df.iloc[idx_70 - 1][time_col]),
                    "count": idx_70,
                    "indices": [0, idx_70]
                },
                "val": {
                    "start": str(sorted_df.iloc[idx_70][time_col]),
                    "end": str(sorted_df.iloc[idx_85 - 1][time_col]),
                    "count": idx_85 - idx_70,
                    "indices": [idx_70, idx_85]
                },
                "test": {
                    "start": str(sorted_df.iloc[idx_85][time_col]),
                    "end": str(sorted_df.iloc[-1][time_col]),
                    "count": total_obs - idx_85,
                    "indices": [idx_85, total_obs]
                }
            },
            "rolling_folds": []
        }

        # 5 rolling-origin expanding window folds (evaluated on the train+val period)
        # Fold 1: train 30%, test 10%
        # Fold 2: train 40%, test 10%
        # ...
        # Fold 5: train 70%, test 15%
        for fold_idx in range(5):
            train_end_pct = 0.30 + fold_idx * 0.10
            val_end_pct = train_end_pct + 0.08
            
            f_train_end = int(train_end_pct * total_obs)
            f_val_end = min(total_obs, int(val_end_pct * total_obs))

            splits_info["rolling_folds"].append({
                "fold": fold_idx + 1,
                "train_indices": [0, f_train_end],
                "val_indices": [f_train_end, f_val_end],
                "train_count": f_train_end,
                "val_count": f_val_end - f_train_end
            })

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        with open(out_path / "folds.json", "w", encoding="utf-8") as f:
            json.dump(splits_info, f, indent=2)

        return splits_info

