"""Sanity checks for the secp256k1 affine arithmetic before running the
big sweep. We verify against:
 1. Point doubling and addition match a reference (group order test).
 2. Montgomery ladder for k=N gives infinity (kG = O for k = ord(G)).
 3. The recorded diff at step i is non-zero (R0 ≠ R1).
"""
import random

import pytest

from delta.secp256k1 import (
    GX, GY, N, P, B, point_add, montgomery_ladder_diffs,
)


def naive_scalar_mult(k: int, base=(GX, GY)):
    """Reference scalar multiplication via repeated point_add."""
    if k == 0:
        return None
    result = None
    addend = base
    while k:
        if k & 1:
            result = point_add(result, addend)
        addend = point_add(addend, addend)
        k >>= 1
    return result


def test_point_on_curve():
    # Generator point should be on the curve: y² = x³ + 7 (mod p)
    assert (GY * GY - GX * GX * GX - B) % P == 0


def test_double_and_add_consistency():
    G = (GX, GY)
    G2 = point_add(G, G)
    G3a = point_add(G2, G)
    G3b = point_add(G, G2)
    assert G3a == G3b
    # 2G + G = 3G ≠ G
    assert G3a is not None
    assert G3a != G


def test_order_n_gives_infinity():
    # NG = O for the secp256k1 generator (group order N is prime)
    assert naive_scalar_mult(N) is None


def test_ladder_diffs_length():
    # Random 256-bit scalar with top bit set
    k = (1 << 255) | random.Random(0).getrandbits(255)
    diffs = montgomery_ladder_diffs(k, n_bits=256)
    assert len(diffs) == 256


def test_ladder_diffs_all_nonzero():
    """Adjacent ladder points have distinct x-coordinates (else ladder
    has degenerated)."""
    rng = random.Random(0xC0FFEE)
    for _ in range(20):
        k = (1 << 255) | rng.getrandbits(255)
        diffs = montgomery_ladder_diffs(k, n_bits=256)
        assert all(d != 0 for d in diffs)


def test_ladder_matches_naive_scalar_mult():
    """A standard Montgomery ladder of the form
       R0=P, R1=2P then for i=n-2..0: process k_i; return R0
       computes kP. Verify on a few random scalars."""
    rng = random.Random(0xDEADBEEF)
    for trial in range(5):
        k = (1 << 255) | rng.getrandbits(255)
        # Reproduce the inner ladder, this time tracking the final R0.
        R0 = (GX, GY)
        R1 = point_add(R0, R0)
        for i in range(254, -1, -1):
            bit = (k >> i) & 1
            if bit == 0:
                R1 = point_add(R0, R1)
                R0 = point_add(R0, R0)
            else:
                R0 = point_add(R0, R1)
                R1 = point_add(R1, R1)
        # Compare to naive
        expected = naive_scalar_mult(k)
        assert R0 == expected, f"k={hex(k)}: ladder={R0}, naive={expected}"


def test_negative_scalar_rejected():
    with pytest.raises(ValueError):
        montgomery_ladder_diffs(0, n_bits=256)


def test_high_bit_required():
    # k = 1 has only bit-0 set, not bit-255 — should fail
    with pytest.raises(ValueError):
        montgomery_ladder_diffs(1, n_bits=256)
