# Experiment 6: Phase-transition curve at log2(M_c / p) ∈ [0, 16]

## Hypothesis

For naive `x ∈ [0, p)` storage in a basis with product `M_c`, `{S} = x/M_c ∈ [0, p/M_c)`. The Kawamura no-offset failure region is `{S} ∈ [0, k · 2⁻ʳ)`. Theoretical abort rate as a function of `T := log2(M_c/p)`:

```
r_abort(T) = min(1, k · 2^(T - r))   (no offset)
```

Saturates at 1 when `T > r - log2(k)`, i.e., the catastrophic region. Below that, scales linearly in `2^T`.

For the offset variant, similar but capped at ~50% in the catastrophic region (failure happens only when truncation `eta` is on the wrong side of zero, which happens roughly half the time for tiny `{S}`).

## Methodology

Hold `k_c = 17` fixed. Construct the basis as `standard17[:16] + (p_extra,)` where `p_extra` ranges over primes that bridge `T ≈ 0` to `T ≈ 16`. This gives a continuous parameter `T` while keeping `k_c` constant.

Distribution: `uniform_in_p` (`x ~ U([0, secp256k1_p))`). Samples: 200 000 per cell. Precisions tested: `r ∈ {12, 14, 16}`, `use_offset ∈ {False, True}`.

## What this answers

Where exactly does the catastrophe happen? Is it a sharp transition (as theory predicts) or a soft slope? How far is the recommended config (`wide20 k_c=13`, `T ≈ 4.0`) from the cliff?

For `r=14`, theoretical cliff is at `T ≈ 14 − log2(17) = 9.9`. So `wide20 k_c=13` at `T=4` should sit ~6 bits below the cliff — a comfortable margin. Empirical confirmation here.

## How to reproduce

```bash
.venv/Scripts/python.exe -m experiments.exp6_threshold.run --n-samples 200000
```
