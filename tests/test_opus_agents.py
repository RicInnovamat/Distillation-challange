"""Static tests for the opus-solver and opus-orchestrator Claude Code subagents.

These are structural checks: the files must exist, the YAML frontmatter must
declare the expected fields, and the body must contain the load-bearing
content markers (output format, magma definition, anti-cheat language,
eval_harness.py-compatible schema fields). Runtime behaviour is verified
manually via the smoke-test task at the end of the plan.
"""
import os
import re
import sys
import traceback
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
AGENTS_DIR = PROJECT_ROOT / ".claude" / "agents"


def _parse_frontmatter(path: Path) -> tuple[dict, str]:
    """Parse `--- ... ---`-delimited YAML frontmatter. Returns (fields, body).

    Only supports the flat `key: value` subset used by Claude Code agent files.
    Strips matching surrounding quotes from values so `name: "foo"` and
    `name: foo` parse identically (the existing `code-review-sentinel.md`
    uses the quoted form, so parsers that don't strip would reject it).
    """
    text = path.read_text()
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", text, re.DOTALL)
    assert m, f"No `--- ... ---` frontmatter block in {path}"
    front, body = m.group(1), m.group(2)
    fields: dict[str, str] = {}
    for line in front.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            v = v.strip()
            if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
                v = v[1:-1]
            fields[k.strip()] = v
    return fields, body


# ---------------------------------------------------------------------------
# opus-solver
# ---------------------------------------------------------------------------

SOLVER_PATH = AGENTS_DIR / "opus-solver.md"


def test_opus_solver_file_exists():
    assert SOLVER_PATH.exists(), f"{SOLVER_PATH} not found"


def test_opus_solver_frontmatter_fields():
    fields, _ = _parse_frontmatter(SOLVER_PATH)
    assert fields.get("name") == "opus-solver"
    assert fields.get("model") == "opus"
    # The flat parser would silently accept a YAML-list tools declaration
    # (`tools:` with indented `- Tool` lines on subsequent rows) — reject
    # that explicitly on the raw file text so "no tools" actually means
    # "no tools", not "we smuggled tools in via a list".
    raw = SOLVER_PATH.read_text()
    assert not re.search(r"^tools:\s*\n\s+-\s*\w", raw, re.MULTILINE), \
        "solver must not declare tools as a YAML list — frontmatter tools: must be empty"
    # Inline tools value must also be empty.
    tools = fields.get("tools", "").strip()
    assert tools in ("", "[]", "none"), f"solver must have no tools, got {tools!r}"


def test_opus_solver_body_demands_verdict_format():
    _, body = _parse_frontmatter(SOLVER_PATH)
    # The first-line VERDICT format is the load-bearing output contract.
    assert "VERDICT: TRUE" in body
    assert "VERDICT: FALSE" in body
    assert "first line" in body.lower(), \
        "solver body must say VERDICT goes on the first line"


def test_opus_solver_body_defines_magma():
    _, body = _parse_frontmatter(SOLVER_PATH)
    body_l = body.lower()
    assert "magma" in body_l
    assert "binary operation" in body_l, \
        "solver body must define the magma's binary operation"


def test_opus_solver_body_forbids_backtracking():
    _, body = _parse_frontmatter(SOLVER_PATH)
    # Load-bearing: once VERDICT is emitted, no contradicting reasoning after.
    # Check for any paraphrase that maps to "do not backtrack after VERDICT".
    body_l = body.lower()
    markers = (
        "do not contradict",
        "do not revise",
        "do not overturn",
        "no backtrack",
        "not contradict",
    )
    assert any(m in body_l for m in markers), \
        f"solver body must forbid backtracking after emitting VERDICT (looked for any of: {markers})"


# ---------------------------------------------------------------------------
# opus-orchestrator
# ---------------------------------------------------------------------------

ORCH_PATH = AGENTS_DIR / "opus-orchestrator.md"


def test_opus_orchestrator_file_exists():
    assert ORCH_PATH.exists(), f"{ORCH_PATH} not found"


