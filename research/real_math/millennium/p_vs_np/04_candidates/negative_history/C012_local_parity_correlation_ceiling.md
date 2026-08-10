# C012 — local-parity correlation ceiling for full graph cover complexity

**Status:** SOURCE_DERIVED_ROUTE_REFUTATION / EXECUTABLE_RECURRENCE / NO_NOVELTY_CLAIM

C012 attacks O9d4 after C011. C011 ruled out coordinate-factorized complement products, so the next discriminator was a genuinely correlated complement relation whose membership cannot be witnessed by one coordinate. The first such family tested here is parity aggregation of a fixed local relation.

The result is negative. Global parity correlation by itself does not create super-logarithmic cover complexity when the local predicate and its complement have constant intersection complexity.

This is not a Boolean circuit lower bound and is not a P-versus-NP solution.

## Primary-source authority

Use Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 / ACM Transactions on Computation Theory 17(2), Article 13 (2025), DOI `10.1145/3718746`.

The load-bearing source facts are:

- Definition 21 defines cover complexity `rho(A,B)` using semi-filters and preserved pairs;
- Theorem 22 gives `rho(A,B) <= D_intersection(A | B)`;
- Proposition 38 specializes the transference to graph complexity: for `N=2^m` and a non-trivial bipartite graph `G subseteq [N] x [N]`,

  `rho(G, G_{N,N}) <= D_intersection(f_G^{-1}(1) | B_{2m})`,

  where `f_G` is the `2m`-bit Boolean predicate encoding graph membership.

The source already uses this style of explicit intersection-complexity upper bound in its `G_NEQ` calibration. C012 is a direct route-screening corollary of the same framework and is not presented as new mathematics.

## Definition C012-D1 — parity-correlated graph family

Fix an alphabet

`A = {0,1}^d`

for a constant `d >= 1`, and a fixed **nonconstant** local Boolean predicate

`q : A x A -> {0,1}`.

The nonconstant assumption guarantees that both local truth values occur. Hence every parity graph below is non-trivial, which is the source-side hypothesis needed for Proposition 38.

For `t >= 1`, define a square bipartite graph `G_t` with left and right vertex sets `A^t` by

`(x,y) in G_t`

iff

`q(x_1,y_1) XOR q(x_2,y_2) XOR ... XOR q(x_t,y_t) = 1`.

The side size is

`N = |A|^t = 2^(d t)`.

Its complement is the even-parity relation. In general this complement is globally correlated and is not a Cartesian product `U_0^t`; graph/complement membership cannot be certified by inspecting one coordinate independently.

Let

`a = D_intersection(q^{-1}(1) | B_{2d})`

and

`b = D_intersection(q^{-1}(0) | B_{2d})`.

Since `d` and `q` are fixed, `a` and `b` are constants.

## Lemma C012-L1 — parity-pair recurrence

Suppose sets `P,Q` are complements of each other in a fixed ambient space, and sets `R,S` are also complements of each other. Then the two sets

`P' = (P union R) intersection (Q union S)`

and

`Q' = (P union S) intersection (Q union R)`

are complements, with `P'` representing XOR of the indicator bits of `P` and `R`, and `Q'` representing XNOR.

The update uses exactly two intersection operations; unions are free in `D_intersection`.

### Proof

Evaluate the four possible indicator pairs `(p,r)`.

- `(0,0)`: `P'=0`, `Q'=1`;
- `(0,1)`: `P'=1`, `Q'=0`;
- `(1,0)`: `P'=1`, `Q'=0`;
- `(1,1)`: `P'=0`, `Q'=1`.

Thus `P'=p XOR r` and `Q'=NOT(P')` pointwise.

## Theorem C012 — fixed-local parity correlation has logarithmic cover complexity

For every `t >= 1`,

`rho(G_t, G_{N,N}) <= t(a+b) + 2(t-1)`.

In particular, for fixed `q` and `d`,

`rho(G_t, G_{N,N}) = O(t) = O(log N)`.

### Proof

For every coordinate `i`, independently construct the local sets

`R_i = { (x,y) : q(x_i,y_i)=1 }`

and

`S_i = { (x,y) : q(x_i,y_i)=0 }`

from the input-literal generators for the `2dt` encoded bits. A local construction for `q^{-1}(1)` can be copied into coordinate `i` with `a` intersections, and a local construction for `q^{-1}(0)` can be copied with `b` intersections. Across all coordinates this costs at most

`t(a+b)`

intersections.

Initialize

`P_1 = R_1`, `Q_1 = S_1`.

For `j=1,...,t-1`, apply C012-L1 with `(P,Q)=(P_j,Q_j)` and `(R,S)=(R_{j+1},S_{j+1})`. This constructs the odd-parity set `P_{j+1}` and its complement `Q_{j+1}` using two further intersections.

