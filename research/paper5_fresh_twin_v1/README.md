# Paper 5 fresh replay twin generator v1 (#446 lane 7)

**Status:** `DESIGN_FROZEN_NO_OUTCOME_ACCESSED`  
**Issue:** [#446](https://github.com/SzeChunYiu/RAKL/issues/446) — fresh replay / twin causal bridge  
**Grants scientific authority:** no  
**Evaluated model outcomes accessed:** no

## What this is

Prospective generator design bridging naturalistic `RAKL_math` failure families to **fresh untouched twins** with deterministic known answers. Each registered family emits:

- one **VALID** twin where `ACCEPT_VALID_GLUE` is correct;
- one **INVALID** twin where `REJECT_FALSE_TRANSFER` is correct.

Historical cycle ids motivate families in `FAILURE_FAMILY_REGISTRY.json` but never appear in solver-facing prompts.

## Artifacts

| File | Role |
|---|---|
| `FAILURE_FAMILY_REGISTRY.json` | six structural failure families + forbidden solver tokens |
| `PROTOCOL_V1.md` | design freeze, arms, outcomes, contamination controls |
| `FREEZE_STUB.json` | hash-bound design receipt (no confirmatory execution) |
| `../../src/rakl/paper5_fresh_twin_generator.py` | deterministic generator + leakage sweep |
| `../../schemas/paper5-fresh-twin-v1.schema.json` | twin task schema |
| `../../schemas/paper5-fresh-twin-family-v1.schema.json` | family registry entry schema |
| `../../experiments/paper5/freeze_fresh_twin_protocol.py` | rebuild freeze stub + dev manifest |
| `../../tests/test_paper5_fresh_twin_generator.py` | hostile tests |

## What this is not

- Not confirmatory causal evidence for current RAKL.
- Not a rerun of exact historical NS/Hodge/YM cases.
- Not `#459` quantifier witness implementation or `#464` chronology hook evidence.
- Not `#461` training Phase 0/1 generator.
- Not GLM mechanism suite v1.1 adapter integration (#443 sibling lane).

## Reproduce

```bash
python experiments/paper5/freeze_fresh_twin_protocol.py \
  --out-dir research/paper5_fresh_twin_v1

python -m pytest tests/test_paper5_fresh_twin_generator.py -q
```

## Overlap / sibling lanes

| Lane | Owner | This directory |
|---|---|---|
| GLM52 mechanism suite v1.1 | #443 / sibling | separate — do not merge adapter work here |
| RAKL_CYCLE_METRICS schema upgrade | #446 metrology sibling | longitudinal harvest unchanged |
| Training Phase 0/1 | #461 sibling | training projection on #455 branch is architecture-only |
| QuantifierCompatibilityWitness | #459 sibling | families inform design tests only |
| Pre-scratch fibre freeze hook | #464 sibling | not implemented here |
