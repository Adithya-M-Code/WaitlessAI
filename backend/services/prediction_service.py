"""
Core prediction service for Waitless AI.
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional
import numpy as np
import pandas as pd

from backend.api.schemas.prediction import (
    PredictionRequest,
    JointPredictionResponse,
    DelayPrediction,
    CrowdingPrediction,
    ModelMetadata,
    FreshnessInfo
)
from backend.models_runtime.registry import ModelRegistry
from backend.models_runtime.loader import ModelRuntimeLoader
from backend.features.feature_builder import FeatureBuilder

class PredictionService:
    def __init__(self):
        self.registry = ModelRegistry()
        self.feat_builder = FeatureBuilder()

    def predict_joint(self, req: PredictionRequest) -> JointPredictionResponse:
        now = datetime.now(timezone.utc)
        model_id = req.model or self.registry.get_champion_id("delay")
        model = ModelRuntimeLoader.load_model(model_id)

        # Assemble single sample DataFrame
        hour = req.hour if req.hour is not None else now.hour
        day_of_week = req.day_of_week if req.day_of_week is not None else now.weekday()
        prev_delay = req.previous_delay if req.previous_delay is not None else 2.5
        
        crowd_map = {"Low": 0, "Medium": 1, "High": 2}
        prev_crowd_idx = crowd_map.get(req.previous_crowding, 1)

        sample_df = pd.DataFrame([{
            "obs_id": "REQ_001",
            "observed_at_utc": now.isoformat(),
            "route_id": req.route_id,
            "stop_id": req.stop_id,
            "trip_id": "TRIP_LIVE",
            "vehicle_no": req.vehicle_no or "TN-01-N-1234",
            "stop_sequence": 5,
            "delay_minutes": prev_delay,
            "previous_delay": prev_delay,
            "is_rain": int(req.is_rain or False),
            "y_crowd_class_idx": prev_crowd_idx
        }])

        features_df = self.feat_builder.build_features(sample_df)

        try:
            preds_df = model.predict(features_df)
            pred_delay = float(preds_df["y_pred_delay"].iloc[0])
            q10 = float(preds_df["q10"].iloc[0]) if "q10" in preds_df.columns else pred_delay - 2.5
            q90 = float(preds_df["q90"].iloc[0]) if "q90" in preds_df.columns else pred_delay + 3.0

            # Delay label rule: <=2 On time, 2-10 Slight delay, >10 Significant delay
            if pred_delay <= 2.0:
                delay_label = "On time"
            elif pred_delay <= 10.0:
                delay_label = "Slight delay"
            else:
                delay_label = "Significant delay"

            # Empirical P(on-time <= 5 min) from normal approximation of interval
            sigma = max(0.5, (q90 - q10) / 2.56)
            from scipy.stats import norm
            p_on_time = float(norm.cdf(5.0, loc=pred_delay, scale=sigma))

            p_low = float(preds_df["proba_low"].iloc[0]) if "proba_low" in preds_df.columns else 0.2
            p_med = float(preds_df["proba_medium"].iloc[0]) if "proba_medium" in preds_df.columns else 0.5
            p_high = float(preds_df["proba_high"].iloc[0]) if "proba_high" in preds_df.columns else 0.3
            crowd_class = preds_df["pred_class"].iloc[0] if "pred_class" in preds_df.columns else "Medium"

            delay_obj = DelayPrediction(
                status="ok",
                minutes=round(pred_delay, 1),
                interval80=[round(q10, 1), round(q90, 1)],
                p_on_time=round(p_on_time, 2),
                label=delay_label
            )

            crowd_obj = CrowdingPrediction(
                status="ok",
                class_=crowd_class,
                probabilities={"Low": round(p_low, 2), "Medium": round(p_med, 2), "High": round(p_high, 2)}
            )

        except Exception as e:
            # Graceful degraded fallback
            delay_obj = DelayPrediction(status="degraded", minutes=prev_delay, interval80=[prev_delay-2, prev_delay+3], p_on_time=0.5, label="Slight delay")
            crowd_obj = CrowdingPrediction(status="degraded", class_="Medium", probabilities={"Low": 0.2, "Medium": 0.6, "High": 0.2})

        family = getattr(model, "family", "boosting")

        return JointPredictionResponse(
            route_id=req.route_id,
            stop_id=req.stop_id,
            model=ModelMetadata(id=model_id, family=family, data_source="synthetic"),
            delay=delay_obj,
            crowding=crowd_obj,
            freshness=FreshnessInfo(live_age_seconds=12, state="fresh"),
            inputs_derived=False,
            warnings=[],
            timestamp=now.isoformat(),
            status="ok"
        )

