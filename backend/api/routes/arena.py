"""
Model Arena, Scorecard, and Model Registry endpoints.
"""

import json
from pathlib import Path
from fastapi import APIRouter
from backend.models_runtime.registry import ModelRegistry

router = APIRouter(tags=["Arena"])
registry = ModelRegistry()

@router.get("/arena/leaderboard")
def get_arena_leaderboard(task: str = "delay"):
    lb_path = Path("ml/arena/results/leaderboard.json")
    if lb_path.exists():
        with open(lb_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"status": "pending_evaluation", "models": {}, "data_source": "synthetic"}

@router.get("/arena/scorecard")
def get_arena_scorecard():
    sc_path = Path("ml/arena/results/scorecard.json")
    if sc_path.exists():
        with open(sc_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"status": "pending_scorecard", "rankings": []}

@router.get("/models/registry")
def get_models_registry():
    return registry.get_registry()

