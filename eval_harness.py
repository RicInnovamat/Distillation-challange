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
from enum import Enum
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
# VERDICT parsing — priority-based extractor ported from SAIR's official
# judge.py (github.com/SAIRcompetition/equational-theories-stage1-judge)
# so our local grader matches the Stage 1 eval exactly.
#
# Three marker types, in descending priority:
#   3. boxed    — \boxed{TRUE} / \boxed{FALSE}
#   2. labeled  — VERDICT:/ANSWER:/FINAL ANSWER:/RESULT:/OUTPUT_RESULT:/\text{}
#   1. line     — first or last non-empty line is bare TRUE/FALSE
# Tie-break: highest priority wins; within same priority, last occurrence wins.
# Instruction preambles like "VERDICT: TRUE or FALSE" and "VERDICT: TRUE/FALSE"
# are detected and ignored.
# ---------------------------------------------------------------------------

_BOXED_START_RE = re.compile(r"(?i)\\+boxed\s*\{")
_VERDICT_RE = re.compile(r"(?i)\bVERDICT\s*[:：]\s*(TRUE|FALSE)\b")
_ANSWER_RE = re.compile(
    r"(?i)\b(?:FINAL\s+ANSWER|ANSWER|OUTPUT_RESULT|RESULT)\s*[:：=-]\s*(TRUE|FALSE)\b"
)
_LATEX_TEXT_RE = re.compile(r"(?i)\\text\s*\{\s*(TRUE|FALSE)\s*\}")
_LINE_RE = re.compile(
    r"(?i)^\s*(?:FINAL\s+ANSWER\s*[:：=-]\s*)?(TRUE|FALSE)\s*[.!?]*\s*$"
)
_LATEX_WRAPPER_RE = re.compile(
    r"(?is)^\\(?:text|mathrm|mathbf|operatorname)\s*\{(.+)\}$"
)


class _VerdictSource(Enum):
    LINE = 1
    LABELED = 2
    BOXED = 3


@dataclass
class _VerdictCandidate:
    value: bool
    source: _VerdictSource
    index: int


def _strip_markdown(s: str) -> str:
    return s.replace("***", "").replace("**", "").replace("__", "").replace("`", "")


def _parse_bool_label(label: str) -> bool | None:
    u = label.upper()
    if u == "TRUE":
        return True
    if u == "FALSE":
        return False
    return None


def _is_instruction_clause(response: str, match_end: int) -> bool:
    """Detect 'VERDICT: TRUE or FALSE' and 'VERDICT: TRUE/FALSE' instruction hints."""
    after = response[match_end:].split("\n", 1)[0].lstrip()
    if after[:2].upper() == "OR":
        rest = after[2:]
        return not rest or rest[0].isspace()
    if after.startswith("/"):
        return bool(re.match(r"(?i)(TRUE|FALSE)\b", after[1:].lstrip()))
    return False


def _parse_boxed_content(token: str) -> bool | None:
    STRIP = " \t\r\n.,;:!?$()[]"
    current = token.strip()
    for _ in range(4):
        current = current.strip(STRIP)
        if current.upper() == "ANSWER":
            return None
        verdict = _parse_bool_label(current)
        if verdict is not None:
            return verdict
        m = _LATEX_WRAPPER_RE.match(current)
        if m:
            current = m.group(1)
            continue
        break
    return None


def _extract_boxed(response: str, out: list) -> None:
    for m in _BOXED_START_RE.finditer(response):
        depth = 1
        content_start = m.end()
        content_end = None
        for i, ch in enumerate(response[content_start:]):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    content_end = content_start + i
                    break
        if content_end is None:
            continue
        value = _parse_boxed_content(response[content_start:content_end])
        if value is not None:
            out.append(_VerdictCandidate(value=value, source=_VerdictSource.BOXED, index=m.start()))


def _extract_labeled(response: str, out: list) -> None:
    for pattern in (_VERDICT_RE, _ANSWER_RE, _LATEX_TEXT_RE):
        for m in pattern.finditer(response):
            if _is_instruction_clause(response, m.end()):
                continue
            value = _parse_bool_label(m.group(1))
            if value is not None:
                out.append(_VerdictCandidate(value=value, source=_VerdictSource.LABELED, index=m.start()))


def _extract_leading_line(response: str, out: list) -> None:
    first = next((line for line in response.splitlines() if line.strip()), None)
    if first is None:
        return
    m = _LINE_RE.match(first)
    if not m:
        return
    value = _parse_bool_label(m.group(1))
    if value is not None:
        out.append(_VerdictCandidate(value=value, source=_VerdictSource.LINE, index=0))


