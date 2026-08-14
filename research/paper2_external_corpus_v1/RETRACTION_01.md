# RETRACTION_01 — the "missing v3/v4 receipt" finding was a false positive

Date: 2026-08-15. Retracts a claim made in commit `0e8b79e1` and in the original
body of PR #709.

## What was claimed

That PRs #703 and #707 state `results_v3_reducer/RESULT.json` and
`results_v4_reducer/RESULT.json` are committed while "neither path exists on its
branch", and that this was a governance defect of the class where a result is
merged without its receipt chain.

## Why it was wrong

The check was run against **stale local refs**. `arn/v3-instance-paired-reducer`
and `arn/v4-relational-reducer` existed in the local repository at commits
predating the actual pull-request heads, and `git ls-tree` on a stale ref
answers truthfully about the wrong object. Verified against the real heads:

```
refs/pull/703/head  ef42786e  -> results_v3_reducer/{ACQUISITION_RECEIPT,MAPPING,RESULT}.json  PRESENT
refs/pull/707/head  5d2d332b  -> results_v4_reducer/{ACQUISITION_RECEIPT,MAPPING,RESULT}.json  PRESENT
origin/main                    -> results_v2_reducer/, results_v3_reducer/, results_v4_reducer/  ALL PRESENT
```

Both PRs are merged. The receipts were never missing.

## The rule this broke

An absence claim needs a search whose *scope* is justified, not merely one that
returned nothing. A local branch name is not the pull request it shares a name
with, and the difference is invisible in the output. The correct check was
`refs/pull/<n>/head`, which was available the whole time. A warning that local
`arn/*` refs were stale relative to the PR heads had already been raised in this
session and was not acted on.

## What survives

The re-executions themselves, and they are worth more as what they actually are
than as what they were claimed to be. The committed receipts on `main` and the
receipts produced by re-running the committed runners against the committed
corpus are **byte-identical**:

| artifact | `origin/main` sha256 (first 16) | independent re-execution |
|---|---|---|
| `results_v3_reducer/RESULT.json` | `c7ebb5c4ea693ab4` | `c7ebb5c4ea693ab4` |
| `results_v4_reducer/RESULT.json` | `d835781472b30164` | `d835781472b30164` |

That is an independent reproduction of both epochs, not a repair of a missing
artifact. The files this branch adds are identical to the ones already on `main`.

## What is unaffected

Nothing else in this branch depended on the retracted claim. The B3 abstention
derivation, its two-sided known-answer validation, the withdrawal of v4's
`INSTRUMENT_NOT_PROBATIVE` reading, the v5 multi-family epoch and its cross-host
reproduction all rest on measurements, not on where a file was committed. In
particular the v4 closure — measured `CANNOT_CHECK` rate 0.5629, identity
prediction 0.1297, recorded advantage 0.1347 — was computed from the receipt
content, which was correct in both places.
