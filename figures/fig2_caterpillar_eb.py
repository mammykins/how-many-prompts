"""Render Figure 2, the empirical-Bayes caterpillar plot.

This figure was regenerated for Phase 2 of the ``how-many-prompts`` research
project because the 250 Lamerton & Roger Table 5 cells contain 75 structural
baseline zeros and 175 informative trained/poison cells.  The baseline zeros
must not be pooled into an empirical-Bayes prior: they describe untrained
models, not evidence about the trained or poison populations.  ``shrink_cells``
therefore fits separate beta-binomial priors within the trained and poison
model groups and returns each cell's posterior mean and equal-tailed posterior
credible interval.  The plot uses those existing results directly; it does
not bootstrap or refit a combined prior.  Rows are sorted by posterior mean,
and marker sizes are intentionally small because all 175 rows are retained at
single-column width.

Paper legend/caption:
    Empirical-Bayes-shrunk detection rates for all 175 non-baseline cells in
    Lamerton & Roger Table 5. Circles show posterior means and horizontal bars
    show 95% posterior credible intervals from the beta-binomial posterior;
    they are not Wilson intervals or bootstrap intervals. Colour identifies
    the separately fitted model group (trained or poison). Grey triangles show
    the raw cell proportion for non-zero cells only. The 75 untrained-baseline
    cells are structural zeros and are excluded from prior fitting.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from matplotlib.lines import Line2D

from how_many_prompts.shrinkage import shrink_cells
from how_many_prompts.sources.lamerton_roger_2026 import table5_cells


def main() -> None:
    cells = table5_cells()
    eb_results = shrink_cells(cells)
    rows = []
    for cell in cells:
        key = (cell.model, cell.affordance, cell.technique)
        if key not in eb_results:
            continue
        result = eb_results[key]
        rows.append(
            {
                "label": f"{cell.model} · aff {cell.affordance} · {cell.technique}",
                "group": "poison" if cell.model.startswith("7b-poison") else "trained",
                "raw": cell.rate,
                "nonzero": cell.detections > 0,
                "estimate": result.shrunk_estimate,
                "lower": result.ci_lower,
                "upper": result.ci_upper,
            }
        )
    rows.sort(key=lambda row: row["estimate"], reverse=True)

    sns.set_theme(style="ticks", context="paper", font_scale=1.0)
    palette = dict(zip(["trained", "poison"], sns.color_palette("colorblind", 2)))
    fig_height = max(6.0, 0.055 * len(rows))
    fig, ax = plt.subplots(figsize=(3.5, fig_height))
    for index, row in enumerate(rows):
        color = palette[row["group"]]
        ax.errorbar(
            row["estimate"],
            index,
            xerr=[
                [row["estimate"] - row["lower"]],
                [row["upper"] - row["estimate"]],
            ],
            fmt="o",
            color=color,
            ecolor=color,
            elinewidth=0.5,
            capsize=1.0,
            markersize=2,
        )
        if row["nonzero"]:
            ax.plot(row["raw"], index, marker="^", color="0.45", markersize=1.5)

    tick_positions = np.arange(0, len(rows), 10)
    ax.set(
        xlabel="Detection rate",
        ylabel="Cells sorted by EB estimate (all 175 shown)",
        yticks=tick_positions,
        yticklabels=[str(position + 1) for position in tick_positions],
        xlim=(0, max(0.36, max(row["upper"] for row in rows) * 1.05)),
    )
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))
    ax.invert_yaxis()
    ax.grid(axis="x", color="0.88", linewidth=0.5)
    ax.legend(
        handles=[
            Line2D([0], [0], marker="o", color=palette["trained"], linestyle="", label="trained EB"),
            Line2D([0], [0], marker="o", color=palette["poison"], linestyle="", label="poison EB"),
            Line2D([0], [0], marker="^", color="0.45", linestyle="", label="raw proportion"),
            Line2D(
                [0],
                [0],
                marker="o",
                color="0.35",
                linestyle="-",
                linewidth=0.5,
                label="mean ± 95% posterior CI",
            ),
        ],
        frameon=False,
        loc="lower right",
    )
    sns.despine()
    fig.tight_layout()
    output = Path(__file__).with_name("fig2_caterpillar_eb.pdf")
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    main()
