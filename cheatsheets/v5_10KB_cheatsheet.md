You are solving equational implication problems over magmas (set + one binary operation \*, no other axioms).
Task: does {{ equation1 }} imply {{ equation2 }} over ALL magmas?

OUTPUT FORMAT (mandatory)
- Plain text only.
- No extra headings or notes.
- `VERDICT:` must be exactly `TRUE` or `FALSE`.
- `REASONING:` must always be filled.
- If `VERDICT: TRUE`, `PROOF:` must be non-empty and `COUNTEREXAMPLE:` empty.
- If `VERDICT: FALSE`, `COUNTEREXAMPLE:` must be non-empty and `PROOF:` empty.
HARD-STOP: Once a FALSE rule or counterexample fires, emit VERDICT: FALSE and STOP. Never override.

GLOBAL DISCIPLINE
- Follow STEPS in order. Stop at the first decisive route.
- Never override an exact route with free-form algebra.
- Never fire a syntactic FALSE rule without checking its literal premise.
- Counterexample verified or FALSE rule fires → VERDICT: FALSE, STOP. Never reconsider.
- No exact route fires → answer FALSE.

STEP 0. NORMALIZE
For EACH equation independently:
  0a. Read the equation as L = R.
  0b. SWAP: if one side is a single variable, put it on the LEFT.
      Otherwise, put the side with fewer nodes on the LEFT.
      If tied on nodes, put the side with fewer distinct variables on the LEFT.
  0c. RENAME variables by first-appearance order reading left-to-right
      (LHS first, then RHS): first → x, second → y, third → z, fourth → w, fifth → u.
  0d. Write the normalized equation. Use it for ALL subsequent steps.

You may also DUALIZE both equations together (reverse every product in both).
Pick whichever form has the smaller/simpler Equation 1.

Examples:
  Raw: (a * b) * a = a → swap (bare) → a = (a * b) * a → rename → x = (x * y) * x
  Raw: (b * a) * c = b * (a * c) → no swap → rename b→x,a→y,c→z → (x * y) * z = x * (y * z)
  Raw: m = (((n * p) * m) * p) * m → already bare-left → rename m→x,n→y,p→z → x = (((y * z) * x) * z) * x

STEP 1. EXTRACT FEATURES (from normalized forms)
Read both normalized equations as binary trees. Definitions:
- leftmost/rightmost variable = first/last leaf in left-to-right reading
- WORD(term) = full leaf list, PARITY(term) = odd/even count per variable
- SET(term) = distinct variables, AB(term) = exact count per variable (multiset)
- bare = one side is a single variable

STEP 2. TRUE ROUTES

2.1 Exact identity
If Equation 2 is identical to Equation 1 up to consistent variable renaming, answer TRUE.
RULE: exact renaming

2.2 Tautological target
If Equation 2 is of the form x = x, answer TRUE.
RULE: tautological target

2.3 Singleton / collapse source
If Equation 1 has the form x = T where x does not appear anywhere in T, then Equation 1 forces a singleton magma. Answer TRUE. Side-swapped T = x also counts.
RULE: singleton collapse

2.4 Constant-operation source
If Equation 1 has the form A = B where both A and B are non-variable product terms, and the variable sets of A and B are disjoint, then all products equal one constant. Answer TRUE.
RULE: constant operation

2.5 Source-collapse lemmas
BARE CHECK: one side of Eq1 is a single variable (no *)? → bare. x CAN appear in the product side.
If bare, normalize: single variable on LEFT as x, rename others by first appearance.
Match normalized Eq1 against:
- x = x*(y*(z*(x*y))) → LEFT PROJ (p\*q=p)
- x = x*((y*z)*(z*z)) → LEFT PROJ (p\*q=p)
- x = (((y*z)*x)*z)*x → RIGHT PROJ (p\*q=q)
If match: evaluate Eq2 under that projection. Both sides same variable → TRUE; else FALSE.
RULE: source collapse

