# Paper 2 V3.2.1 native re-harvest — internal hostile review

Date: 2026-08-11

## Independence boundary

This is internal recursive hostile review, not independent review or peer
review. Exact native receipt bytes and scheduler history are authoritative.

## Concern ledger

### P2-V321-NH-B01 — a new job could be hidden as read-only harvest

**Disposition.** The governed repair bootstrap records zero jobs. The V3.2.1
receipt records `jobs_submitted_by_repair: 0`, exact old job ids only, zero
model executions and zero evaluated result records. This scopes the claim to
the governed repair invocation; it does not assert absence of unrelated
out-of-band activity.

### P2-V321-NH-B02 — the positive successor could erase the original cannot-check

**Disposition.** The native pass binds the exact prior receipt SHA-256
`2e2ecd6f...` and reports `prior_negative_history_preserved: true`. The old file
is preserved and the successor uses a distinct schema, path and hash.

### P2-V321-NH-B03 — the result could come from the wrong source or repair checkout

**Disposition.** The receipt binds the preserved source SHA/tree and the merged
repair SHA. The distinct repair bootstrap binds its exact clean detached tree.
Wrong identities are hostile-tested and fail closed.

### P2-V321-NH-B04 — wrapper permission failure could be hidden

**Disposition.** `Permission denied` is retained as a same-session reported
observation because no raw machine log was frozen. The successful command used
an explicit Bash interpreter without changing any evidence. A mode-only
`100755` candidate is prepared, but is not canonical until its exact commit is
checked and merged; validator bytes and the native receipt remain unchanged.

### P2-V321-NH-B05 — staging success could be overstated as empirical success

**Disposition.** Manuscript/status/receipt all state zero model executions and
zero evaluated results. Current authority is staging pass only; the matched
Paper 2 estimand remains unevaluated and no performance figure is generated.

### P2-V321-NH-B06 — pre-reharvest timestamps contradict Git chronology

**Disposition.** An additive discrepancy receipt preserves the invalid 02:35Z
and 02:55Z metadata, binds candidate commit `98228ce...` at 02:25:24Z and the
native result at 02:31:55Z, and uses Git object inclusion rather than those
erroneous fields as freeze authority.

### P2-V321-NH-B07 — paths, schemas and 6/0/0 counts could be self-asserted

**Disposition.** Evidence paths are exact schema constants; tests hash the
declared paths. The post-result receipt binds all three submission receipts and
derives six jobs, zero model executions and zero evaluated result records from
their contents. Review schema roles, paths, pass order and concern ids are exact.

## Verdict

`PASS__NATIVE_HARVEST_STAGING_PASS__EXECUTION_PACKET_NOT_YET_FROZEN`
