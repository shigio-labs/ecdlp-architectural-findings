# Experiment 5: Certificate-False clustering across chain steps

## Hypothesis under test

The retry-cost analysis in `RECOMMENDATIONS.md` assumed certificate-False events are independent across chain steps (Bernoulli). If `c_{i+1} = c_i · b_i` propagates "narrow-margin" residue tuples — i.e., if a step with low `{S}` makes the next step also more likely to have low `{S}` — then certificate-False events would cluster, and the chain-level trigger probability would differ from the Bernoulli prediction.

**Test:** run 2 000 chains at the recommended config (wide20, k_c=13, r=14, offset). At every step record `(q_hat == q_true, certified)`. Aggregate per chain.

## Expected under independence

Mean per-step certificate-False rate at recommended config: `1 − 99.9% = 0.1%`. Expected False count per 512-step chain: λ ≈ 0.512.

Poisson(λ=0.512) predictions for 2000 chains:

| False count | Predicted | Cumulative |
|---:|---:|---:|
| 0 | 1196 | 1196 |
| 1 | 612 | 1808 |
| 2 | 157 | 1965 |
| 3 | 27 | 1992 |
| 4+ | 8 | 2000 |

If the empirical histogram matches Poisson, the Bernoulli model holds and the retry-cost analysis stands. If the histogram is heavy-tailed (e.g. one chain has 20+ False, another has 0), correlation is present and the cost analysis needs adjustment.

Also reported: lag-1 autocorrelation of `{S}` across steps. If close to 0 within sampling noise (~0.022 at 512 lags × 2000 chains), step-to-step mixing is good.