2.6 Left projection family
If Eq1 is bare: x = x * T where T does NOT contain x → forces a*b=a.
If Eq2 holds when every p*q → p (leftmost var), answer TRUE.
Matches: x=x*y, x=x*(y*z), x=x*(y*(z*w)), x=x*(y*(z*(w*u))), x=x*((y*z)*(w\*u)).
RULE: left projection

2.7 Right projection family
Dual: x = T * x where T does NOT contain x → forces a*b=b.
If Eq2 holds when every p*q → q (rightmost var), answer TRUE.
Matches: x=y*x, x=(y*z)*x, x=((y*z)*w)*x, x=((y*z)*(w*u))\*x.
RULE: right projection

2.8 Bare-source contradiction motifs
Apply if Eq1 is bare and no earlier TRUE route fired.
Normalize: single var on LEFT as x, product side = P. Compute features of P:

- rhsVars = number of distinct variables on P
- Lx = is x the leftmost variable of P?
- Rx = is x the rightmost variable of P?
- xTop: at the top product split U\*V, does x occur only in U (left), only in V (right), or both?
- topShape: v-m if top is variable*product, m-v if product*variable, m-m if product\*product
- rhsTotals = sorted occurrence counts on P (e.g. counts 2,1,1 → "112")
- xCount = number of occurrences of x in P

MANDATORY: Write all 7 features as a vector BEFORE checking motifs below.
Format: rhsVars=_, Lx=_, Rx=_, xTop=_, topShape=_, rhsTotals=_, xCount=_
Only after writing the vector, compare against each motif. Do not skip.

If any motif below matches, answer TRUE immediately:
C1: rhsVars >= 4 AND Lx=FALSE AND Rx=FALSE → TRUE
C4: rhsVars=3, rhsTotals=112, Lx=FALSE, Rx=FALSE, xTop=right, topShape=v-m → TRUE
C5: rhsVars=4, rhsTotals=1112, Lx=FALSE, Rx=FALSE, xTop=right, topShape=v-m → TRUE
C6: rhsVars=3, xTop=right, topShape=v-m, xCount=2 → TRUE
C7: rhsVars=3, Lx=FALSE, Rx=FALSE, xTop=left, topShape=m-v, xCount=2 → TRUE
C8: rhsVars=3, Lx=TRUE, xTop=left, topShape=m-v → TRUE
C9: rhsVars=3, rhsTotals=122, Lx=TRUE, Rx=FALSE, xTop=both, topShape=v-m → TRUE
C11: rhsVars=3, rhsTotals=113, Lx=FALSE, Rx=FALSE, xTop=right, topShape=v-m → TRUE
C12: rhsVars=3, rhsTotals=113, Lx=FALSE, Rx=FALSE, xTop=left, topShape=m-v → TRUE
C13: rhsVars=4, rhsTotals=1112, Lx=FALSE, Rx=TRUE → TRUE
C15: rhsVars >= 4 AND Lx=FALSE → TRUE
RULE: contradiction motif

2.9 Extended projection family
If Equation 1 has one of these shapes:

- x = (x*y)*x, x = ((x*y)*z)\*x
  and Equation 2 preserves the leading x while reshaping, answer TRUE.
  RULE: projection family

  2.10 Square-reduction family
  If Equation 1 is x*x = x, x*(x*x) = x, or (x*x)\*x = x, and the target is obtained by replacing a repeated x-block by x, answer TRUE.
  RULE: square reduction

  2.11 Direct exact instance
  If Equation 2 is exactly a substitution instance or one-hole context instance of Equation 1, answer TRUE.
  RULE: exact instance

  2.12 Structural TRUE heuristics (use only if no earlier route fired)
  These are weaker rules — use as tiebreakers before defaulting FALSE.
  T1: If Equation 1 is bare with vars(Eq1) >= 3 and size(Eq2) > size(Eq1), answer TRUE.
  (size = total variable occurrences on both sides)
  T4: If Equation 1 is bare with vars(Eq1) >= 4 and vars(Eq2) = 2, answer TRUE.
  T5: If vars(Eq2) < vars(Eq1) and imbalance(Eq2) > imbalance(Eq1), answer TRUE.
  (imbalance = sum of |leftCount(v) - rightCount(v)| for each variable v)
  RULE: structural heuristic

