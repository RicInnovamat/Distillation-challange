# SAIR Mathematics Distillation Challenge -- Stage 1 Plan

## Context

**Problem:** Build a compact cheat sheet (max 10KB) that maximizes LLM correctness on "Does Equation 1 imply Equation 2 over all magmas?" questions. The submission is a **complete prompt** (template + cheatsheet) with `{{ equation1 }}` and `{{ equation2 }}` placeholders. Evaluation uses a balanced 50/50 TRUE/FALSE set on unseen problems. Deadline: **April 20, 2026**.

**Evaluation models: NOT yet announced** (as of March 29). Expected by April 10. Playground provides GPT-OSS-120b, Llama 3.3 70b, Gemini Flash Lite, Grok as candidates.

**Key competitive intelligence** (from Zulip community):
- **stokarz achieved 99.5%** on hard dataset (4.3KB cheatsheet, GPT-OSS-120b) using "compact structural classifier with canonical source-family collapse lemmas and ordered invariant-based decision rules"
- **Different models need different cheatsheet formats:** GPT → symbolic solvers; Llama → algebraic family atlases
- **Algebraic cheatsheets generalize better** across unseen distributions (critical since eval set is adversarial)
- **Llama has a FALSE bias** with standard prompts; simplified prompt framing gives +11 points
- **Baseline without cheatsheet:** GPT-OSS-120b = 92% normal / 47% hard
- **Evaluation runs on OpenRouter**, low-reasoning, low-temperature settings
- **Output parsing:** looks for `VERDICT: TRUE` or `VERDICT: FALSE` (colon, not equals). Verdict must be first output line.

**Team roles:**
- **Andrea (A):** Architecture, infrastructure, compute, implementation
- **Riccardo (R):** Methodology design, infra review, platform/submission
- **Tommaso (T):** Research, mathematical content, methodology with Riccardo

**Compute resources:**
- Claude Max 200K subscription (no API cost for orchestration/analysis/compression)
- OpenRouter API for target model evaluation (~$150 total budget, see cost estimates below)
- SAIR Playground (10 credits/day, ~100 cheap-model runs/day)

**Team checkpoints** (from Google Calendar, times in Dubai/GST):

| # | Date | Time (Dubai) | Phase gate |
|---|------|-------------|------------|
| 1 | **Apr 2 (Wed)** | 19:00 | Review baselines + error analysis |
| 2 | **Apr 9 (Wed)** | 18:45 | Review cheatsheet candidates pre-model-announcement |
| 3 | **Apr 11 (Sat)** | 11:00 | React to model announcement, finalize track |
| 4 | **Apr 14 (Mon)** | 20:00 | Near-final cheatsheet review |
| 5 | **Apr 18 (Sat)** | 11:00 | Final review and submit |

**Deadline:** April 20, 23:59 AoE (April 21, 15:59 Dubai time)

---

## System Architecture

All model inference runs in the cloud -- no local GPU required. The system has three layers:

```
┌─────────────────────────────────────────────────────┐
│                  ORCHESTRATION LAYER                 │
│        Claude Max 200K (via Claude Code)             │
│  - Cheatsheet generation, compression, analysis     │
│  - Error analysis and iteration logic                │
│  - AlphaEvolve-style search orchestration            │
│  - Cost: $0 (included in subscription)               │
│                                                      │
├─────────────────────────────────────────────────────┤
│                  EVALUATION LAYER                    │
│              eval_harness.py (Python)                │
│  - Loads JSONL problems from Training_data/          │
│  - Substitutes equations into prompt template        │
│  - Calls target models via OpenRouter API            │
│  - Parses VERDICT from responses                     │
│  - Tracks per-problem results to CSV                 │
│  - Supports parallel requests + cost tracking        │
│  - Runs locally, calls cloud APIs                    │
│                                                      │
├─────────────────────────────────────────────────────┤
│                  INFERENCE LAYER                     │
│            OpenRouter API (cloud models)              │
│  Target models:                                      │
│  - openai/gpt-oss-120b                               │
│  - meta-llama/llama-3.3-70b-instruct                 │
│  - google/gemini-3.1-flash-lite-preview              │
│  - x-ai/grok-4.1-fast                               │
│                                                      │
│  Alternative providers (for speed/cost):             │
│  - GroqCloud (Llama, 276+ tok/s)                     │
│  - Cerebras free tier (Llama, 30 req/min)            │
│  - Google AI Studio free tier (Gemini)               │
└─────────────────────────────────────────────────────┘
```

