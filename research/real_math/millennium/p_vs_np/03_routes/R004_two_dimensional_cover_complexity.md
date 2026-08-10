# R004 — two-dimensional cover complexity for unrestricted circuit lower bounds

**State:** ACTIVE INDEPENDENT FRONTIER

This route is intentionally independent of the MCSP threshold-transport lane. It is source-bound to Bruno Pasqualotto Cavalar and Igor Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 (2025).

## Why this route is active

Let `N=2^n` and let `G subseteq [N] x [N]` be an explicit bipartite graph. Cavalar–Oliveira define graph cover complexity `rho(G, G_{N,N})` and graph intersection complexity `D_cap(G | G_{N,N})` and prove transference to ordinary Boolean circuit complexity.

The source gives three key facts for this research lane.

1. `rho(G,G_{N,N}) <= D_cap(G|G_{N,N})`.
2. A graph intersection-complexity lower bound transfers without the older large additive loss to the corresponding Boolean function.
3. Their Remark 14 shows that an explicit lower bound `C log N` on graph intersection complexity yields a related explicit Boolean function with a `C m - O(1)` lower bound on the total number of AND/OR gates, where `m=2n+1`.

The paper also proves random graphs have `Theta(N)` cover complexity, while the explicit `NEQ` graph has exactly `log N` canonical/full cover complexity. Therefore the first concrete target is not P versus NP itself. It is the smallest explicit step beyond the `NEQ` baseline.

## Atomic target R004-A

Construct an explicit polynomial-time decidable graph family `H_N` and prove, for some fixed `epsilon>0`,

`rho_can(H_N, G_{N,N}) >= (1+epsilon) log_2 N`,

or more strongly the same bound for full cover complexity `rho` or intersection complexity `D_cap`.

Because canonical cover complexity is a lower bound on full cover complexity, a canonical lower bound would provide a valid certificate. C007 now shows that this canonical subroute has a large forbidden region: if `H_N^c` has a perfect matching, then `rho_can(H_N) <= ceil(log_2 N)`.

A super-logarithmic result would not solve P versus NP, but after novelty review it could be a quantitatively new unrestricted-circuit lower-bound checkpoint through the source transference program.

## Source baseline

For

`G_NEQ = {(u,v): u != v}`,

Cavalar–Oliveira prove

`rho_can(G_NEQ) = rho(G_NEQ) = D_cap(G_NEQ) = log_2 N`

for `N=2^n`.

This is the calibration target for every exact-search implementation.

## Candidate graph fibers after C007

### Retired as super-log canonical targets

C007 gives an explicit `ceil(log_2 N)` canonical cover whenever the complement contains a perfect matching. Therefore the following previously proposed families are rejected **for the canonical-cover objective whenever their complement is always perfect-matchable**:

- constant-degree regular bipartite expanders;
- regular bipartite Cayley graphs;
- other regular balanced bipartite complement families.

This retirement does not apply to full cover complexity or graph intersection complexity.

### Still admissible generators

No lower bound is claimed for these families. They are research generators only.

- complements deliberately violating Hall's condition while retaining explicit structure;
- finite-field incidence constructions with controlled Hall deficiency;
- projective/affine incidence-derived graphs after an explicit no-perfect-matching audit;
- irregular code-incidence graphs;
- recursively composed NEQ-like graphs designed to frustrate pair reuse but also destroy the C007 matching witness;
- full semi-filter families on explicit regular/expanding complements, where C007 does not provide an upper bound.

Every canonical candidate must first run a perfect-matching/Hall audit. If a perfect matching exists, the super-log canonical route is closed immediately by C007.

## Canonical semi-filter reduction

Let `U = G^c`. For an edge `e=(u,v) in G`, define

`A_u = R_u intersect U`,
`B_v = C_v intersect U`.

When both are nonempty, the canonical semi-filter is

`F_e = {W subseteq U : A_u subseteq W or B_v subseteq W}`.

C005 records an exact criterion for when a pair `(E,H)` covers `F_e`. C006 recasts a family of pairs as realizable ternary row/column signatures. C007 uses a perfect matching in `U` to realize unconstrained binary label codes and thereby supplies an explicit logarithmic cover.

## Counterexample-first program

1. Reproduce `rho_can(G_NEQ)=ceil(log_2 N)` on tiny non-power-of-two and power-of-two cases.
2. Before exact canonical search, test whether `U` has a perfect matching. If yes, record the C007 logarithmic ceiling and do not spend asymptotic lower-bound effort on that family.
3. Enumerate/symmetry-reduce small **Hall-deficient** structured complements and search for canonical cover number strictly above `ceil(log_2 N)`.
4. In parallel, implement a bounded exact oracle for **full** semi-filter cover complexity on very small graphs, because C007 does not constrain that source-relevant quantity.
5. For any apparent winner, search aggressively for a human-readable short cover before extrapolating.
6. Only after a stable finite pattern exists, formulate an asymptotic family and lower-bound invariant.
7. Check whether the invariant is merely communication complexity, rank, fooling-set size, Hall deficiency, or another known quantity in disguise.
8. Bind any asymptotic proof through the source transference theorem before making a circuit-complexity claim.

## Important barriers

A finite graph with high exact cover number is not an asymptotic circuit lower bound. Random graphs already have linear cover complexity by the source theorem. The scientific burden is **explicitness plus an asymptotic proof**.

C007 adds another barrier specific to the canonical subfamily: expansion often helps guarantee perfect matchings, but a perfect matching gives the explicit logarithmic canonical cover. Therefore a naive plan to combine strong complement expansion with a canonical-cover lower bound was directionally wrong.

## Current research question

The primary R004 question is now bifurcated.

1. **Canonical lane:** can a deliberately Hall-deficient explicit complement force super-logarithmic canonical cover complexity without making the underlying graph trivial or easy to cover by another construction?
2. **Full-cover lane:** can the source's full semi-filter family exploit structural information that the canonical family discards, yielding an explicit super-logarithmic lower bound even when the complement has a perfect matching?

The second lane currently has higher source-level value because it survives C007 and remains directly connected to the unrestricted-circuit transference theorem.
