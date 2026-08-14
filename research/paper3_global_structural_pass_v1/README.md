# First global-loop structural pass v1

A **first structural pass over 9 receipted mutation trajectories** — NOT a validated
generational improvement. The global loop's construct-new-generation and
cross-family-validation stages remain prospective and unexecuted.

Runner: `../../experiments/orion_closure/run_p3_global_structural_pass.py`, reducing
each trajectory mechanically into `src/rakl/structure_space.py` role space
(`defect_stage`, `superstage`, `lever_type`, `instrument_state`, `sign`), with every
trajectory's receipt files read at run time (a receipt not in the tree is recorded
`CANNOT_CHECK`, and exactly one is: the STALE confirmatory receipt lives on PR #673).

Space: 34 distinct roles over 9 trajectories, growth per round `[5,3,3,4,4,5,5,2,3]`,
saturation **OPEN** (the space is nowhere near saturated — more trajectories still add
structure).

## Patterns surfaced (each cites its trajectories; scope: observed in this programme, not a universal law)

- **P1 Evaluation-stage dominance.** Every trajectory whose defect stage is confirmed
  lives on the EVALUATION side — confirmatory gates (T1, T2), applicability licensing
  (T3), measurement interface (T4), instrument power (T5, T8, T9). Zero confirmed
  defects on the proposal-generation side. One import (T6) and one unconfirmed stage
  (T7) are counted separately.
- **P2 Healthy-signal inversion.** The defective instruments looked healthy or perfect
  by their own conventional statistics — registered p=0.03125 (T1), 1.0 accuracy (T4),
  CIs ≈0.0016 wide (T5) — while structurally unable to measure their target. Health
  statistics and measurement capacity are independent axes.
- **P3 Two lever families.** The successful levers are all refusal-shaped (fail-closed
  repair T3, typed refusal T6, ceiling admissibility T5/T8, governed acceptance T9) or
  independence-shaped (black-box audit T1, independent oracle + post-freeze gold T2,
  interpretation narrowing T4): make the acceptance signal able to say no or nothing,
  or make it independent of what it judges.

Receipt: `GLOBAL_STRUCTURAL_PASS.json`. Grants no scientific or promotion authority.
