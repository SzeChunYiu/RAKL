# Open residuals and next-session queue

This file is the compact queue after the semantic merge. “Open” does not mean the packet is incomplete; it means the obligation cannot be honestly converted into support by interface code alone.

## A. Exact-base integration first

1. Re-fetch `main` and compare with `3c24a9f78722ee5fa47ee3527e7e0e774aff91c6`.
2. If exact, run `tools/apply_unified_handoff.py .`; the reviewed current-main edits are guarded by exact Git blob SHA and exact replacement preimages.
3. Run `tests/test_current_main_deep_guards.py` plus all native TCSQ/authority/structural-transfer suites.
4. Run the native full suite and existing hardening workflow.
5. Reconcile the stale/contradictory open-gap register item against the workflow and update the authoritative register only with evidence.

If `main` moved, do **not** force-apply the three current-main edits. Port each obligation against the new code, add equivalent regressions, then run the additive installer with the explicit moved-head reconciliation flags.

## B. Wiring residuals

These are implementation tasks whose types/tests exist here but which must be connected to the live call graph:

- use `assured_materialize_validated_quotient` for production/authority-sensitive TCSQ consumption;
- use `assess_transfer_for_use` where a downstream action depends on a `StructuralWitness`;
- dual-write V3 canonical commitments before any fingerprint migration;
- attach canonical training assurance to learner experiments;
- emit immutable diagnosis-transition receipts;
- bind the exact `StructuralIdentityBundle` through external/training/inference stages;
- create a `UnifiedMechanicsManifest` for every integrated experiment epoch;
- keep model-promotion eligibility and scientific-authority promotion as separate transitions.

## C. Scientific cuts, in dependency order

### Cut 1 — SQ-3 total cost

Does TCSQ beat strong unquotiented/compression/abstraction controls **after** construction, validation, reconstruction and original verification are charged? If not, kill the practical-cost claim while retaining the representation result.

### Cut 2 — neural structural residual

Does explicit TCSQ + directional witness semantics beat the strongest matched conditional-metric and asymmetric relational/causal parents on fresh domains, QoI flips and hostile boundary near-misses? If not, narrow the neural novelty claim.

### Cut 3 — corrected learner signal

Run Phase-1 v2. If no checkpoint-dependent structural residual survives, do not proceed to an adaptive curriculum efficacy claim.

### Cut 4 — exact shared identity reuse

Test exact shared content identity against semantically equivalent but independently reconstructed structure. This determines whether exact reuse is mechanistically useful or only provenance discipline.

### Cut 5 — Verified Transformation Geometry

Construct the bounded verifier-defined formal universe first. Then test **local-only** / bounded-local navigation on held-out theorem families. The primary failure terminal is:

```text
NO_USEFUL_LOCAL_GEOMETRY_IN_REGISTERED_SCOPE
```

Do not add natural dynamics if this cut fails.

### Cut 6 — dynamics / portals

Only after local geometry survives: test multi-chart portals and flow/diffusion/Physarum/path-integral style policies against best-first/A*/MCTS/equality-saturation/learned proof-progress controls at matched total cost.

### Cut 7 — cognitive compilation

Compare typed structural diagnosis → bounded update → disjoint fresh assurance against generic reflection/distillation, failure-example fine-tuning, textual skill compilation, random matched update and no update.

### Cut 8 — end-to-end RAKL value

Compare the integrated system to substantially simpler research/agent baselines at matched model, evidence cutoff, compute, wall-time and human-review budget. Complexity is justified only by a measurable quality/safety/efficiency residual.

## D. External assurance residuals

Same-context expert-role analysis is not independent validation. Still open:

- independent mathematical review of abstraction/reachability/basin claims;
- independent security review of canonicalization, trust-root migration and authority transitions;
- cross-model and cross-seed empirical replication;
- domain-expert review where scientific claims leave known worlds;
- repository ruleset / protected-release governance if the project wants CI and trust-manifest gates to be enforced rather than conventional.

## E. Correct terminal language

Even after every software item above is green, the honest terminal is:

```text
INTEGRATION_CONTRACTS_HARDENED = true
KNOWN_CODE_GAPS_AT_FROZEN_CUTOFF = 0  # only after full-repo hostile audit confirms
OPEN_SCIENTIFIC_COORDINATES = nonempty
GLOBAL_BIBLIOGRAPHIC_COMPLETENESS = false
GLOBAL_NOVELTY = false
SCIENTIFIC_AUTHORITY_FROM_THIS_PACKET = false
```
