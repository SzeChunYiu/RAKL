# Strongest-version campaign scoreboard — 2026-08-12 (terminal after FLOOR_7B)

**Tip main at freeze:** `313fd2eaf0d596f6d5b41e59160b9d79852dc75b` (merge #378)  
**Machine-readable:** `research/STRONGEST_VERSION_CAMPAIGN_SCOREBOARD_20260812.json`  
**CAPABLE_MODEL_AVAILABLE:** `NO_REFUTED` (false)

Closed GitHub issues are historical terminals, **not** proof the scientific question was answered.

## ORACLE chain (receipt-confirmed)

| Jobs | Verdict | Packet / PR |
|------|---------|-------------|
| 3476730 / 3476731 | `MODEL_CAPABILITY_FLOOR_0_5B` | v1.3 |
| 3476742 | `INSTRUMENT_DEFECT` | v1.3_1 |
| 3476756 | `MODEL_CAPABILITY_FLOOR_1_5B` | v1.3_1 / #349 |
| 3476778 (race 3476779) | `MODEL_CAPABILITY_FLOOR_3B` (0/3, parse 3/3) | v1.3_2 / #371 |
| **3476788** | **`MODEL_CAPABILITY_FLOOR_7B`** (1/3, parse 3/3) | v1.3_3 / #374+#378 |

## Escalation (ladder terminus)

- Preregistered staircase: 0.5B → 1.5B → 3B → **7B**, then **stop** or revisit task/gate (`PAPER2_EXPERIENCE_ROOT_CAUSE_PROTOCOL_V1.md`; #372).
- **Next authorized scale: none.** 14B/32B are **not** preregistered; do not invent a larger model because RAKL lost.
- Phase-0 / learning staircase: **unauthorized**.
- Decision: **TERMINAL_STOP** with `CAPABLE_MODEL_AVAILABLE=NO_REFUTED` across all authorized scales.

## Wave 1 lanes

| Lane | Status | PR |
|------|--------|----|
| A ORACLE | FLOOR_7B recorded; ladder terminal | #354/#357/#371/#374/#378 |
| B ALR/A3↔A4 prep | frozen; model jobs blocked | #355 |
| C Paper-III human | BLOCKED_HUMAN freeze | #361 |
| D Paper-V novelty human | BLOCKED_HUMAN freeze | #360 |
| E active-sham | policy frozen; no confirmatory outcomes | #368 |

## Wave 2 blockers

1. Capable-model gate closed for good under this ladder (`NO_REFUTED` at 0.5B/1.5B/3B/7B).
2. No Phase-0 RESET/FAILURE_MEMORY/VERIFIED/FULL_RAKL; no confirmatory ALR / A3↔A4 / four-arm model execution.
3. Real humans still absent for Paper III/V independent tracks.
4. Successor **ORACLE_CAPABILITY_GATE_V2_0** frozen under #379 (`paper2-oracle-capability-gate-v2`, `PROTOCOL_FROZEN_NOT_YET_EXECUTABLE`). Next: author sealed v2 transfer tasks → executable ORACLE freeze. **No jobs authorized by the freeze.** Not scale shopping.
