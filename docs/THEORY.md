# Phase 1 — Theoretical analysis of Δ-compression in projective Montgomery ladder

> **Outcome: (b) preliminary gate-fail.** Three independent lines of reasoning all conclude that `Δ = X_2 − X_1` (or any algebraically equivalent quantity) has bit-size approximately equal to `log₂ p` with high probability over random ladder paths on secp256k1, regardless of the representative-selection strategy. Estimated achievable compression: **≤ 5 bits** of average information, far below the gate threshold of ≥ 100 bits.
>
> Recommendation: declare gate fail without expensive Phase 2 empirics, but optionally run a brief (~1 hour) numerical sanity check against random ladders to confirm the predicted uniform distribution before final write-up.

## 1. Setup

For a projective Montgomery-style ladder on `y² = x³ + ax + b` over `F_p`, the two registers `R_0` and `R_1` always satisfy the invariant `R_1 − R_0 = P` (the base point). At step `i` of the ladder for scalar `k`, the registers hold `(k_i · P, (k_i + 1) · P)` for some intermediate scalar `k_i` that depends on the high-bits prefix of `k`.

Three representative-selection strategies for the projective coordinates of `R_0, R_1`:

* **R1 — independent Z₁, Z₂.** Each register is `(X_j : Y_j : Z_j)` with arbitrary representatives. `Δ` could be defined as `X_2 Z_1 − X_1 Z_2` (the "cross-product affine numerator").
* **R2 — common Z** by post-step normalization. Both registers share the same `Z`, so `(X_1 : Y_1 : Z), (X_2 : Y_2 : Z)`. Then `Δ = X_2 − X_1 = Z · (x_2 − x_1)` where `x_j` is the affine x-coordinate.
* **R3 — co-Z by formula** (Goundar-Joye-Miyaji 2010, Hutter-Joye-Sierra 2011). Maintains `Z_1 = Z_2` throughout the ladder via specially crafted addition formulas. Same identity as R2: `Δ = X_2 − X_1 = Z · (x_2 − x_1)`.

In all three strategies, the bit-size of `Δ` is determined by the bit-size of `x_2 − x_1 mod p` plus a multiplicative factor of `Z` (which does not reduce bit-size — multiplication mod p is a bijection on `(F_p)*`).

**Therefore: `bit-size(Δ) ≈ bit-size(x_2 − x_1 mod p)` in all three R-strategies.**

## 2. Three independent arguments for (b)

### 2.1 Algebraic — multiplication by Z does not compress

For any nonzero `Z ∈ F_p^*`, the map `α ↦ Z · α mod p` is a bijection `F_p → F_p`. If `α` is uniform over `F_p`, so is `Z · α`. Therefore the bit-size distribution of `Z · (x_2 − x_1)` is identical to that of `x_2 − x_1`.

This immediately rules out any compression scheme that relies on the projective scaling factor `Z`. The only way to get small `Δ` is for `x_2 − x_1 mod p` itself to be small.

### 2.2 Cryptographic — uniformity of `x_2 − x_1` is required by ECDLP hardness

For secp256k1 (and any cryptographically used curve), the discrete logarithm is conjecturally as hard as `O(√p)` Pollard-rho. If `x_2 − x_1 mod p` had non-trivial structure for ladder-step pairs `(kP, (k+1)P)` over a uniformly random scalar `k`, this would constitute a **distinguisher** between ladder-step x-differences and uniform `F_p` elements.

A distinguisher of this kind is exploitable. For example, if `Pr[x_2 − x_1 mod p < 2^s] > 2^{s−n}` for some `s` significantly less than `n = 256`, then partial-information attacks (lattice attacks on biased nonces, Bleichenbacher-style, etc.) would apply. secp256k1 has resisted ~15 years of cryptographic scrutiny including such attacks; therefore `x_2 − x_1 mod p` is, to the best of public knowledge, statistically indistinguishable from uniform on `F_p`.

This is not a proof — it is a **strong empirical / community-consensus statement about secp256k1 security**. But it is far stronger than the kind of evidence we have for any of the optimizations in this research line.

### 2.3 Literature — memory-optimized co-Z work didn't find Δ-compression

Hutter, Joye, Sierra 2011 ("Memory-Constrained Implementations of Elliptic Curve Cryptography in Co-Z Coordinate Representation") is **the paper most directly motivated to find such a compression**. Their stated goal is reducing the number of field registers in co-Z (X:Z)-only Montgomery ladder. Result: **10 full-width field registers per ladder step**, no register shrunk by `Δ`-style tricks.

Goundar-Joye-Miyaji 2010 introduces co-Z and analyzes register allocation for ladder. Their Algorithm 7 (Montgomery ladder with co-Z) operates on full-width Jacobian coordinates throughout. Their optimization target is multiplication count `(M, S)`, not bit-width. They explicitly show in ZADDU output that the new common `Z_3 = Z · (X_1 − X_2)` accumulates the difference `X_1 − X_2` as a *factor of Z* — making Z larger, not smaller — which is also consistent with no bit-size compression.

