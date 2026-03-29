# Mathematics Distillation Challenge -- Meeting Notes 23 march 2026
**Date:** 2026-03-26
**Participants:** Andrea (A), Riccardo (R), Tommaso (T)

---

## Challenge Summary

- **What:** build a cheat sheet (max 10KB) that maximizes LLM correctness on equational implication problems over magmas ("Does Eq1 imply Eq2?").
- **Domain:** equational theories. Given 4694 laws, determine pairwise implications. True/false only (Stage 1).
- **Eval set:** balanced 50/50 true/false, different from the 1669 public problems. No tools, no internet at eval time.
- **Models:** TBD, announced by April 10. Candidates: OpenAI OSS, Llama, Gemini Flash.
- **Budget constraint:** recommended avg <= $0.01/problem, <= 10 min/problem.
- **Submissions:** one per team (to verify if re-submission is allowed before deadline).
- **Deadline:** April 20, 23:59 AoE.
- **Stage 2:** starts May 1, harder (counterexamples, Lean proofs, or calibrated probabilities). Larger cheat sheets allowed. Top 1000 teams from Stage 1 advance.

---

## Public Training Data

| Set | Size | Difficulty |
|--------|------|------------|
| normal | 1000 | normal |
| hard1 | 69 | hard |
| hard2 | 200 | hard |
| hard3 | 400 | hard |

Additional problems available from the Equational Theories Project.

---

## Decisions Made

1. **Shared environment:** GitHub repo created by R. Docs and meeting notes go there.
2. **Comms:** WhatsApp group.
3. **Compute:** Andrea handles infra/costs. Starting with Claude Max 200 + Claude Code.
4. **Team registration:** R creates on SAIR platform.
5. **Meeting cadence:** every ~5 days.

| Date | Time | Notes |
|------------|-------|----------------|
| 2026-04-02 | 17:00 | Meet 1 |
| 2026-04-09 | 16:45 | Meet 2 |
| 2026-04-11 | 09:00 | Saturday |
| 2026-04-14 | 18:00 | Meet 4 |
| 2026-04-18 | TBD | Saturday, final |

Possible extra session Sunday April 19 if needed.

---

## Open Questions

1. **Cheat sheet format:** natural language (verbose markdown, as in the original paper) vs. formal notation vs. hybrid. To test empirically.
2. **Content balance:** inference rules vs. worked examples vs. heuristics. Unknown optimal mix.
3. **Lean / formal verification:** Axiom (free API, boolean only) and Harmonic (free, generative) available. Claude Code + Lean is feasible. Priority unclear for Stage 1; likely more relevant for Stage 2.
4. **Re-submission policy:** verify on platform.
5. **Exact eval models:** announced by April 10. Strategy may need adjustment depending on model capabilities.

---

## Strategy Sketch

### Phase 1: Baseline + Error Analysis (by April 2)
- Run target models (or closest proxies) on public problem sets with no cheat sheet.
- Categorize errors: wrong reasoning, wrong strategy, calculation error, correct strategy but failed execution.
- Identify which problem types / equation patterns benefit most from guidance.

### Phase 2: Cheat Sheet Construction (April 2-11)
- Generate long cheat sheet (30-50k tokens) using strong models (Opus, GPT-4/5, Gemini Pro).
- Compress iteratively, guided by error analysis: keep what covers model weaknesses, cut what covers things models already handle.
- Test format variants (A/B on ~30 representative problems): verbose NL, compact formal, hybrid.
- Human review at each compression step to identify redundancies and find more universal formulations.

### Phase 3: Optimization + Submission (April 11-18)
- Fine-tune cheat sheet allocation based on cumulative test results.
- Final testing on held-out subset of public problems.
- Prepare submission, verify parsing with Playground.

---

## Next Steps (by April 2)

| Who | Task |
|-----|------|
| R | Create team on SAIR platform |
| R | Read rules in detail, write essentials doc, push to repo |
| R | Clean up meeting notes (this doc), push to repo |
| R | Verify re-submission policy |
| A | Set up infra, run first baseline (models with no cheat sheet on public sets) |
| A | Share baseline results on repo |
| T | Read 2-3 papers on distillation / prompting for math LLMs |
| T | Form initial view on NL vs. formal vs. hybrid |

---

## Reference Prompt (example from competition page)

```
You are a mathematician specializing in equational theories of magmas.
Your task is to determine whether Equation 1 ({{ equation1 }}) implies
Equation 2 ({{ equation2 }}) over all magmas.
---
## CHEAT SHEET: FAST DECISION FILTERS
[...]
---
Output format (use exact headers without any additional text or formatting):
VERDICT: must be exactly TRUE or FALSE (in the same line).
REASONING: must be non-empty.
PROOF: required if VERDICT is TRUE, empty otherwise.
COUNTEREXAMPLE: required if VERDICT is FALSE, empty otherwise.
```

---

## Key Resources

- Competition page: https://competition.sair.foundation/competitions/mathematics-distillation-challenge-equational-theories-stage1/overview
- Equational Theories Project implication graph: `export_raw_implications`
- Law list (4694 laws): `equations.txt`
- Public problem sets on Hugging Face: normal, hard1, hard2, hard3
- Reference paper: Honda, Murakami, Zhang (2025), "Distilling Many-Shot In-Context Learning into a Cheat Sheet"
- SAIR Zulip: https://zulip.sair.foundation/
