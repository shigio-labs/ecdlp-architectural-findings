"""Correction models for blockwise q_M accumulation.

This module answers a practical Sprint 1 question:
can blockwise truncation be corrected back to exactness while keeping
state width below the baseline q_bits + u_bits?
"""
from __future__ import annotations

from dataclasses import dataclass
from math import ceil, log2
from typing import Iterable


def num_blocks(num_terms: int, block_size: int) -> int:
    if num_terms < 0:
        raise ValueError("num_terms must be >= 0")
    if block_size < 1:
        raise ValueError("block_size must be >= 1")
    if num_terms == 0:
        return 0
    return (num_terms + block_size - 1) // block_size


def bits_for_block_remainder_sum(num_terms: int, block_size: int, u_bits: int) -> int:
    """Bits needed for storing the full sum of per-block remainders."""
    if u_bits < 1:
        raise ValueError("u_bits must be >= 1")
    b = num_blocks(num_terms, block_size)
    if b == 0:
        return 1
    # Max remainder per block is 2^u - 1.
    max_sum = b * ((1 << u_bits) - 1)
    return max_sum.bit_length()


def exact_blockwise_with_remainder_stream(
    terms: Iterable[int],
    u_bits: int,
    block_size: int,
) -> int:
    """Exact quotient via block sums plus streaming remainder carry.

    Algorithm:
    - For each block, add floor(block_sum / 2^u) to q.
    - Accumulate block remainders in an u-bit rolling register `rem`.
    - Carry from `rem` is added to q each block.

    This is exact and equivalent to floor(total_sum / 2^u).
    """
    if u_bits < 1:
        raise ValueError("u_bits must be >= 1")
    if block_size < 1:
        raise ValueError("block_size must be >= 1")

    mask = (1 << u_bits) - 1
    terms = list(terms)
    q = 0
    rem = 0
    for i in range(0, len(terms), block_size):
        block = terms[i : i + block_size]
        s = sum(block)
        q += s >> u_bits
        rem += s & mask
        q += rem >> u_bits
        rem &= mask
    return q


@dataclass(frozen=True)
class CorrectionWidthScenario:
    q_bits: int
    u_bits: int
    num_terms: int
    block_size: int

    def baseline_bits(self) -> int:
        return self.q_bits + self.u_bits

    def exact_blockwise_stream_bits(self) -> int:
        """Exact blockwise streaming needs q register + u-bit rolling remainder."""
        return self.q_bits + self.u_bits

    def full_remainder_sum_bits(self) -> int:
        """Alternative exact correction with explicit full remainder sum."""
        return self.q_bits + bits_for_block_remainder_sum(
            self.num_terms, self.block_size, self.u_bits
        )

    def correction_overhead_bits_vs_baseline(self) -> int:
        return self.full_remainder_sum_bits() - self.baseline_bits()

    def block_count(self) -> int:
        return num_blocks(self.num_terms, self.block_size)

    def correction_counter_bits(self) -> int:
        """Bits for floor(sum(remainders)/2^u) only (not enough for exact correction by itself)."""
        b = self.block_count()
        if b <= 1:
            return 0
        return ceil(log2(b))
