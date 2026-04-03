You are solving equational implication problems over magmas (a set with one binary operation * and no further axioms unless forced by Equation 1).

Task: decide whether Equation 1 implies Equation 2 over ALL magmas.

Equation 1:
{{ equation1 }}

Equation 2:
{{ equation2 }}

MANDATORY OUTPUT FORMAT:
Your first line must be exactly one of:
VERDICT: TRUE
VERDICT: FALSE

After the first line you may write at most two short lines, only if useful:
RULE: <very short reason>
NOTE: <very short note>

Do not output a long proof or long counterexample. Do not invent a custom magma table. Keep reasoning internal and the answer short. Parse reliability matters.

======================================================================
WORKING CHEATSHEET (LONG-FORM 25KB VERSION, FINITE-FIRST, WITH
SYNTACTIC EXCLUSION THEOREMS AND SCHOENFELD-STYLE META-PROCESS)
======================================================================

The goal is NOT open-ended creative reasoning. The goal is to classify the pair, look for exact certificates, and use a very small fallback only at the end.

A valid model of Equation 1 in which Equation 2 fails proves FALSE.
A valid derivation/certificate that Equation 2 follows from Equation 1 proves TRUE.

Use the following order strictly:
1. Read and normalize.
2. Identify exact source families.
3. Apply syntactic exclusion theorems.
4. Check finite witness magmas.
5. Check named high-leverage patterns.
6. Use at most 1-2 safe local rewrites.
7. If still unresolved, use conservative structural judgment.

Never assume associativity, commutativity, identity, cancellation, invertibility, or linearity unless Equation 1 forces them.

Never claim FALSE from an invented or half-checked counterexample, or TRUE from a vague story.

IMPORTANT FINITE-FIRST OPERATING RULE:
Work with a finite-model mindset.
- For refutations, search only within the finite witness magmas listed below, or within the exact syntactic exclusion theorems that come from finite witness constructions tailored to the current pair.
- Do NOT search for infinite models.
- Do NOT conclude TRUE merely because you failed to find a finite counterexample.
- TRUE must still come from an exact source-family solver, a named theorem, or a tiny exact rewrite.

Discipline: FALSE from exact finite witness or exact syntactic exclusion; TRUE from exact family, named pattern, or exact rewrite.

----------------------------------------------------------------------
SECTION 0. META-PROCESS (SCHOENFELD-STYLE, INTERNAL ONLY)
----------------------------------------------------------------------

Internally follow this loop:

READ
- Parse both equations as binary trees.
- Notice whether each side is a bare variable or a genuine product term.
- Notice whether Equation 1 looks like a known family.

ANALYZE
- Compute the key invariants listed below.
- Note exact family candidates and exact exclusion candidates.

PLAN
- Choose ONE main route first:
  A. exact source-family solver
  B. syntactic exclusion theorem
  C. finite witness magma
  D. named pattern
  E. tiny rewrite
- Do not mix five weak routes at once.

IMPLEMENT
- Execute the chosen route literally and minimally.
- If it gives an exact certificate, stop; otherwise switch route.

VERIFY
- Before the final verdict, ask internally:
  1. What exactly am I doing?
  2. Why am I doing it?
  3. How does it help decide TRUE or FALSE?
- If the answer is unclear, the route is probably not exact enough.

BELIEF DISCIPLINE
- Do not assume every problem has a short proof.
- Failure to find a proof is not FALSE; failure to find a finite witness is not TRUE.
- Prefer a short exact certificate over a long narrative.

----------------------------------------------------------------------
SECTION A. NORMALIZATION
----------------------------------------------------------------------

Treat each equation as a binary tree on variables.

Safe symmetries for classification:
- Rename variables by order of first appearance.
- Swap the two sides of an equation.
- You may simultaneously dualize BOTH equations by reversing every product:
  dual(x) = x
  dual(a * b) = dual(b) * dual(a)
  Implication is preserved if both source and target are dualized together.

Important: dualization is for classification only. Do not dualize just one equation.

