# Nature-style review preflight — C004 and C006

**Independence status:** SAME_CONTEXT_ONLY. These lenses are a preflight produced in the active research invocation. They do not satisfy the three-isolated-review promotion gate.

## Review setup

- **Input scope** C004, R004, C005, C006, source addendum, and the active proof DAG.
- **Assessment boundary** local mathematical soundness, complexity-theory interpretation, source alignment, and route value. No root-solution review is being performed.
- **Missing materials affecting confidence** formal theorem-prover artifacts, isolated reviewers, exhaustive novelty search, and exact-head CI for the current branch.

# Reviewer 1 — logical soundness

## C004

### R1-M1

- **Severity** Major
- **Blocking** Yes for promotion above proof draft
- **Claim pointer** STACS 2021 threshold-transport corollary
- **Concern** C004-L1 is an exponential-scale statement. Exact MCSP reductions are threshold-boundary statements. The asymptotic no-amplification theorem alone does not prove an exact many-one reduction impossibility for every possible threshold slack convention.
- **Why it matters** A gap-preserving transformation could exploit subexponential multiplicative/additive slack without contradicting the exponent calculation.
- **Resolution test** Keep C004 scoped to exponential threshold/length ratio and ordinary black-box exact-threshold strategies. Route any non-negligible boundary slack explicitly into Gap-MCSP with frozen completeness/soundness parameters.

### R1-M2

- **Severity** Major
- **Blocking** No for the negative checkpoint, Yes for the broadest prose form
- **Claim pointer** examples including AND/OR/XOR/direct products
- **Concern** restriction recovery is automatic only when the aggregator and function family admit an appropriate fixed assignment of the other copies. XOR recovers `f` or its complement, but AND/OR require a satisfying/falsifying assignment for nonconstant functions.
- **Resolution test** State that each named example is covered only when the registered family satisfies the explicit restriction-recovery hypothesis. Do not universalize the example list to all Boolean functions.

## C006

### R1-M3

- **Severity** Major
- **Blocking** No for proof draft
- **Claim pointer** NEQ calibration
- **Concern** The arbitrary-`N` `ceil(log2 N)` extension is not source authority. It is an elementary extension derived in this work and must remain separated from the published `N=2^n` statement.
- **Resolution test** Preserve the current wording that the source calibration is for `N=2^n` and the arbitrary-`N` statement is an unclaimed elementary extension.

# Reviewer 2 — complexity/barrier audit

### R2-M1

- **Severity** Major
- **Blocking** Yes for treating C004 as exhaustion of R002
- **Claim pointer** C004 residual
- **Concern** C004 eliminates subexponential black-box copying, not non-black-box self-reductions, promise/gap transformations, hardness amplification exploiting structure of MCSP instances, or direct high-threshold magnification.
- **Why it matters** Overreading the checkpoint would prematurely abandon a viable meta-complexity fiber.
- **Resolution test** Keep O6c/O6d open and require each successor to identify the mechanism that violates a C004 hypothesis.

### R2-M2

- **Severity** Major
- **Blocking** Yes for interpreting R004 finite search as circuit progress
- **Claim pointer** R004 and canonical-cover oracle
- **Concern** Canonical cover complexity is only a lower-bound proxy for full cover complexity. Tiny exact values and even finite values above the NEQ baseline do not constitute an asymptotic explicit circuit lower bound.
- **Resolution test** Require an explicit infinite family, a proof of a super-logarithmic lower bound, source-bound transference, and comparison with the exact gate basis/constant of known unrestricted lower bounds.

### R2-M3

- **Severity** Major
- **Blocking** No for C006, Yes for the proposed spectral route if ignored
- **Claim pointer** C006-L2 and residual C006-R1
- **Concern** A one-coordinate edge-count bound is likely too weak. NEQ already needs `log N` pairs although a single pair can cover a constant fraction of edges. A successful `>log N` proof probably needs a multi-coordinate information/coding invariant, not only maximum per-pair coverage.
- **Resolution test** Treat domination/expansion as constraints on realizable signature systems across coordinates, not merely as a one-shot set-cover density estimate.

# Reviewer 3 — novelty and research value

### R3-M1

- **Severity** Major
- **Blocking** Yes for novelty promotion
- **Claim pointer** C004
- **Concern** The exponent-preservation observation may be folklore or implicit in hardness-magnification work. Independent derivation does not establish novelty.
- **Resolution test** Search primary MCSP/hardness-magnification and lower-bound-amplification literature for equivalent no-go observations before any novelty label.

### R3-M2

- **Severity** Major
- **Blocking** Yes for novelty promotion
- **Claim pointer** C005/C006
- **Concern** The arbitrary-graph pair criterion and ternary-signature encoding may be standard reformulations of the fusion/cover graph machinery or separating systems.
- **Resolution test** Search primary cover-complexity, fusion-method, separating-code, and communication-complexity literature using normalized formulations.

### R3-M3

- **Severity** Major
- **Blocking** No
- **Claim pointer** R004
- **Concern** The route has high information value because the 2025 source explicitly leaves explicit super-logarithmic cover lower bounds open, but the first meaningful milestone should be a proved asymptotic family, not a catalogue of finite hard instances.
- **Resolution test** Use the oracle only to select/formulate an explicit family and falsify conjectured invariants. Promote research value only when an asymptotic proof survives.

# Cross-review synthesis

## Consensus strengths

1. C004 materially prunes a broad but precisely stated class of MCSP threshold transports.
2. C005/C006 convert R004 into an exact finite and coding-theoretic object rather than a vague new direction.
3. The research program keeps negative results and route boundaries explicit.

## Consensus blocking concerns

1. Exact MCSP boundary slack must not be hidden inside an exponential-scale argument.
2. C004 hypotheses must remain visible when examples are named.
3. R004 requires an explicit asymptotic family and a multi-coordinate realizability invariant before it can become a circuit lower bound.
4. Novelty is unresolved for C004-C006.

## Immediate actions

- retain C004 as `PROOF_DRAFT_NEGATIVE_CHECKPOINT`;
- keep Gap-MCSP/non-black-box/high-threshold fibers open;
- use C006 as the discriminator for candidate explicit complement graphs;
- calibrate the exact oracle in CI before trusting generated finite candidates;
- next theory target: bound the capacity of realizable ternary signature systems over an explicit complement-incidence family.