### Architecture Deliverables

**A. `eval_harness.py`** -- Core evaluation script
- Config-driven: model, prompt template file, dataset file, concurrency
- OpenRouter API client with retry logic, rate limiting, cost tracking
- Output parser: regex for `VERDICT:\s*(TRUE|FALSE)` with fallback patterns
- Results output: per-problem CSV + accuracy summary + cost report
- Parallel execution (async/aiohttp) to speed up evaluation passes

**B. `cheatsheet_manager/`** -- Cheatsheet versioning and tracking
- Stores cheatsheet versions with metadata (size, date, accuracy scores)
- Comparison view: accuracy delta between versions per dataset
- Size validator: warns if prompt exceeds 10KB

**C. `analysis/`** -- Error analysis and reporting
- Per-problem error classification pipeline
- Accuracy breakdown by structural features (uses implication graph data)
- Generalization gap tracker (train vs validation accuracy)

### Architecture Review
**Owner:** Andrea (design + implement), Riccardo (review)

---

## Cost Estimates

### OpenRouter Pricing (per 1M tokens)

| Model | Input | Output | Cost per eval pass (1669 problems) |
|-------|-------|--------|-----------------------------------|
| openai/gpt-oss-120b | $0.039 | $0.19 | **~$0.40** |
| meta-llama/llama-3.3-70b | $0.10 | $0.32 | **~$0.91** |
| google/gemini-3.1-flash-lite | $0.25 | $1.50 | **~$2.63** |
| x-ai/grok-4.1-fast | $0.20 | $0.50 | **~$1.75** |

*Assumptions: ~4500 input tokens/problem (prompt + cheatsheet), ~300 output tokens/problem*

### Projected Total Spend

| Activity | Runs | Per-run cost (avg) | Subtotal |
|----------|------|--------------------|----------|
| Baselines (4 models x 4 datasets, no cheatsheet) | 16 | ~$1.40 | ~$22 |
| Iterative cheatsheet testing (30-problem probes) | ~80 | ~$0.05 | ~$4 |
| Full eval passes (200-400 problems, best candidates) | ~30 | ~$1.00 | ~$30 |
| Cross-model validation (final cheatsheet x 4 models) | 8 | ~$1.40 | ~$11 |
| Robustness testing (3-5 replicate runs) | 15 | ~$1.40 | ~$21 |
| AlphaEvolve search iterations | ~50 | ~$0.10 | ~$5 |
| **Total OpenRouter** | | | **~$93** |
| Claude Max 200K (orchestration, analysis, compression) | unlimited | $0 | **$0** |
| SAIR Playground (10 credits/day x 22 days) | ~220 | $0 | **$0** |
| **Grand Total** | | | **~$93** |

**Cost optimization strategy:**
- Use GPT-OSS-120b ($0.039/1M in) for most iteration -- it's 6x cheaper than Gemini
- Use Claude Max for all orchestration/analysis/compression (free)
- Use Cerebras/GroqCloud free tiers for Llama during early development
- Reserve Playground credits for final verification only
- Run 30-problem probes ($0.05) for fast signal before committing to full passes ($1-3)

---

## Phase 1: Baseline & Error Analysis (Mar 29 - Apr 2)

**4 working days before Meet 1**

### 1.1 Design & Implement Architecture
**Owner:** Andrea (implement), Riccardo (review)
**Deliverable:** Working `eval_harness.py` + project structure

