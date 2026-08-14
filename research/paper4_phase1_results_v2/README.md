# Paper IV Phase-1 v2 (#461) — exposure-sweep results (corrected instrument)

Real LUNARC A100 runs (**jobs 3489133–3489136**) of the re-frozen Phase-0/1 exposure-ladder
instrument. This is the **v2 corrected generator**: varied instances per family, length-matched
valid/invalid, disjoint train/probe instances (rule generalization, not memorization), and a
**learnability positive-control gate** (`floor=0.65` — a model must clear the base task before any
"no residual" verdict is claimable).

Every run is bound to protocol subject hash `fce2bb17…`, `grants_scientific_authority=false`,
`scientific_claim_status=NO_EMPIRICAL_RESULT`. Terminals are read straight from the data.
Producer git_sha `a72ee8aade`.

| Model | sequence_composition | balance_conservation | state_reachability |
|---|---|---|---|
| Qwen2.5-0.5B | REPETITION_REMAINS_VALUABLE | MODEL_FLOOR | REPETITION_REMAINS_VALUABLE |
| Qwen2.5-1.5B | NO_STATE_DEPENDENT_RESIDUAL | MODEL_FLOOR | REPETITION_REMAINS_VALUABLE |
| Qwen2.5-3B   | NO_STATE_DEPENDENT_RESIDUAL | MODEL_FLOOR | REPETITION_REMAINS_VALUABLE |
| Qwen2.5-7B   | NO_STATE_DEPENDENT_RESIDUAL | REPETITION_REMAINS_VALUABLE | **MECHANISM_SIGNAL_PRESENT** |

## Honest synthesis
Unlike v1 (a blanket negative from a degenerate generator), the corrected instrument yields a
**capability-graded** picture:

- **state_reachability** — the **7B** model reaches `MECHANISM_SIGNAL_PRESENT`: it masters the
  principle at exposure 2, then same-structure accuracy *saturates* while other coordinates keep
  gaining — the genuine differential state-dependent signal. Below 7B the family is only
  `REPETITION_REMAINS_VALUABLE` (principle mastered, but repetition still paying, so the
  differential is not cleanly separable). This is the **only** mechanism signal on the ladder and
  it sits at the top of the capability range.
- **sequence_composition** — 1.5B / 3B / 7B reach `NO_STATE_DEPENDENT_RESIDUAL` (mastered, then
  same-structure late-gain flat or negative). 0.5B stays at repetition-still-valuable.
- **balance_conservation** — 0.5B / 1.5B / 3B hit `MODEL_FLOOR` (never cleared the learnability
  gate, so "no residual" is *not even claimable* — the model cannot do the base task); 7B reaches
  repetition-still-valuable.

## What this is and is not
This is a **Phase-0/1 instrument read**, not a promoted scientific claim
(`grants_scientific_authority=false`). The 7B `state_reachability` mechanism signal is a **lead**,
not a result: it is consistent with the series' standing thesis that the instrument's capability
floor gates the test (`CAPABLE_MODEL_AVAILABLE` blocker, Paper VI §13d), and it sharpens — but does
not discharge — the requirement for a capable in-ladder model + gate #462 before the adaptive
Phase-2 scheduler is built. No terminal here promotes anything; the ladder is preserved as evidence.

## Relationship to v1
`../paper4_phase1_results/` holds the **v1** ladder (jobs 3486377–80), preserved byte-unchanged as
**negative history**: a generator defect (2 unique rendered inputs/family → memorized a one-token
difference) made its blanket negative an instrument artifact, not a test of the mechanism
(see `../paper4_phase1_results/ROOT_CAUSE.md`). v1 is **retracted as an instrument**; v2 (this tree)
is the valid re-run. Neither tree grants scientific authority.

## Provenance
Artifacts are byte-identical to LUNARC (`sha256`-verified at harvest). Each model dir holds
`exposure_outcomes_v2.jsonl` + `run_manifest_v2.json`; model checkpoints remain on LUNARC
(not harvested — too large, and not needed to read the terminals).
