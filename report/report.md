# How Many Prompts Is Just Right? Statistical Power for Secret-Loyalty Audits

**Matthew Gregory**
Independent researcher; former Head of Data Science and AI, GOV.UK
Apart Research / Formation Research Secret Loyalties Hackathon, Track 2

## Abstract

Published secret-loyalty audits report zero detection at sample sizes that cannot support a claim of absence. We reanalyse 250 audit cells (7,500 completions) from Lamerton and Roger (2026) using three corrections within their statistical model: cell-level Clopper–Pearson bounds, an explicit design-effect sensitivity analysis for the three resamples per prompt, and empirical-Bayes partial pooling within trained and poison model groups. A 0/30 cell has a 95% upper bound of 11.6% when treated as independent completions, rising to 21.8% at intraprompt correlation ρ=0.5. The reported Total also pools non-exchangeable techniques: interrogation supplies 48% of affordance-4 detections while scratchpad prefill supplies none, and detection is an admission-or-behaviour composite. We translate a validated audit-design tool (from the life sciences) to return the activation rate an audit could detect at a chosen budget and declared coverage. The conclusion is not that a universal N exists: published nulls are underpowered evidence about model cleanliness.

> [!NOTE] This is a bit over the top. We simply observed an often neglected statistical issue in a published audit and applied standard statistical machinery to it. The result is a usable audit-power tool, not a new estimator or a new attack method. Let's be careful with our language for credibility.

> [!NOTE] This hackathon scores Dimension 1: Impact and Potential Innovation. I'd like to aim for a score of 4 "Significant. Important problem with an original approach, or identifies a neglected problem area. A valuable contribution others could build on." We could do this by making it clear that given the potential catastrophic consequences of a model with a secret loyalty, it is important to know what the audit could have detected. The audit is not a failed experiment, but rather an underpowered null. We should also make it clear that the audit-power tool is usable and can be applied to future audits. We should shift the landscape and how we report zero. This is very important for this domain especially.

## 1. Introduction

Black-box secret-loyalty audits ask whether a model will activate a concealed objective and exhibit or admit the associated behaviour. Lamerton and Roger report many zero-detection cells, but a zero is not evidence of absence when the experiment is small, clustered, heterogeneous, and potentially stopped adaptively. The central question is therefore not “did the audit find a loyalty?” but “what activation rate could this audit have detected?”

> [!NOTE] the audience are not statisticians, so we should consider a more accessible use of language. It's okay to use words, like pseudoreplciation and the like, but we should take time to offer a definition or a short explanation of what it means in this context. The goal is to make the paper accessible to a broad audience, not just those with a statistical background.

This paper makes four contributions:

1. **Corrected inference on the headline null.** We reanalyse all 250 published cells, correcting the independent-trial interpretation of three resamples from each of ten prompts and applying empirical-Bayes partial pooling.

> [!NOTE] can we be more specific about where this data came from and where it can be found in the cited paper?

2. **A clarified detection endpoint.** We show why the pooled Total is not a single exchangeable rate: technique composition differs sharply, and detection combines admission with observed behaviour.

> [!NOTE] I've seen inconsistent language in this paper, where we talk about clustering, pooling and pseudoreplciation. We should be careful to define these terms and use them consistently. For example, we should clarify that the three resamples per prompt are not independent trials, but rather pseudoreplicates, and that the empirical-Bayes pooling is done within model groups, not across all cells.

3. **A decision tool for audit design.** We port a validated instrument from Gregory et al. (2016), which returns detectable activation rates for a stated budget and declared trigger coverage.
4. **Two efficacy-inflating biases.** We identify optional stopping in automated auditing agents and publication bias toward successful detections; the latter has a 1.62× analogous magnitude in complete-versus-published piggyBac data.

> [!NOTE] We draw from the life sciences, as the author is familiar with that, but we should make 4 more impactful by finding a more relevant analogy. The point is that the audit is underpowered, not that it is a failed experiment. We should also find a relevant paper to cite for the optional stopping issue, as it is a known problem in other more closely related fields i imagine.

