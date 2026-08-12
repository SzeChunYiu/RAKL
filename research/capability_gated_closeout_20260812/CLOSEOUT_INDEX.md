# Capability-gated ORACLE leftover closeout — 2026-08-12

**Decision:** `TERMINAL_STOP` after authorized ORACLE staircase + V2_EXEC GATE_FAIL.  
**CAPABLE_MODEL_AVAILABLE:** `NO_REFUTED`  
**Primary pointer:** `research/paper2_oracle_capability_gate_v2_exec/ORACLE_DECISION_RECEIPT_V2_EXEC.json` (job **3476813**, success **2/5**, parse **5/5**)

## Floors preserved (immutable)

| Scale | Job | Verdict |
|------:|-----|---------|
| 0.5B | 3476730 / 3476731 | `MODEL_CAPABILITY_FLOOR_0_5B` |
| 1.5B | 3476742 | `INSTRUMENT_DEFECT` (preserved) |
| 1.5B | 3476756 | `MODEL_CAPABILITY_FLOOR_1_5B` |
| 3B | 3476778 | `MODEL_CAPABILITY_FLOOR_3B` |
| 7B | 3476788 | `MODEL_CAPABILITY_FLOOR_7B` |
| 7B V2_EXEC | **3476813** | **`MODEL_CAPABILITY_FLOOR_7B_V2_EXEC`** (2/5 GATE_FAIL) |

## Already closed (ORACLE ladder)

| Issue | State | Note |
|------:|-------|------|
| #247 | CLOSED | ExperienceBenchmark / capability staircase |
| #356 | CLOSED | Phase-1 3B ORACLE |
| #372 | CLOSED | Phase-1 7B ORACLE |
| #379 | CLOSED | Wave-2 BLOCKED / ladder terminus |

## Closed by this closeout (pointer receipts)

| Issue | Terminal status | Receipt |
|------:|-----------------|---------|
| #398 | `TERMINAL_STOP__ORACLE_CAPABILITY_GATE_LEFTOVER` | `ISSUE_398_TERMINAL_RECEIPT.json` |
| #399 | `BLOCKED_CAPABILITY__CANNOT_IDENTIFY_RAKL_LEARNING` | `ISSUE_399_TERMINAL_RECEIPT.json` |
| #350 | `BLOCKED_CAPABILITY__CANNOT_EXECUTE_CONFIRMATORY_ALR` | `ISSUE_350_TERMINAL_RECEIPT.json` |
| #352 | `BLOCKED_CAPABILITY__CANNOT_IDENTIFY_A3_A4` | `ISSUE_352_TERMINAL_RECEIPT.json` |
| #367 | `BLOCKED_CAPABILITY__CANNOT_BIND_CONFIRMATORY_FOUR_ARM` | `ISSUE_367_TERMINAL_RECEIPT.json` |

## Explicit non-actions

- No 14B / 32B
- No Phase-0
- No gate softening (≥2/3 remains binding)
- No CAPABLE_MODEL flip
- No promotional learning / ALR / A3↔A4 / four-arm lift
