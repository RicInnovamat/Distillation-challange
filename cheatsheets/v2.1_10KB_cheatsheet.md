You solve implication problems over magmas: sets with one binary operation * and NO assumed laws.
Do NOT assume associativity, commutativity, identity, cancellation, order, or idempotence unless forced by Equation 1.

Task: decide whether Equation 1 implies Equation 2 over ALL magmas.

OUTPUT FORMAT:
Your FIRST line must be exactly one of:
VERDICT: TRUE
VERDICT: FALSE

Then output exactly these headers:
REASONING:
PROOF:
COUNTEREXAMPLE:

If VERDICT is TRUE, PROOF must be non-empty and COUNTEREXAMPLE empty.
If VERDICT is FALSE, COUNTEREXAMPLE must be non-empty and PROOF empty.

IMPORTANT DISCIPLINE

- Never override these rules with free-form algebra.
- If a collapse rule, separator, or FALSE rule fires, stop.
- Only answer TRUE when a listed positive certificate applies.
- If no listed rule proves TRUE, answer FALSE.
- Never invent a counterexample table. Use only the standard separator families listed below.

==================================================
STEP 1. NORMALIZE AND EXTRACT FEATURES
==================================================

For each equation E: L = R, compute only these structural features.

Normalization for exact comparison:
- allow renaming of variables by first appearance
- allow swapping the two sides
- allow global duality: reverse every product recursively on both sides
- allow swap + dual together

Treat two equations as the same only under those transformations.
Do NOT reassociate terms.

Features for each equation E:
- bare(E): one side is a single variable and the other side is a product term
- vars(E): number of distinct variables in the whole equation
- size(E): total number of variable occurrences in both sides
- LP(E): leftmost variable is the same on both sides
- RP(E): rightmost variable is the same on both sides
- SET(E): both sides use the same set of variables
- AB(E): every variable has exactly the same count on both sides
- XOR(E): every variable has the same parity on both sides
- topShape(E): at the top split of each compound side, note v-m, m-v, or m-m when useful

For bare equations only, also note:
- whether the bare variable occurs in the product side
- whether it is the leftmost variable there
- whether it is the rightmost variable there
- how many times it occurs there

==================================================
STEP 2. EXACT / TRIVIAL TRUE CASES
==================================================

Return TRUE immediately if any of these holds:

T0. Equation 2 is exactly the same as Equation 1 under renaming, side swap, and/or global duality.
T1. Equation 2 is x = x.
T2. Equation 2 is an obvious substitution instance or one-context instance of Equation 1.

One-context instance means:
if Equation 1 is L = R, then C[Lσ] = C[Rσ] for one term context C[-] and one substitution σ.

Examples:
- from x*y = y*x infer (x*y)*z = (y*x)*z
- from x*y = x infer z*(x*y) = z*x only if the context is really the same on both sides

If unsure whether T2 really matches exactly, do not use it.

==================================================
STEP 3. SOURCE-COLLAPSE AND PROJECTION RULES
==================================================

These are the strongest positive rules.

3A. Singleton-collapse
If Equation 1 has a side that is a single variable x and the other side is a term not containing x, then Equation 1 collapses all magmas to the singleton case.
Examples:
- x = y
- x = y*z
- x = (y*z)*w
- x = y*(z*w)

Then every equation holds. Return TRUE.

3B. Left projection
If Equation 1 is or forces the family x*y = x, then every product term evaluates to its leftmost variable.
Then Equation 2 holds iff its two sides reduce to the same leftmost variable.
If yes, TRUE; otherwise FALSE.

3C. Right projection
If Equation 1 is or forces the family x*y = y, then every product term evaluates to its rightmost variable.
Then Equation 2 holds iff its two sides reduce to the same rightmost variable.
If yes, TRUE; otherwise FALSE.

Use these projection-source triggers:
- exact source equation x*y = x or x*y = y
- exact notational variant under renaming/swap/dual
- a verified source lemma already known to force projection

Do NOT claim projection unless it is explicit or already validated.

3D. Constant-operation family
If Equation 1 forces all binary products to have the same value c, then every non-variable product term evaluates to c.
Under this rule:
- every product term becomes c
- a bare variable remains itself

Then Equation 2 holds iff both sides reduce to the same symbol under that evaluation.

Warning:
constant-operation does NOT by itself imply singleton collapse.
So do NOT infer x = y*z from constant-operation alone.

==================================================
STEP 4. MONOTONE FALSE SEPARATORS
==================================================

If any separator below fires, return FALSE immediately.

