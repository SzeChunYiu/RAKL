# Paper II ExperienceBenchmark power design (#247)

Pre-execution power / MDE freeze for the `root_cause_v1` successor packet.

## Status

- **Zero confirmatory outcomes** observed at power-design time (`ZERO_OUTCOMES_AT_POWER_DESIGN`).
- **ORACLE not executed** — local model assets absent; LUNARC required (`CANNOT_EXECUTE_ORACLE_WITHOUT_COMPUTE`).
- v1/v1.1/v1.2 remain immutable negative history (job 3476548).

## Registered endpoints

| Contrast | Quantity | MDE |
|---|---|---|
| E − A (selective RAKL vs reset) | paired success-rate lift | **0.20** |
| Hostile-near-miss safety | failure-rate increase ceiling | **0.15** unacceptable |
| Repeated-failure guard | rate increase ceiling | **0.20** unacceptable |

Do **not** use `delta > 0` as a success rule. Required inferential statuses:

`DISTINGUISHABLE_BENEFIT`, `DISTINGUISHABLE_HARM`, `MEASURED_BUT_INDISTINGUISHABLE`, `UNDERPOWERED`, `INVALID_OR_CONTAMINATED`.

## Successor task panel

Frozen under `research/paper2_experience_benchmark_root_cause_v1/`:

- 3 development tasks (D1–D3; method-family calibration / unit / context lessons)
- **18 fresh-transfer tasks** across five strata (≥3 each)
- Diagnostic arms per `research/PAPER2_EXPERIENCE_ROOT_CAUSE_PROTOCOL_V1.md`
- `learning_loop_mode=root_cause_v1` (RC1/RC2 from #238 / PR #299)

## Reproduce

```bash
python3 scripts/paper2_power_design_simulate.py
python3 scripts/paper2_power_design_finalize.py
pytest tests/test_paper2_power_design.py tests/test_paper2_capability_floor_receipt.py -q
```

## Claim boundary

Power-design receipts grant **no** ORACLE evidence, no capability-floor clearance, and no experience-learning efficacy claim. They only freeze sizing before evaluated outcomes.
