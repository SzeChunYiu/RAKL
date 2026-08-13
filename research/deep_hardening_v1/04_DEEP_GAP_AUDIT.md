# Deep gap audit — framework and mechanics

Statuses:

- `ON_MAIN`: already closed at the frozen repository subject;
- `PATCHED_HERE`: executable additive contract in this packet;
- `GATED`: cannot be honestly closed without fresh empirical/formal/external evidence;
- `MIGRATION`: implementation exists here but must be integrated without breaking legacy identities.

## A. Integrity, identity and serialization

| Gap | Status | Closure / next obligation |
|---|---|---|
| Ambient Decimal context changes canonical bytes | `PATCHED_HERE` | context-free `as_tuple()` numeric encoding; regression across precisions |
| Float “exactness” represented textually rather than by bits | `PATCHED_HERE` | canonical binary64 bytes |
| Unicode normalization policy ambiguous | `PATCHED_HERE` | explicit versioned policy; default preserve in general commitment |
| `repr(...)` used for current training snapshot/catalog identity | `MIGRATION` | canonical v2 assurance sidecar; do not rewrite historical hashes |
| `repr(...)` used by v3 state fingerprint | `MIGRATION` | additive V3 state commitment; dual-write first |
| Domain separation incomplete across commitment purposes | `PATCHED_HERE` | every canonical hash call names a domain |
| Supply-chain identity not necessarily bound to every derived artifact | `GATED/MIGRATION` | receiving AI should bind builder code/config/input roots to SLSA-style provenance where artifacts are release-bearing |

## B. Structural transfer and quotients

| Gap | Status | Closure / next obligation |
|---|---|---|
| Duplicate structural boundary keys silently collapse through `boundary_map`; duplicate relations/evidence can distort identity/counting | `PATCHED_HERE exact-base edit` | structural type guards + regression tests |
| `non_preserved_properties` stored but not enforced at use site | `PATCHED_HERE` | explicit acknowledgement + resolved witness/property preservation receipts |
| Completeness by counts can preserve wrong items | `ON_MAIN` | current base uses set inclusion |
| Non-finite approximate quotient tolerance (`NaN`/`inf`) can evade the old `< 0` constructor check | `PATCHED_HERE exact-base edit` | require finite non-negative tolerance + full-repo regression |
| A forbidden loss can be placed in `conditionally_erased_coordinates` without tripping the old erased-only intersection | `PATCHED_HERE exact-base edit` | forbidden loss rejects unconditional **or conditional** erasure |
| A caller-created passing TCSQ validation report can be used without resolving an external verifier/replay receipt | `PATCHED_HERE additive use gate` | `semantic_quotient_assurance.py` binds report/proposal/source/evidence to a resolved receipt |
| Approximate quotient tolerance does not automatically compose downstream | `PATCHED_HERE` | approximation budget sidecar with ADDITIVE/MAX/CUSTOM composition |
| Derived lossy view may appear to carry source authority if certificate IDs are copied | `PATCHED_HERE` policy | derived authority defaults provenance-only; reverify exact scope before inheritance |
| Quotient used for navigation without reachability-specific proof | `ON_MAIN + DEEPENED` | current `navigation_quotient.py`; full abstraction class in VTG |
| Abstract “no route” can be mistaken for concrete impossibility | `PATCHED_HERE` | only exact backward-complete quotient can support that interpretation; still no mathematical-impossibility claim beyond subject |

## C. Geometry and search

| Gap | Status | Closure / next obligation |
|---|---|---|
| Operational subject too weakly bound | `PATCHED_HERE` | kernel/tool/options/operator/transition/map/chart/cost hashes |
| Reachability quantifier implicit | `PATCHED_HERE` | existential, controllable, robust, almost-sure, threshold, expected-cost, game typed separately |
| Budget placed inside metric can break geometry laws | `ON_MAIN` | current Lawvere cost geometry puts budget in sublevel set |
| Predictive/semantic distance confused with plannability | `GATED` | Phase-1 closed-loop local routing with fresh families |
| Learned geometry may contain hidden route oracle | `PATCHED_HERE + GATED` | leakage flags and split binding; empirical audit still required |
| Geometry may go stale when map/operator/chart changes | `PATCHED_HERE` | exact `OperationalSubject` equality determines staleness |
| Geometry construction can cost more than it saves | `PATCHED_HERE + GATED` | full CostVector + baseline/geometry total cost + reuse/invalidation horizon |
| Strict local descent can trap despite good one-step alignment | `ON_MAIN evidence + GATED` | evaluate branching curve `N(k,B)`, false descent and local minima |
| Geometry certification duplicated across new subsystem | `PATCHED_HERE design` | reuse current `fieldability` certification classes/witnesses; VTG only binds their identity hash |
| “Certified basin” based on sampled transitions | `PATCHED_HERE` | theorem obligations + assurance floor excluding candidate edges |
| Natural dynamics added before geometry exists | `GATED` | prohibited by experiment ladder |

