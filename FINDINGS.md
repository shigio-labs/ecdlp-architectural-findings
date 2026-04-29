# Architectural Trade-offs in Space-Efficient ECDLP: Three Findings on the Post-CFS Landscape

**Author:** Paul Amelin, Independent researcher
**Status:** Research note. April 2026.

---

## Abstract

Can the 1193-qubit CFS estimate for 256-bit ECDLP (Chevignard, Fouque,
Schrottenloher, ePrint 2026/280) be pushed substantially lower by local
architectural tweaks? We tested the two most plausible directions and
found structural obstructions in both. The only positive result survives
in a different regime: the Kawamura quotient estimator is viable for a
hypothetical *parallel-RNS* architecture (~50 ppm per-step abort, validated
Bernoulli structure across 512-step chains), but this does not transfer
to the sequential-per-prime CFS construction.

We report three findings in detail. First, a numerical verification of
Kawamura under tapered RNS bases, applicable to the parallel-RNS regime
only. Second, an architectural taxonomy distinguishing parallel-RNS-with-
Montgomery-ladder from the sequential-RNS-with-binary-tree (Ekerå-Håstad)
approach used by CFS, making explicit a distinction that has been
implicit in the literature. Third, structural and empirical evidence
that delta-compression for parallel-RNS X-only ladders is bounded by the
security level of the underlying curve: for secp256k1, it cannot save
more than O(1) bits per coordinate without violating established
cryptographic assumptions.

We additionally analyze two candidate optimization levers within the
CFS architecture itself — q_M streaming reconstruction and sub-(k+2) tree
pebbling — and find structural obstructions to both. Exact streaming
retains the full 102-bit width in the CFS parameter regime; 6 → 5 pebble
reduction is infeasible on the P-256 instance under both black-pebble and
relaxed ghost-aware models within our search budgets. Meaningful further
improvements likely require a different architecture, not local tuning.

---

## 1. Introduction

The state of the art for 256-bit ECDLP via Shor's algorithm has compressed
rapidly. Roetteler-Naehrig-Svore-Lauter (2017) used ~2330 logical qubits
without explicit magic-state-factory accounting; Häner-Jaques-Naehrig-
Roetteler-Soeken (2020) reported ~2124 qubits with Toffoli-based costing;
the Chevignard-Fouque-Schrottenloher construction (CFS 2026, ePrint 2026/280)
achieves 1193 qubits for P-256 (1098 for P-224) by combining residue number
system arithmetic with binary-tree windowed scalar multiplication in the
Ekerå-Håstad framework — roughly halving the previous count.

CFS represents a substantial qualitative jump, and the obvious next question
is whether further halving is plausible. Two natural directions present
themselves. First, is there a *parallel-RNS* variant that is competitive,
in which all RNS residues are held coherently and operations are performed
in parallel across the basis? Second, are there low-level optimizations
within the CFS architecture itself that can shave additional qubits at
acceptable Toffoli cost?

We explored both questions and report negative results on both: parallel-RNS
with X-only Montgomery ladder and delta-compression is structurally bounded;
the two most natural local optimizations within CFS (q_M streaming, sub-(k+2)
pebbling) exhibit structural obstructions in our analysis. We obtain a
positive result on a sub-component (Kawamura estimator under tapered bases)
applicable in the parallel-RNS regime only, and a methodological correction
(the architectural distinction between parallel-RNS and the sequential CFS
approach, which we initially conflated). We believe each of these is
independently useful for researchers continuing in this direction, and
presenting them together makes the architectural choices that drove our
conclusions visible.

The note is organized as follows. §2 establishes the architectural taxonomy.
§3 reports the Kawamura verification (positive result). §4 reports the
delta-compression bound (negative result with empirical backstop). §5
analyzes two candidate optimization levers within the CFS architecture and
reports structural obstructions to both. §6 concludes with open questions.

All raw data, code, and per-experiment READMEs are available at
https://github.com/shigio-labs/ecdlp-architectural-findings.

---

## 2. Architectural Taxonomy

We distinguish two architectures for space-efficient ECDLP that have not been
explicitly compared in prior literature, and which require different
optimization strategies.

