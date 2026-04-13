# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

SAIR Mathematics Distillation Challenge -- Equational Theories Stage 1. Build a compact prompt+cheatsheet (max 10KB) that maximizes LLM correctness on "Does Equation 1 imply Equation 2 over all magmas?" (TRUE/FALSE). Submission is a complete prompt with `{{ equation1 }}` and `{{ equation2 }}` placeholders. Deadline: April 20, 2026.

## Architecture

Three-layer cloud-first system (no local GPU):

- **Orchestration:** Claude Max 200K via Claude Code -- cheatsheet generation, compression, error analysis, AlphaEvolve-style search (free)
- **Evaluation:** `eval_harness.py` -- loads JSONL problems, substitutes equations into prompt templates, calls cloud models via OpenRouter API, parses `VERDICT: TRUE`/`VERDICT: FALSE` from responses, outputs per-problem CSV + accuracy summary
- **Inference:** OpenRouter API cloud models -- `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `google/gemma-4-31b-it`, `meta-llama/llama-3.3-70b-instruct`, `deepseek/deepseek-v3.2`, `google/gemini-3.1-flash-lite-preview`, `x-ai/grok-4.1-fast`. Local Ollama for gpt-oss-20b, gemma-4-31b, llama-3.3-70b

## Repository Structure

- `training_data/` -- Official JSONL problem sets: `normal.jsonl` (1000), `hard1.jsonl` (69), `hard2.jsonl` (200), `hard3.jsonl` (400). Each record has `id`, `eq1_id`, `eq2_id`, `equation1`, `equation2`, `answer` (boolean). Equations use `*` for the binary operation.
- `extra_training_data/` -- Community-contributed datasets:
  - `SAIRCommunityBench_v1.jsonl` (199) -- wider distribution (order 4-6), harder than official sets
  - `Hard5_order5.jsonl` (654) -- order-5 equations (5 operations), from Lean proofs
  - `full_2000_equations.jsonl` (1999) -- full dataset from which SAIRCommunityBench was sampled
  - `verification_data_with_citations.jsonl` (199) -- SAIRCommunityBench with Lean proof/countermodel citations
- `cheatsheets/` -- Versioned prompt+cheatsheet files (e.g. `v4.1_10KB_cheatsheet.md`, `v5.2_10KB_cheatsheet.md`, `v.Opus-1_10KB_cheatsheet.md`)
- `results/` -- Organized by batch: `results/YYYYMMDD_HHMM_description/` containing CSV + JSON per run
  - `results/baselines/` -- Baseline (no cheatsheet) CSV results per model per dataset, plus `SUMMARY.md`
  - `results/iterations/` -- Per-iteration CSV results, named `v{N}_{model}_{dataset}.csv`
  - `results/20260406_2308_v4-all-models-hard/` -- Full v4 sweep: 7 models x 3 hard datasets (21 runs)
  - `results/20260410_v4.1-official/` -- v4.1 official-mode sweep (mirrors SAIR evaluation_models.json)
  - `results/20260412_v5.2_official/` -- v5.2 official-mode sweep
  - **`results/Opus_research/`** -- All Opus-thread work (new convention): opus-solver raw-reasoning runs, v.Opus-N cheatsheet sweeps, opus-informed analysis PDFs. New Opus-related dirs go here, not at `results/` root.
- `config/prompts/` -- Prompt templates (e.g. `v0_baseline.txt`)
- `config/models.yaml` -- Model configuration for eval harness
- `eval_harness.py` -- Evaluation harness script
- `scripts/` -- Standalone utilities:
  - `scripts/report_pdf.py` -- Shared PDF report helper; per-report render scripts import `start`, `fmt_pct`, `ReportPDF` instead of duplicating an FPDF subclass. See `.claude/skills/generating-result-pdfs/` for the convention.
  - `scripts/run_opus_benchmark.py` -- Opus-solver benchmark driver (spawns `claude -p --agent opus-solver` subprocesses, parses verdicts via `eval_harness.parse_verdict`)
  - `scripts/refresh_sair_intel.py` -- SAIR Zulip + contributor-network sync (called by `.github/workflows/sair-intel-refresh.yml` every 48h)
- `analysis/error_taxonomy.py` -- Failure-mode classifier for result JSONs
- `tests/` -- Pytest suite (`test_parse_verdict.py`, `test_official_overrides.py`, `test_opus_agents.py`)
- `research/equations.txt` -- Full list of 4694 equational laws (uses `◇` operator)
- `research/Raw_implication_graph.csv` -- Per-equation implication statistics (Implies, Implied by, Does not imply, etc.)
- `blog_data/` -- Community intelligence synced from SAIR sources (see `blog_data/README.md`):
  - `blog_data/cheatsheets/` -- Community cheatsheets from the SAIR contributor-network API (one file per `publicCode`, plus `_network_snapshot.json` graph snapshot and `INDEX.md` navigation table)
  - `blog_data/zulip/` -- Zulip thread dumps organized by stream (`math_distillation_challenge/`, `general/`, `prime_scales/`), with `INDEX.md` navigation table
  - Refreshed every 48h by `.github/workflows/sair-intel-refresh.yml` via `scripts/refresh_sair_intel.py`
- `meeting_notes/` -- Team meeting notes (`Meetings_Notes_DD-MM-YY.md`)
- `docs/` -- Reference material (`docs/superpowers/` etc.)
- `.claude/` -- Project-scoped Claude Code config:
  - `.claude/agents/` -- Custom subagent definitions (`opus-solver.md`, `opus-orchestrator.md`, `sair-community-intel-updater.md`, `code-review-sentinel.md`)
  - `.claude/skills/` -- Project skills (e.g. `generating-result-pdfs/` for the PDF helper convention)
- `Plan.md` -- Full project plan with phases, cost estimates, architecture, and team responsibilities

## Key Domain Knowledge

- A **magma** is a set with a single binary operation (no axioms like associativity or commutativity assumed)
- 4694 equational laws generate 22M+ potential implications; the Equational Theories Project (Terence Tao) resolved all of them
- Evaluation output must contain `VERDICT: TRUE` or `VERDICT: FALSE` (colon separator, not equals). Verdict must be the first output line.
- Different models need different cheatsheet formats: GPT models respond to symbolic solvers; Llama models respond to algebraic family atlases
- Llama has a FALSE bias with verbose "mathematician persona" prompts; use simplified task framing
- **Confabulation is the #1 failure mode for GPT models:** GPT-OSS-120b finds correct counterexamples then "talks itself out" with fluent wrong proofs. GPT-OSS-20b misfires singleton/collapse heuristic on 58% of failures
- **Total FALSE bias dominates DeepSeek/Llama/Gemini:** with v4 cheatsheet, these models answer FALSE on 99%+ of problems (0-1% TRUE recall). They treat the cheatsheet as a pure lookup table
- **Gemini hallucinates structural rules** not in the cheatsheet (e.g. "rightmost exclusion", "count exclusion") -- 53% of its failures
- **Token truncation kills GPT-OSS models:** at 1024 max_tokens, ~90% of GPT-120b failures were truncated mid-reasoning with no VERDICT emitted. Now set to 65536 for reasoning models
- **Reasoning models require temperature=1.0:** gpt-oss-20b/120b silently return empty responses (0 tokens) with temperature=0 on OpenRouter. Per-model `params` in `config/models.yaml` override the global default
- **Eval is confirmed 50/50 TRUE/FALSE** by Terence Tao -- default-FALSE is correctly calibrated

## Cheatsheet Design Rules (community-validated + v4 failure analysis)

- **VERDICT-first output format:** Emit `VERDICT: TRUE` or `VERDICT: FALSE` as the FIRST line, then reasoning after. Eliminates all token-truncation parse errors. Community consensus (Betka, Heath, stokarz).
- **Counterexample hard-stop with named rule lock:** Once a counterexample is found, cite the rule, output FALSE immediately, stop all further reasoning. GPT-120b finds correct counterexamples then overrides them with fluent wrong proofs. Betka/stokarz both use this pattern.
- **Feature-first protocol:** Compute source features (rhsVars, topShape, Lx, Rx, xTop, square) BEFORE checking motifs. Our v4 lets models skip feature computation and pattern-match rule names instead. Betka achieves 98% on hard200 with this approach.
- **Checklist > reasoning:** Rigid structured protocols with numbered rules outperform free-form mathematical reasoning. Structure the cheatsheet as a decision procedure, not a reference document.
- **Force minimal reasoning before default-FALSE:** Llama outputs "RULE: default false" in 88 tokens with zero analysis. Add a forced substitution check (x=y=z) before fallback to catch trivial TRUE cases.
- **Spine Isolation Theorem (McKenna):** "A pure left-spine equation can only imply equations that are themselves pure left-spine of equal or greater depth." Validated on 1.54M pairs with zero exceptions. Fixes +32 hard3 problems.
- **Generalization over benchmark-saturation:** Cheatsheets tuned to one dataset don't generalize. Always test on multiple datasets (hard1, hard2, hard3, SAIRCommunityBench, Hard5).
- **Model-specific framing:** Llama needs minimal task framing (no "mathematician persona"). GPT needs symbolic solver format with rule locks. Gemini needs explicit "do not invent rules not listed here" guardrail.

## External Resources

- Full raw implications table: teorth.github.io/equational_theories/implications/
- Graphiti (22M-edge implication graph visualization): teorth.github.io/equational_theories/graphiti/
- Tao's AlphaEvolve predictors: github.com/teorth/equational_theories/blob/main/scripts/predictor/
- Cheat-sheet ICL reference implementation: github.com/CyberAgentAILab/cheat-sheet-icl
- Knuckledragger (Python proof assistant with Z3/Vampire/Prover9): github.com/philzook58/knuckledragger
- HuggingFace official dataset: SAIRfoundation/equational-theories-selected-problems
- HuggingFace ETP dataset (adamtopaz): huggingface.co/datasets/adamtopaz/equational_dataset
- Order-5 ETP data: github.com/vlad902/equational_theories/tree/order5
- SAIR Playground: competition.sair.foundation (10 credits/day)
