# Paper 2 V4.1 LUNARC execution and native result

Date: 2026-08-11

## Object, QoI and chronology

The object is one fresh native replay of the sealed pendulum task at seed 17
under `DIRECT_CORPUS` and `RAKL_CONTEXT`, using the same model, prompts,
evidence, evaluator and ceilings as V4.  The only versioned intervention is the
already frozen V4.1 serialization policy: accept bare JSON or exactly one
lowercase newline-delimited `json` fence, and reject all nonexact forms.

This is an **adaptive non-confirmatory replay fresh only to V4.1 outputs**.  The
V4 outputs and both frozen parser failures were known before the V4.1 parser and
this batch packet were frozen.  No V4.1 model output existed at either freeze.
V4 job `3475193` remains two parse-invalid null scores and is not re-scored.

The narrow QoI is whether a fresh native run can produce a complete,
schema-parseable task/seed receipt under that exact predeclared normalizer.  It
is not whether either arm wins and it is not the matched Paper-2 estimand.

## Frozen batch lane

The additive contract
`research/paper2_microtrial_v4_1/BATCH_CONTRACT_V4_1.json` binds the exact V4.1
packet, normalization contract and runner, V4 negative-history ingest, parent
runner, batch/submit/harvest programs, receipt builders and schemas, staged
model/tokenizer manifests and pre/post attester.

Submission requires an operator-supplied exact merged SHA, a clean canonical
checkout with `HEAD == refs/remotes/origin/main == EXPECTED_REPO_SHA`, and the
V4.1 packet parent as an ancestor.  The allocated job repeats
those checks, re-hashes every batch-contract binding, checks the adaptive
chronology and V4 non-reinterpretation state, and requires semantic preflight
`PASS` before inference.  All eight model/tokenizer files are attested before
and after inference; the post attestation binds the result receipt.  The
submission receipt must match the executed checkout head during harvest.

V4.1 uses separate FS9 paths:

- runs: `/projects/hep/fs9/users/scyiu/RAKL-paper2/runs/v4_1`;
- receipts: `/projects/hep/fs9/users/scyiu/RAKL-paper2/receipts/v4_1`;
- logs: `/projects/hep/fs9/users/scyiu/RAKL-paper2/logs/v4_1`.

The task/seed receipt records the exact packet, run manifest, result,
normalizer, normalization contract, both snapshot attestations, two raw-output
hashes, resource coordinates and parse/score states.  The harvest fails closed
on missing or ambiguous scheduler, submission, preflight, checkout, packet,
normalizer, result, task/seed or attestation lineage.

## Native result and current authority

The packet merged through PR 77.  The canonical FS9 checkout was then detached
cleanly at merged `origin/main@4a8d5ff19e3e6b26b95cb7408bbf55475208989c`,
whose tree is `1ba49edbf23d46fcc8105f96d0dc45c286c3a9c5` and which
contains packet head `f3211f86d1b7665e44cfa08fa4ec6e257d77c9eb` as an
ancestor.  Exactly one V4.1 batch was submitted.  Native LUNARC job `3475212`
completed on `cn004` in 54 scheduler seconds with return code zero.  Its
allocated-node preflight passed, the clean checkout coordinates agree across
the run, result, task--seed and harvest records, and all eight staged
model/tokenizer files have identical pre/post byte attestations.  The governed
harvest verdict is `HARVEST_V4_1_TASK_SEED_PASS_NONCONFIRMATORY` with no receipt
failure.

The result is a partial parser-engineering pass, not an arm comparison.  Of the
two frozen arm records, `RAKL_CONTEXT` is parse-valid and scorable under the
exact single-fence policy, but it answers only 3 of 5 conceptual fields
correctly and therefore fails the exact conceptual gate.  `DIRECT_CORPUS`
again emits a JSON fence followed by prose and remains parse-invalid with a
null score.  Thus V4.1 has one evaluated task--seed unit, two arm records, one
parse-valid/scorable arm and **zero exact conceptual passes**.  One scorable arm
cannot identify a paired contrast.  The local provider API charge is recorded
as zero for both arms, but electricity, hardware depreciation/opportunity cost,
download network charge and operator labour are unpriced, so neither a fully
costed result nor a fully costed cost-per-success comparison is estimable.  By
the frozen zero-success convention, the observed token count per valid
scientific success is infinite for each arm: both consumed positive token
counts and neither produced a valid scientific success.

The admitted input/output-token and wall-time coordinates are 1,140/108 and
15,789 ms for `RAKL_CONTEXT`, and 638/320 and 32,447 ms for
`DIRECT_CORPUS`.  They are execution coordinates only: the latter arm has no
score, neither arm is a valid scientific success, and no efficiency or
superiority claim follows.  No quantitative figure is generated because a
single scorable arm and one task/seed cannot support a comparison, uncertainty
interval or frontier.

The exact repository-ingest authority is
`research/paper2_microtrial_v4_1/PAPER2_V4_1_NATIVE_JOB_3475212_INGEST_RECEIPT_20260811.json`.
It binds the submission (`186a71d0...`), scheduler (`6a47f867...`), harvest
(`f4836e36...`), checkout, allocated preflight, pre/post snapshot, run,
task--seed, raw-output, resource and result bytes plus the immutable V4 negative
parent.  V4 job `3475193` remains two parse-invalid nulls; V4.1 does not rescore
or reinterpret it.

## Typed residual and pre-candidate memory gate

The result leaves both an R1 serialization/interface residual and an R7
scientific-output residual.  Prompt architecture may affect serialization
independently of scientific content; the 0.5B model may be below the exact
structured-reasoning requirement; and one deterministic task/seed cannot
separate architecture effects from task-specific output variance.  Repeatedly
relaxing the parser or rerunning these opened outputs would be a post-result
rescue and is prohibited.

No successor experiment or method candidate is proposed in this result-ingest
iteration.  The V4 and V4.1 failures are now normalized in the global failure
experience lattice and linked through a receipt-bound public research trace.
Before any future Paper-2 candidate is proposed, a dual `ResearchMemoryReview`
must query both that failure lattice and the success-derived research-tool
inventory under the then-current object/context, preserve applicable warnings
or explicit no-match results, and freeze the required pre-candidate review.
Only after that gate may a later iteration select a discriminator.  The
registered matched empirical claim remains open.

The packet review in `PAPER2_V4_1_LUNARC_INTERNAL_REVIEW_20260811.json` and the
result review in `PAPER2_V4_1_NATIVE_INTERNAL_REVIEW_20260811.json` are
same-context internal reviews, not independent review or peer review.
