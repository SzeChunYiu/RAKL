# External-LLM comparator — CONFIRMATORY result

Scale-up of `research/llm_comparator_dev_v1` to n≈504 (≥ Paper II's registered n≈431 target).
Same frozen 3-condition design; fresh seed **20260812**; glm-5.2; exact-verifier gold.

## Result (bootstrap 95% CI, 20k resamples)
| Condition | False-accept on invalid ↓ | 3-way accuracy ↑ | Abstention |
|---|---|---|---|
| Direct (plain)   | 0.527 [0.460, 0.589] | 0.637 [0.595, 0.679] | 0.03 |
| Free CoT (control) | 0.536 [0.473, 0.603] | 0.577 [0.534, 0.621] | 0.12 |
| **RAKL gate**      | **0.339 [0.277, 0.402]** | **0.708 [0.669, 0.748]** | 0.10 |

## What it establishes
1. **Significant primary effect.** The obligation gate cuts invalid-transfer false-accepts
   **0.53 → 0.34**; the 95% CIs of Direct and RAKL_GATE **do not overlap** (0.460 vs 0.402).
   This is a firm effect at confirmatory N, not the borderline dev-run signal.
2. **The gain is from STRUCTURE, not compute.** Free CoT (0.536) is statistically
   indistinguishable from Direct (0.527) on false-accepts — "think harder" does nothing — while
   the gate (0.339) is well below both. The compute-matched control isolates the obligation
   structure as the cause.
3. **Accuracy also improves** (0.64 → 0.71), CIs essentially separated.
4. **GLM 5.2 clears the capability floor.** With ~0.7 accuracy and a large, well-resolved gate
   effect, GLM 5.2 produces the above-floor signal the series' prior models (Qwen 0.5B–7B, 0/3)
   could not — directly relevant to Paper VI's master blocker (`CAPABLE_MODEL_AVAILABLE`).

## Honest limits (still)
- **One model, one benchmark family-set, one seed.** For a broad claim, replicate across
  models/seeds and the ≥6-family sign test.
- **System/method effect, not a smarter model** (a scaffold + structured inference). Report via
  the model-vs-system attribution, never "the model reasons better."
- **Hardest decoys unhelped:** on `SEMANTIC_NEAR_MISS`, the gate does not beat Direct (0.357 vs
  0.268) — the checklist catches structural violations (direction/boundary/QoI), not the
  trickiest look-alikes. This is a real, reportable weakness.
- Not merged into the frozen Paper II confirmatory packet governance; this is a fresh, honestly
  frozen comparator lane. Report as a preliminary confirmatory comparator, subject to the
  model/seed replication above.

Files: `run.py`, `raw_results.jsonl`, `summary.json`, `comparator_result.pdf`.
