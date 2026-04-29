"""Tests for q_M tradeoff table helper."""
from __future__ import annotations

from experiments.qm_tradeoff import build_tradeoff_rows


def test_tradeoff_includes_exact_and_lossy():
    rows = build_tradeoff_rows(
        q_bits=51,
        u_bits=51,
        num_terms=23959,
        block_sizes=[2, 16, 256],
    )
    modes = {r.mode for r in rows}
    assert "exact_streaming" in modes
    assert "lossy_per_term" in modes
    assert "blockwise_lossy" in modes


def test_blockwise_guard_bits_monotone_with_block_size():
    rows = build_tradeoff_rows(
        q_bits=51,
        u_bits=51,
        num_terms=23959,
        block_sizes=[1, 2, 4, 8, 16, 32, 64, 128, 256],
    )
    block_rows = [r for r in rows if r.mode == "blockwise_lossy"]
    block_rows.sort(key=lambda r: r.block_size)

    # As block size grows, number of blocks decreases, so guard bits do not grow.
    guards = [r.guard_bits for r in block_rows]
    assert guards == sorted(guards, reverse=True)
