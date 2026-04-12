"""Tests for eval_harness.parse_verdict.

Mirrors SAIR's official tests/test_judge.py at
https://github.com/SAIRcompetition/equational-theories-stage1-judge
so our local parser matches the official Stage 1 grader exactly.

Run: `python3 tests/test_parse_verdict.py`
"""
import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from eval_harness import parse_verdict


# ---------------------------------------------------------------------------
# Labeled VERDICT: marker
# ---------------------------------------------------------------------------

def test_verdict_true():
    pred, _ = parse_verdict("VERDICT: TRUE")
    assert pred is True


def test_verdict_false():
    pred, _ = parse_verdict("VERDICT: FALSE")
    assert pred is False


def test_verdict_case_insensitive():
    pred, _ = parse_verdict("verdict: true")
    assert pred is True


def test_verdict_fullwidth_colon():
    pred, _ = parse_verdict("VERDICT： TRUE")
    assert pred is True


# ---------------------------------------------------------------------------
# Boxed verdict (priority 3 — highest)
# ---------------------------------------------------------------------------

def test_boxed_verdict_true():
    pred, _ = parse_verdict(r"\boxed{TRUE}")
    assert pred is True


def test_boxed_verdict_false():
    pred, _ = parse_verdict(r"\boxed{FALSE}")
    assert pred is False


def test_boxed_double_backslash():
    pred, _ = parse_verdict(r"\\boxed{FALSE}")
    assert pred is False


def test_boxed_with_markdown_value():
    pred, _ = parse_verdict(r"\boxed{**FALSE**}")
    assert pred is False


def test_boxed_with_latex_wrapper_text():
    pred, _ = parse_verdict(r"\boxed{\text{TRUE}}")
    assert pred is True


def test_boxed_with_latex_wrapper_mathrm():
    pred, _ = parse_verdict(r"\boxed{\mathrm{FALSE}}")
    assert pred is False


def test_boxed_placeholder_answer_is_ignored():
    pred, _ = parse_verdict(r"Format reminder: \boxed{answer}")
    assert pred is None


# ---------------------------------------------------------------------------
# Other labeled markers (ANSWER, FINAL ANSWER, RESULT, OUTPUT_RESULT)
# ---------------------------------------------------------------------------

def test_answer_label_equals():
    pred, _ = parse_verdict("ANSWER = TRUE")
    assert pred is True


def test_final_answer_label():
    pred, _ = parse_verdict("FINAL ANSWER: FALSE")
    assert pred is False


def test_result_label_dash():
    pred, _ = parse_verdict("RESULT - TRUE")
    assert pred is True


def test_output_result_label():
    pred, _ = parse_verdict("OUTPUT_RESULT: FALSE")
    assert pred is False


# ---------------------------------------------------------------------------
# \text{TRUE}/\text{FALSE} LaTeX labeled marker
# ---------------------------------------------------------------------------

def test_latex_text_true():
    pred, _ = parse_verdict(r"\text{TRUE}")
    assert pred is True


def test_latex_text_false():
    pred, _ = parse_verdict(r"\text{FALSE}")
    assert pred is False


def test_latex_text_in_display_math_block():
    response = "The expressions are equivalent.\n\\[\n\\text{TRUE}\n\\]"
    pred, _ = parse_verdict(response)
    assert pred is True


def test_latex_text_case_insensitive():
    pred, _ = parse_verdict(r"\text{true}")
    assert pred is True


def test_latex_text_with_spaces():
    pred, _ = parse_verdict(r"\text{ FALSE }")
    assert pred is False


# ---------------------------------------------------------------------------
# Markdown wrapper stripping
# ---------------------------------------------------------------------------

def test_bold_verdict_line():
    pred, _ = parse_verdict("**VERDICT: TRUE**\n\nReasoning")
    assert pred is True


def test_bold_keyword_only():
    pred, _ = parse_verdict("**VERDICT**: FALSE")
    assert pred is False


def test_bold_value_only():
    pred, _ = parse_verdict("VERDICT: **TRUE**")
    assert pred is True


def test_bold_italic_verdict():
    pred, _ = parse_verdict("***VERDICT: FALSE***")
    assert pred is False


def test_backtick_verdict():
    pred, _ = parse_verdict("VERDICT: `TRUE`")
    assert pred is True


def test_underscore_bold_verdict():
    pred, _ = parse_verdict("__VERDICT: TRUE__")
    assert pred is True


# ---------------------------------------------------------------------------
# Leading / trailing line detection (priority 1 — lowest)
# ---------------------------------------------------------------------------

def test_leading_line_bare_true():
    pred, _ = parse_verdict("TRUE\n\nBecause both sides simplify to x^2.")
    assert pred is True


