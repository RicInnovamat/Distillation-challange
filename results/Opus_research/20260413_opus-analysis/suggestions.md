# Cheatsheet Improvement Suggestions — v.Opus-1 Design Notes

**Date:** 2026-04-13
**Source data:** hard1 (69 problems) results for opus-solver (Claude Opus 4.6, no cheatsheet, pure reasoning) vs gpt-oss-120b and gemma-4-31b (official mode + fallbacks) with cheatsheets v4.1 and v5.2.

## 1. Executive Summary

Opus-solver scored **56/69 (81.2%)** on hard1 with zero cheatsheet — beating the best cheatsheet result (gemma+v4.1 at 75.4%) by ~6 percentage points. More importantly, Opus's error profile is qualitatively different:

| Model (hard1) | Correct | T->F (missed TRUE) | F->T (confabulated TRUE) | Parse/timeouts |
|---|---|---|---|---|
| **opus-solver** | **56 (81%)** | **0** | 5 | 8 |
| gemma-4-31b v4.1 | 52 (75%) | 12 | 5 | 0 |
| gpt-oss-120b v4.1 | 50 (73%) | 10 | 9 | 0 |
| gemma-4-31b v5.2 | 45 (65%) | 5 | 19 | 0 |
| gpt-oss-120b v5.2 | 45 (65%) | 8 | 16 | 0 |

Two signals stand out:

1. **Opus's T->F = 0** — it never defaulted to FALSE on a real TRUE implication. Both cheatsheet models missed 10–12 TRUE cases. This is the largest headroom for improvement.
2. **9 of those missed-TRUE cases were shared** between Gemma and GPT (both v4.1 predicted FALSE on 9 problems where the answer is TRUE). That's 13% of hard1. The same failure mode, same cheatsheet.

Opus's 5 confabulations (F->T) are a narrower, identifiable failure pattern: the **singleton fallacy** — claiming "Eq1 forces |M|=1, therefore Eq2 holds vacuously" without exhaustive verification.

The goal of v.Opus-1 is to port Opus's winning technique into a cheatsheet while warning against its specific failure mode. This document compares reasoning traces, maps observations to v4.1/v5.2 rules, and defines the concrete suggestions.

## 2. Reasoning Pattern Comparison

### 2.1 Missed-TRUE Cases (v4.1 main failure)

**hard1_0007** — `x = (y*(y*(y*z)))*x` implies `x*y = z*(w*(w*y))` — answer **TRUE**.

**Opus (correct, TRUE):** Uses variable substitution to derive a structural consequence.
> Pick any elements `a, b`. Instantiating `y := a, z := b` in Equation 1 gives `x = (a*(a*(a*b)))*x`. Let `c = a*(a*(a*b))`. Then `c * x = x` for every x, so **c is a left identity**. Now substitute `y := c` … using `c * u = u` three times … Equation 1 becomes `x = z * x` for all x, z. Hence **every element z is a left identity**. Therefore the magma satisfies `u*v = v` for all u, v.

Then verifies Eq2 in the right-projection magma — holds, TRUE.

**GPT v4.1 (wrong, FALSE):** Correctly identifies the structure but stalls.
> Means product (y*(y*(y*z))) acts as left identity for all x. So left identity element L = (y*(y*(y*z))) depends on y,z but must be left identity for all x. In a magma we can define operation such that a*b = a for all a,b (left projection). Then Eq1: RHS = … = y * x = y (left projection) =? LHS x. That gives x = y, not always true. So left projection does not satisfy Eq1 generally unless all variables equal? So need operation where for any y,z, (y*(y*(y*z))) equals a left id[truncated]

GPT identifies "left identity" but doesn't execute the substitution iteratively. Tries canonical witnesses, they fail, gives up with "probably false".

**Gemma v4.1 (wrong, FALSE):** Strict witness-testing only.
> VERDICT: FALSE. RULE: left-zero witness. 1. Test Equation 1 under left-zero (a*b = a): LHS = x, RHS = y. Not identity. … 2. Right-zero: not identity. … 3. Check Step 2.8 (Contradiction Motifs): Eq1: ... rhsVars=3 ... [continues syntactic exclusion checks, none fire] … defaults to FALSE.

