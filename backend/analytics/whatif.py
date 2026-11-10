"""
What-If Simulator and Past Day Replay Engine (Section 12.9).
"""

from typing import Dict, Any

def simulate_whatif(
    base_delay: float,
    hour: int,
    is_rain: bool,
    is_peak: bool,
    upstream_delay: float
) -> Dict[str, Any]:
    new_delay = base_delay
    if is_peak:
        new_delay += 3.5
    if is_rain:
        new_delay += 4.8
    new_delay += upstream_delay * 0.7

    return {
        "original_delay_min": round(base_delay, 1),
        "simulated_delay_min": round(new_delay, 1),
        "delta_min": round(new_delay - base_delay, 1),
        "simulated_crowd": "High" if new_delay > 8.0 else ("Medium" if new_delay > 4.0 else "Low")
    }

