"""
Sequence builder for deep models (M4 GRU and M5 ST-GNN).
Produces fixed-length historical observation windows of size K=8 per sample.
"""

from pathlib import Path
from typing import Dict, Tuple
import numpy as np
import pandas as pd

class SequenceBuilder:
    def __init__(self, k_steps: int = 8):
        self.k_steps = k_steps

    def build_sequences(
        self,
        df: pd.DataFrame,
        feature_cols: list
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Constructs (N, K, D) feature tensors and (N, K) masks.
        Groups observations by vehicle_no and route_id, tracking last K points.
        """
        sorted_df = df.sort_values(by=["route_id", "vehicle_no", "observed_at_utc"]).reset_index(drop=True)
        
        X_mat = sorted_df[feature_cols].values
        n_samples = len(sorted_df)
        d_features = len(feature_cols)

        sequences = np.zeros((n_samples, self.k_steps, d_features), dtype=np.float32)
        masks = np.zeros((n_samples, self.k_steps), dtype=np.float32)

        grouped = sorted_df.groupby(["route_id", "vehicle_no"]).indices

        for _, indices in grouped.items():
            for i, idx in enumerate(indices):
                start_pos = max(0, i - self.k_steps + 1)
                window_indices = indices[start_pos:i + 1]
                window_len = len(window_indices)
                
                # Fill right-aligned (latest observation at end of sequence)
                target_slice = slice(self.k_steps - window_len, self.k_steps)
                sequences[idx, target_slice, :] = X_mat[window_indices]
                masks[idx, target_slice] = 1.0

        return sequences, masks

    def save_split_sequences(
        self,
        sequences: np.ndarray,
        masks: np.ndarray,
        split_name: str,
        output_dir: str = "data/datasets/v1"
    ):
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / f"sequences_{split_name}.npz"
        np.savez_compressed(out_file, sequences=sequences, masks=masks)

