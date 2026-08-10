# C014 — maximum-degree ceiling for full graph cover complexity

**Status:** PROOF_DRAFT_ROUTE_REFUTATION / EXECUTABLE_WITNESS / NO_NOVELTY_CLAIM

C014 attacks O9d6 after C013 ruled out low-cover quotient blow-ups and linear syndrome relations. The next counterexample-first screen asks whether a graph can look globally nonlinear and still be easy merely because its edge set is sparse.

The answer is yes for bounded maximum degree. A bipartite graph of maximum degree `Delta` decomposes into at most `Delta` matchings, while every matching has logarithmic intersection complexity in the row/column generator model. Therefore bounded-degree graph families cannot have super-logarithmic full cover complexity.

This is an upper-bound obstruction for the R004 graph-cover route. It is not a Boolean circuit lower bound and is not a P-versus-NP solution. No novelty claim is made.

## Primary-source model

Use Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 / ACM Transactions on Computation Theory 17(2), Article 13 (2025), DOI `10.1145/3718746`.

For a bipartite graph `G subseteq [N] x [N]`, let `G_{N,N}` be the row/column generator family. The source defines `D_intersection(G | G_{N,N})` as the minimum number of pairwise intersections in any union/intersection construction of `G` from those generators. Unions may occur in the construction but do not contribute to `D_intersection`. The source fusion bound gives

`rho(G,G_{N,N}) <= D_intersection(G | G_{N,N})`.

C014 only needs these source definitions/inequality. The matching decomposition is proved below so the checkpoint does not depend on importing a graph-edge-colouring theorem as a black box.

## Theorem C014

Let `G subseteq [N] x [N]` be a non-trivial bipartite graph with `N >= 2`, and let `Delta >= 1` be its maximum degree over both sides. Put

`k = ceil(log_2 N)`.

Then

`rho(G,G_{N,N}) <= D_intersection(G | G_{N,N}) <= Delta * (2k + 1)`.

Consequently, every explicit family with `Delta=O(1)` has

`rho(G,G_{N,N}) = O(log N)`

and is unusable as a super-logarithmic full-cover target in R004.

## Lemma C014-L1 — a matching costs at most `2k+1` intersections

Let `M subseteq [N] x [N]` be a nonempty matching. Then

`D_intersection(M | G_{N,N}) <= 2k+1`.

### Proof

Extend `M` to a perfect matching `P` of the complete bipartite ambient graph by pairing the unmatched left vertices bijectively with the unmatched right vertices.

Assign the `N` matched pairs of `P` distinct `k`-bit strings. A left vertex and its partner on the right receive the same code.

For each bit position `b`, define two unions of row/column generators:

`A_b = (union of rows whose b-th code bit is 1) union (union of columns whose b-th code bit is 0)`,

`B_b = (union of rows whose b-th code bit is 0) union (union of columns whose b-th code bit is 1)`.

Set

`E_b = A_b intersection B_b`.

For a cell `(u,v)`, membership in `E_b` holds exactly when the b-th code bit of `u` equals the b-th code bit of `v`. Constructing all `E_b` therefore uses exactly `k` counted intersections. Intersect the `k` sets `E_b`; this needs `k-1` additional intersections and leaves exactly `P`, because all `N` codes are distinct. Thus

`D_intersection(P | G_{N,N}) <= 2k-1`.

If `M=P`, this is already stronger than required. Otherwise let `L_M` be the union of rows incident to `M` and `R_M` the union of columns incident to `M`. Their rectangle

`Q_M = L_M intersection R_M`

costs one more intersection. Since `P` is a matching extending `M`,

`M = P intersection Q_M`,

which costs one final intersection. Hence

`D_intersection(M | G_{N,N}) <= (2k-1)+2 = 2k+1`.

Unions used to form `A_b`, `B_b`, `L_M`, and `R_M` do not count toward intersection complexity by the source definition.

## Lemma C014-L2 — a maximum-degree-Delta bipartite graph partitions into at most Delta matchings

Let `G` have maximum degree `Delta`.

### Proof without importing edge colouring

Add parallel dummy edges between left and right vertices until every vertex has degree exactly `Delta`. This is possible because the total degree deficit on the left and on the right are both

`Delta*N - |E(G)|`;

pair the two deficit-stub multisets arbitrarily. The result is a `Delta`-regular bipartite multigraph on the same two vertex sets.

