# P3 acceptance matrix

| Case | Required result |
|---|---|
| pre-contract historical candidate | original verdict + `LEGACY_PRE_PACKET` metadata |
| new positive candidate, no packet id | `KEEP_PROPOSAL_ONLY` |
| new positive candidate, unknown packet id | `KEEP_PROPOSAL_ONLY` |
| new positive candidate, valid frozen packet | ordinary evidence/telemetry verdict unchanged |
| renamed historical mechanic | treated as new; packet required |
| new registration, missing/invalid packet | registration preflight problem; gate main returns nonzero |
| packet itself valid but evidence negative | negative/proposal-only remains negative; packet creates no benefit |
| conditional evidence + invalid packet | conditional promotion blocked |
| scientific authority | always false |
