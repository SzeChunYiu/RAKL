# V4.3 job 3476566 — DIRECT parse_valid=false root cause

## Ruling out

| Hypothesis | Result |
|---|---|
| Fence + trailing prose (V4.1 signature) | **Refuted.** DIRECT raw is bare JSON object. |
| Invalid JSON | **Refuted.** JSON parses. |
| Scorer / tip bug | **Refuted.** Harvest chain PASS; RAKL arm scored 2/5. |
| Soft exact gate needed | **Forbidden / not indicated.** Gate unchanged; residual is serialization shape. |

## Selected diagnosis

**R1:** DIRECT emitted registered-schema envelope `{"fields":{...},"id":"PENDULUM_STRUCTURED_ANSWER_V2"}`
matching the prompt meta OUTPUT SCHEMA descriptor. Flat answer schema required → parse_valid=false.

## Honest fix (V4.3.1)

Replace meta OUTPUT SCHEMA with flat OUTPUT OBJECT SHAPE; optionally unwrap that exact registered
envelope once in a V4.3.1 normalizer overlay. Do **not** soften `exact_conceptual_pass`.