```
project/
├── eval_harness.py          # Core evaluation script
├── config/
│   ├── models.yaml          # Model configs (name, provider, pricing)
│   └── prompts/             # Prompt template files
├── cheatsheets/             # Versioned cheatsheet files
│   └── v0_baseline.txt      # Minimal no-cheatsheet prompt
├── results/                 # Evaluation outputs
│   ├── baselines/           # Phase 1 baseline results
│   └── iterations/          # Phase 2 iteration results
├── analysis/
│   └── error_taxonomy.py    # Error classification helpers
├── Training_data/           # (existing) JSONL problem sets
├── Research/                # (existing) equations, implication graph
└── Blog_data/               # (existing) community discussions
```

Requirements for `eval_harness.py`:
- Config-driven (model, prompt file, dataset, concurrency, temperature)
- OpenRouter API calls with async parallelism, retry, rate limiting
- VERDICT parser with regex + fallback
- Per-problem CSV output + summary stats + cost tracking
- CLI: `python eval_harness.py --model gpt-oss-120b --prompt prompts/v0.txt --data hard2 --concurrency 10`

### 1.2 Run Zero-Cheatsheet Baselines
**Owner:** Andrea
**Deliverable:** Accuracy table per model per dataset + per-problem CSVs

Run on all 4 candidate models x 4 datasets (16 runs, ~$22).
Minimal prompt (no cheatsheet):
```
You are a mathematician specializing in equational theories of magmas.
Determine whether {{ equation1 }} implies {{ equation2 }} over all magmas.
Output exactly: VERDICT: TRUE or VERDICT: FALSE
```

### 1.3 Error Analysis & Problem Taxonomy
**Owner:** Riccardo + Tommaso (methodology), Andrea (tooling)
**Deliverable:** Error taxonomy document + classification script

Methodology (designed by R+T):
- Classify every wrong answer by error type: FALSE-as-TRUE (confabulation), TRUE-as-FALSE (failed derivation / FALSE bias), parse error
- Cross-reference with implication graph using `eq1_id`/`eq2_id` from `Research/Raw_implication_graph.csv`
- Identify structural patterns in failures: operator count, variable overlap, equation "strength" (Implies count)

### 1.4 Analyze Implication Graph & External Resources
**Owner:** Andrea
**Deliverable:** Processed equation families and implication statistics

- Analyze `Research/Raw_implication_graph.csv` (1414 equations with Implies/Implied-by counts)
- Identify equivalence classes and "power equations" (imply >100 others)
- Download Tao's AlphaEvolve predictors from GitHub
- Download full raw implications table from teorth.github.io

### 1.5 Create Stratified Validation Splits
**Owner:** Andrea
**Deliverable:** Train/validation splits (70/30) for each dataset

Reserve 30% for generalization testing. Download community benchmarks:
- SAIRCommunityBench (200 problems)
- Hard5 order-5 dataset (654 problems)

**>>> Meet 1 (Apr 2, 19:00 Dubai):** Review baselines, error analysis, architecture. Decide Track A vs B priority.

---

## Phase 2: Cheatsheet Construction (Apr 2 - Apr 11)

**7 working days between Meet 1 and Meet 3**

### 2.1 Build Long-Form Knowledge Base (30-50KB)
**Owner:** Riccardo + Tommaso (content/methodology), Andrea (implementation/testing)
**Deliverable:** `knowledge_base.md` (~30-50KB)

Content priority (informed by error analysis from Phase 1):

| Content block | Budget % | Description |
|--------------|----------|-------------|
| A. Equation family classification | ~30% | Group 4694 equations into canonical families (trivial, constant-forcing, idempotent, commutative, absorption, band-type, etc.) |
| B. Implication decision rules | ~25% | Collapse lemmas, structural non-implication rules, transitivity |
| C. Counterexample schemas | ~15% | Small magma tables (size 2-3), left/right-zero, constant, projection |
| D. Hard-case guidance | ~10% | Patterns from Tao's hardest ETP problems list |
| E. Meta-instructions & guardrails | ~10% | Anti-confabulation, step-by-step decision procedure |
| F. Prompt template | ~10% | Task framing, output format, model-specific adjustments |

