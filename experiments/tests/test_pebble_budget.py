"""Tests for pebble-budget helpers."""
from __future__ import annotations

from experiments.pebble_budget import node_storage_qubits, p256_default_scenario


def test_node_storage_formula():
    assert node_storage_qubits(pebbles=6, coordinates=3, residue_bits=19) == 342
    assert node_storage_qubits(pebbles=5, coordinates=3, residue_bits=19) == 285
    assert node_storage_qubits(pebbles=4, coordinates=3, residue_bits=19) == 228


def test_p256_default_savings():
    sc5 = p256_default_scenario(5)
    assert sc5.saved_storage_qubits() == 57
    assert sc5.target_total_qubits() == 1135

    sc4 = p256_default_scenario(4)
    assert sc4.saved_storage_qubits() == 114
    assert sc4.target_total_qubits() == 1078