Gemma **never attempts substitution**. Witness testing finds no match, syntactic exclusions don't fire, falls through to FALSE.

---

**hard1_0013** — `x*y = ((z*y)*x)*x` implies `x*y = y*(y*(y*y))` — answer **TRUE**.

**Opus (correct, TRUE):**
> Put `x := y` in E1: for every z, `y*y = ((z*y)*y)*y`. Take `z := y`: `y*y = ((y*y)*y)*y`. Call `a := y*y`, so `(a*y)*y = a`. Take `z := y*y = a`: `y*y = ((a*y)*y)*y`. But `(a*y)*y = a`, so the right-hand side is `a*y`. Thus `y*y = a*y`, i.e. `a = a*y`. So `(y*y)*y = y*y` for every y. [...continues to show Eq1 forces constant magma...]

Opus executes 3+ substitutions to reduce Eq1 to a constant-magma identity. Gemma/GPT both default to FALSE after witness-testing fails.

---

**hard1_0018, hard1_0034, hard1_0041, hard1_0044, hard1_0052, hard1_0067** — same pattern. All are TRUE implications where substitution-driven reasoning resolves, but witness-driven reasoning fails.

### 2.2 Opus's Confabulation Pattern

**hard1_0032** — `x = ((y*x)*x)*(x*z)` implies `x*y = (z*z)*z` — answer **FALSE** (Gemma correct, Opus+GPT wrong).

**Opus (WRONG, TRUE):** Singleton fallacy.
> **Claim.** Equation 1 is only satisfiable in the one-element (trivial) magma. In a trivial magma every equation holds, so Equation 2 is implied. **Why Equation 1 forces |M| = 1.** Variables y and z are *ghost variables*. … Equation 1 is equivalent to the condition (⋆) for every x: `a * b = x` for all a ∈ L_x, b ∈ R_x. Both L_x and R_x are nonempty … [goes on to "prove" singleton-only, incorrectly]

**Gemma (correct, FALSE):** Finds a witness that satisfies Eq1 but not Eq2.

Opus does this **5 times** (hard1_0016, 0025, 0032, 0047, 0062). Each time, it mistakenly argues Eq1 is "too restrictive" to have any non-trivial model. In every case a 2-element (or larger) magma satisfies Eq1 but falsifies Eq2. **The cheatsheet models avoid this by not attempting the singleton argument at all.**

### 2.3 All-Wrong Cases

**hard1_0033** — answer FALSE. Opus timed out. Both cheatsheet models predicted TRUE via over-eager right-projection matching.

GPT reasoning:
> Check if Eq1 forces left projection? It's bare: left side is variable x, right side is product term P = ((y*(z*y))*y)*x. Does P contain x? Yes at the end. So x appears in RHS. For left projection rule, need x = x*T where T does NOT contain x. Here RHS is (something)*x not x*T. It's T*x. So maybe right projection? It's of form x = T*x, where T does NOT contain x. So by rule 2.7 (right projection)…

GPT fires rule 2.7 without verifying that the inner substructure `(y*(z*y))*y` is actually independent of the value of x across the premise set. This is a **superficial syntactic match**: the outer shape matches but the rule's semantic premise is violated. Gemma v4.1 made the same mistake on this problem.

## 3. Mapping to v4.1 and v5.2

| Observed pattern | v4.1 rule | v5.2 rule | Gap |
|---|---|---|---|
| Variable substitution → structural consequence | None | None (STEP 6 adds `x=y=z` forced substitution but only tests projections) | **No explicit substitution-derivation step** |
| Exhaustive 2-element enumeration | Not in witness list | Not in witness list | Witness list only covers 4 canonical magmas (left/right-zero, XOR, constant) |
| Recognize Eq1 forces left/right identity or constant | Partial (2.4, 2.5, 2.6, 2.7) | Same | Rules exist for the conclusion (e.g., right-projection satisfies Eq2), but not for the **derivation** that leads there |
| Guard against over-eager right-projection match | Partial (rule preamble: "check premise literally") | Same | Models still pattern-match the outer `x = T*x` shape without checking T is x-free *as an identity*, not just syntactically |
| Avoid "singleton-only" fallacy | None | None | No anti-pattern warning; Opus makes this mistake in 5/14 confabulations |
| Output format contract | VERDICT+RULE first, HARD-STOP | VERDICT/REASONING/PROOF/COUNTEREXAMPLE fields | v5.2's structured output regresses: breaks HARD-STOP discipline |

