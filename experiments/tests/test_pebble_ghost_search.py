"""Tests for relaxed ghost pebble search."""
from __future__ import annotations

from experiments.pebble_ghost_search import search_relaxed_ghost_model
from experiments.pebble_search import build_balanced_binary_tree, search_compute_root_only


def test_ghost_cap_zero_matches_black_model_on_small_tree():
    t = build_balanced_binary_tree(3)
    black_steps, _ = search_compute_root_only(t, pebble_cap=3)
    ghost_res = search_relaxed_ghost_model(
        t,
        solid_cap=3,
        ghost_cap=0,
    )
    assert ghost_res.min_steps_compute_root == black_steps


def test_relaxed_model_can_only_help_or_equal():
    t = build_balanced_binary_tree(3)
    r0 = search_relaxed_ghost_model(t, solid_cap=3, ghost_cap=0)
    r1 = search_relaxed_ghost_model(t, solid_cap=3, ghost_cap=1)
    if r0.min_steps_compute_root is not None and r1.min_steps_compute_root is not None:
        assert r1.min_steps_compute_root <= r0.min_steps_compute_root


def test_two_leaf_needs_help_at_solid_cap_two():
    t = build_balanced_binary_tree(2)
    r0 = search_relaxed_ghost_model(t, solid_cap=2, ghost_cap=0)
    r1 = search_relaxed_ghost_model(t, solid_cap=2, ghost_cap=1)
    assert r0.min_steps_compute_root is None
    # In relaxed model, one ghost can stand in for one child and make it feasible.
    assert r1.min_steps_compute_root is not None
