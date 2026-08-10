# C013 — quotient blow-up monotonicity and the linear-syndrome ceiling

**Status:** PROOF_DRAFT_ROUTE_REFUTATION / EXECUTABLE_TINY_CHECK / NO_NOVELTY_CLAIM

C013 attacks O9d5 after C012. C012 showed that fixed-local parity aggregation has only logarithmic full cover complexity. O9d5 therefore proposed growing code/syndrome constraints as the next correlated family.

The first discriminator is again negative. Replacing each vertex of a smaller bipartite graph by a nonempty class of indistinguishable clones cannot increase full cover complexity. Consequently, linear-code syndrome equality and inequality graphs inherit the cover complexity of their quotient on syndrome classes. Dense parity-check matrices do not help, because graph cover complexity sees the quotient partition rather than the cost of computing the syndrome in the original vertex encoding.

This is a graph-cover route theorem. It is not a Boolean circuit lower bound and is not a P-versus-NP solution. No novelty claim is made.

## Primary-source model

Use Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 / ACM Transactions on Computation Theory 17(2), Article 13 (2025), DOI `10.1145/3718746`.

The proof uses only their Definitions 18–21 of semi-filters, preservation, and cover complexity. The syndrome corollaries additionally use Proposition 40, which proves

`rho(G_NEQ, G_{K,K}) = log_2 K`

when `K` is a power of two, and Theorem 22 / Proposition 38 for a simple equality upper bound.

## Definition C013-D1 — square vertex blow-up of a quotient graph

Let

`Q subseteq [K] x [K]`

be a non-trivial square bipartite graph. Let

`lambda_L : [N] -> [K]`

and

`lambda_R : [N] -> [K]`

be surjective maps. Define the square blow-up graph

`G = BlowUp(Q; lambda_L, lambda_R)`

on `[N] x [N]` by

`(u,v) in G  iff  (lambda_L(u), lambda_R(v)) in Q`.

Thus every base vertex is replaced by a nonempty class, and adjacency depends only on the two quotient labels. The class sizes need not be uniform and the left/right partitions need not coincide.

Let `U_0 = Q^c` and `U = G^c`. For every set `S subseteq U_0`, define its lift

`Lift(S) = { (u,v) in U : (lambda_L(u),lambda_R(v)) in S }`.

Lifting commutes with inclusion and intersections:

`Lift(S intersect T) = Lift(S) intersect Lift(T)`.

## Theorem C013 — full cover complexity is non-increasing under square vertex blow-up

With the notation above,

`rho(G, G_{N,N}) <= rho(Q, G_{K,K})`.

### Proof

Let

`Lambda_0 = {(E_1,H_1),...,(E_k,H_k)}`

be a minimum pair family witnessing

`k = rho(Q, G_{K,K})`.

Lift each pair to the blow-up complement:

`Lambda = {(Lift(E_i), Lift(H_i)) : i in [k]}`.

Assume for contradiction that `Lambda` does not cover the blow-up. Then there is a semi-filter `F` over `U=G^c` that is above some graph edge `(u,v) in G` and preserves every lifted pair.

Put

`a = lambda_L(u)`, `b = lambda_R(v)`.

Then `(a,b) in Q`. Define a family over the quotient complement by

`F_0 = { S subseteq U_0 : Lift(S) in F }`.

We verify that `F_0` is a semi-filter above `(a,b)` and preserves `Lambda_0`.

### Nonempty and non-trivial

Because `F` is nonempty, choose some `W in F`. Upward closure gives `U in F`. Since `Lift(U_0)=U`, we have `U_0 in F_0`, so `F_0` is nonempty.

Also `Lift(emptyset)=emptyset`, and a semi-filter never contains the empty set. Hence `emptyset` is not in `F_0`.

### Upward closure

If `S in F_0` and `S subseteq T subseteq U_0`, then

`Lift(S) subseteq Lift(T)`.

Upward closure of `F` gives `Lift(T) in F`, so `T in F_0`.

### Above the quotient edge

Let `A_a` be the quotient complement row fibre at `a`. The actual blow-up complement row fibre at `u` is a subset of `Lift(A_a)`. Since `F` is above `(u,v)`, that row fibre belongs to `F`; upward closure therefore gives `Lift(A_a) in F`, hence `A_a in F_0`.

The same argument with the complement column fibre at `v` gives the quotient column fibre at `b` in `F_0`. Thus `F_0` is above `(a,b)` with respect to the quotient row/column generators.

### Preservation

If `E_i,H_i in F_0`, then `Lift(E_i),Lift(H_i) in F`. Since `F` preserves the lifted pair,

`Lift(E_i) intersect Lift(H_i) = Lift(E_i intersect H_i) in F`.

Therefore `E_i intersect H_i in F_0`. Hence `F_0` preserves every pair in `Lambda_0`.

We have produced a quotient semi-filter above a quotient graph edge that preserves a pair family which, by definition of `rho(Q,G_{K,K})`, covers every such semi-filter. This is a contradiction.

Therefore the lifted `k` pairs cover the blow-up, proving

`rho(G,G_{N,N}) <= k`.

## Corollary C013-C1 — cloning cannot amplify a hard gadget

Any square construction obtained only by replacing vertices of a fixed quotient graph by larger nonempty twin classes has cover complexity at most the cover complexity of the quotient. In particular, no amount of cloning can turn a constant-size quotient into a growing full-cover lower bound.

