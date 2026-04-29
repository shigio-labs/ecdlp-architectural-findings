"""Tests for the Kawamura-Kapoor estimator.

Strategy:
  * Cross-check kawamura_estimate against true_quotient (different code paths)
    on small exhaustive cases and large random samples.
  * Verify the *direction* of the error is asymmetric without offset and
    symmetric with offset (this is the structural property the plan flags
    as a primary bug indicator).
  * Verify the "is_provably_correct" certificate NEVER lies (false positives
    would silently mask abort rates in experiments).
  * Confirm at least *some* aborts at low precision; otherwise the test is
    not actually exercising the failure path.
"""
import random
from fractions import Fraction
from itertools import product

import pytest

from rns.basis import RNSBasis
from rns.kawamura import kawamura_estimate, true_quotient
from rns.primes import STANDARD_17_BASIS


SMALL_BASIS = RNSBasis([3, 5, 7])  # k=3, M=105


def all_valid_residue_tuples(basis: RNSBasis):
    return list(product(*(range(p) for p in basis.moduli)))


def true_quotient_via_fractions(residues, basis: RNSBasis) -> int:
    """Independent reference using exact rationals (Fraction) — different
    code path from the integer/CRT-based true_quotient."""
    xi = basis.xi(residues)
    s = sum(Fraction(xi[i], basis.moduli[i]) for i in range(basis.k))
    return int(s)  # for non-negative s, int(Fraction) == floor


# --- Sanity for true_quotient itself ---


def test_true_quotient_x1_in_357():
    """Plan Appendix B sanity: x=1 -> xi=(2,1,1), sum*Mi = 70+21+15 = 106, q=1."""
    basis = SMALL_BASIS
    residues = basis.encode(1)
    assert basis.xi(residues) == (2, 1, 1)
    assert true_quotient(residues, basis) == 1


def test_true_quotient_x0_is_zero():
    assert true_quotient(SMALL_BASIS.encode(0), SMALL_BASIS) == 0


def test_true_quotient_two_implementations_agree_357():
    """Cross-check the integer CRT-based reference against a Fraction-based
    reference on every value in the small basis."""
    basis = SMALL_BASIS
    for x in range(basis.M):
        residues = basis.encode(x)
        assert true_quotient(residues, basis) == true_quotient_via_fractions(
            residues, basis
        )


def test_true_quotient_consistent_with_decode():
    """For every x in [0, M): decode(encode(x)) == x and sum xi*Mi == x + q*M."""
    basis = RNSBasis([3, 5, 7, 11])
    # All test values must lie in [0, basis.M); the decoded value is x mod M.
    for x in [0, 1, 7, 42, 99, 1000, basis.M - 1]:
        assert 0 <= x < basis.M
        residues = basis.encode(x)
        q = true_quotient(residues, basis)
        xi = basis.xi(residues)
        s = sum(xi[i] * basis.Mi[i] for i in range(basis.k))
        assert basis.decode(residues) == x
        assert s == x + q * basis.M


def test_true_quotient_in_zero_to_k_minus_one():
    """For x in [0, M), the quotient lies in {0, ..., k-1}."""
    basis = SMALL_BASIS
    for x in range(basis.M):
        q = true_quotient(basis.encode(x), basis)
        assert 0 <= q < basis.k


# --- Kawamura estimator: high precision => exact ---


def test_kawamura_exact_at_high_precision_357():
    """At r=24, every input in the small basis must reproduce the true q."""
    basis = SMALL_BASIS
    for x in range(basis.M):
        residues = basis.encode(x)
        q_true = true_quotient(residues, basis)
        q_hat, certified = kawamura_estimate(residues, basis, precision_bits=24)
        assert q_hat == q_true
        assert certified


def test_kawamura_exact_at_high_precision_random_17_basis():
    """Random sanity at r=24 on the 17-modulus baseline: all correct & certified."""
    basis = RNSBasis(STANDARD_17_BASIS)
    rng = random.Random(0xCAFEFEED)
    for _ in range(1_000):
        x = rng.randrange(basis.M)
        residues = basis.encode(x)
        q_true = true_quotient(residues, basis)
        q_hat, certified = kawamura_estimate(residues, basis, precision_bits=24)
        assert q_hat == q_true
        assert certified


# --- Error direction: asymmetric without offset, symmetric with ---


def test_kawamura_no_offset_error_in_minus_one_zero():
    """When k * 2^-r < 1 the no-offset error must be in {-1, 0} only.

    This is the plan's primary structural sanity check: a symmetric
    distribution would indicate a bug (likely sign of |M_i|^{-1} or floor
    direction).
    """
    basis = SMALL_BASIS  # k=3
    for r in (4, 5, 6, 8, 10, 12):
        assert basis.k < (1 << r), "test parameters violate k * 2^-r < 1"
        for x in range(basis.M):
            residues = basis.encode(x)
            q_true = true_quotient(residues, basis)
            q_hat, _ = kawamura_estimate(residues, basis, r)
            diff = q_hat - q_true
            assert diff in (-1, 0), (
                f"x={x} r={r}: q_hat - q_true = {diff} outside {{-1, 0}}"
            )


