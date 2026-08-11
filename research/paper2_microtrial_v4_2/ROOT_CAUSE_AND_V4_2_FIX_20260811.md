# V4.1 zero exact conceptual pass — root cause and V4.2 fix

## Object / QoI / context

- Object: sealed pendulum known-answer microtrial under DIRECT_CORPUS vs RAKL_CONTEXT.
- QoI: exact conceptual pass under frozen evaluator `PENDULUM_KNOWN_ANSWER_V2`.
- Context: Qwen2.5-0.5B-Instruct @ 7ae5576, seed 17, COMPLETE_SEALED, tip jobs 3475212/3476520/3476521/3476524.
- Authority: non-confirmatory engineering; not independent review; not #138 experience §B.

## Ruling out

| Hypothesis | Result |
|---|---|
| Scorer bug | **Refuted.** Gold polarity is all-true by field naming; RAKL answers are literally `false` on two fields → 3/5. |
| Wrong subject tip | **Refuted.** Deterministic identical outputs across four tip jobs. |
| Overly strict exact-match vs near-miss content | **Not a bug.** Exact gate is intentional; RAKL misses 2/5 conceptual bits. |
| Env/runtime | **Not causal.** Receipt chain PASS; Transformers warning retained as evidence only. |
| DIRECT parse-null only | **Partial.** Fence+trailing prose correctly rejected by frozen V4.1 policy; if scored anyway → **1/5**. |

## Selected diagnosis

Joint residual:

1. **R1 (serialization):** DIRECT_CORPUS emits ` ```json ` + object + trailing Explanation prose → V4.1 `fullmatch` rejects.
2. **R7 (scientific output / prompt interface):** Registered questions are multi-clause NL; boolean field polarity is not explicit. 0.5B systematically mis-maps Q1/Q2 onto `small_angle_is_asymptotic` and `context_alignment_required_before_contradiction`.

## Honest fix (V4.2)

- Freeze field-polarity + stop-after-JSON prompt interface **without** changing evaluator thresholds or V4.1 normalizer.
- Clip generation after one completed JSON fence/object (serialization hygiene).
- Require dual-memory review + difference witness before candidate.
- Fresh native run only; preserve all V4/V4.1 negatives.

## Paper numbers

Still **BLOCKED** until a fresh V4.2 harvest shows `exact_conceptual_pass_arm_count > 0` under the unchanged gate. If still zero: document as model-capacity limit, not a silent pipeline bug.
