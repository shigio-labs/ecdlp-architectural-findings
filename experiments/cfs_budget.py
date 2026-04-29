"""CFS qubit-budget helpers for sprint-level what-if analysis.

This module turns Table 6/Table 8 numbers into explicit arithmetic so we can
track qubit deltas consistently while exploring optimization levers.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CFSComputationBudget:
    """Computation-phase budget for one curve instance.

    Fields match Table 6-style decomposition:
    - input_qubits
    - output_field_qubits (the curve field element width, e.g. 256 for P-256)
    - qm_register_qubits (the q_M-related part of output register)
    - ancilla_point_addition
    - node_storage_qubits (pebbles * 3 coordinates * residue bit-width)
    """

    curve: str
    input_qubits: int
    output_field_qubits: int
    qm_register_qubits: int
    ancilla_point_addition: int
    node_storage_qubits: int

    @property
    def output_qubits(self) -> int:
        return self.output_field_qubits + self.qm_register_qubits

    @property
    def total_computation_qubits(self) -> int:
        return (
            self.input_qubits
            + self.output_qubits
            + self.ancilla_point_addition
            + self.node_storage_qubits
        )

    @property
    def table8_headline_qubits(self) -> int:
        # Table 8 headline adds one Legendre-symbol output qubit.
        return self.total_computation_qubits + 1

    def with_qm_register(self, qm_register_qubits: int) -> "CFSComputationBudget":
        if qm_register_qubits < 1:
            raise ValueError("qm_register_qubits must be >= 1")
        return CFSComputationBudget(
            curve=self.curve,
            input_qubits=self.input_qubits,
            output_field_qubits=self.output_field_qubits,
            qm_register_qubits=qm_register_qubits,
            ancilla_point_addition=self.ancilla_point_addition,
            node_storage_qubits=self.node_storage_qubits,
        )

    def with_node_storage(self, node_storage_qubits: int) -> "CFSComputationBudget":
        if node_storage_qubits < 0:
            raise ValueError("node_storage_qubits must be >= 0")
        return CFSComputationBudget(
            curve=self.curve,
            input_qubits=self.input_qubits,
            output_field_qubits=self.output_field_qubits,
            qm_register_qubits=self.qm_register_qubits,
            ancilla_point_addition=self.ancilla_point_addition,
            node_storage_qubits=node_storage_qubits,
        )


# Table 6 values from the local CFS 2026/280 full-version PDF.
# P-256 row:
# input=297, output=256+102=358, ancilla=195, node storage=342, total=1192.
P256_BASELINE = CFSComputationBudget(
    curve="P-256",
    input_qubits=297,
    output_field_qubits=256,
    qm_register_qubits=102,
    ancilla_point_addition=195,
    node_storage_qubits=342,
)


def summarize_qm_reduction(
    baseline: CFSComputationBudget,
    target_qm_register_qubits: int,
) -> dict[str, int]:
    """Return before/after totals and savings for a q_M width scenario."""
    after = baseline.with_qm_register(target_qm_register_qubits)
    return {
        "before_total_computation": baseline.total_computation_qubits,
        "after_total_computation": after.total_computation_qubits,
        "saved_computation_qubits": baseline.total_computation_qubits - after.total_computation_qubits,
        "before_table8_headline": baseline.table8_headline_qubits,
        "after_table8_headline": after.table8_headline_qubits,
        "saved_headline_qubits": baseline.table8_headline_qubits - after.table8_headline_qubits,
    }


def summarize_joint_reduction(
    baseline: CFSComputationBudget,
    *,
    target_qm_register_qubits: int,
    target_node_storage_qubits: int,
) -> dict[str, int]:
    """Return savings when both q_M width and node-storage width are changed."""
    after = baseline.with_qm_register(target_qm_register_qubits).with_node_storage(
        target_node_storage_qubits
    )
    return {
        "before_total_computation": baseline.total_computation_qubits,
        "after_total_computation": after.total_computation_qubits,
        "saved_computation_qubits": baseline.total_computation_qubits - after.total_computation_qubits,
        "before_table8_headline": baseline.table8_headline_qubits,
        "after_table8_headline": after.table8_headline_qubits,
        "saved_headline_qubits": baseline.table8_headline_qubits - after.table8_headline_qubits,
    }


if __name__ == "__main__":
    # Minimal CLI-style printout for quick sprint logs.
    b = P256_BASELINE
    print(f"{b.curve} baseline: computation={b.total_computation_qubits}, headline={b.table8_headline_qubits}")
    for target in (90, 80, 70, 60, 51):
        s = summarize_qm_reduction(b, target)
        print(
            f"  qM={target:>3}: "
            f"save={s['saved_computation_qubits']:>3} (comp), "
            f"headline={s['after_table8_headline']}"
        )
