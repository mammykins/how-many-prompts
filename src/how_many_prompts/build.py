"""Rebuild every generated artefact in the repository, in dependency order.

Figures, tables and the report HTML are each produced by their own script, which
is fine when you are iterating on one of them and a trap when you are not: it is
easy to regenerate a figure, forget the table that quotes it, and commit the two
out of step. This module runs the lot, in the order the artefacts depend on each
other, and stops at the first failure.

Validation runs first and is not optional. If the transcription checks fail,
nothing downstream can be trusted, so nothing downstream is built.

Run:  uv run build-all [--skip-glm]
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# (label, argv, stdout redirect target relative to REPO_ROOT or None)
Step = tuple[str, list[str], str | None]

TABLES: list[Step] = [
    ("report tables", [sys.executable, "-m", "report.generate_tables"], None),
]

FIGURES: list[Step] = [
    (
        "figure 1 (technique heterogeneity)",
        [sys.executable, "figures/fig1_technique_heterogeneity.py"],
        None,
    ),
    (
        "figure 2 (empirical-Bayes caterpillar)",
        [sys.executable, "figures/fig2_caterpillar_eb.py"],
        None,
    ),
    ("figure 3 (power vs N)", [sys.executable, "figures/fig3_power_vs_n.py"], None),
    (
        "figure 4 (technique by affordance)",
        [sys.executable, "figures/fig4_technique_by_affordance.py"],
        None,
    ),
]

# The GLM reanalysis is the slow step: 1000 simulation replicates, about a
# minute. It writes its JSON as a side effect and its Markdown on stdout.
GLM: Step = (
    "GLM reanalysis (1000 reps)",
    [sys.executable, "-m", "how_many_prompts.glm", "--json", "report/glm_results.json"],
    "report/glm.md",
)

HTML: list[Step] = [
    ("Docs-ready HTML", [sys.executable, "-m", "report.build_html"], None),
]


def _validate() -> None:
    """Run the transcription checks in process and stop the build if they fail.

    ``validate()`` returns a bool rather than exiting non-zero, so calling the
    console script here would let an invalid transcription build silently.
    """
    from .sources.lamerton_roger_2026 import validate

    print("==> validate transcription", flush=True)
    if not validate():
        raise SystemExit("transcription checks failed; nothing downstream was built")


def _run(step: Step) -> None:
    label, argv, redirect = step
    print(f"==> {label}", flush=True)
    started = time.monotonic()
    if redirect is None:
        subprocess.run(argv, cwd=REPO_ROOT, check=True)
    else:
        target = REPO_ROOT / redirect
        # Write to a temporary file first so a failed run cannot leave a
        # truncated artefact behind looking like a successful one.
        tmp = target.with_suffix(target.suffix + ".tmp")
        try:
            with tmp.open("w", encoding="utf-8") as fh:
                subprocess.run(argv, cwd=REPO_ROOT, check=True, stdout=fh)
            tmp.replace(target)
        finally:
            tmp.unlink(missing_ok=True)
    print(f"    done in {time.monotonic() - started:.1f}s", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--skip-glm",
        action="store_true",
        help="skip the GLM reanalysis, the one slow step",
    )
    args = parser.parse_args()

    steps = [*TABLES, *FIGURES]
    if not args.skip_glm:
        steps.append(GLM)
    steps += HTML

    started = time.monotonic()
    _validate()
    try:
        for step in steps:
            _run(step)
    except subprocess.CalledProcessError as exc:
        print(f"\nFAILED: {exc.cmd[0]} exited {exc.returncode}", file=sys.stderr)
        raise SystemExit(exc.returncode) from exc
    print(f"\nAll artefacts rebuilt in {time.monotonic() - started:.1f}s.")


if __name__ == "__main__":
    main()
