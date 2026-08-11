# RAKL Governed Upgrade Protocol

**Status:** canonical Paper 5 upgrade protocol for future RAKL 3.x challengers.  
**Authority:** this document defines process; it does not itself promote a variant or establish improvement.

## Core separation

`code exists != code is deployed != improvement is supported != method is governed incumbent`.

Direct operator deployment overrides are operational events. They create no evolution-evidence credit merely because code reaches `main`.

## Version coordinates

Track method version, Python package version, Constitution epoch, schema versions, exact Git subject and protected validator bundle separately.

Recommended semantics:

- `3.0.x`: Class-A implementation/bug fixes without intended research-policy change.
- `3.1`, `3.2`, ...: Class-B workflow/method challengers supported by preregistered matched evidence.
- a new major method/Constitution epoch: Class-C authority/governance change requiring explicit human-visible amendment review.

## Roles

Separate, as far as the execution environment permits:

1. telemetry collector;
2. upgrade proposer;
3. challenger engineer;
4. development evaluator;
5. fresh assurance evaluator;
6. governance/promotion authority;
7. post-promotion attestor.

Same-session role separation is never represented as independent review.

## Upgrade trigger

A proposal may be motivated by repeated scoped process failure, successful cross-context method transfer, retrieval coverage failure, representation/root-coordinate mismatch, repeated gluing/interface failure, chronology/provenance cost, supported saturation with stable residual, an ontology/method-basis gap, or an authority interface found to be insufficiently bound.

One anecdote may justify an issue or experiment, not promotion.

## Preregistered proposal packet

Before evaluated outcomes, freeze at least: parent method/version/SHA, change class, source episodes/diagnoses, alternative diagnoses, proposed mechanism, affected method contracts, protected paths, primary/secondary meta-QoIs, material-effect thresholds, possible regressions, negative controls, hostile near-misses, development benchmark, fresh assurance reserve, model/tool/resource contract, rollback plan, proposal hash and timestamp.

## Change classes

### Class A — implementation

Requires a reproducing defect, relevant invariant tests, preserved history and no intentional protected method change. It may justify a patch release but not a capability claim.

### Class B — workflow/method

Requires preregistered meta-QoIs, matched parent/challenger development evaluation, fresh transfer, hostile near-miss controls, resource comparability, protected evaluator identity, no blocking invariant regression and fresh protected assurance for a strong evolution claim.

### Class C — Constitution

May not auto-promote. Requires explicit human-visible amendment review, migration/backward-compatibility analysis, hostile authority tests, fresh assurance and rollback/supersession semantics.

## Coding-agent startup contract

For framework-changing work, a coding agent should read root `AGENTS.md`, `RAKL_VERSION.json`, this protocol, the affected `method_specs.py` contract and applicable protected gates before editing. It must classify A/B/C first. Class-B/C work freezes its hypothesis/evaluator/negative controls/rollback before evaluated outcomes and is implemented on a content-identified challenger branch/PR.

The candidate may not improve its score by changing the evaluator, threshold, assurance packet, subject-identity rule or Constitution rule that judges it in the same evaluation epoch.

## Challenger lifecycle

`OBSERVED_PATHOLOGY -> UPGRADE_HYPOTHESIS -> PREREGISTERED -> CHALLENGER_IMPLEMENTED -> DEVELOPMENT_VALIDATED -> FRESH_ASSURANCE_PENDING -> ASSURED | REJECTED | META_OVERFIT | CANNOT_CHECK -> GOVERNANCE_APPROVED -> PROMOTED -> ACTIVE_PROMOTION_ATTESTED -> MONITORED -> RETAINED | SUPERSEDED | ROLLED_BACK`.

Rejected and superseded variants remain evidence. Previous compatible incumbents remain rollback targets.

## Evaluation

Use two distinct designs:

1. **Method-isolation:** fork the same frozen state into parent and challenger with matched model/tools/resources.
2. **Longitudinal learning:** compare reset and persistent-learning trajectories, then freeze one learned state for independent fresh-transfer tasks.

For memory/experience claims, use Paper 5's four-arm `MODEL_ONLY / RAKL_RESET / RAKL_SHAM_MEMORY / RAKL_LEARNING` attribution design from `docs/RAKL_METROLOGY.md`.

Development tasks that motivated the upgrade are not fresh assurance.

## Meta-QoIs and blockers

Primary research QoIs may include fresh-transfer success/score, repeated-failure rate, invalid-transfer rate, root-coordinate false-progress rate, retrieval misses in a bound universe, gluing/interface detection and residual contraction. Efficiency QoIs include tokens, retrieval/tool calls, wall time and branch count.

Hard blockers include authority escalation from proposal-only evidence, lost negative history, evaluator tampering, subject mismatch, stale evidence accepted as current, false independent-review credit, fresh-transfer leakage and irreproducible candidate identity. Soft gains cannot compensate for blockers.

## Current v3 status and remaining gaps

The original v3 integration audit identified declaration-bound lesson/tool, gluing, evolution/governance and benchmark authority surfaces. Current `main` has hardened the known paths with protected content-bound attestations, subject hashes, certificate-backed local verification and adversarial/internal conformance tests. The historical audit remains negative evidence; it is not a current-code description.

Open stronger claims include:

1. independent/process-lineage-separated external assurance of the hardening;
2. cross-problem memory coverage receipts for bounded completeness/no-match claims (`RAKL#119`);
3. prospective four-arm causal-attribution data;
4. independent retained-semantic-novelty audit;
5. release-level canonical method-version subject binding;
6. longitudinal migration/rollback evidence for future stateful 3.x upgrades.

## Operator override

Record exact subject, requested deviation, known blockers and containment plan. Deployment may occur when repository permissions allow, but no improvement/assurance credit is created by the override. Post-deployment exact-main validation and rollback remain required.

## Promotion and rollback

Promotion authorization and active-deployment attestation are separate. The approved candidate, evidence, Constitution epoch and governance act must be content-bound. After ref movement, independently observe ancestry/content and exact-active-main validation. New failures never erase old evidence; they can narrow, supersede or roll back the decision.

## Paper 5 boundary

Paper 5 reports the architecture, live retrospective process cases and preregistered evaluation design. It does not claim a superior RAKL 3.1 until a future challenger earns that statement under this protocol.
