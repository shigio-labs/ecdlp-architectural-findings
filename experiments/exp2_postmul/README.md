# Experiment 2: Post-multiplication distribution

## Hypothesis

For tapered RNS to apply to Shor-style ECDLP, the *real* input distribution to the Kawamura estimator is not uniform — it is the residue distribution induced by `x = (a · b)` (or `x = a · b mod p`) with `a, b ~ U([0, p))`. The plan flags this as "**критический случай**": if abort rate here is much higher than uniform, there's a structural problem.

Two sub-distributions:
* `product_modMc` — `x = (a · b) mod M_core`, `a, b ~ U([0, p))`. The integer product overflows `M_core` for our parameter range (since `M_core` ≤ 272 bits in `standard17` and ≤ 400 bits in `wide20`, while `p² ≈ 512` bits), so the mod step matters.
* `product_modp` — `x = (a · b) mod p`. Only meaningful when `M_core ≥ p` (`k_c = 16, 17` in `standard17`; `k_c ≥ 13` in `wide20`).

## Methodology

Same sweep as Experiment 1: `(family, k_c, r, use_offset)` over the same grid, `n_samples = 1_000_000`. Adds the distribution axis.

## Key comparison

For each `(family, k_c, r, use_offset)`:

    rate_uniform     # from exp1
    rate_product_modMc # this exp
    rate_product_modp  # this exp (when M_core ≥ p)

If `rate_product` ≪ `rate_uniform` *or* ≫ `rate_uniform` consistently, the Kawamura assumption of uniform inputs is broken and we have a measurable structural effect.

## How to reproduce

```bash
.venv/Scripts/python.exe -m experiments.exp2_postmul.run --n-samples 1000000
```
