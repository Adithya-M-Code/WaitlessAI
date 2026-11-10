"""
Explain-Why endpoint (SHAP drivers and EN/Tamil narrative).
"""

from typing import Literal
from fastapi import APIRouter
from backend.explain.shap_service import get_top_shap_drivers
from backend.explain.narrative import generate_explanation_narrative

router = APIRouter(tags=["Explainability"])

@router.get("/explain")
def explain_prediction(
    route_id: str = "17D",
    stop_id: str = "Central",
    lang: Literal["en", "ta"] = "en"
):
    drivers = get_top_shap_drivers(route_id, stop_id)
    narrative = generate_explanation_narrative(route_id, stop_id, predicted_delay=5.2, lang=lang)
    return {
        "route_id": route_id,
        "stop_id": stop_id,
        "lang": lang,
        "top_drivers": drivers,
        "narrative": narrative["narrative"]
    }

