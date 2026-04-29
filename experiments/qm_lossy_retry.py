"""Lossy+retry envelope for q_M blockwise truncation.

This is a Sprint 1 exploration tool: it estimates, on synthetic term
distributions, how often lossy blockwise quotient disagrees with exact.

Important: this is not a full CFS distribution model. Use results as a
screening signal, not as final cryptographic evidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from random import Random

from .qm_streaming import blockwise_quotient, exact_streaming_quotient, sample_term_sequence


@dataclass(frozen=True)
class LossyRetryStats:
    n_trials: int
    block_size: int
    q_mismatch_count: int
    mismatch_rate: float
    mean_error: float
    max_error: int

    def success_prob_per_call(self) -> float:
        return 1.0 - self.mismatch_rate

    def expected_runs_for_calls(self, num_calls: int) -> float:
        """Expected reruns with perfect mismatch detection and restart."""
        if num_calls < 1:
            raise ValueError("num_calls must be >= 1")
        p = self.success_prob_per_call() ** num_calls
        if p <= 0.0:
            return float("inf")
        return 1.0 / p

    def expected_overhead_for_calls(self, num_calls: int) -> float:
        er = self.expected_runs_for_calls(num_calls)
        if er == float("inf"):
            return er
        return er - 1.0


def estimate_lossy_retry_stats(
    *,
    n_trials: int,
    n_terms: int,
    u_bits: int,
    block_size: int,
    p_min: int,
    p_max: int,
    seed: int,
) -> LossyRetryStats:
    if n_trials < 1:
        raise ValueError("n_trials must be >= 1")
    if n_terms < 1:
        raise ValueError("n_terms must be >= 1")
    if u_bits < 1:
        raise ValueError("u_bits must be >= 1")
    if block_size < 1:
        raise ValueError("block_size must be >= 1")
    if p_min < 2 or p_max < p_min:
        raise ValueError("invalid prime bounds")

    rng = Random(seed)
    mismatches = 0
    err_sum = 0
    err_max = 0

    for _ in range(n_trials):
        terms = sample_term_sequence(
            n_terms=n_terms,
            p_min=p_min,
            p_max=p_max,
            u_bits=u_bits,
            rng=rng,
        )
        q_exact = exact_streaming_quotient(terms, u_bits)
        q_lossy = blockwise_quotient(terms, u_bits, block_size)
        err = q_exact - q_lossy
        if err < 0:
            raise AssertionError("lossy quotient unexpectedly exceeded exact")
        if err != 0:
            mismatches += 1
        err_sum += err
        if err > err_max:
            err_max = err

    return LossyRetryStats(
        n_trials=n_trials,
        block_size=block_size,
        q_mismatch_count=mismatches,
        mismatch_rate=mismatches / n_trials,
        mean_error=err_sum / n_trials,
        max_error=err_max,
    )


def print_envelope_for_block_sizes(
    *,
    block_sizes: list[int],
    n_trials: int,
    n_terms: int,
    u_bits: int,
    p_min: int,
    p_max: int,
    seed: int,
    num_calls: int,
) -> None:
    print(
        f"{'block':>7} {'mismatch':>10} {'mean_err':>10} "
        f"{'max_err':>8} {'exp_runs':>10} {'overhead':>10}"
    )
    print("-" * 67)
    for b in block_sizes:
        st = estimate_lossy_retry_stats(
            n_trials=n_trials,
            n_terms=n_terms,
            u_bits=u_bits,
            block_size=b,
            p_min=p_min,
            p_max=p_max,
            seed=seed ^ b,
        )
        exp_runs = st.expected_runs_for_calls(num_calls)
        overhead = st.expected_overhead_for_calls(num_calls)
        print(
            f"{b:>7} {st.mismatch_rate:>10.6f} {st.mean_error:>10.4f} "
            f"{st.max_error:>8} {exp_runs:>10.4f} {overhead:>10.4f}"
        )


if __name__ == "__main__":
    print_envelope_for_block_sizes(
        block_sizes=[32, 64, 128, 256, 512, 1024, 2048, 4096, 8192, 23959],
        n_trials=2000,
        n_terms=23959,
        u_bits=51,
        p_min=1 << 16,
        p_max=(1 << 19) - 1,
        seed=0xB16B00B5,
        num_calls=1,
    )
