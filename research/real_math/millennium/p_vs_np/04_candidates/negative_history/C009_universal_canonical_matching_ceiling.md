# C009 — universal matching-number ceiling for canonical cover complexity

**Status:** PROOF_DRAFT_ROUTE_REFUTATION / NOVELTY_UNRESOLVED

C009 strictly generalizes the merged perfect-matching checkpoint C007. It closes the Hall-deficient escape hatch for the **canonical** semi-filter subproblem. It does not upper-bound the full cover complexity of Cavalar–Oliveira and is not a P-versus-NP solution.

## Source boundary

The source model is Cavalar–Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 / ACM TOCT 17(2), 2025. Their Definitions 18–21 define semi-filters, the above relation, pair preservation, and cover complexity. Their Proposition 40 proves `rho_can(G_NEQ)=log_2 N` for `N=2^n`, and their Theorem 37 shows that random graphs have full cover complexity `Theta(N)`.

C009 concerns only the canonical subfamily introduced in their Section 4.2.

## Setup

Let `G subseteq [N] x [N]` and let

`U = G^c`.

A left or right vertex is **active** when it has positive degree in `U`. Only graph edges whose two endpoints are active produce canonical semi-filters, because the row and column complement fibres must both be nonempty.

Let `nu(U)` be the maximum matching size of the bipartite graph `U`. Let `rho_can(G)` denote canonical cover complexity.

## Lemma C009-L1 — a maximum matching partitions active vertices into star-biclique classes

Let `M` be a maximum matching of `U`, with edges

`e_j=(l_j,r_j)`, `j=1,...,m`,

where `m=nu(U)`.

Then the active vertices can be partitioned into `m` classes `(L_j,R_j)` such that

1. `l_j in L_j` and `r_j in R_j`;
2. both sides of every class are nonempty;
3. `L_j x R_j subseteq U`;
4. at least one side of each class is a singleton.

### Proof

Every unmatched active left vertex `x` has a neighbour. Because a maximum matching is maximal, every neighbour of `x` is a matched right endpoint. Choose one such neighbour `r_j` and assign `x` to `L_j`.

Symmetrically, assign every unmatched active right vertex `y` to a class `R_j` whose matched left endpoint `l_j` is adjacent to `y`.

No matched edge can receive unmatched extras from both sides. If unmatched `x` is adjacent to `r_j` and unmatched `y` is adjacent to `l_j`, then

`x -- r_j -- l_j -- y`

is an augmenting path with the middle edge in `M`, contradicting maximality of `M` as a maximum matching.

Thus each class is either a left star around `r_j`, a right star around `l_j`, or the matched edge alone. Hence every class is a complete bipartite subgraph of `U`, the classes are vertex-disjoint, and they cover all active vertices.

## Lemma C009-L2 — biclique-class binary coding covers every canonical semi-filter

Suppose the active vertices of `U` are partitioned into `q` nonempty biclique classes `(L_j,R_j)` with

`L_j x R_j subseteq U`.

For `q>=2`, choose distinct binary codes

`z_j in {0,1}^k`, where `k=ceil(log_2 q)`.

For each coordinate `i`, construct a pair `(E_i,H_i)` of subsets of `U` as follows.

- Every complement edge whose endpoints lie in the same class `j` goes exclusively into `E_i` when `z_j[i]=0` and exclusively into `H_i` when `z_j[i]=1`.
- Every complement edge whose endpoints lie in different classes goes into **both** `E_i` and `H_i`.

Take a canonical graph edge `(u,v) in G`. Its endpoints are active. They cannot lie in the same class because each `L_j x R_j` is contained in the complement `U`. Therefore their class codes are distinct and differ in some coordinate `i`.

In that coordinate, the entire complement row fibre of `u` is contained in the side assigned to `u`'s class, while it is not contained in the opposite side because the row has at least one internal class edge. Cross-class complement edges lie in both sides and cannot remove this exclusive witness. The same statement holds for the complement column fibre of `v`.

Because the two class bits differ, the row and column fibres satisfy opposite orientations of the exact canonical pair criterion from C005. Hence `(E_i,H_i)` covers the canonical semi-filter of `(u,v)`.

Thus `k` pairs cover every canonical semi-filter.

For `q=1`, all active left/right vertex pairs lie in the single complement biclique, so no graph edge has two active endpoints. The canonical family is empty and `rho_can(G)=0`.

## Theorem C009 — universal canonical ceiling

If `nu(U)<=1`, then

`rho_can(G)=0`.

If `nu(U)>=2`, then

`rho_can(G) <= ceil(log_2 nu(U)) <= ceil(log_2 N)`.

### Proof

Apply C009-L1 to a maximum matching, obtaining `q=nu(U)` biclique classes. Apply C009-L2.

## Tightness

For `G_NEQ`, the complement is a perfect matching of size `N`. Cavalar–Oliveira prove

`rho_can(G_NEQ)=log_2 N`

for `N=2^n`. Therefore the universal logarithmic ceiling is tight on the source calibration family.

## Route consequence

The former canonical target

`rho_can(G_N) >= (1+epsilon) log_2 N`

is impossible for every square graph family. Hall deficiency does not evade the C007 obstruction. It can only decrease the matching-number ceiling.

This does **not** refute the full two-dimensional cover programme. Full cover complexity quantifies over all relevant semi-filters, and the source proves `Theta(N)` full cover complexity for random graphs. The merged finite checkpoint C008 already shows that canonical cover can be strictly smaller than full cover on an explicit `3 x 3` graph.

The active R004 route therefore remains the full/noncanonical semi-filter problem.

## Five-role same-context research-cell review

### Complexity theory

**ACCEPT AS ROUTE REFUTATION.** The matching argument is elementary and the scope is correctly restricted to canonical semi-filters. The main consequence is to retire all super-log canonical searches.

### Meta-complexity

**ACCEPT WITH SCOPE WARNING.** C009 has no direct MCSP implication and does not establish a root bridge to `P != NP`.

### Adversarial proof review

**ACCEPT PROOF DRAFT.** The critical point is the length-three augmenting-path argument. It guarantees that a matching class cannot acquire unmatched extras on both sides. The coding proof then uses only internal complement edges for exclusive witnesses and puts all cross-class edges in both sets.

### Formal methods

**REVISE BEFORE VERIFIED-LEMMA AUTHORITY.** Executable exhaustive regression is useful but is not theorem-prover formalization or an isolated proof recheck.

### Novelty and research value

**ACCEPT ONLY AS NOVELTY_UNRESOLVED.** The statement should be searched against matching, biclique partition, separating-system, graph-complexity, and fusion-method literature before any novelty promotion.

This review was produced in one research context and is not independent review.

## Typed residual C009-R1

> Work only with genuinely noncanonical semi-filters or another source-complete invariant for full cover complexity. Any proposed compact subfamily must have an explicit theorem connecting it to the full source definition before it is used for asymptotic lower-bound claims.

## Promotion blockers

- theorem-prover formalization absent;
- isolated independent review absent;
- bounded novelty search absent;
- no full-cover asymptotic lower bound follows from C009;
- no root P-versus-NP certificate exists.
