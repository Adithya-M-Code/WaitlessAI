"""
Base model protocol and interface for the Model Arena (Section 9).
Every candidate model in the arena implements this contract.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Literal, Protocol, runtime_checkable
import pandas as pd

@runtime_checkable
class ArenaModel(Protocol):
    model_id: str
    family: str
    task: Literal["delay", "crowding", "joint"]

    def fit(self, train_df: pd.DataFrame, val_df: pd.DataFrame, cfg: Dict[str, Any]) -> None:
        """Fits the model on train_df using val_df strictly for early stopping / validation."""
        ...

    def predict(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Generates predictions conforming strictly to Section 10 prediction file schema:
        obs_id, y_pred_delay, q10, q50, q90, y_pred_delay_h1/h3/h5, proba_low, proba_medium, proba_high, pred_class, latency_ms.
        """
        ...

    def save(self, model_dir: Path) -> None:
        """Serializes model weights and artifacts to models/{model_id}/."""
        ...

    @classmethod
    def load(cls, model_dir: Path) -> "ArenaModel":
        """Deserializes and reconstructs the model from its artifact directory."""
        ...

    def model_card(self) -> Dict[str, Any]:
        """Returns metadata dictionary: params, train_time_s, n_params, seed, framework versions."""
        ...

