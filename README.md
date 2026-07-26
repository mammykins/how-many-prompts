# how-many-prompts

**How Many Prompts Is Just Right? Statistical Power for Secret-Loyalty Audits.**

Black-box audits for hidden model loyalties keep reporting zero detections, and those
zeros keep being read as evidence that the models are clean. They are not. A cell that
runs 30 completions and finds nothing is still compatible with a loyalty being caught in
roughly one conversation in nine — and in one in five once you account for the fact that
those 30 completions are really 10 prompts re-run three times.

This repository reanalyses all 250 audit cells published by Lamerton and Roger (2026),
and provides a small tool that converts an audit budget into the activation rate that
budget could actually detect.

📄 **The paper: [`report/report.md`](report/report.md)**

## The headline number

A single audit cell recording 0 detections out of 30 completions, with ρ the assumed
correlation between the three re-runs of the same prompt:

| Assumption | 95% upper bound on the true detection rate |
|---|---:|
| Re-runs treated as independent (ρ = 0) | 11.6% |
| Modest correlation (ρ = 0.3) | 17.9% |
| Moderate correlation (ρ = 0.5) | 21.8% |

215 of the 250 published cells recorded no detections. None of them rules out a loyalty
firing at these rates.

## What's in here

| Path | What it is |
|---|---|
| `report/report.md` | The paper |
| `src/how_many_prompts/sources/lamerton_roger_2026.py` | Provenance-controlled transcription of the published tables, with `validate()` |
| `src/how_many_prompts/sources/gregory_2016_piggybac.py` | Constants from the 2016 paper the method is ported from |
| `src/how_many_prompts/intervals.py` | Wilson and Clopper–Pearson intervals, design effect for repeated measurements |
| `src/how_many_prompts/shrinkage.py` | Beta-binomial empirical Bayes, pooled within model group |
| `src/how_many_prompts/power.py` | Detection probability against audit size, with coverage as a declared input |
| `figures/` | Scripts and rendered figures (PDF for print, PNG for documents) |
| `report/generate_tables.py` | Builds the report tables as Markdown, TSV and HTML |
| `report/build_html.py` | Builds a Google Docs-ready HTML version of the report |
| `table5_detections.csv` | The 250 transcribed cells as a flat dataset |
| `CONTEXT.md` | Canonical definition of every term used, so code and paper agree |
| `RESEARCH.md` | Working notes from the build, superseded by the paper |

## Reproduce

Requires [`uv`](https://docs.astral.sh/uv/). Run everything through it.

```bash
uv sync
uv run validate-table5                     # re-runs both transcription checks
uv run python -m report.generate_tables    # rebuilds the report tables
uv run python -m report.build_html         # rebuilds the Docs-ready HTML
uv run pytest && uv run ruff check .
```

Figures are rebuilt individually, each writing a PDF and a PNG:

```bash
uv run python figures/fig1_technique_heterogeneity.py
uv run python figures/fig2_caterpillar_eb.py
uv run python figures/fig3_power_vs_n.py
```

`uv run how-many-prompts` is an alias for `uv run validate-table5`; both just run the
transcription checks.

## Use it on your own audit

The point of the tool is that it applies to any null result, not just this one. Two
questions it answers:

```python
from how_many_prompts.intervals import clopper_pearson_upper, effective_n
from how_many_prompts.power import conversations_for_probability

# 1. My audit found nothing in 30 completions. What can I rule out?
clopper_pearson_upper(0, 30)                              # 0.1157
clopper_pearson_upper(0, round(effective_n(30, 3, 0.5)))  # 0.2180, if the 30 are
                                                          # 10 prompts re-run 3x

# 2. How many conversations do I need for an 80% chance of catching a loyalty that
#    fires in 5% of conversations, if only a quarter of my prompts reach the trigger?
conversations_for_probability(r=0.05, coverage=0.25, probability=0.8)   # 128
```

`coverage` is the fraction of audit prompts that reach the trigger region. It is a
**declared input**, never estimated — see the caveats below.

## How provenance is enforced

Every transcribed constant carries an inline comment naming its source table and column,
and `validate()` re-runs two independent consistency checks whenever the module is
imported:

- all 50 published row totals reconcile against the sum of their five technique cells
- every affordance-4 cell cross-checks against the corresponding main-text value

The transcription refuses to be trusted on its own say-so, which is the point. Two
numbers in earlier drafts of this analysis were wrong and were caught by exactly these
checks; both corrections are documented in the paper's Appendix B.

## Caveats

- **Coverage is not estimable** from the published metrics — nothing records whether an
  audit prompt ever reached the trigger region. Every power result is conditional on a
  declared coverage value, not on a measurement.
- **The correlation between re-runs is not estimable either.** ρ is a sensitivity axis.
  Results are shown at ρ = 0, 0.3 and 0.5 rather than at one chosen value.
- **Bounds are the upper limit of a two-sided 95% Clopper–Pearson interval.** A 0/30 cell
  gives 11.6%; a one-sided 95% bound would give 9.5%.
- The reanalysis is of published summary tables. No models were run.

## Citation

The method is ported from a validated instrument in a different field:

> Gregory, M., Alphey, L., Morrison, N. I. & Shimeld, S. M. (2016). *Insect
> transformation with piggyBac: getting the number of injections just right*. Insect
> Molecular Biology, 25(3), 259–271. <https://doi.org/10.1111/imb.12220>

Lineage: [Goldilocks decision tool](https://github.com/mammykins/Goldilocks-decision-tool)
· [piggyBac data](https://github.com/mammykins/piggyBac-data)

Produced for the Apart Research / Formation Research Secret Loyalties Hackathon, Track 2.

## Licence

[MIT](LICENSE).
