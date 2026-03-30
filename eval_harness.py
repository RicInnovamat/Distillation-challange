#!/usr/bin/env python3
"""
Evaluation harness for the SAIR Mathematics Distillation Challenge.

Loads JSONL problems, substitutes equations into a prompt template,
calls target models via OpenRouter API, parses VERDICT from responses,
and outputs per-problem CSV results with accuracy summary and cost tracking.

Usage:
    python eval_harness.py --model gpt-oss-120b --prompt config/prompts/v0_baseline.txt --data hard2
    python eval_harness.py --model llama-3.3-70b --prompt cheatsheets/v1.txt --data normal --concurrency 20
    python eval_harness.py --model gpt-oss-120b --prompt config/prompts/v0_baseline.txt --data hard2 --dry-run
    python eval_harness.py --model gpt-oss-120b --prompt config/prompts/v0_baseline.txt --data hard2 --limit 30
"""

import argparse
import asyncio
import csv
import json
import os
import re
import ssl
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import aiohttp
import certifi
import yaml
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")
CONFIG_PATH = PROJECT_ROOT / "config" / "models.yaml"


def load_config():
    with open(CONFIG_PATH) as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

@dataclass
class Problem:
    id: str
    equation1: str
    equation2: str
    answer: bool
    eq1_id: int | None = None
    eq2_id: int | None = None
    difficulty: str = ""


@dataclass
class Result:
    problem_id: str
    expected: bool
    predicted: bool | None
    raw_verdict: str
    parse_ok: bool
    correct: bool | None
    response_text: str
    latency_s: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0


@dataclass
class RunSummary:
    model: str
    dataset: str
    prompt_file: str
    total: int = 0
    correct: int = 0
    wrong: int = 0
    parse_errors: int = 0
    true_as_true: int = 0
    true_as_false: int = 0
    false_as_true: int = 0
    false_as_false: int = 0
    total_cost: float = 0.0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_latency: float = 0.0
    results: list = field(default_factory=list)

    @property
    def accuracy(self):
        scorable = self.total - self.parse_errors
        return self.correct / scorable if scorable > 0 else 0.0

    @property
    def avg_latency(self):
        return self.total_latency / self.total if self.total > 0 else 0.0


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_problems(dataset_name: str, config: dict, limit: int | None = None) -> list[Problem]:
    datasets = config.get("datasets", {})
    if dataset_name in datasets:
        path = PROJECT_ROOT / datasets[dataset_name]
    else:
        path = Path(dataset_name)
        if not path.is_absolute():
            path = PROJECT_ROOT / path

    if not path.exists():
        print(f"Error: dataset file not found: {path}", file=sys.stderr)
        sys.exit(1)

    problems = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            problems.append(Problem(
                id=rec["id"],
                equation1=rec["equation1"],
                equation2=rec["equation2"],
                answer=rec["answer"],
                eq1_id=rec.get("eq1_id") or rec.get("equation1_id"),
                eq2_id=rec.get("eq2_id") or rec.get("equation2_id"),
                difficulty=rec.get("difficulty", ""),
            ))

    if limit:
        problems = problems[:limit]

    return problems


# ---------------------------------------------------------------------------
# Prompt rendering
# ---------------------------------------------------------------------------

def load_prompt_template(path: str) -> str:
    with open(path) as f:
        return f.read()


def render_prompt(template: str, problem: Problem) -> str:
    return (template
            .replace("{{ equation1 }}", problem.equation1)
            .replace("{{ equation2 }}", problem.equation2)
            .replace("{{equation1}}", problem.equation1)
            .replace("{{equation2}}", problem.equation2))


# ---------------------------------------------------------------------------
# VERDICT parsing
# ---------------------------------------------------------------------------

VERDICT_PATTERNS = [
    re.compile(r"VERDICT\s*:\s*(TRUE|FALSE)", re.IGNORECASE),
    re.compile(r"VERDICT\s*=\s*(TRUE|FALSE)", re.IGNORECASE),
    re.compile(r"\b(TRUE|FALSE)\b", re.IGNORECASE),
]


