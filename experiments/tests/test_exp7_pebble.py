"""Tests for exp7 pebble data collection."""
from __future__ import annotations

from experiments.exp7_pebble.run import collect_data


def test_collect_data_small_tree_fast():
    data = collect_data(
        num_leaves=3,
        black_caps=(2, 3, 4),
        solid_cap=3,
        ghost_caps=(0, 1),
        max_visited_compute=100_000,
        max_visited_full=100_000,
    )
    assert data["experiment"] == "exp7_pebble"
    assert data["tree"]["num_leaves"] == 3
    assert "k=2" in data["black_model"]
    assert "k=3" in data["black_model"]
    assert "g=0" in data["relaxed_ghost_model_k5"]
    assert "g=1" in data["relaxed_ghost_model_k5"]