Every regular bipartite multigraph has a perfect matching. Indeed, for any left subset `S`, exactly `Delta*|S|` incident edge copies leave `S`. All terminate in its neighbour set `N(S)`, whose vertices together have capacity at most `Delta*|N(S)|`. Hence

`|S| <= |N(S)|`,

so Hall's condition holds.

Remove one perfect matching. The remaining multigraph is `(Delta-1)`-regular. Repeating gives a partition of all multiedges into `Delta` perfect matchings.

Now delete the dummy edge copies. The original simple edges of `G` are partitioned among at most `Delta` ordinary matchings. Empty restricted colour classes may be discarded.

## Proof of C014

Use C014-L2 to write the edge set as a disjoint union

`G = M_1 union ... union M_s`

with `s <= Delta` and each `M_i` a nonempty matching.

By C014-L1, each `M_i` can be constructed using at most `2k+1` intersections. Construct the matching sets separately, then take their union. The final unions require no additional counted intersections. Therefore

`D_intersection(G | G_{N,N}) <= s*(2k+1) <= Delta*(2k+1)`.

The source fusion inequality then gives

`rho(G,G_{N,N}) <= Delta*(2k+1)`.

## Counterexample-first executable calibration

The helper `05_falsification/bounded_degree_cover.py` implements the set construction behind C014-L1 rather than trusting the prose proof. It:

- validates that a proposed edge set is a matching;
- extends it deterministically to a perfect matching;
- assigns distinct binary codes;
- realizes every equality-bit set from unions of row/column generators followed by one intersection;
- intersects equality bits to reconstruct the perfect matching;
- applies the active-row/active-column rectangle for a partial matching;
- reports the explicit counted-intersection bound.

Regression tests check permuted perfect matchings, partial matchings for non-power-of-two `N`, a two-matching cycle decomposition, and fail-closed duplicate-row/duplicate-column inputs. These are construction checks only, not asymptotic proof authority.

## Five-role same-context research-cell review

### Complexity theory

**Vote: ACCEPT AS ROUTE REFUTATION.** The two ingredients compose correctly. Bipartite maximum degree controls the matching partition count, and each matching is cheap in the row/column intersection model. The result eliminates all bounded-degree candidates before any full-cover lower-bound search.

### Meta-complexity

**Vote: ACCEPT WITH NO ROOT CLAIM.** This is search control inside R004. It provides no direct MCSP consequence and no unrestricted circuit lower bound. A dense or growing-degree graph remains fully open to the route.

### Adversarial proof review

**Vote: ACCEPT PROOF DRAFT.** The load-bearing checks are that the multigraph regularization preserves equal left/right deficit counts, Hall's argument is valid with parallel edges, restricting the perfect-matching decomposition partitions every original edge exactly once, unused binary codes create no cells because only actual vertices receive codes, and a partial matching is exactly `P intersection (L_M x R_M)`. No complement operation is hidden in the construction.

### Formal methods

**Vote: REVISE BEFORE VERIFIED_LEMMA.** The executable set-equality witness checks the construction on finite instances, but there is no theorem-prover artifact, formal source binding, or isolated kernel recheck. Authority remains proof draft.

### Novelty and research value

**Vote: ACCEPT AS NO-NOVELTY-CLAIM.** The decomposition and coding argument are elementary and could be folklore or an immediate consequence of standard graph-complexity observations. Its value here is diagnostic: it adds maximum degree as a first-line R004 upper-bound adversary. No new-mathematics claim is supported.

This five-role review is same-context only and is **not independent review**.

## Typed residual C014-R1

A viable O9d successor must now survive both C013 quotient compression and C014 degree compression.

In particular, an asymptotic super-log candidate should have:

- no small identical-neighbourhood quotient whose own cover is logarithmic;
- maximum degree growing with `N` fast enough that `Delta*(2 ceil(log_2 N)+1)` is not already an `O(log N)` ceiling;
- no simple source-level `D_intersection` or cyclic construction giving `O(log N)` anyway;
- evidence from exact small instances that pair reuse is not collapsing the full semi-filter cover.

The next lane should therefore examine genuinely nonlinear, growing-degree, globally correlated relations only after applying quotient compression and the degree/matching ceiling. Algebraic or pseudorandom-looking notation is not evidence of cover hardness.

## Promotion blockers

- no theorem-prover artifact;
- no isolated independent review;
- no bounded novelty search because no novelty claim is requested;
- theorem is an R004 upper-bound obstruction only;
- root P-versus-NP status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
