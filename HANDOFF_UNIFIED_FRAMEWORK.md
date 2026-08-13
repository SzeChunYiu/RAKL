# Orion unified problem-solving framework — AI-session handoff

This file is a transfer brief for continuing work on branch `orion/unified-problem-solving-v1`.

## Exact provenance

- Repository: `SzeChunYiu/RAKL`
- Branch: `orion/unified-problem-solving-v1`
- Frozen pre-handoff implementation head: `641923f44613f0c01da06d00b3c207846cf86bec`
- Base before this programme: `8beb877d0f3ef3504b5ca2fdd02fb99c75ed4c38`
- The packaging workflow writes the actual packaged HEAD to `HANDOFF_SUBJECT.txt` and the patch base/head to `HANDOFF_PATCH_SUBJECT.txt`.

## What was implemented

Seven proposal-only unified problem-solving mechanics were added without creating a second canonical scientific state:

1. `src/rakl/operational_map.py` — operational map / known-vs-unknown coverage semantics. Unknown map content cannot be promoted to impossibility.
2. `src/rakl/path_equivalence.py` — path/trajectory equivalence and concurrent-route quotient semantics.
3. `src/rakl/path_cost.py` — noncompensatory path-cost/admissibility algebra: invalid or unlicensed paths cannot buy admissibility by being cheap.
4. `src/rakl/fieldability.py` — field/reuse economics with specification/operator-basis/map/chart identity binding and staleness checks.
5. `src/rakl/mechanic_diagnosis.py` — typed mechanic differential diagnosis; ambiguity is preserved and may request discriminators instead of forcing a diagnosis.
6. `src/rakl/solver_compilation.py` — solver compilation / routing with preservation receipts; routing does not validate itself.
7. `src/rakl/solution_assembly.py` — trajectory-to-certificate assembly with DAG/hash/dependency/verifier checks. Assembly grants zero scientific authority by itself.

Canonical ownership and claim boundaries are executable in `src/rakl/unified_solver_registry.py` and audited by `scripts/audit_unified_framework.py`. The audit deliberately reports `GLOBAL_COMPLETENESS_CLAIMED=false` and `SCIENTIFIC_AUTHORITY_GRANTED=false`.

## Verification/evidence added

- `tests/test_unified_solver_framework.py`
- `tests/test_unified_solver_registry.py`
- `research/unified_problem_solving_v1/VERIFICATION_LEDGER.json`
- `docs/ORION_UNIFIED_FRAMEWORK_VERIFICATION_LEDGER.md`
- `research/unified_problem_solving_v1/run_known_world_stress.py`
- `.github/workflows/unified-framework-hardening.yml`

The dedicated unified tests pass (18 tests in the current hardening job). The registry audit passes. The deterministic known-world stress run completes and deliberately emits `AUTHORITY_GRANTED=false` and `METHOD_PROMOTION_GRANTED=false`; it is development evidence, not a scientific promotion receipt.

## Publication visualisations

Reproducible plot source:

- `paper/generate_unified_solver_figures.py`
- integrated into `paper/generate_demo_figures.py`

Generated figure families:

- `unified_solver_architecture`
- `unified_field_amortization`
- `unified_local_vs_closed_loop`
- `unified_verification_pareto`
- `unified_path_quotient`

The handoff packaging workflow regenerates these and includes PDF/SVG/PNG outputs plus `unified_solver_known_world.source.json`.

## Paper integration

- Paper I: solver epistemic-noninterference ownership note.
- Paper II: chart/portal and structural-preservation ownership note.
- Paper III: unified solver learning/method-evolution ownership note.
- Paper IV: generator-defect correction note and build-time repair script; v1 Phase-1 result must not be interpreted as mechanism evidence.
- Paper V: new `sections/11_verified_transformation_geometry.tex` formalises the verified-transformation-geometry hypothesis, noninterference contract and held-out falsifier; includes new figures.
- Paper VI: new `sections/10c_unified_problem_solving.tex` systems synthesis; includes new figures.
- Series-level integration: `publication/UNIFIED_PROBLEM_SOLVING_CROSS_PAPER_INTEGRATION.md` and updated `publication/PUBLICATION_SERIES_V2.md`.

## Current assurance status

At the latest checked hardening run before this handoff:

- unified framework tests: PASS
- canonical ownership / claim-boundary audit: PASS
- deterministic known-world stress: PASS (no authority or promotion granted)
- all five new figure families: generated successfully
- Paper IV generator-defect repair gate: PASS
- Paper IV direct compile: PASS
- Paper V direct compile: PASS
- Paper VI direct compile in the bespoke hardening workflow: FAIL

The Paper VI failure is currently an integration/build-path issue, not evidence that a new solver mechanic failed. The log reaches `sections/08_known_answer_trace.tex` and then fails because `fig5_demo_growth.tex` references `fig5_demo_growth.pdf`, which is absent in that direct compile path. The established publication pipeline normally stages/generates paper assets; the bespoke hardening workflow currently bypasses that staging. Fix the hardening workflow to use the canonical Paper VI staging/build path (preferred) or explicitly generate/stage the required legacy figure before compiling. Do **not** weaken the render/preflight gates.

Also inspect typography once Paper VI reaches the preflight stage. Paper V currently logs an overfull box around the new VTG section (about 6.5pt), and Paper IV has existing table overfull warnings. The dedicated hardening workflow should remain fail-closed on publication typography rather than suppressing warnings.

## Continuation order for the next AI session

1. Fetch this branch and read this handoff plus `docs/ORION_UNIFIED_FRAMEWORK_VERIFICATION_LEDGER.md`.
2. Bind every claim to the packaged HEAD in `HANDOFF_SUBJECT.txt`.
3. Fix the bespoke Paper VI hardening build by reusing the canonical publication staging/generation path; do not duplicate a second Paper VI build system.
4. Run the full ordinary `test`, `publication-pdfs`, `paper5-verified-discovery-release`, and `unified-framework-hardening` workflows on one exact head.
5. Fix any overfull/undefined-reference/render issue rather than loosening gates.
6. Visually inspect rendered pages containing the new figures and new Paper V/VI sections.
7. Only after all exact-head gates are green, update the verification ledger with exact workflow/run identities and open/merge the PR.
8. Preserve the evidence boundary: passing software/known-world tests demonstrates executable invariants and noninterference on tested cases; it does not prove global logical completeness or empirical scientific effectiveness.

## Important scientific claim boundary

Do not state “the framework is proven to have no logic flaw or gap.” The defensible statement is narrower: load-bearing invariants have executable representations, targeted/adversarial tests and deterministic known-world checks; canonical CI and paper rendering provide exact-subject regression evidence; remaining unproved or empirically unvalidated coordinates must remain explicit `CANNOT_PROVE`/open evidence gates.
