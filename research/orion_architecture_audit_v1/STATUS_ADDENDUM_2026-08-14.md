# Status addendum — 2026-08-14 (same day, post-freeze)

`AUDIT.md` is a **frozen point-in-time artifact** (2026-08-14, wip-623 @ `74a5fe61`)
and is intentionally not edited. Verdict supersessions are recorded HERE; the
original AUDIT.md text stays as history. Same-context status record, not
independent review; nothing below is a benefit measurement.

## Changes landed on main since the freeze

1. **Transport fail-open repaired at the gate** — PR #643 (`b282dc04`).
   `assess_transfer_v2` now returns CANNOT_CHECK with reason
   `empty_load_bearing_obligation_set` on an empty load-bearing obligation set.
   Receipt: `research/transport_failopen_repair_v1/RECEIPT.md`.
   **Supersedes: solver step 7 GAP verdict (AUDIT.md row 7) and ranked gap 2.**
   The `structure_space.match` call-site workaround is retained as defense in
   depth — it remains, per AUDIT.md, not the fix.

2. **Transport gate re-audited FALSIFIABLE** — this branch,
   `research/transport_gate_reaudit_v1/{REAUDIT.json,README.md}`: no-alarm OK,
   7/7 probes SENSITIVE at both seeds; both fail-open probes flip 32/32; the
   pre-repair gate (`631196b4`) reproduces FAIL_OPEN as a planted-FAIL control.
   With saturation + the 12 sweep gates this makes **14 audited gate surfaces
   across all 11 solver steps**, superseding ranked gap 3's "coverage ~1/11".

3. **Durable episode store merged** — PR #641 (`c1b372be`).
   `src/rakl/episode_store.py` (append-only, tamper-evident hash chain) +
   `tests/test_episode_store.py`; wired into `runtime_resumption.py`.
   **ORION capability 1 FRAGMENTED verdict structurally addressed** (the "no
   durable cross-session episode store" clause no longer holds); benefit still
   unmeasured, so the node remains short of ESTABLISHED.

4. **L0 FCR benefit protocol frozen before any result** — PR #644 (`600cfc92`).
   `research/benefit_L0_fcr_v1/{PROTOCOL.json,EVALUATOR.py,CORPUS_PLAN.md,README.md}`.
   Execution run in flight at time of writing; no result exists yet.

## In flight, unmerged at time of writing

5. **Falsifiability sweep receipts** — PR #645, branch
   `solver/gate-falsifiability-sweep-v1` @ `928495eb` (pending merge).
   `research/solver_gate_falsifiability_sweep_v1/{SWEEP.json,README.md}`:
   12 registered gates FALSIFIABLE, atlas declared-topology blind spot found
   (GLUED trusts caller-declared connectivity/cycle booleans), steps 2 and
   3(reduction fidelity) recorded NO_REGISTERED_GATE.

6. **Atlas topology-trust repair** — PR #649, branch
   `solver/atlas-topology-recompute` @ `c7c807e1` (pending).
   `research/atlas_topology_trust_repair_v1/RECEIPT.md` + `src/rakl/atlas_gluing.py`:
   gluing gate recomputes declared topology; **GLUED -> CANNOT_CHECK on mismatch
   discriminator confirmed** (closes sweep finding 1 once merged).

7. **Peer-session solver-unit completion branch** — reducer admission as the
   step-3 reduction-fidelity gate path (AUDIT.md row 3 / sweep NO_REGISTERED_GATE
   finding / PLAN P1.6). In flight in a peer session; no PR number, branch SHA,
   or receipt visible from this worktree at time of writing — status by pointer
   only, CANNOT_CHECK until it lands.

## What has NOT changed

- **Benefit column: still empty for all 19 nodes.** The FCR protocol (#644) is
  frozen but unexecuted; `research/mechanism_benefit_ledger/ledger.json` still
  records zero demonstrated benefits. **Frontier: still L0.**
- Ranked gap 1 (benefit) and gap 5 (recency/churn) stand. Gap 4 is half-addressed
  (episode store merged; reduction fidelity still open pending item 7).
- The frozen ladder entry `FAIL_OPEN_FOUND` (`research/framework_ladder/ladder.json`
  layers[3]) and all preserved negatives (P4 adaptive REFUTED, Paper VI
  retraction, #519 navigation negative, L6 NON_FALSIFIABLE 4/6) are immutable;
  the repairs above supersede forward state only, never history.
- IMPLEMENTED_UNPROVEN verdicts elsewhere are untouched; no node is promoted by
  this addendum.