### 2.2 Two-Track Cheatsheet Architecture
**Owner:** Riccardo + Tommaso (design methodology), Andrea (implementation)
**Deliverable:** Two 10KB cheatsheet variants

**Track A: Algebraic Family Atlas** (better generalization, works across model families)
- Equation family taxonomy with canonical representatives
- Family-pair implication lookup table with proof/countermodel schemas
- Decision tree: classify eq1 → family X, classify eq2 → family Y, lookup X→Y

**Track B: Symbolic Generalized Solver** (higher ceiling, GPT-optimized)
- Structural classification rules (variable analysis, nesting depth)
- Ordered invariant-based decision rules
- Canonical source-family collapse lemmas

### 2.3 Prompt Template Design
**Owner:** Riccardo + Tommaso (methodology), Andrea (testing)
**Deliverable:** Tested prompt templates for each track

Key design decisions:
- **Verdict first** in output (prevents reasoning into wrong answer)
- **Cheatsheet before equations** (enables KV-cache reuse)
- **Simple task framing** for Llama (avoid FALSE bias)
- **Size budget:** ~500B template + ~500B guardrails + ~9000B math content

### 2.4 Iterative Compression & Testing Loop
**Owner:** Andrea (execution), Riccardo (methodology review)
**Deliverable:** Cheatsheet versions v1-v10+ with accuracy tracking

Loop (all model calls via OpenRouter, orchestration via Claude Max):
1. Compress knowledge base to 10KB using Claude (free via Max subscription)
2. Test on 30-problem stratified probe (~$0.05) for quick signal
3. If promising, test on full hard2 (200 problems, ~$1)
4. Claude analyzes failures, proposes modifications (free)
5. Iterate: remove least impactful rules, tighten most impactful
6. Test promising versions on hard3 + community benchmarks for generalization

### 2.5 AlphaEvolve-Style Automated Search
**Owner:** Andrea
**Deliverable:** Optimized cheatsheet via automated loop

1. Claude Max as orchestrator (free): analyzes current cheatsheet + wrong answers + error patterns
2. Claude proposes targeted modifications (free)
3. Test on 30-60 problem probe via OpenRouter (~$0.05-0.10 per iteration)
4. Accept improvements, reject regressions
5. Iterate 50-100 times (~$5 total OpenRouter cost)

**>>> Meet 2 (Apr 9, 18:45 Dubai):** Review best cheatsheet candidates. Prepare for model announcement.

---

## Phase 3: Optimization & Submission (Apr 10 - Apr 18)

**8 days between model announcement and Meet 5**

### 3.1 React to Model Announcement (Apr 10)
**Owner:** All
**Status check:** Models still TBD as of March 29. Expected April 10.

When evaluation model(s) are announced:
- If GPT-OSS-120b → prioritize Track B (symbolic solver) with generalization safeguards
- If Llama 3.3 70b → prioritize Track A (algebraic atlas), simplified prompt
- If Gemini Flash → test both tracks, likely Track A
- If multiple models averaged → optimize for the weakest model
- Adjust prompt template for model-specific quirks (e.g., Llama FALSE bias)

**>>> Meet 3 (Apr 11, 11:00 Dubai, Saturday):** Align on model-specific strategy.

### 3.2 Model-Specific Optimization (Apr 11-14)
**Owner:** Andrea (execution), Riccardo + Tommaso (methodology guidance)
**Deliverable:** Model-tuned cheatsheet with cross-dataset validation

- Run final cheatsheet candidates on held-out validation splits
- Test on SAIRCommunityBench (200 problems) and Hard5 (654 problems)
- Track accuracy by: TRUE vs FALSE problems, equation complexity, operator count
- **Overfitting check:** if train - validation accuracy > 5% → simplify

**>>> Meet 4 (Apr 14, 20:00 Dubai):** Near-final review.

### 3.3 Robustness Testing (Apr 15-17)
**Owner:** Andrea
**Deliverable:** Variance analysis

