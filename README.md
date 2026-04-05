# SAIR Mathematics Distillation Challenge -- Equational Theories Stage 1

Competition entry for the [SAIR Mathematics Distillation Challenge](https://competition.sair.foundation/competitions/mathematics-distillation-challenge-equational-theories-stage1/overview), organized by [Terence Tao](https://terrytao.wordpress.com/2026/03/13/mathematics-distillation-challenge-equational-theories/) and the SAIR Foundation.

## Challenge

Build a compact prompt + cheatsheet (**max 10KB**) that maximizes LLM correctness on equational implication problems over magmas:

> *Given two equational laws, does Equation 1 imply Equation 2 over all magmas?*

A [magma](https://en.wikipedia.org/wiki/Magma_(algebra)) is a set with a single binary operation -- no associativity, commutativity, or identity assumed. The [Equational Theories Project](https://teorth.github.io/equational_theories/) catalogued 4,694 such laws and resolved all 22 million+ pairwise implications.

**Stage 1** asks for a TRUE/FALSE verdict only. **Stage 2** (May 2026) will require counterexamples, Lean proofs, or calibrated probabilities.

## Team

| Member | Role |
|--------|------|
| Andrea | Architecture, infrastructure, compute |
| Riccardo | Methodology, platform, submission |
| Tommaso | Research, mathematical content |

## Repository Structure

```
├── Plan.md                  # Project plan (phases, architecture, costs, timeline)
├── Meetings_Notes_*.md      # Team meeting notes and decisions
├── eval_harness.py          # Evaluation harness (JSONL → model API → CSV + accuracy)
├── config/
│   ├── models.yaml          # Model configuration for eval harness
│   └── prompts/             # Prompt templates (v0_baseline.txt, etc.)
├── cheatsheets/             # Versioned prompt+cheatsheet files
│   └── v1_cheatsheet.txt    # Current best cheatsheet (4.6KB)
├── results/
│   ├── baselines/           # Baseline (no cheatsheet) results per model/dataset + SUMMARY.md
│   └── iterations/          # Per-iteration results: v{N}_{model}_{dataset}.csv
├── Training_data/           # Official problem sets (JSONL)
│   ├── normal.jsonl         # 1000 problems (500 TRUE / 500 FALSE)
│   ├── hard1.jsonl          # 69 problems (deduplicated hard set)
│   ├── hard2.jsonl          # 200 problems (100 TRUE / 100 FALSE)
│   └── hard3.jsonl          # 400 problems (195 TRUE / 205 FALSE)
├── Extra_training_data/     # Community-contributed datasets
│   ├── SAIRCommunityBench_v1.jsonl  # 199 problems (order 4-6, harder distribution)
│   ├── Hard5_order5.jsonl           # 654 problems (order-5 equations)
│   ├── full_2000_equations.jsonl    # 1999 problems (full community set)
│   └── verification_data_with_citations.jsonl  # 199 problems with Lean proof citations
├── Research/
│   ├── equations.txt        # All 4694 equational laws
│   └── Raw_implication_graph.csv  # Per-equation implication statistics
└── Blog_data/               # Community intelligence (see Blog_data/README.md)
    ├── cheatsheets/         # Community cheatsheets from SAIR contributor network
    └── zulip/               # Zulip thread dumps, organized by stream
```

## Data Format

Each problem in the JSONL files has the following schema:

```json
{
  "id": "normal_0001",
  "eq1_id": 2918,
  "eq2_id": 1911,
  "equation1": "x = ((y * (x * y)) * z) * w",
  "equation2": "x = (y * (x * z)) * (y * w)",
  "answer": true
}
```

The full dataset is also available on HuggingFace: [SAIRfoundation/equational-theories-selected-problems](https://huggingface.co/datasets/SAIRfoundation/equational-theories-selected-problems).

## Architecture

All model inference runs in the cloud via [OpenRouter](https://openrouter.ai/). No local GPU required.

| Layer | Tool | Purpose |
|-------|------|---------|
| Orchestration | Claude Max 200K | Cheatsheet generation, compression, error analysis |
| Evaluation | `eval_harness.py` | Batch evaluation: substitute equations → call model → parse verdict → score |
| Inference | OpenRouter API | GPT-OSS-120b, Llama 3.3 70b, Gemini Flash Lite, Grok 4.1 Fast |

## Results

### Baseline (no cheatsheet)

| Model | normal (1000) | hard1 (69) | hard2 (200) | hard3 (400) |
|-------|:---:|:---:|:---:|:---:|
| grok-4.1-fast | 32.0% | 55.1% | 39.0% | 62.0% |
| gpt-oss-120b | 51.9% | 50.7% | 45.5% | 46.5% |
| llama-3.3-70b | 36.7% | 46.4% | 36.5% | 34.8% |
| gemini-flash-lite | 49.8% | 65.2% | 50.0% | 51.2% |

### v1 Cheatsheet (4.6KB)

| Model | Dataset | v1 Accuracy | Baseline | Delta | Parse Fails | Confabulations |
|---|---|---|---|---|---|---|
| **grok-4.1-fast** | normal | 840/1000 (84.0%) | 320/1000 (32.0%) | **+52.0pp** | 150 (15.0%) | 4 (0.4%) |
| gpt-oss-120b | normal | 629/1000 (62.9%) | 519/1000 (51.9%) | +11.0pp | 24 (2.4%) | 313 (31.3%) |
| llama-3.3-70b | normal | 500/1000 (50.0%) | 367/1000 (36.7%) | +13.3pp | 0 (0%) | 500 (50.0%) |
| gemini-flash-lite | normal | 502/1000 (50.2%) | 498/1000 (49.8%) | +0.4pp | 0 (0%) | 498 (49.8%) |
| gpt-oss-120b | hard2_30 | 19/30 (63.3%) | 18/30 (60.0%) | +3.3pp | 2 (6.7%) | 6 (20.0%) |
| llama-3.3-70b | hard2_30 | 15/30 (50.0%) | 11/30 (36.7%) | +13.4pp | 0 (0%) | 15 (50.0%) |
| grok-4.1-fast | hard2_30 | 12/30 (40.0%) | 11/30 (36.7%) | +3.4pp | 13 (43.3%) | 2 (6.7%) |
| gemini-flash-lite | hard2_30 | 15/30 (50.0%) | 15/30 (50.0%) | +0.0pp | 0 (0%) | 15 (50.0%) |

**Key findings:**
- **Grok is the strongest model** -- 84% on normal with the v1 cheatsheet (+52pp over baseline)
- **Confabulation is the dominant failure mode** -- models fabricate counterexamples to claim FALSE when the implication actually holds. Gemini and Llama confabulate on 100% of TRUE problems
- **Grok almost never confabulates** (<1%) but suffers from parse failures/timeouts (15%)
- **All models improved** over baseline with the v1 cheatsheet

## Key Resources

**Competition:**
- [Competition page](https://competition.sair.foundation/competitions/mathematics-distillation-challenge-equational-theories-stage1/overview)
- [SAIR Playground](https://competition.sair.foundation/) -- test prompts against models (10 credits/day)
- [SAIR Zulip](https://zulip.sair.foundation/) -- community discussion forum

**Equational Theories Project:**
- [ETP main page](https://teorth.github.io/equational_theories/) -- full implication graph and equation explorer
- [Graphiti visualization](https://teorth.github.io/equational_theories/graphiti/) -- 22M-edge implication graph
- [Tao's AlphaEvolve predictors](https://github.com/teorth/equational_theories/tree/main/scripts/predictor) -- Python-based implication predictors
- [Hard implications blueprint](https://teorth.github.io/equational_theories/blueprint/hard-implications-chapter.html) -- annotated hardest cases
- [Order-5 ETP branch](https://github.com/vlad902/equational_theories/tree/order5) -- extended equation data

**Papers:**
- [Honda et al. (2025)](https://arxiv.org/abs/2509.20820) -- "Distilling Many-Shot In-Context Learning into a Cheat Sheet"
- [ETP paper (2025)](https://arxiv.org/abs/2512.07087) -- "The Equational Theories Project: Advancing Collaborative Mathematical Research at Scale"
- [Vampire on ETP (2025)](https://arxiv.org/abs/2508.15856) -- ATP performance analysis on these implications

**Tools:**
- [CyberAgentAILab/cheat-sheet-icl](https://github.com/CyberAgentAILab/cheat-sheet-icl) -- reference implementation of the distillation paper
- [Knuckledragger](https://github.com/philzook58/knuckledragger) -- Python proof assistant with Z3/Vampire/Prover9 ([blog](https://www.philipzucker.com/tao_algebra/))
- [adamtopaz equational_dataset](https://huggingface.co/datasets/adamtopaz/equational_dataset) -- HuggingFace ETP implications dataset

## Timeline

| Date | Milestone | Status |
|------|-----------|--------|
| Mar 30 | Baselines + eval harness complete | Done |
| Mar 30 | v1 cheatsheet evaluated (84% grok normal) | Done |
| Apr 2 | Error analysis + v2 cheatsheet iteration | |
| Apr 9 | Cheatsheet candidates ready | |
| Apr 10 | Evaluation models announced by SAIR | |
| Apr 11 | Model-specific optimization begins | |
| Apr 18 | Final review | |
| **Apr 20** | **Submission deadline (23:59 AoE)** | |
