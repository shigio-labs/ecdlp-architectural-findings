import random
from math import prod

import pytest

from rns.basis import RNSBasis


def test_k2_handcheck():
    basis = RNSBasis([3, 5])
    assert basis.M == 15
    assert basis.Mi == (5, 3)
    # Round-trip every value.
    for x in range(15):
        assert basis.encode(x) == (x % 3, x % 5)
        assert basis.decode(basis.encode(x)) == x


def test_k3_357_appendix_b():
    """Plan Appendix B: p=(3,5,7), Mi=(35,21,15), MiInv=(2,1,1)."""
    basis = RNSBasis([3, 5, 7])
    assert basis.M == 105
    assert basis.Mi == (35, 21, 15)
    # 35 mod 3 == 2; 2^-1 mod 3 == 2.
    # 21 mod 5 == 1; 1^-1 mod 5 == 1.
    # 15 mod 7 == 1; 1^-1 mod 7 == 1.
    assert basis.MiInv == (2, 1, 1)


def test_k3_357_exhaustive_roundtrip():
    basis = RNSBasis([3, 5, 7])
    for x in range(105):
        assert basis.decode(basis.encode(x)) == x


def test_round_trip_random_5_moduli():
    random.seed(0xCAFE)
    basis = RNSBasis([3, 5, 7, 11, 13])
    M = prod(basis.moduli)
    assert M == 15015
    for _ in range(10_000):
        x = random.randrange(M)
        assert basis.decode(basis.encode(x)) == x


def test_round_trip_random_17bit_moduli():
    """Round-trip with primes the size we'll use for ECDLP experiments."""
    random.seed(0xBEEF)
    basis = RNSBasis([65537, 65539, 65543, 65551, 65557, 65563])
    M = basis.M
    for _ in range(2_000):
        x = random.randrange(M)
        assert basis.decode(basis.encode(x)) == x


def test_xi_consistency_with_decode():
    """Decoded value equals sum(xi[i] * Mi[i]) mod M."""
    basis = RNSBasis([3, 5, 7, 11])
    for x in [0, 1, 7, 42, 99, 1000, 1154]:
        residues = basis.encode(x)
        xi = basis.xi(residues)
        s = sum(xi[i] * basis.Mi[i] for i in range(basis.k))
        assert s % basis.M == x


def test_invalid_moduli_not_coprime():
    with pytest.raises(ValueError, match="coprime"):
        RNSBasis([3, 6])
    with pytest.raises(ValueError, match="coprime"):
        RNSBasis([4, 9, 6])  # 4 and 6 share factor 2


def test_invalid_too_few_moduli():
    with pytest.raises(ValueError, match="at least 2"):
        RNSBasis([7])


def test_invalid_modulus_below_2():
    with pytest.raises(ValueError, match="< 2"):
        RNSBasis([2, 1])


def test_decode_wrong_residue_count():
    basis = RNSBasis([3, 5, 7])
    with pytest.raises(ValueError, match="residue count"):
        basis.decode([1, 2])


def test_xi_wrong_residue_count():
    basis = RNSBasis([3, 5, 7])
    with pytest.raises(ValueError, match="residue count"):
        basis.xi([1, 2])


def test_repr_roundtrips_moduli_list():
    basis = RNSBasis([3, 5, 7])
    assert repr(basis) == "RNSBasis([3, 5, 7])"
