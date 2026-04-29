"""Experiment 6: phase-transition curve for `uniform_in_p` distribution.

Vary basis product M_c finely between log2(M_c/p) = 0 and ~16 by holding
the first 16 standard primes (above 2^16) fixed and varying a single
extra prime added on top. Measures abort rate as a function of T = log2(M_c/p).
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

from experiments.harness import measure, uniform_in_range


P = SECP256K1_P

# Extra primes spanning log2(p_extra) from ~1 to ~16. All are coprime to
# the first-16 standard primes (which are all > 2^16).
EXTRA_PRIMES = [
    2, 3, 5, 11, 23, 47, 97, 193, 389, 773, 1543, 3079, 6151,
    12289, 24593, 49157,
]

PRECISION_VALUES = (12, 14, 16)
USE_OFFSET_VALUES = (False, True)


def run(out_path: Path, n_samples: int, seed: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    base16 = list(STANDARD_17_BASIS[:16])

    # Also include (no extra) and (full standard17) as endpoints for sanity.
    configs: list[tuple[str, list[int]]] = []
    configs.append(("base16_only", base16))
    for ex in EXTRA_PRIMES:
        configs.append((f"base16+{ex}", base16 + [ex]))
    configs.append(("standard17", list(STANDARD_17_BASIS)))

    total = len(configs) * len(PRECISION_VALUES) * len(USE_OFFSET_VALUES)
    print(f"Sweep: {len(configs)} basis configs x {len(PRECISION_VALUES)} r "
          f"x {len(USE_OFFSET_VALUES)} offset = {total} cells")
    print(f"Sampler: uniform_in_p with secp256k1 p, n_samples={n_samples}")
    print()

    config_idx = 0
    t_start = time.perf_counter()
    with out_path.open("w", encoding="utf-8") as f:
        for name, primes in configs:
            basis = RNSBasis(primes)
            log2_T = log2(basis.M) - log2(P)
            for r in PRECISION_VALUES:
                for use_offset in USE_OFFSET_VALUES:
                    config_idx += 1
                    run_seed = (seed << 16) ^ hash(
                        (name, r, use_offset)
                    ) & 0xFFFFFFFF
                    rng = random.Random(run_seed)
                    sampler = uniform_in_range(basis, P, rng)
                    t0 = time.perf_counter()
                    counters = measure(
                        basis, sampler, precision_bits=r,
                        n_samples=n_samples, use_offset=use_offset,
                    )
                    dt = time.perf_counter() - t0
                    record = {
                        "experiment": "exp6_threshold",
                        "config_name": name,
                        "k_c": basis.k,
                        "moduli": list(basis.moduli),
                        "log2_M_c": log2(basis.M),
                        "T_log2_Mc_over_p": log2_T,
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
                            f"CERTIFICATE BUG: {name} r={r} offset={use_offset}"
                        )

                    print(f"[{config_idx:>3}/{total}] {name:>15} k={basis.k} T={log2_T:>+6.2f} "
                          f"r={r} off={int(use_offset)} | abort={counters.abort_rate:.5f}  "
                          f"({dt:.1f}s)")

    print()
    print(f"Done. Total {time.perf_counter() - t_start:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-samples", type=int, default=200_000)
    parser.add_argument(
        "--seed", type=lambda s: int(s, 0), default=0xCC11FF
    )
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "data.jsonl"
    )
    args = parser.parse_args()
    run(args.out, args.n_samples, args.seed)
