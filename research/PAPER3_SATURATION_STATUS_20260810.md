# Paper 3 structural-amortization saturation status

Date: 2026-08-10  
Branch: `paper/structural-amortization-v0`

## State

**OPEN — formalism/benchmark scaffold is implemented, but the knowledge/novelty lane is not yet saturated and no efficiency result is claimed.**

## Material growth in this pass

The parent-method search changed the residual claim several times:

- MASS and Skill-It occupy skill/dependency-graph training-data selection;
- SWIFT occupies amortized structural workflow transfer;
- Reasoning Primitive Induction and TraceCompiler occupy reusable procedural primitives/workflow compilation;
- ReX occupies a persistent shared Experience Bank with dynamic cross-task composition;
- SkillGraph/SKILLGRAPH/SkillDAG/GraSP occupy dependency-aware structural skill retrieval, evolving graphs, precondition/effect DAG execution and graph-guided policy improvement;
- AgentGL demonstrates a graph-conditioned learning/inference loop;
- SkillSight shows semantic skill retrieval must be calibrated against shared descriptive background;
- asymmetric language-to-biology structural transfer supplies empirical evidence that structural transfer should be directional rather than assumed symmetric.

Each of these parents was assimilated rather than routed around.

## Current residual candidate

> A persistent, context/QoI-scoped and evidence-bearing structural object with directional mapping witnesses is used both to estimate **cross-domain training-data redundancy/selection value** and to license/reject inference-time transfer across surface-disjoint domains, with explicit non-preserved properties/boundaries and total cost-to-capability including induction and verification.

This is a candidate novelty boundary, not a final novelty claim.

## Implemented low-cost falsifiers

The branch contains executable tests for:

- Q2 low-semantic/high-structural transfer;
- Q3 high-semantic/low-structural semantic-decoy rejection;
- boundary-sensitive refusal;
- directional witness identity;
- explicit non-preserved properties;
- total-cost accounting and break-even reuse count;
- cost-to-capability under validity constraints.

The repository CI was green at the pre-latest-research head for these Python tests; later literature/manuscript-only edits must still receive their own exact-head CI result.

## Remaining research before large-scale compute

1. one additional freshness/nearest-work pass specifically for a system that uses the same explicit structural object for **training-data selection** and **inference transfer** across different surface domains;
2. strong semantic controls including SkillSight-style calibrated skill retrieval;
3. human/expert structural annotation protocol and agreement measurement;
4. expand deterministic Q1--Q4 beyond queue/feedback into multiple structure families;
5. run a small-model or no-training pilot demonstrating incremental structural transfer signal before any expensive scaling.

## Stop rule

Do not authorize large pretraining/continual-training runs if:

- structural features add no predictive value beyond strong semantic controls;
- Q3 invalid transfer remains high;
- structural annotation is unstable;
- a parent method matches the full cost/capability frontier;
- induction/verification cost destroys realistic break-even;
- training selection and inference require unrelated representations.

`paper3_saturated = false`
`empirical_efficiency_proved = false`
`shared_substrate_claim_proved = false`
