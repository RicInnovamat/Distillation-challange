---
name: generating-result-pdfs
description: Use when generating a PDF summary of eval results, sweeps, or analysis in this repo — applies whenever about to create a new gen_pdf.py or subclass FPDF inline
---

# Generating Result PDFs

## Overview

All result/analysis PDFs in this repo share **one helper** at `scripts/report_pdf.py`. Per-report scripts import it and write only the domain content — no FPDF subclass, no duplicated `header`/`footer`/`table` code.

**Why this skill exists:** `results/gen_pdf.py`, `results/20260410_v4.1-official/gen_pdf.py`, and `results/20260413_opus-analysis/gen_pdf.py` each carry ~60 identical lines of `class PDF(FPDF)` scaffolding. The copies drift — different header colors, new methods added in one place, bugs fixed in another. Using the shared helper keeps styling consistent and makes each new report ~50 lines of content instead of ~250 lines of scaffolding + content.

## When to use

- User asks for a PDF summary of a sweep, eval run, or cheatsheet analysis.
- You are about to create a new `gen_pdf.py` in a `results/` subdir.
- You are about to write `class PDF(FPDF):` anywhere in this repo.
- You are about to copy an existing `gen_pdf.py` as a starting template.

## When NOT to use

- Output is markdown only (no PDF needed).
- Target is an image/diagram (matplotlib/graphviz), not a text report.
- A constraint rules out fpdf2.

## Core pattern

Per-report render script lives beside the JSON/CSV it summarizes. Name it `render.py` (not `gen_pdf.py`). It imports the shared helper, loads data, and calls `section_title` / `table` / `bullet_list` etc.

**Directory placement:**
- Opus-thread reports (opus-solver runs, v.Opus-N cheatsheet sweeps, opus-informed analysis): `results/Opus_research/<dated-dir>/render.py`
- All other sweeps and analyses: `results/<dated-dir>/render.py`

The `sys.path.insert` line in the example below uses `parents[2]` for `results/<dated-dir>/`. When the render script lives under `results/Opus_research/<dated-dir>/`, use `parents[3]` instead (one level deeper).

```python
#!/usr/bin/env python3
"""v.Opus-3 sweep summary."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from report_pdf import start, fmt_pct  # noqa: E402

ROOT = Path(__file__).parent
OUT = ROOT / "v.Opus-3_sweep.pdf"

def main():
    # load JSON summaries ...
    pdf = start(
        title="v.Opus-3 Cheatsheet Sweep",
        subtitle="SAIR Mathematics Distillation Challenge - Equational Theories Stage 1",
        date="2026-04-14",
    )

    pdf.section_title("Headline Results")
    pdf.table(
        ["Model", "hard1", "hard2", "hard3"],
        [
            ["gemma-4-31b", fmt_pct(51, 69), fmt_pct(117, 200), fmt_pct(226, 399)],
            ["gpt-oss-120b", fmt_pct(54, 69), fmt_pct(150, 200), fmt_pct(240, 400)],
        ],
        highlight_rows=[0],
    )

    pdf.section_title("Key Observations")
    pdf.bullet_list([
        "Observation one ...",
        "Observation two ...",
    ])

    pdf.output(str(OUT))
    print(f"PDF written to {OUT}")

if __name__ == "__main__":
    main()
```

Run from anywhere: `python results/<dir>/render.py`. The `sys.path.insert` line handles the import regardless of CWD.

## Helper API (scripts/report_pdf.py)

| Call | Purpose |
|------|---------|
| `start(title, subtitle="", date="")` | Construct `ReportPDF`, enable page numbers + auto-break, add page 1 |
| `pdf.section_title(text)` | Banner-style section header (brand-color fill) |
| `pdf.sub_title(text)` | Bold inline sub-heading |
| `pdf.body_text(text)` | Regular paragraph |
| `pdf.code_block(text)` | Courier, shaded |
| `pdf.quote_block(who, text)` | Left-border italic quote with speaker label |
| `pdf.bullet_list(items)` | Dashed bullets |
| `pdf.table(headers, rows, col_widths=None, highlight_last_row=False, highlight_rows=None)` | Styled table with zebra rows |
| `fmt_pct(num, den)` | `"47/69 (68.1%)"` string |
| `pdf.output(path)` | fpdf2 native — write the PDF |

## Red flags — STOP and route to the shared helper

| If you are about to... | Do this instead |
|------------------------|-----------------|
| Copy `gen_pdf.py` from another `results/` dir | Import from `scripts/report_pdf.py` |
| Write `class PDF(FPDF): def header(self): ...` | Call `start(title=...)` |
| Name your script `gen_pdf.py` | Name it `render.py` |
| Paste the ~60-line PDF helper class | Delete the paste; `from report_pdf import start` |
| Write a second PDF script for the same analysis | Add a section to the existing `render.py` |

## Extending the helper

Only add a method to `scripts/report_pdf.py` if it will be reused across ≥2 reports. One-off visuals (a bespoke chart, a one-report table layout) stay in the render script — use `self.set_font`, `self.cell`, `self.multi_cell` directly on the `ReportPDF` instance.

If a styling decision changes (e.g. brand color, fonts), change it in `report_pdf.py` once and every future report picks it up.

## Legacy scripts

The three existing `gen_pdf.py` files are left as-is — they still produce their PDFs and are committed history. Do not rewrite them speculatively. New reports use the shared helper.
