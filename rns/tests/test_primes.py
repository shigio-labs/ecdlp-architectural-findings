from math import prod

from rns.primes import SECP256K1_P, STANDARD_17_BASIS, primes_above


def test_first_prime_above_65536_is_65537():
    assert primes_above(65536, 1) == [65537]


def test_primes_above_are_strictly_greater():
    primes = primes_above(100, 5)
    assert all(p > 100 for p in primes)
    assert primes == sorted(set(primes))


def test_standard_17_basis_size_and_pairwise_distinct():
    assert len(STANDARD_17_BASIS) == 17
    assert len(set(STANDARD_17_BASIS)) == 17
    assert all(p > (1 << 16) for p in STANDARD_17_BASIS)


def test_standard_17_basis_first_few_known():
    # The first primes above 65536 are well known — sanity-check by hand.
    # 65537 is prime (Fermat F_4); next primes follow.
    expected_prefix = (65537, 65539, 65543, 65551, 65557)
    assert STANDARD_17_BASIS[: len(expected_prefix)] == expected_prefix


def test_standard_17_basis_product_vs_p_squared():
    """Document where the 17-modulus baseline sits relative to p**2.

    The plan suggests "first 17 primes above 2**16, ~17 bits each, product > p^2".
    For 17-bit primes we have 17*17 = ~289 bits, while p^2 is ~512 bits, so the
    product cannot exceed p^2 — that note in the plan is incorrect. This test
    documents the actual relation so we know how many extra moduli are needed
    if we want product > p^2 in baseline experiments.
    """
    M = prod(STANDARD_17_BASIS)
    assert M > SECP256K1_P  # we can at least represent F_p elements once
    # but not p^2:
    assert M < SECP256K1_P ** 2


def test_count_zero_returns_empty():
    assert primes_above(100, 0) == []
