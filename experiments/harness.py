"""Common harness for Kawamura abort-rate measurements.

Pattern:
    rng = random.Random(seed)
    sampler = uniform_in_M(basis, rng)
    counters = measure(basis, sampler, precision_bits=12, n_samples=1_000_000)
    counters.abort_rate          # primary metric
    counters.certified_when_wrong  # MUST be zero (bug detector)
    counters.diff_distribution   # full shape
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from rns.basis import RNSBasis


Residues = tuple[int, ...]
Sampler = Callable[[], Residues]


# -- Counters --------------------------------------------------------------


@dataclass
class AbortCounters:
    """Aggregate stats from a measurement run.

    `certified_when_wrong` MUST be 0 in any honest run; nonzero indicates
    the certificate logic in kawamura.py is broken and the entire
    experiment is suspect.
    """

    n: int = 0
    aborts: int = 0
    certified_correct: int = 0
    certified_when_wrong: int = 0
    diff_distribution: dict[int, int] = field(default_factory=dict)

    def record(self, diff: int, certified: bool) -> None:
        self.n += 1
        self.diff_distribution[diff] = self.diff_distribution.get(diff, 0) + 1
        if diff != 0:
            self.aborts += 1
        if certified:
            if diff == 0:
                self.certified_correct += 1
            else:
                self.certified_when_wrong += 1

    @property
    def abort_rate(self) -> float:
        return self.aborts / self.n if self.n else 0.0

    @property
    def certified_rate(self) -> float:
        if not self.n:
            return 0.0
        return (self.certified_correct + self.certified_when_wrong) / self.n

    def to_dict(self) -> dict:
        return {
            "n": self.n,
            "aborts": self.aborts,
            "abort_rate": self.abort_rate,
            "certified_correct": self.certified_correct,
            "certified_when_wrong": self.certified_when_wrong,
            "diff_distribution": {
                str(k): v for k, v in sorted(self.diff_distribution.items())
            },
        }


# -- Core measurement ------------------------------------------------------


def measure(
    basis: RNSBasis,
    sampler: Sampler,
    precision_bits: int,
    n_samples: int,
    *,
    use_offset: bool = False,
) -> AbortCounters:
    """Run `n_samples` of the estimator vs. ground-truth comparison.

    Inlined hot loop: avoids attribute lookups on each iteration. Logic
    is identical to kawamura.kawamura_estimate + kawamura.true_quotient
    composed; cross-validated by tests/test_harness.py.
    """
    if precision_bits < 1:
        raise ValueError("precision_bits must be >= 1")
    if n_samples < 0:
        raise ValueError("n_samples must be >= 0")

    counters = AbortCounters()
    Mi = basis.Mi
    MiInv = basis.MiInv
    moduli = basis.moduli
    M = basis.M
    k = basis.k
    r = precision_bits
    offset_fp = (k >> 1) if use_offset else 0
    cert_lower = offset_fp
    cert_upper = (1 << r) - k + offset_fp

    for _ in range(n_samples):
        residues = sampler()
        s_full = 0
        s_fp = 0
        for i in range(k):
            xi_i = (residues[i] * MiInv[i]) % moduli[i]
            s_full += xi_i * Mi[i]
            s_fp += (xi_i << r) // moduli[i]
        q_true = s_full // M
        s_fp += offset_fp
        q_hat = s_fp >> r
        frac_fp = s_fp - (q_hat << r)
        certified = cert_lower <= frac_fp < cert_upper
        counters.record(q_hat - q_true, certified)
    return counters


# -- Samplers --------------------------------------------------------------


def uniform_in_M(basis: RNSBasis, rng: random.Random) -> Sampler:
    """Residues drawn uniformly from the product space (== x ~ U[0, basis.M))."""
    moduli = basis.moduli
    randrange = rng.randrange

    def sample() -> Residues:
        return tuple(randrange(p) for p in moduli)

    return sample


def uniform_in_range(basis: RNSBasis, upper: int, rng: random.Random) -> Sampler:
    """x ~ U([0, upper)). Useful for "x bounded by p" experiments."""
    if upper <= 0:
        raise ValueError("upper must be positive")
    encode = basis.encode
    randrange = rng.randrange

    def sample() -> Residues:
        return encode(randrange(upper))

    return sample


def product_with_modM_wrap(
    basis: RNSBasis, upper: int, rng: random.Random
) -> Sampler:
    """x = (a * b) mod basis.M with a, b ~ U([0, upper)).

    Avoids the huge integer multiplication a*b by reducing a and b mod each
    modulus first and multiplying componentwise. The induced residue
    distribution is identical to what (a*b) mod basis.M would produce.
    """
    if upper <= 0:
        raise ValueError("upper must be positive")
    moduli = basis.moduli
    randrange = rng.randrange

    def sample() -> Residues:
        a = randrange(upper)
        b = randrange(upper)
        return tuple((a % m) * (b % m) % m for m in moduli)

    return sample


def product_mod_p(
    basis: RNSBasis, p: int, rng: random.Random
) -> Sampler:
    """x = (a * b) mod p with a, b ~ U([0, p)). x lies in [0, p).

    The residue distribution is the encoding of a uniform-mod-p value;
    only meaningful when p < basis.M (otherwise multiple x's collide).
    """
    if p <= 0:
        raise ValueError("p must be positive")
    encode = basis.encode
    randrange = rng.randrange

    def sample() -> Residues:
        a = randrange(p)
        b = randrange(p)
        return encode((a * b) % p)

    return sample


def montgomery_t(
    basis: RNSBasis, p: int, rng: random.Random
) -> Sampler:
    """t = (-(a*b) * p^{-1}) mod M_basis, a, b ~ U([0, p)).

    Models the Montgomery-style intermediate value fed into the Kawamura
    estimator: c = a*b is computed, then t = -c * p^{-1} mod M_core, and
    base extension to the extension basis requires the q-estimate on t.

    For coprime gcd(p, basis.M) (always true here since p is the secp256k1
    prime and basis moduli are small primes), p^{-1} mod basis.M exists
    and the multiplication is well-defined. The induced distribution of
    t is approximately uniform on [0, basis.M), which makes this the
    correct distribution to use when assessing tapered RNS in the
    Montgomery setting.
    """
    if p <= 0:
        raise ValueError("p must be positive")
    p_inv_mod_M = pow(p, -1, basis.M)
    M = basis.M
    encode = basis.encode
    randrange = rng.randrange

    def sample() -> Residues:
        a = randrange(p)
        b = randrange(p)
        c = a * b
        t = (-c * p_inv_mod_M) % M
        return encode(t)

    return sample
