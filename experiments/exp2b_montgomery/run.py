"""Experiment 2b: Montgomery-style t-distribution abort-rate sweep.

t = (-(a*b) * p^{-1}) mod M_core,  a, b ~ U([0, p))
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
from experiments.harness import measure, montgomery_t


BASIS_FAMILIES = {
    "standard17": STANDARD_17_BASIS,
    "wide20": WIDE_20BIT_BASIS,
}

K_C_VALUES = (12, 13, 14, 15, 16, 17)
PRECISION_VALUES = (6, 8, 10, 12, 14, 16)
USE_OFFSET_VALUES = (False, True)

P = SECP256K1_P


def run(out_path: Path, n_samples: int, seed: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    total = (
        len(BASIS_FAMILIES)
        * len(K_C_VALUES)
        * len(PRECISION_VALUES)
        * len(USE_OFFSET_VALUES)
    )
    print(f"Running {total} configs, {n_samples} samples each.")
    print(f"Output: {out_path}")
    print()

    config_idx = 0
    t_start = time.perf_counter()
    with out_path.open("w", encoding="utf-8") as f:
        for family_name, family_primes in BASIS_FAMILIES.items():
            for k_c in K_C_VALUES:
                if k_c > len(family_primes):
                    continue
                core = family_primes[:k_c]
                basis = RNSBasis(core)
                M_c = basis.M
                for r in PRECISION_VALUES:
                    for use_offset in USE_OFFSET_VALUES:
                        config_idx += 1
                        run_seed = (seed << 16) ^ hash(
                            (family_name, k_c, r, use_offset)
                        ) & 0xFFFFFFFF
                        rng = random.Random(run_seed)
                        sampler = montgomery_t(basis, P, rng)
                        t0 = time.perf_counter()
                        counters = measure(
                            basis,
                            sampler,
                            precision_bits=r,
                            n_samples=n_samples,
                            use_offset=use_offset,
                        )
                        dt = time.perf_counter() - t0

                        record = {
                            "experiment": "exp2b_montgomery",
                            "family": family_name,
                            "k_c": k_c,
                            "log2_M_c": log2(M_c),
                            "log2_M_c_minus_log2_p": log2(M_c) - log2(P),
                            "precision_bits": r,
                            "use_offset": use_offset,
                            "n_samples": n_samples,
                            "seed": run_seed,
                            "elapsed_seconds": round(dt, 3),
                            **counters.to_dict(),
                        }
                        f.write(json.dumps(record) + "\n")
                        f.flush()

                        if counters.certified_when_wrong != 0:
                            raise AssertionError(
                                f"CERTIFICATE BUG: {family_name} k_c={k_c} "
                                f"r={r} offset={use_offset}"
                            )

                        elapsed_total = time.perf_counter() - t_start
                        print(
                            f"[{config_idx:>3}/{total}] "
                            f"{family_name:>10} k_c={k_c:>2} "
                            f"r={r:>2} offset={int(use_offset)} | "
                            f"abort={counters.abort_rate:.6f} "
                            f"({counters.aborts:>5}/{n_samples}) | "
                            f"{dt:>5.1f}s  total {elapsed_total:>6.1f}s"
                        )

    print()
    print(f"Done. Total elapsed: {time.perf_counter() - t_start:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-samples", type=int, default=1_000_000)
    parser.add_argument(
        "--seed", type=lambda s: int(s, 0), default=0xCAFE_F00D
    )
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "data.jsonl"
    )
    args = parser.parse_args()
    run(args.out, args.n_samples, args.seed)
