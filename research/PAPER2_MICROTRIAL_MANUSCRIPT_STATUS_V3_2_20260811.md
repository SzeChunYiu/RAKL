# Paper 2 sealed pendulum microtrial status through staging V3.2

Date: 2026-08-10; native update: 2026-08-11
Protocol: `PENDULUM_MATCHED_SAME_MODEL_MICROTRIAL_001_EXECUTION_V2`

## Evidence boundary

This lane is a **non-confirmatory engineering microtrial**. It asks whether one
immutable local open model can be run reproducibly on one sealed known-answer
pendulum task under `DIRECT_CORPUS` and `RAKL_CONTEXT`, with identical questions,
seed, evaluator and resource ceilings and with machine-readable output lineage.
It does not establish RAKL superiority, general scientific helpfulness, external
validity or independent review regardless of the eventual arm scores.

The earlier broad Paper 2 architecture-by-evidence programme remains blocked by
fresh confirmatory tasks, fair strong-parent implementations, a protected
task-correctness evaluator, independent replication and complete resource pricing.
This microtrial does not supersede those obligations.

## Frozen execution design

- one sealed eight-source pendulum task;
- seed `17`;
- two arms, `DIRECT_CORPUS` and `RAKL_CONTEXT`;
- exact byte bindings for both materialized prompts, corpus/task, question set,
  evaluator protocol and source, runner, result schema, model and tokenizer
  manifests, execution environment, resource ceiling, blinding map and price
  boundary;
- offline `transformers` inference with `local_files_only=true`,
  `trust_remote_code=false`, no model tools, no retrieval and no repository access
  exposed to the model; these controls constrain Transformers artifact access but
  do not constitute an observed host-level network-isolation receipt;
- raw outputs and separate provider/resource receipts saved by opaque blind id;
  the deterministic scoring function receives only opaque blind ids and raw
  text, and condition labels are joined only after the blinded-score receipt is
  written; the orchestration process necessarily loads the blinding map earlier
  to dispatch the registered prompts, so no process-level or human-blinding
  claim is made;
- execution is restricted to the exact LUNARC FS9 contract under
  `/projects/hep/fs9/users/scyiu/RAKL-paper2`; the immutable model snapshot,
  checkout and output roots are frozen there rather than referring to a local
  macOS cache;
- model inference is forbidden on `cosmos` login hosts and requires a
  syntactically numeric `SLURM_JOB_ID`; this is a guard, not scheduler-backed
  batch attestation. A separately reviewed, byte-bound `sbatch` wrapper and
  scheduler metadata receipt remain required before native execution;
- before either output is opened, the runner requires a clean Git checkout,
  verifies that the packet subject is an ancestor, records the exact checkout
  commit and tree identities, and writes a pre-output run manifest whose hash is
  carried by every raw, provider, resource and final result receipt;
- semantic preflight rejects placeholders, missing mandatory source identities,
  hash drift, evaluator drift, unmatched model/tokenizer revisions and resource
  policies that permit tools or retrieval.
- resource receipts report process-lifetime high-water RSS observed after each
  arm, not an isolated per-arm peak; the frozen ceiling and manuscript language
  use that narrower quantity.
- before writing the final result receipt, a production verifier rejects duplicate
  or incomplete arm identities, cross-record blind-id/prompt/run-manifest drift and
  invalid parse/score states; the bound JSON Schema requires all nine evaluator
  score fields when parsing succeeds.

## Model footprint and monetary boundary

The registered immutable revision is
`Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf67be50417f59c2c2f167def9a775`
under Apache-2.0. The exact registered model plus tokenizer footprint is
**999,597,690 bytes** (953.291 MiB): 988,110,068 model/config/license bytes and
11,487,622 tokenizer bytes.

No provider API transaction is used, so the registered provider-API charge is
USD 0. This is not a zero-total-cost claim. Network charges, electricity,
hardware depreciation/opportunity cost and operator labour remain explicitly
unpriced and prohibit a monetary efficiency conclusion.

## Current readiness result

The model has **not been downloaded or executed** in this construction pass. The
checked-in preflight receipt is therefore `CANNOT_CHECK`, with zero evaluated
result records. It identifies the absent registered FS9 snapshot and execution-environment
version, operating-system and architecture mismatches rather than fabricating outputs or treating missing execution
as a null result.

