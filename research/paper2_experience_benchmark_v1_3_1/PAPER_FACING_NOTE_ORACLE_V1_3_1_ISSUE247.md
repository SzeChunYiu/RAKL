# Paper-facing note — Issue #247 Phase-1 1.5B ORACLE (v1.3_1)

## Bound measurement

- Packet: `paper2-experience-benchmark-v1_3_1`
- `protocol_subject_hash`: `61b9fd42f2a58713f04de1e6a170a0e233beeb057c38f01939e384b7b4cb2bc3`
- Arm: `ORACLE_PROCEDURE_UPPER_BOUND` @ Qwen2.5-1.5B-Instruct (FRESH_TRANSFER T1–T3)
- Primary job after instrument repair: **3476756** (COMPLETED `0:0`)
- Instrument-defect parent (preserved negative history): **3476742** (`INSTRUMENT_DEFECT`; parse-valid 1/3)
- Harness repair lineage: PR #343 (`rejected_evidence_ids` object unwrap / string-array enforcement)
- Decision receipt: `ORACLE_DECISION_RECEIPT_V1_3_1.json`
- Parent 0.5B floor: jobs **3476730** / **3476731** (`MODEL_CAPABILITY_FLOOR_0_5B`)

## Honest result (no promotional lift)

Under the frozen v1.3_1 ORACLE gate (`success_rate >= 2/3` with parse-valid outputs → pass):

| Coordinate | Value |
|---|---|
| success_rate | **0/3** |
| parse-valid | **3/3** (schema-valid after #343 unwrap; content miss on all trials) |
| mean_score | **0.25** |
| Per-trial schema | T1/T2/T3: parse-ok; failures `verdict_mismatch`, `support_recall_incomplete`; verdict `CANNOT_CHECK` |
| Scientific verdict | **`MODEL_CAPABILITY_FLOOR_1_5B`** |

Job **3476742** remains immutable honest-negative history for the pre-repair instrument branch and must not be deleted or rewritten as a floor measurement.

## What this does **not** authorize

- No 1.5B Phase-0 architecture staircase (RESET / FAILURE_MEMORY / VERIFIED / FULL_RAKL)
- No learning-staircase claim
- No promotional / manuscript lift claim
- No reopen of #138 / reinterpretation of jobs 3476548 or 3476730/3476731 as lift
- No experience-learning efficacy claim

Parent v1.3 0.5B ORACLE floor, v1.2 job 3476548, and instrument job 3476742 remain immutable honest-negative history. This note records only the post-repair Phase-1 1.5B ORACLE capability-floor classification.
