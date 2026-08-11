# RAKL Governed Upgrade Protocol

**Status:** proposal-only challenger specification for Paper 5 and future RAKL 3.x evolution.  
**Base incumbent inspected:** `SzeChunYiu/RAKL@decd1a4eae2b10cfdbb98e76b5023e2a756fa7a8` on 2026-08-11.  
**Authority:** this document does not itself promote a framework variant, change the Constitution, or establish an empirical improvement.

## 1. Purpose

RAKL is intended to improve through accumulated research experience without allowing the component that proposes a change to certify its own success. A framework upgrade is therefore not defined as “new code landed on `main`.” It is a governed inference that a content-identified challenger performs better, or is safer/more faithful, under a frozen evaluation boundary without violating protected invariants.

The protocol separates four facts that are easy to conflate:

```text
code exists
!= code is deployed
!= method improvement is supported
!= method is the governed incumbent
```

A human/operator may deliberately deploy code before assurance is complete. Such an event is an operational override, not evidence that the method improved.

## 2. Version identity

RAKL should carry several version coordinates rather than one overloaded version string.

```text
software_package_version  # distribution/API compatibility, e.g. pyproject.toml
method_version            # research-method generation, e.g. 3.0.0, 3.1.0
constitution_epoch        # protected authority/governance rules
schema_versions           # per artifact type
exact_git_subject         # full commit SHA
validator_bundle_hash     # protected evaluator/checker identity
```

Recommended method-version semantics:

- `3.0.x`: Class-A implementation/bug fixes that do not intentionally change research policy.
- `3.1.0`, `3.2.0`, ...: Class-B workflow/method changes supported as distinct challengers.
- `4.0.0` or another major-method epoch: Class-C constitutional changes that alter protected authority/governance semantics and require human-visible amendment review.

The Python package version and RAKL method version need not advance together. A paper must cite the exact Git subject and method identity used in each experiment.

## 3. Roles and authority separation

A strong upgrade claim uses role separation even when one organization operates all components.

1. **Research observer / telemetry collector**
   - records TaskEpisode-style public decision traces, outcomes, residuals, costs and source bindings;
   - cannot promote a lesson or framework change.
2. **Upgrade proposer**
   - may be Codex, another coding agent, or a human;
   - converts repeated process evidence into a falsifiable framework-improvement hypothesis;
   - freezes the predicted benefit, possible regression and target meta-QoIs before implementation results are observed.
3. **Challenger engineer**
   - implements the proposal on a content-identified branch;
   - cannot change protected evaluators, hidden assurance tasks or promotion thresholds that will judge the challenger.
4. **Development evaluator**
   - runs visible, frozen development and replay tests;
   - may expose results for debugging but those tasks cease to be assurance evidence.
5. **Fresh assurance evaluator**
   - uses a packet frozen before mutation and hidden from the proposer/optimizer;
   - should have process and evidence-lineage separation from the challenger;
   - consumes a bounded assurance exposure budget.
6. **Governance / promotion authority**
   - decides whether an assured challenger becomes incumbent;
   - constitutional changes require explicit human-visible amendment review;
   - must use content-bound attestations, not a caller-supplied Boolean.
7. **Post-promotion attestor**
   - observes the actual active repository/ref after promotion;
   - proves that active `main` descends from the approved candidate, required paths match, exact-candidate CI passed, and exact-active-main post-promotion validation passed.

No same-session role separation is represented as independent review.

## 4. What may trigger an upgrade proposal

An upgrade hypothesis should be linked to one or more immutable episodes and a bounded diagnosis. Suitable triggers include:

- the same scoped research-process failure recurs across materially different tasks;
- a successful method sequence transfers across materially different tasks and survives hostile near-misses;
- retrieval repeatedly misses already-registered relevant evidence;
- a surrogate/representation repeatedly fails to preserve a root-critical coordinate;
- local results repeatedly fail at the same gluing/interface boundary;
- chronology/provenance repair consumes repeated research effort;
- a method family is vector-saturated while a stable residual remains;
- the current framework cannot express a recurring failure or success pattern without ontology repair;
- a protected safety/authority invariant is discovered to be declaration-bound rather than content-bound.