def test_leading_line_bold_false():
    pred, _ = parse_verdict("**FALSE**\n\nThe magma tables differ.")
    assert pred is False


def test_trailing_final_answer_line():
    pred, _ = parse_verdict("Reasoning...\nFinal answer: FALSE")
    assert pred is False


def test_standalone_false_in_middle_is_unparsed():
    # Bare TRUE/FALSE only recognised on first or last non-empty line.
    pred, _ = parse_verdict("Here is my analysis:\n\nFALSE\n\nReasoning...")
    assert pred is None


def test_no_false_positive_in_text():
    pred, _ = parse_verdict("The statement is FALSE because of reasons, but I need more info.")
    assert pred is None


# ---------------------------------------------------------------------------
# Instruction-preamble detection (must be ignored)
# ---------------------------------------------------------------------------

def test_verdict_or_clause_ignored():
    pred, _ = parse_verdict("Reply with VERDICT: TRUE or FALSE")
    assert pred is None


def test_verdict_slash_clause_ignored():
    pred, _ = parse_verdict("Reply with VERDICT: TRUE/FALSE")
    assert pred is None


def test_answer_slash_clause_ignored():
    pred, _ = parse_verdict("ANSWER: TRUE/FALSE")
    assert pred is None


def test_final_answer_slash_clause_ignored():
    pred, _ = parse_verdict("FINAL ANSWER: TRUE/FALSE")
    assert pred is None


def test_result_slash_clause_ignored():
    pred, _ = parse_verdict("RESULT: FALSE/TRUE")
    assert pred is None


def test_instruction_preamble_then_real_verdict():
    response = "Output format:\nVERDICT: TRUE or FALSE\nREASONING:\n...\nVERDICT: FALSE"
    pred, _ = parse_verdict(response)
    assert pred is False


def test_slash_pattern_with_real_answer_after():
    pred, _ = parse_verdict("Format: VERDICT: TRUE/FALSE\n\nVERDICT: FALSE")
    assert pred is False


# ---------------------------------------------------------------------------
# Tie-breaking: priority + last-occurrence
# ---------------------------------------------------------------------------

def test_conflicting_labeled_last_wins():
    pred, _ = parse_verdict("VERDICT: TRUE\nREASONING: draft\nVERDICT: FALSE")
    assert pred is False


def test_boxed_beats_labeled_regardless_of_order():
    pred, _ = parse_verdict("VERDICT: TRUE\nFinal: \\boxed{FALSE}")
    assert pred is False


def test_labeled_beats_leading_line():
    pred, _ = parse_verdict("FALSE\n\nAfter further analysis...\nVERDICT: TRUE")
    assert pred is True


def test_line_conflict_trailing_wins():
    pred, _ = parse_verdict("TRUE\n\nOn reflection, the answer is:\nFALSE")
    assert pred is False


def test_multiple_same_verdicts_treated_as_one():
    pred, _ = parse_verdict("VERDICT: FALSE\nREASONING: draft\nVERDICT: FALSE")
    assert pred is False


# ---------------------------------------------------------------------------
# Edge cases: empty / None / no verdict
# ---------------------------------------------------------------------------

def test_empty_string():
    pred, _ = parse_verdict("")
    assert pred is None


def test_none_input():
    pred, _ = parse_verdict(None)
    assert pred is None


def test_no_verdict():
    pred, _ = parse_verdict("I think the answer is yes")
    assert pred is None


def test_json_only_no_verdict_marker():
    pred, _ = parse_verdict(r'{"verdict": "FALSE", "reason": "nope"}')
    assert pred is None


def test_json_with_verdict_marker_still_parsed():
    response = r'{"verdict": "TRUE"} VERDICT: TRUE'
    pred, _ = parse_verdict(response)
    assert pred is True


# ---------------------------------------------------------------------------
# Test runner
# ---------------------------------------------------------------------------

def _run_all():
    tests = [(n, obj) for n, obj in sorted(globals().items())
             if n.startswith("test_") and callable(obj)]
    passed, failed = 0, []
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except AssertionError as e:
            failed.append((name, "AssertionError", traceback.format_exc(limit=2)))
        except Exception as e:
            failed.append((name, type(e).__name__, traceback.format_exc(limit=2)))
    total = len(tests)
    print(f"\n{passed}/{total} tests passed")
    if failed:
        print(f"\n{len(failed)} FAILURES:")
        for name, kind, tb in failed:
            print(f"\n--- {name} [{kind}] ---")
            print(tb)
        sys.exit(1)
    print("All green.")


if __name__ == "__main__":
    _run_all()
