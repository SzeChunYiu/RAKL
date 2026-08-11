# Strongest-version campaign scoreboard — 2026-08-12 (V2_EXEC floor after 3476813)

**Tip main at prior freeze:** `10646fd9d7b451f3cc013600a098530295dc87d1` (merge #383)  
**Machine-readable:** `research/STRONGEST_VERSION_CAMPAIGN_SCOREBOARD_20260812.json`  
**CAPABLE_MODEL_AVAILABLE:** `NO_REFUTED` (false)  
**Wave-2 confirmatory unlock:** **no**

Closed GitHub issues are historical terminals, **not** proof the scientific question was answered.

## ORACLE chain (receipt-confirmed)

| Jobs | Verdict | Packet / PR |
|------|---------|-------------|
| 3476730 / 3476731 | `MODEL_CAPABILITY_FLOOR_0_5B` | v1.3 |
| 3476742 | `INSTRUMENT_DEFECT` | v1.3_1 |
| 3476756 | `MODEL_CAPABILITY_FLOOR_1_5B` | v1.3_1 / #349 |
| 3476778 (race 3476779) | `MODEL_CAPABILITY_FLOOR_3B` (0/3, parse 3/3) | v1.3_2 / #371 |
| **3476788** | **`MODEL_CAPABILITY_FLOOR_7B`** (1/3, parse 3/3) | v1.3_3 / #374+#378 |
| **3476813** | **`MODEL_CAPABILITY_FLOOR_7B_V2_EXEC`** (2/5, parse 5/5) | V2_0_EXEC / #383 + harvest PR |

## Escalation

- Preregistered staircase: 0.5B → 1.5B → 3B → **7B**, then stop or revisit task/gate.
- V2 sealed-task revisit @ 7B (**3476813**) failed ≥2/3 exact-success gate (**2/5**).
- **Next authorized scale: none.** No 14B/32B.
- Phase-0 / learning staircase / confirmatory Wave-2 model jobs: **unauthorized**.
- Decision: **TERMINAL_STOP__V2_EXEC_GATE_FAIL** with `CAPABLE_MODEL_AVAILABLE=NO_REFUTED`.

## Wave 1 lanes

| Lane | Status | PR |
|------|--------|----|
| A ORACLE | FLOOR_7B + V2_EXEC floor recorded | #354/#357/#371/#374/#378/#383 |
| B ALR/A3↔A4 prep | frozen; model jobs blocked | #355 |
| C Paper-III human | BLOCKED_HUMAN freeze | #361 |
| D Paper-V novelty human | BLOCKED_HUMAN freeze | #360 |
| E active-sham | policy frozen; no confirmatory outcomes | #368 |

## Wave 2 blockers

1. Capable-model gate still closed (`NO_REFUTED`) after V2_0_EXEC 7B ORACLE fail (3476813: 2/5).
2. No Phase-0 RESET/FAILURE_MEMORY/VERIFIED/FULL_RAKL; no confirmatory ALR / A3↔A4 / four-arm model execution.
3. Real humans still absent for Paper III/V independent tracks.
4. Further scale shopping (14B/32B) remains protocol-illegal.
