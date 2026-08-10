# C005 — exact pair-coverage criterion for canonical graph semi-filters

**Status:** PROOF_DRAFT / SOURCE-ALIGNED / NOVELTY_UNRESOLVED

This lemma is a local combinatorial tool for route R004. It is not a P-versus-NP solution and is not currently claimed novel.

## Setup

Let `G subseteq [N] x [N]` be a nontrivial bipartite graph and let

`U = G^c`.

For a row `u` and column `v`, define the subsets of the complement

`A_u = R_u intersect U`,
`B_v = C_v intersect U`.

Fix an edge `e=(u,v) in G` such that `A_u` and `B_v` are both nonempty. Following the canonical semi-filter construction used in Cavalar–Oliveira, define

`F_e = { W subseteq U : A_u subseteq W or B_v subseteq W }`.

For subsets `E,H subseteq U`, say that `(E,H)` **covers** `F_e` when `F_e` fails to preserve the pair, i.e.

`E in F_e`, `H in F_e`, but `E intersect H notin F_e`.

## Claim C005

The pair `(E,H)` covers `F_e` if and only if one of the following two oriented conditions holds.

### Orientation 1

`A_u subseteq E`,
`B_v subseteq H`,
`A_u not subseteq H`,
`B_v not subseteq E`.

### Orientation 2

`A_u subseteq H`,
`B_v subseteq E`,
`A_u not subseteq E`,
`B_v not subseteq H`.

Equivalently, the two canonical generators must be fully contained in opposite members of the pair, while neither generator may also be fully contained in the other member.

## Proof

Assume first that Orientation 1 holds. Since `A_u subseteq E`, we have `E in F_e`. Since `B_v subseteq H`, we have `H in F_e`. But `A_u not subseteq H` implies `A_u not subseteq E intersect H`, and `B_v not subseteq E` implies `B_v not subseteq E intersect H`. Hence `E intersect H notin F_e`, so `(E,H)` covers `F_e`. Orientation 2 is symmetric.

Conversely, assume `(E,H)` covers `F_e`. Because `E in F_e`, either `A_u subseteq E` or `B_v subseteq E`. Likewise, because `H in F_e`, either `A_u subseteq H` or `B_v subseteq H`.

The same canonical generator cannot be contained in both `E` and `H`: if `A_u subseteq E` and `A_u subseteq H`, then `A_u subseteq E intersect H`, implying `E intersect H in F_e`, contradiction. The same argument applies to `B_v`.

Therefore `E` and `H` must contain opposite canonical generators. If `A_u subseteq E` and `B_v subseteq H`, then the fact that `E intersect H notin F_e` forces both `A_u not subseteq H` and `B_v not subseteq E`, giving Orientation 1. The other assignment gives Orientation 2.

This proves the claim.

## Relation to the 2025 source

Cavalar–Oliveira prove the analogous criterion for their `G_NEQ` calibration graph, where the relevant complement-row and complement-column sets are singletons. C005 records the same preservation logic for an arbitrary graph edge whose two canonical complement fibers are nonempty.

The result immediately yields an exact finite oracle: enumerate pairs `(E,H)` over `U`, convert each pair into the mask of canonical edge semi-filters it covers using the criterion above, then solve the resulting minimum set-cover instance.

## Why it matters

The source proves `rho_can(G_NEQ)=log_2 N`. C005 makes it possible to search, without heuristic scoring, for structured explicit graphs whose canonical cover number exceeds this baseline on small instances.

A finite excess is only a conjecture generator. An asymptotic lower bound plus explicitness and source-bound transference are still required before any circuit-lower-bound promotion.

## Assurance blockers

- theorem-prover formalization absent;
- primary-literature novelty search for this exact arbitrary-graph formulation incomplete;
- exact-search implementation requires calibration against the published `G_NEQ` value;
- no asymptotic family lower bound has been proved.
