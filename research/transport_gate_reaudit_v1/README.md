# Transport gate re-audit v1 (post-repair, closes the P0.2 sweep skip)

Re-audit of `assess_transfer_v2` (`src/rakl/structural_transport_v2.py`) after the
fail-closed repair (PR #643, on main @ `600cfc92`), using the exact discipline of
`research/solver_gate_falsifiability_sweep_v1/sweep_harness.py` (PR #645 @ `928495eb`):
no-alarm control first, 32 trials/probe, seeds 20260814+20260815, cross-seed agreement
required. Same-context audit, **not independent review**; FALSIFIABLE means only
"this gate can fail", never "its PASS is correct".

Machine-readable results: `REAUDIT.json`. Harness: `reaudit_harness.py`
(`run_battery` copied unchanged from the sweep; deterministic — output reproduces
bit-identically).

## Classification: **FALSIFIABLE** (repaired gate)

No-alarm OK (legitimate 5-load-bearing-obligation witness -> LICENSED). All 7
probes SENSITIVE at both seeds:

| Probe | seed 20260814 | seed 20260815 |
|-------|---------------|---------------|
| empty_obligation_set (fail-open A) | SENSITIVE 32/32 | SENSITIVE 32/32 |
| demote_all_obligations_to_optional (fail-open B) | SENSITIVE 32/32 | SENSITIVE 32/32 |
| corrupt_witness_identity | SENSITIVE 32/32 | SENSITIVE 32/32 |
| force_explicit_violation | SENSITIVE 32/32 | SENSITIVE 32/32 |
| randomize_structural_target_refs | SENSITIVE 31/32 | SENSITIVE 32/32 |
| rewire_role_mapping | SENSITIVE 32/32 | SENSITIVE 32/32 |
| strip_obligation_evidence_ids | SENSITIVE 32/32 | SENSITIVE 32/32 |

## The old fail-open path is dead — probed explicitly

Directed deterministic check (disjoint structures, zero obligations):
pre-repair (`631196b4` = `b282dc04^`) returns **LICENSED with zero reasons**
(the frozen defect, `FAIL_OPEN_FOUND` in `research/framework_ladder/ladder.json`,
intentionally not edited); repaired returns **CANNOT_CHECK** with reason
`empty_load_bearing_obligation_set`. Probe form: both fail-open probes flip the
repaired gate 32/32 at both seeds.

**Validate-the-checker (planted-FAIL world):** the same battery against the
pre-repair module classifies **FAIL_OPEN** — both fail-open probes INSENSITIVE
0/32 while the other 5 probes stay SENSITIVE, i.e. the old gate was
battery-FALSIFIABLE yet still licensed on absence of evidence. FAIL_OPEN is a
distinct class precisely because the plain battery verdict cannot see it; only
the directed absence-of-evidence probes separate the two worlds. The repaired
verdict is trusted only because the probes demonstrably catch the planted defect
(`probes_validated_against_planted_defect: true`).

## Coverage statement

This re-audit completes the sweep that skipped transport as "under repair (P0.1)".
Audited gate surfaces: saturation (AUDIT.md row 5) + 12 sweep gates (PR #645) +
this transport gate = **14 audited gate surfaces across all 11 RAKL_SOLVER steps**.
Step 2 and step-3 reduction fidelity remain NO_REGISTERED_GATE findings (closure:
PLAN P1.6 / peer solver-unit branch), not sweepable surfaces.

## What must NOT be taken from this artifact

- FALSIFIABLE does not certify any LICENSED verdict on real evidence; no benefit
  is measured here and no ladder/authority state changes.
- The frozen `FAIL_OPEN_FOUND` ladder entry and the AUDIT.md step-7 GAP text are
  history; supersession is recorded in the audit STATUS_ADDENDUM, not by edits.
