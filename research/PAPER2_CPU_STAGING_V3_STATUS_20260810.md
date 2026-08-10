# Paper 2 CPU staging V3 status

Date: 2026-08-10  
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

## Current receipt

`CPU_STAGING_CONSTRUCTION_RECEIPT_V3.json` records:

- verdict `READY_NOT_SUBMITTED`;
- jobs submitted: `0`;
- model executions: `0`;
- evaluated result records: `0`;
- exact contract, manifest, wheel-lock and requirements-lock identities.

No Paper 2 quantitative figure or performance section is changed because there is
no new empirical result. After a separately reviewed merge, the next material
step is the two-phase LUNARC staging run and harvest. Only a successful staging
receipt may authorize freezing a later V3 execution packet; it still cannot
authorize a performance claim by itself.
