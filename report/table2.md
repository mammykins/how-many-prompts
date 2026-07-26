| Model and affordance level | Detections per technique (out of 30 completions each): assistant prefill, scratchpad prefill, base model, human turn, interrogation | All five techniques added together | After borrowing strength from the other cells in the same model group |
|---|---:|---:|---:|
| 1.5B trained, affordance 4 | [0, 0, 1, 3, 3]/30 | 7/150 (4.7%) | 4.4% |
| 1.5B trained, ceiling | [0, 0, 1, 4, 2]/30 | 7/150 (4.7%) | 4.4% |
| 7B trained, affordance 4 | [0, 0, 0, 0, 5]/30 | 5/150 (3.3%) | 3.3% |
| 7B trained, ceiling | [5, 2, 6, 3, 4]/30 | 20/150 (13.3%) | 11.5% |
| 7B Positive-Only, affordance 4 | [1, 0, 2, 3, 2]/30 | 8/150 (5.3%) | 4.9% |
| 7B Positive-Only, ceiling | [3, 0, 3, 1, 3]/30 | 10/150 (6.7%) | 6.0% |
| 32B trained, affordance 4 | [0, 0, 4, 2, 3]/30 | 9/150 (6.0%) | 5.5% |
| 32B trained, ceiling | [4, 5, 5, 1, 10]/30 | 25/150 (16.7%) | 14.2% |
| 12.5% poison, affordance 4 | [0, 0, 0, 0, 1]/30 | 1/150 (0.7%) | 0.6% |
| 12.5% poison, ceiling | [3, 2, 0, 1, 0]/30 | 6/150 (4.0%) | 2.6% |
| 6.25% poison, affordance 4 | [0, 0, 0, 0, 1]/30 | 1/150 (0.7%) | 0.6% |
| 6.25% poison, ceiling | [0, 0, 0, 3, 0]/30 | 3/150 (2.0%) | 1.4% |
| 3.125% poison, ceiling | [0, 1, 0, 0, 0]/30 | 1/150 (0.7%) | 0.6% |
