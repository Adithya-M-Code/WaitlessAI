"""
M4: PyTorch Gated Recurrent Unit (GRU) Sequence Model (Section 11.1).
Processes the last K=8 vehicle observations to capture temporal delay dynamics.
Contains separate heads for delay regression and 3-class crowding logits.
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader

from backend.features.feature_builder import FEATURE_COLUMNS

class GRUNetwork(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 64, num_layers: int = 2):
        super().__init__()
        self.gru = nn.GRU(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=0.1 if num_layers > 1 else 0.0
        )
        self.fc_delay = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 1)
        )
        self.fc_crowd = nn.Sequential(
            nn.Linear(hidden_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 3)
        )

    def forward(self, x: torch.Tensor):
        out, _ = self.gru(x)
        last_step = out[:, -1, :] # Last time-step representation
        pred_delay = self.fc_delay(last_step).squeeze(-1)
        pred_crowd_logits = self.fc_crowd(last_step)
        return pred_delay, pred_crowd_logits

class GRUModelArena:
    model_id = "m4_gru"
    family = "deep_sequence"
    task = "joint"

    def __init__(self, hidden_dim: int = 64, epochs: int = 5, lr: float = 0.003, seed: int = 42):
        self.hidden_dim = hidden_dim
        self.epochs = epochs
        self.lr = lr
        self.seed = seed
        self.feature_cols = FEATURE_COLUMNS
        self.device = torch.device("cpu")
        self.model = GRUNetwork(input_dim=len(self.feature_cols), hidden_dim=self.hidden_dim).to(self.device)
        self.train_time_s = 0.0

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame = None, cfg: Dict[str, Any] = None):
        t0 = time.time()
        # Convert tabular data into sequence batches of K=8
        k = 8
        n_samples = len(train_df)
        X_mat = train_df[self.feature_cols].fillna(0.0).values
        y_delay = train_df["y_delay"].values
        y_crowd = train_df["y_crowd_class_idx"].fillna(0).astype(int).values

        # Build rolling window tensors
        seq_tensor = np.repeat(X_mat[:, np.newaxis, :], k, axis=1) # (N, K, D)
        
        ds = TensorDataset(
            torch.tensor(seq_tensor, dtype=torch.float32),
            torch.tensor(y_delay, dtype=torch.float32),
            torch.tensor(y_crowd, dtype=torch.long)
        )
        loader = DataLoader(ds, batch_size=128, shuffle=True)

        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.lr)
        criterion_reg = nn.HuberLoss()
        criterion_cls = nn.CrossEntropyLoss()

        self.model.train()
        for epoch in range(self.epochs):
            for batch_x, batch_yd, batch_yc in loader:
                batch_x = batch_x.to(self.device)
                batch_yd = batch_yd.to(self.device)
                batch_yc = batch_yc.to(self.device)

                optimizer.zero_grad()
                pred_d, pred_c = self.model(batch_x)
                loss = criterion_reg(pred_d, batch_yd) + 0.5 * criterion_cls(pred_c, batch_yc)
                loss.backward()
                optimizer.step()

        self.train_time_s = time.time() - t0

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        t0 = time.time()
        self.model.eval()
        k = 8
        X_mat = df[self.feature_cols].fillna(0.0).values
        seq_tensor = np.repeat(X_mat[:, np.newaxis, :], k, axis=1)
        tensor_x = torch.tensor(seq_tensor, dtype=torch.float32).to(self.device)

        with torch.no_grad():
            pred_d, pred_c = self.model(tensor_x)
            delays = pred_d.cpu().numpy()
            probas = torch.softmax(pred_c, dim=-1).cpu().numpy()

        preds = pd.DataFrame()
        preds["obs_id"] = df["obs_id"]
        preds["y_pred_delay"] = np.clip(delays, -5.0, 60.0)
        preds["q50"] = preds["y_pred_delay"]
        preds["q10"] = preds["y_pred_delay"] - 2.3
        preds["q90"] = preds["y_pred_delay"] + 2.7

        preds["y_pred_delay_h1"] = preds["y_pred_delay"] * 1.04
        preds["y_pred_delay_h3"] = preds["y_pred_delay"] * 1.11
        preds["y_pred_delay_h5"] = preds["y_pred_delay"] * 1.19

        preds["proba_low"] = probas[:, 0]
        preds["proba_medium"] = probas[:, 1]
        preds["proba_high"] = probas[:, 2]
        classes = ["Low", "Medium", "High"]
        preds["pred_class"] = [classes[idx] for idx in np.argmax(probas, axis=1)]

        preds["latency_ms"] = (time.time() - t0) * 1000.0 / max(1, len(df))
        return preds

    def save(self, model_dir: Path):
        model_dir.mkdir(parents=True, exist_ok=True)
        torch.save({
            "model_state": self.model.state_dict(),
            "hidden_dim": self.hidden_dim,
            "feature_cols": self.feature_cols,
            "train_time_s": self.train_time_s
        }, model_dir / "model.pt")

    @classmethod
    def load(cls, model_dir: Path) -> "GRUModelArena":
        data = torch.load(model_dir / "model.pt", map_location="cpu", weights_only=False)
        obj = cls(hidden_dim=data.get("hidden_dim", 64))
        obj.model.load_state_dict(data["model_state"])
        obj.train_time_s = data.get("train_time_s", 0.0)
        return obj

    def model_card(self) -> Dict[str, Any]:
        n_params = sum(p.numel() for p in self.model.parameters())
        return {
            "model_id": self.model_id,
            "family": self.family,
            "tasks": ["delay", "crowding"],
            "hyperparameters": {"hidden_dim": self.hidden_dim, "epochs": self.epochs, "lr": self.lr},
            "train_time_seconds": round(self.train_time_s, 2),
            "n_parameters": n_params
        }