### 2.1 Sequential-per-prime RNS (CFS)

In the CFS construction, RNS primes are processed *one at a time*. For each
prime p_i in the basis, the full Ekerå-Håstad binary tree of point additions
is executed modulo p_i, with intermediate results stored in pebble nodes of
width log_2(p_i) ~ 19 bits. After each prime's contribution is computed, the
residue is accumulated into a CRT-style reconstruction register (q_M in their
notation), and the next prime is processed.

This design choice has a striking consequence: the bulk of the qubit budget
is *not* in field-arithmetic ancilla (which would scale with full coordinate
width), but in:

| Component | Qubits (P-256) | Share |
|---|---:|---:|
| Input register (windowed scalar) | 297 | 25% |
| Output / q_M reconstruction | 358 | 30% |
| Algorithm 1 ancilla | 195 | 16% |
| Pebble nodes (6 × 3 coords × 19 bits) | 342 | 29% |
| **Total (CFS Table 6, computation phase)** | **1192** | |

(CFS Table 8 reports a headline figure of 1193 qubits, which adds one qubit
for Legendre symbol output; we use 1193 throughout the rest of this note
for consistency with external citations.)

The 195-qubit ancilla figure is per-prime, not per-full-coordinate; this is
the architectural feature that makes 1193 possible.

### 2.2 Parallel-RNS with Montgomery ladder (hypothetical alternative)

In a parallel-RNS variant, all k RNS residues of every coordinate are held
coherently. Field operations are performed in parallel across the basis.
Persistent state per coordinate is k × log_2(p_i) ~ 13 × 20 = 260 qubits in
the wide20 configuration (see §3); for an X-only Montgomery ladder, four
such coordinates are persistent, totaling ~1040 qubits before any ancilla.

This architecture admits different optimization levers:

- The RNS basis itself can be tapered (§3) to reduce per-coordinate width.
- The X-only structure permits, in principle, compression of one coordinate
  in terms of the difference of the other two — the delta-compression
  hypothesis we examine in §4.
- Pebbling and uncomputation operate on full-width coordinate registers, with
  different trade-offs from the sequential case.

### 2.3 Why the distinction matters

These architectures share notation (RNS, projective coordinates, Shor) but
differ structurally in what is held coherent at any time, and consequently
in which optimizations apply. Our initial work assumed CFS was a parallel-RNS
construction and treated parallel-RNS optimizations as incremental
improvements. A close reading of CFS Algorithm 1, Lemma 2, and Table 6
revealed otherwise; the present taxonomy makes explicit a distinction that
is implicit in CFS.

In particular, Lemma 6 of CFS shows that intermediate values in their
binary-tree computation grow to O(n^3) bits as integers — they use RNS as a
*reconstruction technique for large integers*, not as a parallel modular
arithmetic scheme. This is qualitatively different from parallel-RNS as the
term is used in classical cryptographic implementations.

### 2.4 Implications for optimization strategy

Optimizations targeting the CFS architecture should focus on:
- The q_M register (102 qubits, breakdown: 51 final + 51 accumulator margin).
- Tree pebbling depth (currently 6 pebbles via Lemma 7 [25]).
- Algorithm 1 internal ancilla (195 qubits, already aggressive).

Optimizations targeting parallel-RNS would focus on:
- RNS basis size reduction (§3).
- Coordinate-register compression (§4 — we show this is structurally bounded).
- Persistent ancilla via aggressive pebbling.

Findings from one architecture do *not* automatically transfer to the other.
The Kawamura verification of §3 applies to parallel-RNS; the
delta-compression bound of §4 applies to parallel-RNS-with-X-only-ladder; CFS
is a distinct optimization target whose internal levers we examine in §5.

---

## 3. Kawamura Estimator under Tapered RNS Bases

### 3.1 Setting

We consider parallel-RNS arithmetic over F_p for secp256k1 (p = 2^256 -
2^32 - 977). A standard RNS basis of k = 17 primes of ~17 bits each yields
k × 17 = 289 qubits per coordinate with prod(p_i) ~ 2^289 > p (sufficient
to encode F_p elements injectively, but not sufficient to encode
multiplication outputs in [0, p^2) without overflow — see §3.5).