For each term, silently compute these signatures:

- leftmost variable: the leftmost leaf
- rightmost variable: the rightmost leaf
- leaf word: variables read left-to-right, ignoring parentheses
- variable set: variables appearing anywhere
- variable multiset: variables with multiplicities
- parity vector: variable multiplicities mod 2
- operator count: number of * nodes
- leaf count: number of variable occurrences
- left spine depth:
  left_spine_depth(x) = 0
  left_spine_depth(a * b) = 1 + left_spine_depth(a)
- right spine depth:
  right_spine_depth(x) = 0
  right_spine_depth(a * b) = 1 + right_spine_depth(b)
- whether a side is a bare variable or a genuine product term

For commutative normalization use:
- commutative_normal(x) = x
- commutative_normal(a * b) = sorted_pair(commutative_normal(a), commutative_normal(b))
That means recursively normalize children, then sort the two children lexicographically so child order is forgotten but the tree shape is preserved.

Examples:
- commutative_normal(x * y) = {x,y}
- commutative_normal((x * y) * z) = {{x,y},z}
- commutative_normal(x * (y * z)) = {x,{y,z}}
These last two are NOT equal under commutativity alone because associativity is not assumed.

----------------------------------------------------------------------
SECTION B. IMMEDIATE TRIVIAL DECISIONS
----------------------------------------------------------------------

1. If Equation 2 is a tautology t = t, then VERDICT: TRUE.

2. If Equation 1 and Equation 2 are the same up to variable renaming, side swap, and optional simultaneous global dualization, then VERDICT: TRUE.

3. If Equation 1 is a tautology t = t, then it implies only tautologies.
   So if Equation 1 is tautological and Equation 2 is not tautological, VERDICT: FALSE.

4. If Equation 2 contains a variable that does not appear in Equation 1, this is a strong FALSE signal unless Equation 1 forces singleton behavior or an exact family below makes new variables irrelevant.

----------------------------------------------------------------------
SECTION C. EXACT SOURCE FAMILIES WITH DIRECT SOLVERS
----------------------------------------------------------------------

These are the most important rules. When Equation 1 matches one of these families exactly (up to renaming, side swap, and optional simultaneous dualization), use the family solver and stop.

C1. Singleton family

If one side of Equation 1 is a bare variable v and the other side does NOT contain v at all, then Equation 1 forces the singleton law.

Reason:
If v = T(other variables) for all assignments and v is arbitrary, then all elements are equal.

Examples: x = y, x = y * y, x = y * z, x = (y * z) * w.

If Equation 1 is in this exact singleton family, then every equation holds in every model of Equation 1.
Therefore VERDICT: TRUE.

Important:
Some complicated laws are also equivalent to the singleton law, but do NOT guess them here unless they appear explicitly in the named-pattern section below.

C2. Left absorption / left projection

If Equation 1 is alpha-equivalent to either
- x = x * y
or
- x * y = x

then the operation is exactly left projection: a * b = a.

Under this law every term evaluates to its leftmost variable.
Therefore Equation 2 holds iff the leftmost variable on the two sides of Equation 2 is the same.

So:
- if leftmost(lhs of Eq2) = leftmost(rhs of Eq2), then VERDICT: TRUE
- otherwise VERDICT: FALSE

C3. Right absorption / right projection

If Equation 1 is alpha-equivalent to either
- x = y * x
or
- x * y = y

then the operation is exactly right projection: a * b = b.

Under this law every term evaluates to its rightmost variable.
Therefore Equation 2 holds iff the rightmost variable on the two sides of Equation 2 is the same.

So:
- if rightmost(lhs of Eq2) = rightmost(rhs of Eq2), then VERDICT: TRUE
- otherwise VERDICT: FALSE

C4. Right-ignored-input family

If Equation 1 is alpha-equivalent to either
- x * x = x * y
or
- x * y = x * z

then the output depends only on the left input.
Equivalently, there is a unary map S such that a * b = S(a), and specifically a * b = a * a.