The packet was re-frozen after a hostile chronology audit found that the prior
checked-in packet and preflight asserted times later than their introducing
commit. The superseding packet records observed UTC times, binds the repaired
runner, enforces strict UTC order (`task seal <= packet freeze <= receipt/run`),
rejects future-dated or reversed event times before output/backend access, and
retains the prior packet hash as supersession lineage. This is a provenance
repair, not an empirical result.

After the exact snapshot and frozen environment are staged, do not reinterpret
the V2 packet as executable. Freeze a chronology-fresh V3 packet and rerun its
semantic preflight. Only a `PASS` may permit model output. The manuscript remains
open for empirical closure after this engineering lane because a one-task
diagnostic cannot replace the matched confirmatory programme.

The registered execution checkout is
`/projects/hep/fs9/users/scyiu/RAKL-paper2/repo`, the model snapshot is under its
sibling `models/` tree and each output must be exactly one new child of
`/projects/hep/fs9/users/scyiu/RAKL-paper2/runs`. These paths are execution
contracts only; their presence is not asserted by the construction receipt.

## V3 CPU staging preparation

A separate staging-only V3 contract now binds the exact standalone CPython
archive, a 29-wheel offline hash lock with `torch==2.8.0+cpu`, and all eight
model/tokenizer files. It adds fail-closed repository bootstrap, network-probe,
dependent staging, submission and harvest scripts with exact-repository-SHA
lineage, atomic promotion and preserved failure/refusal receipts. The checked-in
construction verdict is `READY_NOT_SUBMITTED`: zero jobs, zero model executions
and zero evaluated result records.

This staging iteration does not mutate or supersede the V2 execution packet and
does not authorize inference. A chronology-fresh V3 packet and semantic preflight
may be frozen only after successful native staging and harvest receipts exist.
See `research/PAPER2_CPU_STAGING_V3_STATUS_20260810.md`.

## Native staging-gate result and repair boundary

The first native LUNARC pass at exact merged subject
`2fc6457bce764baef01bca6b19c5a9e053f702f4` produced an atomic bootstrap PASS,
then a fail-closed submission dry-run refusal with failure
`checkout_not_clean`. No SLURM job was submitted. The intervening mutation was
not a scientific result: the wrapper's repository-module Python invocation
created `src/rakl/__pycache__/*.pyc` after the shell cleanliness check but before
the Python-side Git observation. The latter check correctly refused rather than
allowing the changed checkout to reach `sbatch`.

The repair applies `PYTHONDONTWRITEBYTECODE=1` to the repository-module
invocations in the submission, network-probe, staging and harvest paths. The
native refusal remains preserved negative evidence; it is not relabelled as
staging success. Exact CI and the post-merge native bootstrap/dry-run were later
completed against exact merged repair SHA `8184ed2...`, as reported below.

The dirty remote checkout of `2fc6457b...` was quarantined without cleaning or
reuse before that atomic bootstrap. A later read-only exact observation matched
all 24 status entries and bytecode hashes to the prior receipt.

The manuscript evidence state is unchanged: **zero jobs submitted, zero model
executions, and zero evaluated result records**. There is no V3 execution packet,
no inference result, no quantitative Paper 2 figure to update and no empirical
performance or efficiency claim. This status and its hostile review are internal
same-context work, not independent review or independent peer review.

## Post-repair native preflight result

The exact merged repair subject
`8184ed2960078102a6b5c25221dd26fc01f03a7a` passed atomic native bootstrap and
then reached governed verdict `READY_NOT_SUBMITTED` in the submission dry-run.
The active checkout was clean and detached, the contract hash matched, the
failure list and submitted-job-id list were empty, and the planned two-job
`sbatch` vectors were recorded without execution. The prior dirty `2fc6457b...`
checkout remains quarantined with its negative-history status rather than being
silently cleaned or reused.

This closes only the bytecode-mutation preflight residual. It does not establish
native asset staging, successful harvest, model availability, execution-packet
readiness, inference correctness, performance or efficiency. Jobs submitted,
model executions and evaluated result records remain **zero**. Therefore no
quantitative figure or empirical manuscript claim changes. The next admissible
step is a separately reviewed staging-only submission and receipt harvest after
this readiness evidence merges; a chronology-fresh V3 execution packet remains
blocked on successful native staging and harvest receipts.

