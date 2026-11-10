"""
Champion selection module.
Consumes scorecard.json and leaderboard.json to elect the official Champion
and designate active Challengers. Writes models/registry.json.
"""

import json
from pathlib import Path
from ml.arena.scorecard import compute_scorecard

def run_selection():
    card = compute_scorecard()
    top_model = card["top_model"]
    rankings = [r["model_id"] for r in card["rankings"]]

    champion = top_model
    challengers = [m for m in rankings if m != champion and not m.endswith("_baseline")]

    registry = {
        "delay": {
            "champion": champion,
            "challengers": challengers
        },
        "crowding": {
            "champion": champion,
            "challengers": challengers
        },
        "data_source": "synthetic",
        "approved_by_human": False
    }

    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)
    registry_path = models_dir / "registry.json"

    with open(registry_path, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2)

    print(f"Champion selected: {champion} (Scorecard Rank 1)")
    print(f"Registry written to {registry_path}")
    return registry

if __name__ == "__main__":
    run_selection()

