#!/usr/bin/env python3
"""Shared PDF report helper for eval / sweep / analysis summaries.

Import from per-report render scripts instead of copy-pasting an FPDF
subclass into a new gen_pdf.py. See
.claude/skills/generating-result-pdfs/SKILL.md for usage and rationale.

Typical caller:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
    from report_pdf import start, fmt_pct

    pdf = start(title="v.Opus-3 Sweep", subtitle="SAIR Stage 1", date="2026-04-14")
    pdf.section_title("Headline Results")
    pdf.table(["Model", "hard1"], [["gemma-4-31b", "51/69 (73.9%)"]])
    pdf.output("results/.../report.pdf")
"""
from fpdf import FPDF


class ReportPDF(FPDF):
    """FPDF with section/table/quote/code helpers used across SAIR reports."""

    BRAND = (50, 70, 110)

    def __init__(self, title, subtitle="", date=""):
        super().__init__()
        self._title = title
        self._subtitle = subtitle
        self._date = date

    def header(self):
        if self.page_no() != 1:
            return
        self.set_font("Helvetica", "B", 16)
        self.cell(0, 10, self._title, new_x="LMARGIN", new_y="NEXT", align="C")
        if self._subtitle:
            self.set_font("Helvetica", "", 10)
            self.cell(0, 6, self._subtitle, new_x="LMARGIN", new_y="NEXT", align="C")
        if self._date:
            self.set_font("Helvetica", "", 10)
            self.cell(0, 6, self._date, new_x="LMARGIN", new_y="NEXT", align="C")
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(*self.BRAND)
        self.set_text_color(255, 255, 255)
        self.cell(0, 8, " " + title, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.set_text_color(0, 0, 0)
        self.ln(2)

    def sub_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def code_block(self, text):
        self.set_font("Courier", "", 8)
        self.set_fill_color(245, 245, 245)
        self.multi_cell(0, 4.5, text, fill=True, border=1)
        self.ln(1)
        self.set_font("Helvetica", "", 9)

    def quote_block(self, who, text):
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 5, who, new_x="LMARGIN", new_y="NEXT")
        self.set_font("Helvetica", "I", 8)
        self.set_fill_color(250, 248, 240)
        self.multi_cell(0, 4.5, text, fill=True, border="L")
        self.ln(1)
        self.set_font("Helvetica", "", 9)

    def bullet_list(self, items):
        self.set_font("Helvetica", "", 9)
        for item in items:
            self.multi_cell(0, 5, "- " + item)
            self.ln(0.5)
        self.ln(1)

    def table(self, headers, rows, col_widths=None,
              highlight_last_row=False, highlight_rows=None):
        highlight_rows = highlight_rows or []
        if col_widths is None:
            col_widths = [self.epw / len(headers)] * len(headers)
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(*self.BRAND)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, h, border=1, align="C", fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)
        for ri, row in enumerate(rows):
            is_last = ri == len(rows) - 1
            highlighted = (is_last and highlight_last_row) or ri in highlight_rows
            if highlighted:
                self.set_font("Helvetica", "B", 8)
                self.set_fill_color(220, 235, 250)
            else:
                self.set_font("Helvetica", "", 8)
                self.set_fill_color(245, 245, 245 if ri % 2 == 0 else 255)
            for i, val in enumerate(row):
                self.cell(col_widths[i], 5.5, str(val), border=1, align="C", fill=True)
            self.ln()
        self.ln(2)


def start(title, subtitle="", date=""):
    """Construct a ReportPDF, enable page numbering + auto page break, add page 1."""
    pdf = ReportPDF(title, subtitle, date)
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    return pdf


def fmt_pct(num, den):
    return f"{num}/{den} ({num / den * 100:.1f}%)" if den else "-"
