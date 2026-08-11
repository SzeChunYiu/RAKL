# Paper-facing note — ORACLE capability-gate v2.0 (#379)

## Protocol version

`ORACLE_CAPABILITY_GATE_V2_0` / packet `paper2-oracle-capability-gate-v2`

## Why this exists

The preregistered ORACLE ladder terminated at **FLOOR_7B** (job **3476788**, success **1/3**, parse **3/3**).
Further 14B/32B scale shopping is **not authorized**. This packet freezes the **task/gate revisit** successor.

## Floor-7B stratum diagnosis (measurement vs capability)

| Task | Stratum | Result | Dominant signature |
|------|---------|--------|--------------------|
| T1 | REPEATED_FAMILY | success 1.0 | exact match |
| T2 | CROSS_DOMAIN_TRANSFER | fail 0.5 | verdict OK; `support_recall_incomplete` + `reject_recall_incomplete` |
| T3 | HOSTILE_NEAR_MISS | fail 0.375 | `verdict_mismatch` (CONTEXT_MISALIGNED vs REFUTE) + `support_recall_incomplete` |

- **Not** `INSTRUMENT_DEFECT` (parse-valid 3/3).
- **Is** `MODEL_CAPABILITY_FLOOR_7B` under the frozen ≥2/3 exact-success gate.
- Fail-closed: mean_score 0.625 does **not** clear `CAPABLE_MODEL_AVAILABLE`.

## Gate state after this freeze

- `CAPABLE_MODEL_AVAILABLE`: **`NO_REFUTED` / false**
- Learning staircase / Phase-0 / confirmatory ALR / four-arm: **unauthorized**
- ExperienceBenchmark learning claims: **unlicensed** (see `LEARNING_CLAIMS_LICENSE_STATUS.json`)
- Executable v2 ORACLE jobs: **not authorized yet** (`PROTOCOL_FROZEN_NOT_YET_EXECUTABLE`)
- Pilot diagnostic job: **not authorized** (receipt reanalysis only)

## Predicted discriminator (preregistered)

Can any authorized-scale (≤7B) ORACLE clear exact success ≥2/3 on a sealed transfer set that still includes CROSS_DOMAIN evidence-binding and HOSTILE_NEAR_MISS QoI discrimination under **unchanged** evaluator thresholds?

- If no: learning claims remain unlicensed under this ladder.
- If yes: only that receipt may flip `CAPABLE_MODEL_AVAILABLE`; Phase-0 still needs separate authorization.

## Next action

Author sealed v2 transfer tasks → freeze executable ORACLE packet → only then consider ORACLE jobs. Do **not** invent a pass.
