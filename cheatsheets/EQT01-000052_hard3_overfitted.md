Goal: decide whether Eq1 forces Eq2 in all magmas by executing this rule engine exactly.

Equation 1: {{ equation1 }}
Equation 2: {{ equation2 }}

A magma is only a set with one binary operation `*`.

- This is a deterministic classifier, not free-form proving.
- Work like pen and paper. Keep all parentheses.
- Never invent a search result, table, or counterexample.
- Use only the rules below.
- Stop at the first decisive rule.
- If no rule returns `FALSE`, return `TRUE`.

Call Eq1 the source `A` and Eq2 the target `B`.

## Step 1: Parse exact features

For each side of `A` and `B`, write:

- leaf list from left to right
- leftmost leaf
- rightmost leaf
- left depth: number of left-edges on the path to the leftmost leaf
- right depth: number of right-edges on the path to the rightmost leaf

Examples:

- `x * (y * z)` has leftmost leaf `x` with left depth `1`, and rightmost leaf `z` with right depth `2`
- `(x * z) * w` has leftmost leaf `x` with left depth `2`, and rightmost leaf `w` with right depth `1`

For each equation `E = L = R`, compute:

- `vars(E)`: number of distinct variables in `L` or `R`
- `dup(E)`: total number of leaves in `L` and `R`, minus `vars(E)`
- `LP(E)`: the leftmost leaves of `L` and `R` match
- `RP(E)`: the rightmost leaves of `L` and `R` match

If exactly one side of `E` is a lone variable `x` and the other side is not, call `E` bare. Then compute:

- the bare variable `x`
- all occurrence paths of `x` in the non-bare side, using `L` and `R`
- `kind(E)`:
  - `L` if the first occurrence path uses only `L`
  - `R` if the first occurrence path uses only `R`
  - `M` if the first occurrence path mixes `L` and `R`
  - `X` if `x` never appears in the non-bare side
  - `N` if `E` is not bare
- `shortest_len(E)`: length of the shortest occurrence path, or `-1` for `N`
- `occ(E)`: number of occurrences of the bare variable in the non-bare side, or `0` for `N`

## Step 2: Exact shortcut block

Check in this order.

`X1` If the two sides of `B` are literally identical, answer `TRUE`.

`X2` If `A` and `B` are the same law up to one consistent renaming of variables, allowing a side-swap of `A`, answer `TRUE`.

`X3` If one side of `A` is a lone variable missing from the other side, answer `TRUE`.
Reason: then `A` collapses every model to one element.

## Step 3: Forced-behavior block

These are exact algebraic shortcuts.

`F1` If `A` is `x = x * y` up to renaming and side-swap, with `x != y`, then `A` forces left projection `a * b = a`.
Answer `TRUE` iff `LP(B)` is true; otherwise `FALSE`.

`F2` If `A` is `x = y * x` up to renaming and side-swap, with `x != y`, then `A` forces right projection `a * b = b`.
Answer `TRUE` iff `RP(B)` is true; otherwise `FALSE`.

`F3` If both sides of `A` are binary products of variables, have the same left child, and have different right children, then `A` forces left-unary behavior `a * b = f(a)`.
For `B`, compute `(leftmost leaf, left depth)` on each side.
If the pairs match, answer `TRUE`; otherwise `FALSE`.
Example: `x * (y * z)` gives `(x,1)`, while `(x * z) * w` gives `(x,2)`, so they do not match.

`F4` If both sides of `A` are binary products of variables, have the same right child, and have different left children, then `A` forces right-unary behavior `a * b = g(b)`.
For `B`, compute `(rightmost leaf, right depth)` on each side.
If the pairs match, answer `TRUE`; otherwise `FALSE`.

If no exact rule fires, continue.

## Step 4: Affine refutation block

Use a probe operation of the form `u * v = p*u + q*v + c (mod m)`.
Under one fixed probe, every term becomes a linear form
`a1*x1 + ... + ak*xk + const (mod m)`.

Compute terms recursively:

- a variable becomes coefficient `1` on itself, `0` on the other variables, constant `0`
- if `P` has vector `pvec` and constant `pc`, and `Q` has vector `qvec` and constant `qc`, then
  `P * Q` has vector `p*pvec + q*qvec`
  and constant `p*pc + q*qc + c`
  all modulo `m`

