You decide equational implication over magmas: a set with one binary operation \* and no axioms.

Question: Does {{ equation1 }} imply {{ equation2 }} over ALL magmas?

OUTPUT FORMAT (mandatory, strict)
Your FIRST line must be exactly one of:

- VERDICT: TRUE
- VERDICT: FALSE
  Your SECOND line must be exactly:
  RULE: <short rule name>
  Output VERDICT and RULE first. Reasoning goes AFTER, not before.
  After the two header lines you may add at most 3 short sentences.
  If you are uncertain, output VERDICT: FALSE with RULE: default false.
  HARD-STOP: Once a FALSE rule or counterexample fires, emit VERDICT: FALSE + RULE and STOP. Never continue reasoning or override a counterexample.

FORBIDDEN INFERENCES (never reasons for VERDICT: TRUE)

- "Eq1 is too restrictive / forces |M|=1": only rule 2.3 (`x = T`, x not in T) concludes singleton. Any other shape needs exhaustive test of all 16 two-element magmas.
- "Eq1 and Eq2 have similar outer shape": shape similarity is not implication. Only rule 2.1 concludes from shape.
- "Trivial / constant magma satisfies both, therefore TRUE": never valid alone. Use 4.4 only for FALSE.
- "Rules 2.6 / 2.7 fire because T is syntactically x-free": also check T stays x-free under any identity Eq1 itself forces.

IMPORTANT GLOBAL DISCIPLINE

- Follow the STEPS in order. Stop at the first decisive route.
- Never override an exact route with free-form algebra.
- Never use a syntactic FALSE rule unless you checked its literal premise on the written equations.
- Once a counterexample is verified or a FALSE rule fires: emit VERDICT: FALSE, STOP.
- If no route fires and the Substitution Probe (STEP 4.5) does not produce structure, answer FALSE.

STEP 0. QUICK META-CHECK
Read both equations as binary trees.
Useful terms:

- leftmost / rightmost variable = first / last variable in leaf-reading
- WORD(term) = full left-to-right leaf list
- PARITY(term) = odd/even count of each variable
- SET(term) = set of distinct variables
- AB(term) = exact count of each variable (multiset)
- bare = one side is a single variable (see BARE CHECK in 2.5)

STEP 1. EXACT NORMALIZATION
You may: rename variables consistently; swap sides of a single equation; dualize BOTH equations by reversing every product. Do not otherwise simplify.

STEP 2. TRUE ROUTES

2.1 Exact identity. If Eq2 equals Eq1 up to consistent variable renaming → TRUE. RULE: exact renaming

2.2 Tautological target. If Eq2 is `x = x` → TRUE. RULE: tautological target

2.3 Singleton / collapse source. If Eq1 has the form `x = T` where x does NOT appear anywhere in T, Eq1 forces a singleton magma → TRUE. Side-swap `T = x` also counts. RULE: singleton collapse

2.4 Constant-operation source. If Eq1 is `A = B` where A and B are non-variable product terms with disjoint variable sets, all products equal one constant → TRUE. RULE: constant operation

2.5 Source-collapse lemmas.
BARE CHECK: one side of Eq1 is a single variable (no \*) — bare. The variable CAN appear in the product side.
Normalize: single variable on LEFT as x; rename others by first appearance to y, z, w, ...
Canonical shapes (verify literally):

- `x = x*(y*(z*(x*y)))` or `x = x*((y*z)*(z*z))` → LEFT PROJECTION: p\*q = p
- `x = (((y*z)*x)*z)*x` → RIGHT PROJECTION: p\*q = q
  If fired, evaluate Eq2 under that projection (collapse each product p\*q to leftmost / rightmost). Both sides same variable → TRUE, else FALSE. RULE: source collapse

2.6 Left projection family. If Eq1 is bare of the form `x = x * T` where T does NOT contain x → Eq1 forces `a*b = a`. Evaluate Eq2 under that law. Matches include x = x\*y, x = x*(y*z), x = x*(y*(z*w)). RULE: left projection

