# Open gaps register — recursive hardening to zero

Single authoritative TODO consolidating every unresolved finding from the hostile
math audit (15 findings), hostile engineering audit (18 findings), and closure
ledger. Fixed items move to the DONE section with their regression test. Goal state:
this register is empty except DONE, and a fresh hostile audit of the fixed surfaces
finds nothing new (two consecutive clean audit rounds = hardened).

## P0 — soundness (wrong results possible)
(empty — all P0 items moved to DONE)

## P1 — ill-posed / adopter-breaking
(empty — all P1 items moved to DONE)

## P2 — overclaim / CI drift
(empty — all P2 items moved to DONE: O1 restated as Floyd variant+invariant [was false
as stated, 3-state counterexample]; O2 state-indexed licensing + premise-discharge +
hazard-consistent break-even; CI experiment-reproducibility byte-diff gates +
figure-staleness cmp gates + matplotlib pin + quickstart smoke — commit e8fcff90)
- [ ] ENG CI: workflow paths predate self-contained paper folders — repoint.

## P3 — open scientific coordinates (gated, not code fixes)
- [ ] Paper IV v2 A100 ladder (jobs 3489133–36) → harvest, honest terminals, finalize §phase1.
- [ ] Field CONSTRUCTION on non-metric domains (preregistered, Paper V lane).
- [ ] Cross-model comparator replication; six-family sign test (Paper II).
- [ ] Independent human review (#216); gate #462 for any positive Paper IV claim.

## DONE (with regression tests)
- [x] MATH U1–U6 (all six UNSOUND findings): state-indexed independence witnesses +
      fail-closed trace quotient (U1), scope-uniform route composition (U2),
      operator-coordinate + polarity-consistency constraint (U3), coverage certificate
      bound to canonical edge-set hash + dropped on mutation (U4), REFUTES-conflict
      REJECT + REDUCES_TO premise direction (U5), renewal-reward break-even with
      hazard (U6) → tests/test_audit_regressions.py::test_u1…test_u6.
- [x] ENG: NaN/non-finite costs fail closed in PathCostVector, dominance, and
      lexicographic selection; duplicate path_ids rejected →
      test_audit_regressions.py::test_i1_nan_and_nonfinite_costs_fail_closed,
      ::test_i2_duplicate_path_id_fails_closed.
- [x] ENG/R3: path_quotient_experiment.py updated to the state-indexed (U1-hardened)
      path_equivalence API: commutation certified by execution per (pair, reachable
      prefix context); context-bound TransitionIndependenceWitness registered per
      check; global_independence_certified=True asserted only after the exhaustive
      executed sweep; certification cost charged into net saving.
      results/path_quotient_savings.{json,pdf,png} regenerated at HEAD
      (PYTHONHASHSEED=0, seed 461): EQUIVALENCE_SPOT_FAILURES=0,
      CLASS_OUTCOME_MISMATCHES=0, DEMOTED_PAIRS=0 over 3,200 instances.
      Artifacts regenerated in working tree, commit pending; CI wiring of the
      experiment remains tracked under the P2 CI items.
- [x] MATH I1–I3: finiteness axiom (I1), path_id-as-key (I2), UNKNOWN excluded from
      identified-fault verdicts (I3) → test_audit_regressions.py::test_i1/test_i2/test_i3.
- [x] MATH I4: declared effect-conflict relation (EFFECT_CONFLICTS; RELAX×TIGHTEN
      fails closed), CompositePreservationReceipt + compose_preservation_receipts
      (interface-hash-matched, all-passing components only; additive
      target_problem_hash field), CompositeNavigationQuotientValidation +
      compose_navigation_quotient_validations (EXACT∘EXACT=EXACT, sound-overapprox
      degrades, anything weaker CANNOT_CHECK; subject-hash chained) →
      test_audit_regressions.py::test_i4_effect_conflicts_and_composite_receipts.
- [x] MATH I5: CertificationWitness (verifier id + subject hash + class) bound to
      geometry_certification_subject_hash; supports_exact_cost_claim /
      is_theorem_certified_heuristic_class read the WITNESSED class and fail closed
      to UNCERTIFIED without a matching witness →
      test_audit_regressions.py::test_i5_certification_class_requires_bound_witness.
- [x] MATH I6: TransferAssessment carries required/preserved relation+invariant SETS
      (additive); structurally_complete is set inclusion and fails closed without
      sets (counts demoted to cardinality_complete, reporting only);
      ChartTransitionWitness + compose_chart_transitions (partial injections) +
      AtlasCocycleCheck (triple-overlap phi_ik = phi_jk∘phi_ij, fail-closed) →
      test_audit_regressions.py::test_i6_completeness_is_set_inclusion_and_atlas_needs_cocycle.
- [x] ENG/A5: phase1_v2.py git rev-parse wrapped in try/except → git_sha "UNKNOWN"
      on non-git deployments (git-archive zip, Docker COPY, SLURM scratch). No unit
      test (instrument test coverage is the open C3 item).
- [x] ENG/P1: operational_map add_edge O(n)-per-call quadratic wall removed via an
      incremental per-chain validation index (duplicate-id + U3-polarity checks in
      O(1) per edge; branch divergence detected by length and rebuilt). 8k-edge
      chain: 2.36 s → 0.10 s; validation semantics and content_hash unchanged →
      test_audit_regressions.py::test_eng_p1_add_edge_incremental_index_keeps_validation_semantics.
- [x] Generator seeding PYTHONHASHSEED-salted → sha256 (verified cross-process).
- [x] Train/probe prompt-identical leakage → prompt-level disjoint filter.
- [x] orion alias double-load / enum identity → meta-path finder (identity verified).
- [x] Trace-monoid equivalence+congruence laws → path_congruence.py + 9 property tests.
- [x] Budget-in-metric triangle violation → cost_geometry.py + counterexample test.
- [x] v1 Phase-1 instrument defects (degenerate generator; masked answer token) →
      v2 instrument + retraction in Paper IV.
