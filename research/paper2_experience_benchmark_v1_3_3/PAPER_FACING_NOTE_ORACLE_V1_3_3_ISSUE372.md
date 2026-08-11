# Paper-facing note — Issue #372 Phase-1 7B ORACLE (v1.3_3)

## Bound measurement

- Packet: `paper2-experience-benchmark-v1_3_3`
- `protocol_subject_hash`: `dc7bff2e6fae3b54d0af87d116234081d4fd516645d735552fdc0d1b4f2141d6`
- Arm: `ORACLE_PROCEDURE_UPPER_BOUND` @ Qwen2.5-7B-Instruct (FRESH_TRANSFER T1–T3)
- Primary job: **3476788** (COMPLETED `0:0`)
- Parent 3B floor (preserved): **3476778** (`MODEL_CAPABILITY_FLOOR_3B`)
- Parent 1.5B floor (preserved): **3476756** (`MODEL_CAPABILITY_FLOOR_1_5B`)
- Instrument-defect ancestor (preserved): **3476742** (`INSTRUMENT_DEFECT`)
- Harness repair lineage: PR #343 (`rejected_evidence_ids` string-array / object unwrap)
- Decision receipt: `ORACLE_DECISION_RECEIPT_V1_3_3.json`

## Honest result (no promotional lift)

Under the frozen v1.3_3 ORACLE gate (`success_rate >= 2/3` with parse-valid outputs → pass):

| Coordinate | Value |
|---|---|
| success_rate | **1/3** |
| parse-valid | **3/3** |
| mean_score | **0.625** |
| Per-trial | T1 score 1.0 (success); T2 score 0.5 (recall incomplete); T3 score 0.375 (`verdict_mismatch` + incomplete support) |
| Scientific verdict | **`MODEL_CAPABILITY_FLOOR_7B`** |

## What this does **not** authorize

- No 7B Phase-0 architecture staircase (RESET / FAILURE_MEMORY / VERIFIED / FULL_RAKL)
- No learning-staircase claim
- No promotional / manuscript lift claim
- No reopen of #138
- No overwrite of v1.3_1 / v1.3_2 / 3476742 / 3476756 / 3476778 negative history
- CAPABLE_MODEL_AVAILABLE remains **false / NO_REFUTED**