The *tapered* hypothesis: split the basis into

- a *core* B_c with k_c primes, prod(B_c) p_i in (p, p^{1.6}); persistent;
- an *extension* B_e with k_e = k - k_c primes; materialized only during
  reduction, then uncomputed.

Extension residues are computed from core residues via the Kawamura-Kapoor
estimator (Kawamura et al., EUROCRYPT 2000), which produces an estimate
\hat{q} of the CRT quotient floor(x / M_c) using only the core residues.

The estimator can fail by ±1 due to fixed-precision approximation. The core
question of this verification: under what parameters (k_c, precision r, input
distribution) does the abort rate remain low enough to keep the architecture
viable across a full Shor execution (~512 group operations)?

### 3.2 Methodology

We measured abort rates across:

- five core sizes k_c in {12, 13, 14, 15, 16},
- six precisions r in {6, 8, 10, 12, 14, 16},
- four input distributions: uniform, bounded, post-multiplication (modM_c
  and mod-p variants), and adversarial (boundary-case),
- two basis families: standard17 (17-bit primes) and wide20 (20-bit primes),
- two estimator variants: with and without offset trick.

Each cell received 10^6 samples for primary distributions and 10^4 per pool
for adversarial. We additionally ran a 512-step chain experiment with 2000
chains to validate Bernoulli structure under multiplicative mixing.

Detailed methodology, parameter selection rationale, and per-experiment
configurations are in the per-experiment README files under
`experiments/exp1_uniform/`, `experiments/exp2_postmul/`, and so on.

### 3.3 Recommended configuration and key result

The recommended configuration for parallel-RNS over secp256k1:

- **Basis:** wide20 (20 primes of ~20 bits each).
- **Core size:** k_c = 13 (so log_2(M_c / p) ~ +4.0).
- **Precision:** r = 14 bits.
- **Offset trick:** enabled.

Under this configuration:

- Per-step abort rate: ~50 ppm.
- 512-step chain survival: 97.55% (Wilson 95% CI: [96.78%, 98.14%]).
- Bernoulli structure: confirmed (lag-1 autocorrelation = -0.0009,
  Poisson chi^2 = 0.48).
- Phase transition: located far from operating point (5.9 bits of headroom
  from no-offset cliff at log_2(M_c / p) ~ 9.9).

**Scope of this measurement.** The recommended configuration characterizes
the Kawamura q-estimator behavior under a parallel-RNS scheme with a
13-prime core. For a complete Shor implementation, the total basis (core +
extension) must satisfy prod_full > p^2 to support modular multiplication
without overflow. The wide20 basis used here (20 primes × ~20 bits = ~2^400)
satisfies prod_full > p but not prod_full > p^2; a complete implementation
would require expanding to ~27 primes in the wide20 style (or equivalent
in higher-bit primes), which we did not analyze. The 50-ppm abort rate
holds independently of total basis size — it is a function of the core
size k_c and the precision r — but the implementability claim of §3.7
depends on resolving the full-basis-size question.

### 3.4 Phase transition and threshold

We mapped the abort-rate phase transition through a threshold sweep across
T = log_2(M_c / p) in [0, 16], holding r = 14:

| T | Abort (no offset) | Abort (offset) |
|---:|---:|---:|
| +0.02 | 0.045% | 0.001% |
| +4.54 | 1.15% | 0.072% |
| +8.62 | 19.3% | 1.1% |
| +9.61 | 38.2% | 2.2% |
| +11.61 | 99.94% | 9.0% |
| +12.61 | 100% | 17.5% |
| +16.02 | 100% | 45.8% |

The no-offset variant exhibits a sharp threshold near T_crit ~ r - log_2(k_c);
the offset variant degrades smoothly toward an asymptote of 50%. Both behaviors
are consistent with the corrected theoretical bound

\Pr[\hat{q} \neq q] \approx (k/2) \cdot 2^{T-r}

where k is the number of contributing residues. (The factor of 1/2 corrects
a common error in informal analyses; the maximum estimator error is
e_max / (2 s_max) rather than e_max / s_max.)

### 3.5 Real-Shor caveat

