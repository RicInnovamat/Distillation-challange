#!/usr/bin/env python3
"""
Error taxonomy analysis for SAIR evaluation results.

Loads per-problem CSV results from eval_harness.py, cross-references with
the implication graph, and classifies errors by type and structural features.

Usage:
    python analysis/error_taxonomy.py results/gpt-oss-120b_hard2_20260330.csv
    python analysis/error_taxonomy.py results/baselines/*.csv --compare
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Load implication graph
# ---------------------------------------------------------------------------

def load_implication_graph() -> dict:
    """Load equation statistics from Raw_implication_graph.csv.
    Returns dict mapping equation_id -> {implies, implied_by, ...}
    """
    path = PROJECT_ROOT / "Research" / "Raw_implication_graph.csv"
    if not path.exists():
        print(f"Warning: implication graph not found at {path}", file=sys.stderr)
        return {}

    graph = {}
    with open(path) as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            # Format: Equation<N>[...], Implies, Implied by, Does not imply, ...
            eq_str = row[0]
            match = re.search(r"Equation(\d+)", eq_str)
            if not match:
                continue
            eq_id = int(match.group(1))
            graph[eq_id] = {
                "implies": int(row[1]),
                "implied_by": int(row[2]),
                "does_not_imply": int(row[3]),
                "not_implied_by": int(row[4]),
                "unknown": int(row[5]),
                "unknown_by": int(row[6]),
            }
    return graph


# ---------------------------------------------------------------------------
# Load training data for equation IDs
# ---------------------------------------------------------------------------

def load_problem_metadata() -> dict:
    """Load eq1_id and eq2_id from all training JSONL files."""
    meta = {}
    for folder in ["Training_data", "Extra_training_data"]:
        data_dir = PROJECT_ROOT / folder
        if not data_dir.exists():
            continue
        for jsonl_file in data_dir.glob("*.jsonl"):
            with open(jsonl_file) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    rec = json.loads(line)
                    pid = rec["id"]
                    meta[pid] = {
                        "eq1_id": rec.get("eq1_id") or rec.get("equation1_id"),
                        "eq2_id": rec.get("eq2_id") or rec.get("equation2_id"),
                        "equation1": rec.get("equation1", ""),
                        "equation2": rec.get("equation2", ""),
                        "difficulty": rec.get("difficulty", ""),
                    }
    return meta


# ---------------------------------------------------------------------------
# Load results CSV
# ---------------------------------------------------------------------------

def load_results(csv_path: str) -> list[dict]:
    results = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            row["expected"] = row["expected"] == "True"
            row["predicted"] = row["predicted"] == "True" if row["predicted"] else None
            row["correct"] = row["correct"] == "True" if row["correct"] else None
            row["parse_ok"] = row["parse_ok"] == "True"
            row["cost_usd"] = float(row.get("cost_usd", 0))
            results.append(row)
    return results


# ---------------------------------------------------------------------------
# Equation structural features
# ---------------------------------------------------------------------------

def count_operators(eq: str) -> int:
    return eq.count("*") + eq.count("◇")


def count_variables(eq: str) -> set:
    return set(re.findall(r"\b([a-z])\b", eq))


def classify_equation_strength(eq_id: int | None, graph: dict) -> str:
    if eq_id is None or eq_id not in graph:
        return "unknown"
    implies = graph[eq_id]["implies"]
    if implies > 1000:
        return "collapsing"
    elif implies > 100:
        return "strong"
    elif implies > 10:
        return "moderate"
    elif implies > 0:
        return "weak"
    else:
        return "tautology"


# ---------------------------------------------------------------------------
# Error classification
# ---------------------------------------------------------------------------

def classify_error(result: dict, meta: dict, graph: dict) -> dict:
    """Classify a single incorrect result."""
    pid = result["problem_id"]
    pm = meta.get(pid, {})

    error = {
        "problem_id": pid,
        "expected": result["expected"],
        "predicted": result["predicted"],
        "parse_ok": result["parse_ok"],
    }

    # Error type
    if not result["parse_ok"]:
        error["error_type"] = "parse_error"
    elif result["expected"] and not result["predicted"]:
        error["error_type"] = "true_as_false"  # missed implication / FALSE bias
    elif not result["expected"] and result["predicted"]:
        error["error_type"] = "false_as_true"  # confabulation
    else:
        error["error_type"] = "correct"
        return error

    # Structural features
    eq1 = pm.get("equation1", "")
    eq2 = pm.get("equation2", "")
    error["eq1_ops"] = count_operators(eq1)
    error["eq2_ops"] = count_operators(eq2)
    error["eq1_vars"] = len(count_variables(eq1))
    error["eq2_vars"] = len(count_variables(eq2))
    error["var_overlap"] = len(count_variables(eq1) & count_variables(eq2))
    error["eq1_strength"] = classify_equation_strength(pm.get("eq1_id"), graph)
    error["eq2_strength"] = classify_equation_strength(pm.get("eq2_id"), graph)
    error["difficulty"] = pm.get("difficulty", "")

    return error


# ---------------------------------------------------------------------------
# Analysis and reporting
# ---------------------------------------------------------------------------

def analyze_results(csv_path: str):
    """Run full error taxonomy analysis on a results CSV."""
    results = load_results(csv_path)
    graph = load_implication_graph()
    meta = load_problem_metadata()

    errors = []
    for r in results:
        classified = classify_error(r, meta, graph)
        if classified["error_type"] != "correct":
            errors.append(classified)

    total = len(results)
    correct = sum(1 for r in results if r.get("correct"))
    parse_errors = sum(1 for r in results if not r["parse_ok"])
    scorable = total - parse_errors

    print(f"\n{'=' * 60}")
    print(f"  Error Taxonomy: {Path(csv_path).name}")
    print(f"{'=' * 60}")
    print(f"  Total: {total}, Correct: {correct}/{scorable} ({correct/scorable:.1%}), "
          f"Parse errors: {parse_errors}")
    print()

    # Error type breakdown
    type_counts = Counter(e["error_type"] for e in errors)
    print("  Error type breakdown:")
    for etype, count in type_counts.most_common():
        print(f"    {etype}: {count}")

    # Structural patterns for each error type
    for etype in ["false_as_true", "true_as_false", "parse_error"]:
        typed_errors = [e for e in errors if e["error_type"] == etype]
        if not typed_errors:
            continue

        print(f"\n  --- {etype} ({len(typed_errors)} errors) ---")

        # Operator count distribution
        if etype != "parse_error":
            ops = Counter(
                f"eq1={e.get('eq1_ops', '?')},eq2={e.get('eq2_ops', '?')}"
                for e in typed_errors
            )
            print(f"    Op count distribution: {dict(ops.most_common(5))}")

            # Equation strength
            eq1_str = Counter(e.get("eq1_strength", "?") for e in typed_errors)
            eq2_str = Counter(e.get("eq2_strength", "?") for e in typed_errors)
            print(f"    Eq1 strength: {dict(eq1_str.most_common(5))}")
            print(f"    Eq2 strength: {dict(eq2_str.most_common(5))}")

            # Difficulty
            diff = Counter(e.get("difficulty", "?") for e in typed_errors)
            print(f"    Difficulty: {dict(diff)}")

    print()

    return errors


def compare_results(*csv_paths: str):
    """Compare accuracy across multiple result files."""
    print(f"\n{'=' * 80}")
    print(f"  Comparison across {len(csv_paths)} runs")
    print(f"{'=' * 80}")
    print(f"  {'File':<50} {'Acc':>6} {'Err':>5} {'Parse':>5} {'Cost':>8}")
    print(f"  {'-' * 74}")

    for path in csv_paths:
        results = load_results(path)
        total = len(results)
        correct = sum(1 for r in results if r.get("correct"))
        parse_err = sum(1 for r in results if not r["parse_ok"])
        scorable = total - parse_err
        acc = correct / scorable if scorable > 0 else 0
        cost = sum(r["cost_usd"] for r in results)

        name = Path(path).stem
        print(f"  {name:<50} {acc:>5.1%} {total - correct - parse_err:>5} {parse_err:>5} ${cost:>7.4f}")

    print()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Error taxonomy analysis")
    parser.add_argument("csv_files", nargs="+", help="Result CSV file(s)")
    parser.add_argument("--compare", action="store_true", help="Compare multiple runs")
    args = parser.parse_args()

    if args.compare and len(args.csv_files) > 1:
        compare_results(*args.csv_files)
    else:
        for csv_file in args.csv_files:
            analyze_results(csv_file)


if __name__ == "__main__":
    main()
