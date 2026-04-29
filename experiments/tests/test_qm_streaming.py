"""Tests for q_M streaming arithmetic models."""
from __future__ import annotations

from random import Random

from experiments.qm_streaming import (
    QMWidthScenario,
    bits_needed_nonnegative,
    blockwise_error_upper_bound,
    blockwise_quotient,
    exact_streaming_quotient,
    guard_bits_for_error_bound,
    lossy_error_upper_bound,
    lossy_per_term_quotient,
    sample_term_sequence,
)


def test_exact_streaming_matches_one_shot_division():
    rng = Random(0xC0FFEE)
    for _ in range(200):
        u = rng.randrange(6, 17)
        n = rng.randrange(1, 200)
        terms = [rng.randrange(0, 1 << 24) for _ in range(n)]
        q_exact = exact_streaming_quotient(terms, u)
        q_one_shot = sum(terms) >> u
        assert q_exact == q_one_shot


def test_lossy_is_downward_and_within_bound():
    rng = Random(0xBAD5EED)
    for _ in range(200):
        u = rng.randrange(6, 17)
        n = rng.randrange(1, 200)
        terms = [rng.randrange(0, 1 << 24) for _ in range(n)]
        q_exact = sum(terms) >> u
        q_lossy = lossy_per_term_quotient(terms, u)
        err = q_exact - q_lossy
        assert err >= 0
        assert err <= lossy_error_upper_bound(n)


def test_blockwise_error_bound_holds():
    rng = Random(0xA11CE)
    for _ in range(200):
        u = rng.randrange(6, 17)
        n = rng.randrange(1, 300)
        b = rng.randrange(1, 50)
        terms = [rng.randrange(0, 1 << 24) for _ in range(n)]
        q_exact = sum(terms) >> u
        q_blk = blockwise_quotient(terms, u, b)
        err = q_exact - q_blk
        assert err >= 0
        assert err <= blockwise_error_upper_bound(n, b)


def test_width_scenario_p256_like_numbers():
    # P-256-like parameters from current note: q_bits=51, u_bits=51,
    # number of terms around 2^14.55 (rounded up).
    n_terms = 23959
    s = QMWidthScenario(q_bits=51, u_bits=51, num_terms=n_terms)

    # Exact streaming keeps q + remainder -> same 102-bit state width.
    assert s.exact_streaming_state_bits() == 102

    # Lossy truncation removes remainder but needs guard bits to bound error.
    # Guard bits ~= ceil(log2(n_terms)).
    lossy_bits = s.lossy_state_bits_with_guard()
    assert lossy_bits == 66


def test_synthetic_cfs_terms_respect_error_bounds():
    rng = Random(0x12345678)
    terms = sample_term_sequence(
        n_terms=500,
        p_min=1 << 16,
        p_max=(1 << 19) - 1,
        u_bits=51,
        rng=rng,
    )
    q_exact = exact_streaming_quotient(terms, 51)
    q_lossy = lossy_per_term_quotient(terms, 51)
    err = q_exact - q_lossy
    assert err >= 0
    assert err <= lossy_error_upper_bound(len(terms))


def test_guard_bits_and_bit_helpers():
    assert bits_needed_nonnegative(0) == 1
    assert bits_needed_nonnegative(1) == 1
    assert bits_needed_nonnegative(2) == 2
    assert guard_bits_for_error_bound(0) == 0
    assert guard_bits_for_error_bound(1) == 1
    assert guard_bits_for_error_bound(2) == 2
