"""Tradeoff table for q_M streaming variants (Sprint 1 helper)."""
from __future__ import annotations

from dataclasses import dataclass

from .qm_streaming import (
    QMWidthScenario,
    blockwise_error_upper_bound,
    guard_bits_for_error_bound,
)


@dataclass(frozen=True)
class TradeoffRow:
    mode: str
    block_size: int
    error_bound: int
    guard_bits: int
    state_bits: int


def build_tradeoff_rows(
    *,
    q_bits: int,
    u_bits: int,
    num_terms: int,
    block_sizes: list[int],
) -> list[TradeoffRow]:
    s = QMWidthScenario(q_bits=q_bits, u_bits=u_bits, num_terms=num_terms)
    rows: list[TradeoffRow] = [
        TradeoffRow(
            mode="exact_streaming",
            block_size=num_terms,
            error_bound=0,
            guard_bits=0,
            state_bits=s.exact_streaming_state_bits(),
        ),
        TradeoffRow(
            mode="lossy_per_term",
            block_size=1,
            error_bound=num_terms - 1 if num_terms else 0,
            guard_bits=guard_bits_for_error_bound(num_terms - 1 if num_terms else 0),
            state_bits=s.lossy_state_bits_with_guard(),
        ),
    ]

    for b in sorted(set(block_sizes)):
        if b < 1:
            continue
        eb = blockwise_error_upper_bound(num_terms, b)
        gb = guard_bits_for_error_bound(eb)
        rows.append(
            TradeoffRow(
                mode="blockwise_lossy",
                block_size=b,
                error_bound=eb,
                guard_bits=gb,
                state_bits=q_bits + gb,
            )
        )
    return rows


def format_tradeoff_table(rows: list[TradeoffRow]) -> str:
    lines = []
    lines.append(
        f"{'mode':<18} {'block':>8} {'err_bound':>10} {'guard_bits':>11} {'state_bits':>11}"
    )
    lines.append("-" * 66)
    for r in rows:
        lines.append(
            f"{r.mode:<18} {r.block_size:>8} {r.error_bound:>10} {r.guard_bits:>11} {r.state_bits:>11}"
        )
    return "\n".join(lines)


if __name__ == "__main__":
    rows = build_tradeoff_rows(
        q_bits=51,
        u_bits=51,
        num_terms=23959,
        block_sizes=[2, 4, 8, 16, 32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 23959],
    )
    print(format_tradeoff_table(rows))
