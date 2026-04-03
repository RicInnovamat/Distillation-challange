You are solving implication problems in the equational theory of magmas.
A magma is a set with one binary operation * and NO further assumptions:
do NOT assume associativity, commutativity, identity, cancellation, idempotence, order, or any algebraic law unless it is forced by Equation 1.

Task:
Given Equation 1 and Equation 2, decide whether Equation 1 implies Equation 2 over ALL magmas.

Required output:
Your FIRST line must be exactly one of:
VERDICT: TRUE
VERDICT: FALSE

After that, write at most a short structured justification.
Do not output anything before the verdict line.

==================================================
CORE DISCIPLINE
==================================================

You must decide by using only mathematically valid implication logic.

A TRUE answer requires one of the following:
1. Equation 2 is identical to Equation 1 up to renaming / swapping sides / taking the dual form.
2. Equation 1 belongs to a law family that is known to force Equation 2.
3. Equation 2 follows from Equation 1 by a valid substitution/congruence certificate.
4. Equation 1 collapses every magma to the singleton case, so every equation holds.
5. Equation 1 forces the binary operation to be constant, and Equation 2 therefore holds.

A FALSE answer requires one of the following:
1. A valid separating model schema is recognized.
2. Equation 2 requires a structural feature not forced by Equation 1, and there is a known family-level non-implication.
3. Equation 2 introduces a demand that is stronger than Equation 1 in a way that is not certified by any positive rule.
4. A known small-model separator applies.

Never output TRUE because “it seems stronger”.
Never output FALSE because “I cannot derive it”.
Never invent a counterexample table unless it is one of the explicitly permitted standard separators and it truly satisfies Equation 1 while falsifying Equation 2.

If uncertain, prefer the conclusion supported by the strongest explicit certificate.
If no certificate exists, prefer FALSE rather than hallucinated TRUE.

==================================================
NORMALIZATION STAGE
==================================================

Before deciding, normalize both equations conceptually.

An equation is an equality between two magma terms built from variables and the binary operation *.

For each equation E = (L = R), consider the following equivalent presentations:
- original: L = R
- swapped: R = L
- dualized: reverse the order of every product recursively in both sides
- dualized + swapped

Also rename variables canonically by order of first appearance when scanning left side then right side.
Example:
(a * (b * a)) = c  becomes  (x * (y * x)) = z

When comparing equations or checking “same pattern”, treat equations as identical if they match after:
- renaming variables
- swapping the two sides
- taking global dual
- combining these

Do NOT normalize using associativity or commutativity unless Equation 1 itself forces them.

==================================================
HIGH-LEVEL DECISION ORDER
==================================================

Always follow this order.

PHASE A. Exact/trivial implication checks
PHASE B. Collapse and constant-operation checks
PHASE C. Structural family classification
PHASE D. Positive implication certificates
PHASE E. Negative separator checks
PHASE F. Restricted local transformation fallback
PHASE G. Final conservative judgment

Do not skip directly to informal reasoning.

==================================================
PHASE A. EXACT / TRIVIAL CHECKS
==================================================

Return TRUE immediately if any of the following holds:

A1. Equation 2 is identical to Equation 1 after canonical renaming / swap / dual normalization.

A2. Equation 2 is a tautology of the form x = x.

A3. Equation 2 is the same law family as Equation 1 under a notational variant.

Return FALSE immediately if:
A4. Equation 1 is x = x and Equation 2 is not a tautology.

Important:
“same law family” means actually the same equation pattern under the allowed syntactic symmetries, not merely “similar looking”.

==================================================
PHASE B. COLLAPSE AND CONSTANT-OPERATION CHECKS
==================================================

This phase is extremely important.

------------------------------------------
B1. Singleton-collapse laws
------------------------------------------

Equation 1 collapses every magma to a singleton if it forces all elements to be equal.

The strongest collapse signals are:

- A variable equals a term in which that variable does not occur.
  Examples:
  x = y
  x = y * z
  x = (y * z) * w
  x = y * (z * w)

Reason:
If x equals an expression independent of x, then x must take the same value under all assignments, forcing all elements equal.

Also collapse if a nontrivial equation equates two variable patterns in a way known to force x = y for arbitrary values.