**v5.2 diagnosis:** The intent of STEP 6 (force substitution before fallback) is correct — it targets the same gap Opus exploits. But the implementation is narrow (only tests projections) and the output-format change (`REASONING:`/`PROOF:`) dilutes the HARD-STOP lock, encouraging more confabulation. Net regression for both models.

## 4. Suggestions for v.Opus-1

All suggestions keep v4.1 as the base (proven performer) and add targeted techniques from Opus's reasoning while preserving the output contract.

**S1. Add a Substitution Probe step (new, between witness-testing and fallback).**

After canonical witnesses fail, instruct the model to:
1. Set `y := x`, simplify Eq1. If it becomes `x = x` (trivial), mark Eq1 as weak → likely TRUE.
2. Set `x := y` (or `y := x*x`), simplify. If a simpler identity emerges, analyze it.
3. If Eq1 reduces to `u = c*u` (c constant in terms): every element is a right identity → magma satisfies `a*b = b` → check Eq2 in right-projection magma.
4. If Eq1 reduces to `u = u*c`: every element is a left identity → check Eq2 in left-projection magma.

This captures what Opus does in hard1_0007, 0013, 0018, 0034 without asking the model to do unbounded free-form derivation.

**S2. Expand Canonical Witness Library to include more small magmas.**

Current v4.1: left-zero, right-zero, XOR parity, constant (4 magmas).

Add (compact form — one line each):
- `x*y = x + 1 mod n` (cyclic shift) — catches successor-like identities
- `x*y = 0 if x=0 else y` (pointed right-projection) — catches conditional identities
- `x*y = x` unless `x = y`, then `x*x = 0` (diagonal-modified left-projection)

These are all 2-3-element magmas that Opus repeatedly uses. Adding 3 new canonical witnesses costs ~400 bytes.

**S3. Add explicit FORBIDDEN INFERENCES block (anti-confabulation).**

A boxed callout listing three inference patterns the model MUST NOT use:

> **FORBIDDEN:**
> - "Eq1 is restrictive / forces |M| = 1, therefore Eq2 follows" — requires exhaustive 2-element enumeration as proof.
> - "Eq1 and Eq2 have similar structure / same outer shape, therefore Eq2 follows" — outer shape is not a logical connective.
> - "The trivial / constant magma satisfies both, therefore Eq2 follows" — you must verify there is no *non-trivial* magma where Eq1 holds but Eq2 fails.

This directly targets Opus's confabulation pattern and GPT's pattern-match errors. ~300 bytes.

**S4. Tighten right-projection rule premise.**

Rule 2.7 in v4.1 fires on `x = T*x` whenever T is syntactically x-free. Add a required check:

> Before firing 2.7: verify that for at least one element `t ∈ T`, the equation x = t*x is consistent with Eq2. Pattern-matching shape alone is insufficient.

This fixes hard1_0033 (GPT+Gemma both overfired 2.7).

**S5. Keep v4.1's output contract. Drop v5.2's structured fields.**

The `VERDICT: TRUE|FALSE` first line + `RULE: <name>` second line is empirically superior (v4.1 > v5.2 for both models). Do not reintroduce `REASONING:` / `PROOF:` / `COUNTEREXAMPLE:` fields — they dilute HARD-STOP.

**S6. Preserve all existing v4.1 rules.** Nothing in v4.1's 11 TRUE + 7 FALSE + 4 witness routes should be removed. The new material is *additive* and must fit inside the 10,240-byte limit. Target: 9,800 ± 200 bytes.

## 5. Empirical Validation (hard1/2/3, official mode + fallbacks)

Full sweep: both models on all three datasets with `--official-mode --official-fallbacks`. Results versus v4.1 baselines:

