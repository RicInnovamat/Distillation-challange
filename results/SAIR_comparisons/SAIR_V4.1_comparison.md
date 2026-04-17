# SAIR vs Local Run Comparison: v4.1 Cheatsheet, gpt-oss-120b

**Date:** 2026-04-17
**Submission:** EQT01-000057 ("Math Distillation Club 4.1")
**Model:** gpt-oss-120b (official mode, DeepInfra/bf16 primary provider)
**Source:** https://competition.sair.foundation/contributor-network/mathematics-distillation-challenge-equational-theories-stage1/EQT01-000057

## Summary

Same prompt, same model, different runs produce significantly different results due to the stochastic nature of reasoning models (temperature=1.0 required for gpt-oss-120b). SAIR's evaluation and our local evaluation agree on accuracy within ~2-3 percentage points, but the per-problem answers diverge on 28-36% of problems.

## Hard 2 (200 problems)

### Aggregate Metrics

|                | SAIR       | Ours (local) |
|----------------|------------|--------------|
| **Accuracy**   | 46.5% (93/200) | 48.5% (97/200) |
| TP             | 21         | 30           |
| FP             | 28         | 33           |
| FN             | 79         | 70           |
| TN             | 72         | 67           |
| TRUE Precision | 0.429      | 0.476        |
| TRUE Recall    | 0.210      | 0.300        |
| **TRUE F1**    | 0.282      | 0.368        |
| FALSE Precision| 0.477      | 0.489        |
| FALSE Recall   | 0.720      | 0.670        |
| **FALSE F1**   | 0.574      | 0.565        |
| **Macro F1**   | **0.428**  | **0.467**    |

### Per-Problem Mismatches

- **56 out of 200 problems differ** (28% mismatch rate)
- SAIR correct, we wrong: 26
- We correct, SAIR wrong: 30

| H# | Problem ID | Expected | Our Prediction | Winner |
|----|-----------|----------|---------------|--------|
| H6 | hard2_0006 | TRUE | FALSE | SAIR |
| H9 | hard2_0009 | FALSE | TRUE | SAIR |
| H16 | hard2_0016 | FALSE | TRUE | SAIR |
| H19 | hard2_0019 | TRUE | TRUE | Ours |
| H27 | hard2_0027 | FALSE | FALSE | Ours |
| H28 | hard2_0028 | TRUE | FALSE | SAIR |
| H33 | hard2_0033 | TRUE | TRUE | Ours |
| H39 | hard2_0039 | TRUE | FALSE | SAIR |
| H40 | hard2_0040 | TRUE | TRUE | Ours |
| H47 | hard2_0047 | FALSE | TRUE | SAIR |
| H48 | hard2_0048 | FALSE | TRUE | SAIR |
| H50 | hard2_0050 | TRUE | TRUE | Ours |
| H55 | hard2_0055 | FALSE | FALSE | Ours |
| H61 | hard2_0061 | TRUE | FALSE | SAIR |
| H71 | hard2_0071 | FALSE | TRUE | SAIR |
| H72 | hard2_0072 | TRUE | TRUE | Ours |
| H73 | hard2_0073 | TRUE | TRUE | Ours |
| H74 | hard2_0074 | TRUE | TRUE | Ours |
| H77 | hard2_0077 | FALSE | FALSE | Ours |
| H78 | hard2_0078 | TRUE | FALSE | SAIR |
| H80 | hard2_0080 | TRUE | TRUE | Ours |
| H81 | hard2_0081 | TRUE | FALSE | SAIR |
| H83 | hard2_0083 | TRUE | TRUE | Ours |
| H84 | hard2_0084 | FALSE | TRUE | SAIR |
| H90 | hard2_0090 | FALSE | FALSE | Ours |
| H92 | hard2_0092 | FALSE | TRUE | SAIR |
| H96 | hard2_0096 | FALSE | TRUE | SAIR |
| H97 | hard2_0097 | TRUE | TRUE | Ours |
| H99 | hard2_0099 | TRUE | TRUE | Ours |
| H101 | hard2_0101 | TRUE | TRUE | Ours |
| ... | ... | ... | ... | ... |
| *(56 total mismatches)* | | | | |

