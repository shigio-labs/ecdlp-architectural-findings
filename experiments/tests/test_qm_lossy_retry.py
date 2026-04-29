"""Tests for lossy+retry envelope model."""
from __future__ import annotations

from experiments.qm_lossy_retry import estimate_lossy_retry_stats


def test_full_block_is_exact():
    st = estimate_lossy_retry_stats(
        n_trials=200,
        n_terms=300,
        u_bits=20,
        block_size=300,
        p_min=1 << 8,
        p_max=(1 << 10) - 1,
        seed=12345,
    )
    assert st.q_mismatch_count == 0
    assert st.mismatch_rate == 0.0
    assert st.mean_error == 0.0
    assert st.max_error == 0


def test_small_block_has_nonzero_mismatch_on_synthetic_distribution():
    st = estimate_lossy_retry_stats(
        n_trials=500,
        n_terms=300,
        u_bits=20,
        block_size=8,
        p_min=1 << 8,
        p_max=(1 << 10) - 1,
        seed=54321,
    )
    assert st.q_mismatch_count > 0
    assert st.mismatch_rate > 0.0
    assert st.max_error >= 1


def test_expected_runs_formula():
    st = estimate_lossy_retry_stats(
        n_trials=300,
        n_terms=200,
        u_bits=18,
        block_size=16,
        p_min=1 << 8,
        p_max=(1 << 10) - 1,
        seed=0xA55A,
    )
    # For one call, expected runs = 1/(1-mismatch_rate)
    p_ok = 1.0 - st.mismatch_rate
    if p_ok > 0.0:
        assert abs(st.expected_runs_for_calls(1) - (1.0 / p_ok)) < 1e-12
        assert abs(st.expected_overhead_for_calls(1) - ((1.0 / p_ok) - 1.0)) < 1e-12
