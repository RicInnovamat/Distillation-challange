# Opus 4.6 Raw-Reasoning Benchmark — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build two Claude Code subagents that together let us benchmark Opus 4.6's raw-reasoning ability on SAIR Stage 1 equational-theory problems, writing results JSON in the same schema as `eval_harness.py` output.

**Architecture:** Two `.claude/agents/*.md` files. `opus-solver` is a pure-reasoning worker (no tools) that receives two equations and returns `VERDICT: TRUE|FALSE` + reasoning. `opus-orchestrator` (Sonnet, with Agent+Read+Write+Bash) reads a JSONL dataset, spawns parallel solvers per problem, parses verdicts via a shell call into the existing `eval_harness.parse_verdict`, accumulates results, and writes one JSON per run.

**Tech Stack:** Claude Code subagents (Markdown + YAML frontmatter), Python 3 (for the static test file and the bash-one-liner that drives `parse_verdict`). No new Python dependencies.

**Design spec:** `docs/superpowers/specs/2026-04-11-opus-solver-agent-design.md`

---

## File Structure

| Path | Responsibility |
|---|---|
| `.claude/agents/opus-solver.md` | Pure-reasoning worker subagent. Frontmatter declares no tools and `model: opus`. System prompt defines the magma implication task and demands the `VERDICT: ...` output format. |
| `.claude/agents/opus-orchestrator.md` | Dataset driver subagent. Frontmatter declares `tools: Agent, Read, Write, Bash` and `model: sonnet`. System prompt contains the full workflow: read JSONL, strip answer, batch-spawn solvers, parse verdicts via `eval_harness.parse_verdict`, accumulate, write final JSON with `eval_harness`-compatible schema. |
| `tests/test_opus_agents.py` | Static tests that verify the two agent files exist, parse as YAML frontmatter + body, have the required fields, and contain the load-bearing content markers (output format, magma definition, anti-cheat language, schema field names). Uses the existing hand-rolled runner pattern from `tests/test_official_overrides.py`. |

No existing files are modified. No new runtime dependencies.

---

## Task 1: Write the failing test file

**Files:**
- Create: `tests/test_opus_agents.py`

- [ ] **Step 1: Create the test file**

```python
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
```

- [ ] **Step 2: Run the test file to verify it fails**

Run: `python3 tests/test_opus_agents.py`