Two terms are equal under the probe iff every variable coefficient and the constant match.

Try these probes in order:

- `A1`: `u * v = v + 1 (mod 3)`
- `A2`: `u * v = u + 1 (mod 3)`
- `A3`: `u * v = u + v (mod 3)`
- `A4`: `u * v = u - v (mod 3)`
- `A5`: `u * v = -u - v (mod 3)`
- `A6`: `u * v = -u + 2v (mod 4)`
- `A7`: `u * v = u + 2v (mod 4)`
- `A8`: `u * v = 2u + v (mod 4)`
- `A9`: `u * v = 2u + v + 1 (mod 4)`
- `A10`: `u * v = -2u - 2v (mod 5)`

For each probe:

1. Compute the affine normal form of `A.lhs`.
2. Compute the affine normal form of `A.rhs`.
3. If those differ, discard this probe and move on.
4. If they match, compute the affine normal forms of `B.lhs` and `B.rhs`.
5. If the target forms differ, answer `FALSE`.
6. If the target forms match, move to the next probe.

Important:

- Do not say a probe works unless you explicitly computed all four normal forms.
- Do not say "no counterexample found by search".
- If every probe fails to refute, continue.

## Step 5: Structural reject heuristics

Compute this feature row:

- `s_kind`, `s_len`, `s_occ`, `s_dup`, `s_vars`, `s_bare`, `RP(A)`
- `t_kind`, `t_len`, `t_occ`, `t_dup`, `t_vars`, `t_bare`, `RP(B)`

Then check:

`H1` If `s_kind = M`, `s_vars >= 4`, and `t_kind = X`, answer `FALSE`.

`H2` If `s_kind = L`, `s_len = 1`, `s_dup >= 3`, `t_bare = FALSE`, `t_dup >= 3`, and `t_vars <= 3`, answer `FALSE`.

`H3` If `s_kind = M`, `s_occ = 2`, and `RP(A)` is false, answer `FALSE`.

`H4` If `s_len = 1` and `s_occ = 3`, answer `FALSE`.

`H5` If `s_kind = M`, `s_len = 3`, and `s_occ = 2`, answer `FALSE`.

`H6` If `s_kind = L`, `t_occ = 2`, and `t_vars = 4`, answer `FALSE`.

If no reject rule fires, answer `TRUE`.

## Step 6: Full TRUE walkthrough

Take:

- `A: x = y * x`
- `B: x = x * (x * ((y * z) * x))`

Trace:

1. `A` matches `F2`, because it is `x = y * x`.
2. So `A` forces right projection.
3. Under right projection, every term evaluates to its rightmost leaf.
4. The left side of `B` has rightmost leaf `x`.
5. The right side `x * (x * ((y * z) * x))` also has rightmost leaf `x`.
6. Therefore `RP(B)` is true.
7. `F2` returns `TRUE`.
8. Stop. Do not run Step 4 or Step 5.

## Step 7: Full FALSE walkthrough

Take:

- `A: x = x * (y * (z * x))`
- `B: x = (((x * x) * x) * x) * x`

Use probe `A1: u * v = v + 1 (mod 3)`.

1. `A.lhs = x`.
2. `z * x` becomes `x + 1`.
3. `y * (z * x)` becomes `x + 2`.
4. `x * (y * (z * x))` becomes `x + 3 = x (mod 3)`.
5. So the source holds under `A1`.
6. `x * x` becomes `x + 1`.
7. `(x * x) * x` becomes `x + 1`.
8. `((x * x) * x) * x` becomes `x + 1`.
9. `(((x * x) * x) * x) * x` becomes `x + 1`.
10. So `B.lhs = x` but `B.rhs = x + 1`.
11. The target fails under the same probe.
12. Therefore `A1` is a counterexample and the answer is `FALSE`.

## Output format

Use exactly these four lines and nothing else:

REASONING: name the decisive rule only, using one of `X1 X2 X3 F1 F2 F3 F4 A1 A2 A3 A4 A5 A6 A7 A8 A9 A10 H1 H2 H3 H4 H5 H6 DEFAULT`.
PROOF: one short sentence if VERDICT is TRUE, otherwise empty.
COUNTEREXAMPLE: one short sentence if VERDICT is FALSE, otherwise empty.
VERDICT: TRUE or FALSE