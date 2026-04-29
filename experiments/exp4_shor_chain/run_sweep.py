"""Sweep multiple (k_c, r, use_offset) chain configs in one run."""
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
from experiments.exp4_shor_chain.run import run_chain


BASIS_FAMILIES = {
    "standard17": STANDARD_17_BASIS,
    "wide20": WIDE_20BIT_BASIS,
}

# (family, k_c, r, use_offset)
SWEEP_CONFIGS = [
    ("wide20", 13, 10, True),
    ("wide20", 13, 12, True),
    ("wide20", 13, 14, True),
    ("wide20", 13, 16, True),
    ("wide20", 13, 14, False),
    ("wide20", 15, 14, True),
    ("wide20", 16, 14, True),
    ("standard17", 16, 14, True),
    ("standard17", 16, 14, False),
]

P = SECP256K1_P


def run(out_path: Path, n_chains: int, chain_length: int, seed: int) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Sweep: {len(SWEEP_CONFIGS)} configs x {n_chains} chains x {chain_length} steps")
    print()

    t_start = time.perf_counter()
    with out_path.open("w", encoding="utf-8") as f:
        for idx, (family, k_c, precision_bits, use_offset) in enumerate(SWEEP_CONFIGS, 1):
            primes = BASIS_FAMILIES[family][:k_c]
            basis = RNSBasis(primes)
            run_seed = (seed << 16) ^ hash(
                (family, k_c, precision_bits, use_offset)
            ) & 0xFFFFFFFF
            rng = random.Random(run_seed)
            t0 = time.perf_counter()
            survived = 0
            aborted_at = []
            for _ in range(n_chains):
                ok, steps = run_chain(
                    basis, chain_length, precision_bits, use_offset, rng
                )
                if ok:
                    survived += 1
                else:
                    aborted_at.append(steps)
            dt = time.perf_counter() - t0
            survival_rate = survived / n_chains
            per_step = (1 - survival_rate ** (1 / chain_length)) if survival_rate > 0 else float("nan")
            record = {
                "experiment": "exp4_shor_chain_sweep",
                "family": family,
                "k_c": k_c,
                "log2_M_c": log2(basis.M),
                "log2_M_c_minus_log2_p": log2(basis.M) - log2(P),
                "precision_bits": precision_bits,
                "use_offset": use_offset,
                "chain_length": chain_length,
                "n_chains": n_chains,
                "seed": run_seed,
                "survived": survived,
                "survival_rate": survival_rate,
                "implied_per_step_abort": per_step,
                "median_abort_step": (
                    sorted(aborted_at)[len(aborted_at) // 2] if aborted_at else None
                ),
                "elapsed_seconds": round(dt, 2),
            }
            f.write(json.dumps(record) + "\n")
            f.flush()
            elapsed = time.perf_counter() - t_start
            print(
                f"[{idx}/{len(SWEEP_CONFIGS)}] {family} k_c={k_c} r={precision_bits} "
                f"offset={int(use_offset)}: survived {survived}/{n_chains} "
                f"= {survival_rate:.4f}, per-step {per_step:.6f}  "
                f"({dt:.1f}s, total {elapsed:.1f}s)"
            )

    print()
    print(f"Done. Total {time.perf_counter() - t_start:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-chains", type=int, default=2_000)
    parser.add_argument("--chain-length", type=int, default=512)
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0xDEADC0DE)
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "data.jsonl"
    )
    args = parser.parse_args()
    run(args.out, args.n_chains, args.chain_length, args.seed)