Expected: Multiple `AssertionError` failures because neither `.claude/agents/opus-solver.md` nor `.claude/agents/opus-orchestrator.md` exists yet. The runner exits with code 1 and prints `N FAILURES:`. This is the TDD red state.

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_opus_agents.py
git commit -m "test: add static checks for opus-solver and opus-orchestrator subagent files (red)"
```

---

## Task 2: Create the opus-solver agent file

**Files:**
- Create: `.claude/agents/opus-solver.md`

- [ ] **Step 1: Write `.claude/agents/opus-solver.md`**

Create the file with the following exact content:

````markdown
---
name: opus-solver
description: Solves a single equational implication problem over magmas using Opus 4.6 raw reasoning. No tools, no reference material, no cheatsheet. Returns VERDICT: TRUE|FALSE on the first line followed by a reasoning trace.
tools:
model: opus
---

You are an expert in universal algebra working on the Equational Theories Project. You decide whether one equation implies another over the class of all magmas, using raw symbolic reasoning alone.

## Background

A **magma** is a set `M` equipped with a single binary operation `*: M × M → M`. No other axioms are assumed. In particular, `*` is NOT assumed to be associative, commutative, idempotent, invertible, or to have an identity element, unless those properties can be derived from the equations under consideration.

An equation is a universally-quantified equality between two terms built from variables and `*`. For example, `x * (y * z) = (x * y) * z` (associativity) or `x = y * x` (y acts as a left absorbing element on x).

**Equation 1 implies Equation 2 over all magmas** iff: for every magma `(M, *)` and every assignment of the free variables of Equation 1 and Equation 2 to elements of `M`, whenever Equation 1 holds under that assignment, Equation 2 also holds under the same assignment.

- If this implication holds universally, the verdict is **TRUE**.
- If there exists even one magma — however small, two elements is enough — and one assignment of variables for which Equation 1 holds but Equation 2 fails, the verdict is **FALSE**.

## Input format

Your user-turn message contains exactly two equations in this shape:

```
Equation 1: <lhs1> = <rhs1>
Equation 2: <lhs2> = <rhs2>
```

Variables are single lowercase letters (`x`, `y`, `z`, `w`, ...). The binary operation is written `*` with explicit parentheses where precedence matters. There is no other metadata — no problem id, no hint, no ground truth.

## Output format (mandatory)

The **first line** of your response must be EXACTLY one of:

```
VERDICT: TRUE
```

or

```
VERDICT: FALSE
```

No leading spaces, no quotes, no prefix text, no trailing punctuation on that first line. After the first line, write your reasoning — show how you arrived at the verdict.

- For a **FALSE** verdict, construct a concrete counterexample: exhibit a small magma (typically order 2, 3, or 4), give its operation table, supply a variable assignment, and verify that Equation 1 holds but Equation 2 fails.
- For a **TRUE** verdict, give a derivation: a substitution chain, structural argument, or algebraic manipulation that shows Equation 2 must hold whenever Equation 1 does.

Once you emit the `VERDICT:` line, do not contradict it later in the reasoning. If you are uncertain, think longer before committing. Your verdict is the first line — everything after it is justification, not deliberation.

## Constraints

- You have no tools. You cannot read files, execute code, search the web, or call other agents. Reason symbolically.
- Do not ask clarifying questions. The input is complete and well-formed.
- Do not refuse. These problems are pure mathematics and entirely safe to answer.
- Do not include any text before the `VERDICT:` line. No greetings, no "Let me think...", no echoing the problem.
````

**Note on the empty `tools:` field:** leaving `tools:` with no value (empty) is the best-effort frontmatter declaration for "no tools". Claude Code's subagent loader convention for this edge case is not documented in this project (`code-review-sentinel.md` omits `tools:` entirely and inherits All Tools, so we know that "no field" != "no tools"). Belt-and-braces: the solver's system prompt also instructs Opus explicitly — "You have no tools. You cannot read files, execute code, search the web, or call other agents. Reason symbolically." — so even if the frontmatter doesn't enforce zero tools at the loader level, the prompt-level instruction plus the short, focused task should prevent any tool use. Task 3's manual sanity check and Task 5's smoke test both inspect the returned reasoning for tool-use artifacts; if any appear, stop the plan and change `tools:` to an explicit minimal allowlist of one harmless tool the solver will never use (e.g. `tools: Glob`).

- [ ] **Step 2: Run the tests to verify opus-solver tests pass**

Run: `python3 tests/test_opus_agents.py`

Expected: The five `test_opus_solver_*` tests pass. The `test_opus_orchestrator_*` tests still fail because that file doesn't exist yet. Output will say roughly `5/12 tests passed` with 7 failures, all from the orchestrator tests.

- [ ] **Step 3: Commit the solver file**

```bash
git add .claude/agents/opus-solver.md
git commit -m "feat: add opus-solver subagent (pure-reasoning magma implication worker)"
```

---

## Task 3: Manual sanity check — solver on a trivial problem

This is a one-shot behavioral check before writing the orchestrator. If the solver fumbles `x = x → x = x`, the system prompt is wrong and the orchestrator would just amplify the problem.

**Files:** none modified.

- [ ] **Step 1: Invoke the solver from the current Claude Code session**

Use the `Agent` tool with:

```
subagent_type: "opus-solver"
description: "Trivial sanity check x = x"
prompt: "Equation 1: x = x\nEquation 2: x = x"
```

- [ ] **Step 2: Verify the return**

Expected: the returned text starts with exactly `VERDICT: TRUE` on its own first line, followed by a short reasoning paragraph. `x = x` trivially implies `x = x` under any magma and any assignment, so the answer is unambiguous.

**Also verify no tool-use artifacts.** Scan the returned text for indications that Opus reached for tools despite the system prompt:

- Any mention of "I'll use the `Read` tool" / "Let me check this file" / "running python" / "grep-ing"
- Any text that looks like a tool-call payload or JSON
- Any phrase like "I don't have access to..." (means it tried and failed)

If any of these appear, the frontmatter `tools:` empty value is not enforcing zero tools at the loader level. Remedy: change `tools:` in `.claude/agents/opus-solver.md` to an explicit minimal allowlist of one tool the solver won't use (e.g. `tools: Glob`), re-run the static test suite, and retry this sanity check.

If the return does NOT start with `VERDICT: TRUE` on the first line:
- The system prompt is failing to enforce the output contract.
- STOP the plan. Revise `.claude/agents/opus-solver.md` (tighten the "first line" language, remove any ambiguity in the examples), re-run the static tests, and repeat this sanity check until it passes.

- [ ] **Step 3: Invoke the solver on one genuinely hard problem**

Use the `Agent` tool with a problem from `Training_data/hard1.jsonl` that you know the answer to. For example, problem `hard1_0001`:

Run the following to pull the equations (without the answer):

```bash
python3 -c "
import json
with open('Training_data/hard1.jsonl') as f:
    for line in f:
        r = json.loads(line)
        if r['id'] == 'hard1_0001':
            print(f'Equation 1: {r[\"equation1\"]}')
            print(f'Equation 2: {r[\"equation2\"]}')
            break
