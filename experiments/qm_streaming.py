"""q_M streaming arithmetic models for Sprint 1.

We model three variants for the quotient
    q = floor((sum_i term_i) / 2^u):

1) Exact streaming:
   keep both running quotient and u-bit remainder.
   This is algebraically exact and equivalent to one-shot division.

2) Lossy per-term truncation:
   add only floor(term_i / 2^u), discard per-term low bits.
   This saves state but introduces deterministic downward error.

3) Blockwise truncation:
   exact inside a block, discard remainder at block boundaries.
   Error decreases as block size grows, at the cost of keeping u-bit remainder
   live for the whole block.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2
from random import Random
from typing import Iterable


def bits_needed_nonnegative(x: int) -> int:
    if x < 0:
        raise ValueError("x must be non-negative")
    if x == 0:
        return 1
    return x.bit_length()


def exact_streaming_quotient(terms: Iterable[int], u_bits: int) -> int:
    """Compute floor(sum(terms)/2^u) via exact streaming with remainder."""
    if u_bits < 1:
        raise ValueError("u_bits must be >= 1")
    mask = (1 << u_bits) - 1
    q = 0
    rem = 0
    for t in terms:
        if t < 0:
            raise ValueError("terms must be non-negative")
        rem += t
        q += rem >> u_bits
        rem &= mask
    return q


def lossy_per_term_quotient(terms: Iterable[int], u_bits: int) -> int:
    """Compute sum_i floor(term_i/2^u), discarding every per-term remainder."""
    if u_bits < 1:
        raise ValueError("u_bits must be >= 1")
    return sum(t >> u_bits for t in terms)


def blockwise_quotient(terms: list[int], u_bits: int, block_size: int) -> int:
    """Exact within each block, discard remainder between blocks."""
    if u_bits < 1:
        raise ValueError("u_bits must be >= 1")
    if block_size < 1:
        raise ValueError("block_size must be >= 1")

    q = 0
    for i in range(0, len(terms), block_size):
        block = terms[i : i + block_size]
        # Exact within block:
        block_sum = sum(block)
        q += block_sum >> u_bits
    return q


def lossy_error_upper_bound(num_terms: int) -> int:
    """Worst-case downward error for per-term truncation.

    Each discarded remainder is < 1 in units of 2^u, so total error < num_terms.
    """
    if num_terms < 0:
        raise ValueError("num_terms must be >= 0")
    return max(0, num_terms - 1)


def blockwise_error_upper_bound(num_terms: int, block_size: int) -> int:
    """Worst-case downward error for blockwise truncation."""
    if num_terms < 0:
        raise ValueError("num_terms must be >= 0")
    if block_size < 1:
        raise ValueError("block_size must be >= 1")
    num_blocks = ceil(num_terms / block_size) if num_terms else 0
    return max(0, num_blocks - 1)


def guard_bits_for_error_bound(error_bound: int) -> int:
    """Extra bits needed to represent additive correction up to error_bound."""
    if error_bound < 0:
        raise ValueError("error_bound must be >= 0")
    if error_bound == 0:
        return 0
    return ceil(log2(error_bound + 1))


@dataclass(frozen=True)
class QMWidthScenario:
    q_bits: int
    u_bits: int
    num_terms: int

    def exact_streaming_state_bits(self) -> int:
        """State bits for exact streaming (q + remainder)."""
        if self.q_bits < 1 or self.u_bits < 1:
            raise ValueError("q_bits and u_bits must be >= 1")
        return self.q_bits + self.u_bits

    def lossy_state_bits_with_guard(self) -> int:
        """State bits for lossy per-term truncation with explicit error guard."""
        if self.q_bits < 1:
            raise ValueError("q_bits must be >= 1")
        eb = lossy_error_upper_bound(self.num_terms)
        return self.q_bits + guard_bits_for_error_bound(eb)


def sample_term_sequence(
    *,
    n_terms: int,
    p_min: int,
    p_max: int,
    u_bits: int,
    rng: Random,
) -> list[int]:
    """Generate synthetic term_i = r_i * w_i * floor(2^u / p_i) samples.

    This is a statistical backstop for arithmetic identities; it is not a
    full CFS distribution model.
    """
    if n_terms < 0:
        raise ValueError("n_terms must be >= 0")
    if p_min < 2 or p_max < p_min:
        raise ValueError("invalid prime bounds")
    if u_bits < 1:
        raise ValueError("u_bits must be >= 1")

    terms: list[int] = []
    two_u = 1 << u_bits
    for _ in range(n_terms):
        p = rng.randrange(p_min, p_max + 1)
        r = rng.randrange(0, p)
        w = rng.randrange(0, p)
        terms.append(r * w * (two_u // p))
    return terms
