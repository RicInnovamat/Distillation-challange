#!/usr/bin/env python3
"""Generate the v4.1 official-mode sweep PDF summary."""
import json
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).parent
OUT = ROOT / "v4.1_official_sweep.pdf"

RUNS = [
    ("gpt-oss-120b", "hard1", ROOT / "gpt-oss-120b_openrouter_hard1_20260410_135517.json"),
    ("gpt-oss-120b", "hard2", ROOT / "gpt-oss-120b_openrouter_hard2_20260410_135655.json"),
    ("gpt-oss-120b", "hard3", ROOT / "gpt-oss-120b_openrouter_hard3_20260410_140034.json"),
    ("llama-3.3-70b", "hard1", ROOT / "llama-3.3-70b_openrouter_hard1_20260410_162620.json"),
    ("llama-3.3-70b", "hard2", ROOT / "llama-3.3-70b_openrouter_hard2_20260410_163657.json"),
    ("llama-3.3-70b", "hard3", ROOT / "llama-3.3-70b_openrouter_hard3_20260410_165705.json"),
    ("gemma-4-31b",   "hard1", ROOT / "gemma-4-31b_openrouter_hard1_20260411_012506.json"),
    ("gemma-4-31b",   "hard2", ROOT / "gemma-4-31b_openrouter_hard2_20260411_020127.json"),
    ("gemma-4-31b",   "hard3", ROOT / "gemma-4-31b_openrouter_hard3_20260411_044616.json"),
]

DATASET_N = {"hard1": 69, "hard2": 200, "hard3": 400}


def load_all():
    data = {}
    for model, dset, path in RUNS:
        d = json.load(open(path))
        data[(model, dset)] = d["summary"]
    return data


def totals(data, model):
    t = {"total": 0, "correct": 0, "wrong": 0, "parse_errors": 0,
         "true_as_true": 0, "true_as_false": 0, "false_as_true": 0, "false_as_false": 0}
    for (m, _), s in data.items():
        if m != model:
            continue
        for k in t:
            t[k] += s.get(k, 0)
    t["accuracy"] = t["correct"] / t["total"] if t["total"] else 0
    return t


class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font("Helvetica", "B", 16)
            self.cell(0, 10, "v4.1 Cheatsheet - Official Mode Sweep",
                      new_x="LMARGIN", new_y="NEXT", align="C")
            self.set_font("Helvetica", "", 10)
            self.cell(0, 6,
                      "SAIR Mathematics Distillation Challenge - Equational Theories Stage 1",
                      new_x="LMARGIN", new_y="NEXT", align="C")
            self.cell(0, 6, "Sweep dates: 2026-04-10 / 2026-04-11",
                      new_x="LMARGIN", new_y="NEXT", align="C")
            self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    def section_title(self, title):
        self.set_font("Helvetica", "B", 13)
        self.set_fill_color(50, 70, 110)
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

    def bullet_list(self, items):
        self.set_font("Helvetica", "", 9)
        for it in items:
            self.multi_cell(0, 5, "- " + it)
            self.ln(0.5)
        self.ln(1)

    def table(self, headers, rows, col_widths=None, highlight_last_row=False,
              highlight_rows=None, header_color=(50, 70, 110)):
        highlight_rows = highlight_rows or []
        if col_widths is None:
            col_widths = [self.epw / len(headers)] * len(headers)
        # Header
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(*header_color)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, h, border=1, align="C", fill=True)
        self.ln()
        # Rows
        self.set_text_color(0, 0, 0)
        for ri, row in enumerate(rows):
            is_last = ri == len(rows) - 1
            highlight = (is_last and highlight_last_row) or ri in highlight_rows
            if highlight:
                self.set_font("Helvetica", "B", 8)
                self.set_fill_color(220, 235, 250)
            else:
                self.set_font("Helvetica", "", 8)
                if ri % 2 == 0:
                    self.set_fill_color(245, 245, 245)
                else:
                    self.set_fill_color(255, 255, 255)
            for i, val in enumerate(row):
                self.cell(col_widths[i], 5.5, str(val), border=1, align="C", fill=True)
            self.ln()
        self.ln(2)


def fmt_pct(num, den):
    return f"{num}/{den} ({num/den*100:.1f}%)" if den else "-"


