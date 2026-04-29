"""Δ-mini empirical sanity check.

Generate 1e4 random 256-bit scalars (top bit set), run affine Montgomery
ladder for kG on secp256k1, record bit-size of (x_R1 − x_R0) mod p at
every one of the 256 steps. Aggregate into a histogram and quantile
summary. Predicted result (per THEORY.md): essentially uniform on [0, p),
with mean / median / 99th-percentile bit-size all ≈ 255.

Decision logic (per user-confirmed plan):
  99-percentile ≥ 254 → confirms theory → GATE FAIL → γ
  99-percentile in [200, 254) → unexpected, do not pivot to γ yet
  99-percentile < 200 → big surprise, theory was wrong somewhere
"""
from __future__ import annotations

from delta._encoding import _ as _utf8_setup  # noqa: F401  # Windows cp1251 fix

import argparse
import json
import random
import time
from collections import Counter
from pathlib import Path

from delta.secp256k1 import P, montgomery_ladder_diffs


def run(n_scalars: int, seed: int, n_bits: int = 256) -> dict:
    rng = random.Random(seed)
    bit_size_hist: Counter[int] = Counter()
    n_steps_total = 0
    t0 = time.perf_counter()
    for scalar_idx in range(n_scalars):
        # Random 256-bit scalar with top bit forced on
        k = (1 << (n_bits - 1)) | rng.getrandbits(n_bits - 1)
        diffs = montgomery_ladder_diffs(k, n_bits=n_bits)
        for d in diffs:
            bit_size_hist[d.bit_length()] += 1
            n_steps_total += 1
        if (scalar_idx + 1) % max(n_scalars // 20, 1) == 0:
            elapsed = time.perf_counter() - t0
            rate = (scalar_idx + 1) / elapsed
            print(f"  {scalar_idx + 1:>5}/{n_scalars}  ({elapsed:>5.1f}s, {rate:.1f}/s)")
    elapsed = time.perf_counter() - t0

    # Compute quantile-style stats from the histogram
    sizes = sorted(bit_size_hist.keys())
    cum = 0
    cum_to_size: list[tuple[int, int]] = []
    for s in sizes:
        cum += bit_size_hist[s]
        cum_to_size.append((cum, s))

    def quantile(q: float) -> int:
        target = q * n_steps_total
        for cum_val, sz in cum_to_size:
            if cum_val >= target:
                return sz
        return sizes[-1]

    mean = sum(s * c for s, c in bit_size_hist.items()) / n_steps_total
    median = quantile(0.5)
    p99 = quantile(0.99)
    p999 = quantile(0.999)
    minimum = sizes[0]
    maximum = sizes[-1]

    log2p_floor = int(P.bit_length()) - 1  # 255 for secp256k1

    # Theoretical reference: uniform on [0, p) ≈ uniform on [0, 2^256).
    # P(bit_length == 256) = (P − 2^255) / P ≈ ~0.5 (less than half because P just below 2^256).
    # Using exact P:
    n_le_2_to_256 = (1 << 256)
    p_eq_256 = max(0, P - (1 << 255)) / P  # bit-length 256 means value in [2^255, P)
    p_eq_255 = (1 << 255) - (1 << 254)  # values in [2^254, 2^255) → length 255
    p_eq_255 = p_eq_255 / P
    # Just compute predicted full distribution for the report
    predicted = {}
    for b in range(n_bits + 1):
        if b == 0:
            # Single value 0
            predicted[b] = 1 / P
        else:
            lo = 1 << (b - 1)
            hi = min(1 << b, P)
            if hi > lo:
                predicted[b] = (hi - lo) / P
            else:
                predicted[b] = 0.0

    pred_p99 = None
    cum_pred = 0.0
    for b in sorted(predicted.keys()):
        cum_pred += predicted[b]
        if pred_p99 is None and cum_pred >= 0.99:
            pred_p99 = b
            break
    pred_mean = sum(b * pp for b, pp in predicted.items())

    print()
    print(f"Total ladder steps: {n_steps_total} ({n_scalars} scalars x {n_bits} steps)")
    print(f"Elapsed: {elapsed:.1f}s ({n_steps_total/elapsed:.0f} steps/s)")
    print()
    print(f"{'metric':>20} | {'observed':>10} | {'predicted (uniform)':>24}")
    print("-" * 60)
    print(f"{'mean bit-size':>20} | {mean:>10.4f} | {pred_mean:>24.4f}")
    print(f"{'median bit-size':>20} | {median:>10} | (~256)")
    print(f"{'99th percentile':>20} | {p99:>10} | {pred_p99:>24}")
    print(f"{'99.9th percentile':>20} | {p999:>10} | (~256 or 255)")
    print(f"{'min bit-size':>20} | {minimum:>10} | (rare; ~248 expected at 1e6)")
    print(f"{'max bit-size':>20} | {maximum:>10} | 256")
    print()
    print(f"Histogram (counts of bit-size):")
    for s in sorted(bit_size_hist.keys()):
        bar_units = max(1, int(50 * bit_size_hist[s] / max(bit_size_hist.values())))
        share = bit_size_hist[s] / n_steps_total
        print(f"  bit-size={s:>3}: {bit_size_hist[s]:>9} ({share*100:>5.2f}%)  {'#' * min(bar_units, 50)}")

    # Gate decision
    if p99 >= 254:
        gate_decision = "FAIL (confirms theory: Δ has full bit-size, no compression)"
    elif p99 >= 200:
        gate_decision = "UNEXPECTED — theory partially contradicted"
    else:
        gate_decision = "BIG SURPRISE — theory wrong somewhere; investigate"

    print()
    print(f"Gate decision: {gate_decision}")

    return {
        "experiment": "delta_mini",
        "n_scalars": n_scalars,
        "n_bits_per_scalar": n_bits,
        "n_steps_total": n_steps_total,
        "seed": seed,
        "elapsed_seconds": round(elapsed, 2),
        "mean_bit_size": mean,
        "median_bit_size": median,
        "p99_bit_size": p99,
        "p999_bit_size": p999,
        "min_bit_size": minimum,
        "max_bit_size": maximum,
        "predicted_mean_uniform": pred_mean,
        "predicted_p99_uniform": pred_p99,
        "histogram": dict(sorted(bit_size_hist.items())),
        "gate_decision": gate_decision,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-scalars", type=int, default=10_000)
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0xDE17A4)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "delta_mini.json")
    args = parser.parse_args()
    result = run(args.n_scalars, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
    print(f"\nResult saved to {args.out}")
