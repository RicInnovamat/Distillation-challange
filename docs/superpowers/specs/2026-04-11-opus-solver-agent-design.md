# Opus 4.6 raw-reasoning benchmark — design spec

**Date:** 2026-04-11
**Status:** Approved, ready for implementation plan.
**Author:** Andrea (design dialogue with Claude Code)

## Goal

Measure how well Claude Opus 4.6 can solve SAIR Stage 1 equational-theory problems from first principles, with no cheatsheet, no tools, and no access to the ground-truth `answer` field. Produce a results JSON in the same schema as `eval_harness.py` output so the existing `results/20260410_v4.1-official/gen_pdf.py` can include opus in future comparisons.

## Non-goals

- Not a replacement for `eval_harness.py`. This is a parallel experiment with a different execution model (Claude Code subagents instead of OpenRouter HTTP calls).
- Not a production judging harness. No auto-resume on crash, no PDF update, no automation beyond one-shot runs.
- No tool use. Pure reasoning only. Do not add Bash/Read/WebFetch to the solver even if it would help accuracy — the test is about raw Opus 4.6.

## Components

Two files, both Claude Code subagent definitions in `.claude/agents/`.

### `.claude/agents/opus-solver.md`

- **Frontmatter:**
  - `name: opus-solver`
  - `description: Solves a single equational implication problem over magmas using Opus 4.6 raw reasoning. No tools, no reference material.`
  - `tools:` *(empty)*
  - `model: opus`
- **System prompt** (to be drafted as part of the implementation plan):
  - Defines the task: given two equations over magmas, decide whether equation 1 implies equation 2 over ALL magmas.
  - Defines "magma": a set with a single binary operation `*`, no axioms (associativity, commutativity, identity, etc. are NOT assumed unless stated).
  - Defines "implies over all magmas": for every magma M and every assignment of variables, if equation 1 holds, then equation 2 must also hold.
  - Explains the input format: two equations will be passed in the user turn.
  - Demands the output format: first line must be exactly `VERDICT: TRUE` or `VERDICT: FALSE`. Everything after the first line is the reasoning trace.
  - Encourages showing work before committing to a verdict, but forbids backtracking once `VERDICT:` is emitted.
  - Explicitly forbids searching for external sources, since there are no tools to do so anyway — this is defensive documentation.

### `.claude/agents/opus-orchestrator.md`

- **Frontmatter:**
  - `name: opus-orchestrator`
  - `description: Benchmarks opus-solver across a problem dataset and writes a results JSON matching eval_harness.py schema.`
  - `tools: Agent, Read, Write, Bash`
  - `model: sonnet` *(control logic is mechanical; Sonnet is sufficient and saves tokens)*
- **System prompt** (to be drafted):
  - Input: user prompt specifies `dataset=hard1|hard2|hard3` (or a direct path), optional `output_dir`, and optional `limit` (stop after N problems — needed for smoke tests).
  - Step 1: Read the JSONL. Validate schema (must contain `id`, `equation1`, `equation2`, `answer`). Fail fast on bad data.
  - Step 2: Build payload list of `{problem_id, equation1, equation2}` — **never include `answer`**. This is the anti-cheat enforcement.
  - Step 3: TaskCreate for overall progress. For large datasets, one task per batch of 10 is enough.
  - Step 4: For each batch of 5 problems, dispatch 5 parallel `Agent` calls to `opus-solver` in a single message.
  - Step 5: Parse each returned text with a verdict regex (see §Parsing). Record `problem_id`, `expected` (from ground truth the orchestrator held back), `predicted`, `correct`, `parse_ok`, `raw_verdict`, `reasoning` (the full solver return), `content` (reasoning body after the verdict line).
  - Step 6: Every 10 completed problems, Write the current accumulated JSON to disk (for crash safety). Overwrite the same file.
  - Step 7: After all problems done, compute summary stats (total / correct / wrong / parse_errors / accuracy / true_as_true / true_as_false / false_as_true / false_as_false) and write the final JSON.

## Data flow

```
main Claude Code session
    │
    │ Agent(subagent_type="opus-orchestrator",
    │       prompt="run on hard1 → results/opus-benchmark/")
    ▼
opus-orchestrator (sonnet, has Agent+Read+Write+Bash)
    │
    │ 1. Read Training_data/hard1.jsonl  (full records, including `answer`)
    │ 2. Build payloads: {problem_id, equation1, equation2} ONLY
    │ 3. TaskCreate for progress
    │ 4. For each batch of 5 problems:
    │       dispatch 5 parallel Agent(subagent_type="opus-solver",
    │                                  prompt="Equation 1: X\nEquation 2: Y")
    ▼
opus-solver × 5   (opus, no tools)
    │
    │ Pure-reasoning loop, returns final message:
    │ "VERDICT: FALSE\n\n<reasoning>"
    ▼
opus-orchestrator
    │
    │ 5. Parse VERDICT regex from each return
    │ 6. Compare to ground-truth `answer` (orchestrator has it, solver didn't)
    │ 7. Accumulate problem record
    │ 8. Every 10 problems, Write partial JSON (overwrite)
    │ 9. At the end, write final JSON with summary stats
    ▼
results/<output_dir>/opus-solver_<dataset>_<timestamp>.json
```

