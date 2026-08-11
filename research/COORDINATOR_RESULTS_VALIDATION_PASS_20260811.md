# Coordinator results-validation pass (2026-08-11)

Authority: same-session coordinator audit over FS9/LUNARC receipts already
harvested and (where applicable) ingested on `origin/main`. This is **not**
independent review, peer review, or a paper-number promotion.

Fail-closed external gates observed at pass time:

- GitHub issue [#41](https://github.com/SzeChunYiu/RAKL/issues/41): open, **0**
  public responses → no Paper 1 independent-review claim.
- GitHub issue [#43](https://github.com/SzeChunYiu/RAKL/issues/43): open, **0**
  public responses → no Paper 3 annotation/adjudication/provenance claim;
  `training_authorized` remains false on all inspected descriptor harvests.

## Framework expectation checklist

| Lane | Framework expectation | Observed | Match? | Paper numbers? |
|------|----------------------|----------|--------|----------------|
| P2 V4.1 harvest chain (3475212, 3476520, 3476521, 3476524) | Exact receipt/subject/attestation chain may pass without granting arm win/loss | `HARVEST_V4_1_TASK_SEED_PASS_NONCONFIRMATORY` on all four | YES | **No** promotional metrics |
| P2 V4.1 scientific gate | Exact conceptual pass required for valid success; nulls preserved | `exact_conceptual_pass_arm_count=0`, `valid_scientific_success_arm_count=0`; DIRECT_CORPUS parse-null; RAKL_CONTEXT scorable **3/5** fail exact gate | YES (negative preserved) | **Blocked** — do not write win/loss or paired-effect numbers |
| P2 V3.2 staging (3476523, 3476526) | Re-stage refused when candidate/final already exists | `STAGING_REFUSED` / `candidate_or_final_already_exists` | YES | N/A — do **not** thrash-resubmit |
| P2 #166 inference validation | Pytest + null-sim on FS9 runtime; methodology-only | 3476530 `FAIL_TESTS` (missing `pytest` in CPU runtime); 3476533 supersession `PASS` after deps staging | YES after repair | Methodology only; not empirical RESET/LEARNING |
| P3 semantic stage (3476519) | Model stage harvest before descriptor | `HARVEST_MODEL_STAGE_PASS`; `training_authorized=false` | YES | No training claim |
| P3 descriptor (3476527–3476529) | Descriptor may be READY; train only with #43 + authorization | `HARVEST_DESCRIPTOR_READY`, 16 records, `training_authorized=false` | YES | **No** train/inference promotion |

## Root-cause ledger (negatives)

1. **V4.1 zero exact successes (systematic across tip `787c7e0` jobs)**  
   - Signature: one arm parse-invalid; other arm 3/5 conceptual, exact pass false.  
   - Selected diagnosis (already in failure lattice): joint R1 serialization + R7
     scientific-output residual under Qwen2.5-0.5B-Instruct / seed 17.  
   - Disposition: preserve nulls; **no paper metric update**; successor only after
     dual-memory / pre-candidate gates (typed residual already says
     `CANNOT_PROPOSE_UNTIL_DUAL_MEMORY_REVIEW`).

2. **#166 job 3476530 `FAIL_TESTS`**  
   - Root cause: FS9 Paper-2 CPU runtime lacked `pytest`
     (`No module named pytest`) while null-sim itself completed.  
   - Fix/resubmit: job **3476533** staged pydeps and recorded `verdict=PASS`
     (`supersedes_job_id=3476530`).  

3. **Staging 3476523 / 3476526**  
   - Root cause: assets already present → intentional refuse.  
   - Disposition: keep as negative history; no resubmit.

## Paper-update gate (this pass)

**NO paper-update PR authorized.**

Reasons:

- No validated promotional / confirmatory metrics that beat the frozen exact
  conceptual gate.
- V4.1 tip reruns reproduce the same non-confirmatory residual as 3475212.
- #41/#43 remain empty → fail-closed on independent review and Paper 3 labels.
- Descriptor READY ≠ training authorized.

Allowed manuscript moves later: truthful negative-history / non-confirmatory
wording only after a separate publication PR that cites these exact receipts —
still not “latest win numbers.”

## Unblockers landed during this coordination window

Merged on `main` (squash):

- [#206](https://github.com/SzeChunYiu/RAKL/pull/206) CI speedups
- [#192](https://github.com/SzeChunYiu/RAKL/pull/192) V4.1 ingest `job_id` parameterization + tip ingest path
- [#190](https://github.com/SzeChunYiu/RAKL/pull/190) Paper 3 subject-binding freeze window
- [#198](https://github.com/SzeChunYiu/RAKL/pull/198) Paper 2 ALR protocol/result stub
- [#196](https://github.com/SzeChunYiu/RAKL/pull/196) terminology inventory
- [#193](https://github.com/SzeChunYiu/RAKL/pull/193) #166 LUNARC validation documentation
- [#197](https://github.com/SzeChunYiu/RAKL/pull/197) tip-rebind harvest receipts

Evidence pointers:

- `research/paper2_microtrial_v4_1/PAPER2_V4_1_NATIVE_JOB_347652{0,1,4}_INGEST_RECEIPT_20260811.json`
- `research/PAPER2_V4_1_NATIVE_JOBS_3476520_3476521_3476524_INGEST_STATUS_20260811.md`
- `research/paper2_microtrial_v4_1/PAPER2_V4_V4_1_FAILURE_EXPERIENCE_LATTICE_20260811.json`
- FS9: `/projects/hep/fs9/users/scyiu/RAKL-paper2/receipts/...` and
  `.../RAKL-paper3/semantic_descriptor_v1/receipts/...`

## Pass verdict

`RESULTS_VALIDATION_PASS__NEGATIVES_MATCH_FRAMEWORK__PAPER_NUMBERS_BLOCKED`

Pipeline bugs with authorized repair were already resubmitted (#166 → 3476533).
No further blind compute resubmit is authorized from this pass alone.
