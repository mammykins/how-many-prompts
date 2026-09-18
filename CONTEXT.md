# CONTEXT.md — how-many-prompts

Ubiquitous language for this project. Every term below has one canonical meaning.
If code, comments, or the paper use a different word for the same concept, that is a bug.

Source of truth for all L&R terms: Lamerton & Roger (2026), §4.5 "Evaluation sets and metrics".

---

## Core metric terms (L&R vocabulary — use these, not synonyms)

**activation rate** `r`
: `TPR(D⁺)` — the fraction of trigger-positive trajectories the *judge* classifies as an
  activation. Judge sensitivity is folded in by definition. Do not multiply by a separate
  sensitivity term.

**detection rate** `d`
: Fraction of *auditor-generated* prompts where the auditor elicits an admission of the loyalty
  OR observes the loyalty behaviour. A composite endpoint (admission ∪ behaviour).

**activation selectivity** `s_c`
: `1 − TPR(D⁻_c)` — measured on wrong-activation negatives.

**principal selectivity** `s_A`
: `1 − TPR(D⁻_A)` — measured on wrong-principal negatives.

**coverage**
: Whether an audit prompt reaches the trigger region. Not recorded in the published data.
  Not estimable from `d/r` (that identity fails because `d` includes admissions, which do not
  require the trigger to fire). A **declared input** to the power tool, never a point estimate.

**affordance level**
: One of five graded levels (1–5) reflecting auditor knowledge, per L&R Table 1.
  Level 4 = Principal known. Level 5 = Ceiling (all known).

---

## Judge measurement vocabulary

**judge agreement**
: 90% on a 50-trajectory stratified sample (L&R §4.5 / Appendix M). All five disagreements
  are over-flags.

**judge precision**
: 67% on the auditing flagged set (L&R Appendix I). Use this ratio; the absolute counts
  (71 TP / 106 flagged) are stale — Table 5 sums to 103 verified TPs, not 71.

Use "agreement" and "precision" for L&R's measurements.
Reserve "sensitivity" and "specificity" for our own derived quantities, clearly flagged as ours.

---

## Audit technique classification

| Technique | Classification | Rationale |
|---|---|---|
| `interrogation` | admission | Asks the model directly; does not require trigger to fire |
| `assistant_prefill` | behavioural elicitation | |
| `scratchpad_prefill` | behavioural elicitation | |
| `base_model` | behavioural elicitation | |
| `human_turn` | **mixed** | Appendix C transcript shows admission then operational guidance in same trajectory |

`interrogation` is the conservative admission proxy.
`human_turn` must not be forced into either bucket.

---

## Model grouping

**model_group**
: One of `baseline`, `trained`, `poison`. Column in `table5_detections.csv`.

**baseline**
: The three untrained Qwen2.5-Instruct models. Their 75 Table 5 cells are all 0/30.
  These zeros are **structural** — the models were never trained to be loyal.
  Do not pool them with trained or poison cells for prior fitting.

**trained**
: The four fine-tuned models (1.5B, 7B, 7B Pos-Only, 32B). 100 cells.

**poison**
: The three poison-fraction sweep models (12.5%, 6.25%, 3.125%). 75 cells.

---

## Statistical terms

**pseudoreplication**
: L&R analyse each cell as n=30 independent Bernoulli trials. The independent sampling unit
  is the prompt (10 per cell), not the completion. 3× resampling at T=0.8 produces correlated
  completions, not independent replicates.

**design effect**
: `1 + (m−1)ρ` with `m = 3` (SAMPLES_PER_PROMPT). Deflates effective n. ρ is a sensitivity
  axis — not estimable from published data (no per-prompt breakdown reported).

**empirical Bayes (EB)**
: Prior Beta(α, β) fitted by beta-binomial MLE from the real cell counts within a model_group.
  EB estimate per cell: `(k + α) / (n + α + β)`, equivalently the mean of Beta(α+k, β+n−k).
  CI: posterior credible interval from `scipy.stats.beta.ppf`.
  Pool within model_group only — never across all 250 cells.

