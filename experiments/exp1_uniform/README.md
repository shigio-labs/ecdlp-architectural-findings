# Experiment 1: Uniform distribution

## Hypothesis

The Kawamura-Kapoor estimator's abort rate, when residues are drawn uniformly from the product space (equivalently x ~ U([0, M_core))), is determined by precision `r` and basis size `k_c` according to the model

    abort_rate ≈ k_c * 2^{-r}    (no-offset)
    abort_rate ≈ k_c * 2^{-r}    (offset; same total slop, different sign distribution)

If empirical results are wildly off from this model, our implementation has a bug.

This experiment establishes a **lower bound for what's achievable**: any non-uniform distribution (post-multiplication, adversarial) should have ≥ this abort rate; if a structured distribution has *lower* abort rate the analysis must explain why.

## Methodology

Two basis families:

1. **standard17** — the plan's literal baseline (17 primes above 2^16, ~17 bits each). For k_c < 16 the core's product is below secp256k1 p, so this configuration has limited direct ECDLP relevance — we run it to match the plan's parameter grid.
2. **wide20** — 20 primes above 2^20 (~20 bits each), so k_c = 13 already gives M_core > p. ECDLP-relevant.

Sweep:
- `k_c` ∈ {12, 13, 14, 15, 16, 17}
- `precision_bits r` ∈ {6, 8, 10, 12, 14, 16}
- `use_offset` ∈ {false, true}
- `n_samples` = 1,000,000 per config (lower bound for resolving rates ~1e-4)

Total: 2 × 6 × 6 × 2 = 144 configs.

Sampler: `uniform_in_M(core_basis, rng)` — residues drawn directly per-modulus.

## Outputs

* `data.jsonl` — one JSON object per config, with full counter dump (counts, diff distribution, certified flags).
* `RESULTS.md` (in the project root after Phase 4) — the cross-experiment summary.

## Sanity guards

For every config we verify:
* `certified_when_wrong == 0` (would indicate certificate bug).
* For `r` such that `k_c * 2^-r < 1`: no-offset diff distribution lives in `{-1, 0}` (asymmetric).
* For `r >= 18` (not in the main sweep, separately): expect zero aborts.

## How to reproduce

```bash
.venv/Scripts/python.exe -m experiments.exp1_uniform.run --n-samples 1000000 --seed 0xC0FFEE
```
