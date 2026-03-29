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
├── Meetings_Notes.md        # Team meeting notes and decisions
├── Training_data/           # Public problem sets (JSONL)
│   ├── normal.jsonl         # 1000 problems (500 TRUE / 500 FALSE)
│   ├── hard1.jsonl          # 69 problems (deduplicated hard set)
│   ├── hard2.jsonl          # 200 problems (100 TRUE / 100 FALSE)
│   └── hard3.jsonl          # 400 problems (195 TRUE / 205 FALSE)
├── Research/
│   ├── equations.txt        # All 4694 equational laws
│   └── Raw_implication_graph.csv  # Per-equation implication statistics
└── Blog_data/               # SAIR Zulip community discussions (JSON)
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

## Key Resources

- [Competition page](https://competition.sair.foundation/competitions/mathematics-distillation-challenge-equational-theories-stage1/overview)
- [Equational Theories Project](https://teorth.github.io/equational_theories/) -- full implication graph and equation explorer
- [Tao's AlphaEvolve predictors](https://github.com/teorth/equational_theories/tree/main/scripts/predictor) -- Python-based implication predictors
- [Reference paper](https://arxiv.org/abs/2509.20820) -- Honda et al. (2025), "Distilling Many-Shot In-Context Learning into a Cheat Sheet"
- [SAIR Zulip](https://zulip.sair.foundation/) -- community discussion forum

## Timeline

| Date | Milestone |
|------|-----------|
| Apr 2 | Baselines + error analysis complete |
| Apr 9 | Cheatsheet candidates ready |
| Apr 10 | Evaluation models announced by SAIR |
| Apr 11 | Model-specific optimization begins |
| Apr 18 | Final review |
| **Apr 20** | **Submission deadline (23:59 AoE)** |
