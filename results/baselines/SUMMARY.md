# Baseline Results (No Cheatsheet)

**Prompt:** `config/prompts/v0_baseline.txt` (193 bytes)
**Settings:** temperature=0.0, concurrency=10
**Date:** 2026-03-30

## Accuracy Table

| Model | normal (1000) | hard1 (69) | hard2 (200) | hard3 (400) |
|-------|:---:|:---:|:---:|:---:|
| gpt-oss-120b | 54.7% (52pe) | 60.3% (11pe) | 49.7% (17pe) | 50.1% (29pe) |
| llama-3.3-70b | 52.8% (305pe) | 60.4% (16pe) | 51.8% (59pe) | 50.0% (122pe) |
| gemini-3.1-flash-lite | 49.8% (1pe) | 65.2% (0pe) | 50.0% (0pe) | 51.2% (0pe) |
| grok-4.1-fast | 59.6% (463pe) | 77.6% (20pe) | 51.7% (49pe) | 76.5% (76pe) |

*pe = parse errors. Total cost across all 16 runs: $3.31*

## Error Pattern Summary

| Model | Dominant error | Parse errors | Notes |
|-------|---------------|:---:|-------|
| gpt-oss-120b | Mixed (confab + missed) | 5-7% | Reasoning model; content is null, verdict in reasoning tokens |
| llama-3.3-70b | FALSE bias + parse errors | 25-30% | Strong FALSE bias (missed >> confab); needs output format guidance |
| gemini-3.1-flash-lite | Extreme FALSE bias | ~0% | Nearly always says FALSE; 498/500 TRUE missed on normal |
| grok-4.1-fast | FALSE bias + parse errors | 20-46% | Best accuracy when it parses (77.6% hard1); very expensive |

## Key Takeaways

1. **All models are near random** (50%) on hard problems without a cheatsheet
2. **FALSE bias is universal** -- all models miss TRUE implications far more than they confabulate
3. **Grok has highest raw accuracy** (77.6% hard1, 76.5% hard3) but 46% parse errors on normal and 10x cost
4. **Gemini never confabulates** but also never reasons -- just defaults to FALSE
5. **Llama and Grok need output format guidance** -- 25-46% parse error rate
6. **GPT-OSS-120b has the fewest parse errors** (5-7%) but still near-random accuracy
7. **Cheatsheet priority: help models recognize TRUE implications** (FALSE bias is the dominant failure mode)