| Model / Dataset | v4.1 | v.Opus-1 | Delta | T→F (missed) v4.1 → v.Opus-1 | F→T (confab) v4.1 → v.Opus-1 |
|---|---|---|---|---|---|
| gemma-4-31b hard1 | 52/69 (75.4%) | 49/69 (71.0%) | **−4.4pp** | 12 → 19 | 5 → 1 |
| gemma-4-31b hard2 | 150/200 (75.0%) | 148/200 (74.0%) | −1.0pp | 45 → 49 | 5 → 3 |
| gemma-4-31b hard3 | 246/400 (61.5%) | 229/400 (57.2%) | **−4.3pp** | 108 → 142 | 46 → 29 |
| gpt-oss-120b hard1 | 50/69 (72.5%) | 47/69 (68.1%) | **−4.4pp** | 10 → 14 | 9 → 8 |
| gpt-oss-120b hard2 | 97/200 (48.5%) | 89/200 (44.5%) | **−4.0pp** | 72 → 95 | 31 → 16 |
| gpt-oss-120b hard3 | 238/400 (59.5%) | 241/400 (60.2%) | +0.7pp | 97 → 129 | 65 → 30 |

**v.Opus-1 regressed on 5 of 6 runs.** The design hypothesis did not hold empirically.

## 6. Post-mortem: why v.Opus-1 regressed

The data shows a clear pattern — the guardrails worked, but the Substitution Probe did not compensate:

- **Confabulation went down across the board** (F→T: 46 → 29 for gemma hard3, 65 → 30 for gpt hard3, etc.). The FORBIDDEN INFERENCES block achieved its stated goal: models rejected the singleton-fallacy and shape-similarity shortcuts.
- **Missed-TRUE went UP, not down** (T→F: 12 → 19 for gemma hard1, 108 → 142 for gemma hard3, 72 → 95 for gpt hard2). This is the opposite of what the Substitution Probe was supposed to deliver.

Three contributing failure modes:

1. **The FORBIDDEN INFERENCES block is too aggressive.** Gemma and GPT read "never conclude TRUE from X" as a strong prior against TRUE itself. The list enumerates three anti-patterns — but the model generalizes the caution to "avoid TRUE unless a named rule fires exactly."
2. **The Substitution Probe preconditions are too narrow.** P1/P2/P3 fire only when the reduced equation matches a specific shape (`x = C*x`, `x = x*C`, etc.). In practice, after substitution the reduced form is usually *algebraically close but not literally equal* to a projection shape — so the probe does not fire and the model falls through to default-FALSE.
3. **The models do not simulate substitution symbolically.** Opus's 8K-token reasoning trace actually executes `y := x` and simplifies step by step. Gemma and GPT (especially at `reasoning_effort=low`) sketch the probe in one or two sentences without executing it, then pattern-match the probe result against a fixed shape. No match → default FALSE.

## 7. Revised design directions (for v.Opus-2)

Based on the empirical regression, the next iteration should:

- **Remove** the FORBIDDEN INFERENCES block. The confabulation gain (~20-30 fewer F→T) is dwarfed by the T→F penalty (~40 more missed TRUEs on gemma hard3).
- **Expand** the Substitution Probe to accept algebraically-equivalent shapes, not just literal string matches. E.g. "if after P2 the RHS reduces to a term whose leftmost operation's right operand is x, fire right projection."
- **Keep** the witness library additions (S2) and the tightened 2.7 premise (S4) — neither is implicated in the regression.
- **Consider** a hard1-specific cheatsheet variant that leans on the 9 shared-missed-TRUE problems as training signal for a more targeted TRUE-bias rule.
- **Accept** that v4.1 may be at or near the ceiling of what static cheatsheets achieve with reasoning_effort=low. Reaching Opus's 81% level likely requires either a larger token budget or a fundamentally different prompt architecture (e.g., few-shot with worked examples of successful substitution derivations).

## 8. v.Opus-2 Iteration (hard1 only)