Under this law every term reduces to repeated squaring of its leftmost variable.
A complete signature is:
- leftmost variable
- left spine depth

So Equation 2 holds iff BOTH sides of Equation 2 have:
- the same leftmost variable
- the same left spine depth

If both match, VERDICT: TRUE.
Otherwise VERDICT: FALSE.

Example: x * (y * z) has signature (x,1), while (x * y) * z has signature (x,2).

C5. Left-ignored-input family

If Equation 1 is alpha-equivalent to either
- x * x = y * x
or
- x * y = z * y

then the output depends only on the right input.
Equivalently, there is a unary map S such that a * b = S(b), and specifically a * b = b * b.

Under this law every term reduces to repeated squaring of its rightmost variable.
A complete signature is:
- rightmost variable
- right spine depth

So Equation 2 holds iff BOTH sides of Equation 2 have:
- the same rightmost variable
- the same right spine depth

If both match, VERDICT: TRUE.
Otherwise VERDICT: FALSE.

C6. Constant-operation family

If Equation 1 is alpha-equivalent to either
- x * y = z * w
or
- x * x = y * z

then Equation 1 forces the operation to be constant: all products are equal to one fixed value c.

In a constant magma:
- every genuine product term evaluates to c
- a bare variable still evaluates to that variable

Therefore Equation 2 holds under this family exactly in the following cases:
- both sides of Equation 2 are genuine product terms, or
- Equation 2 is a tautology t = t

So if Eq2 has at least one * on both sides, VERDICT: TRUE.
If Eq2 is tautological, VERDICT: TRUE.
Otherwise VERDICT: FALSE.

C7. Associativity family

If Equation 1 is alpha-equivalent to either
- x * (y * z) = (x * y) * z
or its reverse orientation

then Equation 1 is associativity.

Under associativity alone, the complete invariant is the leaf word.
Two terms are forced equal iff they have the same leaf word.

Therefore Equation 2 holds iff:
word(lhs of Eq2) = word(rhs of Eq2)

If equal, VERDICT: TRUE.
Otherwise VERDICT: FALSE.

C8. Commutativity family

If Equation 1 is alpha-equivalent to
- x * y = y * x

then Equation 1 is commutativity.

Under commutativity alone, the correct complete comparison is the recursive commutative normal form: forget the order of children at every node, but keep the tree structure.

Therefore Equation 2 holds iff:
commutative_normal(lhs of Eq2) = commutative_normal(rhs of Eq2)

If equal, VERDICT: TRUE.
Otherwise VERDICT: FALSE.

C9. Idempotence family

If Equation 1 is alpha-equivalent to
- x * x = x
or
- x = x * x

then Equation 1 is idempotence.

Safe exact use:
Only simplify by local contractions/expansions of the form u * u <-> u.
Do NOT use associativity or commutativity unless separately forced.
Do NOT flatten trees.

Operational rule:
- Repeatedly contract identical adjacent subterms u * u to u anywhere in Equation 2.
- If both sides reduce to exactly the same tree, VERDICT: TRUE.
- If an exact exclusion theorem or finite witness below refutes Equation 2 while satisfying idempotence, VERDICT: FALSE.
- Otherwise leave unresolved and continue.

This is intentionally conservative.

----------------------------------------------------------------------
SECTION D. SYNTACTIC EXCLUSION THEOREMS
----------------------------------------------------------------------

These are exact negative certificates. Use them early.

General template:
If Equation 1 has a syntactic invariant on its two sides, but Equation 2 does not have the same invariant on its two sides, then Equation 1 CANNOT imply Equation 2.
Therefore VERDICT: FALSE.

These are not vague heuristics. They come from exact invariant theorems and can be realized by finite witness magmas tailored to the current pair.

Let V be the set of variables appearing anywhere in Equation 1 or Equation 2.
Let K be the maximum leaf count of any one side appearing in Equation 1 or Equation 2.
Use the following exact exclusion rules.

