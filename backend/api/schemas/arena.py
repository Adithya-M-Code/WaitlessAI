"""
Model Arena API schemas.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class LeaderboardEntry(BaseModel):
    model_id: str
    family: str
    data_source: str
    delay_mae: float
    delay_rmse: float
    interval_coverage: float
    crowd_macro_f1: float
    crowd_qwk: float
    latency_ms: float

class ArenaLeaderboardResponse(BaseModel):
    leaderboard: List[Dict[str, Any]]
    champion: Dict[str, str]
    significance: Dict[str, Any]
    data_source: str

