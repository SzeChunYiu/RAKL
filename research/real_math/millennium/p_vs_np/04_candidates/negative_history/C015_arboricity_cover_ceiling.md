# C015 — arboricity ceiling for full graph cover complexity

**Status:** PROOF_DRAFT_ROUTE_REFUTATION / EXECUTABLE_WITNESS / NO_NOVELTY_CLAIM

C015 advances O9d7 by attacking a blind spot left by C014. Maximum degree rules out bounded-degree candidates, but it says almost nothing about sparse graphs with a few very high-degree vertices. A star has maximum degree `Theta(N)` and therefore escapes the useful regime of C014, even though its edge structure is extremely simple.

The correct sparse-structure adversary is stronger. If a bipartite graph is the union of only a few forests, then its full graph cover complexity is still only logarithmic. This kills constant-arboricity families even when their maximum degree grows linearly with `N`.

This is an R004 route-pruning upper bound. It is not a Boolean circuit lower bound and is not a P-versus-NP solution. No novelty claim is made.

## Primary-source model and refreshed provenance

Primary source checked on 2026-08-11:

Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 (18 March 2025), later ACM Transactions on Computation Theory 17(2), Article 13, DOI `10.1145/3718746`.

ECCC report: `https://eccc.weizmann.ac.il/report/2025/033/`

The paper defines, for a target set `A` and generator family `B`, the intersection complexity `D_intersection(A | B)` as the minimum number of pairwise intersections sufficient to construct `A`; unions may be used but are not counted by this measure. For a bipartite graph `G subseteq [N] x [N]`, the graph generator family `G_{N,N}` consists of the `N` rows and `N` columns. Equation (1) of the paper gives

`rho(A,B) <= D_intersection(A | B) <= rho(A,B)^2`.

C015 uses only the left inequality and the source definition of intersection complexity. No lower-bound transference claim is invoked by this negative checkpoint.

## Constructive definition of the sparse parameter

For this checkpoint define `a(G)` to be the minimum integer `a >= 1` such that the edge set of the nonempty graph `G` can be partitioned into `a` forests.

This is the usual edge-arboricity parameter, but C015 needs no external arboricity theorem. The proof starts from any supplied forest partition and derives the cover upper bound directly.

Let

`k = ceil(log_2 N)`

for `N >= 2`.

## Lemma C015-L1 — one-sided partial-function graphs cost at most `2k` intersections

Let `H subseteq [N] x [N]` be nonempty and suppose every right vertex is incident to at most one edge of `H`. Equivalently, `H` is the graph of a partial function from the right side to the left side. Then

`D_intersection(H | G_{N,N}) <= 2k`.

The symmetric statement holds when every left vertex is incident to at most one edge.

### Proof

Assign the `N` left vertices distinct binary codes of length `k`. For each active right vertex `v`, give `v` the code of its unique neighbour `f(v)`. Give inactive right vertices any fixed code; they will be removed at the end.

For each bit position `b`, let

`A_b = (union of rows whose b-th code bit is 1) union (union of columns whose b-th code bit is 0)`,

and

`B_b = (union of rows whose b-th code bit is 0) union (union of columns whose b-th code bit is 1)`.

One counted intersection produces

`E_b = A_b intersection B_b`.

A cell `(u,v)` belongs to `E_b` exactly when the two endpoint codes agree in bit `b`. Constructing the `k` sets `E_b` costs `k` intersections. Intersecting all of them costs another `k-1` intersections and leaves exactly one cell in each right column, namely the row whose code equals the right-column code.

Let `C_active` be the free union of all columns belonging to active right vertices. Intersect once with `C_active`. This removes the artificial cells in inactive columns and leaves exactly `H`.

The total number of counted intersections is

`k + (k-1) + 1 = 2k`.

The left-to-right case is identical with rows and columns exchanged.

## Lemma C015-L2 — every bipartite forest costs at most `4k` intersections

Let `F subseteq [N] x [N]` be a nonempty forest. Then

`D_intersection(F | G_{N,N}) <= 4k`.

### Proof

Root each connected component of `F` arbitrarily and orient every edge away from its root. Partition the edges into two classes.

- `F_L` contains the edges whose parent endpoint lies on the left side.
- `F_R` contains the edges whose parent endpoint lies on the right side.

Every right vertex has at most one parent, so `F_L` is a partial function from right vertices to left vertices. Every left vertex has at most one parent, so `F_R` is a partial function from left vertices to right vertices.

By C015-L1, each nonempty class costs at most `2k` intersections. Construct them independently and take their union. The final union adds no intersection cost. Hence

`D_intersection(F | G_{N,N}) <= 4k`.

If one orientation class is empty, the actual bound is at most `2k`.

## Theorem C015 — arboricity ceiling

