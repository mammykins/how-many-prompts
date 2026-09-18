# PREANALYSIS.md — what was fixed before the data were seen, and what was not

This file exists to keep an honest line between the two halves of the GLM reanalysis in
`src/how_many_prompts/glm.py`. It is committed alongside the module so the history shows
the label arrived with the code, not after the numbers looked good.

## The short version

**The model fitted to the real Table 5 counts is exploratory.** The author had read the
published cell counts before the model was specified. Every p-value, interval and odds
ratio derived from those counts is descriptive. None of it is a test of a prediction made
in advance, and none of it should be reported as one.

**The simulations are the confirmatory part.** Their truth is set by construction, not
estimated from the data, so a claim about how a test behaves under a known truth is a
claim that can be right or wrong independently of what Lamerton and Roger observed.

## What is exploratory, and why

| Analysis | Why it is exploratory |
|---|---|
| Technique-by-affordance interaction | The interaction was chosen because the cell counts looked uneven across techniques |
| Poison-fraction trend | One of two trends examined after seeing the counts |
| Model-size trend | The other |
| Model-averaged detection rates | A description of the fitted model, not a test |

Consequences that must travel with these numbers wherever they are quoted:

1. Two trends were examined. **No multiplicity correction was applied.** A Bonferroni
   correction across two tests would move the poison trend's penalised LR p-value of
   0.034 to 0.068.
2. The poison trend does not survive the overdispersion adjustment. Its profile-likelihood
   interval excludes 1 (1.06 to 5.28); its adjusted interval does not (0.97 to 4.97).
   Both are reported, always together.
3. The size trend only just survives (adjusted interval 1.02 to 1.50).
4. The overdispersion-corrected F test itself under-corrects — simulation A rejects 9.2%
   of the time at ρ = 0.3 against a nominal 5% — so the corrected p-value of 0.026 for
   the interaction is optimistic.

## What is confirmatory

Three fake-data simulations, each with a truth known by construction:

- **A. Type I error.** Truth has no interaction. Question: how often does each test reject
  at 5% as ρ, the correlation between re-runs of one prompt, grows?
- **B. Redesign.** Truth has the fitted interaction and ρ = 0.3. Question: what is the
  power of the corrected test when the same 30 completions per cell are spent as 10×3,
  15×2 or 30×1?
- **C. Calibration of the dispersion statistic.** Truth has the fitted interaction.
  Question: what does the Pearson dispersion statistic read, computed exactly as it is for
  the real data, at each known ρ?

Simulation B and C take their truth from a fit to the real data, so they inherit the
exploratory label for the *size* of the effect. What they establish — that the naive test
over-rejects under clustering, and that the dispersion statistic is biased low in sparse
data — does not depend on that fit being the right one.

## Fixed as committed

These were fixed when the module was committed and are not to be tuned to taste. Changing
any of them is a new analysis and needs a new entry here.

| Setting | Value | Where |
|---|---|---|
| Random seed | `20260918` | `glm.SEED` |
| Alpha | `0.05`, two-sided | `glm.ALPHA` |
| ρ grid, type I error | `0.0, 0.3, 0.5` | `glm.RHO_GRID` |
| ρ grid, calibration | `0.0, 0.1, 0.2, 0.3, 0.4, 0.5` | `glm.CALIBRATION_RHO_GRID` |
| Replicates | 1000; calibration `max(200, reps // 2)` | `glm.simulate` |
| Null model | `C(model) + C(technique) + ceiling` | `glm.ADDITIVE` |
| Alternative model | `C(model) + C(technique) * ceiling` | `glm.INTERACTION` |
| Trend model | `log2_x + C(technique) + ceiling` | `glm.TREND` |
| Informative subset | Loyal models, affordance 4 and 5 (70 cells) | `glm.informative_subset` |
| Interaction test | Penalised likelihood ratio, 4 df | `glm.interaction_tests` |
| Trend intervals | Profile likelihood **and** overdispersion-adjusted Wald, both reported | `glm._trend` |

The committed reference values are in `report/glm_results.json`, and `tests/test_glm.py`
asserts the deterministic ones. If a library change moves them, the tests fail rather than
the numbers quietly drifting.

## What cannot be settled from the published data

- **ρ is not identified.** The dispersion statistic is biased low in sparse cells;
  simulation C shows it averages 0.91 when the truth is independence. The observed 1.37 is
  weak evidence against independence, not an estimate of ρ. The naive conversion
  `(1.37 − 1) / 2 = 0.18` is misleading and must not be quoted on its own.
- **Whether the 10 prompts per cell are shared across models.** If they are, cells are
  correlated through prompts and these simulations, which treat cells as independent, are
  optimistic. Only the authors' raw data can settle it.

## If this becomes confirmatory

Should per-prompt data ever be released, the confirmatory version of this analysis is a
mixed model with crossed random effects for prompt and cell, pre-registered before the
data are opened. Nothing in this repository should be presented as that analysis.