S1. If LP(A) is true and LP(B) is false, FALSE.
S2. If RP(A) is true and RP(B) is false, FALSE.
S3. If SET(A) is true and SET(B) is false, FALSE.
S4. If AB(A) is true and AB(B) is false, FALSE.
S5. If XOR(A) is true and XOR(B) is false, FALSE.

These act as monotone invariants: Equation 1 cannot imply a target that breaks a preserved invariant.

==================================================
STEP 5. FAMILY RULES
==================================================

Classify Equation 1 as closely as possible into one of these source families:

F1. singleton-collapse
F2. constant-operation
F3. left projection
F4. right projection
F5. left-constancy: x*y = x*z
F6. right-constancy: x*y = z*y
F7. commutativity: x*y = y*x
F8. idempotence: x*x = x
F9. linear balanced law
F10. duplication / nested law

Use these positive family consequences only.

P1. singleton-collapse implies every Equation 2.
P2. left projection implies x*y = x*z and x*x = x.
P3. right projection implies x*y = z*y and x*x = x.
P4. commutativity implies only exact substitution/context instances of commutativity.
P5. idempotence implies only exact self-duplication eliminations t*t = t and direct instances.
P6. left-constancy implies only laws expressing irrelevance of the right input in the same structural pattern.
P7. right-constancy implies only laws expressing irrelevance of the left input in the same structural pattern.

Use these safe non-implications.

N1. commutativity does not imply idempotence.
N2. commutativity does not imply projection.
N3. idempotence does not imply commutativity.
N4. idempotence does not imply projection.
N5. left-constancy does not imply right-constancy.
N6. right-constancy does not imply left-constancy.
N7. constant-operation does not imply singleton-collapse.
N8. left projection does not imply right projection.
N9. right projection does not imply left projection.

If Equation 2 requires one of the stronger target families above but Equation 1 is only in a weaker or different family, return FALSE.

==================================================
STEP 6. STANDARD SEPARATOR MODELS
==================================================

Use only these separator families when giving a FALSE proof.

M1. Left-zero magma: a*b = a
Validates left projection and many left-sensitive laws.
Usually falsifies right projection, right-constancy, and commutativity.

M2. Right-zero magma: a*b = b
Validates right projection and many right-sensitive laws.
Usually falsifies left projection, left-constancy, and commutativity.

M3. Constant magma: a*b = c
Validates constant-operation laws and equalities between product terms.
Does not generally validate bare-variable = product laws.

M4. XOR on {0,1}
Validates commutativity.
Falsifies idempotence and projection.

M5. Min or Max on {0,1}
Validate commutativity and idempotence.
Falsify projection, constancy, and collapse.

When VERDICT is FALSE, cite the most relevant separator family above.
Do not fabricate a full multiplication table unless the family is one of M1-M5.

==================================================
STEP 7. RESTRICTED LOCAL REWRITE FALLBACK
==================================================

Use this only if no earlier step fired.

You may prove TRUE by at most one or two local rewrites using Equation 1, and only under these restrictions:

R1. Equation 1 must be used as an equality schema L = R.
R2. Rewrite only a matching subterm Lσ or Rσ.
R3. Use only a safe direction: the rewritten-to term must not introduce variables absent from the matched subterm.
R4. After at most two safe rewrites, Equation 2 must match exactly.

Example:
from x*y = y*x infer ((x*y)*z) = ((y*x)*z).

If the rewrite is not exact and short, do not use it.

==================================================
STEP 8. CONSERVATIVE FINAL RULE
==================================================

If no earlier TRUE rule applies, answer FALSE.

Do NOT answer TRUE because:
- Equation 1 looks stronger
- Equation 2 looks simpler
- a long derivation might exist
- a guessed counterexample was not found

Only explicit certificates justify TRUE.

==================================================
REASONING STYLE
==================================================

REASONING must briefly state:
- the key features used
- whether a collapse/projection/constant rule fired
- whether a separator fired
- or which exact family / substitution / rewrite certificate decided the case

If TRUE:
- PROOF must name the exact certificate: exact match, singleton-collapse, projection evaluation, constant-operation evaluation, substitution/context instance, or restricted local rewrite
- COUNTEREXAMPLE must be empty

If FALSE:
- PROOF must be empty
- COUNTEREXAMPLE must name one of:
  left-zero, right-zero, constant magma, XOR, min/max, or invariant separator

==================================================
PROBLEM
==================================================

Equation 1: {{ equation1 }}
Equation 2: {{ equation2 }}
