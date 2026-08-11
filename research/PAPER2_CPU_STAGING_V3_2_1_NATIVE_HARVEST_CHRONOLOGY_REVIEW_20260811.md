# Paper 2 V3.2.1 post-harvest synthesis chronology — internal hostile review

Date: 2026-08-11

## Independence boundary

This is same-context internal recursive hostile review, not independent review
or peer review. Exact receipt bytes and Git object inclusion are authoritative.

## Concern P2-V321-NH-B08 — the synthesis predates a bound dependency

The preserved V1 synthesis records `created_at_utc: 02:34:00Z` while binding
exact bytes of a discrepancy receipt created at `02:42:19.753852Z`. Its exact
final bytes first entered Git in commit `64529bc...` at `02:47:21Z`. The V1
creation field is therefore impossible and cannot establish chronology.

## Disposition

The invalid V1 remains immutable negative metadata history at SHA-256
`969f7dc5109d66e77b0649c89d749adf16e62cc14d4d7d9816bb3369481c81ab`.
A separate machine-readable discrepancy receipt records the failure. A distinct
chronology-corrected synthesis was created after the dependency, V1 Git freeze,
and discrepancy receipt. Tests parse the timestamps and require this ordering.
No native evidence was changed, no job was submitted, no model was executed,
and no evaluated result was created.

## Verdict

`PASS__NATIVE_HARVEST_STAGING_PASS__CHRONOLOGY_CORRECTED__EXECUTION_PACKET_NOT_YET_FROZEN`

This closes only concern B08 after additive correction. It does not warrant any
Paper 2 empirical claim or quantitative figure.