v.Opus-2 replaced v.Opus-1's suppressive guardrails with a single **positive** TRUE-bias rule: `2.13 Restrictive bare source` in STEP 2, firing on any of (maxMult≥3 OR ghost variable OR xCount≥2+rhsVars≥3). Goal: reduce missed-TRUEs by giving models an explicit "strongly constraining equation → TRUE" shortcut.

| Model (hard1) | v4.1 | v.Opus-1 | **v.Opus-2** | T→F | F→T |
|---|---|---|---|---|---|
| gpt-oss-120b | 50 (72.5%) | 47 | **49 (71.0%)** | 10→14→**8** | 9→8→**12** |
| gemma-4-31b | 52 (75.4%) | 49 | **41 (59.4%)** | 12→19→**3** | 5→1→**25** |

**Split outcome:**
- **GPT**: rule worked as intended. Missed-TRUEs dropped from 10 to 8 (best of all runs). Net just -1 vs v4.1.
- **Gemma**: rule *dramatically* over-fired. F→T jumped from 5 to **25** (5× v4.1). Gemma pattern-matches the trigger and fires TRUE without verifying the downstream implication.

Root cause: rule 2.13 was placed in STEP 2 (TRUE routes), so it fires **before** FALSE syntactic routes (STEP 3) and witnesses (STEP 4). Gemma, running at `reasoning_effort=low`, does not evaluate whether Eq2 actually follows — it fires the TRUE verdict and stops.

## 9. v.Opus-2.1 Iteration (hard1 only)

v.Opus-2.1 addresses the Gemma over-fire by relocating the rule from STEP 2 to **STEP 4.5 "Structural TRUE tiebreaker"** — firing only after all TRUE routes, all syntactic FALSE routes, and all 6 witnesses have failed to fire ("all-quiet" regime). Triggers unchanged.

| Model (hard1) | v4.1 | v.Opus-1 | v.Opus-2 | **v.Opus-2.1** | F→T evolution |
|---|---|---|---|---|---|
| gpt-oss-120b | **50 (72.5%)** | 47 | 49 | **43 (62.3%)** | 9 → 8 → 12 → 13 |
| gemma-4-31b | **52 (75.4%)** | 49 | 41 | **49 (71.0%)** | 5 → 1 → **25 → 7** ↓ |