When Equation 1 collapses to the singleton magma:
- Every term evaluates to the same element.
- Therefore EVERY Equation 2 holds.
- Return TRUE.

------------------------------------------
B2. Constant-operation laws
------------------------------------------

Equation 1 forces the operation to be constant if all products must have the same value, independent of the inputs.

Typical constant-operation pattern:
- two product terms are equated with disjoint variable support, such as:
  x * y = z * w
or any canonical variant where neither side shares determining variables with the other in a way that makes every product equal.

Interpret carefully:
If Equation 1 forces a*b = c for all a,b and for one fixed c, then all binary products are constant.

If Equation 1 forces constant operation, then many Equation 2 instances hold automatically, but not every equation with free variables outside product positions should be accepted blindly.
Use this rule:

If every term in Equation 2 evaluates to the same constant under a constant operation, return TRUE.
If Equation 2 compares a bare variable with a product term, do NOT automatically return TRUE unless singleton collapse also holds.

Examples:
- Under constant operation, x * y = z * w is TRUE.
- Under constant operation, (x * y) * z = u * (v * w) is TRUE.
- Under constant operation alone, x = y * z is NOT automatically true unless the magma is singleton.

So:
constant operation is strong, but weaker than singleton collapse.

------------------------------------------
B3. Do not overfire collapse/constant
------------------------------------------

Do NOT mark collapse merely because Equation 1 “looks strong”.
Do NOT mark constant merely because Equation 1 contains many variables.
Only use collapse/constant when the semantic pattern is genuinely forced.

==================================================
PHASE C. STRUCTURAL FAMILY CLASSIFICATION
==================================================

Classify Equation 1 and Equation 2 into structural families.

The purpose is not to prove by itself, but to locate the correct decision rules.

------------------------------------------
C1. Basic structural descriptors
------------------------------------------

For each equation, note:

- number of variables occurring
- whether each variable occurs once or repeats
- whether variables occur on both sides or only one side
- whether a side is a bare variable or a compound product
- whether left and right are both compound terms
- nesting depth of each side
- whether the equation is linear (every variable appears at most once on each side)
- whether the equation duplicates a variable
- whether the equation drops a variable
- whether the equation introduces a fresh variable not otherwise constrained
- whether the equation is self-dual or dual to another pattern

------------------------------------------
C2. Main families to recognize
------------------------------------------

Family F1. Singleton-collapse laws
Canonical idea:
a variable equals a term not containing that variable.
Examples:
x = y
x = y * z
x = (y * z) * w

Family F2. Constant-operation laws
Canonical idea:
all products are identified.
Examples:
x * y = z * w

Family F3. Left-constancy laws
Canonical idea:
the right input becomes irrelevant.
Examples:
x * y = x * z

Family F4. Right-constancy laws
Canonical idea:
the left input becomes irrelevant.
Examples:
x * y = z * y

Family F5. Commutativity-type laws
Canonical idea:
x * y = y * x

Family F6. Idempotence-type laws
Canonical idea:
x * x = x
or families strongly tied to square collapse/reduction

Family F7. Projection-like laws
Canonical idea:
x * y = x
or
x * y = y

Family F8. Absorption-like or semiprojection laws
Canonical idea:
nested terms reduce to one side or one variable after substitution

Family F9. Linear balanced laws
Every variable appears in controlled parallel fashion on both sides.

Family F10. Duplication/nesting laws
Some variable repeats on one side or both sides, often creating stronger local constraints.

Family F11. Mixed-variable asymmetry laws
One side is much simpler, the other much more nested.

------------------------------------------
C3. Classification principles
------------------------------------------

Use coarse classification first:
- collapse?
- constant?
- constancy family?
- commutativity family?
- idempotence family?
- projection family?
- duplication/nesting family?

Then refine only if needed for the implication judgment.

Do not waste time trying to place Equation 2 in an overly specific subfamily unless a rule depends on it.

==================================================
PHASE D. POSITIVE IMPLICATION CERTIFICATES
==================================================

A TRUE answer should usually be backed by one of the certificates below.

------------------------------------------
D1. Identity certificate
------------------------------------------

If Equation 2 is the same as Equation 1 under renaming / swap / dual, return TRUE.

------------------------------------------
D2. Collapse certificate
------------------------------------------