## Anti-cheat enforcement

**By construction, not by prompt trust.** The solver subagent:
- has an empty `tools:` list in its frontmatter → cannot `Read` files
- has no network tool → cannot access `teorth.github.io` or any implication graph
- receives its input as a plain user-turn message containing only `equation1` and `equation2`

The orchestrator reads the full JSONL record but slices out only the two equation fields before constructing the solver prompt. The `answer` field never enters any solver's context window. No trust in the solver's system prompt is required.

## Output JSON schema

Identical to `eval_harness.py` output so `gen_pdf.py` works without modification. Top-level fields:

- `model`: `"opus-solver (claude-code-subagent)"`
- `backend`: `"claude-code-subagent"`
- `model_id`: `"claude-opus-4-6"`
- `dataset`: e.g. `"hard1"`
- `prompt_file`: `".claude/agents/opus-solver.md"` (marker for the tabula-rasa config)
- `generated_at`: ISO-8601 UTC timestamp
- `summary`: `{total, correct, wrong, parse_errors, accuracy, true_as_true, true_as_false, false_as_true, false_as_false}`
- `problems[]`:
  - `problem_id`: string
  - `expected`: bool (from the JSONL `answer` field, held by the orchestrator)
  - `predicted`: bool or null (from parsed VERDICT)
  - `correct`: bool
  - `parse_ok`: bool
  - `raw_verdict`: string (the matched group, e.g. `"labeled:FALSE"` or `""` on parse fail)
  - `reasoning`: string (the full text the solver returned)
  - `content`: string (the reasoning body after the `VERDICT:` line; same string on parse fail)

Fields that don't apply to a subagent-driven run — `latency_s`, `input_tokens`, `output_tokens`, `cost_usd` — are set to `null` or `0`. `gen_pdf.py` tolerates missing values.

## Parsing

Reuse the logic from `eval_harness.py` (priority-based extractor: boxed > labeled > first/last bare-line). Two implementation options for the orchestrator:

1. Call `Bash python3 -c "from eval_harness import parse_verdict; ..."` per result. Simplest, reuses production parser exactly.
2. Port the regex table inline into the orchestrator's system prompt and have Sonnet parse via Python snippets.

Implementation plan will pick (1) for fidelity.

## Error handling

- **Parse failure** (solver returns text with no recognizable `VERDICT:`): record `parse_ok=False, predicted=None, correct=False, raw_verdict=""`, store full return in `reasoning`. Do NOT retry — the test is about raw one-shot reasoning.
- **Solver error/timeout/refusal**: orchestrator catches the Agent tool failure, records a synthetic failure row (`parse_ok=False, reasoning="<ERROR: ...>"`, predicted=None), continues to the next problem.
- **Orchestrator crash mid-run**: the partial JSON written every 10 problems shows progress. No auto-resume in v1 — re-run the whole dataset manually.
- **Bad dataset file** (missing fields, malformed JSON): orchestrator fails fast with a clear error message before dispatching any solver.

## Parallelism & cost budget

- **Batch size:** 5 solver invocations per orchestrator message. Claude Code supports dispatching multiple `Agent` calls in a single message.
- **Per-problem cost (Opus 4.6 at $15/Mtok in, $75/Mtok out):** ~200 input tokens (system prompt + 2 equations) + ~500-2000 output tokens (reasoning trace). That's $0.003 input + $0.038-0.150 output = **~$0.04-0.15 per problem**.
- **Hard1 (69 problems):** 14 batches, **~$3-10**.
- **Hard2 (200):** 40 batches, **~$8-30**.
- **Hard3 (400):** 80 batches, **~$16-60**.
- **Full sweep (669):** **~$27-100**.

Strongly recommend a 3-problem smoke test (`limit=3`) before any full dataset run, then hard1 before hard2/hard3.

## Testing plan

1. **3-problem smoke test:** dry-run orchestrator on the first 3 entries of hard1. Verify:
   - The solver never receives the `answer` field (inspect the Agent tool prompts in the orchestrator's trace).
   - Output JSON has all required fields and matches `eval_harness.py` schema.
   - Accuracy computation is correct against a manual count.
2. **Trivial-case sanity:** invoke `opus-solver` directly with `x = x → x = x`. Opus should confidently return `VERDICT: TRUE`. If it fumbles this, the system prompt needs work before any full sweep.
3. **Full hard1 run** once both of the above pass.

## Out of scope for v1

- **No auto-resume.** If the orchestrator dies mid-run, you re-run the whole dataset. The partial JSON is inspection-only, not a resume source.
- **No PDF update.** Adding opus to `gen_pdf.py` is a follow-up task once we have a JSON in hand.
- **No tool use for the solver.** Not "not yet" — not ever, for this experiment. A future "opus-solver-with-tools" experiment would be a separate spec.
- **No rate-limit handling.** Anthropic API rate limits apply to the whole Claude Code session. If we hit them, the user will see it in the orchestrator's output; no special handling.

## Open questions — none

All design questions were resolved in the brainstorming dialogue. Ready for implementation plan.
