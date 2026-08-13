# RAKL unified deep-hardening handoff — 2026-08-13

## Purpose

This is **one semantic integration packet** for the next AI development session. It consolidates four inputs:

1. the large recursive hardening overlay;
2. the smaller recursive-closure residual packet;
3. the RAKL × LLM Structural Bridge handoff;
4. the Verified Transformation Geometry / Verified Solution Universe research lane.

It is deliberately **not** a concatenation of old files. Current RAKL `main` moved after several source handoffs were prepared, and current `main` already contains fixes that would be regressed by blind application of older proposals.

## Frozen integration subject

```text
repository: SzeChunYiu/RAKL
base branch: main
base commit: 3c24a9f78722ee5fa47ee3527e7e0e774aff91c6
observed commit time: 2026-08-13T12:19:16Z
integration style: additive / fail-closed / semantic port
```

The receiving session **must re-fetch `main` before editing**. If `HEAD` is not the exact commit above, do not force-apply. Reconcile this packet by obligation against the new head.

## What is actually completed in this packet

This packet closes or strengthens implementation contracts that can be made honestly without inventing new scientific evidence:

- deterministic typed canonical commitments with context-independent Decimal encoding, exact binary64 bit preservation, Unicode policy, cycle/unsupported-type rejection and domain separation;
- an additive V3 state commitment rather than silently changing legacy state fingerprints;
- a canonical assurance sidecar for checkpoint-bound training projections;
- use-site enforcement of `StructuralWitness.non_preserved_properties`;
- a resolved-validation gate for TCSQ so a caller-created `VALID_*` report is not self-authenticating at production solver use;
- composable approximation-error budgets;
- typed VTG contracts covering operational subject identity, edge assurance, reachability quantifiers, exact/sound/empirical abstractions, learned-geometry provenance, staleness, total cost, certified navigation basins, portals, trajectory/certificate separation, root amalgamation, and `pi_solve` non-authority;
- exact structural identity reuse receipts across external reasoning, training and inference;
- a neural contract that keeps quotient geometry separate from asymmetric witness transport and records the symmetric-classifier ceiling on reversed directional pairs;
- a strict diagnosis refinement state machine rather than one-shot relabelling;
- authority-assurance sidecars and a default rule that derived views reference source authority as provenance rather than inheriting it automatically;
- an epistemically governed cognitive-compilation state machine in which training cannot move `pi_epi` and fresh assurance is separated from proposal/training;
- a single `UnifiedMechanicsManifest` / readiness gate binding cross-surface identities and resolved receipts for one integration epoch;
- exact-base repairs for duplicate structural identities, non-finite TCSQ tolerances/conditional forbidden losses, and malformed scientific-evidence lineage;
- hardened canonical/wire logic in the inherited hardening overlay.

Local contract verification for this packet is recorded under `evidence/`.

## What is *not* completed by code

The following are scientific coordinates and remain explicitly gated:

- TCSQ SQ-3 net solver/cost advantage;
- a RAKL-specific Neural TCSQ residual over the strongest matched conditional-metric parents;
- a directional-witness neural residual over strong asymmetric relational/causal parents;
- the full corrected Phase-1 v2 learner-signal experiment;
- adaptive structural gradient allocation efficacy;
- exact fresh train → inference identity-reuse benefit;
- useful local Verified Transformation Geometry on held-out Lean theorem families;
- benefit from flow/diffusion/Physarum/path-integral dynamics over strong search controls;
- epistemically governed cognitive compilation as a useful weight-learning mechanism;
- independent mathematical/security/scientific review;
- any global novelty/priority claim.

These are converted into executable preregistrations/falsifiers rather than filled with implementation assertions.

## Read order for the next AI

1. `01_BASE_SUBJECT_AND_CLAIM_BOUNDARY.md`
2. `02_EXPERT_PANEL_SYNTHESIS.md`
3. `03_SEMANTIC_MERGE_MATRIX.md`
4. `04_DEEP_GAP_AUDIT.md`
5. `05_UNIFIED_ARCHITECTURE.md`
6. `06_IMPLEMENTATION_AND_EXPERIMENT_LADDER.md`
7. `07_NOVELTY_AND_PRIOR_ART_BOUNDARY.md`
8. `08_SECURITY_SUPPLY_CHAIN_MIGRATION.md`
9. `research/VTG_PHASE0_1_PREREGISTRATION.md`
10. `research/NEURAL_STRUCTURAL_BRIDGE_PREREGISTRATION.md`
11. `research/COGNITIVE_COMPILATION_PREREGISTRATION.md`
12. `09_AI_SESSION_PROMPT.md`
13. `10_DEFINITION_OF_DONE.md`
14. `11_CURRENT_MAIN_RECONCILIATION_FINDINGS.md`
15. `12_OPEN_RESIDUALS_AND_NEXT_SESSION_QUEUE.md`

Then inspect `repo_patch/` and `hardening_overlay/`.

## Applying the packet

Preferred workflow (on the frozen exact base, the installer first performs blob-SHA-bound deterministic reviewed edits to current `structural_types.py`, `semantic_quotient.py`, and `v3_scientific_authority.py`, then adds the new modules):

```bash
git clone <RAKL>
cd RAKL
git checkout 3c24a9f78722ee5fa47ee3527e7e0e774aff91c6
python /path/to/handoff/tools/apply_unified_handoff.py .
pytest -q tests/hardening
pytest -q \
  tests/test_canonical_commitment.py \
  tests/test_v3_and_training_commitment.py \
  tests/test_approximation_budget.py \
  tests/test_verified_transformation_geometry.py \
  tests/test_diagnosis_state_machine.py \
  tests/test_identity_neural_compilation_authority.py \
  tests/test_structural_transfer_use.py \
  tests/test_semantic_quotient_assurance.py \
  tests/test_unified_integration_contract.py \
  tests/test_current_main_deep_guards.py
```

Then run the repository's native full suite, current hardening/audit workflows, paper builds and deterministic artifact checks. A locally green additive packet is **not** a substitute for repository-level validation.

## Non-negotiable invariants

```text
proposal != verification != promotion
search utility != scientific authority
training utility != scientific authority
geometry descent != proof progress
reachability under current operators != mathematical possibility
abstract route != concrete verified route
search trajectory != proof certificate
same-context expert roles != independent review
bounded non-finding != global novelty
```