Let `G subseteq [N] x [N]` be a nonempty bipartite graph with `N >= 2`. If its edge set can be partitioned into `a` forests, then

`rho(G,G_{N,N}) <= D_intersection(G | G_{N,N}) <= 4 a ceil(log_2 N)`.

In particular, with `a=a(G)`,

`rho(G,G_{N,N}) <= 4 a(G) ceil(log_2 N)`.

### Proof

Write

`G = F_1 union ... union F_a`

as an edge-disjoint forest partition. C015-L2 constructs every nonempty `F_i` using at most `4k` counted intersections. Construct all forest sets independently and union them. Since unions do not contribute to `D_intersection`,

`D_intersection(G | G_{N,N}) <= 4ak`.

The source inequality `rho <= D_intersection` gives the cover-complexity bound.

## Strict improvement over the C014 screen

C014 gives

`rho(G) <= Delta(G) * (2 ceil(log_2 N)+1)`.

For a star with `N` edges, `Delta(G)=N`, so C014 gives only `O(N log N)`. C015 observes that a star is itself a forest and therefore gives

`rho(G) <= 4 ceil(log_2 N)`.

Thus a family can have unbounded or even linear maximum degree and still be automatically unusable as a super-logarithmic R004 target because its arboricity stays bounded.

## Counterexample-first executable calibration

`05_falsification/arboricity_cover.py` realizes the constructions as actual subsets of `[N] x [N]`.

It checks:

- right-to-left and left-to-right partial-function reconstruction by endpoint equality codes;
- exact removal of inactive-domain cells by one final row/column mask;
- rooting/orienting a supplied bipartite forest and partitioning it by parent side;
- fail-closed rejection when a supplied edge set contains a cycle;
- additive reconstruction from an explicitly supplied edge-disjoint forest partition;
- the high-degree-star case that C014 does not prune sharply.

The matching construction of C014 is not reused as a black box; C015 directly verifies its stronger partial-function primitive.

## Five-role same-context research-cell review

### Complexity theory

**Vote: ACCEPT AS ROUTE REFUTATION.** The orientation argument is a valid structural strengthening of the degree screen. It removes a large class of apparently growing-degree candidates without making any lower-bound claim.

### Meta-complexity

**Vote: ACCEPT WITH NO ROOT CLAIM.** This result lives wholly inside the R004 search-control fiber. It does not advance MCSP hardness magnification, and it supplies no direct `P != NP` consequence. Its value is reducing the family search space before expensive exact cover work.

### Adversarial proof review

**Vote: ACCEPT PROOF DRAFT SUBJECT TO CI.** The load-bearing checks are that endpoint codes are injective on the image side, inactive-domain artifacts are removed by a legal generator union plus one intersection, the forest orientation gives each child exactly one parent, the two orientation classes cover every forest edge, and the final forest union is free in the source's intersection-complexity accounting. The theorem assumes a forest partition rather than importing an unverified algorithm for computing arboricity.

### Formal methods

**Vote: REVISE BEFORE VERIFIED_LEMMA.** The theorem is finite/combinatorial and suitable for formalization, and the executable witnesses make the exact set identities testable. However, there is no theorem-prover artifact, source-formalization witness, dependency receipt, or isolated checker recheck. Authority remains proof draft.

### Novelty and research value

**Vote: ACCEPT AS NO-NOVELTY-CLAIM.** The coding and forest orientation arguments are elementary and may be folklore or implicit in graph-complexity literature. No bounded novelty search has been completed because no novelty claim is requested. The useful contribution to this project is diagnostic: bounded arboricity is now a first-line upper-bound adversary for R004.

This five-role review is same-context only and is **not independent review**.

## Typed residual C015-R1

A viable O9d successor must now survive quotient compression, matching/degree compression, and forest/arboricity compression.

In particular, a family proposed for a super-logarithmic full-cover lower bound should have all of the following before asymptotic proof budget is spent:

- no small identical-neighbourhood quotient with logarithmic cover;
- edge arboricity `a(G_N)` growing with `N` fast enough that `4 a(G_N) log N` is not already the intended ceiling;
- no bounded-degree decomposition making C014 stronger;
- no low-dimensional linear syndrome, local-coordinate, block, or product representation from C010--C013;
- no direct source-level intersection/cyclic construction of logarithmic size;
- exact small-instance evidence that full-cover pair reuse is not collapsing the candidate.

The next search should therefore target **growing-arboricity, nonlinear, globally correlated relations**, and should attempt an arboricity/forest decomposition before interpreting pseudorandom or algebraic notation as cover hardness.

## Promotion blockers

- no theorem-prover artifact;
- no isolated independent review;
- no bounded novelty search because no novelty claim is requested;
- theorem is an R004 upper-bound obstruction only;
- exact CI has not yet been recorded in this document at commit time;
- root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
