# Nature-style review preflight — C007 through C010

**Independence status:** SAME_CONTEXT_ONLY. These lenses were produced in the active research invocation. They do not satisfy the three-isolated-review promotion gate.

## Review setup

- **Input scope** C007, C008, C009, C010, the exact canonical-cover oracle/tests, the R004 source packet, and the active proof DAG.
- **Assessment boundary** local mathematical soundness, source binding, scope of the route refutation, and novelty risk. No root P-versus-NP review is being performed.
- **Primary source anchor** Cavalar–Oliveira, ECCC TR25-033 (2025), especially the definition of canonical semi-filters and Proposition 40 for `G_NEQ`.
- **Missing materials affecting confidence** theorem-prover formalization, isolated reviewers, and a dedicated primary-literature novelty search for the matching/star-biclique ceiling.

# Reviewer 1 — logical soundness

## Overall assessment

C007 correctly preserves a false normalization rather than hiding it. C008 repairs the normalization by eliminating only the `neither` state. C009 and C010 then use the exact three-state representation to derive a clean upper bound. The C010 matching-to-star-biclique argument appears internally coherent.

## Major Concerns

### R1-M1

- **Severity** Major
- **Blocking** Yes for promotion above proof draft
- **Claim pointer** C010-L1
- **Concern** The star-biclique partition requires every active unmatched vertex to attach to a matched neighbour and requires that a matched edge never receives unmatched extras from both sides.
- **Resolution test** Verify explicitly that maximum matching implies maximal matching, hence no edge joins two unmatched vertices, and that simultaneous opposite-side attachments to one matched edge create the augmenting path `x-r_j-l_j-y`. Preserve the active-vertex restriction so isolated complement vertices are not silently assigned.
- **Preflight disposition** The written proof performs both checks.

### R1-M2

- **Severity** Major
- **Blocking** Yes for the `q=1` boundary
- **Claim pointer** C010-L2
- **Concern** `ceil(log2 1)=0` is valid only if one biclique class implies the canonical family is empty.
- **Resolution test** Check that all active rows and columns lie in one complete bipartite subgraph of the complement. Then every pair of active endpoints lies in the complement, so no `G`-edge can have two nonempty complement fibres.
- **Preflight disposition** Boundary appears correct.

### R1-M3

- **Severity** Major
- **Blocking** Yes for the coding step
- **Claim pointer** C010-L2
- **Concern** Cross-class complement edges could corrupt endpoint signs if assigned an exclusive colour.
- **Resolution test** Put every cross-class complement edge in the C008 overlap state in every coordinate, and put all internal biclique edges in the class-code exclusive state. Then each vertex has an internal exclusive witness and no opposite-exclusive incident edge.
- **Preflight disposition** The construction does exactly this.

# Reviewer 2 — complexity and scope audit

## Overall assessment

The theorem is a route refutation for the canonical semi-filter subproblem only. It must not be generalized to full cover complexity.

## Major Concerns

### R2-M1

- **Severity** Major
- **Blocking** Yes for any full-cover claim
- **Claim pointer** Consequence section of C010
- **Concern** `rho_can` quantifies only over the canonical semi-filter family. The full source measure `rho(G,G_{N,N})` covers all relevant semi-filters and can be asymptotically much larger.
- **Resolution test** Keep the inequality direction and terminology explicit. C010 may retire only the proposed super-log **canonical** target. R004 must continue through noncanonical/full-cover objects.
- **Preflight disposition** Current wording respects this boundary.

### R2-M2

- **Severity** Major
- **Blocking** No for C010, Yes for the prior R004 target
- **Claim pointer** proof DAG O9b/O9f
- **Concern** Continuing finite searches for a super-log canonical graph after C010 would be mathematically incoherent.
- **Resolution test** Mark O9b refuted/superseded and redirect the active route to source-complete noncanonical semi-filters.
- **Preflight disposition** The DAG is updated accordingly.

### R2-M3

- **Severity** Major
- **Blocking** No
- **Claim pointer** computational oracle
- **Concern** The exact oracle remains useful for local theorem regression, but its search objective must change because the former asymptotic target is impossible.
- **Resolution test** Retain calibration and counterexample roles; do not interpret finite canonical maxima as evidence toward a super-log theorem.

# Reviewer 3 — novelty and research value

## Overall assessment

C010 is potentially useful even if known, because it sharply explains why the canonical family from the simple `G_NEQ` example cannot witness the source paper's harder full-cover regime. Novelty is completely unresolved.

## Major Concerns

### R3-M1

- **Severity** Major
- **Blocking** Yes for novelty promotion
- **Claim pointer** C008–C010
- **Concern** Union normalization, the three-state formulation, and the matching/star-biclique ceiling may be implicit in fusion-method, graph-complexity, separating-system, or biclique-partition literature.
- **Resolution test** Search exact and equivalent formulations in primary literature before any `BOUNDED_NOVEL_RESULT` or stronger label.

### R3-M2

- **Severity** Major
- **Blocking** No for route pruning
- **Claim pointer** C010-R1
- **Concern** Moving immediately to the full family of arbitrary semi-filters can recreate an exponentially unconstrained search space and lose the executable advantage of C005–C008.
- **Resolution test** Seek a compact source-complete noncanonical subclass, parameterization, or invariant before scaling proof search.

# Cross-review synthesis

## Consensus strengths

1. C007 catches and permanently records a tempting but false generalization of the published singleton-fibre normalization.
2. C008 gives an exact replacement that retains the load-bearing overlap and removes only the unnecessary state.
3. C010 has a short, falsifiable proof architecture. Maximum matching yields star-biclique clusters; binary cluster coding yields the canonical cover.
4. The theorem produces decisive route pruning rather than another unbounded proof narrative.

## Consensus blocking concerns

1. Do not promote novelty without a primary-literature equivalence search.
2. Do not apply the canonical ceiling to full cover complexity.
3. Do not label this same-context preflight independent review.
4. Any next R004 object must reconnect to the source-complete noncanonical semi-filter family.

## Recommendation posture

Merge as a bounded research checkpoint if exact-head CI passes and no repository review blocker appears. Keep C008–C010 at proof-draft / route-refutation authority. Do not promote to verified new mathematics yet.