## Hard 3 (400 problems)

### Aggregate Metrics

|                | SAIR       | Ours (local) |
|----------------|------------|--------------|
| **Accuracy**   | 60.8% (243/400) | 58.0% (232/400) |
| TP             | 75         | 90           |
| FP             | 37         | 63           |
| FN             | 120        | 105          |
| TN             | 168        | 142          |
| TRUE Precision | 0.670      | 0.588        |
| TRUE Recall    | 0.385      | 0.462        |
| **TRUE F1**    | 0.489      | 0.517        |
| FALSE Precision| 0.583      | 0.575        |
| FALSE Recall   | 0.820      | 0.693        |
| **FALSE F1**   | 0.682      | 0.628        |
| **Macro F1**   | **0.585**  | **0.573**    |

### Per-Problem Mismatches

- **143 out of 400 problems differ** (36% mismatch rate)
- SAIR correct, we wrong: 77
- We correct, SAIR wrong: 66

| H# | Problem ID | Expected | Our Prediction | Winner |
|----|-----------|----------|---------------|--------|
| H2 | hard3_0002 | TRUE | FALSE | SAIR |
| H6 | hard3_0006 | TRUE | FALSE | SAIR |
| H11 | hard3_0011 | FALSE | FALSE | Ours |
| H13 | hard3_0013 | FALSE | FALSE | Ours |
| H14 | hard3_0014 | TRUE | TRUE | Ours |
| H15 | hard3_0015 | TRUE | TRUE | Ours |
| H17 | hard3_0017 | FALSE | TRUE | SAIR |
| H20 | hard3_0020 | TRUE | FALSE | SAIR |
| H21 | hard3_0021 | FALSE | FALSE | Ours |
| H33 | hard3_0033 | TRUE | TRUE | Ours |
| H37 | hard3_0037 | FALSE | TRUE | SAIR |
| H38 | hard3_0038 | TRUE | FALSE | SAIR |
| H39 | hard3_0039 | FALSE | FALSE | Ours |
| H40 | hard3_0040 | FALSE | TRUE | SAIR |
| H41 | hard3_0041 | FALSE | TRUE | SAIR |
| H43 | hard3_0043 | TRUE | FALSE | SAIR |
| H46 | hard3_0046 | TRUE | TRUE | Ours |
| H47 | hard3_0047 | TRUE | FALSE | SAIR |
| H48 | hard3_0048 | TRUE | TRUE | Ours |
| H50 | hard3_0050 | FALSE | TRUE | SAIR |
| ... | ... | ... | ... | ... |
| *(143 total mismatches)* | | | | |

## Cross-Dataset Summary

| Dataset | SAIR Acc | Our Acc | SAIR Macro F1 | Our Macro F1 | Mismatches |
|---------|----------|---------|---------------|-------------|------------|
| hard2   | 46.5%    | 48.5%   | 0.428         | 0.467       | 56/200 (28%) |
| hard3   | 60.8%    | 58.0%   | 0.585         | 0.573       | 143/400 (36%) |

## Key Findings

1. **Massive stochastic variance:** 28-36% of answers differ between runs with identical prompts. The reasoning model's required temperature=1.0 makes results fundamentally non-reproducible.

2. **Different error profiles, similar accuracy:** SAIR's hard3 run is more conservative (37 FP vs our 63), yielding better FALSE-F1 (0.682 vs 0.628). Our run has better TRUE recall (90 vs 75 TP) but far more confabulations.

3. **F1 divergence is real:** SAIR reports 28.2% F1 on hard2 — this matches the TRUE-F1 (0.282) we computed from their per-problem results. They appear to report TRUE-F1 only, not macro F1. Our macro F1 (0.467) looks better because it averages in the FALSE-F1.

4. **SAIR's reported F1 = TRUE-class F1:** Confirmed by matching SAIR's displayed 28.2% (hard2) and 48.9% (hard3) against our computed TRUE-F1 of 0.282 and 0.489 from their results.

5. **Implication for optimization:** Improving a cheatsheet by +2% on one run may be within noise. Reliable improvement requires consistent gains across multiple datasets and ideally multiple runs.
