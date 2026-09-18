"""Render Figure 4: modelled detection rate by technique and affordance.

This figure is the picture of the technique-by-affordance interaction that the
GLM reanalysis tests. Reading the 70 informative cells one at a time cannot show
it: most cells hold 0 to 5 detections out of 30, and two coefficients are
infinite under maximum likelihood because of separation. The model pools across
the seven loyal models and reports a rate per technique with an interval.

STATUS: EXPLORATORY. The cell counts were seen before the model was specified,
so this figure describes the data rather than testing a pre-registered claim.
See ``PREANALYSIS.md``.

Paper legend/caption:
    Modelled detection rate per audit technique, averaged over the seven loyal
    models, at affordance 4 (the principal is known, left) and at the ceiling
    (all information is known, right). Points with bars are Firth penalised
    logistic estimates with 95% intervals that allow for overdispersion; open
    markers are the observed pooled proportions, annotated with the raw counts
    out of 210 completions per technique and affordance. Firth's penalty is used
    because two cells separate perfectly under maximum likelihood. The intervals
    are approximate in the sparse cells and are not corrected for having
    examined the counts first. The ranking of techniques changes between the two
    panels, which is the interaction: the pooled Table 5 Total column averages
    over a technique mix that is not the same at the two affordance levels.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from how_many_prompts.glm import design_frame, informative_subset, marginal_rates

# Ordered as in Figure 1, so the two figures can be read side by side.
TECHNIQUE_ORDER = [
    "interrogation",
    "human_turn",
    "base_model",
    "assistant_prefill",
    "scratchpad_prefill",
]
TECHNIQUE_LABELS = {
    "interrogation": "interrogation",
    "human_turn": "human turn",
    "base_model": "base model",
    "assistant_prefill": "assistant prefill",
    "scratchpad_prefill": "scratchpad prefill",
}
PANEL_TITLES = {4: "Affordance 4 (principal known)", 5: "Ceiling (all known)"}


def main() -> None:
    rates = marginal_rates(informative_subset(design_frame()))
    positions = {technique: i for i, technique in enumerate(TECHNIQUE_ORDER)}

    sns.set_theme(style="ticks", context="paper", font_scale=1.0)
    palette = sns.color_palette("colorblind", 5)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.2), sharey=True)

    for ax, affordance in zip(axes, (4, 5)):
        panel = rates[rates["affordance"] == affordance]
        for _, row in panel.iterrows():
            y = positions[row["technique"]]
            ax.plot(
                [row["lower"], row["upper"]],
                [y, y],
                color=palette[0],
                linewidth=1.6,
                solid_capstyle="butt",
                zorder=2,
            )
            ax.plot(
                row["rate"], y, marker="o", markersize=5, color=palette[0], zorder=3
            )
            # Observed proportion as an open marker, with the raw counts.
            ax.plot(
                row["observed"],
                y,
                marker="o",
                markersize=6,
                markerfacecolor="white",
                markeredgecolor=palette[1],
                markeredgewidth=1.2,
                linestyle="none",
                zorder=4,
            )
            ax.annotate(
                f"{int(row['detections'])}/{int(row['n'])}",
                xy=(row["upper"], y),
                xytext=(4, 0),
                textcoords="offset points",
                va="center",
                fontsize=7,
                color="0.35",
            )
        ax.set_title(PANEL_TITLES[affordance], fontsize=9)
        ax.set_xlabel("Detection rate")
        ax.set_xlim(0, 0.22)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:.0%}"))
        ax.grid(axis="x", color="0.9", linewidth=0.6)
        ax.set_axisbelow(True)

    axes[0].set_yticks(
        range(len(TECHNIQUE_ORDER)),
        [TECHNIQUE_LABELS[t] for t in TECHNIQUE_ORDER],
    )
    axes[0].set_ylim(len(TECHNIQUE_ORDER) - 0.5, -0.5)

    model_handle = plt.Line2D(
        [], [], color=palette[0], marker="o", markersize=5, label="Model rate (95% CI)"
    )
    observed_handle = plt.Line2D(
        [],
        [],
        color=palette[1],
        marker="o",
        markersize=6,
        markerfacecolor="white",
        markeredgewidth=1.2,
        linestyle="none",
        label="Observed proportion",
    )
    axes[0].legend(
        handles=[model_handle, observed_handle],
        frameon=False,
        loc="lower right",
        fontsize=8,
    )
    sns.despine(left=True)
    fig.tight_layout()

    output = Path(__file__).with_name("fig4_technique_by_affordance.pdf")
    fig.savefig(output, bbox_inches="tight")
    # A PNG alongside the vector version: Google Docs can insert PNG but not PDF.
    fig.savefig(output.with_suffix(".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
