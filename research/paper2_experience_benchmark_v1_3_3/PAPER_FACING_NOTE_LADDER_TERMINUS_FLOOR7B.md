# Paper-facing note — Ladder terminus after FLOOR_7B (#372)

## Decision

**TERMINAL_STOP** under the preregistered ExperienceBenchmark / root-cause escalation rule.

Authorized ORACLE scales exhausted:

| Scale | Job | Verdict | Success | Parse |
|-------|-----|---------|---------|-------|
| 0.5B | 3476730/3476731 | `MODEL_CAPABILITY_FLOOR_0_5B` | 0/3 | 3/3 |
| 1.5B | 3476742 | `INSTRUMENT_DEFECT` (preserved) | 0/3 | 1/3 |
| 1.5B | 3476756 | `MODEL_CAPABILITY_FLOOR_1_5B` | 0/3 | 3/3 |
| 3B | 3476778 | `MODEL_CAPABILITY_FLOOR_3B` | 0/3 | 3/3 |
| **7B** | **3476788** | **`MODEL_CAPABILITY_FLOOR_7B`** | **1/3** | **3/3** |

## Rule binding

- `research/PAPER2_EXPERIENCE_ROOT_CAUSE_PROTOCOL_V1.md`: remaining moves after 0.5B/1.5B floors are **3B+**, or revisit task/gate.
- Issue #372: after 3B floor, escalate to **7B**, then **stop** or revisit task/gate — do not choose models to make RAKL look good.
- Batch contract `preregistered_escalation=7B_after_3B_floor`.

**14B / 32B are not authorized.** Further scale shopping is protocol-illegal without a new frozen amendment.

## Gate state

- `CAPABLE_MODEL_AVAILABLE`: **`NO_REFUTED` / false**
- Phase-0 / learning staircase: **unauthorized**
- Promotional lift / reopen #138: **forbidden**
- Wave-2 confirmatory model empirics (ALR, A3↔A4, four-arm): **BLOCKED**

## Residual (honest)

Successor work must either (a) freeze a new versioned task/gate revisit protocol, or (b) remain blocked. It must not invent a pass or start Phase-0.
