# Completion plan — ORION / RAKL_SOLVER

Derived from AUDIT.md, 2026-08-14. Ordering rule: the ladder's non-compensatory policy
(defective gates repaired before benefit experiments — a benefit measured through a
fail-open or non-falsifiable gate is uninterpretable) plus the operator directive:
**RAKL_SOLVER unit first**. Refactor (Phase R) is engineering and runs in parallel;
it is not gated on the science and mints no authority.

## Phase 0 — Gate integrity (blocks everything; do first)

- **P0.1** Repair `assess_transfer_v2` fail-open: empty load-bearing obligation set →
  fail-closed (mirror `structure_space.match`'s rule at the gate itself), plus hostile
  tests asserting the LICENSED-with-zero-reasons path is dead. Closes the solver's only
  GAP verdict (step 7). Smallest scoped change; freeze evaluator behavior before/after.
- **P0.2** Sweep `gate_falsifiability` battery across the 10 unaudited solver-step gates
  (contract, decomposition, structuralization, knowledge_space, retrieval, transport
  post-P0.1, composition, navigation, verification-meta, residual). Record per-gate
  FALSIFIABLE / FAIL_OPEN / NON_FALSIFIABLE / NOT_APPLICABLE with receipts. Assert the
  no-alarm control first (validate-the-checker discipline).
- **P0.3** Commit `derivation.py` + `test_derivation.py` (AND-composition; currently
  untracked and at loss risk). Own PR, no bundling.
- **P0.4** Execute the registered P3 successor: independent-oracle structured-action
  conformance with demonstrably failable gates (repairs L6 NON_FALSIFIABLE 4/6 and the
  decorative `shuffle_lesson_verified` input). Prerequisite for any ORION-layer benefit claim.

## Phase 1 — RAKL_SOLVER benefit obligations (ladder order; the priority unit)

Each is a named observable frozen in ladder.json; run in order, one at a time,
clean baseline + shuffle-equal-n null, all costs charged:

- **P1.1** L0 FCR: context-aligned projection vs naive text comparison (false-contradiction rate).
- **P1.2** L1/L2: unsupported-composition rate (typed vs untyped); obstruction-retention vs
  pairwise-only wrong-gluings (prop:obstruction-blind, proved → now measure).
- **P1.3** L3 ALR: authority boundary vs ungoverned arm (requires P0.1 first).
- **P1.4** L4 arm C — **the load-bearing open question**: navigate distilled support
  structure vs read raw sources at matched total budget. This is the claim the whole
  "solver" framing rests on.
- **P1.5** L5 stop-rule IoU: saturation stopping vs arbitrary stop at matched budget.
- **P1.6** Step-3 fidelity gate: define + test a reduction-fidelity check for
  ReducedStructure (known-answer + hostile corruptions), closing the solver's second
  structural hole. (New mechanism, so it enters via mechanism-invention workflow.)

Exit condition per experiment: PROMOTE / NEGATIVE / CONDITIONAL are all recordable;
a conditional or negative gets one attributed revival pass (global-recovery doctrine)
before the residual is filed.

## Phase 2 — ORION substance (after P0; interleave with Phase 1 as capacity allows)

- **P2.1** Durable episode store: extend P7 persistence from controller-state to
  TaskEpisode/ExperienceLedger with content-hash chain + query surface; migrate the 146
  hand-curated SELF_RAKL receipts in as the seed corpus. (Closes ORION cap 1 FRAGMENTED.)
- **P2.2** MECH-METHOD-EVOLUTION fresh-task lift vs static-method parent — the programme's
  single largest benefit gap; requires P0.4 gates + P2.1 episodes; currently
  BLOCKED_ON_CAPABILITY_QUALIFICATION, so the qualification study is the first sub-step.
- **P2.3** Operator-acquisition receipt integrity: locate or regenerate the
  MEC-DERIVATION_QUANTIFIED_REFUSAL transfer receipt under its real ID; audit L7 gates
  with the battery.
- **P2.4** Wire the ORION operating loop: HOURLY_SELF_RND from doc to scheduled runtime
  (external scheduler acceptable; in-repo entrypoint + receipts mandatory).

## Phase R — Codebase refactor to the diagram (parallel track)

- **R1** Full module→package assignment (in flight; assignment agent output →
  `module_assignment.json`).
- **R2** Create `rakl/solver/*` (11 step packages), `rakl/orion/*` (8 capability
  packages), plus `rakl/core`, `rakl/governance`, `rakl/runtime`, `rakl/studies`.
  Physical `git mv` in batches with compatibility shims at old paths (re-export +
  `__main__` forwarding); path-string pins (unified_solver_registry, method_specs,
  promotion, evaluator pins, schemas) updated in the same commit per batch.
- **R3** Per batch: push branch → all 37 GitHub workflows green → merge. No local
  full-suite runs. Receipts and negative history are never rewritten — old paths in
  frozen receipts stay valid via shims.
- **R4** Update `skills/rakl-core/manifest.yaml` invention_resources + docs/MAP.md to
  the new layout in the final batch; regenerate the code-review graph.

## Standing constraints

- Every experiment through the RSHEA pipeline (telemetry→receipts→epoch→gates→shadow
  decision→governed proposal→observability→resumable state); nothing self-promotes.
- Negatives and refutations are preserved verbatim; no post-result threshold rescue.
- Same-session critique is not independent review; strict assurance needs isolated recheck.