This is a stronger screening rule than looking only for disjoint pair multiplexing. It applies to arbitrary full semi-filters and arbitrary base cover pairs.

## Corollary C013-C2 — linear-syndrome inequality graphs

Let

`H in F_2^{r x t}`

have rank `k >= 1`. On left and right vertex sets `F_2^t`, define

`G_H^neq = { (x,y) : Hx != Hy }`.

The syndrome map has image size `K=2^k`, and every image element has a nonempty fibre. Therefore `G_H^neq` is a square vertex blow-up of `G_NEQ` on the `K` syndrome classes.

By C013 and Proposition 40 of the primary source,

`rho(G_H^neq, G_{2^t,2^t}) <= rho(G_NEQ,G_{K,K}) = k <= t = log_2 N`.

The bound depends only on the rank of `H`, not on its row weights, density, or a particular bit-level circuit for computing the syndrome.

## Corollary C013-C3 — linear-syndrome equality graphs

Define

`G_H^eq = { (x,y) : Hx = Hy }`.

This is a square vertex blow-up of the equality graph on `K=2^k` quotient labels.

For `k`-bit labels, each bit equality can be written as

`XNOR(p,q) = (p union NOT q) intersection (NOT p union q)`,

using one intersection from input literals. Intersecting the `k` equality bits uses `k-1` further intersections. Thus the associated equality predicate has

`D_intersection(EQ_k) <= 2k-1`.

Theorem 22 / Proposition 38 gives the quotient equality graph

`rho(G_EQ,G_{K,K}) <= 2k-1`.

Applying C013,

`rho(G_H^eq, G_{2^t,2^t}) <= 2k-1 <= 2t-1 = O(log N)`.

Thus both natural linear-syndrome relations proposed by O9d5 are logarithmically bounded even for dense, high-distance, or otherwise sophisticated linear codes.

## Counterexample-first finite calibration

The executable helper `05_falsification/blowup_cover.py` lifts complement sets and pair families under a quotient map. The regression suite uses the exact full-cover oracle on the one-bit `G_NEQ` and `G_EQ` quotient graphs and the non-uniform label map

`[0,0,1]`.

The resulting `3 x 3` blow-ups remain exactly one-pair coverable, and the lifted one-pair witnesses are checked against every relevant semi-filter. This is finite regression evidence only; theorem authority is the argument above.

A separate exhaustive scratch check during discovery tested every non-trivial `2 x 2` base graph whose `[0,0,1]` blow-up stayed within the exact oracle's five-complement-edge guard. No violation of `rho(blow-up) <= rho(base)` was found. This scratch enumeration is supporting falsification, not a promotion certificate.

## Five-role same-context research-cell review

### Complexity theory

**Vote: ACCEPT AS ROUTE REFUTATION.** The pushdown of a preserving semi-filter is the correct contrapositive object. The result eliminates cloning/quotient amplification at the full-cover level, not merely for canonical filters or disjoint pair families.

### Meta-complexity

**Vote: ACCEPT WITH NO ROOT CLAIM.** Linear syndrome equality/inequality does not provide a new unrestricted-circuit lower bound route because the graph collapses to the quotient on syndrome classes. This has no direct implication for the open MCSP O6c/O6d lanes.

### Adversarial proof review

**Vote: ACCEPT PROOF DRAFT.** The load-bearing points are surjectivity of the label maps, non-triviality of the quotient, `Lift(emptyset)=emptyset`, the fact that an actual blow-up row/column fibre is contained in the lifted quotient fibre, and preservation commuting with lifted intersections. These are explicit. The theorem must not be extended to graphs whose adjacency varies inside a quotient block.

### Formal methods

**Vote: REVISE BEFORE VERIFIED_LEMMA.** Tiny exhaustive regression supports the statement but there is no theorem-prover artifact or isolated kernel recheck. The result remains a route-level proof draft.

### Novelty and research value

**Vote: ACCEPT AS NO-NOVELTY-CLAIM.** Blow-up monotonicity is elementary and may be folklore in graph/discrete complexity. Its research value here is high because it decisively removes a broad code/syndrome amplification family and sharpens the next residual. No new-mathematics claim is supported.

This five-role review was produced in one context and is **not independent review**.

## Typed residual C013-R1

A viable O9d successor cannot obtain hardness merely by compressing vertices to a low-cover quotient and then cloning its fibres.

The next globally correlated family must have load-bearing variation **inside** any natural quotient blocks, or a quotient relation whose own full cover complexity is already super-logarithmic. In particular:

- linear syndrome equality/inequality is retired regardless of parity-check density;
- code distance or dense checks alone are not a cover-complexity amplifier when adjacency depends only on the syndrome labels;
- before studying a code-based graph, quotient by identical row and column neighbourhood types and upper-bound the full cover complexity of the quotient;
- the next candidate should use nonlinear/global constraints that do not collapse to a low-cover label relation.

A concrete next discriminator is to search explicit nonlinear code/correlation graphs with many distinct neighbourhood types, then apply quotient compression, source-level `D_intersection`, cyclic constructions, and exact small-instance cover search before attempting an asymptotic lower bound.

## Promotion blockers

- no theorem-prover artifact;
- no isolated independent review;
- no bounded novelty search because no novelty claim is requested;
- theorem is a cover-complexity upper-bound obstruction only;
- root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
