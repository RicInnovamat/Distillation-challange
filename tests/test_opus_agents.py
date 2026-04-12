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
    # Bash is the only required tool — the orchestrator is a thin wrapper
    # around `scripts/run_opus_benchmark.py`. `Agent` must NOT appear:
    # Claude Code subagents cannot spawn subagents, so listing `Agent` here
    # would falsely advertise a capability the runtime silently strips.
    assert "Bash" in tokens, \
        f"orchestrator missing required tool 'Bash' in tokens={tokens!r}"
    assert "Agent" not in tokens, \
        f"orchestrator must not declare 'Agent' — nested subagent spawn is unsupported; tokens={tokens!r}"


def test_opus_orchestrator_body_references_solver():
    _, body = _parse_frontmatter(ORCH_PATH)
    assert "opus-solver" in body, \
        "orchestrator must reference the opus-solver subagent by name"


def test_opus_orchestrator_body_delegates_to_driver_script():
    _, body = _parse_frontmatter(ORCH_PATH)
    # The wrapper must tell the sonnet runtime to invoke the real driver.
    assert "scripts/run_opus_benchmark.py" in body, \
        "orchestrator body must reference scripts/run_opus_benchmark.py as the driver"


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
# scripts/run_opus_benchmark.py — the real driver
# ---------------------------------------------------------------------------

DRIVER_PATH = PROJECT_ROOT / "scripts" / "run_opus_benchmark.py"


def test_driver_file_exists():
    assert DRIVER_PATH.exists(), f"{DRIVER_PATH} not found"


def test_driver_invokes_claude_cli_with_opus_solver_agent():
    source = DRIVER_PATH.read_text()
    # Must shell out to `claude` with `-p` (non-interactive) and
    # `--agent opus-solver` so each subprocess is a fresh top-level
    # Claude Code session that CAN dispatch opus-solver.
    assert re.search(r'"claude"\s*,\s*\n?\s*"-p"', source, re.MULTILINE), \
        "driver must invoke `claude -p` via subprocess"
    assert '"--agent"' in source and '"opus-solver"' in source, \
        "driver must pass --agent opus-solver to the claude CLI"


def test_driver_imports_parse_verdict_from_eval_harness():
    source = DRIVER_PATH.read_text()
    assert re.search(r'from\s+eval_harness\s+import\s+parse_verdict', source), \
        "driver must import parse_verdict from eval_harness"


def test_driver_documents_all_three_dataset_paths():
    source = DRIVER_PATH.read_text()
    for p in ("hard1.jsonl", "hard2.jsonl", "hard3.jsonl"):
        assert p in source, f"driver missing dataset {p}"


def test_driver_anti_cheat_passes_only_equations():
    source = DRIVER_PATH.read_text()
    # The solver prompt must be built from equation1 and equation2. The
    # `answer` key must NOT be referenced inside the function that builds
    # the solver prompt. Grep the whole source for `answer` occurrences and
    # require every one of them to be outside `call_solver`.
    #
    # Simpler structural check: the call_solver function body must not
    # contain the literal word `answer`. Extract the function and scan.
    m = re.search(r'def call_solver\([^)]*\)[^:]*:(.*?)(?=\ndef |\Z)', source, re.DOTALL)
    assert m, "driver must define a call_solver function"
    body = m.group(1)
    assert "equation1" in body and "equation2" in body, \
        "call_solver must read equation1 and equation2"
    assert "answer" not in body, \
        "call_solver must never reference the `answer` field (anti-cheat)"


def test_driver_output_schema_fields():
    source = DRIVER_PATH.read_text()
    # Every top-level, summary, and per-problem field that gen_pdf.py reads
    # must appear as a quoted dict key somewhere in the driver source.
    for field in (
        "model", "backend", "model_id", "dataset", "prompt_file",
        "generated_at", "summary", "problems",
        "total", "correct", "wrong", "parse_errors", "accuracy",
        "true_as_true", "true_as_false", "false_as_true", "false_as_false",
        "problem_id", "expected", "predicted", "parse_ok", "raw_verdict",
        "reasoning", "content", "latency_s", "input_tokens", "output_tokens",
        "cost_usd",
    ):
        assert f'"{field}"' in source, \
            f"driver source missing JSON schema key {field!r}"


def test_driver_never_retries_on_failure():
    source = DRIVER_PATH.read_text()
    # The benchmark measures raw one-shot performance. The driver must not
    # retry a failed solver call. Check that `call_solver` is invoked
    # exactly once per problem in the main loop — i.e., no retry loop
    # around it (no `while` or `for _ in range(retries)` wrapping it).
    assert not re.search(r'for\s+\w+\s+in\s+range\(\s*\w*retry\w*\s*\)', source, re.IGNORECASE), \
        "driver must not retry failed solver calls"
    assert not re.search(r'while.*retry', source, re.IGNORECASE), \
        "driver must not retry failed solver calls in a while loop"


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
