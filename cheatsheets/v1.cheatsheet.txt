You are solving equational implication problems over magmas (a set with one binary operation *, no other axioms).
Task: Does {{ equation1 }} imply {{ equation2 }} over ALL magmas?

OUTPUT FORMAT (mandatory): Your FIRST line of output must be exactly:
VERDICT: TRUE
or
VERDICT: FALSE
Then optionally a brief justification. No other format is accepted.

---
CHEATSHEET: DECISION PROCEDURE FOR MAGMA IMPLICATIONS

Follow these steps IN ORDER. Stop at the first step that gives a definitive answer.

STEP 1: TRIVIAL CHECKS
- If eq1 and eq2 are identical (up to variable renaming): → TRUE
- If eq2 is "x = x" (tautology): → TRUE (anything implies x = x)
- If eq1 is "x = x": → FALSE (tautology implies nothing except itself)
- If eq2 has a variable NOT appearing in eq1 AND eq1 does not force a constant/singleton magma: likely FALSE

STEP 2: COLLAPSING EQUATIONS
An equation "collapses" the magma if it forces all elements to be equal (making the magma a singleton {c} where c*c=c).

Eq1 collapses the magma (forces x=y for all x,y) if:
- Eq1 directly is "x = y" or equivalent
- Eq1 has form "x = (term involving only other variables)" where x doesn't appear in the RHS — forces x to equal a fixed value for any inputs, so all elements are the same
- Examples: "x = y * z", "x = (y * z) * w", "x = y * (z * w)" → all collapse because x is set to a fixed expression of other variables regardless of x's value
- If eq1 COLLAPSES the magma → check if eq2 holds in the singleton magma {c} where c*c=c. In a singleton, every equation of the form LHS=RHS holds because both sides equal c. → TRUE

Eq1 forces a CONSTANT operation (a*b = c for all a,b) if:
- Eq1 has form "x * y = z * w" or similar with no shared variables between sides → forces all products to be the same constant
- If eq1 forces constant operation → eq2 holds iff eq2 is satisfied when a*b=c for all a,b → usually TRUE

STEP 3: VARIABLE AND STRUCTURAL ANALYSIS
Count variables on each side of eq1 and eq2. Analyze the structure.

Key patterns that suggest TRUE:
- Eq1 is "stronger" (more constraining): has fewer free variables, or forces more relationships
- Eq1's LHS or RHS contains a subterm matching eq2's structure
- Eq1 forces idempotency (x*x=x) or some absorption law, and eq2 follows from it
- Eq1 forces all elements equal → any eq2 holds (TRUE)

Key patterns that suggest FALSE:
- Eq2 requires a property (e.g., commutativity x*y=y*x) that eq1 doesn't force
- Eq2 has strictly MORE variables than eq1 (new variables not derivable)
- Eq1 is satisfiable by a non-trivial magma where eq2 fails

STEP 4: SMALL MAGMA COUNTEREXAMPLE CHECK
Try to find a counterexample: a magma where eq1 holds but eq2 fails.
Test these standard magmas on {0,1}:

Left-zero:  a*b = a     (table: 0*0=0, 0*1=0, 1*0=1, 1*1=1)
Right-zero: a*b = b     (table: 0*0=0, 0*1=1, 1*0=0, 1*1=1)
Constant-0: a*b = 0     (table: 0*0=0, 0*1=0, 1*0=0, 1*1=0)
Constant-1: a*b = 1     (table: 0*0=1, 0*1=1, 1*0=1, 1*1=1)
Left-proj:  a*b = a*a   (on {0,1}: 0*0=0, 0*1=0, 1*0=1, 1*1=1 = left-zero)
Min:        a*b = min(a,b) (0*0=0, 0*1=0, 1*0=0, 1*1=1)
Max:        a*b = max(a,b) (0*0=0, 0*1=1, 1*0=1, 1*1=1)
XOR:        a*b = (a+b)%2  (0*0=0, 0*1=1, 1*0=1, 1*1=0)

Also try these on {0,1}: 0*0=0,0*1=0,1*0=0,1*1=0 and 0*0=1,0*1=0,1*0=0,1*1=1

For each magma: substitute ALL variable assignments and check if eq1 holds for ALL assignments. If eq1 holds, check eq2 for ALL assignments. If eq2 FAILS for any assignment → COUNTEREXAMPLE FOUND.

CRITICAL RULE: If you find a valid counterexample (a magma satisfying eq1 but not eq2), the answer is IMMEDIATELY FALSE. Do NOT second-guess or override a confirmed counterexample. A counterexample is mathematical proof.

STEP 5: PROOF ATTEMPT (only if no counterexample found)
Try to derive eq2 from eq1 by substitution:
- In eq1, replace variables with terms built from eq1's own expressions
- Apply eq1 repeatedly to simplify
- If you can transform eq1's LHS=RHS into eq2's LHS=RHS → TRUE

Common proof techniques:
a) Direct substitution: plug specific terms into eq1's variables
b) Chain of equalities: LHS =eq1= (middle) =eq1= RHS
c) Idempotent reduction: if eq1 forces x*x=x, simplify all self-products
d) Constant collapse: if eq1 forces a constant operation, verify eq2 holds for constants

STEP 6: DEFAULT JUDGMENT
If steps 1-5 are inconclusive:
- If eq1 has MORE variables or MORE operators than eq2: lean TRUE (stronger premise)
- If eq2 has MORE variables or MORE operators than eq1: lean FALSE (harder to derive)
- If eq1 forces relationships between many variables: lean TRUE
- Otherwise: lean FALSE