One anecdote may justify an issue or experiment. It does not justify promotion.

## 5. Upgrade proposal packet

Before implementation outcomes are inspected, freeze a machine-readable `RAKLUpgradeProposal` containing at least:

```text
proposal_id
parent_method_version
parent_git_sha
change_class                # A implementation / B workflow / C constitution
episode_ids                  # exact source observations
failure_or_lesson_ids
bounded_diagnosis
alternative_diagnoses
proposed_mechanism
method_contracts_affected
protected_paths_affected
predicted_primary_meta_qois
predicted_secondary_meta_qois
material_effect_thresholds
possible_regressions
negative_controls
hostile_near_miss_tests
development_benchmark_id
fresh_assurance_reserve_id
model/tool/resource contract
rollback_plan
proposal_hash
frozen_at
```

If the result was observed before this packet was frozen, it is retrospective calibration only.

## 6. Change classes

RAKL already distinguishes implementation, workflow and constitutional changes. This protocol makes the consequences explicit.

### Class A — implementation

Examples: parser bug, CI portability, hash calculation, serialization, deterministic replay.

Requirements:

- exact regression reproducing the defect;
- full relevant invariant tests;
- no intentional change to protected research semantics;
- artifact/release identity checks;
- negative/supersession history preserved.

A Class-A fix may advance a patch method version. It does not establish a research-method capability gain.

### Class B — workflow / method

Examples: retrieval policy, problem-fibre compilation, routing score, saturation rule, gluing policy, lesson induction, research portfolio allocation.

Requirements:

- preregistered positive meta-QoI target;
- matched parent/challenger development evaluation;
- fresh transfer evaluation;
- hostile near-miss / invalid-transfer controls;
- no blocking invariant regression;
- resource comparability;
- protected evaluator identity;
- fresh blind assurance for a strong evolution claim.

A Class-B challenger is the normal route from `3.n` to `3.(n+1)`.

### Class C — constitution

Examples: changing what may mint authority, weakening proof/review independence requirements, changing the meaning of missing evidence, changing who may promote an incumbent.

Requirements:

- never auto-promote;
- explicit human-visible amendment review;
- backward-compatibility and migration analysis;
- red-team/hostile authority tests;
- fresh protected assurance;
- explicit rollback and supersession semantics.

## 7. Codex and coding-agent startup contract

Codex can be guided by repository `AGENTS.md`. The root `AGENTS.md` should remain a concise map rather than a complete manual.

For any task that changes RAKL framework behavior, the coding agent should:

1. read root `AGENTS.md`;
2. read the current method-state manifest (`RAKL_VERSION.json` once adopted);
3. read this upgrade protocol;
4. inspect `src/rakl/method_specs.py` for the affected method owner/contract;
5. inspect the applicable protected gates (`meta.py`, `promotion.py`, `promotion_attestation.py`, `evolution.py`, `self_bootstrap.py`, and v3 evolution surfaces when relevant);
6. classify the proposed change A/B/C before editing;
7. for Class B/C work, freeze the proposal and evaluator contract before evaluated outcomes;
8. implement on a challenger branch/PR;
9. never self-merge a Class-B/C challenger on the basis of its own narrative or caller-provided authority flags;
10. leave a machine-readable handoff stating exact parent, candidate, tests, benchmark identities, remaining blockers and rollback target.

Direct operator instructions may override repository instructions operationally. Any such override must be recorded explicitly and receives no evolution-evidence credit merely because deployment occurred.

## 8. Challenger lifecycle

Recommended state machine:

