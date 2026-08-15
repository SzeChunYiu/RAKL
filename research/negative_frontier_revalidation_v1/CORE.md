# Negative-frontier revalidation — CORE

**The workable set is 8, not 12.** Four of the twelve `REVIVABLE_LOCAL` negatives carry levers that
have already been exercised — every one of them returning negative, refuted, or not-computable. The
frontier records none of it.

Machine record: `RESULT.json`. Proposal-only: **no record is reclassified here.** Every hit below was
opened and verified by hand before being reported.

## Why this ran

Two records had already turned out stale by accident: `p2-arn-v4`'s lever was refuted by executing
it, and `p3-instrument-inadmissible-ceiling`'s lever had been executed on main without the record
referencing the receipt. Spending revival effort on a discharged lever is the cheapest avoidable
waste in the workable set, so the rest were checked the same way.

## The four

| Record | Its lever | What main already shows |
|---|---|---|
| `p2-arn-v4-battery-failed` | remove/instance-pair `role_boost` | **Refuted by execution.** Removing the term moves the leak by 0.000623; the cause is differential abstention (#709), not the scoring term |
| `p3-instrument-inadmissible-ceiling` | compute the oracle ceiling for P3's 0.05 gate | **Executed.** `paper3_lift_ceiling_qualification_v1/CEILING_RECEIPT.json` → `CANNOT_CHECK__ORACLE_NOT_COMPUTABLE_NO_GENERATIVE_MODEL`, all controls passing. It also found no registered 0.05 threshold exists for the lift contrasts |
| `p2-arn-capability-absent` | a capable learned extractor through the admission gate | **Executed.** `PROTOCOL_V5_REDUCER.json` states its purpose as testing *"Paper II's named successor to the deterministic reducer — a capable learned extractor"*; `results_v5_multifamily` → `NEGATIVE__CAPABILITY_ABSENT` |
| `p2-arn-v3-capability-absent` | capable learned extractor under the admission gate | Same v5 epoch, same terminal |

The v5 match is verbatim against the lever text, not an inference from topic overlap.

## Second finding: four records cite receipts absent from main

`p1-source-monitoring-repetition-attack`, `p1-atms-parent-boundary`, `p2-arn-v3-capability-absent`
and `p2-arn-v4-battery-failed` name receipt paths that do not exist on `main`. Verified for the
first: `research/p1_source_identity_repair_v1` is absent because that work sits on an unmerged
branch (PR #718, still open).

A frontier record whose evidence lives on an unmerged branch is not falsifiable by anyone reading
`main`. That is a provenance defect independent of staleness.

## The corrected ledger

| | n |
|---|---|
| `REVIVABLE_LOCAL`, as inventoried | 12 |
| — lever already exercised, did not revive | **4** |
| — effort-bound, support confirmed (`p1-one-claim-not-machine-checked`) | 1 |
| — receipt on an unmerged branch | 1 |
| — genuinely untried locally | **6** |

## What this does and does not establish

It does **not** retract any terminal, and it does not say the four are unrevivable — only that their
*recorded* levers have been tried and did not revive them. A different lever may exist; naming one is
a new epoch with its own freeze.

It does establish that the frontier's `core_lever` field is not maintained against `main`, so the
inventory overstates how much of the workable set is actually open. Any future revival pass should
revalidate before it selects a target.