def _extract_trailing_line(response: str, out: list) -> None:
    last = next((line for line in reversed(response.splitlines()) if line.strip()), None)
    if last is None:
        return
    m = _LINE_RE.match(last)
    if not m:
        return
    value = _parse_bool_label(m.group(1))
    if value is not None:
        out.append(_VerdictCandidate(value=value, source=_VerdictSource.LINE, index=len(response)))


def _best_verdict_candidate(candidates: list) -> _VerdictCandidate | None:
    if not candidates:
        return None
    top = max(c.source.value for c in candidates)
    return max((c for c in candidates if c.source.value == top), key=lambda c: c.index)


def parse_verdict(text: str | None) -> tuple[bool | None, str]:
    """Extract TRUE/FALSE verdict from a model response.

    Returns (prediction, raw_match_description). The description encodes the
    marker tier ("boxed"/"labeled"/"line") and the verdict, for CSV debugging.
    """
    if not text:
        return None, ""
    cleaned = _strip_markdown(text)
    candidates: list[_VerdictCandidate] = []
    _extract_boxed(cleaned, candidates)
    _extract_labeled(cleaned, candidates)
    _extract_leading_line(cleaned, candidates)
    _extract_trailing_line(cleaned, candidates)
    chosen = _best_verdict_candidate(candidates)
    if chosen is None:
        return None, ""
    raw = f"{chosen.source.name.lower()}:{'TRUE' if chosen.value else 'FALSE'}"
    return chosen.value, raw


# ---------------------------------------------------------------------------
# Official Stage 1 eval mode — payload overrides
# ---------------------------------------------------------------------------
#
# When --official-mode is set, the harness mirrors SAIR's official
# evaluation_models.json exactly (except temperature, which the user has
# opted to leave under their existing config). The 3 official models each
# declare an `official_params` block in models.yaml with:
#
#   provider:         "<slug>[/<quantization>]"   e.g. "deepinfra/bf16"
#   reasoning_effort: "low" | "none" | ...         optional
#   seed:             int                          optional
#   max_tokens:       int                          optional
#
# build_official_overrides() turns that block into OpenRouter payload fields.

# OpenRouter provider display-name lookup (mirrors SAIR models.py _PROVIDER_NAMES).
# Only the providers used by the 3 official models are listed; unknown slugs
# pass through unchanged so display names like "DeepInfra" work directly.
_OFFICIAL_PROVIDER_DISPLAY_NAMES: dict[str, str] = {
    "deepinfra": "DeepInfra",
    "novita": "Novita",
}


def _parse_provider_tag(tag: str) -> tuple[str, str | None]:
    """Split 'deepinfra/bf16' → ('deepinfra', 'bf16'); bare 'deepinfra' → ('deepinfra', None)."""
    if "/" in tag:
        slug, quant = tag.split("/", 1)
        return slug.strip(), quant.strip()
    return tag.strip(), None


def _provider_display_name(slug: str) -> str:
    return _OFFICIAL_PROVIDER_DISPLAY_NAMES.get(slug.lower(), slug)


def build_official_overrides(model_config: dict, allow_fallbacks: bool = False) -> dict:
    """Build OpenRouter payload fragments from a model's `official_params` block.

    Returns a dict containing any of: `provider`, `reasoning`, `seed`, `max_tokens`.
    Temperature is deliberately never touched — the caller keeps whatever the
    normal params-resolution produced.

    `allow_fallbacks` defaults to False (strict provider pinning, matching SAIR's
    evaluation_models.json). Set True via `--official-fallbacks` to let OpenRouter
    route past the pinned provider when it's capacity-constrained — the provider
    still stays first in `provider.order`, it's just not exclusive.

    Raises ValueError if the model config has no `official_params` section.
    """
    params = model_config.get("official_params")
    if not params:
        raise ValueError(
            "model has no `official_params` block — not one of the 3 official "
            "Stage 1 evaluation models, cannot use --official-mode"
        )

    overrides: dict = {}

    provider_tag = params.get("provider")
    if provider_tag:
        slug, quant = _parse_provider_tag(provider_tag)
        order = [_provider_display_name(slug)]
        quants: list[str] = [quant] if quant else []
        # When fallbacks are enabled, append any `fallback_providers` from
        # the official_params block. This is the only way OpenRouter will
        # actually route past a rate-limited primary — `allow_fallbacks:
        # true` alone with a single-item order does nothing.
        #
        # Fallback entries support the same `slug/quant` syntax as the
        # primary provider; any distinct quant values are unioned into the
        # `quantizations` filter so mixed-quant fallback pools (e.g. three
        # bf16 providers plus an fp8 alternative) all get through. Without
        # this, a stricter quant filter would silently exclude any fallback
        # served under a different quantization.
        if allow_fallbacks:
            for fb in params.get("fallback_providers", []):
                fb_slug, fb_quant = _parse_provider_tag(fb)
                name = _provider_display_name(fb_slug)
                if name not in order:
                    order.append(name)
                if fb_quant and fb_quant not in quants:
                    quants.append(fb_quant)
        prov: dict = {"order": order}
        if quants:
            prov["quantizations"] = quants
        prov["allow_fallbacks"] = allow_fallbacks
        overrides["provider"] = prov

    reasoning_effort = params.get("reasoning_effort")
    if reasoning_effort is not None:
        overrides["reasoning"] = {"effort": reasoning_effort}

    if "seed" in params:
        overrides["seed"] = params["seed"]

    if "max_tokens" in params:
        overrides["max_tokens"] = params["max_tokens"]

    return overrides


