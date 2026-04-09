#!/usr/bin/env python3
"""Generate v4.1 results PDF using fpdf2."""
from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font("Helvetica", "B", 16)
            self.cell(0, 10, "v4.1 Cheatsheet Evaluation Results", new_x="LMARGIN", new_y="NEXT", align="C")
            self.set_font("Helvetica", "", 10)
            self.cell(0, 6, "SAIR Mathematics Distillation Challenge - Equational Theories Stage 1", new_x="LMARGIN", new_y="NEXT", align="C")
            self.cell(0, 6, "2026-04-09", new_x="LMARGIN", new_y="NEXT", align="C")
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(230, 230, 230)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT", fill=True)
        self.ln(2)

    def sub_title(self, title):
        self.set_font("Helvetica", "B", 11)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def body_text(self, text):
        self.set_font("Helvetica", "", 9)
        self.multi_cell(0, 5, text)
        self.ln(1)

    def table(self, headers, rows, col_widths=None, highlight_last_row=False):
        if col_widths is None:
            col_widths = [self.epw / len(headers)] * len(headers)
        # Header
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(50, 50, 80)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, h, border=1, align="C", fill=True)
        self.ln()
        # Rows
        self.set_text_color(0, 0, 0)
        for ri, row in enumerate(rows):
            is_last = ri == len(rows) - 1
            if is_last and highlight_last_row:
                self.set_font("Helvetica", "B", 8)
                self.set_fill_color(220, 235, 250)
            else:
                self.set_font("Helvetica", "", 8)
                self.set_fill_color(245, 245, 245) if ri % 2 == 0 else self.set_fill_color(255, 255, 255)
            for i, val in enumerate(row):
                self.cell(col_widths[i], 5.5, str(val), border=1, align="C", fill=True)
            self.ln()
        self.ln(2)


pdf = PDF()
pdf.alias_nb_pages()
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()

# Config info
pdf.body_text(
    "Cheatsheet: v4.1_10KB_cheatsheet.md (10,231 bytes)\n"
    "Models: grok-4.1-fast, gpt-oss-120b, gpt-oss-20b, gemma-4-31b\n"
    "Datasets: hard1 (69), hard2 (200), hard3 (400) - 669 problems total per model\n"
    "Backend: OpenRouter API"
)

# Summary table
pdf.section_title("Summary")
cw = [35, 30, 30, 30, 35, 12]
pdf.table(
    ["Model", "hard1", "hard2", "hard3", "ALL", "PE"],
    [
        ["grok-4.1-fast",  "53/69 (76.8%)",  "160/200 (80.0%)", "237/400 (59.2%)", "450/669 (67.3%)", "0"],
        ["gpt-oss-120b",   "54/69 (78.3%)",  "150/200 (75.0%)", "240/400 (60.0%)", "444/669 (66.4%)", "0"],
        ["gpt-oss-20b",    "48/69 (69.6%)",  "140/200 (70.0%)", "234/400 (58.5%)", "422/669 (63.1%)", "0"],
        ["gemma-4-31b",    "51/69 (73.9%)",  "117/200 (58.5%)", "226/399 (56.6%)", "394/668 (59.0%)", "1"],
    ],
    col_widths=cw,
)
pdf.body_text("PE = Parse Errors (problems where no VERDICT could be extracted).")

# Per-model confusion matrices
pdf.section_title("Per-Model Confusion Matrices")
pdf.body_text(
    "T->T = correctly predicted TRUE.  T->F = missed implication (FALSE when TRUE).\n"
    "F->T = confabulation (TRUE when FALSE).  F->F = correctly predicted FALSE."
)

cw2 = [18, 32, 14, 14, 14, 14]

# grok
pdf.sub_title("grok-4.1-fast")
pdf.table(
    ["Dataset", "Accuracy", "T->T", "T->F", "F->T", "F->F"],
    [
        ["hard1", "53/69 (76.8%)", "14", "10", "6", "39"],
        ["hard2", "160/200 (80.0%)", "76", "24", "16", "84"],
        ["hard3", "237/400 (59.2%)", "99", "96", "67", "138"],
        ["TOTAL", "450/669 (67.3%)", "189", "130", "89", "261"],
    ],
    col_widths=cw2, highlight_last_row=True,
)
pdf.body_text("Bias: Balanced. Dominant error on hard3 is T->F (missed implications).")

