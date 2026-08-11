# V4.2 job 3476540 — capability-limit result (not a silent bug)

## Tip
`11f2ecbd3bed118f3fb9c2afac3e8d4229a56052` (PR #226)

## What changed vs V4.1
- Field-polarity prompt interface + stop-after-JSON clipping.
- Evaluator / exact conceptual gate / V4.1 normalizer / model / seed unchanged.

## Observed
- Job **3476540** COMPLETED on cn141.
- Both arms **parse_valid** (DIRECT no longer fence+prose null).
- Both arms **conceptual 3/5**, `exact_conceptual_pass=false`.
- Same two misses as V4.1 RAKL arm: `small_angle_is_asymptotic=false`, `context_alignment_required_before_contradiction=false`.

## Interpretation
Serialization residual (R1) was repaired. Remaining zero exact passes are a **0.5B model-capacity / scientific-output residual (R7/R8)**, not a scorer/parser/tip bug.

## Paper numbers
**Still BLOCKED.** Allowed wording: nonconfirmatory negative / capability limit under this sealed gate. Do not invent passes. Do not use as #138 experience §B. Do not claim #41/#43.

## Next discriminator (optional)
Larger model or different task under a new frozen packet — not threshold softening.
