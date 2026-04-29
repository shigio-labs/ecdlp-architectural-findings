"""Cross-validate the inlined `measure` loop against the public
kawamura_estimate + true_quotient pair on a small basis and a small sample.

If these diverge, the inlined loop has a bug and all experiment results
are suspect.
"""
import random

from rns.basis import RNSBasis
from rns.kawamura import kawamura_estimate, true_quotient

from experiments.harness import (
    AbortCounters,
    measure,
    uniform_in_M,
    uniform_in_range,
    product_with_modM_wrap,
    product_mod_p,
)


def reference_measure(basis, sampler, r, n, *, use_offset=False):
    """Reference: built from the public API. Slower but manifestly correct."""
    counters = AbortCounters()
    for _ in range(n):
        residues = sampler()
        q_true = true_quotient(residues, basis)
        q_hat, certified = kawamura_estimate(
            residues, basis, r, use_offset=use_offset
        )
        counters.record(q_hat - q_true, certified)
    return counters


def test_inlined_measure_matches_reference_uniform():
    """Run identical seeds with inlined `measure` and reference; results must match."""
    basis = RNSBasis([3, 5, 7, 11, 13])
    for r in (4, 6, 8, 10):
        for use_offset in (False, True):
            rng_a = random.Random(0xCAFE_BABE)
            rng_b = random.Random(0xCAFE_BABE)
            sa = uniform_in_M(basis, rng_a)
            sb = uniform_in_M(basis, rng_b)
            a = measure(basis, sa, r, 5_000, use_offset=use_offset)
            b = reference_measure(basis, sb, r, 5_000, use_offset=use_offset)
            assert a.aborts == b.aborts, (r, use_offset, a.aborts, b.aborts)
            assert a.certified_correct == b.certified_correct
            assert a.certified_when_wrong == b.certified_when_wrong
            assert a.diff_distribution == b.diff_distribution


def test_inlined_measure_matches_reference_product():
    basis = RNSBasis([3, 5, 7, 11, 13, 17])
    p = 251  # small prime for testing
    for r in (4, 6, 8):
        rng_a = random.Random(0xF00D)
        rng_b = random.Random(0xF00D)
        sa = product_with_modM_wrap(basis, p, rng_a)
        sb = product_with_modM_wrap(basis, p, rng_b)
        a = measure(basis, sa, r, 3_000)
        b = reference_measure(basis, sb, r, 3_000)
        assert a.diff_distribution == b.diff_distribution


def test_certified_when_wrong_is_zero_in_clean_run():
    """Negative control: a healthy run NEVER has certified_when_wrong > 0."""
    basis = RNSBasis([3, 5, 7, 11, 13])
    rng = random.Random(0xDEAD)
    sampler = uniform_in_M(basis, rng)
    counters = measure(basis, sampler, precision_bits=8, n_samples=10_000)
    assert counters.certified_when_wrong == 0


def test_uniform_in_range_distribution_correct():
    """uniform_in_range(p) should encode a uniform value in [0, p)."""
    basis = RNSBasis([7, 11, 13])  # M = 1001
    p = 100
    rng = random.Random(0xBEEF)
    sampler = uniform_in_range(basis, p, rng)
    # Decode samples — they should all lie in [0, 100).
    from rns.basis import RNSBasis as _RB  # ensure no shadow
    seen = set()
    for _ in range(2_000):
        residues = sampler()
        x = basis.decode(residues)
        assert 0 <= x < p
        seen.add(x)
    # Should cover most values in [0, 100).
    assert len(seen) > 80


def test_product_mod_p_distribution_lies_in_p():
    basis = RNSBasis([7, 11, 13])
    p = 31
    rng = random.Random(0xABCD)
    sampler = product_mod_p(basis, p, rng)
    for _ in range(1_000):
        residues = sampler()
        x = basis.decode(residues)
        assert 0 <= x < p


def test_product_with_modM_wrap_residues_match_integer_form():
    """Cross-check componentwise sampler vs computing (a*b) mod M via int."""
    basis = RNSBasis([7, 11, 13, 17])
    p = 1_000_000_007
    rng_a = random.Random(0x1234)
    rng_b = random.Random(0x1234)
    fast = product_with_modM_wrap(basis, p, rng_a)
    # Reference: integer multiplication then encode.
    randrange_b = rng_b.randrange

    def slow():
        a = randrange_b(p)
        b = randrange_b(p)
        return basis.encode(a * b)

    for _ in range(500):
        assert fast() == slow()


def test_abort_rate_zero_at_high_precision():
    basis = RNSBasis([3, 5, 7, 11, 13])
    rng = random.Random(0)
    sampler = uniform_in_M(basis, rng)
    c = measure(basis, sampler, precision_bits=24, n_samples=5_000)
    assert c.aborts == 0
    assert c.certified_when_wrong == 0


def test_abort_rate_nonzero_at_low_precision():
    """Negative control at low precision: at least *some* aborts must occur."""
    basis = RNSBasis([3, 5, 7, 11, 13])
    rng = random.Random(42)
    sampler = uniform_in_M(basis, rng)
    c = measure(basis, sampler, precision_bits=3, n_samples=5_000)
    assert c.aborts > 0, "no aborts at r=3 — failure path not exercised"