2.7 Right projection family. Dual of 2.6. If Eq1 is bare of the form `x = T * x` where T does NOT contain x → Eq1 forces `a*b = b`. Evaluate Eq2 under that law. **Premise check**: verify T has no occurrence of x AND no variable in T is forced to equal x by Eq1's own substructure (if Eq1 induces `y = x` for every y, do not fire). RULE: right projection

2.8 Bare-source contradiction motifs.
One side of Eq1 bare (x in product OK); no earlier TRUE route fired.
Normalize: single variable LEFT as x; keep full bracketing on product side P.
Compute these 7 features of P:

- rhsVars, Lx, Rx, xTop, topShape, rhsTotals, xCount
  Definitions: rhsVars=distinct var count; Lx=x leftmost?; Rx=x rightmost?; xTop=x lives in U(left)/V(right)/both of top split U\*V; topShape=v-m/m-v/m-m; rhsTotals=sorted occurrence counts (e.g. "112"); xCount=count of x in P.
  MANDATORY: write all 7 features as a vector BEFORE checking motifs. Format: rhsVars=\_, Lx=\_, Rx=\_, xTop=\_, topShape=\_, rhsTotals=\_, xCount=\_.
  If any motif below matches → TRUE:
  C1: rhsVars>=4, Lx=F, Rx=F → TRUE
  C4: rhsVars=3, rhsTotals=112, Lx=F, Rx=F, xTop=right, topShape=v-m → TRUE
  C5: rhsVars=4, rhsTotals=1112, Lx=F, Rx=F, xTop=right, topShape=v-m → TRUE
  C6: rhsVars=3, xTop=right, topShape=v-m, xCount=2 → TRUE
  C7: rhsVars=3, Lx=F, Rx=F, xTop=left, topShape=m-v, xCount=2 → TRUE
  C8: rhsVars=3, Lx=T, xTop=left, topShape=m-v → TRUE
  C9: rhsVars=3, rhsTotals=122, Lx=T, Rx=F, xTop=both, topShape=v-m → TRUE
  C11: rhsVars=3, rhsTotals=113, Lx=F, Rx=F, xTop=right, topShape=v-m → TRUE
  C12: rhsVars=3, rhsTotals=113, Lx=F, Rx=F, xTop=left, topShape=m-v → TRUE
  C13: rhsVars=4, rhsTotals=1112, Lx=F, Rx=T → TRUE
  C15: rhsVars>=4, Lx=F → TRUE
  RULE: contradiction motif

2.9 Extended projection. If Eq1 has shape `x = (x*y)*x` or `x = ((x*y)*z)*x` and Eq2 preserves leading x while reshaping → TRUE. RULE: projection family

2.10 Square reduction. If Eq1 is one of `x*x=x`, `x*(x*x)=x`, `(x*x)*x=x`, and Eq2 is obtained by replacing a repeated x-block with x → TRUE. RULE: square reduction

2.11 Exact instance. If Eq2 is exactly a substitution or one-hole context instance of Eq1 → TRUE. RULE: exact instance

2.12 Structural TRUE heuristics (weaker; tiebreaker only):
T1: Eq1 bare, vars(Eq1)>=3, size(Eq2)>size(Eq1) → TRUE. (size = total variable occurrences)
T4: Eq1 bare, vars(Eq1)>=4, vars(Eq2)=2 → TRUE.
T5: vars(Eq2)<vars(Eq1) AND imbalance(Eq2)>imbalance(Eq1) → TRUE. (imbalance = Σ |leftCount(v) − rightCount(v)|)
RULE: structural heuristic

STEP 3. CLEAR SYNTACTIC FALSE ROUTES
Valid only when the literal premise is satisfied exactly.

3.0 Spine Isolation (McKenna). Apply only if Eq1 is bare (`x = T`) AND x appears exactly once in T. Trace path from root of T to x: at each \* node record L or R.

- Pure left-spine (all-L, e.g. `x=((x*y)*z)*w` → LLL).
- Pure right-spine (all-R, e.g. `x=y*(z*(w*x))` → RRR).
- Mixed: both L and R.
  Do the same for Eq2.
  Rule: pure left-spine Eq1 → Eq2 must be pure left-spine of depth >= Eq1; pure right-spine analogous; same spine type with depths n, m needs n | m. Otherwise FALSE. RULE: spine isolation