After `t-1` updates,

`P_t = f_{G_t}^{-1}(1)`.

Therefore

`D_intersection(f_{G_t}^{-1}(1) | B_{2dt}) <= t(a+b) + 2(t-1)`.

Because `q` is nonconstant, `G_t` is non-trivial: choose one local input with `q=1` and one with `q=0`; assigning all coordinates the latter gives even parity, while replacing one coordinate by the former gives odd parity. Proposition 38 therefore applies and gives

`rho(G_t, G_{N,N}) <= t(a+b) + 2(t-1)`.

Since `N=2^(dt)` and `d,a,b` are fixed constants, this is `O(log N)`.

## Corollary C012-IP — inner-product parity is not an R004 hard family

Take `d=1` and

`q(u,v)=u AND v`.

Then `G_t` is the standard mod-2 inner-product graph

`G_IP,t = { (x,y) : <x,y> = 1 mod 2 }`.

The local `1` predicate needs one intersection, so `a=1`. Its complement is

`NOT(u AND v) = (NOT u) OR (NOT v)`,

which uses no intersection operation from input literals, so `b=0`.

Hence

`rho(G_IP,t, G_{2^t,2^t}) <= 3t - 2 = 3 log_2 N - 2`.

The even-inner-product complement is globally correlated and lies outside C011's coordinate-product hypothesis, but it still cannot be an explicit super-logarithmic cover-complexity family.

## Why this matters

C011 showed that local coordinate witnessability makes tensor products easy. C012 shows that merely replacing coordinatewise conjunction by a global parity constraint is not enough. The source transference itself supplies a stronger upper-bound adversary: if the correlated graph-membership predicate has only linear-in-`t` intersection complexity, then graph cover complexity is automatically only `O(log N)`.

This also exposes a limitation in the auxiliary `sigma(G)` screening parameter from C010. A parity-correlated graph may have no obvious small disjoint generator-separating family, yet full cover complexity can still be small through non-disjoint pairs inherited from a compact intersection construction. O9d3 must therefore use both upper-bound adversaries:

1. explicit disjoint generator-separating pair families when available;
2. source-level intersection/cyclic-construction upper bounds when generator separation is too coarse.

## Five-role same-context research-cell review

### Complexity theory

**Vote: ACCEPT AS ROUTE REFUTATION.** The theorem is a direct construction in the exact source model and kills the first non-factorizing parity family without making any lower-bound claim.

### Meta-complexity

**Vote: ACCEPT WITH SCOPE WARNING.** This is an unrestricted-circuit route filter, not an MCSP magnification result. It does not advance O6c/O6d directly.

### Adversarial proof review

**Vote: ACCEPT PROOF DRAFT / SOURCE-DERIVED COROLLARY.** The critical checks are that `q` is nonconstant so the graph is non-trivial, both the local predicate and its complement are explicitly constructed, the recurrence maintains complementary sets, and Proposition 38 applies because `N=2^(dt)`. All are explicit. The theorem must not be extended to aggregators whose intersection complexity is superlinear in `t`.

### Formal methods

**Vote: REVISE BEFORE VERIFIED_LEMMA.** The recurrence has an executable truth-table regression, but there is no theorem-prover artifact or isolated kernel recheck. Because no novelty promotion is requested, the current status remains a bounded route refutation.

### Novelty and research value

**Vote: ACCEPT AS NO-NOVELTY-CLAIM.** This is an elementary application of the source transference theorem. Its research value is the search-space reduction and the discovery that `sigma(G)` is not a complete upper-bound adversary for correlated complements.

This review is same-context and is **not independent review**.

## Typed residual C012-R1

For fixed-alphabet correlated constructions `N=2^(dt)`, any candidate with an `O(t)`-intersection graph-membership predicate is dead for super-logarithmic R004 cover complexity.

The next viable correlated family must therefore satisfy at least one of the following before expensive lower-bound work:

- its best known intersection-complexity upper bound is superlinear in `t`;
- its full cover structure provably evades compact cyclic/intersection constructions even though membership is explicit;
- it uses a growing global constraint, such as a code/syndrome condition whose number or density of independent checks grows with `t`, rather than a fixed finite-state/parity aggregator.

A concrete next discriminator is a linear-code syndrome constrained complement with growing dual distance or check rank. Before attempting a lower bound, record the exact `D_intersection` upper bound of the membership predicate so the route cannot accidentally target a graph already known to have `O(log N)` cover complexity.

## Promotion blockers

- no theorem-prover artifact;
- no isolated independent review;
- no novelty claim requested or supported;
- theorem is only a cover-complexity upper-bound obstruction;
- root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
