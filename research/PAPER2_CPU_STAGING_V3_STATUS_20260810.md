# Paper 2 CPU staging V3 status

Date: 2026-08-10; native update: 2026-08-11
Contract: `PAPER2_CPU_STAGING_V3`

## Evidence boundary

This iteration prepares a **non-executed asset-staging lane** for the sealed,
non-confirmatory Paper 2 pendulum microtrial. It does not execute the model, open
an evaluated output, establish batch success, or support any RAKL performance or
efficiency claim. The Paper 2 manuscript remains empirically open.

## Frozen assets

The contract binds 38 downloadable objects totaling **1,281,513,075 bytes**:

- the exact `python-build-standalone` CPython 3.11.13 archive from release
  `20250604` (48,610,589 bytes; SHA-256
  `13f898a7ac7a54e97d3efd6a958ef5e16e9329bd9639b03fc95146227d18706c`);
- 29 exact CPython-3.11/Linux-x86_64 wheels totaling 233,304,796 bytes;
- the eight exact model/tokenizer files at
  `Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf67be50417f59c2c2f167def9a775`,
  totaling 999,597,690 bytes.

The offline requirements lock contains one equality and one exact wheel hash per
distribution. In particular, PyTorch is frozen as **`torch==2.8.0+cpu`**; the
CPU build suffix is not weakened to `2.8.0`. Direct runtime versions remain
`transformers==4.55.0`, `tokenizers==0.21.4`, and `safetensors==0.6.2`.
The exact 29 downloaded wheel files were internally checked for bytes/hashes and
target-environment dependency closure. This is same-context construction evidence,
not independent supply-chain assurance.

## Two-phase SLURM contract

The default operator mode is `READY_NOT_SUBMITTED`. A later authorized operator
must supply the exact repository SHA explicitly and run from a clean LUNARC login
checkout with an observed account/partition association.

Before any scheduler interaction, `bootstrap_repo_v3.sh` creates the governed
FS9 directory tree and either atomically promotes a new detached checkout of the
exact supplied SHA or verifies that the existing repository is already the exact
clean detached checkout with the canonical GitHub remote. It never silently
updates an existing checkout. The submission wrapper requires the atomic
bootstrap receipt and rechecks the repository identity, cleanliness, detachment
and origin before it can call `sbatch`.

1. `network_probe.sbatch` performs HEAD-only reachability checks for every frozen
   URL and writes an atomic machine-readable receipt. It downloads no asset and
   never invokes the model.
2. `stage_cpu_assets.sbatch` may be submitted only with SLURM
   `afterok:<network-probe-job-id>`. It verifies the probe receipt, downloads every
   object into a new job-specific candidate directory, verifies exact bytes and
   SHA-256, rejects archive links/devices/path escapes, extracts the exact Python
   archive, performs a no-index/no-dependency-resolution hash-locked install,
   and requires exact installed versions.
3. Only after every check passes is the candidate renamed atomically to the frozen
   final FS9 path. The conditional pass record is written inside the candidate
   first and becomes authoritative only when harvested at the final path; the
   rename is the terminal operation, so no fallible receipt rewrite occurs after
   promotion. Existing candidate/final paths fail closed. Any exception preserves
   an already-created candidate and writes a failure receipt under a separate
   failure root; setup failures before candidate creation explicitly receipt that
   no candidate existed.
4. `harvest_cpu_staging_v3.sh` records scheduler history and receipt lineage; it
   does not call the microtrial runner.

The staging promotion is also gated on at least 6,000,000,000 free FS9 bytes,
an exact clean commit/tree/parent-ancestry attestation, `pip check`, equality of
the complete 31-distribution environment (29 locked wheels plus the bundled pip
and setuptools), `pip freeze --all`, exact standalone Python 3.11.13, an x86_64
platform receipt and a CPU Torch smoke check proving `torch.version.cuda is
None` and a CPU tensor device.

## Execution remains deliberately unfrozen

This staging-only iteration does not create or authorize a V3 inference packet.
The V2 packet retains its original environment and path limitations. After a
successful native staging harvest exists, a separate chronology-fresh iteration
must bind the promoted interpreter, full eight-file snapshot, exact native
staging/harvest receipt hashes, semantic preflight and execution wrapper before
any model access. Missing native evidence remains `CANNOT_CHECK`.

Submission failure after the probe job is accepted but before the staging job is
preserved as `PARTIAL_SUBMISSION_FAILURE` with the probe job id. No failed or
partial event is rewritten as success.

The staging job rejects replayed or incomplete probe receipts: the receipt job id
must equal the dependency id supplied by the operator, expected and observed
repository SHAs must match, and all 38 unique frozen artifact ids must have
successful reachability observations. Refused staging writes the same contract,
repository, dependency and SLURM lineage as an execution failure, and harvest
preserves either state as negative evidence only when bootstrap lineage remains
valid.

## Historical construction baseline

Before native execution, `CPU_STAGING_CONSTRUCTION_RECEIPT_V3.json` recorded:

- verdict `READY_NOT_SUBMITTED`;
- jobs submitted: `0`;
- model executions: `0`;
- evaluated result records: `0`;
- exact contract, manifest, wheel-lock and requirements-lock identities.

