# Experiment 3: Adversarial inputs near the failure boundary

## Hypothesis

The Kawamura no-offset abort happens iff {S} ∈ [0, k·2⁻ʳ); the offset variant has a similarly thin failure window. Uniform inputs hit this region with probability ≈ k·2⁻ʳ. **What if the algorithm produces inputs that concentrate near the boundary?**

This experiment generates "adversarial" inputs by rejection-sampling residues until `{S}` is below a target threshold (deeper than the natural failure region). Reported: the abort rate on such adversarial inputs at every (r, use_offset) — i.e., the conditional rate "given that {S} < threshold, what fraction of these abort?"

This bounds the worst-case rate that any deterministic, non-pathological input distribution could induce.

## Methodology

1. For each `(family, k_c, target_frac)`:
   * Reject-sample `N_pool = 10_000` residue tuples until `{S} < target_frac` for each.
   * `target_frac ∈ {1e-3, 5e-3, 1e-2, 5e-2}`.
2. For each pool, evaluate the estimator at every `r ∈ {6, 8, 10, 12, 14, 16}` × `use_offset ∈ {false, true}`.

Cost: rejection rate ≈ `target_frac`, so `target_frac=1e-3` requires ≈10⁷ candidates to fill the pool. At ~1µs per candidate (the rejection check is a sum + mod), ~10s per pool.

## Interpretation

* If pool abort rate ≈ 100% for `target_frac < k·2⁻ʳ`: estimator failure region is exactly what theory predicts (sanity).
* If pool abort rate < 100% for `target_frac < k·2⁻ʳ`: probable bug somewhere.
* The offset variant should have *much lower* abort rate on small-{S} pools because its failure region is shifted away from {S}=0.

## How to reproduce

```bash
.venv/Scripts/python.exe -m experiments.exp3_adversarial.run --pool-size 10000
```
