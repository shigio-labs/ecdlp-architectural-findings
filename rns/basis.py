"""RNS basis: pairwise coprime moduli with precomputed CRT constants."""
from __future__ import annotations

from math import gcd, prod
from typing import Sequence


class RNSBasis:
    """Residue number system basis.

    Stores moduli and precomputes CRT constants:
        M        = prod(moduli)
        Mi[i]    = M / p_i
        MiInv[i] = (Mi[i] mod p_i)^{-1} mod p_i

    encode/decode are inverses of each other on the range [0, M).
    """

    __slots__ = ("moduli", "k", "M", "Mi", "MiInv")

    moduli: tuple[int, ...]
    k: int
    M: int
    Mi: tuple[int, ...]
    MiInv: tuple[int, ...]

    def __init__(self, moduli: Sequence[int]) -> None:
        ms = tuple(int(m) for m in moduli)
        if len(ms) < 2:
            raise ValueError("RNS basis requires at least 2 moduli")
        for m in ms:
            if m < 2:
                raise ValueError(f"Modulus {m} is < 2")
        for i in range(len(ms)):
            for j in range(i + 1, len(ms)):
                if gcd(ms[i], ms[j]) != 1:
                    raise ValueError(
                        f"Moduli not pairwise coprime: gcd({ms[i]}, {ms[j]}) != 1"
                    )
        self.moduli = ms
        self.k = len(ms)
        self.M = prod(ms)
        self.Mi = tuple(self.M // p for p in ms)
        self.MiInv = tuple(
            pow(self.Mi[i] % ms[i], -1, ms[i]) for i in range(self.k)
        )

    def __repr__(self) -> str:
        return f"RNSBasis({list(self.moduli)})"

    def encode(self, x: int) -> tuple[int, ...]:
        """Encode integer `x` as residues mod each modulus."""
        return tuple(x % p for p in self.moduli)

    def decode(self, residues: Sequence[int]) -> int:
        """CRT-decode residues to the unique integer in [0, M)."""
        if len(residues) != self.k:
            raise ValueError(
                f"residue count {len(residues)} != basis size {self.k}"
            )
        s = 0
        for r, Mi, MiInv, p in zip(residues, self.Mi, self.MiInv, self.moduli):
            xi = (r * MiInv) % p
            s += xi * Mi
        return s % self.M

    def xi(self, residues: Sequence[int]) -> tuple[int, ...]:
        """Return the CRT mixed-radix-like coefficients
        xi[i] = (residues[i] * MiInv[i]) mod p_i.

        These are the per-index quantities that appear in the CRT formula
            x = sum_i xi[i] * Mi[i] - q * M
        and that the Kawamura-Kapoor estimator uses to estimate q.
        """
        if len(residues) != self.k:
            raise ValueError(
                f"residue count {len(residues)} != basis size {self.k}"
            )
        return tuple(
            (r * MiInv) % p
            for r, MiInv, p in zip(residues, self.MiInv, self.moduli)
        )
