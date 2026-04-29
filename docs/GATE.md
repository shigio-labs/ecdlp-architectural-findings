# Phase 3 GATE — Δ-compression in projective Montgomery ladder

> **Decision: FAIL.**
> Δ-compression is structurally impossible in the parallel-RNS + Montgomery-ladder framework over secp256k1. Three independent theoretical arguments and an empirical sanity check at 2.56 × 10⁶ ladder-step samples all converge: `bit-size(X_2 − X_1 mod p) ≈ 256` with high probability, indistinguishable from uniform on `[0, p)`. β-Phase B does not start. The project pivots to γ — final write-up of all three phases as a coherent research artifact.

## 1. Hypothesis under test

For projective Montgomery ladder over secp256k1, in any of the three representative-selection strategies (R1 independent-Z, R2 common-Z, R3 co-Z), is the bit-size of `Δ = X_2 − X_1 mod p` (or the algebraically equivalent quantity in R1) significantly smaller than `log₂ p ≈ 256`, with high probability over random ladder paths?

The β-strategy for the parallel-RNS architecture depended on this being **yes**, with compression ≥ 100 bits per coordinate register.

## 2. Three independent theoretical arguments against (from THEORY.md)

### 2.1 Algebraic
In all three R-strategies, `Δ` reduces to `Z · (x_2 − x_1) mod p`. Multiplication by nonzero `Z ∈ F_p^*` is a bijection on `F_p`, preserving bit-size distribution. The question reduces to: is `x_2 − x_1 mod p` small for ladder-step pairs `(kP, (k+1)P)`?

### 2.2 Cryptographic
If `x_2 − x_1 mod p` had exploitable structure for ladder-step pairs over uniform-random scalars, this would be a distinguisher convertible to a partial-information attack via standard lattice-based reductions (Howgrave-Graham–Smart, Nguyen–Shparlinski). secp256k1 has resisted ~15 years of cryptanalytic scrutiny including such attacks; therefore `x_2 − x_1 mod p` is, to community consensus, statistically indistinguishable from uniform.

### 2.3 Literature
Hutter–Joye–Sierra 2011 ("Memory-Constrained Implementations of Elliptic Curve Cryptography in Co-Z Coordinate Representation") — the work most directly motivated to find such a compression — uses 10 full-width field registers per ladder step. They didn't find compression. Goundar–Joye–Miyaji 2010's ZADDU formula explicitly gives `Z_3 = Z · (X_1 − X_2)`, showing the difference accumulates as a *factor of Z*, growing the register, not shrinking it.

## 3. Empirical backstop (Δ-mini)

Run on 10⁴ random 256-bit scalars (top bit set) × 256 ladder steps each = **2 560 000 ladder-step samples**. For each step, measured `bit-size((R_1.x − R_0.x) mod p)` in the affine Montgomery ladder over secp256k1.

```
              metric |   observed |  predicted (uniform on [0, p))
       mean bit-size |   255.0032 |  255.0000
     median bit-size |        255 |  ~255
     99th percentile |        256 |       256
   99.9th percentile |        256 |       256
        min bit-size |        232 |  ~232 (1-in-a-million tail)
        max bit-size |        256 |       256
```

Histogram of `bit-size`:

```
  bit-size=232:        2 ( 0.00%)
  ...
  bit-size=246:     1220 ( 0.05%)
  bit-size=247:     2458 ( 0.10%)
  bit-size=248:     5010 ( 0.20%)
  bit-size=249:     9682 ( 0.38%)
  bit-size=250:    19623 ( 0.77%)
  bit-size=251:    39200 ( 1.53%)
  bit-size=252:    80373 ( 3.14%)
  bit-size=253:   157391 ( 6.15%)
  bit-size=254:   320081 (12.50%)
  bit-size=255:   647547 (25.29%)
  bit-size=256:  1276220 (49.85%)
```

Each row is half the next, exactly as expected for `bit-size(uniform on [0, 2^256))`. There is no anomaly, no clustering at low bit-sizes, no curve-specific structure. The theoretical prediction is reproduced to four significant figures on the mean.

This is a backstop, not the main evidence. The three theoretical arguments are the substance. The 13-second simulation is a sanity check that closes the blind-spot risk: had the empirical distribution diverged from uniform — for example, a 99-percentile of 230 instead of 256 — the theoretical analysis would be flagged for re-examination. It did not diverge.

## 4. Quantitative ceiling — what little compression *is* present has zero engineering value

The deepest empirical bit-size in 2.56M samples is **232**. To register-width-compress by a meaningful amount in a quantum circuit, one would need ALL ladder steps (or a large fraction guaranteed by detection) to fit in a smaller width.

