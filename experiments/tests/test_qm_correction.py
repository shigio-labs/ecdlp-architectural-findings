"""Tests for blockwise correction models."""
from __future__ import annotations

from random import Random

from experiments.qm_correction import (
    CorrectionWidthScenario,
    bits_for_block_remainder_sum,
    exact_blockwise_with_remainder_stream,
    num_blocks,
)


def test_exact_blockwise_with_remainder_stream_matches_one_shot():
    rng = Random(0xFEE1DEAD)
    for _ in range(200):
        u = rng.randrange(6, 17)
        n = rng.randrange(1, 300)
        b = rng.randrange(1, 80)
        terms = [rng.randrange(0, 1 << 24) for _ in range(n)]
        q = exact_blockwise_with_remainder_stream(terms, u, b)
        assert q == (sum(terms) >> u)


def test_num_blocks():
    assert num_blocks(0, 7) == 0
    assert num_blocks(1, 7) == 1
    assert num_blocks(7, 7) == 1
    assert num_blocks(8, 7) == 2


def test_remainder_sum_bits_p256_like():
    # P-256-like: u=51, n_terms=23959, block=256 => ~94 blocks.
    bits = bits_for_block_remainder_sum(23959, 256, 51)
    # Around u + ceil(log2(94)) = 51 + 7 = 58.
    assert bits == 58


def test_correction_width_scenario_shows_no_exact_width_gain():
    s = CorrectionWidthScenario(
        q_bits=51,
        u_bits=51,
        num_terms=23959,
        block_size=256,
    )
    assert s.baseline_bits() == 102
    # Exact streaming correction keeps baseline width.
    assert s.exact_blockwise_stream_bits() == 102

    # Explicit full-remainder-sum method is wider than baseline.
    assert s.full_remainder_sum_bits() == 109
    assert s.correction_overhead_bits_vs_baseline() == 7

    # Counter bits alone are small but not sufficient for exact reconstruction.
    assert s.correction_counter_bits() == 7
