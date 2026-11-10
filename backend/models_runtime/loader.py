"""
Runtime model loader with graceful fallbacks (Section 5 Failure Matrix).
"""

from pathlib import Path
from typing import Dict, Any, Optional
import joblib

class ModelRuntimeLoader:
    _loaded_cache: Dict[str, Any] = {}

    @classmethod
    def load_model(cls, model_id: str):
        if model_id in cls._loaded_cache:
            return cls._loaded_cache[model_id]

        model_dir = Path(f"models/{model_id}")
        
        # Check classical models
        if (model_dir / "model.joblib").exists():
            if model_id == "m1_ridge_logistic":
                from ml.classical.linear import LinearModelArena
                m = LinearModelArena.load(model_dir)
            elif model_id == "m2_random_forest":
                from ml.classical.random_forest import RandomForestModelArena
                m = RandomForestModelArena.load(model_dir)
            else:
                from ml.classical.xgboost_model import XGBoostModelArena
                m = XGBoostModelArena.load(model_dir)
            cls._loaded_cache[model_id] = m
            return m

        # Check deep models if torch available
        if (model_dir / "model.pt").exists():
            try:
                if model_id == "m4_gru":
                    from ml.deep.gru import GRUModelArena
                    m = GRUModelArena.load(model_dir)
                else:
                    from ml.deep.st_gnn import STGNNModelArena
                    m = STGNNModelArena.load(model_dir)
                cls._loaded_cache[model_id] = m
                return m
            except Exception:
                pass

        # Baselines
        if model_id == "persistence_baseline":
            from ml.classical.baselines import PersistenceBaseline
            return PersistenceBaseline()
        elif model_id == "historical_mean_baseline":
            from ml.classical.baselines import HistoricalMeanBaseline
            return HistoricalMeanBaseline()

        # Fallback to XGBoost default
        from ml.classical.xgboost_model import XGBoostModelArena
        m = XGBoostModelArena()
        cls._loaded_cache[model_id] = m
        return m

