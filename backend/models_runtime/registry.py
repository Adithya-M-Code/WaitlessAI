"""
Model registry manager for Waitless AI.
Loads models/registry.json and manages champion/challenger references.
"""

import json
from pathlib import Path
from typing import Dict, Any, List

REGISTRY_DEFAULT = {
    "delay": {
        "champion": "m3_xgboost",
        "challengers": ["m2_random_forest", "m1_ridge_logistic", "m4_gru", "m5_st_gnn"]
    },
    "crowding": {
        "champion": "m3_xgboost",
        "challengers": ["m2_random_forest", "m1_ridge_logistic", "m4_gru", "m5_st_gnn"]
    },
    "data_source": "synthetic",
    "approved_by_human": False
}

class ModelRegistry:
    def __init__(self, registry_path: str = "models/registry.json"):
        self.path = Path(registry_path)

    def get_registry(self) -> Dict[str, Any]:
        if self.path.exists():
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return REGISTRY_DEFAULT

    def get_champion_id(self, task: str = "delay") -> str:
        reg = self.get_registry()
        return reg.get(task, {}).get("champion", "m3_xgboost")

