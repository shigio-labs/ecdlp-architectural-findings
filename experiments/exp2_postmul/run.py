"""Experiment 2: post-multiplication distribution abort-rate sweep.

Two distributions:
    product_modMc: x = (a*b) mod M_core, a, b ~ U([0, p))
    product_modp:  x = (a*b) mod p (only when M_core >= p)
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
from experiments.harness import measure, product_mod_p, product_with_modM_wrap


BASIS_FAMILIES = {
    "standard17": STANDARD_17_BASIS,
    "wide20": WIDE_20BIT_BASIS,
}

K_C_VALUES = (12, 13, 14, 15, 16, 17)
PRECISION_VALUES = (6, 8, 10, 12, 14, 16)
USE_OFFSET_VALUES = (False, True)
DISTRIBUTIONS = ("product_modMc", "product_modp")

P = SECP256K1_P


def make_sampler(name: str, basis: RNSBasis, rng: random.Random):
    if name == "product_modMc":
        return product_with_modM_wrap(basis, P, rng)
    if name == "product_modp":
        return product_mod_p(basis, P, rng)
    raise ValueError(f"unknown distribution {name}")


def run(out_path: Path, n_samples: int, seed: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Count viable configs (skip product_modp when M_core < p).
    total = 0
    for family_name, primes in BASIS_FAMILIES.items():
        for k_c in K_C_VALUES:
            if k_c > len(primes):
                continue
            from math import prod as _prod
            M_c = _prod(primes[:k_c])
            for dist in DISTRIBUTIONS:
                if dist == "product_modp" and M_c < P:
                    continue
                total += len(PRECISION_VALUES) * len(USE_OFFSET_VALUES)
    print(f"Running {total} configs, {n_samples} samples each "
          f"(~{total * n_samples * 7e-6:.0f}s estimate)")
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
                for dist in DISTRIBUTIONS:
                    if dist == "product_modp" and M_c < P:
                        continue
                    for r in PRECISION_VALUES:
                        for use_offset in USE_OFFSET_VALUES:
                            config_idx += 1
                            run_seed = (seed << 16) ^ hash(
                                (family_name, k_c, dist, r, use_offset)
                            ) & 0xFFFFFFFF
                            rng = random.Random(run_seed)
                            sampler = make_sampler(dist, basis, rng)
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
                                "experiment": "exp2_postmul",
                                "family": family_name,
                                "k_c": k_c,
                                "moduli": list(core),
                                "log2_M_c": log2(M_c),
                                "log2_M_c_minus_log2_p": log2(M_c) - log2(P),
                                "distribution": dist,
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
                                    f"dist={dist} r={r} offset={use_offset}: "
                                    f"certified_when_wrong={counters.certified_when_wrong}"
                                )

                            elapsed_total = time.perf_counter() - t_start
                            print(
                                f"[{config_idx:>3}/{total}] "
                                f"{family_name:>10} k_c={k_c:>2} "
                                f"{dist:>16} r={r:>2} offset={int(use_offset)} | "
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
        "--seed", type=lambda s: int(s, 0), default=0xBADCAFE
    )
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "data.jsonl"
    )
    args = parser.parse_args()
    run(args.out, args.n_samples, args.seed)