```text
OBSERVED_PATHOLOGY
  -> UPGRADE_HYPOTHESIS
  -> PREREGISTERED
  -> CHALLENGER_IMPLEMENTED
  -> DEVELOPMENT_VALIDATED
  -> FRESH_ASSURANCE_PENDING
  -> ASSURED | REJECTED | META_OVERFIT | CANNOT_CHECK
  -> GOVERNANCE_APPROVED (if applicable)
  -> PROMOTED
  -> ACTIVE_PROMOTION_ATTESTED
  -> MONITORED
  -> RETAINED | SUPERSEDED | ROLLED_BACK
```

The archive is a DAG. Rejected and superseded variants remain available as negative history. Previous incumbents remain rollback targets where compatible.

## 9. Evaluation design

Two evaluation modes must be kept separate.

### 9.1 Method-isolation trial

Fork the same frozen RAKL state `S` into parent and challenger variants.

```text
(parent method, S, same model/tools/budget)      -> task outcomes
(challenger method, S, same model/tools/budget) -> task outcomes
```

This estimates the effect of the method change without crediting extra accumulated memory.

### 9.2 Longitudinal learning trial

Use the existing v3 experience benchmark logic.

```text
RESET_BASELINE  # each task starts from S0
LEARNING_ENABLED # development tasks update state S0 -> ... -> Sn
```

After development, every fresh transfer task starts independently from the same frozen `Sn`. Transfer task T1 may not teach T2.

These trials answer different questions and should not be collapsed.

## 10. Task strata

Every Class-B experience/memory/routing upgrade should include at least:

- **repeated-family tasks**: same deep structure, changed surface;
- **fresh transfer tasks**: different domain vocabulary with a registered structural relation;
- **hostile near-miss tasks**: superficially similar but structurally incompatible;
- **historical replay**: old known successes/failures that must remain correctly handled;
- **authority attacks**: forged IDs, stale hashes, changed evaluators, missing evidence, chronology inversion, contaminated assurance;
- **resource stress**: context/token/tool limits and recovery behavior.

Development tasks that motivated the upgrade are not fresh assurance tasks.

## 11. Meta-QoIs

RAKL should report a vector rather than one optimization score.

### Primary learning/research QoIs

- fresh-transfer success delta;
- fresh-transfer registered score delta;
- repeated-failure delta;
- invalid-transfer / false-lesson rate;
- root-coordinate false-progress rate;
- retrieval miss rate inside a bound search universe;
- valid gluing/interface-failure detection rate;
- residual contraction per consequential research cycle.

### Efficiency QoIs

- model input/output tokens;
- preprocessing-model tokens;
- retrieval calls;
- tool calls;
- wall time;
- context compilation size;
- branch/experiment count to a valid discriminator.

### Hard blocking invariants

- theorem/proof/authority escalation from proposal-only evidence;
- loss of raw episode or negative-history lineage;
- evaluator/benchmark tampering;
- candidate/evaluator identity mismatch;
- stale or unbound evidence accepted as current;
- false independent-review credit;
- cross-task leakage in fresh transfer;
- inability to reproduce the candidate from the registered subject.

A gain on a soft metric cannot compensate for a blocking invariant failure.

## 12. Statistical and sequential-evaluation rules

Before execution, freeze:

- primary versus secondary meta-QoIs;
- material-effect thresholds;
- task set/order or sampling rule;
- seeds/model revision/temperature where controllable;
- resource ceilings;
- evaluator protocol;
- multiplicity policy if several primary claims are tested;
- stopping rule and assurance exposure budget.

Use paired analyses whenever parent and challenger can be run on the same tasks. Report effect sizes and uncertainty, not only binary significance. Repeated peeking at an assurance set consumes its evidentiary value. Once exposed to the proposer/optimizer, a packet becomes development evidence and must be replaced for a later strong assurance claim.

## 13. Evaluator protection

The challenger must not be allowed to improve its score by changing the ruler.

Protected objects should include:

- benchmark packet and task hashes;
- evaluator code/protocol hash;
- promotion thresholds;
- subject identity rules;
- evidence-lineage/independence rules;
- Constitution invariants;
- assurance reserve identities;
- post-promotion attestation logic.

If a legitimate upgrade must change an evaluator, that evaluator change is a separate parent change and the candidate must be judged by a frozen external/previous evaluator or a separately governed migration protocol.

## 14. Promotion and deployment

`PromotionGate` should authorize a ref movement only when exact-candidate checks, history preservation, frozen evaluation, protected validator identity and required meta-QoIs pass. `SelfEvolutionAssessor`/`evaluate_bootstrap_trial` provide scoped evolution evidence. Neither should mutate `main` directly.

After a ref moves, `PromotionAttestationPacket` or its successor must prove the deployed state is actually the approved state and passes post-promotion exact-main validation.

The v3 branch archive must not accept a bare `governance_approved=True` as sufficient evidence. Governance approval should be a content-bound attestation referring to exact challenger, exact assurance verdict, exact Constitution epoch and exact approving authority/process.

## 15. Human/operator override

Operational governance must model the possibility that a human intentionally merges/deploys before CI or assurance is complete.

Record:

```text
OPERATOR_OVERRIDE
requested_by
exact subject
requested deviation
known blockers at time of override
operational reason if supplied
post-deployment containment plan
```

Consequences:

- deployment may proceed if repository permissions allow;
- no scoped-evolution or assurance credit is created by the override;
- the variant remains `PROVISIONAL_DEPLOYED` for method-authority purposes;
- post-promotion exact-main validation is mandatory;
- any failure becomes an immutable experience/incident;
- rollback remains available.

This distinction prevents “it is on main” from becoming “it was scientifically validated.”

## 16. Rollback and post-promotion monitoring

A promoted variant should carry:

- exact predecessor/rollback SHA;
- state/schema migration and backward-compatibility notes;
- rollback test;
- monitoring window and meta-QoIs;
- conditions that reopen the promotion decision;
- supersession lineage if a hotfix changes the exact subject.

New failures do not erase the evidence that previously supported a variant. They create new evidence that can narrow, supersede or roll it back.

## 17. Current known implementation gaps motivating RAKL 3.1 candidates

At the inspected base, the following are treated as open engineering gaps, not silently solved properties:

1. v3 `EvolutionArchive.promote_incumbent` accepts a caller-supplied `governance_approved` Boolean rather than a protected content-bound governance attestation.
2. Several v3 authority-bearing evidence surfaces still accept caller-declared IDs/flags that should be resolved against authenticated receipts before promotion.
3. local gluing verification needs certificate-backed semantics rather than a bare verification flag on an authority-bearing path.
4. v3 benchmark state/output hashes identify declared values but need stronger binding to exact task/evaluator/repository/artifact bytes for promotion-grade use.
5. v3 public surfaces need explicit canonical ownership/mapping in `method_specs.py` before they are treated as incumbent method contracts.
6. the repository software package version (`pyproject.toml`) is separate from the informal RAKL method generation and no machine-readable method-version manifest is yet canonical.
7. cross-problem retrieval has already exposed a missing coverage-receipt problem (`RAKL#119`).

These gaps are suitable inputs to challenger proposals. They are not reasons to rewrite history or pretend v3 was never deployed.

## 18. Paper 5 evidence boundary

Paper 5 may describe this protocol as an architecture and preregistered evaluation design immediately. It may describe already observed research-process incidents as qualitative/retrospective case-study evidence. It must not claim that RAKL 3.1 or later is empirically superior until a frozen matched development/fresh-assurance packet supports that statement.

The intended scientific loop is:

```text
observed research episode
-> bounded process diagnosis
-> framework hypothesis
-> preregistered challenger
-> matched development test
-> fresh protected assurance
-> governed promotion
-> post-promotion attestation
-> new longitudinal episodes
```

That loop, rather than self-rewrite alone, is the unit of evidence-governed recursive improvement.
