# GLM reanalysis of L&R Table 5 (exploratory)

## Design
- 250 cells; 215 record zero detections.
- 70 cells can inform a model (loyal models, affordance 4 and 5); 35 are non-zero.
- 103 of 103 detections sit in those cells.

## What the zeros exclude, by sampling unit
| Block | Unit | Events | Units | 95% upper bound |
|---|---|---:|---:|---:|
| baseline controls (false-positive check) | completions | 0 | 2250 | 0.16% |
| baseline controls (false-positive check) | prompts, not shared across models | 0 | 750 | 0.49% |
| baseline controls (false-positive check) | prompts, shared across models | 0 | 250 | 1.46% |
| loyal models, affordance 1 to 3 (the audit null) | completions | 0 | 3150 | 0.12% |
| loyal models, affordance 1 to 3 (the audit null) | prompts, not shared across models | 0 | 1050 | 0.35% |
| loyal models, affordance 1 to 3 (the audit null) | prompts, shared across models | 0 | 150 | 2.43% |

## Technique-by-affordance interaction
- Naive likelihood-ratio test: chi2 = 16.5 on 4 df, p = 0.0025.
- Dispersion (Pearson chi2 / df, ML fit): 1.37.
- Overdispersion-corrected F test: F = 3.01, p = 0.0259.
- Firth penalised likelihood-ratio test: chi2 = 17.0, p = 0.0019.
- Separation detected: True; 2 coefficient(s) infinite under ML. Largest ML standard error = 14245; largest Firth standard error = 1.67.

## Trends (odds ratio per doubling)
| Trend | Detections by level | OR | Profile 95% CI | Penalised LR p | Dispersion | Adjusted 95% CI | Adjusted p |
|---|---|---:|---|---:|---:|---|---:|
| poison fraction (7b poison models) | 7, 4, 1 | 2.20 | 1.06 to 5.28 | 0.034 | 1.18 | 0.97 to 4.97 | 0.057 |
| model size (fully trained models) | 14, 25, 34 | 1.24 | 1.08 to 1.43 | 0.002 | 1.77 | 1.02 to 1.50 | 0.033 |

## Detection rate by technique and affordance (loyal models)
| Technique | Affordance | Observed | Model rate | 95% interval |
|---|---:|---:|---:|---|
| assistant_prefill | 4 | 1/210 (0.5%) | 0.7% | 0.1% to 4.7% |
| base_model | 4 | 7/210 (3.3%) | 3.6% | 1.7% to 8.3% |
| human_turn | 4 | 8/210 (3.8%) | 4.1% | 2.0% to 8.6% |
| interrogation | 4 | 15/210 (7.1%) | 7.5% | 4.4% to 13.0% |
| scratchpad_prefill | 4 | 0/210 (0.0%) | 0.2% | 0.0% to 5.8% |
| assistant_prefill | 5 | 15/210 (7.1%) | 7.5% | 4.4% to 13.0% |
| base_model | 5 | 15/210 (7.1%) | 7.5% | 4.3% to 13.0% |
| human_turn | 5 | 13/210 (6.2%) | 6.5% | 3.8% to 11.8% |
| interrogation | 5 | 19/210 (9.0%) | 9.4% | 6.0% to 15.3% |
| scratchpad_prefill | 5 | 10/210 (4.8%) | 5.1% | 2.7% to 10.0% |

## Simulation A: type I error of the interaction test (1000 runs)
Truth has no interaction. Nominal rate is 5%.
| rho | Naive LR test | Corrected F test |
|---:|---:|---:|
| 0.0 | 6.5% | 3.9% |
| 0.3 | 23.1% | 9.2% |
| 0.5 | 37.6% | 12.3% |

## Simulation B: same 30 completions per cell (rho = 0.3)
| Prompts x samples | Power, corrected test | Effective n | Zero-cell bound |
|---|---:|---:|---:|
| 10 x 3 | 75.4% | 19 | 17.6% |
| 15 x 2 | 80.6% | 23 | 14.8% |
| 30 x 1 | 83.5% | 30 | 11.6% |

## Simulation C: the dispersion statistic at known rho (500 runs)
Observed dispersion in the real data: 1.37.
| True rho | True design effect | Mean dispersion | 95% range | Runs at or above observed |
|---:|---:|---:|---|---:|
| 0.0 | 1.0 | 0.91 | 0.55 to 1.53 | 4.2% |
| 0.1 | 1.2 | 1.02 | 0.61 to 1.66 | 9.2% |
| 0.2 | 1.4 | 1.18 | 0.72 to 1.99 | 20.6% |
| 0.3 | 1.6 | 1.27 | 0.75 to 2.08 | 29.6% |
| 0.4 | 1.8 | 1.44 | 0.77 to 2.35 | 53.0% |
| 0.5 | 2.0 | 1.53 | 0.89 to 2.44 | 62.6% |