D1. Leftmost-variable exclusion theorem
If Equation 1 has the same leftmost variable on both sides, but Equation 2 does not, then VERDICT: FALSE.

D2. Rightmost-variable exclusion theorem
If Equation 1 has the same rightmost variable on both sides, but Equation 2 does not, then VERDICT: FALSE.

D3. Leaf-word exclusion theorem
If Equation 1 has exactly the same leaf word on both sides, but Equation 2 does not, then VERDICT: FALSE.

D4. Variable-set exclusion theorem
If Equation 1 has the same variable set on both sides, but Equation 2 does not, then VERDICT: FALSE.

D5. Variable-multiset exclusion theorem
If Equation 1 has the same variable multiset on both sides, but Equation 2 does not, then VERDICT: FALSE.

D6. Mod-2 parity exclusion theorem
If Equation 1 has the same parity vector on both sides, but Equation 2 does not, then VERDICT: FALSE.

D7. Bare-variable-vs-product exclusion
If Equation 1 is compatible with a non-singleton constant magma, and Equation 2 has a bare variable on one side and a genuine product term on the other, then this is a strong FALSE signal; confirm with the finite constant witness in Section E.

Do not overgeneralize D7 by itself. Use the constant finite witness to finalize.

----------------------------------------------------------------------
SECTION E. FINITE WITNESS MAGMAS
----------------------------------------------------------------------

Use only the finite witness magmas below. If Equation 1 holds and Equation 2 fails in any one of them, then VERDICT: FALSE immediately.

E1. Finite left-zero witness
Carrier: V
Operation: a * b = a
Term value = leftmost variable.
Equation holds iff leftmost variables match.

So this witness exactly realizes D1.

E2. Finite right-zero witness
Carrier: V
Operation: a * b = b
Term value = rightmost variable.
Equation holds iff rightmost variables match.

So this witness exactly realizes D2.

E3. Finite bounded-word witness
Carrier: all words over V of length at most K, plus one overflow symbol O.
Operation: concatenate the two words; if the result length exceeds K, output O.
Each variable is interpreted as the corresponding one-letter word.

On the current pair, evaluation never overflows, so the term value is exactly the leaf word. Equation holds iff leaf words match.

So this witness exactly realizes D3, but with a finite carrier.

E4. Finite set-union witness
Carrier: the power set P(V).
Operation: union.
Each variable is interpreted as its singleton set.

Term value = variable set.
Equation holds iff variable sets match.

So this witness exactly realizes D4 and is finite.

E5. Finite bounded-count witness
Carrier: (Z/(K+1)Z)^V.
Operation: vector addition modulo K+1.
Each variable is interpreted as its unit basis vector.

Because counts are at most K on the current pair, equality modulo K+1 is exact here. Equation holds iff variable multisets match.

So this witness exactly realizes D5 and is finite.

E6. Finite parity witness
Carrier: (F2)^V.
Operation: vector addition mod 2.
Each variable is interpreted as its unit basis vector.

Term value = parity vector.
Equation holds iff parity vectors match.

So this witness exactly realizes D6 and is finite.

E7. Two-element constant witness
Carrier: {0,1}
Operation: a * b = 0

Here every genuine product term evaluates to 0, but bare variables stay free if they appear alone.
Use this to confirm false targets against constant-operation-compatible sources.

E8. Two-element min witness
Carrier: {0,1}
Operation: a * b = min(a,b)

This is a small idempotent commutative associative witness.
Use only when the check is obvious and short.

E9. Two-element max witness
Carrier: {0,1}
Operation: a * b = max(a,b)

Also a small idempotent commutative associative witness.
Use only when the check is obvious and short.

----------------------------------------------------------------------
SECTION F. NAMED HIGH-LEVERAGE SOURCE PATTERNS
----------------------------------------------------------------------

If Equation 1 matches one of these exact patterns (up to renaming, side swap, and optional simultaneous dualization), apply the stated consequence.

F1. Putnam pair
The laws
- x = y * (x * y)
and
- x = (y * x) * y
are equivalent.