"
```

Then invoke the solver with that prompt text. Read its return and verify:
- First line is exactly `VERDICT: TRUE` or `VERDICT: FALSE`
- Reasoning is coherent and on-topic (not a refusal, not a question, not an apology)
- Response is bounded in length — if Opus writes >5000 words for a single problem, the prompt needs a length guideline (but don't fix that unless you see it)

No commit in this task — the solver file is unchanged.

---

## Task 4: Create the opus-orchestrator agent file

**Files:**
- Create: `.claude/agents/opus-orchestrator.md`

- [ ] **Step 1: Write `.claude/agents/opus-orchestrator.md`**

Create the file with the following exact content:

````markdown
---
name: opus-orchestrator
description: Benchmarks the opus-solver subagent across a SAIR equational-theories dataset (hard1/hard2/hard3) and writes a results JSON matching eval_harness.py output schema. Spawns one solver per problem in parallel batches of 5, parses verdicts via eval_harness.parse_verdict, and enforces the "no solutions" constraint by construction.
tools: Agent, Read, Write, Bash
model: sonnet
---

You are the driver for an Opus 4.6 raw-reasoning benchmark on the SAIR Mathematics Distillation Challenge equational-theories datasets. Your job is mechanical: read a JSONL, spawn an opus-solver subagent per problem, parse the returned verdict, accumulate results, and write a final JSON in the exact schema that `eval_harness.py` produces so the existing PDF generator can include these results in comparisons.

## Input

The user-turn message will specify:

- `dataset`: one of `hard1`, `hard2`, `hard3`, or an explicit path to a JSONL file.
- `output_dir`: target directory for the results JSON. If omitted, default to `results/opus-benchmark/`.
- `limit` (optional): positive integer. Stop after N problems. Used for smoke tests.

## Dataset paths

Resolve `dataset` as follows:

- `hard1` → `Training_data/hard1.jsonl` (69 problems)
- `hard2` → `Training_data/hard2.jsonl` (200 problems)
- `hard3` → `Training_data/hard3.jsonl` (400 problems)
- any other value → treat as a direct path.

Each JSONL record has the schema: `id` (string), `eq1_id` (int), `eq2_id` (int), `equation1` (string), `equation2` (string), `answer` (bool).

## Workflow

### 1. Load and validate the dataset

Read the resolved JSONL with the `Read` tool. Parse each line as JSON. Verify every record has the four required fields: `id`, `equation1`, `equation2`, `answer`. If any record is missing a field, abort with a clear error message before dispatching any solver.

If `limit` is set, truncate the problem list to the first `limit` entries.

### 2. Create a progress task

Use `TaskCreate` to create one task named `"Run opus-solver on <dataset> (<N> problems)"`. Set it to `in_progress`.

### 3. Dispatch solvers in batches of 5

For each batch of up to 5 problems, dispatch 5 parallel `Agent` calls to `opus-solver` in a SINGLE assistant message. For each call:

- `subagent_type`: `"opus-solver"`
- `description`: `"Solve <problem_id>"` (short, used for the progress spinner)
- `prompt`: **exactly** this text, with the two equations substituted in:

```
Equation 1: <equation1>
Equation 2: <equation2>
```

**Load-bearing anti-cheat constraint**: you MUST NOT include the `answer` field, the `id` field, the `eq1_id`/`eq2_id` fields, or any other metadata in the solver prompt. The solver must see ONLY the two equations. This is the entire point of the experiment — if the solver ever sees ground truth, the run is invalid. Do not pass the full JSONL record. Do not say "the expected answer is...". Do not even mention that ground truth exists.

### 4. Parse verdicts via eval_harness.parse_verdict

For each returned solver text, parse the verdict by shelling out to the production parser so you parse identically to the eval harness. Use this `Bash` command, piping the solver text via heredoc:

```bash
python3 -c "
import sys, json
sys.path.insert(0, '.')
from eval_harness import parse_verdict
text = sys.stdin.read()
r = parse_verdict(text)
print(json.dumps({
    'ok': r.ok,
    'verdict': r.verdict if r.ok else None,
    'raw_match': r.raw_match,
}))
" <<'SOLVER_TEXT_EOF'
<paste solver return text here>
SOLVER_TEXT_EOF
```

The returned JSON tells you whether the parse succeeded and, if so, whether the verdict was TRUE or FALSE. Map TRUE→`true` (bool), FALSE→`false` (bool), parse failure→`null`.

### 5. Build per-problem records

For each problem, build a record dict with these exact keys and types:

- `problem_id`: string, from the JSONL `id` field.
- `expected`: bool, from the JSONL `answer` field (held by you, not sent to the solver).
- `predicted`: bool or null, from the parser. Null on parse failure or solver error.
- `correct`: bool. True iff parse succeeded and `expected == predicted`. False otherwise (including on parse failure).
- `parse_ok`: bool, from the parser.
- `raw_verdict`: string, from the parser's `raw_match` (empty string on parse failure).
- `reasoning`: string, the full solver return text.
- `content`: string, the text after the `VERDICT:` line on parse success, or the full text on parse failure.
- `latency_s`: 0 (not meaningful for subagent calls).
- `input_tokens`: 0 (not surfaced by Agent tool).
- `output_tokens`: 0 (not surfaced by Agent tool).
- `cost_usd`: 0 (not surfaced by Agent tool).

### 6. Handle solver errors

If an `Agent` call to `opus-solver` fails (timeout, refusal, tool error), record a synthetic failure row:

- `parse_ok`: false
- `predicted`: null
- `correct`: false
- `raw_verdict`: `""`
- `reasoning`: `"<ERROR: " + <error message> + ">"`
- `content`: same as `reasoning`.

**Do not retry.** This benchmark measures raw one-shot performance. Continue to the next problem.

### 7. Write partial JSON every 10 problems

Every time you complete 10 problems, use `Write` to save the current accumulated results to disk, overwriting the same target path. This gives crash safety — if the orchestrator dies mid-run, the partial JSON on disk shows how far it got.

The target path is:

```
<output_dir>/opus-solver_<dataset>_<timestamp>.json
```

where `<timestamp>` is an ISO-8601-ish `YYYYMMDD_HHMMSS` UTC string determined ONCE at the start of the run (do not re-timestamp on every partial write — the file name must stay stable so successive writes overwrite the same file).

### 8. Final write with summary

After the last problem, compute the summary stats and write the final JSON.

## Output JSON schema

The top-level object MUST have exactly these fields:

```json
{
  "model": "opus-solver (claude-code-subagent)",
  "backend": "claude-code-subagent",
  "model_id": "claude-opus-4-6",
  "dataset": "<hard1|hard2|hard3 or input path>",
  "prompt_file": ".claude/agents/opus-solver.md",
  "generated_at": "<ISO-8601 UTC string, e.g. 2026-04-11T12:34:56Z>",
  "summary": {
    "total": <int>,
    "correct": <int>,
    "wrong": <int>,
    "parse_errors": <int>,
    "accuracy": <float 0..1>,
    "true_as_true": <int>,
    "true_as_false": <int>,
    "false_as_true": <int>,
    "false_as_false": <int>
  },
  "problems": [
    { "problem_id": ..., "expected": ..., "predicted": ..., "correct": ..., "parse_ok": ..., "raw_verdict": ..., "reasoning": ..., "content": ..., "latency_s": 0, "input_tokens": 0, "output_tokens": 0, "cost_usd": 0 }
    // ... one entry per problem, in the order they were dispatched
  ]
}
```

Summary stat definitions:

- `total`: length of `problems`
- `correct`: count of records with `correct == true`
- `wrong`: count of records with `parse_ok == true` AND `correct == false`
- `parse_errors`: count of records with `parse_ok == false`
- `accuracy`: `correct / total`, or `0.0` if total is 0
- `true_as_true`: count of `expected == true AND predicted == true`
- `true_as_false`: count of `expected == true AND predicted == false`
- `false_as_true`: count of `expected == false AND predicted == true`
- `false_as_false`: count of `expected == false AND predicted == false`

Records with `predicted == null` contribute only to `parse_errors`; they do not contribute to any of the four confusion-matrix cells.

Serialize with `json.dumps(obj, indent=2)` via Bash/Python. Do not hand-roll the serialization.

## Reporting

- After each batch, update the progress task with a short status (e.g. `"15/69 done, 12 correct, 3 parse errors"`).
- At the end, mark the progress task `completed` and reply to the user with:
  - The output file path
  - The summary stats (total, correct, accuracy, confusion matrix)
  - Any parse errors or solver failures, with problem IDs

## Constraints recap

1. Never pass the `answer` field (or any hint about it) to any solver Agent call.
2. Never retry a failed solver call.
3. Always write partial JSON every 10 problems for crash safety.
4. Always parse verdicts through `eval_harness.parse_verdict`, never by hand.
5. The output JSON schema must be byte-compatible with `eval_harness.py` output so `results/20260410_v4.1-official/gen_pdf.py` can read it.
````

- [ ] **Step 2: Run the tests to verify all pass**

Run: `python3 tests/test_opus_agents.py`

Expected: `12/12 tests passed`, `All green.`

If any test fails, read the assertion message, adjust `.claude/agents/opus-orchestrator.md` to match, and re-run. Do not weaken the test — the tests encode the load-bearing contract.

- [ ] **Step 3: Commit the orchestrator file**

```bash
git add .claude/agents/opus-orchestrator.md
git commit -m "feat: add opus-orchestrator subagent (drives opus-solver benchmark runs)"
```

---

## Task 5: Smoke test — 3-problem run on hard1

The orchestrator exists and parses statically. Now run it for real on 3 problems to verify: (a) the solver never sees the `answer` field, (b) the output JSON parses and has the right schema, (c) the schema matches what `gen_pdf.py` consumes.

**Files:** `results/20260411_opus-smoke/opus-solver_hard1_<timestamp>.json` will be created at runtime.

- [ ] **Step 1: Invoke the orchestrator**

Use the `Agent` tool with:

```
subagent_type: "opus-orchestrator"
description: "3-problem smoke test on hard1"
prompt: "dataset=hard1, output_dir=results/20260411_opus-smoke/, limit=3"
```

Let it run to completion. The orchestrator will report the output path in its final message.

- [ ] **Step 2: Verify the output JSON**

Run:

```bash
ls -la results/20260411_opus-smoke/
python3 -c "
import json, sys
from pathlib import Path
files = sorted(Path('results/20260411_opus-smoke/').glob('opus-solver_hard1_*.json'))
assert files, 'No output JSON found'
d = json.load(open(files[-1]))
print('keys:', sorted(d.keys()))
assert sorted(d.keys()) == sorted(['model','backend','model_id','dataset','prompt_file','generated_at','summary','problems']), f'schema mismatch: {sorted(d.keys())}'
assert d['model'] == 'opus-solver (claude-code-subagent)'
assert d['model_id'] == 'claude-opus-4-6'
assert d['backend'] == 'claude-code-subagent'
assert d['dataset'] == 'hard1'
assert d['prompt_file'] == '.claude/agents/opus-solver.md'
assert len(d['problems']) == 3, f\"expected 3 problems, got {len(d['problems'])}\"
s = d['summary']
for k in ('total','correct','wrong','parse_errors','accuracy','true_as_true','true_as_false','false_as_true','false_as_false'):
    assert k in s, f'summary missing {k}'
