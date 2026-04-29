"""Pebble-storage budget helpers for Sprint 2 preparation."""
from __future__ import annotations

from dataclasses import dataclass


def node_storage_qubits(*, pebbles: int, coordinates: int, residue_bits: int) -> int:
    if pebbles < 0:
        raise ValueError("pebbles must be >= 0")
    if coordinates < 1:
        raise ValueError("coordinates must be >= 1")
    if residue_bits < 1:
        raise ValueError("residue_bits must be >= 1")
    return pebbles * coordinates * residue_bits


@dataclass(frozen=True)
class PebbleScenario:
    baseline_pebbles: int
    target_pebbles: int
    coordinates: int
    residue_bits: int
    baseline_total_qubits: int

    def baseline_storage(self) -> int:
        return node_storage_qubits(
            pebbles=self.baseline_pebbles,
            coordinates=self.coordinates,
            residue_bits=self.residue_bits,
        )

    def target_storage(self) -> int:
        return node_storage_qubits(
            pebbles=self.target_pebbles,
            coordinates=self.coordinates,
            residue_bits=self.residue_bits,
        )

    def saved_storage_qubits(self) -> int:
        return self.baseline_storage() - self.target_storage()

    def target_total_qubits(self) -> int:
        return self.baseline_total_qubits - self.saved_storage_qubits()


def p256_default_scenario(target_pebbles: int) -> PebbleScenario:
    # CFS P-256 Table 6 values:
    # baseline pebbles=6, coordinates=3, residue bits=19, total=1192.
    return PebbleScenario(
        baseline_pebbles=6,
        target_pebbles=target_pebbles,
        coordinates=3,
        residue_bits=19,
        baseline_total_qubits=1192,
    )


if __name__ == "__main__":
    print("P-256 pebble what-if (computation-phase total baseline 1192):")
    for p in (6, 5, 4):
        sc = p256_default_scenario(p)
        print(
            f"  pebbles={p}: storage={sc.target_storage()}, "
            f"saved={sc.saved_storage_qubits()}, total={sc.target_total_qubits()}"
        )
