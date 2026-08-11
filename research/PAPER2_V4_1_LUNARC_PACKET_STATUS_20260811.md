# Paper 2 V4.1 LUNARC execution packet

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

## Current authority and next action

Verdict: `READY_AFTER_MERGE_NOT_SUBMITTED`.  This means the code packet is ready
for post-merge execution; it is not a native readiness or result claim.  Counts
remain one planned job, zero submitted V4.1 jobs, zero V4.1 executions, zero
evaluated V4.1 task/seed units and zero quantitative figures.

After exact CI and merge, synchronize a new clean detached LUNARC checkout to
the exact merged SHA, run the V4.1 submission wrapper once, wait for terminal
SLURM state and harvest the exact receipts.  Preserve any parser null or other
failure.  Do not report an arm comparison from this one adaptive task/seed
replay.  The broader matched architecture-by-evidence-access study remains
open.

The review in
`PAPER2_V4_1_LUNARC_INTERNAL_REVIEW_20260811.json` is same-context internal
review, not independent review or peer review.
