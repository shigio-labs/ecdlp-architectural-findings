"""Componentwise arithmetic on RNS-encoded values."""
from __future__ import annotations

from typing import Sequence

from .basis import RNSBasis

Residues = tuple[int, ...]


def add(basis: RNSBasis, a: Sequence[int], b: Sequence[int]) -> Residues:
    return tuple((x + y) % p for x, y, p in zip(a, b, basis.moduli))


def sub(basis: RNSBasis, a: Sequence[int], b: Sequence[int]) -> Residues:
    return tuple((x - y) % p for x, y, p in zip(a, b, basis.moduli))


def mul(basis: RNSBasis, a: Sequence[int], b: Sequence[int]) -> Residues:
    return tuple((x * y) % p for x, y, p in zip(a, b, basis.moduli))


def neg(basis: RNSBasis, a: Sequence[int]) -> Residues:
    return tuple((-x) % p for x, p in zip(a, basis.moduli))
