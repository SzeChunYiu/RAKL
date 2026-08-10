# Paper 2 CPU staging V3 — same-context hostile review

Date: 2026-08-10  
Scope: asset identities, dependency lock, SLURM staging/submission/harvest path,
receipts, and claim boundaries.

## Independence boundary

This is an internal same-context hostile review, **not independent review, not
external peer review, and not model-performance evidence**.

## Findings and dispositions

### P2-V3-H1 — direct-package pins did not close the executable environment

**Finding.** Freezing only Python, Torch, Transformers, Tokenizers and
Safetensors would permit unconstrained transitive resolution on the cluster.

**Resolution.** The V3 lock selects 29 exact compatible wheels, URLs, byte sizes
and SHA-256 identities for CPython 3.11/Linux x86_64. The offline requirements
file contains exact equalities and hashes. Internal downloaded-wheel metadata
checking found zero target-environment dependency gaps. The staging command uses
`--no-index`, a local wheelhouse and `--require-hashes`.

**State:** resolved for the frozen wheel set; independent mirror/build provenance
remains open.

### P2-V3-H2 — `torch==2.8.0` would silently admit a different build

**Finding.** The earlier environment document named `2.8.0`, which does not bind
the registered PyTorch CPU local-version build.

**Resolution.** V3 requires exact equality to `2.8.0+cpu` in the artifact
manifest, wheel lock, requirements lock, installed-version check and tests.

**State:** resolved without weakening equality. The V2 execution packet is not
silently mutated; a later execution requires a separately frozen V3 packet.

### P2-V3-H3 — staging downloads on a compute node may have no network route

**Finding.** Submitting the full 1.28 GB staging job before testing compute-node
reachability could waste allocation time and confound network failure with
artifact identity failure.

**Resolution.** A bounded HEAD-only network probe is a distinct first batch job.
The staging submission carries an exact `afterok` dependency and revalidates the
probe receipt. A successful HEAD is only reachability evidence; a later GET may
still fail, in which case the staging candidate and failure receipt are preserved.

**State:** resolved as a two-phase discriminator, not as a guarantee of download
success.

### P2-V3-H4 — branch construction SHA cannot be the later execution subject

**Finding.** A committed contract cannot self-contain the final commit that
contains it without a circular identity claim.

**Resolution.** The contract records its construction parent. The operator must
supply the exact merged repository SHA at submission; both batch jobs compare the
clean checkout to that supplied SHA. Submission receipts preserve expected and
observed identities.

**State:** resolved by runtime exact-subject attestation; no job has yet provided
that external observation.

### P2-V3-H5 — partial submission and failed candidates could be lost

**Finding.** The probe can be accepted by SLURM while the dependent staging
submission fails. Deleting a failed staging directory would erase diagnostic
history.

**Resolution.** A partial submission receipt retains the probe id. Job-specific
candidate directories are never reused, failures write atomic receipts to a
separate root, and only an all-pass candidate can be atomically renamed to the
final path.

**State:** resolved in software/hostile tests; native behavior remains unexecuted.

### P2-V3-H6 — bootstrapping still trusts the cluster system Python and transport

**Finding.** System Python runs the verifier before the exact standalone Python is
available, and TLS/download infrastructure is outside the repository trust base.

**Disposition.** Every promoted byte is checked against the frozen digest and the
exact standalone interpreter performs the offline install/version check. This
limits but does not eliminate bootstrap/OS/TLS trust. Independent staging or a
prepopulated trusted mirror remains a stronger future assurance route.

**State:** retained external-assurance limitation; blocking for a strong
supply-chain reproducibility claim, not for this bounded staging attempt.

### P2-V3-H7 — an archive digest alone does not make extraction safe

**Finding.** A byte-correct tar archive could still contain absolute paths,
parent traversal, links, devices or FIFOs. A permissive extractor would give the
archive write authority outside the candidate tree.

**Resolution.** The V3 extractor enumerates every member before materialization,
rejects absolute/parent paths, symbolic and hard links, devices, FIFOs and every
non-file/non-directory type, and writes only below the fresh candidate root.
Hostile tests plant each rejected class.

**State:** resolved in software; native extraction remains unexecuted.

### P2-V3-H8 — the FS9 checkout did not yet have a governed bootstrap