So if Equation 1 is one of these and Equation 2 is the other, VERDICT: TRUE.

More generally, if Equation 1 is one of these, use 1-2 direct substitutions safely before falling back.

F2. The law x * y = (y * y) * x
This law implies commutativity.

So if Equation 1 matches
- x * y = (y * y) * x
then you may freely use commutativity as a derived law.

Operationally:
- if Equation 2 becomes identical after recursive commutative normalization, VERDICT: TRUE
- otherwise continue; do not assume more than commutativity from this rule alone

F3. The law x = y * ((z * x) * (z * z))
This law is equivalent to the singleton law.

So if Equation 1 matches
- x = y * ((z * x) * (z * z))
then VERDICT: TRUE for every Equation 2.

F4. The law x = (y * z) * (y * (x * z))
This law characterizes abelian groups of exponent two.

So if Equation 1 matches
- x = (y * z) * (y * (x * z))

then every term reduces to parity.
Operational solver:
Equation 2 holds iff the parity vectors of the two sides match.
So compare variable multiplicities modulo 2.

If parity vectors match, VERDICT: TRUE.
Otherwise VERDICT: FALSE.

F5. Central-groupoid pattern
If Equation 1 matches
- x = (y * x) * (x * z)

then it is a strong structured law.
Use safe rewrite only; do not assume associativity or commutativity unless derivable.
If Equation 2 is the weak central-groupoid variant
- x = (y * x) * (x * (z * y))
then VERDICT: TRUE.
Otherwise continue.

----------------------------------------------------------------------
SECTION G. SAFE LOCAL REWRITE FALLBACK
----------------------------------------------------------------------

Use this only if Sections C, D, E, and F did not settle the case.

Allowed rewrite principle:
If Equation 1 is L = R, then for any substitution sigma and any one-hole context C[ ],
you may replace C[L sigma] by C[R sigma], or vice versa.

But keep the fallback extremely small and safe.

Rules for the fallback:
1. Use at most two rewrite steps.
2. Prefer exact subterm replacement, not imaginative proof sketches.
3. Do not introduce new variables in the rewritten term unless they were already present in the matched subterm pattern.
4. Do not build a brand-new derived law and then use it recursively many times.
5. If the source family already has an exact solver, use that solver instead of generic rewriting.
6. If the rewrite route stalls, stop and switch; do not persist.

Good fallback uses:
- commutativity inside one subterm
- associativity to rebracket one local region
- idempotence to contract u * u
- replacing x * y by x under left absorption
- replacing x * y by y under right absorption
- replacing x * y by x * x in the right-ignored-input family
- replacing x * y by y * y in the left-ignored-input family

Example:
Eq1: x * y = y * x
Eq2: (x * y) * z = (y * x) * z

This is TRUE by one contextual rewrite inside the left-hand side of Eq2.

Another example:
Eq1: x * (y * z) = (x * y) * z
Eq2: (a * b) * (c * d) = a * (b * (c * d))

This is TRUE by one associativity rewrite.

Bad fallback behavior:
- inventing a three-page proof
- inventing a custom finite magma
- using more than two non-obvious derived identities
- silently assuming associativity or commutativity without having them

If a clean 1-2 step exact contextual rewrite converts one side of Eq2 into the other, VERDICT: TRUE.

----------------------------------------------------------------------
SECTION H. CONSERVATIVE STRUCTURAL JUDGMENT WHEN STILL UNRESOLVED
----------------------------------------------------------------------

Only reach this section if:
- no exact source-family solver applied
- no exact syntactic exclusion theorem applied
- no finite witness refutation applied
- no named pattern applied
- no safe local rewrite settled the case

Use a conservative classifier, not creative theorem proving.

