"""Prime selection utilities for RNS bases."""
from __future__ import annotations

import gmpy2


SECP256K1_P: int = (1 << 256) - (1 << 32) - 977


def primes_above(threshold: int, count: int) -> list[int]:
    """Return the `count` smallest primes strictly greater than `threshold`."""
    if count < 0:
        raise ValueError("count must be >= 0")
    primes: list[int] = []
    p = gmpy2.mpz(threshold)
    for _ in range(count):
        p = gmpy2.next_prime(p)
        primes.append(int(p))
    return primes


# Standard 17-modulus baseline used in CFS-style RNS over secp256k1:
# the first 17 primes strictly greater than 2**16. Each prime is ~17 bits,
# so the product is ~17*17 = 289 bits which exceeds p^2 (= 512 bits) — wait, no:
# 17 * 17 = 289 bits is *less* than 512. The product check is asserted in tests
# and we extend the basis there if 17 moduli are insufficient. Treat this
# constant as "the natural starting basis"; experiments may extend it.
STANDARD_17_BASIS: tuple[int, ...] = tuple(primes_above(1 << 16, 17))
