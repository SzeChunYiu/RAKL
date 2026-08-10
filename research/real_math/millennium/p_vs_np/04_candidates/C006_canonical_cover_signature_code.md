# C006 — canonical cover as a constrained ternary signature code

**Status:** PROOF_DRAFT / SOURCE-ALIGNED / NOVELTY_UNRESOLVED

This is a structural reformulation of C005 for route R004. It is not a P-versus-NP solution and is not currently claimed novel.

## Setup

Let `G subseteq [N] x [N]`, let `U=G^c`, and use the canonical complement fibers

`A_u = R_u intersect U`,
`B_v = C_v intersect U`.

Restrict attention to canonical edges `(u,v) in G` for which both fibers are nonempty.

For one pair `p=(E,H)` of subsets of `U`, define a ternary row sign

`r_p(u) in {+, -, 0}`

by

- `r_p(u)=+` iff `A_u subseteq E` and `A_u not subseteq H`;
- `r_p(u)=-` iff `A_u subseteq H` and `A_u not subseteq E`;
- `r_p(u)=0` otherwise.

Define the column sign `c_p(v)` analogously from `B_v`.

For a family of `k` pairs `p_1,...,p_k`, define signatures

`r(u) = (r_{p_1}(u),...,r_{p_k}(u)) in {+, -, 0}^k`,
`c(v) = (c_{p_1}(v),...,c_{p_k}(v)) in {+, -, 0}^k`.

## Lemma C006-L1 — exact signature criterion

A pair `p_i` covers the canonical semi-filter associated with an edge `(u,v)` if and only if

`(r_{p_i}(u), c_{p_i}(v))` is either `(+, -)` or `(-, +)`.

Consequently, the `k` pairs cover all canonical edge semi-filters if and only if every canonical edge `(u,v)` has at least one coordinate `i` at which the row and column signatures have opposite nonzero signs.

### Proof

This is exactly C005 after grouping its two orientations into the ternary sign notation.

## Corollary C006-C1 — canonical cover is a constrained bipartite separation-code length

The canonical cover number is the minimum number of coordinates needed to assign **realizable** ternary row/column signatures such that every canonical graph edge is separated by an opposite-sign coordinate.

The word `realizable` is essential. The signs at one coordinate do not arise from arbitrary row and column labels. They must come from one common edge-state assignment induced by subsets `E,H subseteq U`.

This turns an R004 lower bound into two possible proof tasks.

1. Show that `k` coordinates provide too few realizable signatures to separate all canonical edges.
2. Show that the complement-incidence constraints force collisions or non-opposite endpoint pairs when `k` is small.

## Lemma C006-L2 — complement-incidence witness constraints

Fix one pair `(E,H)` and write

`R_+ = {u : r_p(u)=+}`,
`R_- = {u : r_p(u)=-}`,
`C_+ = {v : c_p(v)=+}`,
`C_- = {v : c_p(v)=-}`.

Then:

1. every `u in R_+` has at least one complement neighbour in `[N] \ C_-`;
2. every `u in R_-` has at least one complement neighbour in `[N] \ C_+`;
3. every `v in C_+` has at least one complement neighbour in `[N] \ R_-`;
4. every `v in C_-` has at least one complement neighbour in `[N] \ R_+`.

### Proof of item 1

Because `u in R_+`, all complement edges in `A_u` lie in `E`, and at least one edge `x=(u,v') in A_u` does not lie in `H`.

If `v'` were in `C_-`, then `B_{v'} subseteq H`, forcing the shared complement edge `x` into `H`, contradiction. Thus `v' notin C_-`.

The other three statements follow symmetrically.

### Interpretation

The excluded column set `[N] \ C_-` must dominate `R_+` in the complement graph `U`, and similarly for the other orientations. Therefore expansion, domination, or incidence properties of `U` can constrain which large opposite-sign rectangles are realizable by one pair.

## Calibration C006-C2 — the NEQ coding lower bound

For the published calibration graph `G_NEQ`, the complement `U` is the diagonal perfect matching. Hence each nonempty row and column fiber is the same singleton corresponding to its label.

At one coordinate, the row and column signs of label `u` are identical:

- `+` when its matching edge lies in `E \ H`;
- `-` when it lies in `H \ E`;
- `0` otherwise.

Therefore covering every edge `(u,v)` with `u != v` requires a family of ternary words `s(u) in {+, -, 0}^k` such that every two distinct words have an opposite-sign coordinate.

For each ternary word `s`, let `Q(s) subseteq {+,-}^k` be the nonempty set of binary completions obtained by replacing every `0` arbitrarily by `+` or `-`.

Two ternary words have no opposite-sign coordinate if and only if their completion sets intersect. Thus pairwise edge coverage makes the sets `Q(s(u))` pairwise disjoint. Since the binary cube has only `2^k` points,

`N <= 2^k`,

so

`k >= ceil(log_2 N)`.

Conversely, assign `N` distinct binary words of length `ceil(log_2 N)` to the labels and define each pair coordinate from its `+` and `-` matching edges. This covers every unequal pair. Therefore the canonical cover number of `G_NEQ` is

`ceil(log_2 N)`

for arbitrary `N>=2`, and specializes to the source statement `log_2 N` when `N=2^n`.

This arbitrary-`N` calibration extension is elementary and is not claimed as a novel result.

## What a super-logarithmic explicit construction now requires

NEQ allows essentially one unconstrained binary bit of label separation per cover pair. To force more than `log N` pairs, an explicit complement graph must make each realizable coordinate convey **strictly less effective separation information** than an unconstrained binary coordinate across the graph edges that still need coverage.

A useful asymptotic invariant would therefore bound the growth, over `k` realizable pair coordinates, of the largest edge-separable row/column signature system.

Candidate source-level parameters to test include:

- robust domination profiles of the complement graph;
- vertex/edge expansion;
- spectral mixing;
- neighbourhood overlap and private-neighbour structure;
- VC/shatter behavior of complement fibres;
- entropy of realizable ternary signatures under the shared edge-state constraint.

## Typed residual C006-R1

> Find an explicit family `U_N` for which every `k`-coordinate realizable signature system with `k <= (1+epsilon) log_2 N` necessarily leaves at least one canonical edge with no opposite-sign coordinate.

A proof of this residual would imply the corresponding super-logarithmic canonical cover lower bound. It would still require source-bound transference and novelty/assurance review before any Boolean-circuit claim is promoted.