3.1 WORD exclusion. Eq1 same WORD both sides but Eq2 different → FALSE. RULE: word exclusion
3.2 PARITY exclusion. Eq1 same PARITY both sides but Eq2 different → FALSE. RULE: parity exclusion
3.3 Leftmost exclusion. Eq1 same leftmost-var both sides but Eq2 not → FALSE. RULE: leftmost exclusion
3.4 Rightmost exclusion. Eq1 same rightmost-var both sides but Eq2 not → FALSE. RULE: rightmost exclusion
3.5 SET exclusion. Eq1 same variable SET both sides but Eq2 not → FALSE. RULE: set exclusion
3.6 AB exclusion. Eq1 same exact variable counts both sides but Eq2 not → FALSE. RULE: count exclusion

STEP 4. SMALL FINITE WITNESS ROUTES
A counterexample is decisive only if Eq1 holds for ALL assignments and Eq2 fails for SOME.
HARD STOP: once a counterexample verifies, output VERDICT: FALSE immediately and stop.

4.1 Left-zero (a\*b=a): recursively replace each A\*B by A. Eq1 same var both sides → holds; Eq2 different → FALSE. RULE: left-zero witness
4.2 Right-zero (a\*b=b): recursively replace each A\*B by B. Eq1 holds, Eq2 different → FALSE. RULE: right-zero witness
4.3 XOR parity (a\*b=a+b mod 2): holds iff same PARITY both sides. Eq1 yes, Eq2 no → FALSE. RULE: XOR parity witness
4.4 Constant (a\*b=0 or 1): replace all products with the constant. Eq1 holds, Eq2 fails → FALSE. RULE: constant witness
4.5 Cyclic shift on Z/3 (a\*b = a+1 mod 3): evaluate both sides. Eq1 holds (id), Eq2 fails → FALSE. RULE: cyclic witness
4.6 Pointed right-projection (a\*b = b unless a=0, then 0\*b=0): evaluate both sides as tables. Eq1 holds, Eq2 fails → FALSE. RULE: pointed witness

STEP 4.5. SUBSTITUTION PROBE (mandatory before default-FALSE)
Apply if STEPs 2, 3, 4 did not decide. Catches cases where Eq1 silently forces projection or constant structure the canonical witnesses missed.

Execute these three probes on Eq1:

(P1) Total collapse: set every non-x variable to x; simplify. If the result is an x-only identity (`x=x`, `x=x*x`, `x*x=x`, `(x*x)*x=x`), re-run STEP 2.10. If it fires → TRUE. RULE: substitution probe (square)

(P2) Single collapse: set y := x (first non-x var), keep others; simplify.

- Shape `x = C * x` with x not in C → fire 2.7. RULE: substitution probe (right proj)
- Shape `x = x * C` with x not in C → fire 2.6. RULE: substitution probe (left proj)

(P3) Square: for each non-x variable v try `v := x*x`; simplify. If result matches a projection / square pattern → fire that TRUE rule. RULE: substitution probe (square-derived)

If no probe recognizes a structure AND no earlier route fired → FALSE. RULE: default false

STEP 5. TINY EXACT REWRITE
Use only if STEPs 2–4.5 did not decide. Write Eq1 as L = R. You may:

- choose a substitution for L and R
- replace one exact occurrence of Lσ by Rσ (or Rσ by Lσ) inside a one-hole context
  Restrictions: at most 2 steps; exact subterm replacement only; no invented lemmas.
  If you reach Eq2 exactly, answer TRUE. RULE: exact rewrite

FINAL REMINDERS

- VERDICT and RULE always appear; RULE is never blank.
- Syntactic FALSE routes require exact literal premise match.
- 2.6 / 2.7: verify T stays x-free after any Eq1-forced identity.
- COUNTEREXAMPLE LOCK: a verified counterexample is decisive; never override it.
- SUBSTITUTION PROBE (P1,P2,P3) is the only licensed derivation tool; invent nothing beyond it.
