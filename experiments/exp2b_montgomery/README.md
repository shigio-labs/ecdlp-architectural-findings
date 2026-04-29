# Experiment 2b: Montgomery-style intermediate distribution

## Why this experiment exists

Experiment 2 (`product_modMc` and `product_modp`) measures abort rate for inputs `x = a·b (mod something)` where `a, b ~ U([0, p))`. This is **not** the distribution that the Kawamura estimator sees in real Montgomery-RNS.

In Montgomery-RNS, the chain of operations is:

1. Compute `c = a · b` in the *full* basis. `c ∈ [0, p²)`.
2. Compute `t = (-c · p⁻¹) mod M_core` in the **core only**. By construction `t ∈ [0, M_core)`.
3. Extend `t` to the extension basis (this is the step that requires the Kawamura q-estimate).

The estimator's input is `t`. Empirical observation (`{S} = t / M_core` mean ≈ 0.5, max ≈ 1.0): `t` is approximately uniformly distributed on `[0, M_core)`, so **the Montgomery estimator abort rate matches `exp1` (uniform-in-M)** rather than `exp2` (`product_mod_p`).

This experiment runs the same sweep as exp1 but with the Montgomery sampler, to *verify directly* that Montgomery distribution gives uniform-like abort rates and not the catastrophic 100% rate of `uniform_in_p` with `M_core ≫ p`.

## Methodology

`(family, k_c, r, use_offset)` sweep × Montgomery sampler. `n_samples = 1_000_000` per config.