The 512-step chain experiment uses a generic mixing chain (random
multipliers per step). A realistic Shor schedule has *deterministic*
operation sequences with potential structural correlations between steps.
We did not verify Bernoulli independence on a real Shor schedule, because
classical simulation of the full schedule for a 256-bit ECDLP is
computationally inaccessible.

For implementations of parallel-RNS, we recommend re-verifying per-step
abort rate on a faithfully simulated small-field Shor schedule (e.g.,
F_p with p ~ 2^16) before committing to circuit construction. This is a
known debt rather than a discovered issue.

### 3.6 Retry strategy analysis

For the recommended configuration, three retry strategies were compared:

- **(a) Accept + classical post-check:** 50 ppm/op, 2.5% bad chains, ~2.6%
  circuit-run overhead, no scheme complexity.
- **(b) Certificate-based abort:** 50 ppm/op, ~40% chains trigger certificate,
  but ~95% of triggers are false-False; effective overhead ~33%, requires
  margin-check + restart logic.
- **(c) Higher precision (r=16):** 9 ppm/op, 0.5% bad chains, ~0.5%
  circuit-run overhead, +26 ancilla qubits.

Strategy (b) is dominated by both (a) and (c). The choice between (a) and (c)
is determined by the relative cost of qubits versus Toffoli volume; in
qubit-constrained regimes (a) is preferable, in spacetime-constrained regimes
(c) is preferable. Spacetime ratio V_c / V_a ~ 1.06 across realistic budgets.

### 3.7 Status of this finding

The Kawamura verification establishes that *if* a parallel-RNS architecture
is built and the full-basis-size question of §3.3 is resolved, the
tapered-basis q-estimator does not block it. It does not
establish that parallel-RNS is competitive with CFS overall: the
delta-compression bound of §4 closes the most promising lever for compressing
parallel-RNS coordinates further, leaving parallel-RNS at approximately wash
with CFS in our analysis. The result is presented as a positive verification
of a sub-component, applicable in a defined architectural context.

---

## 4. Structural Bound on Delta-Compression in Parallel-RNS Ladders

### 4.1 Hypothesis

In an X-only Montgomery ladder, two projective points (X_1 : Z_1) and
(X_2 : Z_2) are maintained, with the invariant that their affine difference
equals a fixed point P. The *delta-compression hypothesis* posits that one
of these coordinates can be stored in compressed form Delta := X_2 - X_1
(or a representative-dependent variant), exploiting structure in the
difference to reduce per-coordinate width.

If the bit-size of Delta were on the order of 128 bits (half the field
width), this would save ~130 bits per coordinate, translating to ~6–7 RNS
words at wide20 configuration, or ~120 qubits per coordinate.

### 4.2 Three independent arguments against

**Algebraic.** In all natural representative-selection strategies (R1:
independent Z; R2: common Z; R3: co-Z), Delta reduces to Z * (x_2 - x_1)
mod p, where (x_1, x_2) are the affine x-coordinates of the two ladder
points. Multiplication by a nonzero element of F_p is a bijection F_p ->
F_p; it cannot reduce bit-size. The compression question therefore reduces
to: how small is x_2 - x_1 mod p?

**Cryptographic.** If x_2 - x_1 mod p had exploitable structure — i.e., if
its distribution differed substantially from uniform on [0, p) — this would
constitute a distinguisher for secp256k1. By the standard reduction
machinery (Howgrave-Graham–Smart, Nguyen–Shparlinski), partial information
of \Delta_bits bits per ladder step would yield an attack on ECDLP of
complexity ~2^{(n - \Delta_bits) / 2}. Preserving the 128-bit security level
of secp256k1 therefore bounds \Delta_bits <= 0 (i.e., no exploitable
compression). secp256k1 has been subject to extensive cryptanalysis since
2009; a structure of this kind would have been identified.

**Literature evidence.** Hutter, Joye, and Sierra (CHES 2011) — "Memory-
Constrained Implementations of Elliptic Curve Cryptography in Co-Z Coordinate
Representation" — explicitly target memory minimization for X-only co-Z
Montgomery ladders. Their result uses 10 full-width field registers; no
compression is reported. Goundar, Joye, Miyaji, Rivain, and Vanelli (2010)
give explicit co-Z addition formulae in which the difference accumulates as
a factor of Z, growing rather than compressing the representation. (Our
reading of HJS is based on the abstract and CHES summary; we did not access
the full PDF directly.)

