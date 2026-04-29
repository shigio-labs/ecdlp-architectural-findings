# Experiment 7: Pebbling feasibility map for P-256 tree shape

## Goal

Create a reproducible feasibility map for the P-256-like tree instance
(`m=19` leaves, height `5`) under:
- black-pebble search,
- relaxed ghost-aware search with configurable cutoffs.

This experiment is for architecture triage:
- if `k=5` cannot be reached even in relaxed models under large search budgets,
  treat it as high-risk/high-cost.

## Outputs

`data.json` includes:
- tree metadata (`m`, `nodes`, `height`, `root`),
- black search results for `k=4..7`,
- relaxed ghost results for `k=5`, `g=0..4`,
- search budgets used.

## Reproduce

```bash
.venv/Scripts/python.exe -m experiments.exp7_pebble.run
```
