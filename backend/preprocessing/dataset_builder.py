"""
Dataset builder pipeline orchestrator for Waitless AI.
Coordinates GTFS generation, synthetic data simulation, validation, cleaning,
feature construction, sequence tensor creation, stop graph assembly, and time splits.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
import pandas as pd
import numpy as np

from backend.collectors.gtfs_loader import GTFSLoader
from backend.collectors.synthetic_generator import SyntheticDataGenerator
from backend.preprocessing.validator import DataValidator
from backend.preprocessing.cleaner import clean_and_label
from backend.features.feature_builder import FeatureBuilder
from backend.features.sequence_builder import SequenceBuilder
from backend.features.graph_builder import GraphBuilder
from backend.features.folds import TimeSplitter

def build_complete_dataset(version: str = "v1", days: int = 90, num_routes: int = 25):
    """
    Executes the end-to-end data preparation workflow and writes datasets to data/datasets/{version}/.
    """
    dataset_dir = Path(f"data/datasets/{version}")
    dataset_dir.mkdir(parents=True, exist_ok=True)

    print(f"--- [Step 1/7] Initializing GTFS Network ---")
    gtfs = GTFSLoader()
    routes_df, stops_df, trips_df, stop_times_df = gtfs.load_or_generate()

    print(f"--- [Step 2/7] Generating Synthetic Bus Trajectories ({days} days) ---")
    gen = SyntheticDataGenerator()
    raw_df = gen.generate(days=days, output_dir=f"data/raw/synthetic")

    print(f"--- [Step 3/7] Validating Observations with Audit Trail ---")
    validator = DataValidator()
    validated_df, rejection_counts = validator.validate(raw_df)

    print(f"--- [Step 4/7] Cleaning & Labeling Targets (Delay, Crowding, Downstream Horizons) ---")
    cleaned_df = clean_and_label(validated_df)

    print(f"--- [Step 5/7] Building Shared Features ---")
    feat_builder = FeatureBuilder()
    features_df = feat_builder.build_features(cleaned_df)
    feat_builder.export_schema()

    # Sort chronologically (Rule R4)
    features_df = features_df.sort_values(by="observed_at_utc").reset_index(drop=True)

    print(f"--- [Step 6/7] Building Splits and Tensors ---")
    # Time splits
    splits_info = TimeSplitter.create_splits(features_df, output_dir=str(dataset_dir))
    
    # Mark split labels on tabular parquet
    train_idx = splits_info["main"]["train"]["indices"]
    val_idx = splits_info["main"]["val"]["indices"]
    test_idx = splits_info["main"]["test"]["indices"]

    features_df["split"] = "train"
    features_df.iloc[val_idx[0]:val_idx[1], features_df.columns.get_loc("split")] = "val"
    features_df.iloc[test_idx[0]:test_idx[1], features_df.columns.get_loc("split")] = "test"

    # Save tabular datasets
    features_df.to_parquet(dataset_dir / "tabular_dataset.parquet", index=False)
    # Also separate convenience files
    features_df.to_parquet(dataset_dir / "tabular_delay.parquet", index=False)
    features_df.to_parquet(dataset_dir / "tabular_crowding.parquet", index=False)

    # Build sequence tensors for train, val, test
    seq_builder = SequenceBuilder(k_steps=8)
    for s_name, s_info in [("train", train_idx), ("val", val_idx), ("test", test_idx)]:
        sub_df = features_df.iloc[s_info[0]:s_info[1]]
        seqs, masks = seq_builder.build_sequences(sub_df, feat_builder.feature_columns)
        seq_builder.save_split_sequences(seqs, masks, s_name, output_dir=str(dataset_dir))

    # Build Stop Graph
    graph_builder = GraphBuilder(transfer_distance_m=200.0)
    graph_builder.build_graph(stops_df, stop_times_df, output_dir=str(dataset_dir))

    print(f"--- [Step 7/7] Generating Manifest ---")
    crowd_counts = features_df["y_crowd_class"].value_counts(dropna=False).to_dict()
    manifest = {
        "dataset_version": version,
        "source": "synthetic",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total_observations": len(features_df),
        "train_observations": splits_info["main"]["train"]["count"],
        "val_observations": splits_info["main"]["val"]["count"],
        "test_observations": splits_info["main"]["test"]["count"],
        "num_routes": int(features_df["route_id"].nunique()),
        "num_stops": int(features_df["stop_id"].nunique()),
        "time_range": {
            "start": str(features_df["observed_at_utc"].min()),
            "end": str(features_df["observed_at_utc"].max())
        },
        "crowding_class_balance": {str(k): int(v) for k, v in crowd_counts.items()},
        "rejected_records_audit": rejection_counts,
        "feature_count": len(feat_builder.feature_columns)
    }

    with open(dataset_dir / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print(f"Complete dataset {version} successfully built in {dataset_dir}!")
    return manifest

if __name__ == "__main__":
    build_complete_dataset()

