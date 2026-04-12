#!/usr/bin/env python3
"""Benchmark the opus-solver subagent across a SAIR equational-theories dataset.

Sidesteps Claude Code's "subagents cannot spawn subagents" limit by shelling out
to `claude -p --agent opus-solver` per problem from a plain Python process.
Each invocation is a fresh Claude Code process that CAN spawn opus-solver via
its own top-level Agent dispatch. The script parses verdicts via
`eval_harness.parse_verdict` (SAIR-compliant last-match semantics) and writes
results JSON in the exact schema the existing opus-orchestrator spec defines.

Usage:
    python3 scripts/run_opus_benchmark.py --dataset hard1 [--limit 3] \
        --output-dir results/20260411_opus-smoke/ [--parallel 3]

Anti-cheat: only `equation1` and `equation2` are sent to each solver call. The
`answer` field is held by the driver and used only to compute `correct`.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from eval_harness import parse_verdict  # noqa: E402

DATASET_PATHS = {
    "hard1": ROOT / "Training_data" / "hard1.jsonl",
    "hard2": ROOT / "Training_data" / "hard2.jsonl",
    "hard3": ROOT / "Training_data" / "hard3.jsonl",
}

SOLVER_TIMEOUT_S = 1800  # 30 min per problem hard cap


def resolve_dataset(dataset: str) -> Path:
    if dataset in DATASET_PATHS:
        return DATASET_PATHS[dataset]
    return Path(dataset).resolve()


def load_problems(jsonl_path: Path) -> list[dict]:
    problems = []
    with jsonl_path.open() as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            for field in ("id", "equation1", "equation2", "answer"):
                if field not in record:
                    raise ValueError(
                        f"{jsonl_path}:{line_no} missing required field {field!r}"
                    )
            problems.append(record)
    return problems


def call_solver(equation1: str, equation2: str) -> tuple[str, float, str | None]:
    """Run opus-solver on one problem via `claude -p --agent opus-solver`.

    Returns (solver_text, latency_s, error_message_or_none).
    """
    prompt = f"Equation 1: {equation1}\nEquation 2: {equation2}"
    t0 = time.monotonic()
    try:
        result = subprocess.run(
            [
                "claude",
                "-p",
                "--agent",
                "opus-solver",
                "--output-format",
                "text",
                prompt,
            ],
            capture_output=True,
            text=True,
            timeout=SOLVER_TIMEOUT_S,
        )
    except subprocess.TimeoutExpired as e:
        return e.stdout or "", time.monotonic() - t0, "timeout"
    except FileNotFoundError:
        return "", time.monotonic() - t0, "claude CLI not found on PATH"
    latency = time.monotonic() - t0
    if result.returncode != 0:
        return result.stdout or "", latency, f"exit={result.returncode}: {result.stderr.strip()[:500]}"
    return result.stdout, latency, None


def build_record(problem: dict, solver_text: str, latency_s: float, error: str | None) -> dict:
    # Always attempt verdict parsing — even partial output from timeouts/crashes
    # may contain a usable VERDICT line.
    predicted, raw_match = parse_verdict(solver_text) if solver_text else (None, "")
    if error is not None:
        parse_ok = predicted is not None
        correct = problem["answer"] == predicted if parse_ok else None
        return {
            "problem_id": problem["id"],
            "expected": problem["answer"],
            "predicted": predicted,
            "correct": correct,
            "parse_ok": parse_ok,
            "raw_verdict": raw_match or "",
            "reasoning": solver_text if solver_text else f"<ERROR: {error}>",
            "content": solver_text if solver_text else f"<ERROR: {error}>",
            "error": error,
            "latency_s": round(latency_s, 3),
            "input_tokens": 0,
            "output_tokens": 0,
            "cost_usd": 0,
        }
    predicted, raw_match = parse_verdict(solver_text)
    parse_ok = predicted is not None
    if parse_ok:
        correct = problem["answer"] == predicted
    else:
        correct = None
    return {
        "problem_id": problem["id"],
        "expected": problem["answer"],
        "predicted": predicted,
        "correct": correct,
        "parse_ok": parse_ok,
        "raw_verdict": raw_match,
        "reasoning": solver_text,
        "content": solver_text,
        "latency_s": round(latency_s, 3),
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": 0,
    }


def summarize(records: list[dict]) -> dict:
    total = len(records)
    correct = sum(1 for r in records if r["correct"] is True)
    wrong = sum(1 for r in records if r["parse_ok"] and r["correct"] is False)
    parse_errors = sum(1 for r in records if not r["parse_ok"])
    accuracy = correct / total if total else 0.0
    true_as_true = sum(1 for r in records if r["expected"] is True and r["predicted"] is True)
    true_as_false = sum(1 for r in records if r["expected"] is True and r["predicted"] is False)
    false_as_true = sum(1 for r in records if r["expected"] is False and r["predicted"] is True)
    false_as_false = sum(1 for r in records if r["expected"] is False and r["predicted"] is False)
    return {
        "total": total,
        "correct": correct,
        "wrong": wrong,
        "parse_errors": parse_errors,
        "accuracy": accuracy,
        "true_as_true": true_as_true,
        "true_as_false": true_as_false,
        "false_as_true": false_as_true,
        "false_as_false": false_as_false,
    }


def write_results(
    out_path: Path,
    dataset_name: str,
    records: list[dict],
) -> None:
    payload = {
        "model": "opus-solver (claude-code-subagent)",
        "backend": "claude-code-subagent",
        "model_id": "claude-opus-4-6",
        "dataset": dataset_name,
        "prompt_file": ".claude/agents/opus-solver.md",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "summary": summarize(records),
        "problems": records,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2))


def load_resume(resume_path: Path, dataset_name: str) -> tuple[dict[str, dict], str]:
    """Read an existing results JSON and return a (problem_id → record) map plus its timestamp.

    The timestamp is extracted from the filename suffix so resume writes keep
    the original filename — `opus-solver_<dataset>_<YYYYMMDD_HHMMSS>.json`.
    """
    if not resume_path.exists():
        raise FileNotFoundError(f"resume file not found: {resume_path}")
    existing = json.loads(resume_path.read_text())
    if existing.get("dataset") != dataset_name:
        raise ValueError(
            f"resume dataset mismatch: file has {existing.get('dataset')!r}, "
            f"requested {dataset_name!r}"
        )
    records_by_id = {r["problem_id"]: r for r in existing.get("problems", [])}
    # Extract original timestamp from filename: opus-solver_<ds>_<YYYYMMDD_HHMMSS>.json
    m = re.search(r"_(\d{8}_\d{6})\.json$", resume_path.name)
    if not m:
        raise ValueError(f"cannot extract timestamp from filename: {resume_path.name}")
    return records_by_id, m.group(1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dataset", required=True, help="hard1|hard2|hard3 or a path to a JSONL file")
    parser.add_argument("--output-dir", default="results/opus-benchmark/", help="target directory for results JSON")
    parser.add_argument("--limit", type=int, default=None, help="stop after N problems (for smoke tests)")
    parser.add_argument("--parallel", type=int, default=3, help="number of parallel solver calls (default 3)")
    parser.add_argument(
        "--resume",
        default=None,
        help="path to an existing results JSON; problems already recorded are skipped and new results are merged into the same file (keeping the original timestamp in the filename)",
    )
    args = parser.parse_args()

    dataset_name = args.dataset if args.dataset in DATASET_PATHS else Path(args.dataset).stem
    jsonl_path = resolve_dataset(args.dataset)
    if not jsonl_path.exists():
        print(f"ERROR: dataset not found: {jsonl_path}", file=sys.stderr)
        return 2

    all_problems = load_problems(jsonl_path)
    if args.limit is not None:
        all_problems = all_problems[: args.limit]
    if not all_problems:
        print("ERROR: no problems to run", file=sys.stderr)
        return 2

    # --resume: pre-load completed records and filter the work list.
    pre_loaded: dict[int, dict] = {}
    if args.resume is not None:
        resume_path = Path(args.resume)
        pre_records_by_id, resume_timestamp = load_resume(resume_path, dataset_name)
        # Map each pre-loaded record to its index in the full dataset.
        id_to_index = {p["id"]: i for i, p in enumerate(all_problems)}
        skipped = []
        for pid, rec in pre_records_by_id.items():
            if pid not in id_to_index:
                print(f"[driver] WARN: resume record {pid} not in dataset — ignoring", file=sys.stderr, flush=True)
                continue
            pre_loaded[id_to_index[pid]] = rec
            skipped.append(pid)
        problems_todo = [p for p in all_problems if p["id"] not in pre_records_by_id]
        timestamp = resume_timestamp
        out_path = resume_path
        print(
            f"[driver] RESUME {resume_path.name}: "
            f"{len(pre_loaded)} pre-loaded, {len(problems_todo)} remaining",
            flush=True,
        )
    else:
        problems_todo = all_problems
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out_path = Path(args.output_dir) / f"opus-solver_{dataset_name}_{timestamp}.json"

    total_expected = len(all_problems)
    print(
        f"[driver] dataset={dataset_name} total={total_expected} todo={len(problems_todo)} "
        f"parallel={args.parallel} out={out_path}",
        flush=True,
    )

    records_by_index: dict[int, dict] = dict(pre_loaded)
    done_before = len(pre_loaded)
    id_to_index = {p["id"]: i for i, p in enumerate(all_problems)}
    with ThreadPoolExecutor(max_workers=args.parallel) as executor:
        futures = {
            executor.submit(call_solver, p["equation1"], p["equation2"]): (id_to_index[p["id"]], p)
            for p in problems_todo
        }
        done_count = 0
        for fut in as_completed(futures):
            i, problem = futures[fut]
            solver_text, latency_s, error = fut.result()
            record = build_record(problem, solver_text, latency_s, error)
            records_by_index[i] = record
            done_count += 1
            total_done = done_before + done_count
            marker = "PARSE_ERR" if not record["parse_ok"] else (
                "CORRECT" if record["correct"] else "WRONG"
            )
            print(
                f"[driver] {total_done}/{total_expected} {problem['id']} "
                f"{marker} latency={latency_s:.1f}s predicted={record['predicted']} expected={problem['answer']}",
                flush=True,
            )
            if done_count % 10 == 0:
                ordered = [records_by_index[k] for k in sorted(records_by_index.keys())]
                write_results(out_path, dataset_name, ordered)
                print(f"[driver] partial JSON written: {out_path}", flush=True)

    final_records = [records_by_index[k] for k in sorted(records_by_index.keys())]
    write_results(out_path, dataset_name, final_records)
    summary = summarize(final_records)
    print(f"[driver] FINAL {out_path}", flush=True)
    print(f"[driver] summary={summary}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
