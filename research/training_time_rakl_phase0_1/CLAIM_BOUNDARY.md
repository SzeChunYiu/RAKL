# Claim boundary — training-time RAKL Phase 0/1 (#461)

## What this lane owns

- Known-structure generator with deterministic verifier gold (≥3 heterogeneous families)
- Hostile controls: template-leak probes, coordinate-ablated twins, semantic-near decoys
- Exposure-curve experiment harness **scaffold** (schedule only)
- Pre-outcome protocol freeze receipt

## What this lane does not own

| Excluded | Owner |
|----------|-------|
| GLM-5.2 mechanism suite | #443 / `research/glm52_mechanism_suite_v1*` |
| RAKL_math cycle metrology | #446 / `RAKL_math` |
| Paper V four-arm causal attribution | #446 |
| Adaptive vs static allocation | #466 (hard blocked) |
| Train/inference structure reuse | #467 (hard blocked) |
| Paper VI decision | #462 |

## Architecture vs experiment

`src/rakl/training_projection.py` remains proposal-only architecture (#455/#465).
This lane supplies the **empirical instrument** for Phase 0/1 only. Merging the
training projection PR does not license efficacy wording.

## Authority

- `grants_scientific_authority`: **false**
- `scientific_claim_status`: **NO_EMPIRICAL_RESULT**
- Training utility is not scientific authority.

## Negative history preserved

No prior #461 learner outcomes exist. This freeze is chronology-bound before any
exposure-curve or mastery-coordinate results are accessed.