If Equation 1 forces singleton collapse, return TRUE.

This is the strongest certificate.

------------------------------------------
D3. Constant-operation certificate
------------------------------------------

If Equation 1 forces a constant binary operation, and both sides of Equation 2 necessarily evaluate to the same constant-product value, return TRUE.

Do not use this certificate when Equation 2 equates a bare variable with a product term, unless collapse also holds.

------------------------------------------
D4. Family implication certificate
------------------------------------------

Return TRUE when a known family-level implication applies.

Safe positive rules include:

Rule P1.
Singleton-collapse implies every equation.

Rule P2.
Projection law x*y = x implies left-constancy x*y = x*z.
Reason:
both sides reduce to x.

Rule P3.
Projection law x*y = y implies right-constancy x*y = z*y.
Reason:
both sides reduce to y.

Rule P4.
Projection law x*y = x implies idempotence x*x = x.

Rule P5.
Projection law x*y = y implies idempotence x*x = x.

Rule P6.
If Equation 1 explicitly states commutativity, then any exact contextual instance of commutativity is implied.
Example:
from x*y = y*x infer (x*y)*z = (y*x)*z
and
z*(x*y) = z*(y*x)

Rule P7.
If Equation 1 explicitly states an identity L = R, then any substitution instance Lσ = Rσ is implied.

Rule P8.
If Equation 1 explicitly states L = R, then any one-context congruence instance C[Lσ] = C[Rσ] is implied, where C[-] is a term context with one hole.
This is valid because equality is preserved under substitution into terms.

Rule P9.
If Equation 1 is exactly a law that makes one argument irrelevant, then any Equation 2 expressing the same irrelevance at greater contextual depth is implied when it is a direct congruence instance.

Rule P10.
If Equation 1 is a direct projection law, then many nested equations collapsing to the same projection value are implied, provided both sides reduce uniformly by repeated substitution.

------------------------------------------
D5. Direct substitution certificate
------------------------------------------

This is one of the most important constructive rules.

Suppose Equation 1 is:
L = R

If Equation 2 can be written exactly as:
Lσ = Rσ
for some substitution σ sending variables to terms,
then Equation 1 implies Equation 2.

Examples:
From x*y = y*x
infer:
(x*y)*z = (y*x)*z
by context C[-] = [-]*z

From x*y = x
infer:
(x*y)*z = x*z
by replacing x with x and y with y, then using context [-]*z

Use this certificate whenever possible because it is short and reliable.

------------------------------------------
D6. One-context congruence certificate
------------------------------------------

If Equation 2 is obtained by inserting a substitution instance of Equation 1 into the same surrounding context on both sides, return TRUE.

Safe examples:
- C[Lσ] = C[Rσ]
- D[C[Lσ]] = D[C[Rσ]]

Do not chain many contexts informally.
Prefer one explicit context or at most two transparent steps.

------------------------------------------
D7. Two-step certificate
------------------------------------------

A two-step derivation is allowed only if both steps are explicit substitution/congruence applications of Equation 1.

Good pattern:
1. transform left side of Equation 2 using Equation 1
2. obtain right side exactly

or:
1. both sides of Equation 2 reduce to the same intermediate term using Equation 1

If the derivation is longer than two simple steps, do not trust it unless it is completely transparent.

------------------------------------------
D8. Projection reduction certificate
------------------------------------------

If Equation 1 is x*y = x, then every term built only by products reduces recursively to its leftmost leaf.
If Equation 1 is x*y = y, then every term built only by products reduces recursively to its rightmost leaf.

Therefore:
under x*y = x, Equation 2 holds iff both sides of Equation 2 have the same leftmost variable.
under x*y = y, Equation 2 holds iff both sides of Equation 2 have the same rightmost variable.

This is a strong and safe evaluation rule.

------------------------------------------
D9. Left/right-constancy evaluation certificate
------------------------------------------

If Equation 1 is x*y = x*z, then for fixed left input, the right input does not matter.
So in any term, subterms sharing the same left branch can collapse across right replacements.

Dually, if Equation 1 is x*y = z*y, then for fixed right input, the left input does not matter.

Use these to validate Equation 2 only when the same irrelevance pattern is genuinely present.
Do not overgeneralize them to projection unless projection is actually forced.

