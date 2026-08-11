# Paper 2 tip-rebind harvest status (tip `5816452`)

Date: 2026-08-11

## Object and claim boundary

FS9 tip-rebind of already-completed staging/harvest and V4.1 native ingest
artifacts onto repository tip
`5816452992cdafa9d61aa5e821d71f7a562001ce`. No new SLURM jobs were submitted.
This is tip-binding / staging-chain evidence only — not microtrial performance,
matched-arm comparison, independent review, peer review, acceptance, or
publication.

## V3.2.1 harvest rebind (jobs `3475123` / `3475124`)

Preserved layout-fail / cannot-check receipt (negative history kept):

- FS9 path:
  `$R/receipts/v3_2_1/harvest-rebind-5816452…-jobs-3475123-3475124.json`
- SHA-256 `8ccc6972f46317dc6e2e1f67a159cbf72380574925ba38e477b81a77e232110c`
- Verdict `HARVEST_CANNOT_CHECK`
- Committed mirror:
  `research/paper2_microtrial_v3/native_receipts/HARVEST_CANNOT_CHECK_TIP_REBIND_5816452_NATIVE_V3_2_1_JOBS_3475123_3475124.json`

Additive PASS successor on the same tip (does not delete the cannot-check):

- FS9 path:
  `$R/receipts/v3_2_1/harvest-rebind-5816452…-jobs-3475123-3475124-pass.json`
- SHA-256 `80b497a26cf3567ad05f632e6d650ef90bb120e3dca5878c5714309d6d66c9d6`
- Verdict `HARVEST_STAGING_PASS`
- `repair_repository_sha` = `5816452992cdafa9d61aa5e821d71f7a562001ce`
- Zero repair-submitted jobs, zero model executions, zero evaluated results
- Committed mirror:
  `research/paper2_microtrial_v3/native_receipts/HARVEST_PASS_TIP_REBIND_5816452_NATIVE_V3_2_1_JOBS_3475123_3475124.json`

Prior native harvest pass on repair subject `3db76e3…` remains immutable
history under
`research/paper2_microtrial_v3/native_receipts/HARVEST_PASS_NATIVE_V3_2_1_JOBS_3475123_3475124.json`.

## V4.1 ingest rebind (preserved job `3475212` only)

- FS9 path:
  `$R/receipts/v4_1/ingest_rebind_5816452…/INGEST_NATIVE_V4_1_JOB_3475212.json`
- SHA-256 `32ec7b8ea2fdc19449f8814d3c37083c9839c187c51e43b0ed0b594484f0a25c`
- Verdict
  `NATIVE_EXECUTION_CHAIN_PASS__ONE_ARM_SCORABLE_NO_EXACT_PASS__COMPARISON_NOT_ESTIMABLE`
- Committed mirror:
  `research/paper2_microtrial_v4_1/native_job_3475212/receipts/v4_1/ingest_rebind_5816452992cdafa9d61aa5e821d71f7a562001ce/INGEST_NATIVE_V4_1_JOB_3475212.json`

Does not touch sibling V4.1 jobs `3476520` / `3476521` / `3476524` (owned by
`fix/paper2-v4-1-native-ingest-job-id`).

`$R` = `/projects/hep/fs9/users/scyiu/RAKL-paper2`
