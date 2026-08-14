# SELF_RAKL_RESEARCH_* Seed-Corpus Migration Receipt (v1)

Object: PLAN.md P2.1 — migrate the de facto durable episode record (the
hand-curated `research/SELF_RAKL_RESEARCH_*` file receipts identified by
`research/orion_architecture_audit_v1/AUDIT.md`) into the durable episode
store (`src/rakl/episode_store.py`) as the seed corpus for P2.2.

Migration code: `research/self_rakl_seed_corpus_v1/migrate.py`
(deterministic; run via `python3 research/self_rakl_seed_corpus_v1/migrate.py`).
Tests: `research/self_rakl_seed_corpus_v1/test_migrate.py` (8 passed).

## Authority disclaimer

**Ingestion grants nothing.** Every stored episode is
`PROPOSAL_SHADOW_STORED` and was admitted only through the existing
proposal-only flow (`rakl.episode_admission.retain_proposal_shadow_episode`,
verdict `SHADOW_RETAINED` for all 139). No episode is canonical-inventory
admitted; the store contains zero `ADMISSION_RECEIPT` records; storage never
upgrades admission. The raw `research/SELF_RAKL_RESEARCH_*` files remain the
immutable, canonical evidence roots — they were not modified or moved, and
every episode binds its source by repo-relative path + content sha256 in
`evidence_pointers`. Store membership, paths and filenames are not authority
mechanisms.

## Counts (sum invariant: 139 + 7 = 146)

| Quantity | Value |
| --- | --- |
| Inventory (files matching `research/SELF_RAKL_RESEARCH_*`) | 146 |
| Ingested as episodes | 139 |
| Skipped (typed) | 7 |

## Store verification

| Item | Value |
| --- | --- |
| Store file | `research/self_rakl_seed_corpus_v1/seed_corpus.jsonl` |
| Records | 139 (all `EPISODE`) |
| Head hash | `7113f24bbed5b93c0197069078fff9e7189dee0b912fd7d65e35ef16e4c55396` |
| `verify_episode_store(..., expected_head_hash=head)` | `VALID` |
| Determinism | two independent runs produced byte-identical store + sidecars |

Sidecars (derived, deterministic):
`skip_list.json` (typed skip-list), `admission_receipts.json` (139 shadow
admission receipts, `inventory_registry_id = shadow:self_rakl_seed_corpus_v1`).

## Skip-list (CANNOT_PARSE / NO_RECOVERABLE_DATE are first-class outcomes)

No file failed to parse (`CANNOT_PARSE`: 0; the path is exercised by tests).
7 files were skipped as `NO_RECOVERABLE_DATE`: they contain no dedicated date
field (json top-level `date`/`frozen_at`) or `Date:` line, times are derived
from receipt content only, and `TaskEpisode.timestamp` is mandatory-valid in
the store schema — so an UNKNOWN date is unrepresentable as a stored episode
and fabricating one is forbidden. The raw files remain un-migrated evidence
roots.

| File | Reason |
| --- | --- |
| `research/SELF_RAKL_RESEARCH_003.md` | NO_RECOVERABLE_DATE |
| `research/SELF_RAKL_RESEARCH_005.md` | NO_RECOVERABLE_DATE |
| `research/SELF_RAKL_RESEARCH_033_RECEIPT.json` | NO_RECOVERABLE_DATE |
| `research/SELF_RAKL_RESEARCH_033_VALIDATION.json` | NO_RECOVERABLE_DATE |
| `research/SELF_RAKL_RESEARCH_036_VALIDATION.json` | NO_RECOVERABLE_DATE |
| `research/SELF_RAKL_RESEARCH_042.md` | NO_RECOVERABLE_DATE |
| `research/SELF_RAKL_RESEARCH_045_RESEARCH_MACHINE_WORKFLOW_V2.md` | NO_RECOVERABLE_DATE |

## Mapping design (from observed field variance, not one example)

Corpus variance (surveyed across all 146 files): 43 markdown study records
(39 with `Date:` lines) and 103 JSON sidecars in 9 id-key shapes
(`receipt_id` 29, `benchmark_id` 35, `validation_id` 26, `erratum_id` 3,
`pointer_id`/`supplement_id`/`fiber_id` 6, no id key 3).

* Identity (bookkeeping only, never authority): `episode_id` = filename stem;
  `task_id` = `SELF_RAKL_RESEARCH_<round>`; `atom_id` = filename role suffix
  (`MAIN`, `RECEIPT`, `FROZEN_BENCHMARK`, `VALIDATION`, `*_ERRATUM`, …).
* Timestamp: json `date`/`frozen_at` field or md `Date:` line only. Date-only
  values are encoded at UTC midnight (day-resolution encoding, declared via a
  `timestamp_source:*` evidence pointer); full timezone-aware values kept
  verbatim. Embedded ISO strings elsewhere in a file are **not** treated as
  dates. No run-time clock is ever consulted.
* Outcome: explicit markers only — `promotion.status == PROMOTED` or a
  top-level `PROMOTED*` status → `SUCCESS` (2 episodes); exact `REFUTED` →
  `FAILURE`; exact `BLOCKED` → `BLOCKED` (0 occurrences of either in this
  corpus); everything else, including all prose statuses, → typed `UNKNOWN`
  (137 episodes). Prose is never interpreted.
* Negative history preserved: `native_process_residual` ids from receipts
  survive into `residual_signature` (e.g.
  `native_process_residual:META_N016_PREPROMOTION_STAGING`); CI run ids
  survive into `verification_ids` (`ci_run:<id>`).
* Unrecoverable fields carry typed `UNKNOWN:*` markers (`context_hash`,
  `fibre_snapshot_hash`, `operator_ids`, `action_trace`, `observation_ids`,
  and `verification_ids` when no CI ids exist) — never fabricated values.
  `cost` retains the schema default `0.0` (not recoverable; documented here).

## Residuals (typed)

1. `SCHEMA_GAP`: `TaskEpisode.timestamp` is mandatory-valid, so undated
   receipts are unrepresentable as stored episodes (7 skips). Closing this
   needs either a schema decision or an explicitly licensed cross-file/git
   date-derivation rule — not licensed in this fiber.
2. `UNMIGRATED_VALIDATION_EVIDENCE`: `SELF_RAKL_RESEARCH_033_VALIDATION.json`
   (status `PROMOTED_SCOPED_SUPPORT_VALIDATED`), `033_RECEIPT` and
   `036_VALIDATION` are among the undated skips; their promotion/validation
   evidence exists only in the raw files until residual 1 is resolved.
3. `SHALLOW_EXTRACTION`: `action_trace`/`operator_ids`/`observation_ids` are
   typed UNKNOWN across the corpus; deeper structured extraction from the
   markdown studies would be interpretation and was deliberately not done.
