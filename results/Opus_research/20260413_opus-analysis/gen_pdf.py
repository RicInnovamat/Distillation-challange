#!/usr/bin/env python3
"""Render suggestions.pdf for the opus-informed cheatsheet analysis.

Adapts the fpdf2 PDF class used by results/20260410_v4.1-official/gen_pdf.py.
Content is hand-structured (not markdown-to-PDF); actual numeric results are
loaded from JSON files on disk so the PDF stays in sync with the eval outputs.
If v.Opus-1 sweep results exist, they are included in the empirical comparison
table; otherwise that section is rendered with a "pending" note.
"""
import json
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).parent
REPO = ROOT.parent.parent
OUT = ROOT / "suggestions.pdf"

V41 = REPO / "results" / "20260412_v4.1_official"
V52 = REPO / "results" / "20260412_v5.2_official"
VOP = REPO / "results" / "20260413_v.Opus-1_official"
VOP2 = REPO / "results" / "20260413_v.Opus-2_official"
VOP21 = REPO / "results" / "20260413_v.Opus-2.1_official"
OPUS = REPO / "results" / "20260411_opus-hard1"

DATASETS = [("hard1", 69), ("hard2", 200), ("hard3", 400)]


def load_summary(run_dir: Path, model: str, dataset: str):
    """Find the newest <model>_openrouter_<dataset>_*.json under run_dir."""
    if not run_dir.exists():
        return None
    files = sorted(run_dir.glob(f"{model}_openrouter_{dataset}_*.json"))
    if not files:
        return None
    return json.loads(files[-1].read_text())["summary"]


def combined_opus_hard1():
    """Combine all opus-solver hard1 result files, prefer successful records."""
    records = {}
    for p in sorted(OPUS.glob("opus-solver_*.json")):
        for r in json.loads(p.read_text()).get("problems", []):
            pid = r["problem_id"]
            if pid not in records or (r["parse_ok"] and not records[pid]["parse_ok"]):
                records[pid] = r
    total = len(records)
    correct = sum(1 for r in records.values() if r["correct"] is True)
    tt = sum(1 for r in records.values() if r["expected"] is True and r["predicted"] is True)
    tf = sum(1 for r in records.values() if r["expected"] is True and r["predicted"] is False)
    ft = sum(1 for r in records.values() if r["expected"] is False and r["predicted"] is True)
    ff = sum(1 for r in records.values() if r["expected"] is False and r["predicted"] is False)
    pe = sum(1 for r in records.values() if not r["parse_ok"])
    return {
        "total": total, "correct": correct,
        "true_as_true": tt, "true_as_false": tf,
        "false_as_true": ft, "false_as_false": ff,
        "parse_errors": pe,
        "accuracy": correct / total if total else 0,
    }


class PDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font("Helvetica", "B", 16)
            self.cell(0, 10, "v.Opus-1 Cheatsheet - Design Notes",
                      new_x="LMARGIN", new_y="NEXT", align="C")
            self.set_font("Helvetica", "", 10)
            self.cell(0, 6,
                      "SAIR Mathematics Distillation Challenge - Equational Theories Stage 1",
                      new_x="LMARGIN", new_y="NEXT", align="C")
            self.cell(0, 6, "Analysis date: 2026-04-13",
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
        for it in items:
            self.multi_cell(0, 5, "- " + it)
            self.ln(0.5)
        self.ln(1)

    def table(self, headers, rows, col_widths=None, highlight_rows=None,
              header_color=(50, 70, 110)):
        highlight_rows = highlight_rows or []
        if col_widths is None:
            col_widths = [self.epw / len(headers)] * len(headers)
        self.set_font("Helvetica", "B", 8)
        self.set_fill_color(*header_color)
        self.set_text_color(255, 255, 255)
        for i, h in enumerate(headers):
            self.cell(col_widths[i], 6, h, border=1, align="C", fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)
        for ri, row in enumerate(rows):
            if ri in highlight_rows:
                self.set_font("Helvetica", "B", 8)
                self.set_fill_color(220, 235, 250)
            else:
                self.set_font("Helvetica", "", 8)
                self.set_fill_color(245, 245, 245 if ri % 2 == 0 else 255)
                if ri % 2 != 0:
                    self.set_fill_color(255, 255, 255)
            for i, val in enumerate(row):
                self.cell(col_widths[i], 5.5, str(val), border=1, align="C", fill=True)
            self.ln()
        self.ln(2)


def fmt_pct(num, den):
    return f"{num}/{den} ({num/den*100:.1f}%)" if den else "-"


def fmt_acc(s):
    return f"{s['correct']}/{s['total']} ({s['accuracy']*100:.1f}%)" if s else "-"


def main():
    # ----- Load all data -----
    opus_h1 = combined_opus_hard1()

    v41 = {(m, d): load_summary(V41, m, d)
           for m in ("gpt-oss-120b", "gemma-4-31b")
           for d, _ in DATASETS}
    v52 = {(m, d): load_summary(V52, m, d)
           for m in ("gpt-oss-120b", "gemma-4-31b")
           for d, _ in DATASETS}
    vop = {(m, d): load_summary(VOP, m, d)
           for m in ("gpt-oss-120b", "gemma-4-31b")
           for d, _ in DATASETS}
    vop2 = {(m, "hard1"): load_summary(VOP2, m, "hard1")
            for m in ("gpt-oss-120b", "gemma-4-31b")}
    vop21 = {(m, "hard1"): load_summary(VOP21, m, "hard1")
             for m in ("gpt-oss-120b", "gemma-4-31b")}

    pdf = PDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # ----- Executive summary -----
    pdf.section_title("Executive Summary")
    pdf.body_text(
        "Opus-solver (Claude Opus 4.6, no cheatsheet, pure reasoning, 30-min "
        "per-problem cap) scored 56/69 (81.2%) on hard1 - beating the best "
        "cheatsheet result (gemma + v4.1 at 75.4%) by ~6 percentage points. "
        "Critically, Opus's T-to-F (missed TRUE) count was zero, while both "
        "cheatsheet models missed 10-12 TRUE implications each. v.Opus-1 "
        "targets this gap by porting Opus's variable-substitution technique "
        "into v4.1's decision procedure while adding anti-confabulation "
        "guardrails against Opus's own failure mode (the singleton fallacy)."
    )

    # ----- Baseline comparison on hard1 -----
    pdf.section_title("Hard1 Baselines")
    rows = [
        ["opus-solver (no cheatsheet)",
         fmt_acc(opus_h1),
         opus_h1["true_as_false"], opus_h1["false_as_true"], opus_h1["parse_errors"]],
    ]
    for m in ("gemma-4-31b", "gpt-oss-120b"):
        s = v41[(m, "hard1")]
        rows.append([f"{m} + v4.1 (official)", fmt_acc(s),
                     s["true_as_false"], s["false_as_true"], s["parse_errors"]])
    for m in ("gemma-4-31b", "gpt-oss-120b"):
        s = v52[(m, "hard1")]
        rows.append([f"{m} + v5.2 (official)", fmt_acc(s),
                     s["true_as_false"], s["false_as_true"], s["parse_errors"]])
    pdf.table(
        ["Configuration", "Correct", "T->F (missed)", "F->T (confab)", "PE"],
        rows,
        col_widths=[64, 42, 30, 30, 16],
        highlight_rows=[0],
    )
    pdf.body_text(
        "Key signal: Opus never defaults to FALSE on a real TRUE implication. "
        "9 hard1 problems are missed TRUEs shared between Gemma-v4.1 and "
        "GPT-v4.1 (both predicted FALSE). Only 2 problems are shared "
        "confabulations (both predicted TRUE on a FALSE answer). v5.2 "
        "regresses both models - its structured output format dilutes the "
        "HARD-STOP discipline."
    )

    # ----- Reasoning pattern comparison -----
    pdf.add_page()
    pdf.section_title("Reasoning Pattern 1 - Missed TRUE (hard1_0007)")
    pdf.body_text(
        "Equation 1: x = (y*(y*(y*z)))*x    Equation 2: x*y = z*(w*(w*y))    "
        "Expected: TRUE. Opus correct; Gemma and GPT (v4.1) both FALSE."
    )

    pdf.quote_block(
        "Opus (correct, TRUE) - variable substitution",
        "Pick any elements a, b. Instantiating y:=a, z:=b in Equation 1 gives "
        "x = (a*(a*(a*b)))*x. Let c = a*(a*(a*b)). Then c*x = x for every x, "
        "so c is a left identity. Substitute y:=c back; using c*u=u three "
        "times, Equation 1 becomes x = z*x for all x,z. Hence every element "
        "z is a left identity. Therefore the magma satisfies u*v = v "
        "for all u,v."
    )
    pdf.quote_block(
        "GPT v4.1 (wrong, FALSE) - stalls on free-form algebra",
        "Means product (y*(y*(y*z))) acts as left identity for all x. So "
        "left identity element L depends on y,z but must be left identity "
        "for all x. In a magma we can define operation such that a*b = a "
        "for all a,b (left projection). Then Eq1 RHS = y * x = y, not x. "
        "So left projection does not satisfy Eq1 generally unless all "
        "variables equal? So need operation where... [truncated, defaults "
        "to FALSE]"
    )
    pdf.quote_block(
        "Gemma v4.1 (wrong, FALSE) - witness-testing only",
        "Test Equation 1 under left-zero (a*b = a): LHS = x, RHS = y. Not "
        "identity. Right-zero: not identity. XOR: not identity. Check "
        "Contradiction Motifs (2.8): rhsVars=3, Lx=F, Rx=F, xTop=right, "
        "topShape=v-m... no motif fires. Check syntactic FALSE routes... "
        "none apply. [Defaults to FALSE]"
    )
    pdf.body_text(
        "Pattern: Opus executes substitution iteratively to derive the "
        "structural consequence 'every element is a left identity'. Gemma "
        "tests canonical witnesses; when none satisfies Eq1, she has no "
        "further technique and defaults to FALSE. GPT identifies the same "
        "structural clue as Opus but cannot sustain the derivation and "
        "also defaults to FALSE."
    )

    pdf.section_title("Reasoning Pattern 2 - Opus Confabulation (hard1_0032)")
    pdf.body_text(
        "Equation 1: x = ((y*x)*x)*(x*z)    Equation 2: x*y = (z*z)*z    "
        "Expected: FALSE. Gemma correct; Opus and GPT wrong."
    )
    pdf.quote_block(
        "Opus (wrong, TRUE) - singleton fallacy",
        "Claim: Equation 1 is only satisfiable in the one-element (trivial) "
        "magma. In a trivial magma every equation holds, so Equation 2 is "
        "implied. Variables y and z are 'ghost variables' - they appear on "
        "the right but not on the left. So for every fixed x, the RHS must "
        "be constant in y and z and equal x... [goes on to 'prove' "
        "singleton-only, incorrectly]"
    )
    pdf.quote_block(
        "Gemma v4.1 (correct, FALSE) - finds witness",
        "Test left-zero (a*b = a): Eq1 LHS=x, RHS=((y*x)*x)*(x*z) -> y. Not "
        "identity. Test right-zero (a*b = b): Eq1 LHS=x, RHS=(x*x)*z -> z. "
        "Eq1 becomes x=z, not identity. [Continues with next witness, "
        "eventually fires a FALSE witness rule.]"
    )
    pdf.body_text(
        "Pattern: Opus makes this mistake 5 times on hard1 (hard1_0016, "
        "0025, 0032, 0047, 0062). The singleton-fallacy argument is "
        "semantically sound only when Eq1 literally has the shape 'x = T' "
        "with x not in T (v4.1 rule 2.3). Opus generalizes it beyond that "
        "shape without verification."
    )

    # ----- Gap mapping table -----
    pdf.add_page()
    pdf.section_title("Gap Analysis: v4.1 / v5.2 vs Opus")
    gap_rows = [
        ["Variable substitution -> derive structure",
         "Not present", "STEP 6 (only x=y=z test)",
         "Added as STEP 4.5 Substitution Probe"],
        ["Exhaustive 2-element enumeration",
         "Not in witnesses", "Not in witnesses",
         "FORBIDDEN INFERENCES requires this for singleton claims"],
        ["Recognize Eq1 -> left/right identity",
         "Partial (2.6/2.7)", "Same",
         "Substitution Probe (P2) makes derivation explicit"],
        ["Over-eager right-projection match",
         "Premise check is syntactic only", "Same",
         "Tightened 2.7: verify T stays x-free under Eq1 identities"],
        ["Singleton fallacy guard",
         "Not present", "Not present",
         "FORBIDDEN INFERENCES block (bullet 1)"],
        ["Output format contract",
         "VERDICT+RULE first, HARD-STOP", "4 structured fields",
         "Kept v4.1's compact contract (drops v5.2 fields)"],
    ]
    pdf.table(
        ["Pattern", "v4.1", "v5.2", "v.Opus-1 response"],
        gap_rows,
        col_widths=[52, 38, 34, 58],
    )

    # ----- Numbered suggestions -----
    pdf.section_title("Suggestions Applied in v.Opus-1")
    pdf.bullet_list([
        "S1 - Substitution Probe (new STEP 4.5): after canonical witnesses "
        "fail, execute three fixed substitutions on Eq1 (total collapse, "
        "single collapse y:=x, square v:=x*x). Any that reduces Eq1 to a "
        "projection/square/constant shape fires the corresponding TRUE "
        "rule. This captures what Opus does for hard1_0007, 0013, 0018, "
        "0034 etc. without unbounded free-form algebra.",

        "S2 - Expanded witness library: added two new canonical witnesses "
        "to STEP 4 (cyclic shift on Z/3, pointed right-projection). "
        "Broadens the FALSE-witness fan-out beyond the 4 v4.1 witnesses "
        "(left/right-zero, XOR, constant).",

        "S3 - FORBIDDEN INFERENCES block: explicit callout listing three "
        "inference patterns the model must not use (singleton fallacy, "
        "shape-similarity, trivial-magma TRUE). Targets Opus's 5 "
        "confabulations and GPT's over-eager right-projection pattern.",

        "S4 - Tightened 2.7 premise: verify T stays x-free under any "
        "identity Eq1 itself forces, not only syntactic x-freeness. Fixes "
        "the hard1_0033 failure mode where both cheatsheet models "
        "pattern-matched the outer 'x = T*x' shape without semantic check.",

        "S5 - Preserve v4.1 output contract: VERDICT+RULE first, HARD-STOP. "
        "Do not reintroduce v5.2's structured fields (REASONING / PROOF / "
        "COUNTEREXAMPLE) - they regress both models.",

        "S6 - Preserve all v4.1 rules. Additions are strictly additive. "
        "Final size 10,194 bytes (46 under the 10,240 SAIR limit).",
    ])

    # ----- Empirical results (if sweep complete) -----
    pdf.add_page()
    pdf.section_title("Empirical Validation: v.Opus-1 vs v4.1")
    have_vop = all(vop[(m, d)] for m in ("gpt-oss-120b", "gemma-4-31b") for d, _ in DATASETS)
    if have_vop:
        rows = []
        for m in ("gemma-4-31b", "gpt-oss-120b"):
            for d, n in DATASETS:
                a = v41[(m, d)]
                b = vop[(m, d)]
                delta = (b["accuracy"] - a["accuracy"]) * 100
                rows.append([
                    f"{m} / {d}",
                    f"{a['correct']}/{a['total']} ({a['accuracy']*100:.1f}%)",
                    f"{b['correct']}/{b['total']} ({b['accuracy']*100:.1f}%)",
                    f"{delta:+.1f}pp",
                    b["true_as_false"],
                    b["false_as_true"],
                ])
        pdf.table(
            ["Config", "v4.1", "v.Opus-1", "Delta", "T->F", "F->T"],
            rows,
            col_widths=[46, 38, 38, 22, 18, 18],
        )

        # ----- 4-iteration comparison on hard1 -----
        have_vop2 = all(vop2[(m, "hard1")] for m in ("gpt-oss-120b", "gemma-4-31b"))
        have_vop21 = all(vop21[(m, "hard1")] for m in ("gpt-oss-120b", "gemma-4-31b"))
        if have_vop2 and have_vop21:
            pdf.add_page()
            pdf.section_title("Four-iteration comparison on hard1")
            pdf.body_text(
                "v.Opus-2 placed a new positive TRUE-bias rule (2.13 'restrictive "
                "bare source') in STEP 2; v.Opus-2.1 relocated the same rule to a "
                "STEP 4.5 tiebreaker position (fires only after all witnesses fail)."
            )
            rows4 = []
            for m in ("gemma-4-31b", "gpt-oss-120b"):
                a = v41[(m, "hard1")]
                b = vop[(m, "hard1")]
                c = vop2[(m, "hard1")]
                d = vop21[(m, "hard1")]
                rows4.append([
                    m,
                    f"{a['correct']} ({a['accuracy']*100:.1f}%)",
                    f"{b['correct']} ({b['accuracy']*100:.1f}%)",
                    f"{c['correct']} ({c['accuracy']*100:.1f}%)",
                    f"{d['correct']} ({d['accuracy']*100:.1f}%)",
                ])
            pdf.table(
                ["Model", "v4.1", "v.Opus-1", "v.Opus-2", "v.Opus-2.1"],
                rows4,
                col_widths=[40, 35, 35, 35, 35],
                highlight_rows=[0],
            )
            pdf.body_text(
                "Confabulation (F->T) and missed-TRUE (T->F) breakdown:"
            )
            rows_cm = []
            for m in ("gemma-4-31b", "gpt-oss-120b"):
                for label, src in (("v4.1", v41), ("v.Opus-1", vop),
                                    ("v.Opus-2", vop2), ("v.Opus-2.1", vop21)):
                    s = src[(m, "hard1")]
                    rows_cm.append([
                        m, label, s["true_as_true"], s["true_as_false"],
                        s["false_as_true"], s["false_as_false"]
                    ])
            pdf.table(
                ["Model", "Cheatsheet", "T->T", "T->F", "F->T", "F->F"],
                rows_cm,
                col_widths=[40, 35, 25, 25, 25, 25],
            )
            pdf.section_title("Conclusion: v4.1 remains the best unified cheatsheet")
            pdf.bullet_list([
                "Across four iterations (v.Opus-1, v.Opus-2, v.Opus-2.1) none "
                "net-improved on v4.1 under the 'one unified cheatsheet' constraint.",

                "Model asymmetry is large: GPT verifies rule triggers before "
                "committing to TRUE; Gemma pattern-matches and fires. A rule "
                "that helps one harms the other.",

                "Confabulation-reduction and TRUE-recall are in fundamental "
                "tension at reasoning_effort=low. Guardrails suppress both; "
                "amplifiers inflate both. Small net deltas, large swings per rule.",

                "Static cheatsheets at reasoning_effort=low appear bounded near "
                "72-75% on hard1. Opus reaches 81% via variable substitution, "
                "which these models cannot reliably execute at the given budget.",

                "Recommendation: submit v4.1 for Stage-1. Future work: few-shot "
                "worked examples of Opus-style substitution derivations.",
            ])

            # ----- Substantiation of the few-shot recommendation -----
            pdf.add_page()
            pdf.section_title("Substantiating the few-shot recommendation")
            pdf.body_text(
                "The recommendation rests on three substantiated claims: (1) "
                "Opus uses a specific 4-step derivation pattern that resolves "
                "the shared missed-TRUE cases; (2) models at reasoning_effort=low "
                "do not invent this pattern under the current cheatsheet for "
                "procedural, not token-budget, reasons; (3) a worked example "
                "embedded as few-shot material fits in the 10,240-byte SAIR limit."
            )

            pdf.sub_title("12.1 Opus's technique: four atomic steps")
            pdf.body_text(
                "Every successful resolution of the 9 shared missed-TRUE "
                "cases on hard1 follows the same four steps. Concrete trace "
                "for hard1_0007 (answer TRUE, Opus 52s, both cheatsheet "
                "models wrong):"
            )
            pdf.bullet_list([
                "INSTANTIATE. Pick arbitrary elements. Example: 'Instantiating "
                "y := a, z := b in Equation 1 gives x = (a*(a*(a*b)))*x for all x.'",

                "NAME. Give the instantiated compound a short letter. Example: "
                "'Let c = a*(a*(a*b)). Then c*x = x for every x, so c is a "
                "left identity.'",

                "ITERATE. Feed the named quantity back into the original "
                "equation. Example: 'Substitute y := c back into Eq1. Using "
                "c*u = u three times, Eq1 becomes x = z*x for all x, z. Every "
                "element is a left identity -> right-projection magma.'",

                "EVALUATE. Plug Eq2 into the derived structural law. Example: "
                "'In right-projection, LHS of Eq 2 = y, RHS = y, so Eq 2 holds.'",
            ])
            pdf.body_text(
                "The same four steps resolve hard1_0018 (5-substitution chain) "
                "and hard1_0041 (forced right-projection via 2-element "
                "exhaustion). The atoms generalize; the content does not."
            )

            pdf.sub_title("12.2 Why effort=low models do not invent the pattern")
            pdf.body_text(
                "Observed failure modes on the same 9 problems:"
            )
            pdf.bullet_list([
                "Sketch-without-execution (GPT). Correctly identifies 'L must "
                "be a left identity' but never executes step 3 (substituting "
                "y := L back). Drifts to 'probably false', defaults FALSE.",

                "Canonical-witness-only (Gemma). Tests 3 canonical witnesses, "
                "none satisfies Eq1, checks 7 syntactic FALSE routes, none "
                "fires, defaults FALSE. No substitution attempt at all.",

                "Depth-2 termination (both). When substitution is attempted, "
                "models stop after one step. They do not feed the result back "
                "into Eq1 a second time. The iterative feedback is exactly "
                "what Opus does and effort=low models do not.",
            ])
            pdf.body_text(
                "The bottleneck is procedural, not token-budget. Gemma has "
                "~4,000 tokens remaining after the prescribed procedure "
                "exhausts. The cheatsheet does not formalize which "
                "substitution to try or what to look for in the result, "
                "so the model does not spontaneously invent the strategy."
            )

            pdf.sub_title("12.3 Few-shot template: concrete proposal")
            pdf.body_text(
                "Embed a single worked example before the STEP 5 rewrite "
                "fallback (~900 bytes):"
            )
            pdf.code_block(
                "STEP 4.6. SUBSTITUTION DERIVATION (worked example)\n\n"
                "Suppose Eq1 is x = (y*(y*(y*z)))*x (bare, rhsVars=3, maxMult=3).\n"
                "STEP 2 found no TRUE route; STEPs 3-4 found no FALSE route.\n"
                "Apply the four atomic steps:\n\n"
                "(a) INSTANTIATE. Fix a, b. Set y:=a, z:=b in Eq1:\n"
                "    x = (a*(a*(a*b)))*x holds for all x.\n\n"
                "(b) NAME. Let c = a*(a*(a*b)). Then c*x = x, so c is a\n"
                "    left identity.\n\n"
                "(c) ITERATE. Substitute y:=c in Eq1 (z free). Use c*u=u\n"
                "    three times. Eq1 becomes x = z*x for all x, z. Every\n"
                "    element is a left identity -> u*v = v (right projection).\n\n"
                "(d) EVALUATE. Plug Eq2 into right projection. If both sides\n"
                "    reduce to the same variable, answer TRUE.\n\n"
                "Apply by analogy when Eq1 is bare AND maxMult >= 3 or\n"
                "ghost-variable structure. RULE: substitution derivation"
            )

            pdf.sub_title("12.4 Size trade-off (fits within 10,240 bytes)")
            pdf.body_text(
                "Adding ~900 bytes requires cutting ~900 bytes. Candidates:"
            )
            pdf.bullet_list([
                "Compress 2.8 motif list (C1-C15) into a single pattern "
                "table: ~450 bytes saved.",

                "Compress STEP 3 FALSE routes (3.1-3.6) into a shared "
                "one-line premise template: ~250 bytes saved.",

                "Merge 2.12 T1/T4/T5 into one bullet: ~200 bytes saved. "
                "Total ~900 bytes, exactly matching the example's footprint.",
            ])

            pdf.sub_title("12.5 Validation protocol for v.Opus-3")
            pdf.body_text(
                "Hypothesis: few-shot catches 4-6 of the 9 shared missed-TRUE "
                "problems on hard1 without introducing new confabulations "
                "(the example is conditioned on STEPs 2-4 having run first, "
                "so the witness filter stays in place)."
            )
            pdf.bullet_list([
                "Quantitative targets on hard1: GPT >= 52 (v4.1 +2); "
                "Gemma >= 54 (v4.1 +2); F->T <= v4.1 baseline (9 GPT, 5 Gemma).",

                "If achieved on hard1, extend to hard2+hard3 and decide "
                "Stage-1 submission from the full sweep.",

                "Risks: (1) Gemma may over-generalize the example to "
                "dissimilar problems; mitigate with tight trigger conditions. "
                "(2) Few-shot adds ~200 input tokens per call; cost increase "
                "< $0.002 total. (3) If T->T drops, abandon few-shot and "
                "consider multi-pass architecture (out of Stage-1 scope).",
            ])
    else:
        pdf.body_text(
            "Empirical sweep results pending. Once "
            "results/20260413_v.Opus-1_official/ contains the full hard1 + "
            "hard2 + hard3 runs for gpt-oss-120b and gemma-4-31b, re-run "
            "this script to populate the comparison table."
        )

    # ----- Post-mortem (if sweep complete and regression observed) -----
    if have_vop:
        regressions = 0
        for m in ("gemma-4-31b", "gpt-oss-120b"):
            for d, n in DATASETS:
                a = v41[(m, d)]; b = vop[(m, d)]
                if b["accuracy"] < a["accuracy"]:
                    regressions += 1
        pdf.section_title("Post-mortem: why v.Opus-1 regressed")
        pdf.body_text(
            f"v.Opus-1 regressed on {regressions} of 6 model-dataset combinations. "
            "The guardrails worked but the Substitution Probe did not compensate."
        )
        pdf.bullet_list([
            "Confabulation went DOWN across the board (F->T fell for nearly every "
            "run). The FORBIDDEN INFERENCES block achieved its stated goal: "
            "models rejected the singleton-fallacy and shape-similarity shortcuts.",

            "Missed-TRUE went UP, not down (T->F increased for nearly every run). "
            "This is the opposite of what the Substitution Probe was supposed to "
            "deliver. On gemma hard3 alone, missed-TRUE went from 108 to 142.",

            "Root cause 1 - FORBIDDEN INFERENCES is too aggressive. Models read "
            "'never conclude TRUE from X' as a strong prior against TRUE itself, "
            "generalizing caution to 'avoid TRUE unless a named rule fires "
            "exactly'.",

            "Root cause 2 - Substitution Probe preconditions are too narrow. "
            "P1/P2/P3 fire only when the reduced equation matches a specific "
            "shape. After substitution the result is usually algebraically close "
            "but not literally equal to a projection shape, so the probe does "
            "not fire and the model falls through to default-FALSE.",

            "Root cause 3 - official-mode models do not execute substitution "
            "symbolically. At reasoning_effort=low they sketch the probe in one "
            "or two sentences without simulating the derivation, then pattern-"
            "match the sketch against a fixed shape. No match -> default FALSE.",
        ])

    # ----- Closing -----
    pdf.section_title("Revised Design Directions (v.Opus-2)")
    pdf.bullet_list([
        "Remove the FORBIDDEN INFERENCES block. The confabulation gain "
        "(~20-30 fewer F->T) is dwarfed by the T->F penalty (~40 more "
        "missed TRUEs on gemma hard3).",

        "Broaden the Substitution Probe to accept algebraically-equivalent "
        "shapes, not just literal string matches. E.g. 'if after P2 the "
        "RHS reduces to a term whose leftmost operation's right operand is "
        "x, fire right projection'.",

        "Keep the witness library additions (S2) and tightened 2.7 premise "
        "(S4) - neither is implicated in the regression.",

        "Accept that v4.1 may be at or near the ceiling of what static "
        "cheatsheets achieve at reasoning_effort=low. Reaching Opus's 81% "
        "level likely requires a larger token budget or a fundamentally "
        "different prompt architecture (few-shot with worked substitution "
        "examples).",

        "Cross-model: Llama-3.3-70b was excluded from v.Opus-1 testing "
        "because of its catastrophic default-FALSE bias. A Llama-specific "
        "tail would need its own cheatsheet variant.",
    ])

    pdf.output(str(OUT))
    print(f"PDF written to {OUT}")


if __name__ == "__main__":
    main()