These three arguments are independent: the first is structural at the level
of the operation, the second is a security-derived upper bound on
exploitable structure, the third is observed practice by researchers
specifically optimizing the relevant memory.

### 4.3 Empirical backstop

To guard against a blind spot in the theoretical analysis, we ran a direct
measurement of bit-size(x_2 - x_1 mod p) over a full Montgomery ladder.

**Setup.** secp256k1 affine X-only ladder, 10^4 random 256-bit scalars,
yielding 2.56 × 10^6 ladder-step samples of (x_1, x_2). The affine
representation was used because, by the algebraic argument above, it is
the most-favorable case for the compression hypothesis: any projective
\Delta = Z(x_2 - x_1) cannot have smaller bit-size than the affine
difference. Verifying compression fails on the affine case strengthens
the result.

**Results (two independent runs with different seeds).**

| Metric | Run 1 | Run 2 | Predicted (uniform) |
|---|---:|---:|---:|
| Mean bit-size | 255.0032 | 254.9943 | 255.0000 |
| Median bit-size | 255 | 255 | ~255 |
| 99th percentile | 256 | 256 | 256 |
| Min observed | 232 | 234 | tail-dependent |

Bit-length histogram (Run 1):

| bit-size | observed | uniform prediction |
|---:|---:|---:|
| 256 | 49.85% | 50.00% |
| 255 | 25.29% | 25.00% |
| 254 | 12.50% | 12.50% |
| 253 | 6.15% | 6.25% |
| 252 | 3.14% | 3.13% |

The geometric decay (each step ~half the previous) is the textbook
signature of bit-size distribution under uniform x in [0, 2^n). Run 2
confirms the deep tail (single 232 in Run 1) was sampling noise, not
systematic structure.

### 4.4 Quantitative bound

Combining the cryptographic argument with the empirical distribution: any
compression scheme reducing the storage width of Delta below n - \Delta_bits
bits with probability >= 1/2 implies a distinguisher of secp256k1 admitting
attack complexity 2^{n/2 - \Delta_bits / 2}. For \Delta_bits = 1, this is
2^{127.5} — already in tension with the 128-bit security target. For
\Delta_bits >= 2, the implied attack is below the security target; absence
of such an attack after 15+ years implies \Delta_bits <= 1 in any usable
sense.

In practice: at the 99th percentile we observe full 256-bit width. At the
50th percentile a 1-bit savings is possible (median 255 rather than 256),
but this is the bias inherent in the bit-length statistic of a uniform
random variable, not exploitable structure for register-width reduction.

### 4.5 Status of this finding

We treat the conclusion — that delta-compression in parallel-RNS X-only
ladder architectures is structurally bounded to <= 1 bit per coordinate by
the cryptographic security of the underlying curve — as supported by
strong structural and empirical evidence rather than a formal reduction
proof. The structural arguments rest on the standard caveat of
cryptographic reasoning: they are conditional on the security assumption
of secp256k1, which is widely believed but unproven in the formal sense.
Anyone wishing to circumvent this bound must explicitly contend with the
implication that their compression scheme is also a partial-information
attack on secp256k1.

This closes the most promising path for compressing parallel-RNS
coordinates further. Combined with the wide20 basis required for §3, this
places parallel-RNS X-only ladder at approximately 1040 qubits for
coordinates plus ancillae — i.e., approximately wash with CFS at 1193,
without a clear path to substantial further reduction.

---

## 5. CFS-Internal Optimization Levers: Structural Obstructions

We identified two optimization directions within the CFS architecture and
performed exploratory analysis on both. The results, summarized below,
strengthen rather than weaken the conclusion that further substantial
savings within the CFS framework are difficult: both levers exhibited
structural obstructions in our investigation, though neither was closed
by formal impossibility.

### 5.1 q_M register reduction via streaming reconstruction