**Outcome:**
- **Gemma recovered as predicted**. F→T dropped from 25 back to 7 (near v4.1's 5). The tiebreaker placement prevented the fire-first-verify-never pattern. But T→T also dropped from 21 to 11 — the tiebreaker catches far fewer TRUE cases because it rarely fires (most problems are decided earlier).
- **GPT regressed unexpectedly**. T→T fell from 16 to 11, and F→T rose from 12 to 13. GPT had been *benefiting* from rule 2.13's STEP-2 placement because GPT actually verifies the downstream implication before committing to TRUE. Moving it to tiebreaker position starved GPT of the TRUE hints.

## 10. Final Experiment Summary — Hard1 (4 iterations × 2 models)

| | v4.1 | v.Opus-1 | v.Opus-2 | v.Opus-2.1 |
|---|---|---|---|---|
| gpt-oss-120b | **50** | 47 | 49 | 43 |
| gemma-4-31b | **52** | 49 | 41 | 49 |
| **Sum (of 138)** | **102** | 96 | 90 | 92 |

**v4.1 remains the best unified cheatsheet.** Four iterations explored the design space; none net-improved on v4.1.

## 11. Conclusions

1. **Static cheatsheets at `reasoning_effort=low` appear to have a ceiling around 72-75% on hard1.** Reaching Opus's 81% likely requires a fundamentally different architecture: few-shot worked examples, larger token budget, or a multi-pass protocol.

2. **Confabulation-reduction and TRUE-recall are in fundamental tension.** Guardrails (FORBIDDEN INFERENCES in v.Opus-1) push down F→T *and* T→T. Amplifiers (rule 2.13 in v.Opus-2) push up both. The net improvement signal in hard1 (+0.5pp across models per percentage point of design change) is smaller than the natural variance between iterations.

3. **Model-specific response to rule placement is significant**: GPT verifies rule triggers; Gemma pattern-matches. A rule that helps one harms the other. Under the "one unified cheatsheet" constraint, the safest choice is one that doesn't change behavior much (v4.1).

4. **Recommendation for Stage-1 submission**: **use v4.1** unless a qualitatively different approach (few-shot, multi-pass, or higher token budget) is adopted. The v.Opus-series iterations are valuable as design-space exploration but do not produce a drop-in replacement.

5. **Path forward (out of scope here)**: test v4.1 + **few-shot worked examples** of Opus-style substitution derivations. Few-shot may transfer the derivation technique without requiring the model to invent it under tight reasoning budget.

## 12. Substantiating the few-shot recommendation

Claim under test: *the derivation technique that effort=low cannot invent under this budget.*

This section decomposes the technique, quantifies the budget gap, and proposes a concrete few-shot template sized to fit the 10KB SAIR limit.

### 12.1 What Opus actually does: four atomic steps

Every one of Opus's successful resolutions of the 9 shared missed-TRUE cases on hard1 follows the same four-step pattern. Concrete trace for **hard1_0007** (`x = (y*(y*(y*z)))*x` ⇒ `x*y = z*(w*(w*y))`, answer TRUE, Opus 52s, both cheatsheet models wrong):

> **Step 1 — Instantiate.** Pick arbitrary elements. "Instantiating `y := a, z := b` in Equation 1 gives `x = (a*(a*(a*b)))*x` for all x."
>
> **Step 2 — Name the instantiated RHS.** "Let `c = a*(a*(a*b))`. Then `c*x = x` for every x, so `c` is a left identity."
>
> **Step 3 — Iterate the derived property.** "Substitute `y := c` back into Equation 1. Using `c*u = u` three times: `c*z = z`, `c*(c*z) = z`, `c*(c*(c*z)) = z`. So Equation 1 becomes `x = z*x` for all x, z. Hence every element is a left identity — the magma is the right-projection magma."
>
> **Step 4 — Evaluate target under the derived structure.** "In right-projection: LHS of Eq 2 = `x*y = y`; RHS = `z*(w*(w*y)) = y`. Both equal y. Eq 2 holds."

The atoms are: **instantiate** (pick specific elements for free variables), **name** (give the resulting compound a short letter), **iterate** (feed the named quantity back into the original equation), **evaluate** (check the target under the derived structural law).

The same four steps resolve hard1_0018 (5-step chain: `y:=x` → (B); `z:=x` in (B) → (B'); `y:=x*x` in original, use (B') to collapse → R2; apply R2 to `(y*x)*y` → R1; combine R1, R2 to get Eq 2). Same for hard1_0041 (2-element exhaustion forces right-projection, then Eq 2 verified under that law).

### 12.2 Why effort=low cannot invent this under the current cheatsheet

We observe three distinct failure modes across GPT and Gemma traces on the same problems:

**A. Sketch-without-execution.** GPT on hard1_0007 correctly identifies the conclusion ("`L = (y*(y*(y*z)))` must be a left identity") but does not execute step 3 (substituting `y := L` back). It drifts into a tangent about "probably false" and defaults FALSE.

**B. Canonical-witness-only.** Gemma on hard1_0007 tests three canonical witnesses (left-zero, right-zero, XOR), observes none satisfies Eq1, checks the 7 syntactic FALSE routes (none fire), and defaults FALSE. No substitution attempt at all.

**C. Depth-2 early termination.** When GPT does attempt a substitution, it stops after one step. It does not feed the result back into Eq1 a second time (step 3 of the pattern). The iterative feedback — substitute, name, substitute the named quantity back — is the step Opus executes and effort=low models do not.

Budget math (approximate, from token accounting in existing runs):

| Stage | Tokens (Gemma effort=low) | Tokens (Opus) |
|---|---|---|
| Read prompt (10KB cheatsheet + equations) | ~2,500 | ~2,500 |
| Feature vector (2.8) | ~150 | ~150 |
| Run 6 witnesses + 7 syntactic FALSE routes | ~500–1,200 | ~400 |
| Invented derivation | ~0 | ~800–2,000 |
| **Budget remaining at effort=low (8192 cap)** | **~4,000** | — |
| **Opus total (no cap)** | — | 3,500–6,000 |

Gemma has technical room — the cap is not the bottleneck. The bottleneck is **procedural**: the cheatsheet prescribes witnesses and syntactic rules, and the model exhausts those before attempting derivation. When the prescribed procedure fails, the default fallback is FALSE, not "attempt substitution derivation." The model does not spontaneously invent a substitution strategy because nothing in the cheatsheet formalizes *which* substitution to try or *what* to look for in the result.

### 12.3 Few-shot template — concrete proposal

A single worked example embedded at the end of the cheatsheet, before the `STEP 5` rewrite fallback, targeting ~900 bytes:

```
STEP 4.6. SUBSTITUTION DERIVATION (worked example; apply by analogy)

Suppose Eq1 is `x = (y*(y*(y*z)))*x` (bare, rhsVars=3, y has maxMult=3).
STEP 2 found no TRUE route; STEP 3 found no FALSE route; STEP 4
found no witness. Apply the following four atomic steps:

(a) INSTANTIATE. Fix arbitrary a, b. Set y:=a, z:=b in Eq1:
    x = (a*(a*(a*b)))*x holds for all x.

(b) NAME. Let c = a*(a*(a*b)). Then c*x = x for every x,
    so c is a left identity.

(c) ITERATE. Substitute y:=c in Eq1 (z free). Use c*u=u three times
    to simplify. Eq1 becomes x = z*x for all x, z. Every element
    is a left identity -> the magma satisfies u*v = v (right projection).

(d) EVALUATE. Plug Eq2 into right projection: every product p*q -> q.
    If both sides of Eq2 reduce to the same variable, answer TRUE.

When Eq1 is bare AND 2.8 features show high multiplicity
(maxMult >= 3) or ghost-variable structure, try steps (a)-(d).
If (c) produces u*v = u (left projection) or u*v = v (right projection)
or u*v = c (constant), evaluate Eq2 accordingly.
RULE: substitution derivation
```

This is a **reusable template**, not a one-off. The same four steps resolved hard1_0007, 0013, 0018, 0041 — four of the nine shared missed-TRUE problems.

### 12.4 Size trade-off (fits in 10,240 bytes)

v4.1 is 10,231 B. Adding ~900 B requires cutting ~900 B elsewhere. Candidates (sizes measured):

- Compress **2.8 motif list** (C1–C15): the 11 motif lines can be condensed into a single 2-line pattern table (`rhsVars, rhsTotals, Lx, Rx, xTop, topShape → TRUE/FALSE`). Saves ~450 B.
- Compress **STEP 3 FALSE routes** (3.1–3.6): the six rules can share a one-line premise template. Saves ~250 B.
- Merge **2.12 T1/T4/T5** heuristics into a single bullet. Saves ~200 B.

Total savings ~900 B, exactly what the worked example needs. Feasibility confirmed.

### 12.5 Expected effect and validation protocol

Hypothesis: few-shot reduces the T→F miss-rate on hard1 by catching 4–6 of the 9 shared missed-TRUE problems (the ones structurally similar to the worked example), without introducing new confabulations (the example is conditioned on STEPs 2–4 having been run first, so the witness filter remains in place).

Quantitative target for a future **v.Opus-3**:
- GPT hard1 ≥ 52 (better than v4.1 by +2)
- Gemma hard1 ≥ 54 (better than v4.1 by +2)
- F→T ≤ v4.1's baseline (9 for GPT, 5 for Gemma)

If achieved, extend to hard2 and hard3 with the same protocol and decide submission from the full sweep.

Risks:
1. The worked example primes a specific shape (`x = (y*...)*x` with high y-multiplicity). Gemma may over-generalize to problems that look similar but are not. Mitigation: keep the trigger condition in the template tight (`maxMult ≥ 3` AND bare AND STEPs 2–4 failed).
2. The example itself consumes tokens during inference (Gemma reads ~200 tokens of the example each call). At 69 problems × 200 = 13,800 extra input tokens; cost increase < $0.002. Acceptable.
3. Few-shot may *reduce* Gemma's confabulation budget (she reads more, thinks less). If T→T drops, abandon few-shot and consider multi-pass architecture (out of Stage-1 scope).