Strong FALSE signals:
1. Equation 2 introduces a genuinely new variable not present in Equation 1, and Equation 1 is not singleton / constant / a named strong pattern.
2. Equation 2 requires obvious symmetry absent from Equation 1, such as a direct commutative swap, while no rule derived commutativity.
3. Equation 2 fails one of the standard invariants naturally suggested by Equation 1.
4. Equation 2 asks for a new reassociation or new child-order freedom, but Equation 1 is not associativity-like or commutativity-like.
5. Equation 2 contains a bare variable on one side while Equation 1 is compatible with non-singleton constant witnesses.
6. The only support for TRUE is “Equation 1 feels stronger”.

Strong TRUE signals:
1. Equation 1 is visibly more restrictive than Equation 2 and already forces a simple canonical semantics.
2. Equation 2 is an obvious contextual or substitution instance of Equation 1.
3. Equation 2 matches all exact invariants naturally suggested by Equation 1's family and also survives the safe rewrite check.
4. Equation 1 is a named strong pattern with known downstream algebraic structure.
Tie-break rule:
- Prefer FALSE if the only support for TRUE is a vague story.
- Prefer TRUE if there is a clean exact family match or clean local rewrite.
- Never choose FALSE based on an invented counterexample.
- Never choose TRUE based on “it feels stronger”.
- If you used only finite-first search and found nothing, that is NOT itself evidence for TRUE.

In other words:
TRUE requires a certificate.
FALSE requires an exact exclusion theorem, an exact finite witness, OR several converging structural negatives.
----------------------------------------------------------------------
SECTION I. QUICK REFERENCE TABLE
----------------------------------------------------------------------

1. Eq2 tautology -> TRUE.
2. Eq1 alpha-equals Eq2 -> TRUE.
3. Eq1 tautology and Eq2 non-tautology -> FALSE.
4. Eq1 has variable side not occurring on the other side -> singleton -> TRUE.
5. Eq1 = x = x * y or x * y = x -> solve Eq2 by leftmost variable.
6. Eq1 = x = y * x or x * y = y -> solve Eq2 by rightmost variable.
7. Eq1 = x * x = x * y or x * y = x * z -> solve Eq2 by (leftmost variable, left spine depth).
8. Eq1 = x * x = y * x or x * y = z * y -> solve Eq2 by (rightmost variable, right spine depth).
9. Eq1 = x * y = z * w or x * x = y * z -> constant operation:
   Eq2 true iff both sides of Eq2 are genuine product terms, or Eq2 is tautological.
10. Eq1 = associativity -> solve Eq2 by leaf word equality.
11. Eq1 = commutativity -> solve Eq2 by recursive commutative normal form.
12. Eq1 = idempotence -> only local u * u <-> u contractions/expansions.
13. If Eq1 has same leftmost variable on both sides but Eq2 does not -> FALSE.
14. If Eq1 has same rightmost variable on both sides but Eq2 does not -> FALSE.
15. If Eq1 has same leaf word on both sides but Eq2 does not -> FALSE.
16. If Eq1 has same variable set on both sides but Eq2 does not -> FALSE.
17. If Eq1 has same variable multiset on both sides but Eq2 does not -> FALSE.
18. If Eq1 has same parity vector on both sides but Eq2 does not -> FALSE.
19. If Eq1 matches x = y * ((z * x) * (z * z)) -> singleton -> TRUE.
20. If Eq1 matches x = (y * z) * (y * (x * z)) -> solve Eq2 by parity vector equality.
21. If Eq1 holds in any listed finite witness and Eq2 fails there -> FALSE.
22. Never conclude TRUE from failure to find a finite witness.

----------------------------------------------------------------------
SECTION J. FINAL ANTI-CONFABULATION RULES
----------------------------------------------------------------------

- Do not write “counterexample” unless it comes from one of the exact finite witnesses above.
- Do not invent a custom operation table.
- Do not claim FALSE from a model you did not fully specify.
- Do not claim TRUE from a vague feeling of strength.
- Prefer one exact rule over five weak heuristics.
- If you use a fallback rewrite, keep it tiny and literal.
- The first line must remain exactly VERDICT: TRUE or VERDICT: FALSE.

Now solve the given pair.
