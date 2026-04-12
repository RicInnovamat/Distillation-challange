## Parsing Error Resolution & Model Performance

- Fixed all parsing errors in latest run with GPT 4.1
- Parse errors reduced from 65 to 0 across all models
- Current accuracy ranges:
  - Hard 1: 70–80%
  - Hard 2: 60–70%
  - Hard 3: ~60%
- Consumed 77 million tokens total
- Cheat sheet at 20 bytes under maximum limit

## Model Speed & Cost Analysis

- Grok performance breakthrough:
  - 1,500–1,800 tokens/second (peaks at 2,300)
  - GPT-4o: 700 tokens/second
  - Other models: ~200 tokens/second maximum
- Grok costs double per token but is ~10x faster
- Using OpenRouter for multi-provider optimization

## False vs True Implication Challenge

- False implications: successfully detecting most cases
- True implications: major weakness identified
  - Models correctly identify true procedures but fail execution
  - Need strategies beyond counter-examples for validation
- Pattern analysis:
  - GPT models: high false positives (marking true as false)
  - Grok: opposite bias pattern
  - Gemma: extreme false bias

## Research Insights from Tommy

- Simple rewrites strategy covers 4M+ implications on 22M dataset
  - Apply commutative law repeatedly until evident correctness
  - Combined with transitivity for major coverage
- Syntactic matching as pre-filter (98% accuracy on Hard 1–2)
- Canonicalization approach:
  - Normalize equations to standard form first
  - Apply standardized rules after normalization
  - May conflict with current two-step procedure issues

## Next Steps & Strategy

- Wait for model announcement (due Saturday, California time)
- Tommy: create shared document for cheat sheet analysis and version control
- Experiment with Python integration approach:
  - Give models coding tools instead of pure logical reasoning
  - Leverage models' coding optimization strengths
- Focus on true implication strategies over false detection
- Next team sync: Tuesday 6 PM
