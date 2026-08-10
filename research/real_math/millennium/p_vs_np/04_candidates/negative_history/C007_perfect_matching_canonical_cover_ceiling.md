# C007 — perfect-matching ceiling for canonical cover complexity

**Status:** PROOF_DRAFT_NEGATIVE_ROUTE_CHECKPOINT / SOURCE-ALIGNED / NOVELTY_UNRESOLVED

This is a route-pruning lemma for R004. It is **not** a P-versus-NP solution, does not upper-bound full graph cover complexity, and is not currently claimed novel.

## Setup

Let `G subseteq [N] x [N]` be a bipartite graph and let `U = G^c`. Use the canonical complement fibers and semi-filters from C005/C006. Thus

`A_u = R_u intersect U`, `B_v = C_v intersect U`,

and for each graph edge `(u,v) in G` with both fibers nonempty,

`F_(u,v) = {W subseteq U : A_u subseteq W or B_v subseteq W}`.

Let `rho_can(G)` be the minimum number of pairs `(E,H)` of subsets of `U` required to cover all canonical edge semi-filters. Assume `U` contains a perfect matching

`M = {(u, pi(u)) : u in [N]}`

for a permutation `pi` of `[N]`.

## Claim C007

If `U` contains a perfect matching, then

`rho_can(G) <= ceil(log_2 N)`.

Therefore no explicit family whose complement always has a perfect matching can yield a super-logarithmic lower bound through the **canonical** semi-filter subfamily alone.

## Proof

Let `k = ceil(log_2 N)` and assign the `N` rows distinct binary codewords `b(u) in {+,-}^k`.

For each coordinate `i`, construct a pair `(E_i,H_i)`.

1. Put every nonmatching complement edge in `U \ M` into both `E_i` and `H_i`.
2. For the matching edge `m_u=(u,pi(u))`, put `m_u` in `E_i \ H_i` if `b_i(u)=+`, and in `H_i \ E_i` if `b_i(u)=-`.

For any row `u`, every nonmatching edge of `A_u` lies in both sets, while its unique matching edge `m_u` is exclusive to the set selected by `b_i(u)`. Hence the C006 row sign is exactly `b_i(u)`. The same argument shows that the C006 sign of column `pi(u)` is also `b_i(u)`.

Now take a graph edge `(u,v) in G`. Since `(u,pi(u)) in U`, necessarily `v != pi(u)`. Let `w=pi^{-1}(v)`. Then `w != u`, so distinct codewords `b(u)` and `b(w)` disagree in some coordinate `i`. At that coordinate, row `u` and column `v=pi(w)` have opposite nonzero signs. By C005/C006, `(E_i,H_i)` covers `F_(u,v)`.

Thus the `k` pairs cover every canonical graph edge and

`rho_can(G) <= k = ceil(log_2 N)`.

## Immediate corollary — regular complements are dead as canonical super-log targets

Every finite `d`-regular balanced bipartite graph with `d>=1` has a perfect matching by Hall's theorem. Therefore if `U_N=G_N^c` is regular bipartite,

`rho_can(G_N) <= ceil(log_2 N)`.

This eliminates regular constant-degree bipartite expanders, regular Cayley graphs, and any other always-perfect-matchable complement family as candidates for a **super-logarithmic canonical-cover** lower bound. It does not eliminate them from full cover complexity or graph intersection complexity.

## Counterexample-first finite evidence

The tiny exact oracle was used only to guide the proof.

- Exhaustive `N=3` full-support complements with at most six complement edges never exceeded `ceil(log_2 3)=2`.
- Exhaustive `N=4` full-support complements with at most six complement edges never exceeded `2`.
- For `N=5`, the perfect-matching complement has canonical cover `3`, while a matching plus a cyclic shift has exact canonical cover `2`.

These checks are not part of the proof and carry no asymptotic authority.

## Five-role same-context research-cell review

### Complexity theory

**Vote:** ACCEPT AS NEGATIVE ROUTE CHECKPOINT. The proof is correctly scoped to canonical cover complexity and does not upper-bound full cover or graph intersection complexity.

### Meta-complexity

**Vote:** ACCEPT WITH SCOPE WARNING. There is no MCSP threshold consequence. The value is search-space reduction.

### Adversarial proof review

**Vote:** ACCEPT PROOF DRAFT. The critical edge case is handled: a graph edge cannot be its complement matching edge, so the corresponding row codes are distinct. Shared nonmatching complement edges do not destroy the exclusive matched-edge witnesses.

### Formal methods

**Vote:** REVISE BEFORE THEOREM PROMOTION. Add an executable constructor and tests that the matching-derived pairs cover every canonical edge. A proof-assistant artifact remains absent.

### Novelty and research value

**Vote:** ACCEPT AS NOVELTY_UNRESOLVED. The primary 2025 source gives the NEQ logarithmic calibration and motivates explicit super-logarithmic cover lower bounds, but the exact perfect-matching ceiling was not identified in the source text reviewed in this run. Broader prior-art search remains required. The immediate value is route pruning.

This five-role review occurred in one research context and is **not independent review**.

## Source boundary

Primary source checked at the 2026-08-10 cutoff:

- Bruno Pasqualotto Cavalar and Igor Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033, published 21 March 2025.

The source reports random graphs with linear graph cover complexity and motivates explicit super-logarithmic cover lower bounds with circuit-complexity consequences. C007 is a derived local lemma and is not attributed to that source.

## Typed residual C007-R1

One of the following must replace the retired regular-complement canonical search:

1. construct an explicit complement family with no perfect matching and prove a super-logarithmic canonical-cover lower bound;
2. prove a stronger ceiling showing the canonical semi-filter subfamily is insufficient for a wider class; or
3. move to **full** semi-filter cover complexity and seek an explicit super-logarithmic lower bound there, where C007 supplies no upper bound.

The third option currently has the strongest direct connection to the primary source's unrestricted-circuit transference program.
