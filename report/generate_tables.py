"""Generate the Phase 3 report's reanalysis table from the validated source data.

This module exists so Table 2 is regenerated from the provenance-focused Table 5
transcription rather than hand-edited numbers.  It retains the published
technique-level ``k/30`` cells, adds their transparent pooled ``k/150`` total,
and computes the empirical-Bayes and design-effect sensitivity quantities using
the project's existing analysis APIs.  The report's 13 rows are the non-zero
model/affordance pairs; the 215 zero cells remain part of the analysis but are
described in prose instead of being expanded into a misleading table.

The issue specification calls the raw column ``k/30`` even though each row
contains five technique cells.  The generated table therefore shows the five
technique numerators explicitly as ``[k, k, k, k, k]/30`` and separately reports
the pooled numerator/denominator.  For each rho sensitivity column, the value is
the largest one-sided 95% Clopper–Pearson upper bound among that row's five
technique cells.  This is deliberately conservative and keeps the bounds tied
to the published cell-level sampling unit; it does not pretend the five
techniques are exchangeable.
"""

from __future__ import annotations

from pathlib import Path

from scipy.stats import beta

from how_many_prompts.intervals import effective_n
from how_many_prompts.shrinkage import shrink_cells
from how_many_prompts.sources.lamerton_roger_2026 import (
    N_PER_CELL,
    TECHNIQUES,
    table5_cells,
)

RHO_VALUES = (0.0, 0.3, 0.5)
OUT = Path(__file__).with_name("table2.md")


def upper_bound(k: int, n: int, rho: float) -> float:
    """Return a two-sided 95% Clopper–Pearson upper bound after deflation."""
    n_eff = effective_n(n, 3, rho)
    k_eff = k * n_eff / n
    if k_eff >= n_eff:
        return 1.0
    return float(beta.ppf(0.975, k_eff + 1, n_eff - k_eff))


def label_model(model: str) -> str:
    return {
        "1.5b-trained": "1.5B trained",
        "7b-trained": "7B trained",
        "7b-pos-only": "7B Positive-Only",
        "32b-trained": "32B trained",
        "7b-poison-12.5": "12.5% poison",
        "7b-poison-6.25": "6.25% poison",
        "7b-poison-3.125": "3.125% poison",
    }[model]


def make_table() -> str:
    cells = table5_cells()
    by_pair: dict[tuple[str, int], list] = {}
    for cell in cells:
        if cell.detections:
            by_pair.setdefault((cell.model, cell.affordance), [])
    for pair in by_pair:
        by_pair[pair] = [
            cell
            for cell in cells
            if (cell.model, cell.affordance) == pair
        ]

    eb = shrink_cells(cells)
    lines = [
        "| Model / affordance | Raw (k/30; assistant, scratchpad, base, human, interrogation) | Pooled | Within-group EB mean | UB ρ=0 | UB ρ=0.3 | UB ρ=0.5 |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for (model, affordance), pair_cells in by_pair.items():
        pair_cells.sort(key=lambda cell: TECHNIQUES.index(cell.technique))
        raw = ", ".join(str(cell.detections) for cell in pair_cells)
        pooled_k = sum(cell.detections for cell in pair_cells)
        pooled_n = len(pair_cells) * N_PER_CELL
        eb_mean = sum(
            eb[(cell.model, cell.affordance, cell.technique)].shrunk_estimate
            for cell in pair_cells
        ) / len(pair_cells)
        bounds = [
            max(upper_bound(cell.detections, cell.n, rho) for cell in pair_cells)
            for rho in RHO_VALUES
        ]
        lines.append(
            f"| {label_model(model)}, {('ceiling' if affordance == 5 else 'affordance 4')} "
            f"| [{raw}]/30 | {pooled_k}/{pooled_n} ({pooled_k / pooled_n:.1%}) "
            f"| {eb_mean:.1%} | "
            + " | ".join(f"{bound:.1%}" for bound in bounds)
            + " |"
        )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    OUT.write_text(make_table())
    print(f"Wrote {OUT}")
