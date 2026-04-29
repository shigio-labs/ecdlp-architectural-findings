"""Experiment 5: certificate-False distribution across chain steps.

Runs a multiplication chain at the recommended config and records, at each
step, whether the q-estimate matched ground truth and whether the certificate
was True. Reports:
  - histogram of certificate-False counts per chain (vs Poisson prediction)
  - histogram of abort counts per chain
  - lag-1 autocorrelation of {S} across the chain
"""
from __future__ import annotations

import argparse
import json
import random
import time
from math import exp, factorial, log2
from pathlib import Path

from rns.basis import RNSBasis
from rns.primes import SECP256K1_P

from experiments.configs import WIDE_20BIT_BASIS


def run_chain_with_records(
    basis: RNSBasis,
    chain_length: int,
    precision_bits: int,
    use_offset: bool,
    rng: random.Random,
) -> tuple[list[bool], list[bool], list[float]]:
    """Run a chain to completion (no early exit) and record per-step
    (correct, certified, frac_S) for every step.

    `c_{i+1} = c_i * b_i` componentwise, with random `b_i` per step.
    The estimator's wrong q-values are NOT propagated — `c` is the actual
    residue product. We are measuring the *intrinsic* certificate
    distribution of the chain's residue trajectory, not error
    propagation."""
    moduli = basis.moduli
    Mi = basis.Mi
    MiInv = basis.MiInv
    M = basis.M
    k = basis.k
    r = precision_bits
    offset_fp = (k >> 1) if use_offset else 0
    cert_lower = offset_fp
    cert_upper = (1 << r) - k + offset_fp
    randrange = rng.randrange

    a = tuple(randrange(p) for p in moduli)
    correct_seq: list[bool] = []
    cert_seq: list[bool] = []
    frac_S_seq: list[float] = []

    for _ in range(chain_length):
        b = tuple(randrange(p) for p in moduli)
        c = tuple((a[i] * b[i]) % moduli[i] for i in range(k))
        s_full = 0
        s_fp = 0
        for i in range(k):
            xi = (c[i] * MiInv[i]) % moduli[i]
            s_full += xi * Mi[i]
            s_fp += (xi << r) // moduli[i]
        q_true = s_full // M
        frac_S = (s_full - q_true * M) / M
        s_fp += offset_fp
        q_hat = s_fp >> r
        frac_fp = s_fp - (q_hat << r)
        certified = cert_lower <= frac_fp < cert_upper
        correct_seq.append(q_hat == q_true)
        cert_seq.append(certified)
        frac_S_seq.append(frac_S)
        a = c
    return correct_seq, cert_seq, frac_S_seq


def poisson_pmf(k: int, lam: float) -> float:
    return exp(-lam) * lam**k / factorial(k)