def parse_verdict(text: str | None) -> tuple[bool | None, str]:
    """Parse VERDICT from model output. Returns (prediction, raw_match)."""
    if not text:
        return None, ""
    for pattern in VERDICT_PATTERNS:
        match = pattern.search(text)
        if match:
            val = match.group(1).upper()
            return val == "TRUE", match.group(0)
    return None, ""


# ---------------------------------------------------------------------------
# OpenRouter API client
# ---------------------------------------------------------------------------

SEMAPHORE = None
MAX_RETRIES = 3
RETRY_DELAYS = [2, 5, 15]


async def call_openrouter(
    session: aiohttp.ClientSession,
    model_id: str,
    prompt: str,
    api_key: str,
    base_url: str,
    temperature: float,
    max_tokens: int,
) -> dict:
    """Call OpenRouter chat completion API with retry logic."""
    url = f"{base_url}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/RicInnovamat/Distillation-challange",
        "X-Title": "SAIR-Distillation-Challenge",
    }
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    for attempt in range(MAX_RETRIES):
        try:
            async with SEMAPHORE:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=120)) as resp:
                    if resp.status == 429:
                        delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                        print(f"  Rate limited, waiting {delay}s...", file=sys.stderr)
                        await asyncio.sleep(delay)
                        continue
                    if resp.status >= 500:
                        delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                        print(f"  Server error {resp.status}, retrying in {delay}s...", file=sys.stderr)
                        await asyncio.sleep(delay)
                        continue
                    resp.raise_for_status()
                    return await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                print(f"  Request error: {e}, retrying in {delay}s...", file=sys.stderr)
                await asyncio.sleep(delay)
            else:
                raise

    raise RuntimeError(f"Failed after {MAX_RETRIES} retries")


# ---------------------------------------------------------------------------
# Evaluation logic
# ---------------------------------------------------------------------------

async def evaluate_problem(
    session: aiohttp.ClientSession,
    problem: Problem,
    prompt_template: str,
    model_id: str,
    model_config: dict,
    api_key: str,
    base_url: str,
    temperature: float,
    max_tokens: int,
    dry_run: bool = False,
) -> Result:
    """Evaluate a single problem and return the result."""
    rendered = render_prompt(prompt_template, problem)

    if dry_run:
        return Result(
            problem_id=problem.id,
            expected=problem.answer,
            predicted=None,
            raw_verdict="[DRY RUN]",
            parse_ok=False,
            correct=None,
            response_text="[DRY RUN]",
            latency_s=0.0,
        )

    try:
        start = time.monotonic()
        response = await call_openrouter(
            session, model_id, rendered, api_key, base_url, temperature, max_tokens
        )
        latency = time.monotonic() - start

        # Extract response text (handle reasoning models where content may be null)
        text = ""
        if "choices" in response and response["choices"]:
            msg = response["choices"][0].get("message", {})
            text = msg.get("content", "") or ""
            # For reasoning models (e.g. GPT-OSS), content may be null;
            # fall back to reasoning field
            if not text:
                text = msg.get("reasoning", "") or ""

        # Check for API error in response
        if "error" in response:
            err_msg = response["error"].get("message", str(response["error"]))
            return Result(
                problem_id=problem.id, expected=problem.answer,
                predicted=None, raw_verdict="", parse_ok=False, correct=None,
                response_text=f"[API ERROR] {err_msg}"[:500], latency_s=latency,
            )

        # Extract token usage
        usage = response.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        # Calculate cost
        input_cost = (input_tokens / 1_000_000) * model_config.get("input_cost_per_1m", 0)
        output_cost = (output_tokens / 1_000_000) * model_config.get("output_cost_per_1m", 0)

        # Parse verdict
        predicted, raw_verdict = parse_verdict(text)
        parse_ok = predicted is not None
        correct = (predicted == problem.answer) if parse_ok else None

        return Result(
            problem_id=problem.id,
            expected=problem.answer,
            predicted=predicted,
            raw_verdict=raw_verdict,
            parse_ok=parse_ok,
            correct=correct,
            response_text=text[:500],
            latency_s=latency,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=input_cost + output_cost,
        )
    except Exception as e:
        return Result(
            problem_id=problem.id, expected=problem.answer,
            predicted=None, raw_verdict="", parse_ok=False, correct=None,
            response_text=f"[EXCEPTION] {type(e).__name__}: {e}"[:500],
            latency_s=time.monotonic() - start if 'start' in dir() else 0.0,
        )


