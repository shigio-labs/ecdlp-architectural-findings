"""Tests for CFS sprint-budget accounting helpers."""
from __future__ import annotations

from experiments.cfs_budget import (
    P256_BASELINE,
    summarize_joint_reduction,
    summarize_qm_reduction,
)


def test_p256_baseline_matches_table6_table8():
    b = P256_BASELINE
    assert b.output_qubits == 358
    assert b.total_computation_qubits == 1192
    assert b.table8_headline_qubits == 1193


def test_qm_reduction_to_51_saves_51_qubits():
    s = summarize_qm_reduction(P256_BASELINE, 51)
    assert s["before_total_computation"] == 1192
    assert s["after_total_computation"] == 1141
    assert s["saved_computation_qubits"] == 51
    assert s["before_table8_headline"] == 1193
    assert s["after_table8_headline"] == 1142
    assert s["saved_headline_qubits"] == 51


def test_joint_reduction_example_qm_plus_one_pebble():
    # Example scenario:
    # - q_M width 102 -> 70 saves 32.
    # - node storage 342 -> 285 saves 57 (one pebble for 3x19 bits).
    s = summarize_joint_reduction(
        P256_BASELINE,
        target_qm_register_qubits=70,
        target_node_storage_qubits=285,
    )
    assert s["before_total_computation"] == 1192
    assert s["after_total_computation"] == 1103
    assert s["saved_computation_qubits"] == 89
    assert s["before_table8_headline"] == 1193
    assert s["after_table8_headline"] == 1104
    assert s["saved_headline_qubits"] == 89
