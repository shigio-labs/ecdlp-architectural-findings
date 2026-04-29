"""Experiment 4: simulate Shor-style operation chains.

Each "step" performs one multiplication followed by a Kawamura base extension.
If any step's q-estimate is wrong, the chain aborts. The chain feeds the output
of step `i` into step `i+1` to model state propagation.

Usage:
    .venv/Scripts/python.exe -m experiments.exp4_shor_chain.run \
        --family wide20 --k-c 13 --precision 14 --offset \
        --n-chains 1000 --chain-length 512
"""
from __future__ import annotations

import argparse
import json
import random
import time
from math import log2, log
from pathlib import Path

from rns.basis import RNSBasis
from rns.primes import SECP256K1_P, STANDARD_17_BASIS

from experiments.configs import WIDE_20BIT_BASIS


BASIS_FAMILIES = {
    "standard17": STANDARD_17_BASIS,
    "wide20": WIDE_20BIT_BASIS,
}

P = SECP256K1_P


def step_check(
    basis: RNSBasis,
    a_residues: tuple[int, ...],
    b_residues: tuple[int, ...],
    precision_bits: int,
    use_offset: bool,
) -> tuple[bool, tuple[int, ...]]:
    """Compute c = a * b componentwise, then run Kawamura q estimate.

    Returns (success, c_residues). Success = q_hat == q_true.
    """
    moduli = basis.moduli
    Mi = basis.Mi
    MiInv = basis.MiInv
    M = basis.M
    k = basis.k
    r = precision_bits
    offset_fp = (k >> 1) if use_offset else 0

    c_residues = tuple((a_residues[i] * b_residues[i]) % moduli[i] for i in range(k))

    s_full = 0
    s_fp = 0
    for i in range(k):
        xi = (c_residues[i] * MiInv[i]) % moduli[i]
        s_full += xi * Mi[i]
        s_fp += (xi << r) // moduli[i]
    q_true = s_full // M
    s_fp += offset_fp
    q_hat = s_fp >> r
    return q_hat == q_true, c_residues


def run_chain(
    basis: RNSBasis,
    chain_length: int,
    precision_bits: int,
    use_offset: bool,
    rng: random.Random,
) -> tuple[bool, int]:
    """Run one chain. Returns (survived, steps_completed)."""
    moduli = basis.moduli
    randrange = rng.randrange
    a_residues = tuple(randrange(p) for p in moduli)
    for step in range(chain_length):
        b_residues = tuple(randrange(p) for p in moduli)
        ok, a_residues = step_check(
            basis, a_residues, b_residues, precision_bits, use_offset
        )
        if not ok:
            return False, step + 1
    return True, chain_length


def run(
    out_path: Path,
    family: str,
    k_c: int,
    precision_bits: int,
    use_offset: bool,
    n_chains: int,
    chain_length: int,
    seed: int,
) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    primes = BASIS_FAMILIES[family][:k_c]
    basis = RNSBasis(primes)
    rng = random.Random(seed)

    print(f"family={family} k_c={k_c} precision={precision_bits} offset={use_offset}")
    print(f"chain_length={chain_length}, n_chains={n_chains}")
    print(f"log2(M_c) = {log2(basis.M):.2f}")
    print()

    survived = 0
    aborted_steps = []
    t0 = time.perf_counter()
    for chain_idx in range(n_chains):
        ok, steps = run_chain(
            basis, chain_length, precision_bits, use_offset, rng
        )
        if ok:
            survived += 1
        else:
            aborted_steps.append(steps)
        if (chain_idx + 1) % max(n_chains // 20, 1) == 0:
            elapsed = time.perf_counter() - t0
            rate_so_far = survived / (chain_idx + 1)
            print(f"  chain {chain_idx+1}/{n_chains}: survival={rate_so_far:.4f}  ({elapsed:.1f}s)")

    elapsed = time.perf_counter() - t0
    survival_rate = survived / n_chains if n_chains else 0
    # Implied per-step abort rate: if survival = (1-p)^L, p = 1 - survival^(1/L).
    if survival_rate > 0:
        per_step_p = 1 - survival_rate ** (1 / chain_length)
    else:
        per_step_p = float("nan")
    median_abort_step = (
        sorted(aborted_steps)[len(aborted_steps) // 2]
        if aborted_steps
        else None
    )

    record = {
        "experiment": "exp4_shor_chain",
        "family": family,
        "k_c": k_c,
        "moduli": list(primes),
        "log2_M_c": log2(basis.M),
        "log2_M_c_minus_log2_p": log2(basis.M) - log2(P),
        "precision_bits": precision_bits,
        "use_offset": use_offset,
        "chain_length": chain_length,
        "n_chains": n_chains,
        "seed": seed,
        "survived": survived,
        "survival_rate": survival_rate,
        "implied_per_step_abort": per_step_p,
        "median_abort_step": median_abort_step,
        "elapsed_seconds": round(elapsed, 2),
    }
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    print()
    print(f"Survived: {survived}/{n_chains} = {survival_rate:.4f}")
    print(f"Implied per-step abort: {per_step_p:.6f}")
    print(f"Total elapsed: {elapsed:.1f}s")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--family", choices=list(BASIS_FAMILIES), required=True)
    parser.add_argument("--k-c", type=int, required=True)
    parser.add_argument("--precision", type=int, required=True)
    parser.add_argument("--offset", action="store_true")
    parser.add_argument("--n-chains", type=int, default=1_000)
    parser.add_argument("--chain-length", type=int, default=512)
    parser.add_argument("--seed", type=lambda s: int(s, 0), default=0xCAFEBAFE)
    parser.add_argument(
        "--out", type=Path, default=Path(__file__).parent / "data.jsonl"
    )
    args = parser.parse_args()
    run(
        args.out,
        args.family,
        args.k_c,
        args.precision,
        args.offset,
        args.n_chains,
        args.chain_length,
        args.seed,
    )