# gpt-oss-120b
pdf.sub_title("gpt-oss-120b")
pdf.table(
    ["Dataset", "Accuracy", "T->T", "T->F", "F->T", "F->F"],
    [
        ["hard1", "54/69 (78.3%)", "19", "5", "10", "35"],
        ["hard2", "150/200 (75.0%)", "82", "18", "32", "68"],
        ["hard3", "240/400 (60.0%)", "128", "67", "93", "112"],
        ["TOTAL", "444/669 (66.4%)", "229", "90", "135", "215"],
    ],
    col_widths=cw2, highlight_last_row=True,
)
pdf.body_text("Bias: Slight TRUE bias. F->T confabulations (135) exceed T->F misses (90). Best TRUE recall (229/319 = 71.8%).")

pdf.add_page()

# gpt-oss-20b
pdf.sub_title("gpt-oss-20b")
pdf.table(
    ["Dataset", "Accuracy", "T->T", "T->F", "F->T", "F->F"],
    [
        ["hard1", "48/69 (69.6%)", "16", "8", "13", "32"],
        ["hard2", "140/200 (70.0%)", "76", "24", "36", "64"],
        ["hard3", "234/400 (58.5%)", "122", "73", "93", "112"],
        ["TOTAL", "422/669 (63.1%)", "214", "105", "142", "208"],
    ],
    col_widths=cw2, highlight_last_row=True,
)
pdf.body_text("Bias: Moderate TRUE bias. Similar pattern to gpt-oss-120b but less accurate overall.")

# gemma
pdf.sub_title("gemma-4-31b")
pdf.table(
    ["Dataset", "Accuracy", "T->T", "T->F", "F->T", "F->F"],
    [
        ["hard1", "51/69 (73.9%)", "8", "16", "2", "43"],
        ["hard2", "117/200 (58.5%)", "19", "81", "2", "98"],
        ["hard3", "226/399 (56.6%)", "48", "147", "26", "178"],
        ["TOTAL", "394/668 (59.0%)", "75", "244", "30", "319"],
    ],
    col_widths=cw2, highlight_last_row=True,
)
pdf.body_text("Bias: Extreme FALSE bias. T->F (244) dominates errors - model misses 76.5% of TRUE implications. Very few confabulations (30).")

# v4 comparison
pdf.section_title("Comparison vs v4 Cheatsheet")
cw3 = [28, 22, 22, 22, 22, 22, 22]
pdf.table(
    ["Model", "v4 h1", "v4.1 h1", "v4 h2", "v4.1 h2", "v4 h3", "v4.1 h3"],
    [
        ["grok",     "77.9%", "76.8%", "76.5%", "80.0%", "60.5%", "59.2%"],
        ["gpt-120b", "43.9%", "78.3%", "52.6%", "75.0%", "46.1%", "60.0%"],
        ["gpt-20b",  "58.5%", "69.6%", "43.7%", "70.0%", "50.0%", "58.5%"],
        ["gemma",    "62.3%", "73.9%", "73.6%", "58.5%", "52.5%", "56.6%"],
    ],
    col_widths=cw3,
)

# Fixes
pdf.section_title("Harness Fixes Applied")
fixes = [
    ("1. temperature=1.0 for reasoning models",
     "gpt-oss-20b/120b now use per-model params.temperature: 1.0. Root cause: OpenAI reasoning models silently fail with temperature=0 on OpenRouter."),
    ("2. max_tokens=65536 for reasoning models",
     "gpt-oss-20b averaged 9,215 output tokens; 48/346 responses hit the old 32K ceiling. Reasoning tokens count against the limit."),
    ("3. Per-request hard timeout (180s)",
     "Replaced buggy asyncio.wait_for (which included semaphore queue wait) with per-request aiohttp.ClientTimeout(total=180)."),
    ("4. Null response body guard",
     "Handles resp.json() returning None from OpenRouter."),
    ("5. Empty response retry",
     "Detects 0-token responses and retries instead of silently accepting them."),
    ("6. Longer retry backoff",
     "Changed from [2, 5, 15]s to [5, 15, 30]s."),
]
for title, desc in fixes:
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 5, title, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 8)
    pdf.multi_cell(0, 4.5, desc)
    pdf.ln(1)

pdf.output("results/v4.1_results.pdf")
print("PDF written to results/v4.1_results.pdf")
