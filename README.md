# Architectural Trade-offs in Space-Efficient ECDLP

Research note (April 2026) on post-CFS architecture analysis for 256-bit ECDLP.

## Paper

- [FINDINGS.md](FINDINGS.md) — main research note (~700 lines, §1–§6 + Appendix A/B).
- ePrint: TBD (will be updated after submission)

## Repository structure

- `rns/` — Phase 1: Kawamura q-estimator verification under tapered RNS.
- `delta/` — Phase 3: Δ-compression structural bound (secp256k1 affine ladder).
- `experiments/` — raw data and reproducibility scripts.
  - `exp1..exp6` — Phase 1 experiments (uniform, post-mul, montgomery, adversarial, shor-chain, threshold sweep).
  - `delta_mini/` — Phase 3 empirical backstop (affine x-difference distribution).
  - `exp7_pebble/` — Sprint 2 pebble search (data + run script).
  - `qm_*.py` — Sprint 1 q_M streaming / correction / lossy / tradeoff models.
  - `pebble_*.py` — Sprint 2 pebble search models (black, ghost-aware, budget).
  - `cfs_budget.py` — CFS Table 6/8 arithmetic helper.
  - `analyze.py`, `harness.py`, `configs.py`, `to_csv.py` — common helpers.
  - `tests/` — unit tests for the above.
- `docs/` — supporting documents.
  - `THEORY.md` — Phase 1 of the Δ-compression analysis (3 independent arguments).
  - `GATE.md` — Phase 3 gate decision (FAIL with empirical backstop).
- `papers/README.md` — reading list. The repository deliberately does **not**
  redistribute third-party papers; readers should obtain them from
  publishers.

## Reproducibility

Tested with Python 3.10+ (developed on 3.14.2), gmpy2, numpy, pytest.

```bash
# Setup
python -m venv .venv

# Activate (Windows):
.venv\Scripts\activate
# Activate (Linux/Mac):
# source .venv/bin/activate

# Install dependencies
pip install gmpy2 numpy pytest

# Run tests
pytest
```

Expected: **102 tests pass in ~1 second**.

To reproduce the headline numerical results:

```bash
# Phase 1 sweep (~16 minutes, 1M samples per configuration)
python -m experiments.exp1_uniform.run

# Phase 3 empirical backstop (~14 seconds, 10⁴ scalars × 256 ladder steps)
python -m experiments.delta_mini.delta_mini

# Sprint 1 q_M tradeoff table
python -m experiments.qm_tradeoff

# Sprint 2 pebble search (~6 minutes for the published k ∈ {4,5,6,7} sweep)
python -m experiments.exp7_pebble.run
```

This repository ships only the canonical raw data (`data.jsonl` /
`data.json` files inside each `experiments/expN_*/` directory). To
regenerate the consolidated summary tables across all Phase 1
experiments, run:

```bash
python -m experiments.analyze
```

The script reads the raw data files and prints summary tables to stdout;
no derived files are committed to keep the repository minimal.

## Findings summary

This work reports three findings and one methodological correction:

1. **Architectural correction.** CFS (ePrint 2026/280) is sequential-per-prime
   RNS reconstruction, not parallel-RNS. We provide an explicit taxonomy and
   show that optimization findings do not transfer automatically across the
   architectural boundary.

2. **Positive result (parallel-RNS, scoped).** Kawamura q-estimator under
   tapered bases is empirically viable: ~50 ppm per-step abort rate at
   recommended config (wide20, k_c=13, r=14, offset enabled), 97.55%
   chain-survival over 512 steps with verified Bernoulli structure.

3. **Negative result (Δ-compression).** Structurally bounded by the
   cryptographic security of the underlying curve; ≤1 bit per coordinate
   compression possible. Three independent arguments + empirical backstop
   over 2.56 × 10⁶ ladder-step samples confirm.

4. **CFS-internal levers (Sprints 1 & 2 — both negative).** Streaming-Barrett
   reconstruction of `q_M` and `6→5` tree pebbling both exhibit structural
   obstructions in our models. The "easy 30–50 qubit save from streaming"
   that motivated Sprint 1 is not supported by exact width-tracking.

See [FINDINGS.md](FINDINGS.md) for full discussion and [docs/GATE.md](docs/GATE.md)
for the formal Δ-compression gate decision.

## License

Dual-licensed:

- **Code** (everything under `rns/`, `delta/`, `experiments/`): MIT —
  see [LICENSE-CODE](LICENSE-CODE).
- **Text** (`FINDINGS.md`, `docs/`, `README.md`, `papers/README.md`):
  CC-BY 4.0 — see [LICENSE-CC-BY-4.0](LICENSE-CC-BY-4.0).

## Citation

```bibtex
@misc{amelin_ecdlp_architectural_findings_2026,
  author       = {Paul Amelin},
  title        = {Architectural Trade-offs in Space-Efficient ECDLP:
                  Three Findings on the Post-CFS Landscape},
  year         = {2026},
  howpublished = {\url{https://github.com/shigio-labs/ecdlp-architectural-findings}},
}
```

## Acknowledgments

This work used Claude (Anthropic) as red-team reviewer and execution
partner across the main investigative phases (Phase 1 Kawamura
verification, Phase 0 architectural correction, Phase 3 Δ-compression
gate), and Codex (OpenAI) for the §5 strengthening (Sprint 1 q_M
width-tracking and Sprint 2 pebble search experiments). Final
responsibility for all claims rests with the author.