## D. Search/certificate/authority separation

| Gap | Status | Closure / next obligation |
|---|---|---|
| Search trajectory treated as proof | `PATCHED_HERE / existing DAG` | trajectory explicitly not certificate; constellation binds existing proof DAG/root receipt |
| Verified children automatically imply verified parent | `PATCHED_HERE` | amalgamation obligations + root verifier required |
| Training metric or model improvement moves scientific authority | `PATCHED_HERE + existing noninterference` | cognitive compilation checks `epi_before == epi_after`; scientific promotion remains separate |
| Internal HMAC fixture mistaken for production trust root | `PATCHED_HERE policy` | explicit `INTERNAL_HMAC_FIXTURE` vs `EXTERNAL_PUBLIC_KEY` / `EXTERNAL_ATTESTATION_SERVICE` |
| Authority sidecar does not bind evidence/evaluator/trust backend | `PATCHED_HERE` | `CertificateAssuranceBinding` |
| Evidence lineage may cycle or end at an unregistered upstream ID; old terminal-root logic can miscount malformed cycles as independent roots | `PATCHED_HERE exact-base edit` | lineage traversal fails closed on cycle/unresolved parent before independent-root accounting |

## E. Diagnosis and self-improvement

| Gap | Status | Closure / next obligation |
|---|---|---|
| One-shot diagnosis can change labels without immutable discriminator result | `PATCHED_HERE` | state transition requires selected registered discriminator and outcome |
| `UNKNOWN` treated as a real identified cause | `ON_MAIN` | current base fails closed |
| Repair can be evaluated on same examples used to discover defect | `PATCHED_HERE + GATED` | cognitive compilation requires disjoint fresh assurance |
| Proposer/evaluator are same identity | `PATCHED_HERE` | fresh assurance rejects same identity |
| Challenger model overwrites incumbent automatically | `PATCHED_HERE policy` | explicit model-promotion eligibility only; governance remains external |
| Negative/retracted history disappears after repair | `GATED integration` | receiving AI must preserve existing RAKL negative-history and retracted Phase-1 v1 artifacts |

## F. Neural/training mechanics

| Gap | Status | Closure / next obligation |
|---|---|---|
| Conditional similarity mistaken for RAKL novelty | `GATED` | matched conditional-metric parent mandatory |
| Symmetric quotient scorer asked to model one-way transfer | `PATCHED_HERE formal diagnostic` | reversed-pair ceiling + asymmetric witness head requirement |
| Generic relational/causal bottleneck not included as parent | `GATED` | require strong relational/causal comparators |
| Adaptive structural curriculum claimed before learner signal | `GATED` | corrected Phase-1 v2 first |
| Training checkpoint/tokenizer/optimizer/sampling not fully content-bound | `PATCHED_HERE` | training assurance sidecar |
| Exact structure ID drifts external→train→inference | `PATCHED_HERE` | shared bundle + equality check across stages |
| Fresh task/test overlap hidden behind new IDs | `PATCHED_HERE` | split identity disjointness and new identity receipt; semantic leakage still needs benchmark-specific audit |

## G. Cross-surface composition

| Gap | Status | Closure / next obligation |
|---|---|---|
| Strong modules remain individually correct but can be combined with mismatched base/receipts | `PATCHED_HERE` | `UnifiedMechanicsManifest` binds one base, state commitment, structural identity, operational subject and required resolved receipts; readiness grants no authority |
| “all gaps filled” can be confused with “all experiments succeeded” | `PATCHED_HERE process` | software closure and scientific closure are different terminals; the latter remains preregistered/gated |

## H. Remaining scientific coordinates that code cannot close

1. Does SQ-3 show net benefit after quotient construction, validation, reconstruction and original verification?
2. Does a RAKL-specific neural residual survive strongest matched parents?
3. Does structural failure diagnosis improve weight updates beyond generic failure-example fine-tuning/reflection/distillation?
4. Does exact shared structural identity add benefit, or only bookkeeping?
5. Does verifier-defined mathematical reachability admit useful local geometry at all on held-out formal theorem families?
6. If yes, which geometry class and what branching budget is required?
7. Do multi-chart portals improve total cost after portal construction/verification?
8. Do adaptive dynamics improve matched total cost over best-first/MCTS/equality saturation?
9. Does the integrated framework outperform simpler research workflows at matched resource ceilings?
10. Does fresh independent assurance reproduce the claimed improvements?

Any next AI that converts these to `SUPPORTED` without executing the registered evidence gates is violating the framework rather than completing it.
