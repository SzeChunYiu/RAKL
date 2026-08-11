# Paper II ExperienceBenchmark root-cause successor (v1)

**Status:** `PROTOCOL_FROZEN_AWAITING_ORACLE / ROOT_CAUSE_V1 / NO_EMPIRICAL_RESULT`

**Issue:** #247 (successor to #138 / v1.2 job 3476548)

## What this packet is

The first **honest successor** after #238 RC1/RC2 repair (PR #299):

- `learning_loop_mode=root_cause_v1` — no pseudo-lessons; selective materialization with receipts
- **18 fresh-transfer tasks** across five strata (not the v1.2 n=3 panel)
- Diagnostic arms frozen per `research/PAPER2_EXPERIENCE_ROOT_CAUSE_PROTOCOL_V1.md`
- **ORACLE runs first** at Qwen2.5-0.5B before any architecture-comparison arm

## What this packet is not

- Not a scale-only DifferenceWitness clone of v1.2
- Not authorized for 1.5B ExperienceBenchmark until ORACLE gate completes
- Not a capability-floor kill — ORACLE outcomes do not exist yet

## Execution gate

```text
CANNOT_EXECUTE_ORACLE_WITHOUT_COMPUTE
```

Local model assets are absent. Submit ORACLE arm on LUNARC using the frozen 0.5B snapshot from the inherited model block.

## Bindings

| Artifact | Role |
|---|---|
| `PROTOCOL_FREEZE_PACKET.json` | Protocol subject hash + model/evaluator inheritance |
| `TASK_PANEL_DESIGN.json` | Strata-balanced 18-task transfer panel |
| `tasks/` | Frozen task bytes (D1–D3 development; T1–T18 transfer) |
| `research/paper2/power_design/DECISION_RECEIPT.json` | Pre-execution power / MDE freeze |
| `research/paper2/CAPABILITY_FLOOR_DECISION_RECEIPT.json` | Adjacent-job capability evidence (non-ORACLE) |

## Parent negative history

`paper2-experience-benchmark-v1_2` / job **3476548** remains immutable. Do not rebind or rerun under the same protocol subject hash.
