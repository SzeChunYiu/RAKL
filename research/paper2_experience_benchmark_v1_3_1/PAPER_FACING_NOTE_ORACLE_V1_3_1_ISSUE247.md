# Paper-facing note — Issue #247 Phase-1 1.5B ORACLE (v1.3_1)

## Bound measurement

- Packet: `paper2-experience-benchmark-v1_3_1`
- `protocol_subject_hash`: `61b9fd42f2a58713f04de1e6a170a0e233beeb057c38f01939e384b7b4cb2bc3`
- Arm: `ORACLE_PROCEDURE_UPPER_BOUND` @ Qwen2.5-1.5B-Instruct (FRESH_TRANSFER T1–T3)
- Primary job: **3476742** (COMPLETED {'status': ['SUCCESS'], 'return_code': {'set': True, 'infinite': False, 'number': 0}, 'signal': {'id': {'set': False, 'infinite': False, 'number': 0}, 'name': ''}})
- Decision receipt: `ORACLE_DECISION_RECEIPT_V1_3_1.json`
- Parent 0.5B floor: jobs **3476730** / **3476731** (`MODEL_CAPABILITY_FLOOR_0_5B`)

## Honest result (no promotional lift)

Under the frozen v1.3_1 ORACLE gate (`success_rate >= 2/3` with parse-valid outputs → pass):

| Coordinate | Value |
|---|---|
| success_rate | **0/3** |
| parse-valid | **1/3** (T1/T2 `schema_violation` on `rejected_evidence_ids` object items; T3 schema-ok content miss) |
| Scientific verdict | **`INSTRUMENT_DEFECT`** |

## What this does **not** authorize

- No 1.5B Phase-0 architecture staircase (RESET / FAILURE_MEMORY / VERIFIED / FULL_RAKL)
- No learning-staircase claim
- No `MODEL_CAPABILITY_FLOOR_1_5B` recording while parse-invalid outputs remain (instrument/format branch)
- No reopen of #138 / reinterpretation of jobs 3476548 or 3476730/3476731 as lift
- No experience-learning efficacy or promotional manuscript claim

Parent v1.3 0.5B ORACLE floor and v1.2 job 3476548 remain immutable honest-negative history. This note records only the Phase-1 1.5B ORACLE instrument-defect classification and the required same-size re-run after harness/prompt schema repair.
