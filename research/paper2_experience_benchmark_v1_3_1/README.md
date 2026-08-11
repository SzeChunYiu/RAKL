# ExperienceBenchmark v1.3_1 — Phase-1 1.5B ORACLE (#247)

Model-scale overlay of frozen v1.3 ORACLE protocol after
`MODEL_CAPABILITY_FLOOR_0_5B` on jobs **3476730** / **3476731**.

## What this is

- Same `learning_loop_mode=root_cause_v1`
- Same `ORACLE_PROCEDURE_UPPER_BOUND` on FRESH_TRANSFER (T1/T2/T3)
- Same evaluator / tasks / system prompt / pass rule (`success_rate >= 2/3`, parse-valid)
- Model: **Qwen2.5-1.5B-Instruct** staged at FS9 `assets/paper2-model-qwen25-1_5b-v4-3`

## DifferenceWitness

Parent is floored **v1.3 0.5B ORACLE**, not broken v1.2.
This is **not** a scale-only escape from the v1.2 learning-loop failure.

## Forbidden until ORACLE passes

- learning / architecture staircase (RESET / FAILURE_MEMORY / VERIFIED / FULL_RAKL)
- promotional lift claims
- reopening #138
- reinterpreting 3476548 or 3476730/3476731 as lift

## Decision (job 3476756; parent instrument 3476742 preserved)

Landed native re-run **3476756** after PR #343 instrument repair: success_rate 0/3, parse-valid 3/3, mean_score 0.25.
Scientific verdict: **MODEL_CAPABILITY_FLOOR_1_5B**.
Prior job **3476742** remains landed as **INSTRUMENT_DEFECT** negative history (do not delete).
See `ORACLE_DECISION_RECEIPT_V1_3_1.json` and `PAPER_FACING_NOTE_ORACLE_V1_3_1_ISSUE247.md`.
Phase-0 / learning staircase remain unauthorized. #138 stays closed.

