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
    """
    text = path.read_text()
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    assert m, f"No `--- ... ---` frontmatter block in {path}"
    front, body = m.group(1), m.group(2)
    fields: dict[str, str] = {}
    for line in front.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            fields[k.strip()] = v.strip()
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
    # tools must be empty (pure-reasoning, no tools, no file access).
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
    body_l = body.lower()
    assert "do not contradict" in body_l or "no backtrack" in body_l or "not change" in body_l, \
        "solver body must forbid backtracking after emitting VERDICT"


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
    tools = fields.get("tools", "")
    for required in ("Agent", "Read", "Write", "Bash"):
        assert required in tools, \
            f"orchestrator missing required tool {required!r} in {tools!r}"


def test_opus_orchestrator_body_references_solver():
    _, body = _parse_frontmatter(ORCH_PATH)
    assert "opus-solver" in body, \
        "orchestrator must reference the opus-solver subagent by name"


def test_opus_orchestrator_body_enforces_no_answer_leak():
    _, body = _parse_frontmatter(ORCH_PATH)
    body_l = body.lower()
    # Must explicitly document that the `answer` field is withheld from the solver.
    assert "answer" in body_l
    assert ("never" in body_l or "do not" in body_l or "must not" in body_l), \
        "orchestrator body must use negation around the answer field"


def test_opus_orchestrator_body_output_schema_fields():
    _, body = _parse_frontmatter(ORCH_PATH)
    # The orchestrator must document every field that gen_pdf.py reads.
    for field in (
        "model", "backend", "model_id", "dataset", "prompt_file",
        "generated_at", "summary", "problems",
        "total", "correct", "wrong", "parse_errors", "accuracy",
        "true_as_true", "true_as_false", "false_as_true", "false_as_false",
    ):
        assert field in body, \
            f"orchestrator body missing schema field {field!r}"


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
