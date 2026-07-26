"""Render Figure 1: technique detection shares at affordance 4 and ceiling.

Legend/caption: bars show each technique's share of all detections within the
affordance cluster (not a per-technique detection rate). Affordance 4 means the
principal is known; Ceiling means all information is known. Interrogation is
the conservative admission proxy, while assistant prefill, scratchpad prefill,
and base-model generation are behavioural-elicitation techniques. The hatched
``human_turn`` bars are mixed: the source transcript contains both an elicited
admission and observed behaviour. The unequal technique composition cautions
against treating the pooled Table 5 Total as one exchangeable detection rate.
"""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from matplotlib.patches import Patch

from how_many_prompts.sources.lamerton_roger_2026 import table5_cells


def main() -> None:
    cells = pd.DataFrame(c.__dict__ for c in table5_cells())
    cells["affordance_label"] = cells["affordance"].map({4: "Affordance 4", 5: "Ceiling"})
    selected = cells[cells["affordance"].isin([4, 5])]
    totals = selected.groupby("affordance")["detections"].transform("sum")
    selected = selected.assign(share=selected["detections"] / totals)
    selected = selected.groupby(["technique", "affordance_label"], as_index=False)["share"].sum()
    order = ["interrogation", "human_turn", "base_model", "assistant_prefill", "scratchpad_prefill"]

    sns.set_theme(style="ticks", context="paper", font_scale=1.0)
    palette = sns.color_palette("colorblind", 5)
    fig, ax = plt.subplots(figsize=(3.5, 2.8))
    sns.barplot(
        data=selected,
        x="technique",
        y="share",
        hue="affordance_label",
        order=order,
        hue_order=["Affordance 4", "Ceiling"],
        palette=palette[:2],
        ax=ax,
    )
    for patch, technique in zip(ax.patches, order * 2):
        if technique == "human_turn":
            patch.set_hatch("/")
    ax.set(xlabel=None, ylabel="Share of detections", ylim=(0, 0.55))
    ax.set_xticks(
        range(len(order)),
        ["interrogation", "human turn", "base model", "assistant prefill", "scratchpad prefill"],
        rotation=35,
        ha="right",
    )
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda value, _: f"{value:.0%}"))
    legend_handles = [
        Patch(facecolor=palette[0], label="Affordance 4"),
        Patch(facecolor=palette[1], label="Ceiling"),
        Patch(facecolor="white", edgecolor="black", hatch="/", label="human_turn (mixed)"),
    ]
    ax.legend(handles=legend_handles, title="Detection share", frameon=False, loc="upper right")
    sns.despine()
    fig.tight_layout()
    output = Path(__file__).with_name("fig1_technique_heterogeneity.pdf")
    fig.savefig(output, bbox_inches="tight")
    # A PNG alongside the vector version: Google Docs can insert PNG but not PDF.
    fig.savefig(output.with_suffix(".png"), bbox_inches="tight", dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    main()
