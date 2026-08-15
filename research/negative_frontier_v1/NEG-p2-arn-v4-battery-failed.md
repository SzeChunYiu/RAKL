# `BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE (PR text says NEGATIVE__BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE)`

**Paper:** II (successor lineage; NOT in the current manuscript)  
**Class:** `REVIVABLE_LOCAL`  
**In current manuscript:** no (successor lineage / receipt-level)  
**Artifact immutable:** no

## Where the manuscript states it

Nowhere. This terminal is not in any of the three current manuscripts; it is successor-lineage history recorded only in the repository / open PRs.

## Receipt

- **`receipt_path`:** `research/paper2_external_corpus_v1/results_v4_reducer/RESULT.json @ PR #707 head 5d2d332b2ed6b4a0a59ca7e53b2e87221be582c9` — **verified present**
- Branch-only, open PR #707. **Local ref `arn/v4-relational-reducer` is stale** (c38a9561); fetch from the PR head. Verified: the artifact's terminal string is `BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE` and the B3 advantage is 0.1346739299610895. **String mismatch preserved:** the PR title and body say `NEGATIVE__BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE`; the artifact omits the `NEGATIVE__` prefix. The artifact string is authoritative.
- supporting: `arn/v4-relational-reducer:research/paper2_external_corpus_v1/PROTOCOL_V4_REDUCER.json`
- supporting: `PR #707 body (gh pr view 707)`

## What happened

v4 aligned relation triples (source_role_type, relation_type, target_role_type) with scoring 0.8*triple_score + 0.2*role_boost. B3_shuffled_gold FAILED: advantage 0.135, CI [0.105, 0.163], g1_fails_as_required false. The run stopped at the battery; no confirmatory gates were read.

## One-stage attribution

instrument-construct. PR body: 'The role_boost component (exact token matches) introduced marginal statistics that survive label shuffling'; triple extraction/scoring failed to maintain the v3 instance-paired property.

## Lever

Restore the v3 instance-paired property -- remove or instance-pair the role_boost term -- before any second-order relational feature is scored. This is a code fix with an already-attributed cause, not a research target.

## Class justification

Deterministic scoring code with a one-line-scope attributed defect. Not a frontier: it is a regression of v3.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