If a representative scheme existed that gave `Δ` small bit-size with high probability, both papers would have used it. They didn't.

## 3. Quantitative ceiling on possible compression

Even granting some hidden small bias in `x_2 − x_1 mod p`, the maximum bit-compression is limited by the curve's known security margin. Public estimates of secp256k1 classical security place its complexity at `~2^128`. A bias that compressed `x_2 − x_1` to `n − Δ_bits` bit-size with probability ≥ 0.5 would imply a distinguisher of advantage `2^{Δ_bits − 1}`, which translates (via standard hybrid arguments) to a partial-information attack of complexity `~2^{n/2 − Δ_bits/2}`.

For this attack complexity to remain `≥ 2^128`, we need `Δ_bits ≤ n − 256 = 0` for n=256. **Any amount of compression visible at the 50%-quantile bears a cost in security margin.**

In practice, to be conservative, distinguishers `≤ 2^{−40}` in advantage are considered ignorable. This translates to potential `Δ`-bit-compression of perhaps **≤ 5 bits at 50% probability** — but only as a hidden reservoir of statistical bias, not as an exploitable register-width reduction. **Useless for our purposes.**

## 4. What this rules out and what it doesn't

**Rules out (with high confidence):**
* `Δ`-compression as a register-width reduction in any of R1, R2, R3 strategies.
* The β-Phase B parallel-RNS-with-X-only-ladder architecture gaining qubits over the naive X-only ladder via `Δ`-compression.

**Does not rule out (still open, but not in scope of this gate):**
* Other compression mechanisms in parallel-RNS that don't rely on `Δ` smallness (e.g., Karatsuba-style or windowed-NAF representation of intermediate values).
* `Δ`-style structure on **differential** but not **adjacent** ladder pairs (e.g., `X_2P − X_P` rather than `X_{(k+1)P} − X_{kP}`). This is a different quantity; not analyzed here.
* `Δ`-compression on **special curves** with structure beyond cryptographic generic-curve assumptions (e.g., curves with very small CM discriminant or unusual j-invariant). secp256k1 has CM by `Z[ζ_3]`, but this doesn't yield small ladder x-differences — it yields the GLV decomposition for fast scalar mult, which is orthogonal.

## 5. Optional sanity check (Phase 2 lite)

The argument above is theoretical. A 1-hour numerical sanity check would:

1. Sample `10^4` random scalars `k ∈ [1, ord(P))`.
2. For each, run the affine Montgomery ladder over secp256k1, recording `x_2 − x_1 mod p` (signed, in `(−p/2, p/2]`) at every one of the ~256 ladder steps.
3. Compute the empirical distribution of `bit-size(|x_2 − x_1|)`.

**Predicted result:** mean `bit-size ≈ 256 − log₂(2) = 255` (because uniform over `(−p/2, p/2]` has expected absolute value `p/4`), 99th percentile `≥ 255`, and < 1 in 10^4 samples have bit-size below 250.

If the empirical distribution matches this prediction, gate fails firmly. If it deviates significantly (low percentiles fall below 200), I missed something theoretical and Phase 2 full empirics are warranted.

This sanity check is **optional under the plan's exit logic** (outcome (b) goes directly to fail without Phase 2). But it costs little and protects against my theoretical blind spots.

## 6. Recommendation to user

**Phase 1 result: outcome (b).** Δ-compression in projective Montgomery ladder over secp256k1 is structurally blocked by the cryptographic uniformity of `x_2 − x_1 mod p`, confirmed by literature absence of any such compression scheme.

**Decision needed (mandatory check-in per plan):**
* (i) Accept (b) without empirics → β-Phase B does not start. Project pivots to γ (publish Phase 1 + this analysis as standalone artefact).
* (ii) Run the 1-hour sanity check first → confirms (b) firmly before write-up. I recommend this; cost negligible.
* (iii) Run full Phase 2 anyway → only justified if there's a specific reason to distrust the theoretical analysis. I do not see one.

I recommend (ii) → (γ).

## References

* Brier, Joye 2002 — "Weierstraß Elliptic Curves and Side-Channel Attacks". Original X-only differential addition for short Weierstrass.
* Goundar, Joye, Miyaji 2010 — "Co-Z Addition Formulæ and Binary Ladders on Elliptic Curves". CHES 2010 / ePrint 2010/309. Co-Z technique reduces multiplication count, not register width.
* Hutter, Joye, Sierra 2011 — "Memory-Constrained Implementations of Elliptic Curve Cryptography in Co-Z Coordinate Representation". CHES 2011. Memory-optimized (X:Z)-only co-Z; uses 10 full-width registers, finds no Δ-compression.
* EFD database, [XZ coordinates for short Weierstrass](https://www.hyperelliptic.org/EFD/g1p/auto-shortw-xz.html). Comprehensive operation-count tables; no register-width-compression entries.