STEP 3. CLEAR SYNTACTIC FALSE ROUTES
Valid only when their literal premise is satisfied exactly.

3.0 Spine Isolation (McKenna theorem)
Apply only if Eq1 is bare (x = T) AND x appears exactly once in T. Trace path from root of T to x: at each * node record L or R.
- Pure left-spine: all-L (e.g. x=((x*y)*z)*w → LLL, depth 3)
- Pure right-spine: all-R (e.g. x=y*(z*(w*x)) → RRR, depth 3)
- Mixed: both L and R.
Do the same for Eq2 (normalize as y = S).
- Pure left-spine Eq1 → Eq2 must be pure left-spine with depth >= Eq1. Otherwise FALSE.
- Pure right-spine Eq1 → Eq2 must be pure right-spine with depth >= Eq1. Otherwise FALSE.
- Same spine type: Eq1 depth n, Eq2 depth m → need n divides m. If not, FALSE.
RULE: spine isolation

3.1 WORD exclusion
If both sides of Eq1 have the same WORD, but Eq2's sides have different WORD → FALSE.
RULE: word exclusion

3.2 PARITY exclusion
If both sides of Eq1 have the same PARITY, but Eq2's sides have different PARITY → FALSE.
RULE: parity exclusion

3.3 Leftmost-variable exclusion
If Eq1 has the same leftmost variable on both sides, but Eq2 does not → FALSE.
RULE: leftmost exclusion

3.4 Rightmost-variable exclusion
If Eq1 has the same rightmost variable on both sides, but Eq2 does not → FALSE.
RULE: rightmost exclusion

3.5 SET exclusion
If both sides of Eq1 use the same variable set, but Eq2's sides use different sets → FALSE.
RULE: set exclusion

3.6 AB (exact count) exclusion
If both sides of Eq1 have the same exact variable counts, but Eq2's sides do not → FALSE.
RULE: count exclusion

STEP 4. SMALL FINITE WITNESS ROUTES
Counterexample is decisive only if Eq1 holds for ALL assignments and Eq2 fails for SOME.
HARD STOP: verified counterexample → VERDICT: FALSE immediately, stop.

4.1 Left-zero (a*b=a): recursively replace each A*B → A until single var.
Do both sides of Eq1: same var → holds. Then Eq2: different → FALSE.
RULE: left-zero witness

4.2 Right-zero (a*b=b): recursively replace each A*B → B until single var.
Do both sides of Eq1: same var → holds. Then Eq2: different → FALSE.
RULE: right-zero witness

4.3 XOR parity (a*b=a+b mod 2): eq holds iff same PARITY both sides.
Eq1 same, Eq2 different → FALSE. RULE: XOR parity witness

4.4 Constant (a*b=0 or a*b=1): replace all products with constant.
Eq1 holds, Eq2 fails → FALSE. RULE: constant witness

STEP 5. TINY EXACT REWRITE
Use only if STEPs 2-4 did not decide. Write Eq1 as L = R. You may:
- substitute variables in L and R
- replace one occurrence of Lσ by Rσ (or vice versa) in a one-hole context
At most 2 steps, exact subterm replacement only, no invented lemmas.
If you reach Eq2 exactly → TRUE. RULE: exact rewrite

FINAL REMINDERS
- VERDICT must always appear. Cite the RULE name in REASONING.
- Syntactic FALSE routes: check literal premise before firing.
- For left/right projection: T must NOT contain x.
- COUNTEREXAMPLE LOCK: verified counterexample is decisive. Never override.
