# how-many-prompts
How Many Prompts Is Just Right? Statistical Power for Secret-Loyalty Audits.

## Quickstart
```bash
uv sync
uv run validate-table5
uv run python -m report.generate_tables   # regenerates report Tables 1-3
uv run ruff check .
uv run how-many-prompts
```

The table generator writes each report table three ways: Markdown for the report source,
TSV, and `report/tables.html`. The HTML exists because Markdown tables paste into Google
Docs as plain text, whereas a rendered HTML table pastes as a real Docs table.

## What this repository is
This repository contains the working materials for a research project on statistical power in secret-loyalty auditing. The core idea is to evaluate whether low/zero detection results in published black-box audits are actually informative, given sample sizes and audit design choices.

## What is currently in this repo
- `lamerton_roger_2026.py`: a provenance-focused transcription of published results from Lamerton & Roger (2026), including validation checks.
- `table5_detections.csv`: flat 250-row dataset exported from the transcription (Table 5 cells, including zeros).
- `RESEARCH.md`: project research handoff with assumptions, calculations, references, and planned next steps.

## What the Python module does
`lamerton_roger_2026.py` is designed to be auditable and explicit:
- stores constants and table values with source-aware comments
- reconstructs all Table 5 cells (10 models × 5 affordances × 5 techniques)
- provides `validate()` to run internal consistency checks
- provides `to_csv(path)` to export the table as CSV

## Environment and execution policy
Use `uv` for Python/runtime management in this repo.
- Do not run scripts with raw `python ...`.
- Do not install tools with `pip ...`.
- Run all project commands through `uv`.

Initial setup:

```bash
uv sync
```

Run validation:

```bash
uv run validate-table5
```

Run lint:

```bash
uv run ruff check .
```

Export CSV from a Python session:

```bash
uv run python -c "from lamerton_roger_2026 import to_csv; to_csv('table5_detections.csv')"
```

Or run the project entry point:

```bash
uv run how-many-prompts
```

Python example (for reference only):

```python
from lamerton_roger_2026 import to_csv
to_csv("table5_detections.csv")
```

## Project goal
Build a defensible analysis pipeline for answering:
- what detection rates current audit sample sizes can and cannot rule out
- how much conclusions change under clustered sampling assumptions
- how to design audit budgets around power rather than raw null outcomes
