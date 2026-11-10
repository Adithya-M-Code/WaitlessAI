"""
Best-Bus Recommender (Section 11.4 & Section 12.7).
Ranks candidate buses along a route by Speed, Comfort, or Balanced objective.
"""

from typing import List, Dict, Any, Literal

def recommend_best_bus(
    route_id: str,
    stop_id: str,
    mode: Literal["speed", "comfort", "balanced"] = "balanced"
) -> List[Dict[str, Any]]:
    # Next 3 approaching buses
    candidates = [
        {
            "bus_id": "TN-01-N-1288",
            "eta_minutes": 4.5,
            "predicted_delay": 2.0,
            "crowding_class": "High",
            "crowd_score": 0.85,
            "reliability_score": 92
        },
        {
            "bus_id": "TN-01-N-1342",
            "eta_minutes": 11.0,
            "predicted_delay": 5.2,
            "crowding_class": "Low",
            "crowd_score": 0.15,
            "reliability_score": 88
        },
        {
            "bus_id": "TN-01-N-1490",
            "eta_minutes": 19.0,
            "predicted_delay": 1.5,
            "crowding_class": "Medium",
            "crowd_score": 0.45,
            "reliability_score": 95
        }
    ]

    for c in candidates:
        if mode == "speed":
            score = 100 - (c["eta_minutes"] * 3.0)
            reason_en = f"Earliest arrival in {c['eta_minutes']} min."
            reason_ta = f"{c['eta_minutes']} நிமிடங்களில் முன்கூட்டியே வருகை."
        elif mode == "comfort":
            score = 100 - (c["crowd_score"] * 70.0) - (c["eta_minutes"] * 1.0)
            reason_en = f"High comfort ({c['crowding_class']} crowd), worth waiting."
            reason_ta = f"அதிக வசதி ({c['crowding_class']} கூட்டம்), காத்திருக்கலாம்."
        else: # Balanced
            score = 100 - (c["eta_minutes"] * 2.0) - (c["crowd_score"] * 30.0) + (c["reliability_score"] * 0.2)
            reason_en = f"Optimal trade-off between wait ({c['eta_minutes']}m) and crowd ({c['crowding_class']})."
            reason_ta = f"காத்திருப்பு மற்றும் கூட்டத்திற்கான சமநிலையான தேர்வு."

        c["recommendation_score"] = round(score, 1)
        c["reason"] = {"en": reason_en, "ta": reason_ta}

    candidates.sort(key=lambda x: x["recommendation_score"], reverse=True)
    return candidates

