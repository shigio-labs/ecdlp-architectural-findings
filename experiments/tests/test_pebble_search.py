"""Tests for pebble state-space search."""
from __future__ import annotations

from experiments.pebble_search import build_balanced_binary_tree, search_tree


def test_tree_shape_for_19_leaves():
    t = build_balanced_binary_tree(19)
    assert t.num_leaves == 19
    assert t.num_nodes == 37  # 19 leaves + 18 internal nodes
    assert t.height() == 5


def test_single_leaf_tree():
    t = build_balanced_binary_tree(1)
    r = search_tree(t, pebble_cap=1)
    # Need one add to pebble root and one remove to return to empty.
    assert r.min_steps_compute_root == 1
    assert r.min_steps_compute_uncompute == 2


def test_two_leaf_root_requires_three_pebbles():
    t = build_balanced_binary_tree(2)
    r2 = search_tree(t, pebble_cap=2)
    r3 = search_tree(t, pebble_cap=3)
    assert r2.min_steps_compute_root is None
    assert r2.min_steps_compute_uncompute is None
    assert r3.min_steps_compute_root == 3
    assert r3.min_steps_compute_uncompute == 6


def test_more_pebbles_do_not_increase_min_steps():
    t = build_balanced_binary_tree(3)
    r3 = search_tree(t, pebble_cap=3)
    r4 = search_tree(t, pebble_cap=4)
    r5 = search_tree(t, pebble_cap=5)
    assert r3.min_steps_compute_root is not None
    assert r4.min_steps_compute_root is not None
    assert r5.min_steps_compute_root is not None
    assert r4.min_steps_compute_root <= r3.min_steps_compute_root
    assert r5.min_steps_compute_root <= r4.min_steps_compute_root
