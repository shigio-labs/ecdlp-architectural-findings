"""Basis configurations used by the experiments.

Two families are defined:

* `STANDARD_17_BASIS` — the user-plan baseline: 17 primes just above 2^16,
  product ~272 bits. With this basis, *core sizes* k_c < 16 give
  M_core < p (secp256k1) and so cannot represent F_p elements uniquely;
  experiments with such k_c are still mathematically meaningful for the
  estimator but should not be read as "valid ECDLP configurations".

* `WIDE_20BIT_BASIS` — chosen so that k_c = 13 already gives M_core > p.
  This matches the plan's stated `prod p_i in (p, p^1.6)` for k_c around
  13–14 and is the ECDLP-relevant variant for the reduced-core question.
"""
from __future__ import annotations

from math import log2, prod

from rns.primes import SECP256K1_P, STANDARD_17_BASIS, primes_above


# Wide basis: 20 primes above 2**20, each ~20 bits.
# 13 primes * 20 bits ~ 260 bits > 256 = log2(p). Full 20 -> ~400 bits.
WIDE_20BIT_BASIS: tuple[int, ...] = tuple(primes_above(1 << 20, 20))


def basis_summary(name: str, primes: tuple[int, ...]) -> dict:
    M = prod(primes)
    return {
        "name": name,
        "k": len(primes),
        "primes_first": primes[:3],
        "primes_last": primes[-3:],
        "log2_M": log2(M),
        "log2_M_minus_log2_p": log2(M) - log2(SECP256K1_P),
    }


if __name__ == "__main__":
    import json

    print(json.dumps(basis_summary("STANDARD_17_BASIS", STANDARD_17_BASIS), indent=2))
    print(json.dumps(basis_summary("WIDE_20BIT_BASIS", WIDE_20BIT_BASIS), indent=2))
    p = SECP256K1_P
    print(f"\nlog2(p) = {log2(p):.3f}")
    print("\nCore-size sweep (log2 M_core minus log2 p):")
    for name, full in [
        ("standard17", STANDARD_17_BASIS),
        ("wide20", WIDE_20BIT_BASIS),
    ]:
        for k_c in range(10, len(full) + 1):
            Mc = prod(full[:k_c])
            print(f"  {name:>10} k_c={k_c:>2}: log2(M_c)={log2(Mc):.2f}, "
                  f"vs p: {log2(Mc) - log2(p):+.2f} bits")