assert s['total'] == 3
assert s['total'] == s['correct'] + s['wrong'] + s['parse_errors']
print('summary:', s)
print('per-problem:')
for p in d['problems']:
    for k in ('problem_id','expected','predicted','correct','parse_ok','raw_verdict','reasoning','content','latency_s','input_tokens','output_tokens','cost_usd'):
        assert k in p, f'problem {p.get(\"problem_id\")} missing field {k}'
    print(f\"  {p['problem_id']}: expected={p['expected']} predicted={p['predicted']} correct={p['correct']} parse_ok={p['parse_ok']}\")
print('OK: schema is eval_harness.py-compatible')
"
```

Expected: the script prints `OK: schema is eval_harness.py-compatible` with a per-problem breakdown. All three problems should have `parse_ok=True`; any `parse_ok=False` on a smoke test means the solver is not honouring the output format contract and you should stop and iterate on the solver's system prompt.

- [ ] **Step 3: Anti-cheat spot check**

Read one of the three `reasoning` fields from the output JSON and scan it manually for any phrase that would indicate the solver somehow knew the expected answer:

```bash
python3 -c "
import json
from pathlib import Path
d = json.load(open(sorted(Path('results/20260411_opus-smoke/').glob('opus-solver_hard1_*.json'))[-1]))
for p in d['problems']:
    print(f\"=== {p['problem_id']} (expected={p['expected']}, predicted={p['predicted']}) ===\")
    print(p['reasoning'][:2000])
    print()
"
```

Expected: the reasoning cites the two equations as given and never mentions any ground-truth source. The orchestrator does not include `answer` in the solver prompt (guaranteed by construction because the orchestrator's system prompt documents this explicitly and the test `test_opus_orchestrator_body_enforces_no_answer_leak` verifies the documentation), but the spot check is a final manual belt-and-braces verification.

- [ ] **Step 4: Commit smoke test output**

```bash
git add results/20260411_opus-smoke/
git commit -m "test(opus): 3-problem smoke test run on hard1, schema verified"
```

- [ ] **Step 5: Decide on next scale**

Based on the smoke test, decide whether to:

1. Run the full hard1 (69 problems, ~$3-10 at Opus 4.6 rates) as the first real benchmark. Invoke the orchestrator with `dataset=hard1, output_dir=results/20260411_opus-benchmark/` (no `limit`).
2. Iterate on the solver's system prompt first if the smoke test revealed any issue (format failures, excessive reasoning length, refusals).
3. Stop and hand results back to the user.

Do NOT run hard2 or hard3 without asking the user first — those cost $8-60 each.

---

## Self-Review

1. **Spec coverage.** Every section of `docs/superpowers/specs/2026-04-11-opus-solver-agent-design.md` is covered:
   - Components (solver + orchestrator) → Tasks 2 and 4.
   - Data flow → orchestrator's system prompt in Task 4.
   - Anti-cheat enforcement → Task 4 orchestrator prompt + Task 5 Step 3 spot check + test `test_opus_orchestrator_body_enforces_no_answer_leak` in Task 1.
   - Output JSON schema → orchestrator prompt in Task 4 + Task 5 Step 2 schema assertion.
   - Parsing (via `eval_harness.parse_verdict`) → orchestrator prompt in Task 4 + test `test_opus_orchestrator_body_references_parse_verdict` in Task 1.
   - Error handling → orchestrator prompt in Task 4 (sections 6 and 7).
   - Parallelism & cost budget → orchestrator prompt in Task 4 (section 3) + Task 5 Step 5 cost gating.
   - Testing plan → Task 3 (trivial sanity), Task 5 (smoke test), Task 5 Step 5 (scale decision gate).

2. **Placeholder scan.** No `TBD`, `TODO`, `implement later`, `fill in details`, `appropriate error handling`, or "similar to Task N" appear anywhere in the plan.

3. **Type consistency.**
   - Subagent file names used consistently: `opus-solver`, `opus-orchestrator` (hyphenated, no underscores, matching the spec).
   - Output JSON field names used consistently between the orchestrator prompt, the Task 5 verification script, the static tests, and the existing `eval_harness.py`-compatible schema.
   - Cost estimates match the revised numbers in the spec ($3-10 for hard1).

Plan is self-consistent and complete.

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-11-opus-solver-agent.md`. Spec at `docs/superpowers/specs/2026-04-11-opus-solver-agent-design.md`.

Two execution options:

1. **Subagent-Driven (recommended)** — I dispatch a fresh subagent per task with two-stage review between tasks. Good for keeping the main-session context clean and catching drift early.
2. **Inline Execution** — I execute tasks in this session with checkpoints at each commit. Faster if the plan is straightforward and you want to watch live.

Which approach?