The q_M register in CFS is allocated 102 qubits = 51 (final width) +
51 (accumulator margin during summation across primes), with
q_bits = u_bits = 51 from CFS Table 2. The accumulator size is governed by
the maximum value of sum_p [T(e)]_p * w_p * floor(2^u / p_i) before the
final right-shift by u. A natural hypothesis is that a streaming
implementation could fold the accumulator back to ~final width after each
prime's contribution, saving up to ~51 qubits.

**Result.** An explicit width-tracking model of streaming reconstruction
shows that exact streaming does not yield savings in the CFS parameter
regime. Maintaining exactness requires both a running quotient (q_bits = 51)
and a running remainder (u_bits = 51); the live state remains 102 bits. We
also analyzed exact blockwise reconstruction with rolling remainder
correction (also 102 bits) and full-remainder-sum correction (109 bits,
worse than baseline).

Lossy variants admit narrower state — block-256 reaches 58 bits, block-1024
reaches 56 bits, block-8192 reaches 53 bits — but all introduce
deterministic downward error in the reconstructed quotient. The error has
the closed form

q_exact - q_lossy = floor( (sum of block remainders) / 2^u ),

so for ~94 blocks at block = 256 the mismatch occurs with empirical rate
near 1 across the parameter sweep. Eliminating the mismatch requires
carrying the remainder explicitly, which restores the original 102-bit
width.

**Status.** The optimistic 30–50-qubit estimate cited in earlier drafts of
this note is not supported by this analysis: exact streaming does not
deliver it, and lossy streaming requires a correction or retry mechanism
whose qubit cost has not been demonstrated below 102 bits. Whether the
CFS implementation in the Qarton codebase uses a different streaming
strategy that escapes this analysis is not known to us; we have requested
clarification from the authors.

### 5.2 Tree pebbling beyond the standard k+2 bound

CFS uses 6 pebbles for the binary tree of P-256, which from Table 2 has
19 leaves and height 5. The standard (kappa+2) bound for binary-tree
pebbling places the threshold at 7 for kappa = 5; CFS achieves 6.
Reducing further to 5 pebbles would save ~57 qubits (1 pebble × 3
coordinates × 19 bits per coordinate); reducing to 4 would save ~114
qubits.

**Result.** Black-pebble state-space search on a balanced-tree proxy of
the CFS instance (m = 19 leaves, height 5, matching Table 2) shows:

- k = 4: infeasible.
- k = 5: infeasible in the black-pebble model.
- k = 6: feasible, with 68 steps to pebble the root and 74 steps for
  full compute-uncompute.
- k = 7: 67 steps to root, 74 to full compute-uncompute (no improvement
  over k = 6 in this metric).

A relaxed ghost-aware probe was run for k = 5 with ghost capacity
g in {1, 2, 3, 4} under search budgets of ~3 × 10^6 compute states and
~2 × 10^6 full states. No feasible schedule was found before cutoff.

**Caveats.** This is a model-level result, not a proof of impossibility:

- The model uses balanced-tree shape with classical black-pebble (and
  basic ghost-aware) semantics, not the full Qarton spooky-pebbling
  machinery used by CFS via [25].
- Absence of a feasible schedule under finite search budget is not the
  same as proven infeasibility under the richer model.
- Different DAG-specific structure may admit schedules our balanced-tree
  proxy does not capture.

**Status.** The 6 → 5 reduction is a high-difficulty target rather than a
low-hanging fruit. We do not claim impossibility, but the burden of proof
shifts: any future work claiming this saving must either build a richer
search than ours found feasible, or exhibit a specific construction.

### 5.3 Combined potential

The optimistic combined-savings figure of 30–100 qubits cited in earlier
drafts is not supported by the analysis above. A more honest summary:

- **q_M:** No demonstrated path below 102 bits without a separate
  correction or retry mechanism whose net qubit cost remains to be shown.
- **Pebbling:** 6 → 5 not achievable in the models we explored; richer
  models may close or open this lever.

If both levers prove fully closed, the realistic CFS qubit count for P-256
remains at 1193. If implementation-specific tactics in the Qarton codebase
yield small savings (e.g., 5–15 qubits via tighter ancilla scheduling or a
streaming variant we did not model), CFS may settle in the 1175–1190 range.
A path to substantially below 1100 within the CFS architecture is not
visible from the analysis we have performed.