This was the pre-native baseline. Its then-next steps—preserving and retiring the
dirty checkout, bootstrapping the exact merged repair SHA and repeating the
dry-run—were subsequently completed and are reported in the exact-subject section
below. No Paper 2 quantitative figure or performance section changed because
neither the construction baseline nor the later dry-run is empirical evidence.
Only successful native staging and harvest may authorize freezing a later V3
execution packet; they still cannot authorize a performance claim by themselves.

## Native bootstrap and submission dry-run update

The first native LUNARC operator pass used the exact merged subject
`2fc6457bce764baef01bca6b19c5a9e053f702f4`. Its atomic bootstrap receipt,
preserved as
`research/paper2_microtrial_v3/native_receipts/BOOTSTRAP_NATIVE_2FC6457B.json`, has
SHA-256 `6c76c22ecc36f36c7b42ed998b819d5c91d8306de1095597069d234092453fdf`
and verdict `BOOTSTRAP_PASS_ATOMICALLY_PROMOTED`. This is native checkout
bootstrap evidence only: it is not asset-staging success, model execution, or
Paper 2 empirical evidence.

The subsequent submission dry-run failed closed before `sbatch` and job submission.
Its preserved receipt,
`research/paper2_microtrial_v3/native_receipts/SUBMISSION_DRYRUN_NATIVE_2FC6457B.json`,
has SHA-256
`5e102ec6e1d0f6145e4c19d5e45f989c30fd236a4d7975d0de05c2aa84b1f445`,
verdict `REFUSE_PREFLIGHT_VALIDATION`, failure `checkout_not_clean`, and no
submitted job ids. The shell wrapper observed the checkout as clean, then its
repository-module invocation wrote Python bytecode under
`src/rakl/__pycache__` before the Python-side Git observation. The Python
preflight correctly treated that newly dirty checkout as a falsifier rather
than proceeding.

The repair sets `PYTHONDONTWRITEBYTECODE=1` on every repository-module Python
invocation in the submission, network-probe, staging and harvest paths. It does
not reinterpret the refusal as a pass. The repaired scripts and regenerated contract subsequently passed exact CI
and the post-merge native bootstrap/dry-run reported below. That later result closes
the preflight residual but is not native staging success.

A read-only native observation at `2026-08-10T23:41:29Z`, preserved as
`research/paper2_microtrial_v3/native_receipts/REMOTE_DIRTY_CHECKOUT_OBSERVATION_NATIVE_2FC6457B.json`
with SHA-256
`f58bdc2646b055c4e048f5ffe75d17195c047a9efb3541356ba639dc11aa4921`,
found zero tracked changes and exactly 24 untracked
`src/rakl/__pycache__/*.pyc` files at the exact `2fc6457b...` checkout. Exact
paths and byte hashes are retained in that receipt. This bounded native sequence
supports bytecode generation as a sufficient observed mechanism; it does not
claim bytecode was the sole possible mutation at the earlier refusal time. The remote checkout remained negative-history evidence with the observed
bytecode dirt. It was later quarantined without cleaning or reuse, and the exact current
status and file hashes were re-observed against the prior receipt as reported
below.

Across this native update, jobs submitted, model executions and evaluated
result records all remain **zero**. No inference packet exists, no evaluated
output was opened, and no empirical or performance claim is licensed.

## Exact merged-subject native preflight readiness

After PR #51 merged, the post-repair native pass used exact subject
`8184ed2960078102a6b5c25221dd26fc01f03a7a`. The atomic bootstrap receipt at
`research/paper2_microtrial_v3/native_receipts/BOOTSTRAP_NATIVE_8184ED2.json`
has SHA-256
`fa6fe7b716da221419005001dd26d75a5ecf11f335168282c501e2bd81f0db02`,
verdict `BOOTSTRAP_PASS_ATOMICALLY_PROMOTED`, a clean detached checkout and the
exact observed tree `b743cb72655111e5d850ecdaed84fad8ee57b999`.

The governed submission dry-run receipt at
`research/paper2_microtrial_v3/native_receipts/SUBMISSION_DRYRUN_NATIVE_8184ED2.json`
has SHA-256
`b5120b4ff2179a962ab41c6a81861fcc6867b10176a7a97f594f346702065c09`,
verdict `READY_NOT_SUBMITTED`, no failures, no submitted job ids and the exact
contract canonical SHA-256
`22cee21eacefacae2af44c735ce37e73efabc41af1bd2952089e8fcb7ca0f2a1`.
The two `sbatch` command vectors are plans recorded by the receipt; they were not
executed.

A read-only observation found the prior dirty `2fc6457b...` checkout preserved
at
`/projects/hep/fs9/users/scyiu/RAKL-paper2/failures/v3/repo-dirty-2fc6457bce764baef01bca6b19c5a9e053f702f4`
with its 24 status entries, while the active `8184ed2...` checkout had zero
status entries. The machine-readable observation receipt has SHA-256
`8635afd77787b809f1ea356479e38d8f103a0dc88154938b4971442761944efe`.
This preserves rather than erases the earlier refusal lineage.

The synthesis receipt
`PAPER2_NATIVE_STAGING_PREFLIGHT_READINESS_RECEIPT_20260811.json` has verdict
`NATIVE_PREFLIGHT_READY_NOT_SUBMITTED__PRIOR_FALSIFIER_PRESERVED`. Across this
result, jobs submitted, model executions and evaluated result records remain
**zero**. Native asset staging, harvest, an execution packet and empirical or
performance evidence remain absent. A separately reviewed and merged iteration
is required before any staging-only job submission.