Run best cheatsheet 3-5 times on same problem set via OpenRouter.
If variance > 3%, add guardrails or simplify decision rules.

### 3.4 Final Submission (Apr 17-18)
**Owner:** Riccardo (submits), Andrea (final verification)
**Deliverable:** Submitted prompt on SAIR platform

Checklist:
- [ ] Prompt contains `{{ equation1 }}` and `{{ equation2 }}` (double curly braces)
- [ ] Total size < 10KB (`wc -c final_prompt.txt` < 10240)
- [ ] Tested in SAIR Playground with "empty" template (0 parse errors on 10+ runs)
- [ ] Output parses correctly: `VERDICT: TRUE` / `VERDICT: FALSE`
- [ ] Tested on at least 3 dataset variants for generalization
- [ ] Submitted before April 20, 23:59 AoE

**>>> Meet 5 (Apr 18, 11:00 Dubai, Saturday):** Final review and submit.
**Apr 19-20:** Emergency buffer.

---

## Feasibility Assessment

| Phase | Duration | Workload | Bottleneck | Feasible? |
|-------|----------|----------|-----------|-----------|
| Phase 1 | 4 days (Mar 29 - Apr 2) | Architecture + baselines + error analysis | Architecture implementation (1-2 days) | Yes -- tight but doable. Architecture is straightforward (Python + OpenRouter). Baselines are parallelizable across models. |
| Phase 2 | 9 days (Apr 2 - Apr 11) | Knowledge base + two cheatsheet tracks + iterative testing | Mathematical content quality (Riccardo + Tommaso) and iteration speed | Yes -- longest phase with most buffer. Claude Max handles orchestration for free. |
| Phase 3 | 8 days (Apr 10 - Apr 18) | Model-specific optimization + validation + submission | Depends on model announcement timing and how much pivot is needed | Yes -- if Tracks A and B are solid by Apr 9, pivot is a tuning exercise not a rewrite. |

**Key risk:** Phase 1 is the tightest (4 days). Mitigation: start architecture implementation immediately; baselines can run overnight once harness is ready.

---

## Risk Mitigation

| Risk | Mitigation |
|------|-----------|
| Eval includes order-5+ equations | Test on Hard5 dataset; ensure rules generalize beyond 4-op |
| Eval model not in our test set | Algebraic atlas works across model families (85%+ on all) |
| Adversarial problems defeat heuristics | Include deep-reasoning fallback rules alongside shortcuts |
| Overfitting to training distributions | Always test on held-out + community benchmarks; track gap |
| Parse errors on evaluation | Verdict first, page break after, test extensively |
| 10KB too tight | Template ~500B; budget 9.5KB for math content |
| OpenRouter rate limits / outages | Implement retry logic; have GroqCloud/Cerebras as fallback |

---

## Key Files

| File | Purpose |
|------|---------|
| `Training_data/normal.jsonl` (1000) | Primary training/testing data |
| `Training_data/hard1.jsonl` (69), `hard2.jsonl` (200), `hard3.jsonl` (400) | Hard problem sets |
| `Research/equations.txt` | Complete list of 4694 equations |
| `Research/Raw_implication_graph.csv` | Equation-level implication statistics |
| `Blog_data/discussions.json` | stokarz methodology and competitive insights |
| `Blog_data/The_hardest_ETP_problems.json` | Tao's hardest implications list |

## External Resources

- Full raw implications: `teorth.github.io/equational_theories/implications/`
- Tao's predictors: `github.com/teorth/equational_theories/blob/main/scripts/predictor/`
- SAIR Playground: `competition.sair.foundation` (10 credits/day)
- Community GitHub: `github.com/SAIRcompetition/equational-theories-community`

---

## Verification

End-to-end validation before submission:
1. Run eval harness on all 1669 public problems → target: >95% normal, >85% hard
2. Run on community benchmarks → target: >85%
3. 3-5 replicate runs → variance < 3%
4. SAIR Playground → 0 parse errors on 10+ runs
5. File size: `wc -c final_prompt.txt` < 10240 bytes
