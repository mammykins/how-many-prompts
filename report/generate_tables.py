"""Generate the report's tables from the validated source data, in three formats.

Every table in the report is built here from the provenance-focused transcription
rather than hand-edited in the Markdown, so the numbers cannot drift.  Each table is
emitted three ways:

``report/tableN.md``
    Markdown, for the report source.
``report/tables.html``
    A rendered HTML page.  Markdown tables paste into Google Docs as pipe-character
    plain text; an HTML ``<table>`` on the clipboard pastes as a real Docs table.  Open
    the file in a browser, select the table, copy, paste into the submission template.
``report/tableN.tsv``
    Tab-separated fallback: paste into Google Sheets, then copy the range into Docs.

The reanalysis tables cover the 13 model/affordance pairs that recorded at least one
detection.  The 215 cells that recorded none are not omitted from the analysis — they
are summarised by the final row of Table 3, which is the paper's headline number.

For each correlation value, the reported upper bound is the largest one-sided bound
among that row's five technique cells.  This is deliberately conservative and keeps the
bound tied to the published cell-level sampling unit; it does not treat the five
techniques as interchangeable.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from pathlib import Path

from scipy.stats import beta

from how_many_prompts.intervals import effective_n
from how_many_prompts.shrinkage import shrink_cells
from how_many_prompts.sources.gregory_2016_piggybac import ISOMORPHISM_MAPPING
from how_many_prompts.sources.lamerton_roger_2026 import (
    N_PER_CELL,
    SAMPLES_PER_PROMPT,
    TECHNIQUES,
    table5_cells,
)

RHO_VALUES = (0.0, 0.3, 0.5)
REPORT_DIR = Path(__file__).parent


@dataclass(frozen=True)
class Table:
    """A report table, renderable as Markdown, HTML or TSV."""

    number: int
    title: str
    headers: list[str]
    rows: list[list[str]]
    right_align_from: int = 1

    @property
    def slug(self) -> str:
        return f"table{self.number}"

    def _alignment(self, column: int) -> str:
        return "right" if column >= self.right_align_from else "left"

    def to_markdown(self) -> str:
        divider = [
            "---" if self._alignment(i) == "left" else "---:"
            for i in range(len(self.headers))
        ]
        lines = [
            "| " + " | ".join(self.headers) + " |",
            "|" + "|".join(divider) + "|",
        ]
        lines += ["| " + " | ".join(row) + " |" for row in self.rows]
        return "\n".join(lines) + "\n"

    def to_tsv(self) -> str:
        lines = ["\t".join(self.headers)]
        lines += ["\t".join(row) for row in self.rows]
        return "\n".join(lines) + "\n"

    def to_html(self) -> str:
        """Render with inline styles, which survive a clipboard paste into Google Docs."""
        border = "1px solid #999"
        head_cells = "".join(
            f'<th style="border:{border};padding:6px 9px;background:#eee;'
            f'text-align:{self._alignment(i)};">{html.escape(header)}</th>'
            for i, header in enumerate(self.headers)
        )
        body_rows = "".join(
            "<tr>"
            + "".join(
                f'<td style="border:{border};padding:6px 9px;'
                f'text-align:{self._alignment(i)};">{html.escape(value)}</td>'
                for i, value in enumerate(row)
            )
            + "</tr>"
            for row in self.rows
        )
        return (
            f"<h2>Table {self.number}. {html.escape(self.title)}</h2>\n"
            f'<table style="border-collapse:collapse;border:{border};'
            f'font-family:Arial,sans-serif;font-size:10pt;">\n'
            f"<thead><tr>{head_cells}</tr></thead>\n"
            f"<tbody>{body_rows}</tbody>\n</table>\n"
        )


def upper_bound(k: int, n: int, rho: float) -> float:
    """Return a 95% Clopper–Pearson upper bound after the design-effect deflation."""
    n_eff = effective_n(n, SAMPLES_PER_PROMPT, rho)
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


def label_affordance(affordance: int) -> str:
    return "ceiling" if affordance == 5 else f"affordance {affordance}"


def detecting_pairs() -> list[tuple[tuple[str, int], list]]:
    """Return the model/affordance pairs with at least one detection, in source order."""
    cells = table5_cells()
    pairs: dict[tuple[str, int], list] = {}
    for cell in cells:
        if cell.detections:
            pairs.setdefault((cell.model, cell.affordance), [])
    for pair in pairs:
        pairs[pair] = sorted(
            (c for c in cells if (c.model, c.affordance) == pair),
            key=lambda c: TECHNIQUES.index(c.technique),
        )
    return list(pairs.items())


def build_table2() -> Table:
    """What the audit observed."""
    eb = shrink_cells(table5_cells())
    rows = []
    for (model, affordance), pair_cells in detecting_pairs():
        raw = ", ".join(str(cell.detections) for cell in pair_cells)
        pooled_k = sum(cell.detections for cell in pair_cells)
        pooled_n = len(pair_cells) * N_PER_CELL
        eb_mean = sum(
            eb[(cell.model, cell.affordance, cell.technique)].shrunk_estimate
            for cell in pair_cells
        ) / len(pair_cells)
        rows.append(
            [
                f"{label_model(model)}, {label_affordance(affordance)}",
                f"[{raw}]/30",
                f"{pooled_k}/{pooled_n} ({pooled_k / pooled_n:.1%})",
                f"{eb_mean:.1%}",
            ]
        )
    return Table(
        number=2,
        title="What the audit observed: detections in the 13 model/affordance pairs "
        "that recorded any",
        headers=[
            "Model and affordance level",
            (
                "Detections per technique (out of 30 completions each): assistant "
                "prefill, scratchpad prefill, base model, human turn, interrogation"
            ),
            "All five techniques added together",
            "After borrowing strength from the other cells in the same model group",
        ],
        rows=rows,
    )


def build_table3() -> Table:
    """What the audit could not rule out."""
    rows = []
    for (model, affordance), pair_cells in detecting_pairs():
        bounds = [
            max(upper_bound(cell.detections, cell.n, rho) for cell in pair_cells)
            for rho in RHO_VALUES
        ]
        rows.append(
            [f"{label_model(model)}, {label_affordance(affordance)}"]
            + [f"{bound:.1%}" for bound in bounds]
        )
    rows.append(
        ["Any cell recording no detections (215 of the 250)"]
        + [f"{upper_bound(0, N_PER_CELL, rho):.1%}" for rho in RHO_VALUES]
    )
    return Table(
        number=3,
        title="What the audit could not rule out: 95% upper bounds on the true "
        "detection rate",
        headers=[
            "Model and affordance level",
            "If the three re-runs of a prompt are treated as independent (ρ = 0)",
            "At modest correlation between re-runs (ρ = 0.3)",
            "At moderate correlation between re-runs (ρ = 0.5)",
        ],
        rows=rows,
    )


def build_table1() -> Table:
    return Table(
        number=1,
        title="The two problems side by side",
        headers=["Injecting insect embryos (Gregory et al., 2016)", "Auditing for a secret loyalty"],
        rows=[list(row) for row in ISOMORPHISM_MAPPING],
        right_align_from=99,
    )


def write_all(directory: Path = REPORT_DIR) -> list[Path]:
    tables = [build_table1(), build_table2(), build_table3()]
    written = []
    for table in tables:
        for suffix, text in (
            (".md", table.to_markdown()),
            (".tsv", table.to_tsv()),
        ):
            path = directory / f"{table.slug}{suffix}"
            path.write_text(text)
            written.append(path)

    page = (
        "<!doctype html>\n<meta charset='utf-8'>\n"
        "<title>how-many-prompts — report tables</title>\n"
        "<body style=\"font-family:Arial,sans-serif;margin:2rem;max-width:60rem;\">\n"
        "<p style='color:#555;'>Generated by "
        "<code>uv run python -m report.generate_tables</code>. "
        "Select a table, copy, and paste into the Google Docs template: it arrives as a "
        "real Docs table.</p>\n"
        + "\n".join(table.to_html() for table in tables)
        + "</body>\n"
    )
    html_path = directory / "tables.html"
    html_path.write_text(page)
    written.append(html_path)
    return written


def main() -> None:
    for path in write_all():
        print(f"Wrote {path}")


if __name__ == "__main__":
    main()