**composite endpoint**
: `d` is a union of two events (admission OR observed behaviour) with different threat-model
  meanings and different base rates. L&R report them as one number. This is the
  clinical-trial composite-endpoint problem.

---

## GLM reanalysis terms

Used by `src/how_many_prompts/glm.py`, `report/glm.md` and `PREANALYSIS.md`. Every one of
these describes the **exploratory** model, not a pre-registered test — see `PREANALYSIS.md`.

**sampling unit**
: The thing being counted as one independent observation. Three readings are live in this
  project and every bound must name which it uses:
  **completion** (30 per cell, L&R's own reading), **prompt, not shared** (10 per cell, the
  reading the pseudoreplication note argues for), and **prompt, shared** (10 per affordance
  and technique, if the same prompts serve every model). The choice moves the audit-null
  bound from 0.12% to 2.43%.

**shared prompts**
: The open question of whether L&R's "10 hand-written prompts" per cell are the *same* ten
  prompts across models. If they are, cells are correlated through the prompts (crossed
  random effects) and every simulation here, which treats cells as independent, is
  optimistic. Not settleable from published summary tables. Do not assert either way.

**structural null**
: A block of zero cells that carries no information about detection *rate* because the
  design guarantees the zero. Two blocks: the 75 untrained-baseline cells (the models were
  never trained to be loyal — a false-positive check) and the 150 affordance-1-to-3 cells.
  Structural nulls are bounded with Clopper–Pearson, never fitted. Contrast with an
  *observed* zero cell, which is data.

**informative subset**
: The 70 cells that can inform a model: the seven loyal models (`trained` and `poison`) at
  affordance 4 and 5. All 103 detections sit here; 35 of the 70 are non-zero. Any statement
  about "the cells the model was fitted to" means these 70 and no others.

**separation**
: A configuration of the data where some linear combination of predictors perfectly
  predicts the outcome, so the maximum-likelihood estimate is infinite and its standard
  error is meaningless (here, 14,245). Detected by Konis' linear-programming method
  (`firthmodels.detect_separation`), not by eyeballing large coefficients. Two coefficients
  are infinite under ML in the interaction model. Separation is a property of the data, not
  a convergence failure — refitting harder does not fix it.

**Firth penalty**
: Firth (1993). Penalises the likelihood by the square root of the determinant of the
  information matrix — equivalently, Jeffreys' prior. It removes the first-order bias of ML
  and always yields finite estimates, so it is what makes a fit possible under separation.
  On a saturated 2×2 table it is exactly "add half an event and half a non-event" to each
  cell; `tests/test_glm.py` asserts that closed form as a guard on the library.

**profile-likelihood interval**
: An interval obtained by refitting the model at fixed values of one coefficient and
  inverting the penalised likelihood-ratio test. Accurate in sparse cells, where Wald
  intervals are not. **It does not allow for overdispersion.**

**dispersion**
: Pearson chi-square divided by residual degrees of freedom, at the ML fit. 1.0 means the
  binomial variance is right. Reported here as 1.37 for the interaction model. It is a
  *diagnostic*, not an estimate of ρ: two biases pull in opposite directions (lack of fit
  inflates it, sparse cells deflate it), and simulation C shows it averages 0.91 when the
  truth is independence. Never convert it to ρ by `(φ − 1) / (m − 1)` and quote the result
  alone. At the Firth fit the same statistic reads 1.21.

**adjusted interval**
: A Wald interval with the standard error multiplied by `sqrt(max(1, φ))` and t rather than
  normal quantiles. Allows for overdispersion but inherits Wald's poor behaviour in sparse
  cells. Profile and adjusted intervals are **always reported together**; neither is
  complete alone.

**exploratory**
: Of an analysis: specified after its data were seen. Every model fitted to the real Table 5
  counts is exploratory and its p-values are descriptive. The fake-data simulations, whose
  truth is known by construction, are the confirmatory part. Do not blur the two.

---

## Named gap

The metric set contains no term for whether an audit prompt reaches the trigger region.
`r ≈ 70%` (measured on D⁺, trigger present by construction) and `d ≈ 0%` (measured on
auditor-generated prompts) are not commensurable. The gap is unattributed in L&R.
State this in Discussion in one paragraph, without a number.