def main():
    data = load_all()

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ----- Overview -----
    pdf.body_text(
        "Cheatsheet: v4.1_10KB_cheatsheet.md (~10,231 bytes). "
        "Datasets: hard1 (69), hard2 (200), hard3 (400) - 669 problems per model. "
        "Backend: OpenRouter. "
        "Mode: --official-mode (mirrors SAIR evaluation_models.json) with documented "
        "divergences for gemma-4-31b noted below. All official runs use seed=0, "
        "temperature=0.0, max_tokens=8192, bf16 provider pinning."
    )

    # ----- Headline table -----
    pdf.section_title("Headline Results")
    cw = [32, 30, 32, 32, 34, 14]
    headline_rows = []
    order = ["gemma-4-31b", "gpt-oss-120b", "llama-3.3-70b"]
    for m in order:
        t = totals(data, m)
        row = [m]
        for ds in ["hard1", "hard2", "hard3"]:
            s = data[(m, ds)]
            row.append(fmt_pct(s["correct"], s["total"]))
        row.append(fmt_pct(t["correct"], t["total"]))
        row.append(str(t["parse_errors"]))
        headline_rows.append(row)
    pdf.table(
        ["Model", "hard1 (69)", "hard2 (200)", "hard3 (400)", "ALL (669)", "PE"],
        headline_rows,
        col_widths=cw,
        highlight_rows=[0],  # gemma wins
    )

    # ----- Per-model confusion matrices -----
    pdf.section_title("Confusion Matrices by Dataset")

    # one subsection per model
    for m in order:
        pdf.sub_title(m)
        rows = []
        for ds in ["hard1", "hard2", "hard3"]:
            s = data[(m, ds)]
            n = s["total"]
            rows.append([
                ds,
                s["total"],
                f"{s['correct']} ({s['accuracy']*100:.1f}%)",
                s["true_as_true"],
                s["true_as_false"],
                s["false_as_true"],
                s["false_as_false"],
                s["parse_errors"],
            ])
        t = totals(data, m)
        rows.append([
            "ALL",
            t["total"],
            f"{t['correct']} ({t['accuracy']*100:.1f}%)",
            t["true_as_true"],
            t["true_as_false"],
            t["false_as_true"],
            t["false_as_false"],
            t["parse_errors"],
        ])
        pdf.table(
            ["Set", "N", "Correct", "T->T", "T->F", "F->T", "F->F", "PE"],
            rows,
            col_widths=[18, 14, 32, 18, 18, 18, 18, 14],
            highlight_last_row=True,
        )

    # ----- Recall section -----
    pdf.section_title("TRUE/FALSE Recall (totals across 669 problems)")
    recall_rows = []
    for m in order:
        t = totals(data, m)
        tt, tf, ft, ff = t["true_as_true"], t["true_as_false"], t["false_as_true"], t["false_as_false"]
        true_n = tt + tf
        false_n = ff + ft
        recall_rows.append([
            m,
            fmt_pct(tt, true_n),
            fmt_pct(ff, false_n),
            ft,  # confabulations
            tf,  # missed implications
            f"{t['accuracy']*100:.1f}%",
        ])
    pdf.table(
        ["Model", "TRUE recall", "FALSE recall", "Confab. (F->T)", "Missed (T->F)", "Overall"],
        recall_rows,
        col_widths=[34, 36, 36, 32, 32, 20],
        highlight_rows=[0],
    )

    # ----- Key observations -----
    pdf.add_page()
    pdf.section_title("Key Observations")
    pdf.bullet_list([
        "gemma-4-31b leads the official sweep at 67.4% (451/669) - 10.9pp ahead of "
        "gpt-oss-120b and 15.2pp ahead of llama. This flips the non-official v4.1 "
        "ranking where grok-4.1-fast was strongest.",

        "llama-3.3-70b is a degenerate default-FALSE classifier: 0/317 TRUE recall "
        "across all three hard sets. It answers FALSE on every parseable problem "
        "and collects all 349 FALSE-labelled cases for free. The v4.1 cheatsheet "
        "decision procedure collapses to \"RULE: default false\" for llama - this "
        "reproduces prior observations in CLAUDE.md.",

        "gpt-oss-120b is the most balanced on TRUE/FALSE but pays for it with the "
        "highest confabulation rate (109 F->T errors). It is the only official "
        "model that actually engages with TRUE cases at a non-trivial rate (137 "
        "correct TRUE answers) while still catching 241/350 FALSE cases.",

        "gemma-4-31b has the best TRUE recall by far (48.3%, 154/319) while "
        "maintaining 84.9% FALSE recall. Moderate FALSE bias, not catastrophic.",

        "All three models hit near-zero parse errors (3 total, all from llama "
        "hard2). The harness retry fixes applied on 2026-04-10 (empty-content "
        "retry matching SAIR's llm.py behaviour, 180s->300s timeout, concurrency "
        "cap for reasoning models) held across 2007 API calls.",

        "Provider pinning + seed=0 gives gemma a measurable accuracy lift over "
        "the 2026-04-09 non-official v4.1 sweep (73.9->76.8 on hard1, 55.5->75.0 "
        "on hard2, 56.6->62.0 on hard3). Most of the gain is on hard2 and hard3 "
        "where default OpenRouter routing had previously landed on less consistent "
        "providers.",

        "gpt-oss-120b output tokens stay well below the 8192 cap on every call "
        "(max 2742, avg ~820). Its reasoning at effort=low is roughly 3x more "
        "compact than gemma-4-31b's at the same setting - this is the root cause "
        "of the gemma-specific failure mode documented below.",
    ])

    # ----- Technical specs -----
    pdf.section_title("Technical Specifications")

    pdf.sub_title("gpt-oss-120b - strict SAIR official")
    pdf.code_block(
        'provider: {order: ["DeepInfra"], quantizations: ["bf16"], allow_fallbacks: false}\n'
        'reasoning: {effort: "low"}\n'
        'seed: 0\n'
        'temperature: 0.0\n'
        'max_tokens: 8192'
    )
    pdf.body_text(
        "Mirrors SAIR evaluation_models.json exactly. No divergence. "
        "Max observed output tokens: 2742 (well below 8192 cap), avg ~820. "
        "Sweep date: 2026-04-10 13:54-14:00."
    )

    pdf.sub_title("llama-3.3-70b-instruct - strict SAIR official")
    pdf.code_block(
        'provider: {order: ["DeepInfra"], quantizations: ["fp8"], allow_fallbacks: false}\n'
        'reasoning_effort: "none"  (no reasoning mode - matches SAIR spec)\n'
        'seed: 0\n'
        'temperature: 0.0\n'
        'max_tokens: 8192'
    )
    pdf.body_text(
        "Mirrors SAIR evaluation_models.json exactly. No divergence. "
        "3 parse errors on hard2 (empty-content retries exhausted). "
        "Sweep date: 2026-04-10 14:06-16:57."
    )

    pdf.sub_title("gemma-4-31b-it - divergence from strict SAIR")
    pdf.code_block(
        'provider: {\n'
        '  order: ["Novita", "Parasail", "Venice", "AkashML"],\n'
        '  quantizations: ["bf16", "fp8"],\n'
        '  allow_fallbacks: true\n'
        '}\n'
        '# reasoning_effort: "low"  <-- DISABLED (see note)\n'
        'seed: 0\n'
        'temperature: 0.0\n'
        'max_tokens: 8192\n'
        '--concurrency 5  (hard3 only, after bf16 providers rate-limited)'
    )
    pdf.body_text(
        "Two documented divergences from SAIR evaluation_models.json:"
    )
    pdf.bullet_list([
        "reasoning_effort=\"low\" disabled. Under SAIR's strict config gemma's "
        "thinking tokens fully exhaust the 8192 max_tokens budget on every hard1 "
        "problem with a 10KB cheatsheet (content=\"\", finish_reason=length). "
        "SAIR's llm.py has a doubled-budget retry guardrail but it is a no-op "
        "for gemma (retry_cap == initial cap == 8192). Verified via direct "
        "OpenRouter probe: a minimal test problem returns 103 reasoning tokens / "
        "0 content tokens / finish_reason=length. Flagged upstream to SAIR.",

        "AkashML/fp8 added as 4th fallback provider (alongside bf16 Novita/"
        "Parasail/Venice). All three bf16 providers hit simultaneous 429 "
        "server_overload during the hard3 run; AkashML at fp8 was the only "
        "healthy remaining provider. Quantization diverges (bf16 -> mixed "
        "bf16+fp8) but weights and pricing are identical across quants."
    ])
    pdf.body_text(
        "Sweep dates: hard1 2026-04-11 00:42 / hard2 2026-04-11 01:25 / "
        "hard3 2026-04-11 03:15-04:46."
    )

    # ----- Harness notes -----
    pdf.section_title("Harness Fixes Applied During This Sweep")
    pdf.bullet_list([
        "eval_harness.py HARD_TIMEOUT_S: 180 -> 300. Matches SAIR llm.py's "
        "recommended httpx client timeout; reduces spurious timeouts under "
        "reasoning-mode tail latency.",

        "Empty-content retry: previously only fired when completion_tokens==0; "
        "now fires on any empty text response (matching SAIR llm.py). Catches "
        "the gemma reasoning-exhaustion case and llama's occasional empty "
        "finish_reason=stop responses.",

        "Concurrency cap: when official-mode + reasoning.effort is non-none, "
        "concurrency is auto-capped at 3 to avoid provider 429 stampedes. "
        "Non-reasoning official runs retain the configured concurrency.",

        "build_official_overrides: fallback_providers entries now support the "
        "same slug/quant syntax as the primary (e.g. \"AkashML/fp8\"). Any "
        "distinct quant values are unioned into the quantizations filter so "
        "mixed-quant fallback pools work correctly.",
    ])

    pdf.output(str(OUT))
    print(f"PDF written to {OUT}")


if __name__ == "__main__":
    main()
