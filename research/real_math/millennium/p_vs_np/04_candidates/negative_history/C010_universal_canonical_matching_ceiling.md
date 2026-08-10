# C010 — universal matching-number ceiling for canonical cover complexity

**Status:** PROOF_DRAFT_ROUTE_REFUTATION / NOVELTY_UNRESOLVED

C010 resolves the discriminator opened by C009. The canonical semi-filter subproblem cannot yield a super-logarithmic graph-cover lower bound on any square bipartite graph.

This is a route-level negative theorem. It is **not** a P-versus-NP solution, and it does not upper-bound the full cover complexity studied by Cavalar–Oliveira.

## Setup

Let `G subseteq [N] x [N]` and let

`U = G^c`.

Delete isolated vertices of `U` from consideration and call the remaining left/right vertices **active**. Exactly these vertices can occur as endpoints of a canonical edge whose row and column complement fibres are both nonempty.

Let

`nu(U)`

be the maximum matching size of `U`.

Write `rho_can(G)` for the canonical cover complexity defined from the canonical semi-filters of Cavalar–Oliveira.

## Lemma C010-L1 — a maximum matching induces a vertex-disjoint star-biclique partition of the active complement graph

Let `M` be a maximum matching of `U` with edges

`e_j = (l_j,r_j)`, `j=1,...,m`,

where `m=nu(U)`.

Then all active vertices of `U` can be partitioned into `m` classes

`(L_j,R_j)`, `j=1,...,m`,

such that

1. `l_j in L_j` and `r_j in R_j`;
2. `L_j` and `R_j` are both nonempty;
3. `L_j x R_j subseteq U`;
4. every class is in fact a star biclique: at least one of `|L_j|`, `|R_j|` equals 1.

### Proof

Every unmatched active left vertex `x` has a neighbour. Since a maximum matching is maximal, no neighbour of `x` can be an unmatched right vertex; otherwise that single edge could be added to the matching. Hence `x` is adjacent to some matched right endpoint `r_j`. Choose one such endpoint and assign `x` to `L_j`.

Symmetrically, every unmatched active right vertex `y` is adjacent to some matched left endpoint `l_j`; choose one and assign `y` to `R_j`.

It remains to show that no matching edge `e_j=(l_j,r_j)` receives both an unmatched left vertex and an unmatched right vertex. If there were an unmatched left `x` adjacent to `r_j` and an unmatched right `y` adjacent to `l_j`, then

`x -- r_j -- l_j -- y`

would be an augmenting path for `M`: the first and last edges are outside the matching and the middle edge is in the matching. Flipping along this path would increase the matching size by one, contradicting maximality of `M` as a maximum matching.

Therefore a class contains either

- `r_j` together with `l_j` and zero or more unmatched left vertices, or
- `l_j` together with `r_j` and zero or more unmatched right vertices,

but never extras on both sides. By construction every extra vertex is adjacent to the single opposite matched endpoint, so `L_j x R_j subseteq U`. The classes are vertex-disjoint and cover every active vertex.

## Lemma C010-L2 — biclique-cluster coding cover

Suppose the active vertices of `U` are partitioned into `q` nonempty biclique classes

`(L_j,R_j)`, `j=1,...,q`,

with

`L_j x R_j subseteq U`.

Then

`rho_can(G) <= ceil(log_2 q)`

for `q>=2`; for `q=1` there are no canonical `G`-edges and `rho_can(G)=0`.

### Proof

For `q>=2`, choose `q` distinct binary codewords

`z_j in {0,1}^k`,
`k=ceil(log_2 q)`.

For every coordinate `i`, use the C008 three-state normal form on the complement edges:

- put every internal edge of a class `L_j x R_j` in `P_i` when `z_j[i]=0`;
- put every internal edge of that class in `M_i` when `z_j[i]=1`;
- put every remaining complement edge, necessarily a cross-class edge, in the overlap state `B_i`.

Every active row or column in class `j` has at least one internal complement edge because both sides of the class are nonempty. At coordinate `i`, all of its internal edges have the class's exclusive colour and every cross-class complement edge is in `B_i`. Hence the endpoint has sign `+` when `z_j[i]=0` and sign `-` when `z_j[i]=1`.

Take a canonical edge `(u,v) in G`. Its endpoints cannot belong to the same class: if `u in L_j` and `v in R_j`, then the biclique condition would place `(u,v)` in `U`, contradiction. Thus their class codes are distinct and differ in some coordinate. At that coordinate the endpoint signs are opposite and nonzero, so C008 covers the canonical semi-filter associated with `(u,v)`.

The `k` colourings cover all canonical semi-filters.

If `q=1`, every active left/right pair lies in the single biclique and therefore lies in `U`; there is no `G`-edge with both complement fibres nonempty, so the canonical family is empty.

## Theorem C010 — universal matching-number ceiling

For every square bipartite graph `G subseteq [N] x [N]`:

- if `nu(U)=0`, the canonical family is empty and `rho_can(G)=0`;
- if `nu(U)=1`, `rho_can(G)=0`;
- if `nu(U)>=2`,

  `rho_can(G) <= ceil(log_2 nu(U)) <= ceil(log_2 N)`.

### Proof

Apply C010-L1 with a maximum matching of size `nu(U)`, then apply C010-L2 to the resulting star-biclique partition.

## Tightness

For `G_NEQ`, the complement `U` is a perfect matching of size `N`. Cavalar–Oliveira prove

`rho_can(G_NEQ)=log_2 N`

when `N=2^n`. Therefore the universal `log N` ceiling is tight on the published calibration family.

C009 is recovered as the special case `nu(U)=N`.

## Consequence — R004 canonical super-log target is refuted

The earlier atomic target

`rho_can(G_N) >= (1+epsilon) log_2 N`

for an explicit square graph family is impossible.

This does **not** refute the Cavalar–Oliveira full-cover program. Their full cover complexity `rho(G,G_{N,N})` quantifies over all relevant semi-filters, while `rho_can` covers only the canonical subfamily. The source proves linear full cover complexity for random bipartite graphs. C010 instead proves that this linear hardness cannot be witnessed by canonical semi-filters alone.

That distinction is now a hard research boundary:

> any R004 attempt to obtain super-logarithmic graph cover complexity must use genuinely noncanonical semi-filters or another full-cover invariant.

## Computational regression

The existing exact canonical oracle remains useful as a validator for local C005/C006/C008 claims, but finite searches for a super-log canonical graph should stop. Such a target is now mathematically ruled out by C010.

A Hall-deficient complement does not escape the ceiling. Its smaller maximum matching only decreases the upper bound.

## Typed residual C010-R1

> Lift the exact three-state/overlap analysis from canonical semi-filters to a source-complete class of noncanonical semi-filters capable of witnessing full cover complexity, without reintroducing an exponentially unconstrained search object.

This is the next R004 obstruction.

## Assurance notes

- C010 is an upper bound for the canonical subproblem, not an unrestricted Boolean circuit lower bound.
- The theorem should receive theorem-prover or independent mathematical verification before any stronger promotion.
- Novelty is unresolved. The matching/star-biclique ceiling must be searched against fusion-method, graph-complexity, and separating-system literature before being labeled new.
- Root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