------------------------------------------
D10. Idempotence certificate
------------------------------------------

If Equation 1 is or directly forces x*x = x, then any Equation 2 that is simply a valid elimination of duplicate self-products may hold.
But be careful:
idempotence alone does NOT imply commutativity, constancy, projection, or collapse.

Use idempotence only for equations whose only difference is removal/insertion of exact self-products in positions licensed by Equation 1.

==================================================
PHASE E. NEGATIVE SEPARATOR CHECKS
==================================================

A FALSE answer should ideally be supported by a separator family.

You may use ONLY the standard separator schemas below unless another separator is immediately obvious and unquestionably correct.

For each separator, the logic is:
if Equation 1 holds in that magma family but Equation 2 fails there, then the implication is FALSE.

------------------------------------------
E1. Left-zero magma
------------------------------------------

Operation:
a*b = a

This validates:
- x*y = x
- x*y = x*z
- many left-projection consequences

This often falsifies:
- x*y = y
- x*y = z*y
- commutativity
- symmetric laws not forced by left projection

Use left-zero to refute any claim that a left-projection-like premise implies a genuinely right-sensitive or symmetric conclusion.

------------------------------------------
E2. Right-zero magma
------------------------------------------

Operation:
a*b = b

This validates:
- x*y = y
- x*y = z*y
- many right-projection consequences

This often falsifies:
- x*y = x
- x*y = x*z
- commutativity
- symmetric laws not forced by right projection

------------------------------------------
E3. Constant magma
------------------------------------------

Operation:
a*b = c for fixed c

This validates:
- x*y = z*w
- any equation between nontrivial product terms
- many constant-operation consequences

But it does NOT generally validate:
- x = y*z
unless the magma is singleton.

Use constant magmas to separate product-level equalities from variable-level collapse.

------------------------------------------
E4. XOR / non-idempotent commutative separator
------------------------------------------

On {0,1}, let a*b = a xor b.

This validates:
- commutativity
It falsifies:
- idempotence x*x = x
- projection x*y = x
- projection x*y = y
- many absorption-like laws

Use this when someone tries to infer projection or idempotence from commutativity alone.

------------------------------------------
E5. Min / Max semilattice-style separators
------------------------------------------

On {0,1}, min and max are associative, commutative, idempotent.
They validate:
- commutativity
- idempotence
They may falsify:
- projection
- constancy
- collapse
- many asymmetric laws

Use min/max to refute claims from commutativity + idempotence to projection/constancy/collapse.

------------------------------------------
E6. Generic noncommutative projection separators
------------------------------------------

Left-zero and right-zero together are extremely useful.
If Equation 1 is satisfied by both, but Equation 2 distinguishes left from right or requires symmetry, then Equation 2 is not implied.

------------------------------------------
E7. Variable-introduction warning
------------------------------------------

If Equation 2 contains a variable absent from Equation 1, and Equation 1 is neither singleton-collapse nor otherwise strong enough to make that variable irrelevant, this is strong evidence for FALSE.

Reason:
Equation 2 is asking for a uniform law about a degree of freedom not controlled by Equation 1.

This is not an absolute theorem in every formulation, so use it as a negative guide supported by separator intuition.

------------------------------------------
E8. Structural strengthening warning
------------------------------------------

If Equation 2 demands:
- commutativity
- full symmetry
- projection
- collapse
- a new irrelevance property
and Equation 1 belongs only to a weaker family like idempotence or partial constancy, this is strong evidence for FALSE.

------------------------------------------
E9. Safe family-level non-implications
------------------------------------------

The following non-implications are safe in general unless Equation 1 has extra structure explicitly forcing more:

- commutativity does not imply idempotence
- commutativity does not imply projection
- commutativity does not imply collapse
- idempotence does not imply commutativity
- idempotence does not imply projection
- left-constancy does not imply right-constancy
- right-constancy does not imply left-constancy
- constant-operation does not imply singleton collapse
- projection-left does not imply projection-right
- projection-right does not imply projection-left

Use these as robust FALSE defaults when the family mismatch is clear.

==================================================
PHASE F. RESTRICTED LOCAL TRANSFORMATION FALLBACK
==================================================

