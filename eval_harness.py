#!/usr/bin/env python3
"""
Evaluation harness for the SAIR Mathematics Distillation Challenge.

Loads JSONL problems, substitutes equations into a prompt template,
calls target models via OpenRouter API, parses VERDICT from responses,
and outputs per-problem CSV results with accuracy summary and cost tracking.

Usage (interactive — model/backend prompted at start):
    python eval_harness.py --prompt cheatsheets/v1_cheatsheet.txt --data hard2

Usage (scripted — model/backend fully specified):
    python eval_harness.py --model gpt-oss-120b --backend openrouter --prompt config/prompts/v0_baseline.txt --data hard2
    python eval_harness.py --model llama-3.3-70b --backend ollama     --prompt cheatsheets/v1.txt --data normal
    python eval_harness.py --model gpt-oss-120b --prompt config/prompts/v0_baseline.txt --data hard2 --dry-run --limit 30
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
from datetime import datetime, timezone
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
    response_text: str        # truncated content (for CSV display)
    latency_s: float
    input_tokens: int = 0
    output_tokens: int = 0
    cost_usd: float = 0.0
    content: str = ""         # full message content (for JSON reasoning dump)
    reasoning: str = ""       # separate reasoning thread, if the model emits one


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
RETRY_DELAYS = [5, 15, 30]
HARD_TIMEOUT_S = 180  # asyncio.wait_for hard cutoff per API call


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
        "HTTP-Referer": "https://github.com/Distilliation-Math/Distillation-challange",
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
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=HARD_TIMEOUT_S)) as resp:
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
                    data = await resp.json()

                    # Guard against null JSON body from OpenRouter
                    if data is None:
                        delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                        print(f"  Null response body, retrying in {delay}s...", file=sys.stderr)
                        await asyncio.sleep(delay)
                        continue

                    # Detect empty responses (0 tokens, no content) — treat as
                    # retriable server-side failure instead of accepting silently.
                    usage = data.get("usage", {})
                    choices = data.get("choices", [])
                    content = ""
                    if choices:
                        content = (choices[0].get("message", {}).get("content", "") or "").strip()
                    tok_out = usage.get("completion_tokens", 0)
                    if not content and tok_out == 0 and "error" not in data:
                        delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                        print(f"  Empty response (0 tokens), retrying in {delay}s...", file=sys.stderr)
                        await asyncio.sleep(delay)
                        continue

                    return data
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                print(f"  Request error: {e}, retrying in {delay}s...", file=sys.stderr)
                await asyncio.sleep(delay)
            else:
                raise

    raise RuntimeError(f"Failed after {MAX_RETRIES} retries")


async def call_ollama(
    session: aiohttp.ClientSession,
    model_id: str,
    prompt: str,
    base_url: str,
    temperature: float,
    max_tokens: int,
    num_ctx: int | None = None,
) -> dict:
    """Call local Ollama chat API; return response shaped like OpenRouter's.

    num_ctx overrides ollama's default context window (2048). Set it to
    the model's max to avoid silent truncation of long cheatsheet prompts.
    """
    url = f"{base_url}/api/chat"
    options: dict = {
        "temperature": temperature,
        "num_predict": max_tokens,
    }
    if num_ctx is not None:
        options["num_ctx"] = num_ctx
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": options,
    }

    for attempt in range(MAX_RETRIES):
        try:
            async with SEMAPHORE:
                async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=300)) as resp:
                    if resp.status >= 500:
                        delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                        print(f"  Ollama error {resp.status}, retrying in {delay}s...", file=sys.stderr)
                        await asyncio.sleep(delay)
                        continue
                    if resp.status == 404:
                        body = await resp.text()
                        raise RuntimeError(
                            f"Ollama model not found: {model_id}. "
                            f"Pull it first: `ollama pull {model_id}`. Server said: {body[:200]}"
                        )
                    resp.raise_for_status()
                    raw = await resp.json()
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt < MAX_RETRIES - 1:
                delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
                print(f"  Ollama request error: {e}, retrying in {delay}s...", file=sys.stderr)
                await asyncio.sleep(delay)
                continue
            raise
        # Shape ollama response like OpenRouter's (OpenAI format) so downstream
        # parsing code is backend-agnostic. Ollama thinking-mode models return
        # the reasoning trace in message.thinking; expose it as "reasoning" for
        # a unified downstream interface.
        message = raw.get("message", {})
        content = message.get("content", "") or ""
        reasoning = message.get("thinking", "") or ""
        return {
            "choices": [{"message": {"role": "assistant", "content": content, "reasoning": reasoning}}],
            "usage": {
                "prompt_tokens": raw.get("prompt_eval_count", 0),
                "completion_tokens": raw.get("eval_count", 0),
            },
        }

    raise RuntimeError(f"Ollama failed after {MAX_RETRIES} retries")


# ---------------------------------------------------------------------------
# Interactive model/backend selection
# ---------------------------------------------------------------------------

def prompt_select_model(models: dict) -> str:
    """Show a numbered menu of models and return the chosen key."""
    names = list(models.keys())
    print("\nSelect a model:")
    for i, name in enumerate(names, 1):
        disp = models[name].get("display_name", name)
        backends = [b for b in ("openrouter", "ollama") if b in models[name]]
        tag = "" if "ollama" in backends else "  (remote only)"
        print(f"  {i}. {disp}{tag}")
    while True:
        raw = input(f"Enter number [1-{len(names)}]: ").strip()
        try:
            idx = int(raw)
            if 1 <= idx <= len(names):
                return names[idx - 1]
        except ValueError:
            pass
        print(f"Invalid choice. Enter a number between 1 and {len(names)}.")


def prompt_select_backend(model_name: str, model_cfg: dict) -> str:
    """If model has multiple backends, prompt user; otherwise return the only one."""
    backends = [b for b in ("openrouter", "ollama") if b in model_cfg]
    if len(backends) == 1:
        print(f"  → only '{backends[0]}' backend available for {model_name}")
        return backends[0]
    print(f"\nSelect backend for {model_cfg.get('display_name', model_name)}:")
    print("  1. Remote (OpenRouter)")
    print("  2. Local (Ollama)")
    while True:
        raw = input("Enter number [1-2]: ").strip()
        if raw == "1":
            return "openrouter"
        if raw == "2":
            return "ollama"
        print("Invalid choice. Enter 1 or 2.")


# ---------------------------------------------------------------------------
# Evaluation logic
# ---------------------------------------------------------------------------

async def evaluate_problem(
    session: aiohttp.ClientSession,
    problem: Problem,
    prompt_template: str,
    backend: str,
    backend_cfg: dict,
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

    model_id = backend_cfg["model_id"]
    try:
        start = time.monotonic()
        if backend == "openrouter":
            response = await call_openrouter(
                session, model_id, rendered, api_key, base_url, temperature, max_tokens
            )
        elif backend == "ollama":
            response = await call_ollama(
                session, model_id, rendered, base_url, temperature, max_tokens,
                num_ctx=backend_cfg.get("num_ctx"),
            )
        else:
            raise ValueError(f"unknown backend: {backend}")
        latency = time.monotonic() - start

        # Extract content and reasoning separately (kept independent for the
        # reasoning-thread JSON dump). For verdict parsing, prefer content;
        # if content is empty (some reasoning models return null), fall back
        # to reasoning so we can still extract a TRUE/FALSE answer.
        content = ""
        reasoning = ""
        if "choices" in response and response["choices"]:
            msg = response["choices"][0].get("message", {})
            content = msg.get("content", "") or ""
            reasoning = msg.get("reasoning", "") or ""
        text = content if content else reasoning

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

        # Calculate cost (ollama has no cost; costs are on openrouter backend_cfg)
        input_cost = (input_tokens / 1_000_000) * backend_cfg.get("input_cost_per_1m", 0)
        output_cost = (output_tokens / 1_000_000) * backend_cfg.get("output_cost_per_1m", 0)

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
            content=content,
            reasoning=reasoning,
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
    backend: str,
    backend_cfg: dict,
    config: dict,
    dry_run: bool = False,
) -> RunSummary:
    """Run evaluation across all problems with async parallelism."""
    global SEMAPHORE

    defaults = config.get("defaults", {})
    if backend == "openrouter":
        api_key = os.environ.get("OPENROUTER_API_KEY", "")
        if not api_key and not dry_run:
            print("Error: OPENROUTER_API_KEY environment variable not set.", file=sys.stderr)
            sys.exit(1)
        base_url = defaults.get("openrouter_base_url", "https://openrouter.ai/api/v1")
    elif backend == "ollama":
        api_key = ""  # no auth for local ollama
        base_url = defaults.get("ollama_base_url", "http://localhost:11434")
    else:
        raise ValueError(f"unknown backend: {backend}")

    # Per-model parameter overrides (e.g., reasoning models need temperature=1)
    model_params = config.get("models", {}).get(model_name, {}).get("params", {})
    temperature = model_params.get("temperature", defaults.get("temperature", 0.0))
    max_tokens = model_params.get("max_tokens", defaults.get("max_tokens", 1024))
    concurrency = defaults.get("concurrency", 10)
    SEMAPHORE = asyncio.Semaphore(concurrency)

    summary = RunSummary(model=f"{model_name} ({backend})", dataset="", prompt_file="")

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            evaluate_problem(
                session, p, prompt_template, backend, backend_cfg,
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


def write_reasoning_json(
    summary: RunSummary,
    backend: str,
    backend_cfg: dict,
    output_path: Path,
) -> None:
    """Write full per-problem reasoning threads + content (no truncation).

    Both OpenRouter and Ollama backends populate `content` and `reasoning`;
    reasoning-mode models (GPT-OSS family, DeepSeek-R1, ollama thinking-mode)
    typically have non-empty `reasoning`, while regular models have it empty.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": summary.model,
        "backend": backend,
        "model_id": backend_cfg.get("model_id", ""),
        "dataset": summary.dataset,
        "prompt_file": summary.prompt_file,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "total": summary.total,
            "correct": summary.correct,
            "wrong": summary.wrong,
            "parse_errors": summary.parse_errors,
            "accuracy": summary.accuracy,
            "true_as_true": summary.true_as_true,
            "true_as_false": summary.true_as_false,
            "false_as_true": summary.false_as_true,
            "false_as_false": summary.false_as_false,
            "total_cost_usd": summary.total_cost,
            "total_input_tokens": summary.total_input_tokens,
            "total_output_tokens": summary.total_output_tokens,
            "avg_latency_s": summary.avg_latency,
        },
        "problems": [
            {
                "problem_id": r.problem_id,
                "expected": r.expected,
                "predicted": r.predicted,
                "correct": r.correct,
                "parse_ok": r.parse_ok,
                "raw_verdict": r.raw_verdict,
                "latency_s": round(r.latency_s, 3),
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "cost_usd": round(r.cost_usd, 6),
                "reasoning": r.reasoning,
                "content": r.content,
            }
            for r in summary.results
        ],
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"Reasoning written to: {output_path}")


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
        "--model", default=None,
        help="Model name from config/models.yaml (e.g., gpt-oss-120b). If omitted, prompts interactively."
    )
    parser.add_argument(
        "--backend", choices=["openrouter", "ollama"], default=None,
        help="Inference backend. If omitted, prompts interactively (unless only one is available for the model)."
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
        help="Output CSV path (default: results/<batch>/<model>_<backend>_<dataset>_<timestamp>.csv)"
    )
    parser.add_argument(
        "--output-dir", default=None,
        help="Batch output directory (e.g. results/20260407_1530_v4-sweep). "
             "If omitted, creates results/<YYYYMMDD_HHMM>/ automatically."
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
    models = config.get("models", {})

    # Model selection (interactive if --model not provided)
    model_name = args.model
    if model_name is None:
        model_name = prompt_select_model(models)
    elif model_name not in models:
        print(f"Error: unknown model '{model_name}'. Available: {', '.join(models.keys())}", file=sys.stderr)
        sys.exit(1)
    model_config = models[model_name]

    # Backend selection (interactive if --backend not provided)
    backend = args.backend
    if backend is None:
        backend = prompt_select_backend(model_name, model_config)
    elif backend not in model_config:
        avail = [b for b in ("openrouter", "ollama") if b in model_config]
        print(f"Error: backend '{backend}' not configured for {model_name}. Available: {', '.join(avail)}", file=sys.stderr)
        sys.exit(1)
    backend_cfg = model_config[backend]

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

    print(f"Model: {model_config.get('display_name', model_name)} | backend: {backend} | model_id: {backend_cfg['model_id']}")

    if args.dry_run:
        print("\n[DRY RUN] Skipping API calls.")

    # Run evaluation
    summary = asyncio.run(run_evaluation(
        problems, prompt_template, model_name, backend, backend_cfg, config, args.dry_run
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
            if args.output_dir:
                batch_dir = Path(args.output_dir)
            else:
                batch_dir = PROJECT_ROOT / "results" / time.strftime("%Y%m%d_%H%M")
            batch_dir.mkdir(parents=True, exist_ok=True)
            output_path = batch_dir / f"{model_name}_{backend}_{args.data}_{ts}.csv"
        write_csv(summary, output_path)
        write_reasoning_json(summary, backend, backend_cfg, output_path.with_suffix(".json"))


if __name__ == "__main__":
    main()
