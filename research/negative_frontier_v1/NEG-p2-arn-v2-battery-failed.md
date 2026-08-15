# `NEGATIVE__BATTERY_FAILED__INSTRUMENT_NOT_PROBATIVE`

**Paper:** II (successor lineage; NOT in the current manuscript)  
**Class:** `IMMUTABLE_HISTORY`  
**In current manuscript:** no (successor lineage / receipt-level)  
**Artifact immutable:** no

## Where the manuscript states it

Nowhere. This terminal is not in any of the three current manuscripts; it is successor-lineage history recorded only in the repository / open PRs.

## Receipt

- **`receipt_path`:** `NOT_FOUND` — *not verified*
- **No committed result artifact exists.** The v2 terminal is asserted only in the body of PR #703. `gh pr view 703 --json files` lists twelve files and contains NO `results_v2_reducer/` directory; the same directory is absent from the PR #707 head tree (`gh api .../contents/research/paper2_external_corpus_v1?ref=5d2d332b`). Only `PROTOCOL_V2_REDUCER.json` and `scripts/paper2_external_corpus_confirmatory_v2.py` were committed. Local branch refs `arn/v2-*`/`arn/v3-*` are stale relative to the PR head SHAs (local ecce469e vs head ef42786e), so a local `git show` is not a valid check here.
- **Search scope:** Enumerated the complete file list of both open PRs from the GitHub API, and listed the full `research/paper2_external_corpus_v1/` tree at the PR #707 head SHA. `results_v2_reducer/` appears in neither. This is 'checked and absent from the PR heads', not 'could not check'.
- supporting: `PR #703 body (gh pr view 703)`

## What happened

ARN v2 introduced typed extraction and type-preserving partial-credit mapping. Per the PR #703 body: B3_shuffled_gold advantage 0.121, CI [0.091, 0.150] when it should be ~0; the instrument is not probative and the confirmatory gates were not read. **Caveat recorded rather than smoothed:** these numbers have no committed result artifact -- the protocol and runner were committed but `results_v2_reducer/` was not. Treated as CANNOT_CHECK at the artifact level, exactly as Paper III treats the unreproducible 21-family router result.

## One-stage attribution

instrument-construct. PR body: 'The mapping score used label-INDEPENDENT type marginals, so it survived gold shuffling -- a band-similarity proxy, not structural analogy.'

## Lever

v3 instance-paired correspondence scoring, already executed and successful at making the instrument probative. Separately: commit the v2 result artifact, or record the v2 terminal as CANNOT_CHECK.

## Class justification

Preserved as lineage history; v3 is the successor epoch. Classed IMMUTABLE_HISTORY as lineage, but note the artifact gap above -- an uncommitted result cannot be preserved history in the sense the programme's own discipline requires.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
