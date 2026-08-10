# C007 — perfect-matching ceiling for canonical cover complexity

**Status:** PROOF_DRAFT_NEGATIVE_ROUTE_CHECKPOINT / SOURCE-ALIGNED / NOVELTY_UNRESOLVED

This is a route-pruning lemma for R004. It is **not** a P-versus-NP solution, does not upper-bound full graph cover complexity, and is not currently claimed novel.

## Setup

Let `G subseteq [N] x [N]` be a bipartite graph and let

`U = G^c`.

Use the canonical complement fibers and semi-filters from C005/C006. Thus for a row `u` and column `v`,

`A_u = R_u intersect U`,
`B_v = C_v intersect U`,

and for each graph edge `(u,v) in G` with both fibers nonempty,

`F_(u,v) = {W subseteq U : A_u subseteq W or B_v subseteq W}`.

Let `rho_can(G)` be the minimum number of pairs `(E,H)` of subsets of `U` required to cover all such canonical edge semi-filters.

Assume the complement graph `U` contains a perfect matching

`M = {(u, pi(u)) : u in [N]}`

for a permutation `pi` of `[N]`.

## Claim C007

If `U` contains a perfect matching, then

`rho_can(G) <= ceil(log_2 N)`.

Therefore no explicit family whose complement always has a perfect matching can yield a super-logarithmic lower bound through the **canonical** semi-filter subfamily alone.

## Proof

Let

`k = ceil(log_2 N)`.

Assign the `N` rows distinct binary codewords

`c(u) in {+,-}^k`.

For each coordinate `i in [k]`, construct a pair `(E_i,H_i)` as follows.

1. Put every nonmatching complement edge in `U \ M` into **both** `E_i` and `H_i`.
2. For the matching edge `m_u=(u,pi(u))`:
   - if `c_i(u)=+`, put `m_u` in `E_i` and not in `H_i`;
   - if `c_i(u)=-`, put `m_u` in `H_i` and not in `E_i`.

Consider any row `u`. Every nonmatching edge of its complement fiber `A_u` lies in both sets. Its unique matching edge `m_u` is exclusive to the set selected by `c_i(u)`. Hence the ternary row sign of C006 is exactly

`r_i(u) = c_i(u)`.

Likewise, because column `pi(u)` has the same unique matching edge `m_u`, its ternary column sign is

`c_i(pi(u)) = c_i(u)`

where the left-hand `c_i(pi(u))` denotes the C006 column sign, not the row code notation.

Now take any graph edge `(u,v) in G`. Since `(u,pi(u))` belongs to the complement `U`, we have

`v != pi(u)`.

Let

`w = pi^{-1}(v)`.

Then `w != u`. Because the binary codewords assigned to distinct rows are distinct, there is some coordinate `i` with

`c_i(u) != c_i(w)`.

At that coordinate, row `u` and column `v=pi(w)` have opposite nonzero C006 signs. By C005/C006, the pair `(E_i,H_i)` covers the canonical semi-filter associated with `(u,v)`.

Every graph edge is therefore covered by at least one of the `k` pairs, proving

`rho_can(G) <= k = ceil(log_2 N)`.

## Immediate corollary — regular complements are dead as canonical super-log targets

Every finite `d`-regular bipartite graph with equal left and right sides and `d>=1` has a perfect matching by Hall's theorem. Consequently, if `U_N=G_N^c` is regular bipartite, then

`rho_can(G_N) <= ceil(log_2 N)`.

This eliminates complements of constant-degree regular bipartite expanders, regular Cayley graphs, and any other always-perfect-matchable complement family as candidates for a **super-logarithmic canonical-cover** lower bound.

The statement does **not** eliminate those families from the full cover-complexity or graph-intersection-complexity programs.

## Exact finite evidence

The tiny exact oracle was used only as a falsification/calibration aid before the proof was written.

- For `N=3`, exhaustive full-support complements with at most six complement edges never exceeded the NEQ baseline `ceil(log_2 3)=2`.
- For `N=4`, exhaustive full-support complements with at most six complement edges never exceeded the NEQ baseline `2`.
- For `N=5`, the perfect-matching complement has canonical cover `3`, while a matching plus a cyclic shift has exact canonical cover `2`.

These finite checks are not part of the theorem proof and carry no asymptotic authority.

## Five-role same-context research-cell review

### Complexity-theory lens

**Vote:** ACCEPT AS NEGATIVE ROUTE CHECKPOINT.

The proof is elementary and correctly scoped to canonical cover complexity. It does not establish an upper bound on full graph cover complexity or graph intersection complexity, so R004 remains open.

### Meta-complexity lens

**Vote:** ACCEPT WITH SCOPE WARNING.

There is no MCSP threshold implication. The value is search-space reduction. Future canonical-cover searches should avoid perfect-matchable complements unless the goal is calibration rather than a super-logarithmic lower bound.

### Adversarial proof-review lens

**Vote:** ACCEPT PROOF DRAFT.

The critical edge case is handled. A graph edge `(u,v)` cannot equal the complement matching edge `(u,pi(u))`, so `u` and `pi^{-1}(v)` are distinct and therefore receive different binary codewords. Putting all nonmatching complement edges into both `E_i` and `H_i` does not destroy the exclusive matching-edge witness that fixes each row/column sign.

### Formal-methods lens

**Vote:** REVISE BEFORE THEOREM PROMOTION.

Add an executable constructor for the matching-derived cover and tests that it covers every canonical edge for NEQ and complements containing a specified perfect matching. A proof-assistant artifact is still absent.

### Novelty / research-value lens

**Vote:** ACCEPT AS NOVELTY_UNRESOLVED.

The primary 2025 source establishes the NEQ logarithmic calibration and motivates explicit super-logarithmic cover lower bounds, but this exact perfect-matching ceiling was not identified in the source text reviewed for this run. A broader prior-art search is still required before any novelty claim. The immediate research value is high because it invalidates several previously listed canonical candidate families at once.

This five-role review occurred in one research context. It is **not independent review** and cannot satisfy the RAKL three-isolated-review gate.

## Source boundary

Primary source checked at the 2026-08-10 cutoff:

- Bruno Pasqualotto Cavalar and Igor Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033, published 21 March 2025.

The source proves random graphs have linear full graph cover complexity and that explicit super-logarithmic graph cover lower bounds would have significant circuit-complexity consequences. It also proves the logarithmic `G_NEQ` calibration used by C005/C006. C007 is a derived local lemma and is not attributed to the source.

## Typed residual C007-R1

One of the following must now replace the retired regular-complement canonical search:

1. construct an explicit complement family with **no perfect matching** and prove a super-logarithmic canonical-cover lower bound;
2. prove a stronger general ceiling showing the canonical semi-filter subfamily is intrinsically unable to exceed the desired baseline for a wider class; or
3. move to the **full** semi-filter cover complexity and seek an explicit super-logarithmic lower bound there, where the perfect-matching construction above does not supply an upper bound.

The third option currently has the strongest connection to the primary source's unrestricted-circuit transference program.
