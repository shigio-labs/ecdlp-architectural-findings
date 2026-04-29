"""Run Sprint 2 pebbling feasibility experiment and write data.json."""
from __future__ import annotations

import json
import time
from pathlib import Path

from experiments.pebble_ghost_search import search_relaxed_ghost_model
from experiments.pebble_search import build_balanced_binary_tree, search_tree


HERE = Path(__file__).parent
OUT = HERE / "data.json"


def collect_data(
    *,
    num_leaves: int = 19,
    black_caps: tuple[int, ...] = (4, 5, 6, 7),
    solid_cap: int = 5,
    ghost_caps: tuple[int, ...] = (0, 1, 2, 3, 4),
    max_visited_compute: int = 3_000_000,
    max_visited_full: int = 2_000_000,
) -> dict:
    t0 = time.time()
    tree = build_balanced_binary_tree(num_leaves)

    black = {}
    for k in black_caps:
        r = search_tree(tree, k)
        black[f"k={k}"] = {
            "possible": r.possible,
            "min_steps_compute_root": r.min_steps_compute_root,
            "min_steps_compute_uncompute": r.min_steps_compute_uncompute,
            "visited_states_compute": r.visited_states_compute,
            "visited_states_full": r.visited_states_full,
        }

    relaxed = {}
    for g in ghost_caps:
        r = search_relaxed_ghost_model(
            tree,
            solid_cap=solid_cap,
            ghost_cap=g,
            max_visited_compute=max_visited_compute,
            max_visited_full=max_visited_full,
        )
        relaxed[f"g={g}"] = {
            "possible": r.possible,
            "min_steps_compute_root": r.min_steps_compute_root,
            "min_steps_compute_uncompute": r.min_steps_compute_uncompute,
            "visited_compute": r.visited_compute,
            "visited_full": r.visited_full,
            "cutoff_hit_compute": r.cutoff_hit_compute,
            "cutoff_hit_full": r.cutoff_hit_full,
        }

    return {
        "experiment": "exp7_pebble",
        "tree": {
            "num_leaves": tree.num_leaves,
            "num_nodes": tree.num_nodes,
            "height": tree.height(),
            "root": tree.root,
        },
        "black_model": black,
        "relaxed_ghost_model_k5": relaxed,
        "budgets": {
            "max_visited_compute": max_visited_compute,
            "max_visited_full": max_visited_full,
        },
        "elapsed_seconds": round(time.time() - t0, 3),
    }


def main() -> None:
    data = collect_data()
    OUT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"Elapsed: {data['elapsed_seconds']}s")


if __name__ == "__main__":
    main()
