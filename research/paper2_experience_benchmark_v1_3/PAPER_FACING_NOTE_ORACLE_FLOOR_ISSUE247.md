# Paper-facing note — Issue #247 Phase-1 ORACLE floor (v1.3)

## Bound measurement

- Packet: `paper2-experience-benchmark-v1_3`
- `protocol_subject_hash`: `ed116353230dc526fa45657d1a81afab26a460fe3b8411480a0f84bb1f711672`
- Arm: `ORACLE_PROCEDURE_UPPER_BOUND` @ Qwen2.5-0.5B-Instruct (FRESH_TRANSFER T1–T3)
- Primary job: **3476730** (COMPLETED 0:0)
- Race duplicate (preserved negative history): **3476731** (COMPLETED 0:0)
- Decision receipt: `ORACLE_DECISION_RECEIPT_V1_3.json`

## Honest result (no promotional lift)

Under the frozen v1.3 ORACLE gate (`success_rate >= 2/3` parse-valid → pass):

| Coordinate | Value |
|---|---|
| success_rate | **0/3** |
| parse-valid | **3/3** (schema-valid JSON; not INSTRUMENT_DEFECT) |
| Scientific verdict | **`MODEL_CAPABILITY_FLOOR_0_5B`** |

## What this does **not** authorize

- No 0.5B Phase-0 architecture staircase (RESET / FAILURE_MEMORY / VERIFIED / FULL_RAKL) as the primary discriminator
- No ExperienceBenchmark@1.5B submit from this ORACLE gate alone
- No reopen of #138 / reinterpretation of job 3476548 as lift
- No experience-learning efficacy or promotional manuscript claim

Parent v1.2 job 3476548 remains immutable honest-negative history. This note records only the Phase-1 capability-floor classification.