* To compress register from 256 to 246 bits (10 bits saved): only `~0.4%` of steps fit. The other 99.6% would overflow → restart or detection-and-recovery on essentially every step.
* To compress to 240 bits: `~0.012%` of steps fit. Useless.
* To compress to 256 bits: 49.85% fit (top bit unset). Half the time you save 1 bit. Ratio of cases to lost cases is ~1, not exploitable as a register reduction.

For the partial-information attack ceiling derived in `THEORY.md` § 3: any structure compressing `x_2 − x_1` to `n − Δ_bits` bits with ≥ 50% probability would imply a classical attack on secp256k1 of complexity `~2^{n/2 − Δ_bits/2}`. Sustaining the conjectured 128-bit security bar requires `Δ_bits ≤ 0`. The empirical histogram is consistent with this — *none* of the bit-size deviation observed is exploitable.

## 5. Decision

**FAIL.** Δ-compression in the projective Montgomery ladder over secp256k1 is structurally blocked. β-Phase B does not start.

This decision required ~5 hours of work split into three theoretical lines and a 13-second empirical run. By exit criteria pre-committed in `PLAN_DELTA.md` (99-percentile ≥ 254 → confirm theory → FAIL → γ), the gate result is unambiguous.

## 6. Implications

### 6.1 Project pivots to γ
The qubit-reduction research line (parallel-RNS Shor variant for secp256k1) does not have a viable architectural path to beating CFS 2026/280 within the tools we have explored. The next action is consolidation: write the three phases as a single research artifact (see § 7 below).

### 6.2 Negative result is publishable
"Δ-compression is impossible in the parallel-RNS + Montgomery-ladder framework over cryptographically generic curves" is a non-trivial statement. Three independent arguments combine into a no-go result that future researchers in this area should consult before re-proposing the idea. Filed alongside the Phase 1 positive result (Kawamura abort rate verification) and the Phase 0/2 architectural correction (CFS = sequential-RNS), the bundle constitutes a coherent research story:

* What works in parallel-RNS for secp256k1 (Kawamura).
* What does not work in parallel-RNS for secp256k1 (Δ-compression).
* Where parallel-RNS sits in the architectural landscape vs CFS-style sequential-RNS.

### 6.3 What we would need to revive the parallel-RNS line in the future
The result rules out compression *for cryptographically generic curves* with our current toolbox. It does not rule out:

* A compression mechanism that does **not** depend on `Δ` smallness (e.g., Karatsuba representation of intermediate point coordinates; or a different ladder algorithm with structurally smaller intermediate registers).
* A different curve where `x_2 − x_1` *is* structured by curve construction (a non-cryptographic curve), if it has alternative cryptographic value somewhere else in PQ landscape.
* A different scheme entirely (e.g., not Eker̊a-H̊astad + RNS but a fundamentally different organization of Shor for ECDLP).

These are open questions but **not** the open question this gate was supposed to settle. They constitute new research projects, not extensions of this one.

## 7. Suggested γ-publication structure

For the final write-up combining Phases 1, 0/2, and 3:

1. **Introduction** — qubit reduction for 256-bit ECDLP as a research target; tapered-RNS hypothesis as starting point; CFS 2026/280 as baseline.
2. **Phase 1 result (positive)** — parallel-RNS Kawamura q-estimator abort rate at `r=14, offset, k_c=13` is 50 ppm/op for Montgomery-style intermediates; 512-step Shor-chain survival 97.5%; Bernoulli independence verified. *Architecturally relevant for parallel-RNS, not CFS sequential-RNS.*
3. **Architectural finding** — CFS uses sequential-per-prime + binary-tree-of-additions (Eker̊a-H̊astad) + spooky pebbling; their RNS is CRT-reconstruction over big integers, not parallel mod-q arithmetic. Phase 1's parallel-RNS verification therefore characterizes a different architecture, not an incremental improvement of CFS.
4. **Phase 3 result (negative)** — Δ-compression in projective Montgomery ladder is structurally blocked by algebraic + cryptographic + literature arguments and confirmed empirically. The natural alternative architecture (parallel-RNS X-only Montgomery ladder with Δ-compression) cannot be made qubit-competitive with CFS via this lever.
5. **Open levers in CFS** (from Track α reading): `q_M = 102`-qubit Barrett-reduction accumulator is the most plausible internal optimization target with realistic ceiling 30–50 qubits saved. Whether the Qarton implementation already streams Barrett is unknown without code access (Track α was inconclusive due to Anubis-protected GitLab; user-side action required to resolve).
6. **Conclusion** — net contribution is one positive result for an alternative architecture, one negative result that rules out a natural extension of it, and one architectural correction to the qubit-reduction landscape. The 256-bit ECDLP qubit-reduction line, as we have framed it here, is exhausted with our toolbox and pivots either to CFS sub-component optimization (which requires their code) or to a new toolbox.

This is a clean story. ~3 weeks of focused work, three discrete findings, all defensible.