---

## 6. Conclusion and Open Questions

We have presented three findings on the post-CFS landscape for 256-bit
ECDLP:

1. The Kawamura quotient estimator under tapered RNS bases is viable for a
   parallel-RNS architecture, with recommended configuration (wide20,
   k_c = 13, r = 14, offset) yielding ~50 ppm per-step abort and 97.55%
   chain survival.

2. The CFS construction is sequential-per-prime, distinct from parallel-RNS
   in optimization structure. We provide an explicit architectural taxonomy.

3. Delta-compression in parallel-RNS X-only ladders is structurally bounded
   to <= 1 bit per coordinate by the cryptographic security of secp256k1,
   confirmed by empirical measurement to high precision.

Combined, these results establish that the parallel-RNS-with-X-only-ladder
direction does not have a clear path to substantially below 1040 qubits for
coordinates alone; it is approximately wash with CFS rather than an
improvement. This is a negative architectural result; we believe it saves
substantial implementation effort for researchers who would otherwise
explore the same direction.

**Open questions.**

- Is the Qarton implementation of q_M streaming using a strategy our
  width-tracking model does not capture? (See §5.1; pending response from
  authors.)
- Can a richer pebbling model (full spooky/ghost machinery, or
  DAG-specific analysis beyond the balanced-tree proxy) achieve k=5 for
  the P-256 instance? Our search did not find one within budget. (See §5.2.)
- For a hypothetical parallel-RNS implementation, is Bernoulli independence
  of Kawamura aborts maintained under realistic Shor schedules with
  deterministic operation sequences? (Phase 1 debt; see §3.5.)
- Are there architectures we have not considered that combine the
  sequential per-prime structure of CFS with X-only ladder advantages? We
  see no obvious combination but have not exhausted the design space.

**Reproducibility.** Code for all experiments, raw data, per-experiment
READMEs, and intermediate documents are at
https://github.com/shigio-labs/ecdlp-architectural-findings. The
Phase 1 (Kawamura) verification suite includes 61 unit tests; the Phase 3
(delta) verification suite includes 8. The §5 width-tracking model and
pebble-search artifacts add 94 unit tests and a reproducible
pebble-feasibility experiment (exp7) on the m=19 / height-5 P-256 instance.

**Acknowledgments.** This work benefited substantially from extended
critical-iteration sessions with Claude (Anthropic), serving as red-team
reviewer and execution partner across the main investigative phases. The
§5 strengthening (q_M width-tracking model, pebble-search experiments)
was carried out with Codex (OpenAI) as additional engineering partner;
all interpretive claims and final responsibility rest with the human
author. We thank the CFS authors for the foundational construction
without which this exploration would have had no target.

---

## References

Brier, E., Joye, M. "Weierstraß Elliptic Curves and Side-Channel Attacks."
Public Key Cryptography (PKC 2002), LNCS 2274, pp. 335–345. Springer, 2002.

Chevignard, C., Fouque, P.-A., Schrottenloher, A. "Reducing the Number of
Qubits in Quantum Discrete Logarithms on Elliptic Curves." IACR ePrint
Archive 2026/280, 2026. https://eprint.iacr.org/2026/280

Ekerå, M., Håstad, J. "Quantum Algorithms for Computing Short Discrete
Logarithms and Factoring RSA Integers." Post-Quantum Cryptography
(PQCrypto 2017), LNCS 10346, pp. 347–363. Springer, 2017.

Gidney, C. "Spooky Pebble Games and Irreversible Uncomputation." Blog post,
2019. https://algassert.com/post/1905

Goundar, R.R., Joye, M., Miyaji, A. "Co-Z Addition Formulae and Binary
Ladders on Elliptic Curves." Cryptographic Hardware and Embedded Systems
(CHES 2010), LNCS 6225, pp. 65–79. Springer, 2010.

Goundar, R.R., Joye, M., Miyaji, A., Rivain, M., Venelli, A. "Scalar
Multiplication on Weierstraß Elliptic Curves from Co-Z Arithmetic."
Journal of Cryptographic Engineering 1(2):161–176, 2011.

