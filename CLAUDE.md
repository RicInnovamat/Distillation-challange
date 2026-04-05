# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

SAIR Mathematics Distillation Challenge -- Equational Theories Stage 1. Build a compact prompt+cheatsheet (max 10KB) that maximizes LLM correctness on "Does Equation 1 imply Equation 2 over all magmas?" (TRUE/FALSE). Submission is a complete prompt with `{{ equation1 }}` and `{{ equation2 }}` placeholders. Deadline: April 20, 2026.

## Architecture

Three-layer cloud-first system (no local GPU):

- **Orchestration:** Claude Max 200K via Claude Code -- cheatsheet generation, compression, error analysis, AlphaEvolve-style search (free)
- **Evaluation:** `eval_harness.py` -- loads JSONL problems, substitutes equations into prompt templates, calls cloud models via OpenRouter API, parses `VERDICT: TRUE`/`VERDICT: FALSE` from responses, outputs per-problem CSV + accuracy summary
- **Inference:** OpenRouter API cloud models -- `openai/gpt-oss-120b`, `meta-llama/llama-3.3-70b-instruct`, `google/gemini-3.1-flash-lite-preview`, `x-ai/grok-4.1-fast`. Fallbacks: GroqCloud, Cerebras free tier

## Repository Structure

- `Training_data/` -- Official JSONL problem sets: `normal.jsonl` (1000), `hard1.jsonl` (69), `hard2.jsonl` (200), `hard3.jsonl` (400). Each record has `id`, `eq1_id`, `eq2_id`, `equation1`, `equation2`, `answer` (boolean). Equations use `*` for the binary operation.
- `Extra_training_data/` -- Community-contributed datasets:
  - `SAIRCommunityBench_v1.jsonl` (199) -- wider distribution (order 4-6), harder than official sets
  - `Hard5_order5.jsonl` (654) -- order-5 equations (5 operations), from Lean proofs
  - `full_2000_equations.jsonl` (1999) -- full dataset from which SAIRCommunityBench was sampled
  - `verification_data_with_citations.jsonl` (199) -- SAIRCommunityBench with Lean proof/countermodel citations
- `cheatsheets/` -- Versioned prompt+cheatsheet files (e.g. `v1_cheatsheet.txt`, 4.6KB)
- `results/baselines/` -- Baseline (no cheatsheet) CSV results per model per dataset, plus `SUMMARY.md`
- `results/iterations/` -- Per-iteration CSV results, named `v{N}_{model}_{dataset}.csv`
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
- **Confabulation is the #1 failure mode:** models fabricate counterexamples to claim FALSE when the answer is TRUE. Gemini and Llama confabulate on ~100% of TRUE problems; GPT on ~31%; Grok on <1%
- **FALSE bias is universal** across all models at baseline; cheatsheets must specifically help models recognize TRUE implications

## Cheatsheet Design Rules (community-validated)

- **Counterexample finality:** GPT models find correct counterexamples then "talk themselves out of it" with plausible but wrong proofs. The cheatsheet MUST include: "Once a counterexample is found, output FALSE immediately. Do not attempt further proof."
- **Checklist > reasoning:** Rigid structured protocols with numbered rules outperform free-form mathematical reasoning. Structure the cheatsheet as a decision procedure, not a reference document.
- **Model-specific framing:** Llama needs minimal task framing (no "mathematician persona"). GPT needs symbolic solver format. Prepare both tracks.
- **Generalization over benchmark-saturation:** Cheatsheets tuned to one dataset don't generalize. Always test on multiple datasets (hard1, hard2, hard3, SAIRCommunityBench, Hard5).

## Current Results (v1 cheatsheet)

v1 cheatsheet (4.6KB) evaluated on normal (1000) and hard2 first-30 problems:

| Model | normal | Baseline | Delta | hard2_30 | Baseline | Delta |
|-------|--------|----------|-------|----------|----------|-------|
| grok-4.1-fast | 840/1000 (84%) | 320/1000 (32%) | +52pp | 12/30 (40%) | 11/30 (37%) | +3pp |
| gpt-oss-120b | 629/1000 (63%) | 519/1000 (52%) | +11pp | 19/30 (63%) | 18/30 (60%) | +3pp |
| llama-3.3-70b | 500/1000 (50%) | 367/1000 (37%) | +13pp | 15/30 (50%) | 11/30 (37%) | +13pp |
| gemini-flash-lite | 502/1000 (50%) | 498/1000 (50%) | +0pp | 15/30 (50%) | 15/30 (50%) | +0pp |

**Key findings:** Grok is the strongest model (+52pp lift). Confabulation (fabricated counterexamples) is the dominant failure: Gemini/Llama confabulate on 100% of TRUE problems. Grok has low confabulation (<1%) but 15% parse failures from timeouts.

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