This phase exists only for edge cases.
It must remain tightly bounded.

You may perform at most one or two local rewrites using Equation 1, and only under these restrictions:

F1. Equation 1 must be used as an equality schema L = R.

F2. A rewrite is allowed only on a subterm matching Lσ or Rσ for some substitution σ.

F3. Use only a SAFE direction:
the rewritten-to term must not introduce variables that were absent from the matched subterm.
Equivalently, the target side of the rewrite may use only variables already present in the matched side.

This prevents uncontrolled expansion and hallucination.

F4. After one local rewrite, the transformed side of Equation 2 must match the other side exactly, or both sides must reduce to the same obvious term within one more safe step.

Example of valid use:
Equation 1: x*y = y*x
Equation 2: ((x*y)*z) = ((y*x)*z)

Use Equation 1 inside the left subterm x*y.
Then the left side of Equation 2 becomes ((y*x)*z), matching the right side exactly.
Return TRUE.

Example of invalid use:
If the chosen rewrite direction introduces a new variable not present in the matched term, do not use it.

This fallback is secondary.
Do not use it when a family rule or separator already decides the case.

==================================================
PHASE G. FINAL CONSERVATIVE JUDGMENT
==================================================

If all earlier phases fail, use this conservative logic.

Return TRUE only if there is a clear structural reason that Equation 2 is a substitution instance, contextual instance, or immediate family consequence of Equation 1.

Otherwise return FALSE.

Important:
In these problems, unsupported TRUE answers are usually more dangerous than supported FALSE answers.
Do not produce a creative derivation unless it is explicit and short.

==================================================
DETAILED FAMILY GUIDE
==================================================

This section is a longer reference for classification and quick judgments.

------------------------------------------
G1. Singleton-collapse family
------------------------------------------

Prototype:
x = t
where x does not occur in t

Interpretation:
x is forced to be a fixed value independent of x.
Hence all elements are equal.
All equations follow.

Quick rule:
If Equation 1 is in this family, answer TRUE immediately.

------------------------------------------
G2. Constant-operation family
------------------------------------------

Prototype:
product term = product term
with enough variable separation to force all products equal.

Interpretation:
the output of * is independent of inputs.
Every product term becomes the same constant value.

Quick rule:
This implies any equation whose two sides are both guaranteed product terms.
This does not by itself imply equations equating a free variable with a product term.

------------------------------------------
G3. Left projection family
------------------------------------------

Prototype:
x*y = x

Interpretation:
the right argument is discarded at each multiplication.

Recursive evaluation fact:
Every non-variable term evaluates to its leftmost variable.

Consequences:
- x*x = x
- x*y = x*z
- (x*y)*z = x
- x*(y*z) = x
- any two terms with the same leftmost variable are equal

Non-consequences:
- x*y = y
- commutativity
- right-constancy
- collapse

Preferred separator against overclaims:
left-zero magma.

------------------------------------------
G4. Right projection family
------------------------------------------

Prototype:
x*y = y

Interpretation:
the left argument is discarded at each multiplication.

Recursive evaluation fact:
Every non-variable term evaluates to its rightmost variable.

Consequences:
- x*x = x
- x*y = z*y
- (x*y)*z = z
- x*(y*z) = z
- any two terms with the same rightmost variable are equal

Non-consequences:
- x*y = x
- commutativity
- left-constancy
- collapse

Preferred separator:
right-zero magma.

------------------------------------------
G5. Left-constancy family
------------------------------------------

Prototype:
x*y = x*z

Interpretation:
for fixed left input, the right input is irrelevant.

This is weaker than left projection.
It does not force the value to be exactly x.
It only says dependence on the right slot disappears.

Consequences:
- x*y = x*(anything)
- terms differing only in the right descendant below the same left branch may be equal
- direct contextual instances are valid

Non-consequences:
- x*y = x
- commutativity
- right-constancy
- collapse

Preferred separator:
a magma whose product depends on left input but is not literally x.

------------------------------------------
G6. Right-constancy family
------------------------------------------

Prototype:
x*y = z*y

Dual of left-constancy.

Consequences:
- for fixed right input, left input is irrelevant

Non-consequences:
- x*y = y
- commutativity
- left-constancy
- collapse

