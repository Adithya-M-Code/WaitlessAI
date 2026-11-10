"""
Data freshness tracking service (Rule R6).
fresh (<60s), aging (60-180s), stale (>180s).
"""

from datetime import datetime, timezone
from typing import Dict, Literal, Tuple
import os

class FreshnessService:
    def __init__(self, stale_threshold_s: int = 180):
        self.stale_threshold_s = stale_threshold_s

    @staticmethod
    def tier_for_age(age_s: int, live_threshold_s: int = 180) -> Literal["live", "recent", "schedule"]:
        """Map an observation age to the public degradation tier."""
        if age_s <= live_threshold_s:
            return "live"
        if age_s <= 600:
            return "recent"
        return "schedule"

    def tier_for_timestamp(self, timestamp_utc: datetime) -> Tuple[int, Literal["live", "recent", "schedule"]]:
        age, _ = self.evaluate(timestamp_utc)
        return age, self.tier_for_age(age, self.stale_threshold_s)

    def evaluate(self, timestamp_utc: datetime) -> Tuple[int, Literal["fresh", "aging", "stale"]]:
        now = datetime.now(timezone.utc)
        if timestamp_utc.tzinfo is None:
            timestamp_utc = timestamp_utc.replace(tzinfo=timezone.utc)
        
        age = int(max(0, (now - timestamp_utc).total_seconds()))
        if age <= 60:
            state = "fresh"
        elif age <= self.stale_threshold_s:
            state = "aging"
        else:
            state = "stale"
        return age, state