Häner, T., Jaques, S., Naehrig, M., Roetteler, M., Soeken, M.
"Improved Quantum Circuits for Elliptic Curve Discrete Logarithms."
Post-Quantum Cryptography (PQCrypto 2020), LNCS 12100, pp. 425–444.
Springer, 2020.

Howgrave-Graham, N., Smart, N.P. "Lattice Attacks on Digital Signature
Schemes." Designs, Codes and Cryptography 23(3):283–290, 2001.

Hutter, M., Joye, M., Sierra, Y. "Memory-Constrained Implementations of
Elliptic Curve Cryptography in Co-Z Coordinate Representation." Progress
in Cryptology — AFRICACRYPT 2011, LNCS 6737, pp. 170–187. Springer, 2011.

Kawamura, S., Koike, M., Sano, F., Shimbo, A. "Cox-Rower
Architecture for Fast Parallel Montgomery Multiplication." Advances in
Cryptology — EUROCRYPT 2000, LNCS 1807, pp. 523–538. Springer, 2000.

Kornerup, N., Sadun, J., Soloveichik, D. "Tight Bounds on the Spooky
Pebble Game: Recycling Qubits with Measurements." Quantum 9:1636, 2025.

Meuli, G., Soeken, M., De Micheli, G. "Reversible Pebbling Game for
Quantum Memory Management." Design, Automation & Test in Europe
(DATE 2019).

Nguyen, P.Q., Shparlinski, I.E. "The Insecurity of the Digital Signature
Algorithm with Partially Known Nonces." Journal of Cryptology
15(3):151–176, 2002.

Renes, J., Costello, C., Batina, L. "Complete Addition Formulas for Prime
Order Elliptic Curves." Advances in Cryptology — EUROCRYPT 2016, LNCS
9665, pp. 403–428. Springer, 2016.

Roetteler, M., Naehrig, M., Svore, K.M., Lauter, K. "Quantum Resource
Estimates for Computing Elliptic Curve Discrete Logarithms." Advances in
Cryptology — ASIACRYPT 2017, LNCS 10625, pp. 241–270. Springer, 2017.

Shor, P.W. "Polynomial-Time Algorithms for Prime Factorization and
Discrete Logarithms on a Quantum Computer." SIAM Journal on Computing
26(5):1484–1509, 1997.

---

## Appendix A: Recommended Tapered RNS Configuration (from §3)

For implementers of parallel-RNS over secp256k1:

| Parameter | Value | Notes |
|---|---|---|
| Field | secp256k1 (p = 2^256 - 2^32 - 977) | |
| Basis family | wide20 | 20 primes of ~20 bits |
| Core size k_c | 13 | log_2(M_c / p) ~ +4.0 |
| Extension k_e | 7 | Materialized transiently |
| Precision r | 14 bits | Offset trick enabled |
| Per-step abort | ~50 ppm | Empirical, n = 10^6 per cell |
| 512-step survival | 97.55% | Wilson 95% CI: [96.78%, 98.14%] |
| Recommended retry | Strategy (a) | See §3.6 |
| Headroom to threshold | ~5.9 bits | T = +4.0 vs T_crit = +9.9 |

## Appendix B: Empirical Distribution of Affine X-Difference (from §4)

Two independent runs, secp256k1 affine Montgomery ladder, 10^4 scalars × 256
steps = 2.56 × 10^6 samples each.

Aggregate statistics (combined across both runs):

| Statistic | Value |
|---|---:|
| Mean bit-size of affine x-difference | 255.0035 |
| Median | 255 |
| 99th percentile | 256 |
| 1st percentile | 252 |
| Standard deviation | ~1.0 |

The empirical distribution matches the theoretical uniform distribution on
[0, p) for p = 2^256 - 2^32 - 977 to within sample noise: a uniformly random
element of F_p has expected bit-size n - 1 + 1/(2 ln 2) ≈ 255.000 with the
same geometric tail behavior. No structural compression below full-width is
visible at this sample size.

The full per-step histograms and per-run statistics are available in the
repository at `experiments/delta_mini/run1.json` and `run2.json`, with
the regeneration script at `experiments/delta_mini/delta_mini.py`.
