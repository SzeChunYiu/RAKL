# Paper 2 CPU staging V3.2.1 native harvest status

Date: 2026-08-11

## Object and claim boundary

This tranche re-reads the exact already-completed V3.2 scheduler and receipt
chain with the merged additive V3.2.1 parser repair. It submits no job, executes
no model and reads no evaluated microtrial result. It is staging-chain evidence,
not performance or efficiency evidence, independent review, peer review,
acceptance or publication.

## Exact merged repair subject

PR #63 merged as `3db76e37c6e8a72fad32a38bc28aef2f093a5152`; exact CI passed
11/11 checks and trusted-parent run `31452566656` returned `valid=true` for the
candidate. A distinct clean detached FS9 checkout was bootstrapped at tree
`80e961f4db739914b773c999034ae3ea1d7f6733`. Its bootstrap receipt has SHA-256
`e9285276c28718ea7fac60fba4cbe358d554377bccc99f49aad1ab225d9302f6` and
records zero jobs and zero model executions.

## Native V3.2.1 harvest

The harvest-only successor returned `HARVEST_STAGING_PASS` for source jobs
`3475123` and `3475124`. Its exact receipt has SHA-256
`8dc6207f771943cc4597ba2504e11e886e55af9ae1901b131100f6baf439824a`.
It binds:

- source SHA `c10ba7a261af02cc42690022226555a3197351ae` and tree
  `4f8053958d9ed4ea6e506ffa6dc8e60ee36715a5`;
- original governed `HARVEST_CANNOT_CHECK` SHA-256
  `2e2ecd6f5cb2ad84f17352fea598b30210de225f745e1d9c13154b8872a03e96`;
- probe, stage, submission and bootstrap hashes;
- exact two `COMPLETED` scheduler rows with exit `0:0`;
- no failure receipt, zero repair-submitted jobs, zero model executions and zero
  evaluated result records.

The old `HARVEST_CANNOT_CHECK` remains immutable negative history. The new
receipt is an additive successor; it does not relabel or delete the prior result.

## Invocation residual

In the same operator session, the first direct wrapper invocation was reported
by the shell as `Permission denied` because the merged script mode was `100644`.
That refusal was not written to a raw machine log, so it is retained as a
same-session reported operational observation rather than promoted as an exact
native receipt. Explicit invocation via `bash harvest_cpu_staging_v3_2_1.sh ...`
then produced the exact native pass above. This branch prepares a mode-only
`100755` candidate; it is not canonical until its exact commit passes CI and is
merged. The mode change is not used to warrant the native harvest result.

The pre-reharvest readiness and internal-review receipts also contain invalid
manually assigned `created_at_utc` values later than the native result. Their
exact bytes were nevertheless frozen in Git candidate commit `98228ce...` at
02:25:24Z, before the 02:31:55Z native harvest. The additive discrepancy receipt
`research/paper2_microtrial_v3/PAPER2_V3_2_1_PRE_REHARVEST_CHRONOLOGY_DISCREPANCY_20260811.json`
preserves the metadata error and makes Git object inclusion the chronology
authority; the erroneous original fields are not silently edited.

## Current authority

`HARVEST_STAGING_PASS__NO_MODEL_EXECUTION__NO_EVALUATED_RESULT`

The machine synthesis is
`research/paper2_microtrial_v3/PAPER2_NATIVE_V3_2_1_HARVEST_PASS_RECEIPT_20260811.json`.
A chronology-fresh execution packet and exact empirical evaluator must be
frozen, reviewed, checked and merged before any separately authorized model
batch. No Paper 2 quantitative performance figure is warranted yet.
