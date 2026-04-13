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

IMPORTANT GLOBAL DISCIPLINE

- Follow the STEPS in order. Stop at the first decisive route.
- Never override an exact route with free-form algebra.
- Never use a syntactic FALSE rule unless you checked its literal premise on the written equations.
- Once a counterexample is verified or a FALSE rule fires: emit VERDICT: FALSE, STOP. Never reconsider.
- If no exact TRUE route fires and no exact FALSE route fires, answer FALSE.

STEP 0. QUICK META-CHECK
Read both equations as binary trees. Useful terms: leftmost/rightmost variable (first/last in leaf-reading); WORD(term)=leaf list; PARITY(term)=odd/even count per var; SET(term)=distinct vars; AB(term)=exact count per var (multiset); bare=one side is a single variable (see 2.5).

STEP 1. EXACT NORMALIZATION
You may: rename variables consistently; swap sides of a single equation; dualize BOTH equations by reversing every product. Do not otherwise simplify.

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
BARE CHECK: Is one side of Eq1 a single variable (no \*)? → bare. x CAN appear in the product side.
If bare, normalize: put single variable on LEFT as x, rename others by first appearance to y, z, w, ...
Compare normalized Equation 1 to these canonical forms:

- x = x\*(y*(z*(x*y))) → LEFT PROJECTION: p\*q = p
- x = x\*((y*z)*(z*z)) → LEFT PROJECTION: p\*q = p
- x = (((y*z)*x)*z)\*x → RIGHT PROJECTION: p\*q = q
  If a collapse lemma fires, evaluate Equation 2 under that projection:
- LEFT PROJECTION: every product collapses to its leftmost variable
- RIGHT PROJECTION: every product collapses to its rightmost variable
  If both sides of Equation 2 collapse to the same variable, answer TRUE; otherwise FALSE.
  RULE: source collapse

  2.6 Left projection family (generalized)
  If Equation 1 is bare and has the form x = x \* T, where T is any product term (possibly deeply nested) that does NOT contain x, then Equation 1 forces left-projection-like behavior: a\*b = a for all a,b.
  If Equation 2 also holds when every product p\*q is replaced by p (leftmost variable), answer TRUE.
  Examples that match: x = x*y, x = x*(y*z), x = x*(y*(z*w)), x = x*(y*(z*(w*u))), x = x*((y*z)*(w\*u)).
  RULE: left projection

  2.7 Right projection family (generalized)
  Dual of 2.6. If Equation 1 is bare and has the form x = T \* x, where T does NOT contain x, then Equation 1 forces right-projection-like behavior: a\*b = b for all a,b.
  If Equation 2 also holds when every product p\*q is replaced by q (rightmost variable), answer TRUE.
  Examples that match: x = y*x, x = (y*z)*x, x = ((y*z)*w)*x, x = ((y*z)*(w*u))\*x.
  RULE: right projection

  2.8 Bare-source contradiction motifs
  Apply if one side of Eq1 is a single variable (bare — x in product OK) and no earlier TRUE route fired. Normalize: single variable on LEFT as x, keep full bracketing on product side P. Compute P-features: rhsVars (distinct var count); Lx (x leftmost?); Rx (x rightmost?); xTop (x lives in U/V/both of top split U\*V); topShape (v-m/m-v/m-m); rhsTotals (sorted occurrence counts, e.g. "112"); xCount (count of x in P); maxMult (max single-variable multiplicity on P).
  MANDATORY: Write the feature vector BEFORE checking motifs: rhsVars=\_, Lx=\_, Rx=\_, xTop=\_, topShape=\_, rhsTotals=\_, xCount=\_, maxMult=\_. Do not skip.

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

  2.13 Restrictive bare source (NEW in v.Opus-2)
  Apply only if Eq1 is bare AND no earlier TRUE route fired AND no STEP 3/4 FALSE route has fired.
  If ANY of these structural indicators hold on the product side P of Eq1:
  - maxMult >= 3 (some single variable occurs 3 or more times on P), OR
  - there exists a variable in P that does NOT appear on Eq2 (one-sided ghost: Eq1 constrains a variable Eq2 does not mention), OR
  - xCount >= 2 AND rhsVars >= 3 (x recurs inside P with multiple other variables)
  then Eq1 imposes a strongly constraining identity, answer TRUE.
  RULE: restrictive bare source