def test_opus_orchestrator_frontmatter_fields():
    fields, _ = _parse_frontmatter(ORCH_PATH)
    assert fields.get("name") == "opus-orchestrator"
    model = fields.get("model", "")
    assert model in ("sonnet", "opus", "haiku"), \
        f"orchestrator model must be sonnet/opus/haiku, got {model!r}"
    # Tokenize the tools field so substring hits like "BashCommand" don't
    # falsely satisfy the "Bash" requirement.
    tools_str = fields.get("tools", "")
    tokens = [t.strip(" \t[]'\"") for t in tools_str.split(",")]
    for required in ("Agent", "Read", "Write", "Bash"):
        assert required in tokens, \
            f"orchestrator missing required tool {required!r} in tokens={tokens!r}"


def test_opus_orchestrator_body_references_solver():
    _, body = _parse_frontmatter(ORCH_PATH)
    assert "opus-solver" in body, \
        "orchestrator must reference the opus-solver subagent by name"


def test_opus_orchestrator_body_enforces_no_answer_leak():
    _, body = _parse_frontmatter(ORCH_PATH)
    # Must explicitly name the `answer` field as the cheat-risk token,
    # not just mention the word "answer" in prose.
    assert re.search(r'(?:"answer"|`answer`|answer field)', body, re.IGNORECASE), \
        "orchestrator body must name the 'answer' field as the cheat risk (quoted or backticked)"
    # Must pair a negation verb with the word "answer" within 120 chars so
    # vacuous prose like "the orchestrator answers questions" doesn't satisfy it.
    assert re.search(
        r'(?:never|do not|don\'t|must not|withhold|strip|exclude|remove)[^.\n]{0,120}answer',
        body, re.IGNORECASE,
    ), "orchestrator body must negate leaking the answer field to the solver"


def test_opus_orchestrator_body_output_schema_fields():
    _, body = _parse_frontmatter(ORCH_PATH)
    # Every field `gen_pdf.py` reads must appear as a JSON key inside a
    # fenced code block, not just as a bare word in prose. Extract all
    # fenced blocks and concatenate them, then require each field to
    # appear in the shape `"field":`.
    code_blocks = re.findall(r"```.*?\n(.*?)```", body, re.DOTALL)
    combined = "\n".join(code_blocks) if code_blocks else ""
    assert combined, \
        "orchestrator body must include at least one fenced code block documenting the JSON schema"
    for field in (
        "model", "backend", "model_id", "dataset", "prompt_file",
        "generated_at", "summary", "problems",
        "total", "correct", "wrong", "parse_errors", "accuracy",
        "true_as_true", "true_as_false", "false_as_true", "false_as_false",
    ):
        pattern = rf'"{re.escape(field)}"\s*:'
        assert re.search(pattern, combined), \
            f"orchestrator body must document {field!r} as a JSON schema key inside a fenced code block"


def test_opus_orchestrator_body_references_parse_verdict():
    _, body = _parse_frontmatter(ORCH_PATH)
    # The orchestrator must call back into eval_harness.parse_verdict
    # so we parse identically to the eval harness.
    assert "parse_verdict" in body
    assert "eval_harness" in body


def test_opus_orchestrator_body_documents_dataset_paths():
    _, body = _parse_frontmatter(ORCH_PATH)
    for p in ("Training_data/hard1.jsonl", "Training_data/hard2.jsonl", "Training_data/hard3.jsonl"):
        assert p in body, f"orchestrator body missing dataset path {p}"


# ---------------------------------------------------------------------------
# Runner (mirrors tests/test_official_overrides.py)
# ---------------------------------------------------------------------------

def _run_all():
    tests = [(n, obj) for n, obj in sorted(globals().items())
             if n.startswith("test_") and callable(obj)]
    passed, failed = 0, []
    for name, fn in tests:
        try:
            fn()
            passed += 1
        except AssertionError:
            failed.append((name, "AssertionError", traceback.format_exc(limit=3)))
        except Exception as e:
            failed.append((name, type(e).__name__, traceback.format_exc(limit=3)))
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
