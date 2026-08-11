# Paper 2 matched empirical state and V4 next iteration

Date: 2026-08-11
Live branch audit: `origin/main@c352c2097fddc2d66432d03774a302d495237061`
Latest Paper-2-affecting audit subject: `af2d0be61522d1f8f657a48daaf6369ff3e44a3e`
Frozen publication parent: `origin/paper/closeout-rakl-framework-20260810@4ecd4ac3f1ef9783409b24b952f2aa5859dd012e`

## Object, QoI and authority

The object is the effect of research-control architecture on valid scientific
success and cost when model, task, evidence access, tools and resource ceiling
are held fixed.  The primary Paper-2 QoI remains the within-evidence-level
architecture contrast and the architecture-by-evidence-access interaction over
the preregistered task panel.  Current empirical authority is **open**: no
matched task result exists on `origin/main`.

The frozen publication branch has not moved from the SHA recorded in the
handoff package.  It correctly reports that deterministic pilot worlds and
software tests are conformance instruments rather than comparative model
evidence.

During this iteration `origin/main` advanced from `af2d0be...` to
`c352c209...` through Paper-1-only commits.  A path-scoped diff found no change
to the Paper-2 protocol, receipt, manuscript or test tree.  The Paper-2 audit
below therefore remains byte-current through the latest Paper-2-affecting
subject `af2d0be...` while recording the newer live branch head separately.

## What later main commits actually achieved

The Paper-2 lineage after the frozen publication parent is additive:

1. `168d7947...` preserved a provider-backed execution preflight that returned
   `CANNOT_CHECK`; it created no evaluated record.
2. `f272a6f9...` froze a one-task pendulum harness with two prompt
   materializations, a local Qwen2.5-0.5B snapshot, deterministic scorer,
   blinding map and result schema.  It remained ready-not-executed.
3. `2fc6457b...`, `8184ed29...` and `1a9d3079...` built and repaired a governed
   LUNARC CPU asset-staging lane and established preflight readiness.
4. `ef4d59ce...` preserved the first native staging failure (HTTP 403) and
   versioned the downloader repair.
5. `e698a0bd...` preserved the second native failure (over-strict archive link
   rejection) and froze the V3.2 safe-extraction repair.
6. `98228ceb...` bound the successful V3.2 staging jobs `3475123/3475124` but
   retained a harvest representation mismatch as `CANNOT_CHECK`.
7. `64529bce...` ingested the V3.2.1 re-harvest pass without submitting a new
   job or executing a model.
8. `2ba0b1dc...` preserved an invalid synthesis timestamp and replaced it with a
   chronology-corrected additive receipt.

The net authoritative result through `af2d0be...` is therefore:

```text
native staging jobs submitted = 6
model executions = 0
evaluated result records = 0
current staging authority = HARVEST_STAGING_PASS
Paper-2 comparative authority = UNEVALUATED
```

The verified native environment is nevertheless material infrastructure: FS9
contains standalone Python 3.11.13, Torch 2.8.0+cpu, Transformers 4.55.0,
Tokenizers 0.21.4, Safetensors 0.6.2 and the eight exact Qwen snapshot files.
A read-only observation through `billy-laptop-old` found the staged receipt at
the registered SHA-256 and the governed remote checkout clean, but still at
`c10ba7a...` rather than a checkout containing this V4 iteration.

## Remaining matched architecture x evidence-access blockers

The pendulum harness is not the preregistered factorial.  It has only
`DIRECT_CORPUS` and `RAKL_CONTEXT`, only `COMPLETE_SEALED` access, one
known-answer task, one small model and one deterministic seed.  It lacks:

- executable, fair strong-parent arms for `RAG_STRONG`, `GENERIC_AGENT` and
  `HYPOTHESIS_EVIDENCE_LOOP` (and a separately assured `RAKL_EVOLVING` arm);
- matched `PUBLIC`, `CURATED` and `COMPLETE_SEALED` manifests for every task;
- a topology-stratified task panel with protected task correctness and hard-gate
  outcomes;
- arm-blind protected evaluation beyond the narrow deterministic pendulum
  scorer;
- repeated seed schedules and model-family robustness;
- task-level acquisition, tool, verification, latency and cost receipts under a
  common ceiling;
- independent reproduction or external scientific review.

These coordinates cannot be inferred from successful staging, green CI or the
one-task bridge.

## Smallest material next discriminator

V4 freezes the smallest run that can create honest native execution evidence
without external labels or secrets: one sealed known-answer task, seed 17, two
prompt-materialization arms, equal complete-sealed evidence, no tools and the
already staged immutable model.  A successful job will emit:

- two exact arm records in the existing result receipt;
- one separate task/seed receipt binding both arm records and their resource and
  score records;
- pre- and post-inference attestations of all eight model/tokenizer files, with
  exact byte counts, hashes and a common canonical snapshot identity;
- scheduler and native-harvest receipts preserving failure as
  `HARVEST_CANNOT_CHECK`.

This is a bridge/engineering discriminator, not a Paper-2 superiority test.  It
tests whether the receipt chain survives real inference before resources are
spent expanding the task panel and strong-parent arms.

## Current V4 state

The execution packet, staged-runtime manifests, batch script, submission
wrapper, harvest wrapper, task/seed builder and batch contract are frozen under
`research/paper2_microtrial_v4/` and `experiments/paper2/lunarc/`.  The
machine-readable readiness receipt is
`PAPER2_V4_FROZEN_BATCH_READINESS_RECEIPT_20260811.json`.

The submission, task/seed, snapshot-attestation and harvest receipts each have a
frozen JSON Schema.  The harvest parser was checked against the actual nested
LUNARC `sacct --json` root-row shape from successful staging job `3475124`
(`state.current`, `exit_code.status` and `exit_code.return_code`).  Packet parent
SHA and the executed checkout head/tree are retained as separate coordinates;
neither is substituted for the other.

Its verdict is `CANNOT_CHECK_NOT_MERGED_NOT_SUBMITTED`.  The artifacts have not
yet passed merge/remote checkout gates; no V4 job has been submitted, no model
has executed, no evaluated task/seed unit exists and no quantitative figure is
warranted.  The same-context hostile protocol review is internal review only,
not independent review or peer review.
