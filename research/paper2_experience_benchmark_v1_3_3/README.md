# ExperienceBenchmark v1.3_3 — Phase-1 7B ORACLE (#372)

Model-scale overlay of frozen ORACLE protocol after
`MODEL_CAPABILITY_FLOOR_3B` on job **3476778** (parents **3476756**
`MODEL_CAPABILITY_FLOOR_1_5B` and **3476742** `INSTRUMENT_DEFECT` preserved).

## What this is

- Same `learning_loop_mode=root_cause_v1`
- Same `ORACLE_PROCEDURE_UPPER_BOUND` on FRESH_TRANSFER (T1/T2/T3)
- Same evaluator / tasks / system prompt / pass rule (`success_rate >= 2/3`, parse-valid)
- Same corrected schema interface from PR #343 (`rejected_evidence_ids` string arrays)
- Model: **Qwen2.5-7B-Instruct** staged at FS9 `assets/paper2-model-qwen25-7b-v1`
- Successor issue ownership: **#372** (parent campaign #247 closed)

## DifferenceWitness

Parent is floored **v1.3_2 3B ORACLE**, not broken v1.2 and not instrument-defect 3476742.
This is **not** a scale-only escape from the v1.2 learning-loop failure.
Preregistered escalation: `PAPER2_EXPERIENCE_ROOT_CAUSE_PROTOCOL_V1.md` remaining moves are **3B+**; #372 locks **7B** after FLOOR_3B.

## Forbidden until ORACLE passes

- learning / architecture staircase (RESET / FAILURE_MEMORY / VERIFIED / FULL_RAKL)
- promotional lift claims
- reopening #138
- reinterpreting 3476548 / 3476730 / 3476731 / 3476756 / 3476778 as lift
- overwriting v1.3_1 / v1.3_2 negative history

## Decision (job 3476788)

Landed native ORACLE **3476788**: success_rate 1/3, parse-valid 3/3, mean_score 0.62.
Scientific verdict: **MODEL_CAPABILITY_FLOOR_7B**.
Parents **3476778** (`MODEL_CAPABILITY_FLOOR_3B`), **3476756** (`MODEL_CAPABILITY_FLOOR_1_5B`) and **3476742** (`INSTRUMENT_DEFECT`) remain immutable negative history.
See `ORACLE_DECISION_RECEIPT_V1_3_3.json` and `PAPER_FACING_NOTE_ORACLE_V1_3_3_ISSUE372.md`.
Phase-0 / learning staircase remain unauthorized. #138 stays closed.
