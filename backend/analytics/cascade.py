"""
Stop-by-stop delay propagation cascade along journey ribbon (Section 12.2).
Computes widening uncertainty intervals downstream as errors accumulate.
"""

from typing import List, Dict, Any
import numpy as np

def compute_journey_ribbon(route_id: str, start_stop_id: str, initial_delay: float = 4.0) -> List[Dict[str, Any]]:
    # Mock sequence of 5 downstream stops along the route
    stop_names = [
        "Current Stop",
        "+1 Stop (DMS)",
        "+2 Stop (Saidapet)",
        "+3 Stop (Guindy)",
        "+4 Stop (Kathipara)",
        "+5 Stop (Airport)"
    ]

    ribbon = []
    accum_delay = initial_delay
    uncertainty_width = 2.0

    for i, name in enumerate(stop_names):
        if i > 0:
            # Downstream propagation: delay drifts upwards slightly with road friction
            accum_delay += float(np.random.uniform(0.3, 1.2))
            # Widening interval band downstream
            uncertainty_width += 1.1

        q10 = max(-5.0, accum_delay - uncertainty_width)
        q90 = accum_delay + uncertainty_width

        ribbon.append({
            "step": i,
            "stop_name": name,
            "predicted_delay_min": round(accum_delay, 1),
            "interval_80": [round(q10, 1), round(q90, 1)],
            "estimated_eta_min": round(i * 4.5 + accum_delay, 1),
            "crowding_forecast": "High" if accum_delay > 8 else ("Medium" if accum_delay > 3 else "Low")
        })

    return ribbon