# ---------------------------------------------------------------------------
# OpenRouter API client
# ---------------------------------------------------------------------------

SEMAPHORE = None
MAX_RETRIES = 5
RETRY_DELAYS = [5, 15, 30, 60, 120]  # handles persistent upstream 429s on BYOK providers
HARD_TIMEOUT_S = 300  # aiohttp total timeout per API call. Matches SAIR judge
                      # llm.py recommended httpx timeout. Reasoning-mode gemma
                      # (effort=low) runs 30-67s per call under concurrent load;
                      # the old 180s tripped on tail latency and caused retry
                      # storms against Novita.


async def call_openrouter(
    session: aiohttp.ClientSession,
    model_id: str,
    prompt: str,
    api_key: str,
    base_url: str,
    temperature: float,
    max_tokens: int,
    extra_payload: dict | None = None,
) -> dict:
    """Call OpenRouter chat completion API with retry logic.

    `extra_payload` is merged on top of the base request body — used by
    --official-mode to inject provider pinning, reasoning, and seed.
    `max_tokens` inside `extra_payload` overrides the positional argument.
    """
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
    if extra_payload:
        payload.update(extra_payload)

    # The SEMAPHORE wraps only the HTTP request itself, not the retry-sleep.
    # Holding the slot during `asyncio.sleep(delay)` would serialize retries
    # behind a single slow provider: at concurrency N, N tasks in sustained
    # retry-sleep cycles lock out all other requests. Releasing the slot
    # between attempts lets healthy tasks make progress while retrying ones
    # are backed off.
    for attempt in range(MAX_RETRIES):
        delay = RETRY_DELAYS[min(attempt, len(RETRY_DELAYS) - 1)]
        retry_msg: str | None = None
        data: dict | None = None
        try:
            async with SEMAPHORE:
                async with session.post(url, json=payload, headers=headers, timeout=aiohttp.ClientTimeout(total=HARD_TIMEOUT_S)) as resp:
                    status = resp.status
                    if status == 429:
                        retry_msg = f"Rate limited, waiting {delay}s..."
                    elif status >= 500:
                        retry_msg = f"Server error {status}, retrying in {delay}s..."
                    else:
                        resp.raise_for_status()
                        data = await resp.json()
            # Semaphore released here — decisions/sleeps happen outside.
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  Request error: {e}, retrying in {delay}s...", file=sys.stderr)
                await asyncio.sleep(delay)
                continue
            raise

        if retry_msg is None:
            # HTTP succeeded with 200 — validate payload shape.
            if data is None:
                retry_msg = f"Null response body, retrying in {delay}s..."
            elif "error" in data:
                # OpenRouter returns HTTP 200 with an `error` field for
                # transient upstream failures (e.g. code 504 "operation
                # was aborted", code 429 passed through from the provider).
                # Treat any 5xx or 408/429 error code as retriable.
                err = data.get("error") or {}
                err_code = err.get("code")
                err_msg = err.get("message", "")
                transient_codes = {408, 429, 500, 502, 503, 504}
                if isinstance(err_code, int) and err_code in transient_codes:
                    retry_msg = f"Upstream error code={err_code} ({err_msg}), retrying in {delay}s..."
                # else: permanent error, fall through and let evaluate_problem
                # surface it to the user.
            else:
                usage = data.get("usage", {})
                choices = data.get("choices", [])
                content = ""
                finish_reason = None
                if choices:
                    choice = choices[0] or {}
                    content = (choice.get("message", {}).get("content", "") or "").strip()
                    finish_reason = choice.get("finish_reason")
                tok_out = usage.get("completion_tokens", 0)
                if not content:
                    # Reasoning models (gemma-4-31b at effort=low) emit tokens
                    # into a hidden `reasoning` field; `content` comes back empty
                    # when the budget is exhausted (finish_reason=length) or the
                    # model skips the final answer (finish_reason=stop). Mirrors
                    # SAIR judge llm.py: retry once on any empty text response.
                    retry_msg = (
                        f"Empty content (finish={finish_reason}, out_tok={tok_out}), "
                        f"retrying in {delay}s..."
                    )

        if retry_msg is None:
            return data

        print(f"  {retry_msg}", file=sys.stderr)
        await asyncio.sleep(delay)

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
    extra_payload: dict | None = None,
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
                session, model_id, rendered, api_key, base_url, temperature, max_tokens,
                extra_payload=extra_payload,
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
    official_mode: bool = False,
    official_fallbacks: bool = False,
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
    model_cfg_root = config.get("models", {}).get(model_name, {})
    model_params = model_cfg_root.get("params", {})
    temperature = model_params.get("temperature", defaults.get("temperature", 0.0))
    max_tokens = model_params.get("max_tokens", defaults.get("max_tokens", 1024))
    concurrency = defaults.get("concurrency", 10)

    # Official Stage 1 mode: pin provider, reasoning effort, seed, and
    # (optionally) override max_tokens to mirror SAIR's evaluation_models.json.
    # Temperature is deliberately left untouched by --official-mode.
    extra_payload: dict | None = None
    if official_mode:
        if backend != "openrouter":
            print(
                f"Error: --official-mode requires --backend openrouter (got {backend}).",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            extra_payload = build_official_overrides(
                model_cfg_root, allow_fallbacks=official_fallbacks
            )
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
        if "max_tokens" in extra_payload:
            max_tokens = extra_payload["max_tokens"]
        # Reasoning-mode models (gemma-4-31b-it at effort=low, gpt-oss-120b at
        # effort=low) run 15-70s per call. At concurrency=10, the pinned bf16
        # providers (Novita, Parasail, Venice) hit 429 server_overload within
        # seconds and the whole batch stalls in retry storms. SAIR's judge is
        # effectively concurrency=1 — 3 is already 3x theirs while keeping
        # wall-clock reasonable on 69-400 problem datasets.
        reasoning = extra_payload.get("reasoning") or {}
        reasoning_effort = reasoning.get("effort") if isinstance(reasoning, dict) else None
        if reasoning_effort and reasoning_effort != "none" and concurrency > 3:
            print(
                f"[official-mode] reasoning.effort={reasoning_effort} — capping "
                f"concurrency {concurrency} → 3 to avoid provider 429 stampedes"
            )
            concurrency = 3
        print(
            f"[official-mode] overrides for {model_name}: "
            f"{json.dumps(extra_payload, separators=(',', ':'))}"
        )

    SEMAPHORE = asyncio.Semaphore(concurrency)

    summary = RunSummary(model=f"{model_name} ({backend})", dataset="", prompt_file="")

    ssl_ctx = ssl.create_default_context(cafile=certifi.where())
    connector = aiohttp.TCPConnector(ssl=ssl_ctx)
    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            evaluate_problem(
                session, p, prompt_template, backend, backend_cfg,
                api_key, base_url, temperature, max_tokens, dry_run,
                extra_payload=extra_payload,
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
    parser.add_argument(
        "--official-mode", action="store_true",
        help="Mirror SAIR's official Stage 1 evaluation_models.json: provider "
             "pinning, reasoning effort, seed, and max_tokens=8192 for the 3 "
             "official models (gpt-oss-120b, llama-3.3-70b, gemma-4-31b). "
             "Temperature is NOT changed. Requires --backend openrouter and "
             "a model with an `official_params` block in models.yaml."
    )
    parser.add_argument(
        "--official-fallbacks", action="store_true",
        help="When used with --official-mode, set allow_fallbacks=True so "
             "OpenRouter can route past the pinned provider if it's capacity-"
             "constrained. The pinned provider stays first in provider.order. "
             "Use this when a provider like Novita is returning persistent "
             "server_overload errors. Diverges slightly from official config."
    )
    parser.add_argument(
        "--call-timeout", type=int, default=None,
        help="Per-request HTTP hard timeout in seconds (default: 180). "
             "Raise this when a pinned provider (e.g. Novita) has long tail "
             "latencies under concurrent load."
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
    if args.call_timeout:
        global HARD_TIMEOUT_S
        HARD_TIMEOUT_S = args.call_timeout
        print(f"HTTP call timeout overridden to {HARD_TIMEOUT_S}s")

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
        problems, prompt_template, model_name, backend, backend_cfg, config,
        args.dry_run, official_mode=args.official_mode,
        official_fallbacks=args.official_fallbacks,
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
