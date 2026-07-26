"""Build a Google Docs-ready HTML version of the report.

Google Drive converts an uploaded HTML file into a native Google Doc, preserving
headings, bold, links and — the reason this script exists — real tables.  Pasting
Markdown into Docs instead yields pipe characters and plain text.

Two details matter for that conversion:

* Drive's converter is far more reliable with **inline** style attributes than with a
  stylesheet, so the table borders are injected onto each element rather than declared
  once in a ``<style>`` block.
* Task-list syntax is disabled, so the submission checklist arrives as readable
  ``[x]`` / ``[ ]`` text rather than as checkbox widgets that Drive discards.
* Hard line breaks are enabled so the author/affiliation block stays on separate lines;
  this is safe because each paragraph in the source is a single unwrapped line.
* Syntax highlighting is off, so the one shell block becomes a plain ``<pre>`` rather
  than a thicket of coloured spans and anchors.

Requires ``pandoc`` on the PATH.  Run from the repository root::

    uv run python -m report.build_html
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

REPORT_DIR = Path(__file__).parent
SOURCE = REPORT_DIR / "report.md"
OUTPUT = REPORT_DIR / "report.html"

BORDER = "1px solid #999"
TABLE_STYLE = f"border-collapse:collapse;border:{BORDER};font-size:10pt;"
CELL_STYLE = f"border:{BORDER};padding:5px 8px;vertical-align:top;"
HEAD_STYLE = f"{CELL_STYLE}background:#eeeeee;"


def to_fragment(source: Path = SOURCE) -> str:
    """Convert the Markdown body to an HTML fragment with pandoc."""
    if shutil.which("pandoc") is None:
        raise RuntimeError("pandoc is not on the PATH; install it with `brew install pandoc`")
    result = subprocess.run(
        [
            "pandoc",
            str(source),
            "--from",
            "gfm-task_lists+hard_line_breaks",
            "--to",
            "html",
            "--no-highlight",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def inline_table_styles(fragment: str) -> str:
    """Attach inline borders to every table element so Drive keeps the grid."""
    fragment = re.sub(r"<table\b[^>]*>", f'<table style="{TABLE_STYLE}">', fragment)
    fragment = re.sub(r"<th\b[^>]*>", f'<th style="{HEAD_STYLE}">', fragment)
    fragment = re.sub(r"<td\b[^>]*>", f'<td style="{CELL_STYLE}">', fragment)
    return fragment


def build(source: Path = SOURCE, output: Path = OUTPUT) -> Path:
    fragment = to_fragment(source)
    # The generator provenance comments are for the Markdown source, not the Doc.
    fragment = re.sub(r"<!--.*?-->\n?", "", fragment, flags=re.DOTALL)
    body = inline_table_styles(fragment)
    output.write_text(
        "<!doctype html>\n<html>\n<head>\n<meta charset='utf-8'>\n"
        "<title>How Many Prompts Is Just Right?</title>\n</head>\n"
        "<body style=\"font-family:Arial,sans-serif;font-size:11pt;line-height:1.4;\">\n"
        f"{body}</body>\n</html>\n"
    )
    return output


def main() -> None:
    path = build()
    print(f"Wrote {path}")
    print("Upload as text/html and let Drive convert it to a Google Doc.")


if __name__ == "__main__":
    main()