STEP 3. CLEAR SYNTACTIC FALSE ROUTES (valid only when literal premise is satisfied exactly)

3.0 Spine Isolation (McKenna). Apply only if Eq1 is bare (x=T) AND x appears exactly once in T. Trace path from root of T to x; at each \* node record L or R.
- Pure left-spine: all-L (e.g. x=((x*y)*z)\*w → LLL).
- Pure right-spine: all-R (e.g. x=y*(z*(w\*x)) → RRR).
- Mixed: both L and R.
Do the same for Eq2. Pure left-spine Eq1 → Eq2 must be pure left-spine depth >= Eq1. Pure right-spine analogous. Same spine type with depths n,m → need n divides m. Else FALSE. RULE: spine isolation

3.1 WORD exclusion. Same WORD Eq1 both sides, different Eq2 → FALSE. RULE: word exclusion
3.2 PARITY exclusion. Same PARITY Eq1 both sides, different Eq2 → FALSE. RULE: parity exclusion
3.3 Leftmost exclusion. Same leftmost-var Eq1 both sides, different Eq2 → FALSE. RULE: leftmost exclusion
3.4 Rightmost exclusion. Same rightmost-var Eq1 both sides, different Eq2 → FALSE. RULE: rightmost exclusion
3.5 SET exclusion. Same variable SET Eq1 both sides, different Eq2 → FALSE. RULE: set exclusion
3.6 AB exclusion. Same exact variable counts Eq1 both sides, different Eq2 → FALSE. RULE: count exclusion

STEP 4. SMALL FINITE WITNESS ROUTES
A counterexample is decisive only if Eq1 holds for ALL assignments and Eq2 fails for SOME.
HARD STOP: once you verify a counterexample, output VERDICT: FALSE immediately and stop.

4.1 Left-zero (a\*b=a): recursively replace each A\*B → A until single var. Eq1 same var both sides → holds; Eq2 different → FALSE. RULE: left-zero witness
4.2 Right-zero (a\*b=b): recursively replace A\*B → B. Eq1 holds, Eq2 different → FALSE. RULE: right-zero witness
4.3 XOR parity (a\*b=a+b mod 2): holds iff same PARITY both sides. Eq1 yes, Eq2 no → FALSE. RULE: XOR parity witness
4.4 Constant (a\*b=0 or 1): replace all products with constant. Eq1 holds, Eq2 fails → FALSE. RULE: constant witness
4.5 Cyclic shift on Z/3 (a\*b = a+1 mod 3): evaluate both sides. Eq1 identity → holds; Eq2 non-identity → FALSE. RULE: cyclic witness
4.6 Pointed right-projection (a\*b = b for a!=0, 0\*b = 0): evaluate as table. Eq1 holds, Eq2 fails → FALSE. RULE: pointed witness

STEP 5. TINY EXACT REWRITE
Use only if STEPs 2-4 did not decide. Write Eq1 as L = R. You may choose a substitution for L and R; replace one exact occurrence of Lσ by Rσ (or Rσ by Lσ) inside a one-hole context. At most 2 steps; exact subterm replacement only; no invented lemmas. If you reach Eq2 exactly → TRUE. RULE: exact rewrite

FINAL REMINDERS

- VERDICT and RULE always appear; RULE is never blank.
- Syntactic FALSE routes require exact literal premise match.
- For 2.6 / 2.7: verify T does NOT contain x.
- COUNTEREXAMPLE LOCK: verified counterexamples are decisive; never override.
