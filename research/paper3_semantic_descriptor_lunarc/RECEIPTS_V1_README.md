# Paper III semantic-descriptor LUNARC execution — preserved artifact bundle v1

Status: `SEMANTIC_CONTROL_DESCRIPTOR_COMPUTED / LABEL_BLIND / CONFIRMATORY_GATE_STILL_BLOCKED / NO_STRUCTURAL_SIGNAL_RESULT / NO_TRAINING_AUTHORIZATION`

This directory preserves the complete allocated-execution evidence for section **A1** of issue #138:
staging the exact frozen `BAAI/bge-reranker-v2-m3` semantic control on LUNARC and computing its
label-blind descriptors under `CONTRACT_V1.json`.

**No contract, schema, evaluator, predicate or gate was modified to obtain this result.**

## Executed chain

Bound subject for every phase: `0c5384e84ac62ab0fe14a7f728a0f68ffd3f2186`
(`HEAD == refs/remotes/origin/main`, clean tree, origin `https://github.com/SzeChunYiu/RAKL.git`,
`frozen_parent_sha f86fb72e…` verified as ancestor, all 16 `CONTRACT_V1.json` bindings matching).

| Phase | Job | Verdict | Elapsed |
|---|---|---|---|
| model stage | `3476291` | `STAGING_PASS_ATOMICALLY_PROMOTED` | 72 s |
| stage harvest | `3476291` | `HARVEST_MODEL_STAGE_PASS` | — |
| descriptor | `3476296` | `DESCRIPTOR_EXECUTION_PASS`, `descriptor_status READY`, 16 records | 36 s |
| descriptor harvest | `3476296` | `HARVEST_DESCRIPTOR_READY` | — |

Account `lu2026-2-51`, partition `lu48`. Descriptor payload SHA-256
`5b33d0e858121b991ea5c2233af903a78342652f9cba048760ce9289a55fba1a`, 16 records, bound in the
execution receipt and re-verified against the copied bytes.

## Label chronology

The descriptor was computed while **zero external labels existed**, and that is proven from both sides:

- `chronology_v1/PRE_DESCRIPTOR_ZERO_LABEL_20260811T140614Z.json` — created before submission,
  after the contract's frozen anchor `2026-08-11T04:48:47Z`.
- descriptor `created_at_utc` `2026-08-11T14:06:26Z`.
- `chronology_v1/POST_DESCRIPTOR_ZERO_LABEL_20260811T140752Z.json` — created after the descriptor,
  `state ZERO_LABELS_OBSERVED`, all counts zero, `label_payload_accessed false`.

Both observations are payload-free. At each point, `research/paper3/annotation/` contained only the
packet, rubric and source sets (no response, adjudication or evaluated-result artifacts) and issue
#43 had zero public responses. Private/coordinator response status is `CANNOT_CHECK` from the public
repository, which is why the chronology is asserted only as "zero labels observed", never as "zero
labels exist".

The execution receipt independently records
`label_access = {external_annotation_accessed: false, adjudication_accessed: false, evaluated_result_accessed: false}`.

## Preserved negative history — do not delete

`receipts_v1/harvest-model-stage-3475389.json` has verdict **`HARVEST_MODEL_STAGE_CANNOT_CHECK`**
with failures `["exact_checkout_sha_mismatch", "origin_main_sha_mismatch"]`, together with its
submission/execution/`sacct` receipts. That is the earlier staging attempt (job `3475389`, subject
`dd2c23a…`) which became unharvestable once `main` advanced 137 commits past its bound subject. It is
kept deliberately: it is the evidence for issue **#144** and it demonstrates the fail-closed
machinery working exactly as designed. It must not be cleaned up to make this bundle look tidy.

The asset that job promoted was **preserved, not deleted**, at
`/projects/hep/fs9/users/scyiu/RAKL-paper3/assets/superseded/stage-3475389-953dc6f…` (2.2 GB) before
re-staging. Re-staging re-downloaded the same pinned revision and re-verified all six files against
the contract's byte lengths and SHA-256 values, so the promoted asset is byte-identical to the
superseded one.

## How #144 was cleared without weakening anything

Issue #144 records that the lane requires the executed subject to be simultaneously the
`expected_repo_sha` of a completed, one-shot staging job and exactly equal to `origin/main`. That was
resolved by **re-running the pipeline correctly at the current subject** — not by relaxing the
predicate, re-freezing the contract, or rewriting a remote-tracking ref, each of which was considered
and rejected. The predicate remains exactly as strict as before.

The ordering constraint #144 identifies is unchanged and still undocumented in the lane: a stage
receipt is only harvestable while `main` has not moved past its subject. That finding stands.

## What this bundle does NOT establish

- **No structural-signal result.** The descriptors are the strong non-structural semantic control's
  outputs only. The witnessed-structure comparison has not been run.
- **No ROC-AUC, average precision, Brier, log-loss, Q2 true-accept or Q3 false-accept.** Those require
  the external annotation gate (#43: annotator A, annotator B, a distinct adjudicator, and a distinct
  external provenance auditor), which has zero responses. `src/rakl/paper3_confirmatory_gate.py` must
  not be run before that gate passes.
- **No training or inference authorization.** `harvest-descriptor-3476296.json` records
  `training_authorized: false`.
- No independent review, no peer review, no publication claim.

Section A1 of #138 is complete. A2 and A3 remain blocked on external human annotation.