async def run_evaluation(
    problems: list[Problem],
    prompt_template: str,
    model_name: str,
    model_config: dict,
    config: dict,
    dry_run: bool = False,
) -> RunSummary:
    """Run evaluation across all problems with async parallelism."""
    global SEMAPHORE

    defaults = config.get("defaults", {})
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key and not dry_run:
        print("Error: OPENROUTER_API_KEY environment variable not set.", file=sys.stderr)
        sys.exit(1)

    base_url = defaults.get("openrouter_base_url", "https://openrouter.ai/api/v1")
    temperature = defaults.get("temperature", 0.0)
    max_tokens = defaults.get("max_tokens", 1024)
    concurrency = defaults.get("concurrency", 10)
    SEMAPHORE = asyncio.Semaphore(concurrency)

    model_id = model_config["model_id"]
    summary = RunSummary(model=model_name, dataset="", prompt_file="")

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            evaluate_problem(
                session, p, prompt_template, model_id, model_config,
                api_key, base_url, temperature, max_tokens, dry_run
            )
            for p in problems
        ]

        completed = 0
        total = len(tasks)
        for coro in asyncio.as_completed(tasks):
            result = await coro
            summary.results.append(result)
            completed += 1

            # Progress
            status = "PARSE_ERR" if not result.parse_ok else ("OK" if result.correct else "WRONG")
            if not dry_run:
                print(f"  [{completed}/{total}] {result.problem_id}: {status} "
                      f"(expected={result.expected}, got={result.predicted}, "
                      f"${result.cost_usd:.4f}, {result.latency_s:.1f}s)")

    # Sort results by problem ID for stable output
    summary.results.sort(key=lambda r: r.problem_id)

    # Compute summary stats
    for r in summary.results:
        summary.total += 1
        summary.total_cost += r.cost_usd
        summary.total_input_tokens += r.input_tokens
        summary.total_output_tokens += r.output_tokens
        summary.total_latency += r.latency_s

        if not r.parse_ok:
            summary.parse_errors += 1
            continue

        if r.correct:
            summary.correct += 1
        else:
            summary.wrong += 1

        if r.expected and r.predicted:
            summary.true_as_true += 1
        elif r.expected and not r.predicted:
            summary.true_as_false += 1
        elif not r.expected and r.predicted:
            summary.false_as_true += 1
        else:
            summary.false_as_false += 1

    return summary


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_csv(summary: RunSummary, output_path: Path):
    """Write per-problem results to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "problem_id", "expected", "predicted", "correct", "parse_ok",
            "raw_verdict", "latency_s", "input_tokens", "output_tokens",
            "cost_usd", "response_text"
        ])
        for r in summary.results:
            writer.writerow([
                r.problem_id,
                r.expected,
                r.predicted if r.predicted is not None else "",
                r.correct if r.correct is not None else "",
                r.parse_ok,
                r.raw_verdict,
                f"{r.latency_s:.2f}",
                r.input_tokens,
                r.output_tokens,
                f"{r.cost_usd:.6f}",
                r.response_text.replace("\n", "\\n")[:200],
            ])
    print(f"\nResults written to: {output_path}")


def print_summary(summary: RunSummary):
    """Print accuracy summary to stdout."""
    scorable = summary.total - summary.parse_errors
    print("\n" + "=" * 60)
    print(f"  Model:       {summary.model}")
    print(f"  Dataset:     {summary.dataset}")
    print(f"  Prompt:      {summary.prompt_file}")
    print(f"{'=' * 60}")
    print(f"  Total problems:     {summary.total}")
    print(f"  Correct:            {summary.correct}/{scorable} ({summary.accuracy:.1%})")
    print(f"  Wrong:              {summary.wrong}")
    print(f"  Parse errors:       {summary.parse_errors}")
    print(f"  ---")
    print(f"  TRUE→TRUE:          {summary.true_as_true}")
    print(f"  TRUE→FALSE:         {summary.true_as_false}  (missed implications)")
    print(f"  FALSE→TRUE:         {summary.false_as_true}  (confabulations)")
    print(f"  FALSE→FALSE:        {summary.false_as_false}")
    print(f"  ---")
    print(f"  Total cost:         ${summary.total_cost:.4f}")
    print(f"  Total tokens:       {summary.total_input_tokens} in / {summary.total_output_tokens} out")
    print(f"  Avg latency:        {summary.avg_latency:.1f}s")
    print(f"{'=' * 60}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="SAIR Distillation Challenge - Evaluation Harness"
    )
    parser.add_argument(
        "--model", required=True,
        help="Model name from config/models.yaml (e.g., gpt-oss-120b)"
    )
    parser.add_argument(
        "--prompt", required=True,
        help="Path to prompt template file"
    )
    parser.add_argument(
        "--data", required=True,
        help="Dataset name from config or path to JSONL file"
    )
    parser.add_argument(
        "--concurrency", type=int, default=None,
        help="Max concurrent API requests (default: from config)"
    )
    parser.add_argument(
        "--temperature", type=float, default=None,
        help="Model temperature (default: from config)"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=None,
        help="Max output tokens (default: from config)"
    )
    parser.add_argument(
        "--output", default=None,
        help="Output CSV path (default: results/<model>_<dataset>_<timestamp>.csv)"
    )
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Limit number of problems to evaluate"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Skip API calls, test data loading and prompt rendering"
    )
    return parser.parse_args()


def main():
    args = parse_args()
    config = load_config()

    # Validate model
    models = config.get("models", {})
    if args.model not in models:
        print(f"Error: unknown model '{args.model}'. Available: {', '.join(models.keys())}", file=sys.stderr)
        sys.exit(1)
    model_config = models[args.model]

    # Override defaults
    if args.concurrency:
        config.setdefault("defaults", {})["concurrency"] = args.concurrency
    if args.temperature is not None:
        config.setdefault("defaults", {})["temperature"] = args.temperature
    if args.max_tokens:
        config.setdefault("defaults", {})["max_tokens"] = args.max_tokens

    # Load data
    problems = load_problems(args.data, config, args.limit)
    print(f"Loaded {len(problems)} problems from '{args.data}'")

    # Load prompt
    prompt_template = load_prompt_template(args.prompt)
    prompt_size = len(prompt_template.encode("utf-8"))
    print(f"Prompt template: {args.prompt} ({prompt_size} bytes)")
    if prompt_size > 10240:
        print(f"WARNING: Prompt size ({prompt_size} bytes) exceeds 10KB limit!", file=sys.stderr)

    # Show sample render
    sample = render_prompt(prompt_template, problems[0])
    print(f"Sample rendered prompt ({len(sample)} chars):\n---\n{sample[:300]}{'...' if len(sample) > 300 else ''}\n---")

    if args.dry_run:
        print("\n[DRY RUN] Skipping API calls.")

    # Run evaluation
    summary = asyncio.run(run_evaluation(
        problems, prompt_template, args.model, model_config, config, args.dry_run
    ))
    summary.dataset = args.data
    summary.prompt_file = args.prompt

    # Output
    print_summary(summary)

    if not args.dry_run:
        if args.output:
            output_path = Path(args.output)
        else:
            ts = time.strftime("%Y%m%d_%H%M%S")
            output_path = PROJECT_ROOT / "results" / f"{args.model}_{args.data}_{ts}.csv"
        write_csv(summary, output_path)


if __name__ == "__main__":
    main()