**Finding.** A submission contract naming `/repo` is insufficient if that path is
absent, silently updated, dirty, on a branch, or points at a different origin.

**Resolution.** A separate login-host bootstrap requires an exact supplied SHA,
canonical GitHub remote, detached clean checkout and commit/tree identities. A
new checkout is built in a preserved candidate and atomically promoted; an
existing checkout must already match and is never mutated. The operator wrapper
requires and revalidates its atomic JSON receipt before any `sbatch` call.

**State:** resolved in code; the FS9 bootstrap has not been run.

### P2-V3-H9 — direct versions did not prove the promoted runtime

**Finding.** Four direct package versions do not exclude an extra or wrong
transitive distribution, broken metadata, a CUDA-enabled Torch build, a wrong
interpreter, or a wrong host architecture.

**Resolution.** Promotion now requires `pip check`, exact equality of the full
distribution set, `pip freeze --all`, standalone Python 3.11.13 identity, x86_64
platform/libc observation, repository commit/tree/ancestry attestation, free-space
headroom, and a Torch smoke test with exact `2.8.0+cpu`, null CUDA build metadata
and a CPU tensor.

**State:** resolved as a fail-closed native gate; no native receipt exists yet.

### P2-V3-H10 — V2 paths and `torch==2.8.0` cannot authorize V3 execution

**Finding.** Mutating V2 in place would erase chronology, while continuing to use
it would bind the old model path and the wrong Torch version string.

**Disposition.** This PR is narrowed to staging only and deliberately creates no
V3 execution packet. A successor may be frozen only after native staging and
harvest receipts exist, while preserving all original sealed task/evaluator
bindings and supersession lineage.

**State:** retained as a hard execution blocker, not papered over by construction.

### P2-V3-H11 — a nominal probe PASS could be replayed or incomplete

**Finding.** Checking only a verdict and contract hash would admit a receipt from
another probe job or a receipt that omitted unreachable assets.

**Resolution.** Staging now binds the receipt to the exact dependency job id,
expected and observed repository SHA, and exactly 38 unique registered artifact
ids, each with a reachable 2xx/3xx status. Hostile tests plant both a replayed job
id and a truncated observation set. Refusal receipts preserve contract, repo,
probe, current SLURM and failure identities; harvest recognizes refusal as
negative evidence rather than silently losing it.

**State:** resolved in software; native scheduler behavior remains unexecuted.

### P2-V3-H12 — semantic preflight must bind native staging and interpreter lineage

**Finding.** V2-compatible semantic checks alone cannot enforce the promoted
interpreter or prove that staging and harvest passed. Freezing an execution
wrapper before those receipts exist would add untestable chronology and runner
identity obligations to this staging PR.

**Disposition.** No execution packet, semantic-preflight batch job or inference
wrapper is promoted here. The post-staging iteration must validate exact
`sys.executable`, the staging contract, successful staging and harvest receipt
hashes, bootstrap lineage, merged commit/tree and SLURM identity, and must prove
missing or mismatched native evidence refuses before any backend access.

**State:** retained blocker for the next iteration; this staging-only verdict does
not imply inference readiness.

### P2-V3-H13 — setup and post-promotion exceptions escaped the receipt boundary

**Finding.** Repository attestation, manifest loading, free-space inspection and
candidate creation occurred before the staging exception boundary. The earlier
success path also renamed the candidate and then rewrote its receipt, allowing a
post-promotion write failure to escape after the candidate had moved.

**Resolution.** An outer failure boundary now covers every setup and promotion
step and writes a machine-readable negative receipt with candidate/final presence.
The exact pass commit record is written inside the candidate with an explicit
location-based authority condition; atomic rename is the terminal operation.
If rename fails, the candidate and conditional record remain and the outer/inner
negative receipt is preserved. Hostile tests plant a pre-setup Git failure,
exercise successful terminal promotion and force a rename refusal against an
occupied final directory.

**State:** resolved in software; native filesystem behavior remains unexecuted.

## Verdict

`INTERNAL_STAGING_CONTRACT_READY__NO_JOB_SUBMITTED__NO_MODEL_EXECUTED`

The V3 lane is ready for exact CI and review as a staging-only iteration. It must
be merged before any operator submits the jobs. A future successful harvest may
permit a separate V3 microtrial packet freeze; it is not itself an empirical
Paper 2 result.
