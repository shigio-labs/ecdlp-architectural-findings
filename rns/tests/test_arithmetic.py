import random
from math import prod

from rns import arithmetic as ar
from rns.basis import RNSBasis


def test_add_exhaustive_357():
    basis = RNSBasis([3, 5, 7])
    M = 105
    for a in range(M):
        for b in range(M):
            r = ar.add(basis, basis.encode(a), basis.encode(b))
            assert basis.decode(r) == (a + b) % M


def test_mul_exhaustive_357():
    basis = RNSBasis([3, 5, 7])
    M = 105
    for a in range(M):
        for b in range(M):
            r = ar.mul(basis, basis.encode(a), basis.encode(b))
            assert basis.decode(r) == (a * b) % M


def test_sub_exhaustive_357():
    basis = RNSBasis([3, 5, 7])
    M = 105
    for a in range(M):
        for b in range(M):
            r = ar.sub(basis, basis.encode(a), basis.encode(b))
            assert basis.decode(r) == (a - b) % M


def test_neg_exhaustive_357():
    basis = RNSBasis([3, 5, 7])
    M = 105
    for a in range(M):
        r = ar.neg(basis, basis.encode(a))
        assert basis.decode(r) == (-a) % M


def test_mul_random_large():
    random.seed(0xDEAD)
    basis = RNSBasis([65537, 65539, 65543, 65551, 65557])
    M = basis.M
    for _ in range(10_000):
        a = random.randrange(M)
        b = random.randrange(M)
        r = ar.mul(basis, basis.encode(a), basis.encode(b))
        assert basis.decode(r) == (a * b) % M


def test_add_random_large():
    random.seed(0xBEEF)
    basis = RNSBasis([65537, 65539, 65543, 65551, 65557])
    M = basis.M
    for _ in range(10_000):
        a = random.randrange(M)
        b = random.randrange(M)
        r = ar.add(basis, basis.encode(a), basis.encode(b))
        assert basis.decode(r) == (a + b) % M


def test_sub_random_large():
    random.seed(0xF00D)
    basis = RNSBasis([65537, 65539, 65543])
    M = basis.M
    for _ in range(5_000):
        a = random.randrange(M)
        b = random.randrange(M)
        r = ar.sub(basis, basis.encode(a), basis.encode(b))
        assert basis.decode(r) == (a - b) % M


def test_neg_random_large():
    random.seed(0xBABE)
    basis = RNSBasis([65537, 65539, 65543])
    M = basis.M
    for _ in range(5_000):
        a = random.randrange(M)
        r = ar.neg(basis, basis.encode(a))
        assert basis.decode(r) == (-a) % M


def test_distributivity_random():
    """a*(b+c) == a*b + a*c (mod M)."""
    random.seed(0x123456)
    basis = RNSBasis([3, 5, 7, 11, 13])
    M = basis.M
    for _ in range(2_000):
        a = random.randrange(M)
        b = random.randrange(M)
        c = random.randrange(M)
        ea = basis.encode(a)
        eb = basis.encode(b)
        ec = basis.encode(c)
        lhs = ar.mul(basis, ea, ar.add(basis, eb, ec))
        rhs = ar.add(basis, ar.mul(basis, ea, eb), ar.mul(basis, ea, ec))
        assert basis.decode(lhs) == basis.decode(rhs)
