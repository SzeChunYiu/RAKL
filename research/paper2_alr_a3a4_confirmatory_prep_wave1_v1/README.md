# Paper II Wave-1 ALR / A3↔A4 confirmatory preparation v1

**Status:** `PREP_FROZEN_EXECUTION_FORBIDDEN`

**Lane:** Wave-1 Lane B

**CAPABLE_MODEL_AVAILABLE:** `false`

Versioned successor prep packet. Does **not** overwrite
`research/paper2_alr_confirmatory_v1/` or
`research/paper2_closest_parent/A3_A4_MATCHED_EMPIRICAL_PACKET_V1.json`.

## What this packet is

- Exact V2 panel/evaluator/protocol hash binding
- Capability gate freeze (`CAPABLE_MODEL_AVAILABLE=false` until ORACLE ≥2/3)
- Explicit ban on confirmatory model-job submission while the gate is false
- Negative-history pointers (3476730/31, 3476742, 3476756, prior ALR / A3↔A4 jobs)

## What this packet is not

- Confirmatory ALR results
- Confirmatory A3↔A4 superiority
- Permission to submit capability-dependent model jobs

## Successor issues

- ALR confirmatory science: #350
- A3↔A4 confirmatory science: #352
- Closed parents (science unmet): #324, #156

## Reproduce / inspect

```bash
python -m json.tool research/paper2_alr_a3a4_confirmatory_prep_wave1_v1/PREP_PACKET.json
pytest tests/test_paper2_alr_a3a4_confirmatory_prep_wave1.py -q
```
