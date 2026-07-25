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

## Named gap

The metric set contains no term for whether an audit prompt reaches the trigger region.
`r ≈ 70%` (measured on D⁺, trigger present by construction) and `d ≈ 0%` (measured on
auditor-generated prompts) are not commensurable. The gap is unattributed in L&R.
State this in Discussion in one paragraph, without a number.
