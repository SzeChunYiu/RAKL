# R004 — two-dimensional cover complexity for unrestricted circuit lower bounds

**State:** ACTIVE INDEPENDENT FRONTIER

This route is intentionally independent of the MCSP threshold-transport lane. It is source-bound to Cavalar and Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 (2025).

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

Because canonical cover complexity is a lower bound on full cover complexity, a canonical lower bound already provides a valid certificate.

This would not solve P versus NP, but it would be a quantitatively new unrestricted-circuit lower-bound checkpoint if it exceeds the strongest source-equivalent baseline after novelty review.

## Source baseline

For

`G_NEQ = {(u,v): u != v}`,

Cavalar–Oliveira prove

`rho_can(G_NEQ) = rho(G_NEQ) = D_cap(G_NEQ) = log_2 N`

for `N=2^n`.

This is the calibration target for every exact-search implementation.

## Candidate graph fibers

No lower bound is claimed for the following families. They are generators only.

- complements of constant-degree bipartite expanders;
- finite-field inner-product / orthogonality graphs;
- projective-plane or affine-plane incidence-derived graphs;
- quadratic-residue / Paley-type bipartite graphs;
- error-correcting-code incidence graphs;
- Cayley graphs with strong spectral mixing;
- recursively composed NEQ-like graphs designed to frustrate pair reuse.

Every family must be rejected early if an explicit small cover construction gives `O(log N)`.

## Canonical semi-filter reduction

Let `U = G^c`. For an edge `e=(u,v) in G`, define

`A_u = R_u intersect U`,
`B_v = C_v intersect U`.

When both are nonempty, the canonical semi-filter is

`F_e = {W subseteq U : A_u subseteq W or B_v subseteq W}`.

Candidate C005 records an exact criterion for when a pair `(E,H)` covers `F_e`. This turns the canonical lower-bound subproblem into a finite set-cover problem and supports exact small-instance search.

## Counterexample-first program

1. Reproduce `rho_can(G_NEQ)=ceil(log_2 N)` on tiny non-power-of-two and power-of-two cases.
2. Enumerate/symmetry-reduce small structured complements `U` and search for graphs with canonical cover number strictly above `ceil(log_2 N)`.
3. For any apparent winner, search aggressively for a human-readable short cover before extrapolating.
4. Only after a stable finite pattern exists, formulate an asymptotic family and a lower-bound invariant.
5. Check whether the invariant is merely communication complexity, rank, fooling-set size, or another known quantity in disguise.
6. Bind any asymptotic proof through the source transference theorem before making a circuit-complexity claim.

## Important barrier

A finite graph with high exact cover number is not an asymptotic circuit lower bound. Random graphs already have linear cover complexity by the source theorem. The scientific burden is **explicitness plus an asymptotic proof**.

## Current research question

Can canonical semi-filter coverage be bounded using an expansion/spectral property of the complement graph `U`, in a way that forces each pair `(E,H)` to cover only a controlled fraction of edges and therefore requires more than `log N` pairs?

The first step is to make pair coverage exact and executable. That is C005 plus the tiny canonical-cover oracle.
