# ExperienceBenchmark v1.3_2 — Phase-1 3B ORACLE (#247)

Model-scale overlay of frozen ORACLE protocol after
`MODEL_CAPABILITY_FLOOR_1_5B` on job **3476756** (instrument parent **3476742** preserved).

## What this is

- Same `learning_loop_mode=root_cause_v1`
- Same `ORACLE_PROCEDURE_UPPER_BOUND` on FRESH_TRANSFER (T1/T2/T3)
- Same evaluator / tasks / system prompt / pass rule (`success_rate >= 2/3`, parse-valid)
- Same corrected schema interface from PR #343 (`rejected_evidence_ids` string arrays)
- Model: **Qwen2.5-3B-Instruct** staged at FS9 `assets/paper2-model-qwen25-3b-v1`

## DifferenceWitness

Parent is floored **v1.3_1 1.5B ORACLE**, not broken v1.2 and not instrument-defect 3476742.
This is **not** a scale-only escape from the v1.2 learning-loop failure.
Preregistered escalation: `PAPER2_EXPERIENCE_ROOT_CAUSE_PROTOCOL_V1.md` remaining moves are **3B+**.

## Forbidden until ORACLE passes

- learning / architecture staircase (RESET / FAILURE_MEMORY / VERIFIED / FULL_RAKL)
- promotional lift claims
- reopening #138
- reinterpreting 3476548 / 3476730 / 3476731 / 3476756 as lift
- overwriting v1.3_1 negative history

## Decision (job 3476778)

Landed native ORACLE **3476778**: success_rate 0/3, parse-valid 3/3, mean_score 0.33.
Scientific verdict: **MODEL_CAPABILITY_FLOOR_3B**.
Parents **3476756** (`MODEL_CAPABILITY_FLOOR_1_5B`) and **3476742** (`INSTRUMENT_DEFECT`) remain immutable negative history.
See `ORACLE_DECISION_RECEIPT_V1_3_2.json` and `PAPER_FACING_NOTE_ORACLE_V1_3_2_ISSUE247.md`.
Phase-0 / learning staircase remain unauthorized. #138 stays closed.