def run(out_path: Path, n_chains: int, chain_length: int, seed: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    family = "wide20"
    k_c = 13
    precision_bits = 14
    use_offset = True
    primes = WIDE_20BIT_BASIS[:k_c]
    basis = RNSBasis(primes)

    print(f"Recommended config: {family} k_c={k_c} r={precision_bits} offset={use_offset}")
    print(f"Running {n_chains} chains x {chain_length} steps")
    print()

    rng = random.Random(seed)
    abort_per_chain: list[int] = []  # # of steps where q_hat != q_true
    false_cert_per_chain: list[int] = []  # # of steps with certified=False
    all_lag1_corr_sum = 0.0
    all_lag1_corr_n = 0
    var_sum = 0.0
    var_n = 0

    t0 = time.perf_counter()
    for chain_idx in range(n_chains):
        correct, cert, frac_S = run_chain_with_records(
            basis, chain_length, precision_bits, use_offset, rng
        )
        n_aborts = sum(1 for c in correct if not c)
        n_false = sum(1 for c in cert if not c)
        abort_per_chain.append(n_aborts)
        false_cert_per_chain.append(n_false)

        # Lag-1 autocorrelation of frac_S within this chain.
        n = len(frac_S)
        mean = sum(frac_S) / n
        var = sum((x - mean) ** 2 for x in frac_S) / n
        if var > 0:
            cov = sum(
                (frac_S[i] - mean) * (frac_S[i + 1] - mean) for i in range(n - 1)
            ) / (n - 1)
            all_lag1_corr_sum += cov / var
            all_lag1_corr_n += 1
        var_sum += var
        var_n += 1

        if (chain_idx + 1) % 500 == 0:
            print(f"  chain {chain_idx+1}/{n_chains}  ({time.perf_counter() - t0:.0f}s)")

    elapsed = time.perf_counter() - t0
    print(f"Done in {elapsed:.0f}s")

    # Empirical histograms
    def histogram(counts: list[int], max_bin: int = 8) -> dict[int, int]:
        h: dict[int, int] = {}
        for c in counts:
            key = c if c < max_bin else max_bin
            h[key] = h.get(key, 0) + 1
        return h

    abort_hist = histogram(abort_per_chain)
    false_hist = histogram(false_cert_per_chain)

    # Predict from observed mean
    abort_lam = sum(abort_per_chain) / n_chains
    false_lam = sum(false_cert_per_chain) / n_chains

    # KS-style chi-square goodness of fit vs Poisson
    def chi_square_poisson(hist: dict[int, int], lam: float, n: int) -> float:
        chi2 = 0.0
        for k, observed in hist.items():
            if k == 8:  # last bin is "8 or more"
                expected = n * (1 - sum(poisson_pmf(j, lam) for j in range(8)))
            else:
                expected = n * poisson_pmf(k, lam)
            if expected > 5:
                chi2 += (observed - expected) ** 2 / expected
        return chi2

    abort_chi2 = chi_square_poisson(abort_hist, abort_lam, n_chains)
    false_chi2 = chi_square_poisson(false_hist, false_lam, n_chains)

    avg_lag1 = all_lag1_corr_sum / all_lag1_corr_n if all_lag1_corr_n else float("nan")
    avg_var = var_sum / var_n if var_n else float("nan")

    record = {
        "experiment": "exp5_cluster",
        "family": family,
        "k_c": k_c,
        "precision_bits": precision_bits,
        "use_offset": use_offset,
        "chain_length": chain_length,
        "n_chains": n_chains,
        "seed": seed,
        "elapsed_seconds": round(elapsed, 1),
        "abort_per_chain_mean": abort_lam,
        "false_cert_per_chain_mean": false_lam,
        "abort_histogram": {str(k): v for k, v in sorted(abort_hist.items())},
        "false_cert_histogram": {str(k): v for k, v in sorted(false_hist.items())},
        "abort_chi2_vs_poisson": abort_chi2,
        "false_chi2_vs_poisson": false_chi2,
        "lag1_autocorrelation_frac_S": avg_lag1,
        "mean_variance_frac_S": avg_var,
        "max_aborts_in_one_chain": max(abort_per_chain) if abort_per_chain else 0,
        "max_false_in_one_chain": max(false_cert_per_chain) if false_cert_per_chain else 0,
    }
    with out_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(record, indent=2) + "\n")

    print()
    print(f"Mean aborts per chain: {abort_lam:.4f} (= per-step rate {abort_lam/chain_length:.2e})")
    print(f"Mean false-certs per chain: {false_lam:.4f} (= per-step rate {false_lam/chain_length:.2e})")
    print(f"Lag-1 autocorrelation of frac_S: {avg_lag1:.4f} (Bernoulli expects ~ 0, |z| < 0.05)")
    print()
    print(f"{'k':>3} | {'abort_obs':>10} {'abort_poiss':>12} | {'false_obs':>10} {'false_poiss':>12}")
    print("-" * 60)
    for k in range(9):
        ao = abort_hist.get(k, 0)
        ap = n_chains * poisson_pmf(k, abort_lam) if k < 8 else n_chains * (
            1 - sum(poisson_pmf(j, abort_lam) for j in range(8))
        )
        fo = false_hist.get(k, 0)
        fp = n_chains * poisson_pmf(k, false_lam) if k < 8 else n_chains * (
            1 - sum(poisson_pmf(j, false_lam) for j in range(8))
        )
        label = f"{k}" if k < 8 else "8+"
        print(f"{label:>3} | {ao:>10} {ap:>12.1f} | {fo:>10} {fp:>12.1f}")
    print()
    print(f"chi^2 abort vs Poisson: {abort_chi2:.2f}")
    print(f"chi^2 false vs Poisson: {false_chi2:.2f}")
    print(f"(reference: chi^2 with 5 df at 0.05 sig = 11.07; smaller = no evidence against Poisson)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-chains", type=int, default=2_000)
    parser.add_argument("--chain-length", type=int, default=512)
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0xCC1057E2)
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "data.json"
    )
    args = parser.parse_args()
    run(args.out, args.n_chains, args.chain_length, args.seed)
