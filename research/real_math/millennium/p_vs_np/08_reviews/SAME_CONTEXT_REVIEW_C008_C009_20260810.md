# Nature-style review preflight — C008 and C009

**Independence status:** SAME_CONTEXT_ONLY. These reports were produced in the active research invocation. They do not satisfy the three-isolated-review promotion gate.

## Review setup

- **Input scope** merged C005-C007 canonical-cover machinery, C008, C009, exact oracle/tests, the current R004 proof DAG, and the Cavalar-Oliveira source packet.
- **Assessment boundary** local mathematical soundness, scope, novelty risk, and route-control value. No root P-versus-NP review is being performed.
- **Primary source anchor** Cavalar and Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 / ACM TOCT 17(2), 2025.
- **Novelty-search boundary** focused searches of the current source, fusion-method/graph-complexity terminology, and exact matching/semi-filter phrases did not surface an equivalent matching-number ceiling. This is insufficient to establish novelty.
- **Missing materials affecting confidence** theorem-prover formalization, three isolated reviewers, and a deeper primary-literature equivalence search through the older fusion/graph-complexity papers.

# Reviewer 1 — logical soundness

## Overall assessment

C008 correctly distinguishes a false normalization from a valid one. C009 appears to be a valid finite combinatorial ceiling for the canonical subproblem and strictly subsumes the perfect-matching special case already merged as C007.

## Major Concerns

### R1-M1

- **Severity** Major
- **Blocking** Yes for C008 promotion
- **Claim pointer** C008-X1 and C008-L1
- **Concern** The invalid step and valid replacement must not be conflated. Deleting overlap can fail, whereas adding all `neither` elements to both sides is safe.
- **Resolution test** Preserve the explicit three-element counterexample for overlap deletion and prove union normalization directly from C005's four containment conditions.
- **Preflight disposition** Passed in the current draft and regression suite.

### R1-M2

- **Severity** Major
- **Blocking** Yes for C009
- **Claim pointer** C009-L1
- **Concern** The maximum-matching construction must cover every active unmatched vertex while ensuring each matched edge receives extras from at most one side.
- **Resolution test** Use maximum implies maximal to rule out unmatched-to-unmatched complement edges. If an unmatched left vertex attaches to `r_j` and an unmatched right vertex attaches to `l_j`, exhibit the augmenting path `x-r_j-l_j-y`.
- **Preflight disposition** Passed in the written proof.

### R1-M3

- **Severity** Major
- **Blocking** Yes for C009-L2
- **Claim pointer** biclique-cluster coding
- **Concern** Cross-class complement edges could corrupt endpoint signs.
- **Resolution test** Put every internal biclique edge in the class-code exclusive state and every cross-class complement edge in overlap. Check that every active class vertex has an internal exclusive witness and no opposite-exclusive incident edge.
- **Preflight disposition** Passed.

### R1-M4

- **Severity** Major
- **Blocking** Yes for the `nu(U)<=1` boundary
- **Claim pointer** theorem statement
- **Concern** The zero-cover boundary requires the canonical family to be empty, not merely easy.
- **Resolution test** With matching number one, C009-L1 produces one biclique containing every active vertex. Hence every active left/right pair is a complement edge, so there is no graph edge with two active endpoints.
- **Preflight disposition** Passed.

# Reviewer 2 — complexity and scope audit

## Overall assessment

The central scientific value is route pruning. C009 must not be generalized from canonical cover complexity to the full source measure.

## Major Concerns

### R2-M1

- **Severity** Major
- **Blocking** Yes for any circuit-lower-bound inference
- **Claim pointer** C009 route consequence
- **Concern** `rho_can` covers only the canonical semi-filter subfamily. Cavalar-Oliveira's full cover complexity quantifies over all relevant semi-filters and is the object that can be linear on random graphs.
- **Resolution test** Retire only the super-log canonical target and keep R004 active through noncanonical/full-cover objects.
- **Preflight disposition** Current DAG does so.

### R2-M2

- **Severity** Major
- **Blocking** No for the theorem, Yes for future search allocation
- **Claim pointer** exact canonical oracle
- **Concern** Once C009 is accepted as a proof draft, searching for finite super-log canonical examples is incoherent.
- **Resolution test** Keep the oracle for regression, counterexample generation, and local theorem checks; move asymptotic search budget to a compact source-complete noncanonical family.

### R2-M3

- **Severity** Major
- **Blocking** No
- **Claim pointer** R004 successor
- **Concern** Brute-force enumeration of all semi-filters can reintroduce an exponentially unconstrained object and destroy the advantage of the canonical formulation.
- **Resolution test** Before scaling computation, identify the smallest source-complete noncanonical subclass or a typed invariant that provably lower-bounds full cover complexity.

# Reviewer 3 — novelty and mathematical value

## Overall assessment

C009 may be useful whether novel or rediscovered. It closes a tempting canonical route and clarifies why the source paper's random full-cover lower bound cannot be witnessed by canonical filters alone. Novelty remains unresolved.

## Major Concerns

### R3-M1

- **Severity** Major
- **Blocking** Yes for novelty promotion
- **Claim pointer** C008-C009
- **Concern** The three-state normalization and matching/star-biclique ceiling may be implicit in older fusion-method, graph-complexity, biclique-partition, or separating-system literature even if absent from the 2025 paper's visible canonical discussion.
- **Resolution test** Search primary older sources and normalized equivalents before assigning `BOUNDED_NOVEL_RESULT` or stronger authority.

### R3-M2

- **Severity** Major
- **Blocking** No for route-control merge
- **Claim pointer** C009-R1
- **Concern** The next research object should remain directly connected to the source transference theorem. An arbitrary new combinatorial measure without a proved relation to full cover complexity would be another disconnected proxy.
- **Resolution test** Bind the next noncanonical object to the exact full-cover definition before generating candidate lower bounds.

# Cross-review synthesis

## Consensus strengths

1. C008 catches a real proof trap and replaces it with an exact normal form.
2. C009 provides a short, falsifiable universal ceiling that subsumes merged C007.
3. The result materially reduces search space rather than producing another speculative proof narrative.
4. The scope boundary between canonical and full cover complexity is explicit.

## Consensus blocking concerns

1. Novelty is unresolved.
2. This same-context preflight is not independent review.
3. No canonical upper bound may be interpreted as a full-cover or circuit upper bound.
4. The next R004 object must be source-bound to noncanonical/full cover complexity.

## Recommendation posture

Merge as a bounded route-control checkpoint if exact-head CI passes and repository integration is clean. Keep C008 and C009 at proof-draft / route-refutation authority. Do not promote either as verified new mathematics yet.
