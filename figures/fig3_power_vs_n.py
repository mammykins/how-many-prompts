"""Render Figure 3, the declared-coverage audit-power plot.

This figure was regenerated for Phase 2 because the project needs a decision
tool showing what an audit sample size can and cannot detect, rather than
interpreting a published zero-detection result as evidence of absence.  It
uses the existing ``p_at_least_one_detection`` API without introducing a new
funnel or judge-sensitivity factor.  The left panel uses Lamerton & Roger's
activation rate ``r = 0.695`` for the trained 7B model; the right uses
``r = 0.116``, the Clopper--Pearson 95% upper bound for one 0/30 null cell.
Each curve conditions on a declared trigger coverage value. Coverage is not
estimated as ``d/r`` because detection rate ``d`` includes both admissions and
observed behaviour, while ``r`` is measured on trigger-positive ``D+``
trajectories by construction.

Paper legend/caption:
    Probability of at least one detection in N audit conversations under
    declared trigger coverage values. The left panel shows r = 0.695 (7B
    trained, Lamerton & Roger Table 2); the right shows r = 0.116 (the 95%
    Clopper--Pearson upper bound for a 0/30 null cell). Curves correspond to
    coverage values 1.0, 0.5, 0.25, and 0.1; dashed lines mark 80% and 95%
    power. Coverage—whether an audit prompt reaches the trigger region—is not
    recorded in the published data and is a declared input, so results are
    conditional on the stated coverage rather than an estimate of coverage.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

from how_many_prompts.power import p_at_least_one_detection

RATES = (0.695, 0.116)
COVERAGES = (1.0, 0.5, 0.25, 0.1)


def main() -> None:
    sns.set_theme(style="ticks", context="paper", font_scale=1.0)
    palette = sns.color_palette("colorblind", len(COVERAGES))
    n_values = np.geomspace(10, 1000, 300).round().astype(int)
    fig, axes = plt.subplots(1, 2, figsize=(7.0, 3.5), sharey=True)
    for ax, rate, title in zip(
        axes,
        RATES,
        (
            "r = 0.695 (7B trained, L&R Table 2)",
            "r = 0.116 (95% UB of 0/30 null cell)",
        ),
    ):
        for coverage, color in zip(COVERAGES, palette):
            probability = [p_at_least_one_detection(n, rate, coverage) for n in n_values]
            ax.plot(n_values, probability, color=color, label=f"coverage = {coverage:g}")
        ax.axhline(0.8, color="0.4", linestyle="--", linewidth=0.7)
        ax.axhline(0.95, color="0.4", linestyle="--", linewidth=0.7)
        ax.set(
            title=title,
            xscale="log",
            xlim=(10, 1000),
            ylim=(0, 1),
            xlabel="N audit conversations",
        )
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{int(value):,}"))
        ax.grid(axis="y", color="0.88", linewidth=0.5)
    axes[0].set_ylabel("P(≥1 detection)")
    axes[1].legend(frameon=False, loc="lower right")
    fig.text(
        0.5,
        0.01,
        "Coverage is a declared input: whether an audit prompt reaches the trigger region "
        "is not recorded in the published data.",
        ha="center",
        va="bottom",
        fontsize=7,
    )
    sns.despine()
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    output = Path(__file__).with_name("fig3_power_vs_N.pdf")
    fig.savefig(output, bbox_inches="tight")
    # A PNG alongside the vector version: Google Docs can insert PNG but not PDF.
    fig.savefig(output.with_suffix(".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
