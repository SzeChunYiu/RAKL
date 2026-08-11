# Paper-facing note — Issue #247 Phase-1 3B ORACLE (v1.3_2)

## Bound measurement

- Packet: `paper2-experience-benchmark-v1_3_2`
- `protocol_subject_hash`: `c8afd4ca39ff2e4abce968a53bf52dab3854ebbb97ff0e73c3b151f1a42d27e8`
- Arm: `ORACLE_PROCEDURE_UPPER_BOUND` @ Qwen2.5-3B-Instruct (FRESH_TRANSFER T1–T3)
- Primary job: **3476778** (COMPLETED `0:0`)
- Parent 1.5B floor (preserved): **3476756** (`MODEL_CAPABILITY_FLOOR_1_5B`)
- Instrument-defect ancestor (preserved): **3476742** (`INSTRUMENT_DEFECT`)
- Harness repair lineage: PR #343 (`rejected_evidence_ids` string-array / object unwrap)
- Decision receipt: `ORACLE_DECISION_RECEIPT_V1_3_2.json`

## Honest result (no promotional lift)

Under the frozen v1.3_2 ORACLE gate (`success_rate >= 2/3` with parse-valid outputs → pass):

| Coordinate | Value |
|---|---|
| success_rate | **0/3** |
| parse-valid | **3/3** |
| mean_score | **0.33** |
| Per-trial | T1 score 0.5 (`verdict_mismatch`); T2 score 0.5 (recall incomplete); T3 score 0.0 (`unknown_evidence_id` empty reject id + mismatches) |
| Scientific verdict | **`MODEL_CAPABILITY_FLOOR_3B`** |

## What this does **not** authorize

- No 3B Phase-0 architecture staircase (RESET / FAILURE_MEMORY / VERIFIED / FULL_RAKL)
- No learning-staircase claim
- No promotional / manuscript lift claim
- No reopen of #138
- No overwrite of v1.3_1 / 3476742 / 3476756 negative history
