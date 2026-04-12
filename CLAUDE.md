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

- `Training_data/` -- Official JSONL problem sets: `normal.jsonl` (1000), `hard1.jsonl` (69), `hard2.jsonl` (200), `hard3.jsonl` (400). Each record has `id`, `eq1_id`, `eq2_id`, `equation1`, `equation2`, `answer` (boolean). Equations use `*` for the binary operation.
- `Extra_training_data/` -- Community-contributed datasets:
  - `SAIRCommunityBench_v1.jsonl` (199) -- wider distribution (order 4-6), harder than official sets
  - `Hard5_order5.jsonl` (654) -- order-5 equations (5 operations), from Lean proofs
  - `full_2000_equations.jsonl` (1999) -- full dataset from which SAIRCommunityBench was sampled
  - `verification_data_with_citations.jsonl` (199) -- SAIRCommunityBench with Lean proof/countermodel citations
- `cheatsheets/` -- Versioned prompt+cheatsheet files (e.g. `v3.4.1_10KB_cheatsheet.md`, `v4_10KB_cheatsheet.md`)
- `results/` -- Organized by batch: `results/YYYYMMDD_HHMM_description/` containing CSV + JSON per run
  - `results/baselines/` -- Baseline (no cheatsheet) CSV results per model per dataset, plus `SUMMARY.md`
  - `results/iterations/` -- Per-iteration CSV results, named `v{N}_{model}_{dataset}.csv`
  - `results/20260406_2308_v4-all-models-hard/` -- Full v4 sweep: 7 models x 3 hard datasets (21 runs)
- `config/prompts/` -- Prompt templates (e.g. `v0_baseline.txt`)
- `config/models.yaml` -- Model configuration for eval harness
- `eval_harness.py` -- Evaluation harness script
- `Research/equations.txt` -- Full list of 4694 equational laws (uses `◇` operator)
- `Research/Raw_implication_graph.csv` -- Per-equation implication statistics (Implies, Implied by, Does not imply, etc.)
- `Blog_data/` -- Community intelligence synced from SAIR sources (see `Blog_data/README.md`):
  - `Blog_data/cheatsheets/` -- Community cheatsheets from the SAIR contributor-network API (one file per `publicCode`, plus `_network_snapshot.json` graph snapshot and `INDEX.md` navigation table)
  - `Blog_data/zulip/` -- Zulip thread dumps organized by stream (`math_distillation_challenge/`, `general/`, `prime_scales/`), with `INDEX.md` navigation table
  - Refreshed every 48h by `.github/workflows/sair-intel-refresh.yml` via `scripts/refresh_sair_intel.py`
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

## Current Results

### v4.1 cheatsheet -- 4-model hard sweep (2026-04-09)

v4.1_10KB_cheatsheet.md (10.2KB) evaluated on 4 models x hard1/hard2/hard3 via OpenRouter. All parse errors resolved via retries. Full results with confusion matrices in `results/v4.1_results.pdf`.

| Model | hard1 (69) | hard2 (200) | hard3 (400) | ALL (669) | Bias |
|-------|-----------|-------------|-------------|-----------|------|
| **gpt-oss-120b** | **54/69 (78.3%)** | 150/200 (75.0%) | **240/400 (60.0%)** | **444/669 (66.4%)** | Slight TRUE |
| **grok-4.1-fast** | 53/69 (76.8%) | **160/200 (80.0%)** | 237/400 (59.2%) | 450/669 (67.3%) | Balanced |
| gpt-oss-20b | 48/69 (69.6%) | 140/200 (70.0%) | 234/400 (58.5%) | 422/669 (63.1%) | Moderate TRUE |
| gemma-4-31b | 51/69 (73.9%) | 117/200 (58.5%) | 226/399 (56.6%) | 394/668 (59.0%) | Extreme FALSE |

**Key findings (v4 → v4.1 delta):**
- **GPT-OSS-120b massive improvement:** +34pp hard1, +22pp hard2, +14pp hard3 (was 43.9%/52.6%/46.1% in v4). Fixed by temperature=1.0 + max_tokens=65536
- **GPT-OSS-20b recovered:** 83 parse errors → 0 after temperature=1.0 fix. Accuracy +11-26pp across datasets
- **Grok steady:** +3.5pp on hard2 (80.0%), slight regression on hard3. Best overall at 67.3%
- **Gemma extreme FALSE bias:** T→F=244 (misses 76.5% of TRUE implications), only F→T=30 confabulations
- **Harness fixes:** temperature=1.0 for reasoning models, max_tokens=65536, per-request 180s timeout, null body guard, empty response retry, longer backoff [5,15,30]s

### v4 cheatsheet -- full hard sweep (2026-04-06)

v4_10KB_cheatsheet.md (8.8KB) evaluated on all 7 models x hard1/hard2/hard3 via OpenRouter:

| Model | hard1 (69) | hard2 (200) | hard3 (400) | Parse Err | Bias |
|-------|-----------|-------------|-------------|-----------|------|
| **grok-4.1-fast** | **53/68 (77.9%)** | **153/200 (76.5%)** | **242/400 (60.5%)** | 1 | Balanced |
| gemma-4-31b | 43/69 (62.3%) | 145/197 (73.6%) | 202/385 (52.5%) | 18 | TRUE bias |
| gemini-flash-lite | 51/69 (73.9%) | 104/200 (52.0%) | 225/400 (56.2%) | 0 | FALSE bias |
| deepseek-v3.2 | 45/69 (65.2%) | 101/200 (50.5%) | 206/400 (51.5%) | 0 | Total FALSE |
| llama-3.3-70b | 45/69 (65.2%) | 100/200 (50.0%) | 206/400 (51.5%) | 0 | Total FALSE |
| gpt-oss-20b | 38/65 (58.5%) | 76/174 (43.7%) | 179/358 (50.0%) | 72 | TRUE bias |
| gpt-oss-120b | 29/66 (43.9%) | 102/194 (52.6%) | 170/369 (46.1%) | 40 | Extreme TRUE |

**Key findings (from JSON failure analysis):**
- **Grok dominates** -- best on all 3 datasets, only model >60% on hard3. Most balanced TRUE/FALSE predictions
- **v4 creates polarized bias:** DeepSeek/Llama answer FALSE on 99%+ of problems; GPT-OSS answers TRUE on 85-91%
- **GPT-120b: 90% of failures from 1024-token truncation** -- reasoning cut off mid-step, no VERDICT emitted. Fixed in v4.1 with max_tokens=65536
- **Llama: pure lookup table** -- 99.7% of failures are identical "RULE: default false" boilerplate in 88 tokens
- **Gemini: fabricates heuristic rules** not in the cheatsheet ("rightmost exclusion", "count exclusion")
- **Community top: Betka 98% on hard200** with feature-first protocol + contradiction motifs C1-C14

### v1 cheatsheet (historical)

v1 cheatsheet (4.6KB) evaluated on normal (1000) and hard2 first-30:

| Model | normal | Baseline | Delta |
|-------|--------|----------|-------|
| grok-4.1-fast | 840/1000 (84%) | 320/1000 (32%) | +52pp |
| gpt-oss-120b | 629/1000 (63%) | 519/1000 (52%) | +11pp |
| llama-3.3-70b | 500/1000 (50%) | 367/1000 (37%) | +13pp |
| gemini-flash-lite | 502/1000 (50%) | 498/1000 (50%) | +0pp |

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