This update and its hostile review are internal same-context work, not
independent review or peer review.

## Native V3 staging failure and V3.1 repair

The subsequently authorized staging-only pass at exact subject
`1a9d3079571e1f1278e32061665be885845bd5cf` submitted two jobs and no model
run. Job `3475080` completed its bounded network probe with 38/38 HTTP-200 HEAD
observations. Job `3475081` then failed during GET-based staging with HTTP 403;
the failed candidate was preserved and the final asset path was not created.
Both chronological harvest receipts retain the negative scheduler result.

Read-only localization found the exact Python archive and first 24 wheels
through Tokenizers present and hash-matching. The first missing manifest entry
was `torch==2.8.0+cpu`. That ordering is a bounded inference about the likely
active request because the V3 failure receipt did not record artifact identity;
it is not direct proof. The repair therefore does not alter V3 in place. A new
V3.1 runtime applies the probe's bound User-Agent to GET and makes future 403
receipts artifact- and status-specific while preserving the V3 candidate and
contract unchanged.

The first recursive internal review of V3.1 found that a negative harvest could
be labelled preserved despite absent scheduler rows or contradictory candidate
observations. The successor now fails closed unless both submitted root rows,
exact job-id lineage and path-presence facts match. Planted missing and
contradictory worlds return `HARVEST_CANNOT_CHECK`; the original V3 native
receipts are not reinterpreted by this software correction.

V3.1 is locally `REPAIR_READY_NOT_SUBMITTED`; no retry has been submitted and
no native V3.1 success exists. Exact counts for the material native tranche are
two staging-only jobs, zero model executions and zero evaluated result records.
Consequently the manuscript still has no microtrial outcome, no performance or
efficiency estimate, and no quantitative result figure. A chronology-fresh
execution packet remains blocked on successful native V3.1 staging and harvest.
This update and its recursive hostile review are internal same-context work,
not independent review or peer review.

## Native V3.1 retry and archive-policy residual

The post-merge V3.1 retry at exact subject `9d6ee25c...` again submitted only a
network probe and dependent staging job. Probe `3475098` completed, while stage
`3475099` failed before promotion with
`archive unsafe member:python/bin/2to3`. The candidate remains preserved, the
final path is absent, and the harvest retains the failure as negative history.

This retry closes the HTTP-download uncertainty but not staging: all 38 frozen
artifacts are present and exact, including the 1.0 GB model snapshot. A read-only
archive inventory found 1,048 symbolic links, all resolving to existing regular
file members inside the archive root, with no hard links or special members.
V3.1's categorical link rejection was therefore too coarse for this exact
trusted archive. The versioned V3.2 successor permits only prevalidated in-root,
acyclic relative links and retains strict rejection of escape and special-file
worlds.

No V3.2 retry has been submitted. The exact scientific boundary remains four
staging-only jobs across V3/V3.1, zero model executions and zero evaluated
result records. There is still no microtrial outcome, performance/efficiency
estimate or quantitative result figure. This update and review are internal
same-context work, not independent review or peer review.

The post-result internal review found and closed a harvest-assurance blocker:
the first V3.2 draft could accept semantically empty positive receipts. The
repaired harvest and schemas now require the exact probe, artifact, environment,
repository and smoke-test evidence and return `HARVEST_CANNOT_CHECK` for the
planted exploit. This software assurance change does not add any model result,
does not authorize a V3.2 job, and does not alter the manuscript's empirical
claim boundary.

The next hostile recursion corrected the expected native `pip check` success
receipt and bound harvest to the exact contract, source submission bytes,
bootstrap semantics, governed roots and clean repository identity. Planted
contract/bootstrap mismatches now fail closed. This remains staging-software
assurance, not empirical manuscript evidence.

The final hostile assurance recursion also restricted bootstrap success to the
two exact governed verdicts and required the exact 31-distribution freeze and
frozen FS9 capacity threshold before a positive harvest. These additional
fail-closed checks do not change any Paper 2 result or figure.
