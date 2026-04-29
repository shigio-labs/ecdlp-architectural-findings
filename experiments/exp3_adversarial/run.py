"""Experiment 3: adversarial inputs concentrated in {S} ∈ [0, target_frac).

Strategy: rejection-sample until pool is full, then evaluate estimator
at every (r, use_offset) on the same pool. This both verifies the failure
region matches theory and quantifies the offset variant's robustness.
"""
from __future__ import annotations

import argparse
import json
import random
import time
from math import log2
from pathlib import Path

from rns.basis import RNSBasis
from rns.primes import SECP256K1_P, STANDARD_17_BASIS

from experiments.configs import WIDE_20BIT_BASIS
from experiments.harness import AbortCounters


BASIS_FAMILIES = {
    "standard17": STANDARD_17_BASIS,
    "wide20": WIDE_20BIT_BASIS,
}

# Smaller k_c sweep: adversarial pool generation is expensive, focus on
# the cases that matter for ECDLP (M_core >= p).
K_C_VALUES = (13, 15, 16, 17)
PRECISION_VALUES = (6, 8, 10, 12, 14, 16)
USE_OFFSET_VALUES = (False, True)
TARGET_FRACS = (1e-3, 5e-3, 1e-2, 5e-2)

P = SECP256K1_P


def build_adversarial_pool(
    basis: RNSBasis,
    target_frac: float,
    pool_size: int,
    rng: random.Random,
    max_attempts: int = 200_000_000,
) -> tuple[list[tuple[int, ...]], list[int], int]:
    """Reject-sample until pool has `pool_size` residue tuples with
    {S} < target_frac. Returns (pool, q_true_per_pool_item, total_attempts).

    Computes q_true alongside frac so we don't recompute it later.
    """
    Mi = basis.Mi
    MiInv = basis.MiInv
    moduli = basis.moduli
    M = basis.M
    k = basis.k
    randrange = rng.randrange
    threshold_int = max(1, int(target_frac * M))
    pool: list[tuple[int, ...]] = []
    q_trues: list[int] = []
    attempts = 0
    while len(pool) < pool_size and attempts < max_attempts:
        residues = tuple(randrange(p) for p in moduli)
        s_full = 0
        for i in range(k):
            xi = (residues[i] * MiInv[i]) % moduli[i]
            s_full += xi * Mi[i]
        attempts += 1
        frac_int = s_full % M
        if frac_int < threshold_int:
            pool.append(residues)
            q_trues.append(s_full // M)
    return pool, q_trues, attempts


def evaluate_on_pool(
    basis: RNSBasis,
    pool: list[tuple[int, ...]],
    q_trues: list[int],
    precision_bits: int,
    *,
    use_offset: bool = False,
) -> AbortCounters:
    """Evaluate the estimator on a precomputed adversarial pool."""
    counters = AbortCounters()
    Mi = basis.Mi
    MiInv = basis.MiInv
    moduli = basis.moduli
    k = basis.k
    r = precision_bits
    offset_fp = (k >> 1) if use_offset else 0
    cert_lower = offset_fp
    cert_upper = (1 << r) - k + offset_fp

    for residues, q_true in zip(pool, q_trues):
        s_fp = 0
        for i in range(k):
            xi = (residues[i] * MiInv[i]) % moduli[i]
            s_fp += (xi << r) // moduli[i]
        s_fp += offset_fp
        q_hat = s_fp >> r
        frac_fp = s_fp - (q_hat << r)
        certified = cert_lower <= frac_fp < cert_upper
        counters.record(q_hat - q_true, certified)
    return counters


def run(out_path: Path, pool_size: int, seed: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n_pools = sum(
        len(TARGET_FRACS)
        for fam, primes in BASIS_FAMILIES.items()
        for k_c in K_C_VALUES
        if k_c <= len(primes)
    )
    print(f"Building {n_pools} adversarial pools, {pool_size} samples each.")
    print(f"Output: {out_path}")
    print()

    pool_idx = 0
    t_start = time.perf_counter()
    with out_path.open("w", encoding="utf-8") as f:
        for family_name, family_primes in BASIS_FAMILIES.items():
            for k_c in K_C_VALUES:
                if k_c > len(family_primes):
                    continue
                core = family_primes[:k_c]
                basis = RNSBasis(core)
                M_c = basis.M
                for target_frac in TARGET_FRACS:
                    pool_idx += 1
                    pool_seed = (seed << 24) ^ hash(
                        (family_name, k_c, target_frac)
                    ) & 0xFFFFFFFF
                    rng = random.Random(pool_seed)

                    t_pool = time.perf_counter()
                    pool, q_trues, attempts = build_adversarial_pool(
                        basis, target_frac, pool_size, rng
                    )
                    pool_dt = time.perf_counter() - t_pool

                    if len(pool) < pool_size:
                        print(
                            f"[POOL {pool_idx:>2}/{n_pools}] {family_name} "
                            f"k_c={k_c} target={target_frac:.0e}: only filled "
                            f"{len(pool)}/{pool_size} after {attempts} attempts; "
                            "writing partial."
                        )

                    for r in PRECISION_VALUES:
                        for use_offset in USE_OFFSET_VALUES:
                            counters = evaluate_on_pool(
                                basis, pool, q_trues, r, use_offset=use_offset
                            )
                            record = {
                                "experiment": "exp3_adversarial",
                                "family": family_name,
                                "k_c": k_c,
                                "log2_M_c": log2(M_c),
                                "log2_M_c_minus_log2_p": log2(M_c) - log2(P),
                                "target_frac": target_frac,
                                "pool_size": len(pool),
                                "rejection_attempts": attempts,
                                "rejection_rate": len(pool) / max(attempts, 1),
                                "precision_bits": r,
                                "use_offset": use_offset,
                                "seed": pool_seed,
                                **counters.to_dict(),
                            }
                            f.write(json.dumps(record) + "\n")
                            f.flush()

                            if counters.certified_when_wrong != 0:
                                raise AssertionError(
                                    f"CERTIFICATE BUG: {family_name} k_c={k_c} "
                                    f"tf={target_frac} r={r} offset={use_offset}"
                                )

                    elapsed_total = time.perf_counter() - t_start
                    print(
                        f"[POOL {pool_idx:>2}/{n_pools}] "
                        f"{family_name:>10} k_c={k_c:>2} "
                        f"tf={target_frac:.0e}: pool {len(pool)}/{pool_size} "
                        f"in {pool_dt:>5.1f}s ({attempts:>10} attempts) "
                        f"| total {elapsed_total:>6.1f}s"
                    )

    print()
    print(f"Done. Total elapsed: {time.perf_counter() - t_start:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pool-size", type=int, default=10_000)
    parser.add_argument(
        "--seed", type=lambda s: int(s, 0), default=0xADBEEF
    )
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "data.jsonl"
    )
    args = parser.parse_args()
    run(args.out, args.pool_size, args.seed)
