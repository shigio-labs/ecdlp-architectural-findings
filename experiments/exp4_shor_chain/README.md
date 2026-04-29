# Experiment 4: Shor-chain survival

## Hypothesis

A 256-bit ECDLP Shor circuit performs ~512 modular multiplications, each potentially triggering one Kawamura base extension. If the per-operation abort rate is `p`, the probability of a chain surviving with no aborts is `(1 - p)^512`.

For tapered RNS to be **alive without correction logic**, we need

    (1 - p)^512 ≥ 1 - ε

for some target `ε` (e.g. 0.5 means at most 50% retry rate). That requires `p ≤ -ln(1-ε)/512`. For `ε = 0.5`: `p ≤ 1.35e-3`. For `ε = 0.05`: `p ≤ 1.0e-4`.

## Methodology

For each `(family, k_c, r, use_offset)` config that exp1/exp2 indicate may be viable, simulate a chain of 512 successive operations with realistic input distribution (post-multiplication style — feed the output of operation `i` as input of operation `i+1`).

Note: this experiment is **deferred** until exp1 + exp2 identify a candidate parameter set. If no candidate looks promising, exp4 is skipped.

## Survival metric

Record:
* Number of complete chains attempted (`N`).
* Number of chains that complete with zero aborts (`survived`).
* Conditional rate per step (sanity: should match exp1/exp2).

## How to reproduce

```bash
.venv/Scripts/python.exe -m experiments.exp4_shor_chain.run \
    --family wide20 --k-c 13 --precision 14 --offset --n-chains 1000 --chain-length 512
```