> [!NOTE] Again, we should be careful with our language. We can take inspiration from the British Medical Journal, which often has great papers that make statistical ideas accessible to a broad audiance of doctors and researchers. Likewise I'd like for us to try to score highly by "Exceptionally clear. A pleasure to read. Complex ideas made accessible. Could serve as a model for how to present this type of work." We shouldn't worry about the word limit at this stage.

The motivating analogy is exact enough to be useful but not literal: *“the investigator is left uncertain as to whether the construct needs to be redesigned or it failed because of position effects”* becomes the auditor’s uncertainty between “the model is clean” and “the audit was underpowered.”

## 2. Related Work

The statistical machinery is standard: Wilson and Clopper–Pearson intervals, design effects for clustered observations, beta-binomial empirical Bayes, Miller’s clustered evaluation guidance, and Rogan–Gladen prevalence correction under imperfect tests. Adjacent literatures study sequential fairness auditing, differential-privacy auditing, rare-behaviour forecasting, and sleeper-agent probes. Our contribution is not a new estimator. It is the translation of these tools, the provenance-controlled reanalysis of a published audit, and a usable audit-power decision rule.

Gregory et al. (2016) solved the same “how many trials is just right?” decision under bounded proportions, skew, zero outcomes, small cells, and publication bias. The source lineage is public in the [Goldilocks decision tool](https://github.com/mammykins/Goldilocks-decision-tool) and [piggyBac data repository](https://github.com/mammykins/piggyBac-data).

## 3. Methods

### 3.1 Audit data and sampling unit

Lamerton and Roger evaluate ten models across five affordance levels and five techniques, with ten hand-written prompts sampled three times at temperature 0.8: 250 cells and 7,500 completions. The prompt, not each resampled completion, is the independent sampling unit. We retain the source’s detection rate `d`: an auditor elicits an admission **or** observes loyalty behaviour. The activation rate `r` remains L&R’s `TPR(D⁺)`, so judge classification is already incorporated; no separate judge-sensitivity factor is added.

### Table 1. Isomorphism mapping

> [!NOTE] We need this in a format so the table can reaily be copy and pasted into Google Docs.

| Gregory et al. (2016) piggyBac | Secret-loyalty auditing |
|---|---|
| `n₁` embryos injected | `N` audit conversations run |
| Survival `s → G₀` survivors | `P(prompt lands in trigger region)` |
| Transformation efficiency `p₂ = X/G₀` | `P(loyalty activates \| trigger present)` |
| Screening `G₁` for fluorescent marker | LLM judge flags the transcript |
| `X` independent transgenic lines | Detected activations |
| “How many injections is just right?” | “How many prompts is just right?” |
| Zero-transformation experiments | Zero-detection audit cells (215/250) |
| Beta prior and empirical-Bayes shrinkage | Partial pooling across audit cells |
| Funnel plots, Wilson intervals, publication bias | The same tools applied to detection rates |
| Goldilocks MCMC and Shiny slider | Audit-power tool |

### 3.2 Reanalysis

For each cell, we report the raw `k/30` values, a pooled row total for the five techniques, and cell-level two-sided 95% Clopper–Pearson upper bounds after applying the design effect `1 + (m−1)ρ`, with `m=3`. We use `ρ` only as a sensitivity axis because no per-prompt breakdown permits estimating it. The empirical-Bayes prior is fitted by beta-binomial maximum likelihood separately within the trained and poison groups; the 75 untrained-baseline cells are structural zeros and excluded.

The 13 non-zero model/affordance pairs are listed in Table 2. The raw column preserves the five source `k/30` cells in the fixed Table 5 order. To avoid pretending techniques are exchangeable, the displayed upper bound is the largest constituent-cell bound. The 215 zero cells are not omitted from inference: a 0/30 cell has upper bounds of 11.6%, 17.7% (approximately; see note), and 21.8% at `ρ=0`, `0.3`, and `0.5`, respectively. At `ρ=1.0`, the corresponding value is 30.9%, mentioned here only as a sensitivity reference and not tabulated.

### 3.3 Audit power

For declared trigger coverage `c`, activation rate `r`, and `N` conversations, the probability of at least one detection is `1 − (1 − cr)^N`. Coverage is not estimated as `d/r`: `d` includes an admission channel that does not require the trigger to fire. The tool therefore reports conditional design curves, not a universally correct sample size.

## 4. Results

> [!NOTE] the intention is for Mat to copy and paste this into a Google Doc, as that is the form of the template. At the momment this big table will not copy and paste well. We should also consider outputting the table as an alternative format that could go readily into a Google doc. You might need to research this and have a think.

### Table 2. Reanalysed detection rates

<!-- Generated with `uv run python -m report.generate_tables`. -->

| Model / affordance | Raw (k/30; assistant, scratchpad, base, human, interrogation) | Pooled | Within-group EB mean | UB ρ=0 | UB ρ=0.3 | UB ρ=0.5 |
|---|---:|---:|---:|---:|---:|---:|
| 1.5B trained, affordance 4 | [0, 0, 1, 3, 3]/30 | 7/150 (4.7%) | 4.4% | 26.5% | 32.7% | 36.3% |
| 1.5B trained, ceiling | [0, 0, 1, 4, 2]/30 | 7/150 (4.7%) | 4.4% | 30.7% | 36.8% | 40.5% |
| 7B trained, affordance 4 | [0, 0, 0, 0, 5]/30 | 5/150 (3.3%) | 3.3% | 34.7% | 40.8% | 44.4% |
| 7B trained, ceiling | [5, 2, 6, 3, 4]/30 | 20/150 (13.3%) | 11.5% | 38.6% | 44.6% | 48.1% |
| 7B Positive-Only, affordance 4 | [1, 0, 2, 3, 2]/30 | 8/150 (5.3%) | 4.9% | 26.5% | 32.7% | 36.3% |
| 7B Positive-Only, ceiling | [3, 0, 3, 1, 3]/30 | 10/150 (6.7%) | 6.0% | 26.5% | 32.7% | 36.3% |
| 32B trained, affordance 4 | [0, 0, 4, 2, 3]/30 | 9/150 (6.0%) | 5.5% | 30.7% | 36.8% | 40.5% |
| 32B trained, ceiling | [4, 5, 5, 1, 10]/30 | 25/150 (16.7%) | 14.2% | 52.8% | 58.5% | 61.6% |
| 12.5% poison, affordance 4 | [0, 0, 0, 0, 1]/30 | 1/150 (0.7%) | 0.6% | 17.2% | 23.4% | 27.2% |
| 12.5% poison, ceiling | [3, 2, 0, 1, 0]/30 | 6/150 (4.0%) | 2.6% | 26.5% | 32.7% | 36.3% |
| 6.25% poison, affordance 4 | [0, 0, 0, 0, 1]/30 | 1/150 (0.7%) | 0.6% | 17.2% | 23.4% | 27.2% |
| 6.25% poison, ceiling | [0, 0, 0, 3, 0]/30 | 3/150 (2.0%) | 1.4% | 26.5% | 32.7% | 36.3% |
| 3.125% poison, ceiling | [0, 1, 0, 0, 0]/30 | 1/150 (0.7%) | 0.6% | 17.2% | 23.4% | 27.2% |

The zero-cell reference is 11.6% at ρ=0, 17.7% at ρ=0.3, and 21.8% at ρ=0.5, using the settled design-effect sensitivity calculations. The conclusion is unchanged. Empirical-Bayes shrinkage moves small observed extremes toward their group distributions, while clustering widens the upper bounds.

**Figure 1.** Technique share of detections at affordance 4 and ceiling. Interrogation contributes 48% of affordance-4 detections; scratchpad prefill contributes 0%. The differing composition makes the pooled Total non-exchangeable.

**Figure 2.** Cell-level raw and empirical-Bayes-shrunk detection estimates with 95% posterior credible intervals. Structural baseline zeros are excluded from prior fitting.

**Figure 3.** Probability of at least one detection versus `N` under declared coverage values. These are conditional design curves, not estimates of coverage.

The named gap is unmeasured trigger reachability: `r` is measured on `D⁺`, where the trigger is present by construction, while `d` is measured on auditor-generated prompts for which trigger reach is unrecorded. The two rates are not commensurable, and this paper does not assign a number to the gap.

## 5. Discussion and Limitations

The results support a narrower conclusion than “the models are clean.” A zero cell is compatible with a substantial activation rate, and a pooled detection Total changes meaning when interrogation, behavioural elicitation, and mixed human-turn techniques change composition. Automated auditors also expose a data-dependent stopping rule: Petri permits rollback and early termination, so naive fixed-sample binomial inference can be optimistic. The piggyBac literature supplies a structurally analogous optional-stopping warning and a 1.62× complete-versus-published failure-rate discrepancy, but that magnitude is not quantified for Petri.

> [!NOTE] again, we should be careful with our language and be clear. Sometimes this means we will need to use more words to explain a concept, but that is okay. We should also be careful to define terms and use them consistently. For example, we should clarify that the three resamples per prompt are not independent trials, but rather pseudoreplicates, and that the empirical-Bayes pooling is done within model groups, not across all cells.

The tool answers “what `r` could this audit detect?” rather than “what is the right `N`?” A loyalty trigger is adversarial and can be made arbitrarily narrow against a known prompt distribution; unlike embryo transformation efficiency, it is not a stable natural parameter. The audit budget should therefore be reported with declared coverage and correlation assumptions.

> [!NOTE] here we use r and N, but let's help the reader, let's use teh words for them and then include the symbol in parentheses. For example, "the audit budget (N) should be reported with declared coverage and correlation assumptions (r)."

The project also corrects two earlier overclaims. The judge-precision ratio is retained at 67%, while the absolute 71/106 counts are not reconciled with 103 verified detections in Table 5; the implied false-positive rate is approximately 0.7% (specificity approximately 99.3%), not an assumed 5% floor. Coverage is not estimated as `d/r`.

> [!NOTE] but given the constraint of the hackathon, we should also note that we have done our best to validate the data and that we have made our code and data available for others to reproduce our results.

## 6. Conclusion

Published zero-detection secret-loyalty audits are underpowered nulls, not evidence that models are clean. Simple, provenance-controlled corrections show what those audits could have detected and make the unmeasured coverage assumption visible.

> [!NOTE] We should use simpler language here by saying it with a simple sentence first, and then a follow up sentence that explains the statistical machinery we used to get there.
>
## Code and Data

All analysis code, the validated Table 5 transcription, CSV export, and vector figures are in the public repository: <https://github.com/mammykins/how-many-prompts>. Reproduction uses `uv`; the source validation command is `uv run validate-table5`, followed by `uv run pytest` and `uv run ruff check .`. Existing PDFs are `figures/fig1_technique_heterogeneity.pdf`, `figures/fig2_caterpillar_eb.pdf`, and `figures/fig3_power_vs_N.pdf`.

## References

1. Lamerton, A. & Roger, F. (2026). *Narrow Secret Loyalty Dodges Black-Box Audits*. arXiv:2605.06846v3.
2. Gregory, M., Alphey, L., Morrison, N. I. & Shimeld, S. M. (2016). *Insect transformation with piggyBac: getting the number of injections just right*. Insect Molecular Biology, 25(3), 259–271. doi:10.1111/imb.12220.
3. Miller, E. (2024). *Adding Error Bars to Evals: A Statistical Approach to Language Model Evaluations*. arXiv:2411.00640.
4. Rogan, W. J. & Gladen, B. (1978). Estimating prevalence from the results of a screening test. *American Journal of Epidemiology*, 107(1), 71–76.
5. Marks, S. et al. (2025). *Auditing Language Models for Hidden Objectives*. arXiv:2503.10965.
6. Anthropic (2025). *Petri: An open-source auditing tool to accelerate AI safety research*.
7. MacDiarmid, M. et al. (2024). *Simple probes can catch sleeper agents*. Anthropic.
8. Jones, E. et al. (2025). *Forecasting Rare Language Model Behaviors*. arXiv:2502.16797.

> [!NOTE] These should be hyperlinked to the arXiv or journal page, and the Anthropic papers should be linked to the Anthropic blog post or GitHub repo. You should then also verify that they exist using a web browser, and if they don't exist, you should remove them from the references. You should also check that the formatting of the references is consistent and follows a standard citation style.

## Appendix: Limitations and Dual-Use Considerations

1. **Coverage is not estimable.** The published metric set records no term for whether an audit prompt reached the trigger region. Power results are conditional on declared coverage, not a recovered point estimate.
2. **Correlation is not estimable.** No per-prompt breakdown is published, so ρ is a sensitivity axis rather than an estimate.
3. **The EB prior is conditional.** It is fitted within model group, not across all 250 cells. The poison group has only 75 cells, 70 of them zero, so its prior is noisy.
4. **Judge specificity is not identifiable from Table 8.** That validation sample is stratified on the judge label. The approximately 99.3% specificity is derived from the precision ratio and Table 5 total, not a direct measurement and not a lower-bound claim about the judge in general.
5. **Optional stopping is not quantified for Petri.** We identify the stopping rule, but the 1.62× magnitude comes from a different domain.

This project is defensive: it tells auditors when their null results are uninformative and publishes no installation recipe, model-training procedure, or attack method. The residual dual-use concern is explicit: the same power calculation could let an attacker read off how rarely a loyalty must fire to survive a given audit budget. That risk is why the paper presents conditional arithmetic and measurement limitations rather than an evasion recipe.

## LLM Usage Statement

An LLM-assisted coding tool was used to inspect repository context, draft and edit report-source prose, and help implement the reproducible Table 2 generator. The author reviewed the source documents, issue specifications, statistical definitions, generated values, and validation results; the LLM was not treated as an authority for source facts. No claim of PDF export, Google Docs editing, submission-form completion, or external review is made here.

> [!NOTE] This should be replaced. Please summarise the following for me: the author used Claude to assisst with initial planning and brainstorming of ideas. Mat observed the potential issue with the analysis in the Lamerton and Roger paper and then proposed the idea to Claude. It was similar to Mat gregory's earlier paper from 2016, which was about how many injections is just right for piggyBac. Claude helped Mat to think through the statistical issues and how to present them in a clear way. Mat then worked in Warp, an agentic development environment, and broke the project down into milestones, and then milestones into tickets. Mat then assigned the issues to a range of models, depending on the complexity of the task. Mat then reviewed the outputs from the models and made decisions about how to proceed. Mat used a LLM to help pull out data from the initial paper and then verified it was accurate. The LLM was used to help with the writing of the report. Mat sketched out a draft by providing key sentences and how the paragraphs would stich together. Mat then got Claude to draft the paper by filling in the gaps and connecting it based on Mat's strucure. Mat then reviwed and made inline notes for Claude to then review and iterate upon. Mat was responsible for the final content and accuracy of the report.

## Final Submission Checklist

- [ ] PDF generated from the Apart template (not performed in this repository).
- [ ] Main text verified at four pages or fewer excluding references and appendix (not verifiable from Markdown alone).
- [x] Abstract is 150 words or fewer.
- [x] Figures 1–3 have numbered, self-contained captions in this source; visual legibility remains to be checked in the Apart export.
- [x] “Limitations and Dual-Use Considerations” appendix is present.
- [x] LLM Usage Statement is present.
- [x] Repository is public at <https://github.com/mammykins/how-many-prompts>.
- [ ] Submission form submitted before the stated deadline (not performed).
