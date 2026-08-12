# External-LLM comparator — development-tier result

**Status: DEVELOPMENT / EXPLORATORY, not confirmatory.** A real experiment (not a
simulation, not fabricated), but at N=144 with wide CIs — it *motivates* a larger frozen
confirmatory run, it does not yet establish a confirmatory claim.

## Question
Does forcing an LLM through RAKL's fail-closed applicability-obligation gate reduce
invalid-transfer **false-accepts** versus (a) direct judgement and (b) free chain-of-thought?

## Design (frozen before scoring; see run_comparator.py header)
- 144 fresh transfer tasks, `rakl.objective_transfer_benchmark`, **seed 424242** (not the
  frozen confirmatory seed); **exact-verifier gold** (64 ACCEPT / 64 REJECT / 16 CANNOT_CHECK),
  includes hostile `SEMANTIC_NEAR_MISS` decoys.
- Same model (**glm-5.2**), three conditions differing only in instruction: `DIRECT`,
  `FREE_COT` (controls for compute), `RAKL_GATE` (obligation checklist, fail-closed).
- Primary metric: invalid-transfer false-accept = P(model=ACCEPT | gold=REJECT).

## Result (bootstrap 95% CI, 20k resamples)
| Condition | False-accept on invalid ↓ | 3-way accuracy ↑ | Abstention |
|---|---|---|---|
| Direct (plain)   | 0.578 [0.453, 0.703] | 0.611 [0.528, 0.688] | 0.02 |
| Free CoT (control) | 0.453 [0.328, 0.578] | 0.549 [0.465, 0.625] | 0.19 |
| **RAKL gate**      | **0.344 [0.234, 0.453]** | **0.694 [0.618, 0.771]** | 0.10 |

- The obligation gate **cut false-accepts 0.58 → 0.34 (≈41% relative)** and **raised accuracy
  0.61 → 0.69**, and **beat the compute-matched Free-CoT control** on both — so the gain is
  attributable to the obligation **structure**, not just more thinking. Point estimates are
  monotone in the expected direction.

## Honest caveats (do not overclaim)
1. **N=144 → wide CIs; borderline significance.** Direct-vs-gate false-accept CIs *touch*
   (0.453 vs 0.453). This is a directional signal, not a confirmed effect. Paper II's own
   power analysis suggested n≈431 decidable for the registered 0.05 MDE.
2. **System/method effect, not a smarter model.** The gate is a prompt scaffold + structured
   inference; report as system-level uplift, never "the model reasons better."
3. **Honest weakness:** on the hardest `SEMANTIC_NEAR_MISS` decoys the gate did **not** help
   (false-accept 0.375, same as Direct) — the checklist catches structural violations
   (direction/boundary/QoI) but not the trickiest look-alikes.
4. One model, one seed, one benchmark family set; development tier.

## Next step to make it a paper claim
Re-run frozen at n≈431 across ≥6 families, seed and thresholds declared first, as the
Paper II confirmatory-lane "strong external LLM comparator" (currently declared open).
Files: `run_comparator.py` (frozen design), `raw_results.jsonl`, `summary.json`,
`comparator_result.pdf` (figure).
