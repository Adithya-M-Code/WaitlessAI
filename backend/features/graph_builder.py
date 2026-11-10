"""
Stop Graph builder for M5 Spatio-Temporal GNN.
Extracts route-order connectivity and transfer edges between stops within 200m.
"""

from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd
from scipy.spatial.distance import cdist

class GraphBuilder:
    def __init__(self, transfer_distance_m: float = 200.0):
        self.transfer_distance_m = transfer_distance_m

    def build_graph(
        self,
        stops_df: pd.DataFrame,
        stop_times_df: pd.DataFrame,
        output_dir: str = "data/datasets/v1"
    ):
        """
        Creates graph nodes and directed adjacency edges with edge attributes:
        1. Route-order sequential edges (buses moving from stop A to stop B)
        2. Transfer edges between distinct stops situated within 200m of each other
        """
        unique_stops = stops_df.drop_duplicates(subset=["stop_id"]).sort_values("stop_id").reset_index(drop=True)
        stop_to_idx = {sid: idx for idx, sid in enumerate(unique_stops["stop_id"])}
        n_nodes = len(unique_stops)

        # Node coordinates (approximate meter projection in Chennai lat ~13.0)
        coords = unique_stops[["stop_lat", "stop_lon"]].values
        # 1 deg lat ~ 111,000m, 1 deg lon ~ 108,000m
        coords_m = coords * np.array([111000.0, 108000.0])

        edge_list: List[Tuple[int, int, float, float]] = [] # src, dst, distance_m, mean_travel_time_m

        # 1. Route-order sequential edges
        st_sorted = stop_times_df.sort_values(by=["trip_id", "stop_sequence"])
        for _, trip_group in st_sorted.groupby("trip_id"):
            stop_ids = trip_group["stop_id"].values
            for i in range(len(stop_ids) - 1):
                u = stop_to_idx.get(stop_ids[i])
                v = stop_to_idx.get(stop_ids[i + 1])
                if u is not None and v is not None and u != v:
                    dist = float(np.linalg.norm(coords_m[u] - coords_m[v]))
                    edge_list.append((u, v, dist, 5.0)) # ~5 min travel time

        # 2. Transfer edges within 200m
        pairwise_dist = cdist(coords_m, coords_m)
        transfer_indices = np.argwhere((pairwise_dist > 0) & (pairwise_dist <= self.transfer_distance_m))
        for u, v in transfer_indices:
            edge_list.append((int(u), int(v), float(pairwise_dist[u, v]), 2.0))

        # Deduplicate edges
        edge_dict = {}
        for u, v, dist, t_time in edge_list:
            key = (u, v)
            if key not in edge_dict:
                edge_dict[key] = (dist, t_time)

        edges = np.array(list(edge_dict.keys()), dtype=np.int64)
        edge_attrs = np.array(list(edge_dict.values()), dtype=np.float32)

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        graph_file = out_path / "graph.npz"
        np.savez_compressed(
            graph_file,
            nodes=unique_stops["stop_id"].values,
            edges=edges,
            edge_attrs=edge_attrs,
            num_nodes=n_nodes
        )
        print(f"Graph built with {n_nodes} nodes and {len(edges)} edges saved to {graph_file}")

