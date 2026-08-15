# Hostile engineering assurance matrix

Every row must have a planted failure, expected typed terminal, exact release identity, and immutable result receipt.

| ID | Attack / failure | Expected invariant | Allowed result |
|---|---|---|---|
| H01 | kill during canonical blob write | no corrupt object admitted | retry or integrity failure |
| H02 | blob committed, metadata transition killed before commit | orphan blob harmless; project head unchanged | retry |
| H03 | metadata references unavailable blob | doctor/read fails closed | CANNOT_CHECK / integrity failure |
| H04 | mutate stored blob bytes | verified read detects digest mismatch | integrity failure |
| H05 | torn episode JSONL tail | historical prefix preserved; typed tail loss | TRUNCATED |
| H06 | delete interior episode record | hash chain identifies first bad index | TAMPERED |
| H07 | concurrent identical idempotency key, identical request | one logical result | exact replay |
| H08 | same idempotency key, different request | key meaning immutable | conflict |
| H09 | two writers plan on same project snapshot | at most one installs next head | loser RETRY_REQUIRED |
| H10 | stale controller decision replayed after semantic mutation | old decision cannot mutate new head | RETRY_REQUIRED / CANNOT_CHECK |
| H11 | saturation certificate basis fingerprint changes | old certificate invalid | reopen / CANNOT_CHECK |
| H12 | new native residual after bounded saturation | only implicated axis/fibre reopens | targeted refresh |
| H13 | delete full-text/vector/graph index | canonical state remains; index rebuildable | degraded/rebuild state |
| H14 | corrupt derived index to return nonexistent atom | referential verification blocks use | CANNOT_CHECK |
| H15 | worker finishes external effect, crashes before completion record | non-idempotent effect not blindly retried | RECOVERY_REQUIRED |
| H16 | duplicate activity delivery | idempotent activities converge | one semantic outcome |
| H17 | DB failover mid-transition | no partial committed project state | retry/recovery |
| H18 | object store temporary outage | no fabricated missing evidence conclusion | CANNOT_CHECK / retry |
| H19 | restore backup into empty environment | frozen snapshot identities reproduce | PASS or restore failure |
| H20 | point-in-time replay to older snapshot | exact historical status can be reconstructed | PASS |
| H21 | partial schema migration | mixed-version state not silently served | migration block/rollback |
| H22 | rollback after failed migration | old fixtures byte/semantic equal | PASS |
| H23 | secret rotation during worker lifetime | no secret in receipt/log; declared revision changes as required | PASS / worker restart |
| H24 | infrastructure admin submits unverified scientific promotion | infra role cannot bypass RAKL governance | BLOCKED |
| H25 | malicious fabricated hard-gate ID in status | receipt lookup/authority binding fails | CANNOT_CHECK |
| H26 | clock skew on worker | ordering depends on sequence/history, not wall clock alone | PASS / bounded warning |
| H27 | execution artifact rebuilt from different source but same label | build provenance distinguishes artifact | BLOCKED |
| H28 | audit/log exporter unavailable | scientific transition semantics do not change silently | degraded observability + explicit health |
| H29 | high transaction contention | bounded retry/latency envelope measured | PASS / PERFORMANCE_ENVELOPE_EXCEEDED |
| H30 | huge knowledge lattice + context request | active/prompt capacity guards fail closed | compact/demote/CANNOT_COMPILE |

## Fresh assurance rule

Development failures may be used to repair the implementation, but the final release terminal must be produced from a reset environment and a frozen hostile packet. A repair cannot rewrite the failed predecessor result.
