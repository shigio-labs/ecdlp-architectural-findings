"""secp256k1 affine point arithmetic for the Δ-mini experiment.

Optimized just enough to run 1e4 ladders × 256 steps in tens of seconds.
gmpy2.invert for the modular inverse (fastest available without C extension).
"""
from __future__ import annotations

from typing import Optional

import gmpy2

P: int = (1 << 256) - (1 << 32) - 977
A: int = 0
B: int = 7
GX: int = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798
GY: int = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8
N: int = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141

# gmpy2 versions for speed
_P = gmpy2.mpz(P)

# Point = (x, y) tuple of ints, or None for point at infinity O
Point = Optional[tuple[int, int]]


def point_add(P_pt: Point, Q_pt: Point) -> Point:
    """Affine point addition for y² = x³ + 7 over F_p (a = 0)."""
    if P_pt is None:
        return Q_pt
    if Q_pt is None:
        return P_pt
    x1, y1 = P_pt
    x2, y2 = Q_pt
    if x1 == x2:
        if (y1 + y2) % P == 0:
            return None  # P + (-P) = O
        # Doubling: x1 == x2 and y1 == y2
        if y1 == 0:
            return None
        # λ = 3x₁² / 2y₁ (a = 0)
        num = 3 * x1 * x1 % P
        den = 2 * y1 % P
        lam = num * int(gmpy2.invert(den, _P)) % P
    else:
        # General addition
        num = (y2 - y1) % P
        den = (x2 - x1) % P
        lam = num * int(gmpy2.invert(den, _P)) % P
    x3 = (lam * lam - x1 - x2) % P
    y3 = (lam * (x1 - x3) - y1) % P
    return (x3, y3)


def montgomery_ladder_diffs(k: int, n_bits: int = 256) -> list[int]:
    """Run an affine Montgomery ladder for kP on secp256k1, recording
    (x_R1 − x_R0) mod p at each step. The scalar's high bit must be set
    so the ladder never hits the point-at-infinity edge case.

    Returns a list of length `n_bits` of unsigned residues in [0, p).
    """
    if not (k >> (n_bits - 1)) & 1:
        raise ValueError("scalar's high bit must be set")
    if k <= 0:
        raise ValueError("scalar must be positive")
    R0: Point = (GX, GY)
    R1: Point = point_add(R0, R0)
    diffs: list[int] = []
    if R0 is None or R1 is None:
        raise RuntimeError("ladder degenerated on initialization")
    diffs.append((R1[0] - R0[0]) % P)
    for i in range(n_bits - 2, -1, -1):
        bit = (k >> i) & 1
        if bit == 0:
            R1 = point_add(R0, R1)
            R0 = point_add(R0, R0)
        else:
            R0 = point_add(R0, R1)
            R1 = point_add(R1, R1)
        if R0 is None or R1 is None:
            raise RuntimeError(f"ladder hit O at step {n_bits - 1 - i}")
        diffs.append((R1[0] - R0[0]) % P)
    return diffs
