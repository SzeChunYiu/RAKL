# Solver gate-falsifiability sweep v1 (PLAN P0.2)

Black-box perturbation battery (`src/rakl/gate_falsifiability.py`, 32 trials/probe,
seeds 20260814+20260815, classification must agree across seeds) swept across the
RAKL_SOLVER step gates. Skipped: transport (under repair, P0.1) and saturation
(already audited FALSIFIABLE). Same-context audit, **not independent review**;
FALSIFIABLE means only "this gate can fail", never "its PASS is correct".

Machine-readable results: `SWEEP.json`. Harness: `sweep_harness.py`.
Finding reproductions (each verified twice): `reproduce_insensitive_findings.py`.

## Per-step classification

| Step | Gate | Classification | No-alarm | Sens/Insens |
|------|------|----------------|----------|-------------|
| 1 contract | `hard_gates.evaluate_hard_gates` | FALSIFIABLE | OK | 5/1 |
| 1 contract | `framework_candidate_freeze.gate_candidate_materialization_framework_subject` | FALSIFIABLE | OK | 6/0 |
| 2 decomposition | — | **NO_REGISTERED_GATE** | n/a | n/a |
| 3 structuralization | `structure_space.match` (admission only) | FALSIFIABLE | OK | 5/0 |
| 3 structuralization | reduction fidelity | **NO_REGISTERED_GATE** | n/a | n/a |
| 4 knowledge space | `atlas_gluing.evaluate_atlas_gluing` | FALSIFIABLE* | OK | 6/1 |
| 4 knowledge space | `typed_lattice.construct_paths` | FALSIFIABLE | OK | 4/0 |
| 5 retrieval | `semantic_shortcut.audit_obstruction_transformation_review` | FALSIFIABLE | OK | 6/0 |
| 6 composition | `bridge_composition.evaluate_bridge_path` | FALSIFIABLE | OK | 7/0 |
| 6 composition | `solution_assembly.validate_solution_assembly` | FALSIFIABLE | OK | 6/0 |
| 7 navigation | `support_solver.solve` | FALSIFIABLE | OK | 5/0 |
| 8 verification-meta | `evidence_binding_certificate.evaluate_evidence_binding_for_promotion` | FALSIFIABLE | OK | 6/0 |
| 9 residual | `epistemic_trajectory.evaluate_epistemic_trajectory` | FALSIFIABLE | OK | 7/0 |
| 9 residual | `diagnosis_state_machine.resolve_discriminator` (exception-channel adapter) | FALSIFIABLE | OK | 5/0 |

Every no-alarm control (intact correct evidence must PASS) was asserted before
probing; all 12 registered gates passed it and all classifications were stable
across both seeds.

## Findings beyond the headline classifications

1. **Atlas declared-topology trust (real blind spot, reproduced twice).**
   `evaluate_atlas_gluing` validates each declared transition but never recomputes
   cover connectivity / cycle structure from the transition set: `cover_connected`,
   `cover_has_cycles`, `cycle_basis_complete` and cycle-witness consistency are
   caller-declared booleans (`atlas_gluing.py:463-528`). A single-transition atlas
   with intact declarations still returns GLUED. Follow-up work; no gate modified.
2. **hard_gates checks evidence presence, not gate↔evidence binding (scope note,
   reproduced twice).** Swapping evidence ids between gates keeps PASS; the
   `shuffle_gate_ids` INSENSITIVE result is a structural no-op on homogeneous
   all-PASS rows, not non-falsifiability. Binding is owned by
   `evidence_binding_certificate`.
3. **Framework-subject gate inactive mode (directed check).** With
   `required=False` and no binding, the gate licenses unconditionally — by-design
   free-form mode. Live call site (`math_research_runtime.py:314-321`) activates
   the gate whenever a binding exists or the require flag is set; residual risk is
   confined to callers leaving both unset.
4. **Probe artifact caught and preserved (validate-the-checker).** v1 navigation
   probe `rewire_edge_targets` was INSENSITIVE because every permutation of the
   fixture's target multiset keeps the goal reachable (exhaustively verified);
   corrected to `retarget_edges_away_from_goal` (SENSITIVE 32/32). The v1 negative
   is preserved in the probe diagnosis, not rewritten.
5. **NO_REGISTERED_GATE is itself the finding for decomposition** (gating inline
   in `recursive_solver.solve_recursive`: saturation check, match delegation, LIFT
   precondition) **and for step-3 reduction fidelity** (closure item PLAN P1.6).
   No sweep was forced onto a non-gate.

## What must NOT be taken from this artifact

- No verdict upgrades any claim's authority; nothing here is a benefit measurement.
- FALSIFIABLE does not certify any gate's PASS on real evidence.
- The atlas and hard_gates findings are follow-up work items, not silent patches;
  no gate implementation was modified and `ladder.json` is untouched.