------------------------------------------
G7. Commutativity family
------------------------------------------

Prototype:
x*y = y*x

Interpretation:
binary arguments can be swapped locally.

Consequences:
- any substitution instance of x*y = y*x
- any one-context insertion of such an instance
- local reordering within one product node

Non-consequences:
- associativity
- idempotence
- projection
- collapse
- constancy

Preferred separators:
XOR, min, max.

------------------------------------------
G8. Idempotence family
------------------------------------------

Prototype:
x*x = x

Interpretation:
duplicate self-products contract.

Consequences:
- exact self-duplication elimination
- substitution instances like t*t = t

Non-consequences:
- commutativity
- associativity
- projection
- collapse
- constancy

Preferred separators:
min/max validate idempotence and commutativity but not projection.

------------------------------------------
G9. Balanced linear family
------------------------------------------

Typical property:
variables appear in parallel controlled positions, usually once each on each side.

These are often not strong enough by themselves to imply asymmetric or collapsing laws.
Be conservative.

------------------------------------------
G10. Duplication family
------------------------------------------

Typical property:
one variable appears twice on one side or both sides.

This may be stronger than a linear law, but duplication alone does not determine the resulting algebraic behavior.
Look for specific consequences only.

==================================================
PREFERRED JUSTIFICATION TEMPLATES
==================================================

For TRUE, use one of these short forms:

Template T1:
VERDICT: TRUE
Equation 1 collapses all magmas to the singleton case, so every equation holds.

Template T2:
VERDICT: TRUE
Equation 2 is the same as Equation 1 up to renaming / swapping / duality.

Template T3:
VERDICT: TRUE
Equation 2 is a direct substitution/context instance of Equation 1.

Template T4:
VERDICT: TRUE
Equation 1 is a projection/constancy law and Equation 2 is an immediate consequence of that family.

Template T5:
VERDICT: TRUE
Equation 1 forces constant operation, and both sides of Equation 2 evaluate to the same constant product value.

For FALSE, use one of these short forms:

Template F1:
VERDICT: FALSE
Equation 1 holds in the left-zero magma, but Equation 2 fails there.

Template F2:
VERDICT: FALSE
Equation 1 holds in the right-zero magma, but Equation 2 fails there.

Template F3:
VERDICT: FALSE
Equation 1 is compatible with a constant-operation magma, but Equation 2 requires more than constant operation.

Template F4:
VERDICT: FALSE
Equation 2 requires commutativity/projection/collapse, which Equation 1 does not force.

Template F5:
VERDICT: FALSE
Equation 2 introduces a stronger structural demand not certified by Equation 1.

==================================================
ANTI-CONFABULATION RULES
==================================================

These rules are critical.

1. Never say “counterexample found” unless it is one of the standard separator families and the fit is obvious.

2. Never say “Equation 1 seems stronger, so TRUE”.
Strength is not enough; you need a certificate.

3. Never use associativity to reassociate terms.
Magma terms are fully parenthesized and structure matters.

4. Never use commutativity globally unless Equation 1 explicitly gives it.

5. Never infer singleton collapse from constant operation alone.

6. Never infer projection from constancy alone.

7. Never infer left-constancy from commutativity, or right-constancy from idempotence, unless explicitly forced.

8. When a variable appears in Equation 2 but not in Equation 1, treat that as a serious warning sign for FALSE unless Equation 1 collapses everything or clearly makes that variable irrelevant.

9. If a proof attempt is longer than two transparent schema applications, do not trust it unless a family rule already guarantees it.

10. If no positive certificate and no strong separator are available, default to FALSE.

==================================================
FINAL WORKING CHECKLIST
==================================================

Before writing the verdict, silently check:

- Did I normalize by renaming / swap / dual?
- Is Equation 1 a collapse law?
- Is Equation 1 a constant-operation law?
- What family is Equation 1 in?
- Is Equation 2 an exact/substitution/context instance?
- Does a standard separator refute the implication?
- Am I accidentally assuming associativity or commutativity?
- Am I confusing constant operation with singleton collapse?
- Do I have an explicit certificate for TRUE or FALSE?

Then output the verdict first.

==================================================
PROBLEM
==================================================

Equation 1:
{{ equation1 }}

Equation 2:
{{ equation2 }}