def test_kawamura_offset_error_in_minus_one_zero_plus_one():
    """With offset, error is symmetric and lands in {-1, 0, +1}."""
    basis = SMALL_BASIS
    for r in (4, 5, 6, 8, 10, 12):
        assert basis.k < (1 << r)
        for x in range(basis.M):
            residues = basis.encode(x)
            q_true = true_quotient(residues, basis)
            q_hat, _ = kawamura_estimate(residues, basis, r, use_offset=True)
            diff = q_hat - q_true
            assert diff in (-1, 0, 1), (
                f"x={x} r={r}: q_hat - q_true = {diff} outside {{-1, 0, 1}}"
            )


def test_kawamura_no_offset_never_overshoots():
    """Stronger statement: q_hat <= q_true always (no offset)."""
    basis = SMALL_BASIS
    for r in (4, 6, 8, 12, 16):
        for x in range(basis.M):
            residues = basis.encode(x)
            q_true = true_quotient(residues, basis)
            q_hat, _ = kawamura_estimate(residues, basis, r)
            assert q_hat <= q_true


# --- Certificate must never lie ---


def test_certificate_never_false_positive_small():
    """When is_provably_correct is True the estimate MUST equal true q.
    A false positive here would silently corrupt all downstream measurements.
    """
    basis = SMALL_BASIS
    for r in range(2, 16):
        for x in range(basis.M):
            residues = basis.encode(x)
            q_true = true_quotient(residues, basis)
            for use_offset in (False, True):
                q_hat, certified = kawamura_estimate(
                    residues, basis, r, use_offset=use_offset
                )
                if certified:
                    assert q_hat == q_true, (
                        f"FALSE CERTIFICATE: x={x} r={r} use_offset={use_offset}"
                        f" q_hat={q_hat} q_true={q_true}"
                    )


def test_certificate_never_false_positive_random_5_basis():
    basis = RNSBasis([3, 5, 7, 11, 13])
    rng = random.Random(0xDEADBEEF)
    for _ in range(5_000):
        x = rng.randrange(basis.M)
        residues = basis.encode(x)
        q_true = true_quotient(residues, basis)
        for r in (4, 6, 8, 10, 12):
            for use_offset in (False, True):
                q_hat, certified = kawamura_estimate(
                    residues, basis, r, use_offset=use_offset
                )
                if certified:
                    assert q_hat == q_true


# --- Negative control: low precision MUST produce some aborts ---


def test_low_precision_actually_has_aborts():
    """At r=2 with k=3 (slop = 3/4 < 1), there must be inputs where q_hat != q.

    If this passes silently with zero aborts, our experiment apparatus is
    broken — the test would never detect the very thing it's measuring.
    """
    basis = SMALL_BASIS
    aborts_no = 0
    aborts_off = 0
    for x in range(basis.M):
        residues = basis.encode(x)
        q_true = true_quotient(residues, basis)
        q_hat_no, _ = kawamura_estimate(residues, basis, precision_bits=2)
        q_hat_off, _ = kawamura_estimate(
            residues, basis, precision_bits=2, use_offset=True
        )
        if q_hat_no != q_true:
            aborts_no += 1
        if q_hat_off != q_true:
            aborts_off += 1
    assert aborts_no > 0, (
        f"no-offset r=2 k=3 produced ZERO aborts in {basis.M} inputs — "
        "the failure path is not being exercised"
    )
    # Document the actual count for visibility (no strict assertion on offset).
    print(f"\nr=2 k=3: aborts no_offset={aborts_no}, offset={aborts_off}")


# --- Distribution shape ---


def test_kawamura_zero_aborts_at_high_precision_5_basis():
    basis = RNSBasis([3, 5, 7, 11, 13])
    for x in range(basis.M):
        residues = basis.encode(x)
        q_true = true_quotient(residues, basis)
        q_hat, _ = kawamura_estimate(residues, basis, precision_bits=20)
        assert q_hat == q_true


def test_kawamura_invalid_precision():
    with pytest.raises(ValueError, match="precision_bits"):
        kawamura_estimate(SMALL_BASIS.encode(7), SMALL_BASIS, precision_bits=0)


# --- Cross-check on a 17-modulus basis at moderate precision ---


def test_kawamura_random_17_basis_r12_no_false_certificates():
    """At r=12 on the 17-modulus basis, certificates must be honest.

    Allows aborts to occur but they must never coincide with certified=True.
    """
    basis = RNSBasis(STANDARD_17_BASIS)
    rng = random.Random(0xABADCAFE)
    n = 2_000
    for _ in range(n):
        x = rng.randrange(basis.M)
        residues = basis.encode(x)
        q_true = true_quotient(residues, basis)
        for use_offset in (False, True):
            q_hat, certified = kawamura_estimate(
                residues, basis, precision_bits=12, use_offset=use_offset
            )
            if certified:
                assert q_hat == q_true
