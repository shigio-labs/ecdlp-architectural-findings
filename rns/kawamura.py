"""Kawamura-Kapoor base-extension quotient estimator.

For an RNSBasis with moduli (p_1, ..., p_k) and product M, given residues
x_i = x mod p_i representing some x in [0, M), the CRT identity is

    x = sum_i xi_i * M_i  -  q * M

where M_i = M / p_i, xi_i = (x_i * |M_i|^{-1}) mod p_i in [0, p_i),
and q = floor(sum_i xi_i / p_i) in {0, 1, ..., k - 1}.

Recovering q exactly requires computing the sum at full precision; the
Kawamura-Kapoor estimator approximates xi_i / p_i in fixed point with r
fractional bits and infers q with a small probability of error. The error
is asymmetric (q_hat in {q-1, q}) without an offset and symmetric
(q_hat in {q-1, q, q+1}) when a centering offset of approximately
k * 2^-(r+1) is added before flooring.
"""
from __future__ import annotations

from typing import Sequence

from .basis import RNSBasis


def true_quotient(residues: Sequence[int], basis: RNSBasis) -> int:
    """Exact q = floor(sum_i xi_i / p_i), computed without truncation.

    Brute-force reference for cross-checking the Kawamura estimator.
    """
    xi = basis.xi(residues)
    s = 0
    for i in range(basis.k):
        s += xi[i] * basis.Mi[i]
    return s // basis.M


def kawamura_estimate(
    residues: Sequence[int],
    basis: RNSBasis,
    precision_bits: int,
    *,
    use_offset: bool = False,
) -> tuple[int, bool]:
    """Estimate the base-extension quotient via Kawamura-Kapoor fixed-point.

    Args:
        residues: residues in ``basis``.
        basis: an :class:`RNSBasis` instance.
        precision_bits: r >= 1, bits of precision for alpha_i ~ xi_i / p_i.
        use_offset: if True, add a centering offset of floor(k/2) / 2^r
            before flooring. The offset symmetrizes the truncation error so
            errors land in {-1, 0, +1} instead of {-1, 0}.

    Returns:
        ``(q_hat, is_provably_correct)``. When ``is_provably_correct`` is True,
        ``q_hat`` is guaranteed to equal :func:`true_quotient`; the margin
        is conservative, so False does not imply ``q_hat`` is incorrect.
    """
    if precision_bits < 1:
        raise ValueError("precision_bits must be >= 1")
    r = precision_bits
    k = basis.k
    xi = basis.xi(residues)

    # alpha_i_fp = floor(2^r * xi_i / p_i); s_fp accumulates hat_S in units of 2^-r.
    s_fp = 0
    for xi_i, p in zip(xi, basis.moduli):
        s_fp += (xi_i << r) // p

    if use_offset:
        offset_fp = k >> 1  # floor(k/2) in units of 2^-r
        s_fp += offset_fp
    else:
        offset_fp = 0

    q_hat = s_fp >> r
    frac_fp = s_fp - (q_hat << r)

    # Conservative provable-correctness margin.
    # Truncation error epsilon in [0, k * 2^-r); shifted by delta this gives
    # eta in [-delta, k*2^-r - delta]. T := hat_S + delta has true integer
    # part equal to floor(S) when {T} in [delta, 1 - k*2^-r + delta), i.e.,
    # frac_fp in [offset_fp, 2^r - k + offset_fp).
    lower = offset_fp
    upper = (1 << r) - k + offset_fp
    is_correct = lower <= frac_fp < upper
    return q_hat, is_correct
