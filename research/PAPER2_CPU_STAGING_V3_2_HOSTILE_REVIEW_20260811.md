# Paper 2 CPU staging lineage through V3.2 — same-context hostile review

Date: 2026-08-10; native update: 2026-08-11
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

**State:** native bootstrap passed atomically for exact subject
`2fc6457bce764baef01bca6b19c5a9e053f702f4`. This establishes the bounded
checkout-bootstrap claim only; the later dry-run refusal below prevents any
staging-readiness or execution inference.

### P2-V3-H9 — direct versions did not prove the promoted runtime

**Finding.** Four direct package versions do not exclude an extra or wrong
transitive distribution, broken metadata, a CUDA-enabled Torch build, a wrong
interpreter, or a wrong host architecture.

**Resolution.** Promotion now requires `pip check`, exact equality of the full
distribution set, `pip freeze --all`, standalone Python 3.11.13 identity, x86_64
platform/libc observation, repository commit/tree/ancestry attestation, free-space
headroom, and a Torch smoke test with exact `2.8.0+cpu`, null CUDA build metadata
and a CPU tensor.

**State:** the native submission dry-run exercised this fail-closed boundary and
refused the checkout as dirty before `sbatch` or job submission. No native staging or
promoted-runtime receipt exists.

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

### P2-V3-H14 — the preflight mutated the checkout it was required to attest

**Finding.** The native bootstrap for exact subject
`2fc6457bce764baef01bca6b19c5a9e053f702f4` passed atomically, but the following
submission dry-run refused with `checkout_not_clean`. The shell wrapper first
observed a clean checkout, then invoked `python -m rakl.paper2_cpu_staging` with
the repository `src/` tree on `PYTHONPATH`. CPython created
`src/rakl/__pycache__/*.pyc` before the module performed its independent Git
observation. The preflight therefore changed the object it was supposed to
measure.

**Evidence.** The preserved bootstrap receipt has verdict
`BOOTSTRAP_PASS_ATOMICALLY_PROMOTED` and SHA-256
`6c76c22ecc36f36c7b42ed998b819d5c91d8306de1095597069d234092453fdf`.
The preserved dry-run receipt has verdict `REFUSE_PREFLIGHT_VALIDATION`, failure
`checkout_not_clean`, SHA-256
`5e102ec6e1d0f6145e4c19d5e45f989c30fd236a4d7975d0de05c2aa84b1f445`,
and an empty submitted-job-id list. A later read-only observation at
`2026-08-10T23:41:29Z`, receipt SHA-256
`f58bdc2646b055c4e048f5ffe75d17195c047a9efb3541356ba639dc11aa4921`,
found zero tracked changes and exactly 24 untracked bytecode files at the exact
checkout, with every path and byte hash retained. This bounded native sequence
supports bytecode generation as a sufficient observed mechanism but does not establish it
as the sole possible mutation at the earlier refusal time. Jobs submitted, model
executions and evaluated result records remain zero.

**Resolution.** Every repository-module Python invocation in the submission,
network-probe, staging and harvest paths now sets
`PYTHONDONTWRITEBYTECODE=1`. The native refusal is retained as a falsifier and
is not overwritten by the repair.

**State:** resolved for exact merged subject `8184ed2...` by the native result in
H15. The old refusal remains negative history rather than being rewritten.

### P2-V3-H15 — repaired preflight still required native exact-subject evidence

**Finding.** Local regression tests and a merged script repair could not prove
that the exact LUNARC checkout would remain clean through the governed dry-run,
that the contract hash would match, or that the earlier dirty checkout would be
preserved rather than silently cleaned.

**Evidence.** Exact subject `8184ed2960078102a6b5c25221dd26fc01f03a7a`
produced atomic bootstrap PASS receipt SHA-256
`fa6fe7b716da221419005001dd26d75a5ecf11f335168282c501e2bd81f0db02`
and dry-run receipt SHA-256
`b5120b4ff2179a962ab41c6a81861fcc6867b10176a7a97f594f346702065c09`
with verdict `READY_NOT_SUBMITTED`, no failures and no submitted job ids. A
read-only receipt with SHA-256
`8635afd77787b809f1ea356479e38d8f103a0dc88154938b4971442761944efe`
observed the old dirty checkout quarantined with 24 status entries and the new
active checkout clean with zero status entries.

**Resolution.** The machine synthesis binds all three receipts, the exact
contract canonical hash, the planned-but-unexecuted `sbatch` vectors and the
prior refusal/repair lineage. Jobs submitted, model executions and evaluated
result records remain zero.

**State:** resolved for native preflight readiness only. Native asset staging,
harvest and the V3 execution packet remain blocked and cannot be inferred from a
dry-run.

### P2-V3-H16 — HEAD success did not imply GET success

**Finding.** Exact subject `1a9d3079571e1f1278e32061665be885845bd5cf`
submitted the authorized two-phase staging lane. Probe job `3475080` completed
with 38/38 HTTP-200 HEAD observations, while dependent staging job `3475081`
failed with HTTP 403 before promotion. The candidate was preserved and the final
path remained absent. Both chronological harvest receipts record the same
negative scheduler state. This falsifies any inference from probe pass to
staging success.

**Diagnosis.** The V3 probe bound a User-Agent but its GET call used a bare URL.
Read-only manifest-order inspection found the first 25 objects present and
identity-matching, followed by missing Torch at index 25. Because the failure
receipt omitted the active artifact, Torch is the strongest deterministic
candidate, not directly proven as the failing request.

**Resolution.** Preserve V3 and its failed candidate. Create a V3.1 successor
whose GET and HEAD use the same bound User-Agent and whose failure receipt names
the exact artifact id, URL and HTTP status. Synthetic hostile tests plant a 403
and verify the receipt boundary.

**State:** native V3 failure resolved only as a local versioned repair;
`REPAIR_READY_NOT_SUBMITTED`. Native V3.1 behavior remains `CANNOT_CHECK` until
a later authorized exact-subject submission and harvest.

### P2-V3-H17 — an in-place repair would rewrite a protected evaluated subject

**Finding.** The V3 contract byte-binds `src/rakl/paper2_cpu_staging.py` and its
protected parent evaluator. Updating that file or regenerating V3 around new
bytes would obscure which runtime generated jobs `3475080` and `3475081` and
invalidate the trusted-parent readiness invariant.

**Resolution.** The correction is versioned as V3.1 with a new runtime, new
contract and new operator scripts using distinct candidate/final/failure/receipt
paths. The V3 runtime and contract remain byte-identical to their evaluated
parent. The synthesis receipt binds V3 negative evidence and V3.1 repair bytes
without claiming a retry occurred.

**State:** resolved in local construction and protected-parent tests; native
V3.1 staging remains unexecuted.

### P2-V3-H18 — a negative harvest could pass without scheduler or preservation evidence

**Finding.** The first V3.1 draft allowed its negative branch to remove a
missing-scheduler-row failure and accepted a typed stage failure without exact
stage-job identity or observed candidate preservation. A planted world with no
scheduler rows, wrong job id and `candidate_preserved=false` therefore returned
`HARVEST_STAGING_NEGATIVE_PRESERVED`. This violated missing-evidence-fails-closed.

**Resolution.** V3.1 now requires exactly one root scheduler row for each of the
two distinct submitted job ids, exact probe/stage receipt job-id lineage, a
terminal negative stage row, and path-presence observations consistent with the
failure receipt. `STAGING_FAILED_PRESERVED` requires the exact job candidate to
exist, `candidate_preserved=true`, `final_exists=false`, and no final root.
Refusals require explicit candidate/final observations. Missing, duplicate,
mismatched or contradictory evidence returns `HARVEST_CANNOT_CHECK` and
`negative_history_preserved=false`.

**State:** resolved in the versioned runtime with planted hostile tests for
missing/duplicate rows, missing/wrong job ids, missing/unpreserved candidate and
both final-path contradictions. This is local software evidence only.

### P2-V3-H19 — categorical archive-link rejection blocked the exact runtime archive

**Finding.** The authorized V3.1 retry at exact subject `9d6ee25c...` closed the
HTTP 403 residual but failed with
`archive unsafe member:python/bin/2to3`. Probe job `3475098` completed; stage job
`3475099` failed; the candidate was preserved and the final path remained
absent. Harvest returned `HARVEST_STAGING_NEGATIVE_PRESERVED`.

**Evidence.** A read-only exact-identity inventory found all 38 artifacts present
and hash-matching. The registered Python archive contains 4,352 regular files
and 1,048 symbolic links, with no hard links or special members. Every link
normalizes inside the archive root and targets an existing regular-file member;
300 use `../` syntax without escaping. The first rejected member is the ordinary
relative link `python/bin/2to3 -> 2to3-3.11`.

**Disposition.** Treat this as an extraction-policy mismatch, not asset staging
success and not proof that arbitrary links are safe. Preserve V3.1 unchanged and
version the minimal successor.

**State:** native V3.1 negative preserved. The HTTP repair is supported for this
retry, while full staging remains failed.

### P2-V3-H20 — link support must not reopen archive traversal

**Finding.** Simply removing `issym`/`islnk` rejection would allow absolute or
escaping link targets, missing targets, cycles and link-ancestor write hazards.
Standard extraction convenience cannot replace a frozen security policy.

**Resolution.** V3.2 prevalidates the entire member graph before writing. It
allows only relative symlink/hardlink targets whose normalized target remains
inside the archive root and whose acyclic member chain terminates at an allowed
file or directory. It rejects absolute/escaping links, devices, FIFOs, unknown
types, duplicate normalized paths, missing targets, cycles and any link path
that is an ancestor of another archive member. Regular content is materialized
before validated links. Planted hostile worlds cover every rejection class and
the exact observed parent-relative representation.

**State:** resolved in local versioned construction only. Native V3.2 behavior
remains `CANNOT_CHECK` until a separately merged and explicitly authorized
retry.

## Verdict

`NATIVE_V3_1_STAGING_FAILURE_PRESERVED__V3_2_REPAIR_READY_NOT_SUBMITTED`

This recursive hostile review is internal same-context work, not independent
review or peer review. It preserves two native staging failures and a locally
validated successor; it does not establish V3.2 staging success, model
execution, evaluated empirical evidence, performance or manuscript submission
readiness. The latest retry added two staging-only jobs; cumulative counts are
four staging-only jobs, zero model executions and zero evaluated result records.
A later authorized native V3.2 discriminator is required before an execution
packet can be frozen.

## Recursive V3.2 harvest-evidence review

### P2-V32-HR-B01 — semantically empty positive receipts could pass harvest

**Finding.** The first V3.2 harvest draft checked receipt identity and scheduler
rows but did not require the 38 probe observations or the full staging
attestation vector. A planted zero-observation probe and attestation-free staging
receipt could therefore be combined with synthetic successful scheduler rows to
return `HARVEST_STAGING_PASS`.

**Resolution.** Harvest now validates the exact 38 unique manifest artifacts,
reachable probe observations, repository identities, probe-to-stage lineage,
38 exact observed staged files, complete locked distribution set, `pip check`,
Torch/Python/platform smokes, repository attestation, and absence of a
contradictory failure receipt. The planted former exploit returns
`HARVEST_CANNOT_CHECK`; a complete known-answer pass fixture remains accepted.

**State:** resolved locally; native V3.2 success remains unobserved.

### P2-V32-HR-B02 — future-positive JSON Schemas were fail-open

**Finding.** Initial schemas admitted empty `NETWORK_PROBE_PASS`, zero-job
`SUBMITTED_TWO_PHASE_STAGING`, attestation-free staging pass and zero-job harvest
pass documents.

**Resolution.** Verdict-conditional exact cardinalities, empty/nonempty failure
constraints, typed paths and positive-attestation requirements now reject all
four planted counterexamples. Archive observation, repository bootstrap and the
V3.1/V3.2 synthesis now also have exact bound schemas.

**State:** resolved in schema validation and counterexample tests.

### P2-V32-HR-B03 — synthesis tests repeated rather than derived source facts

**Finding.** The first synthesis tests checked byte hashes but repeated scheduler,
chronology and archive literals from the synthesis itself.

**Resolution.** The successor tests derive chronology from each source receipt,
derive scheduler rows from raw `sacct --json`, compare probe/failure/harvest and
archive facts to their source documents, check all artifact identities against
the manifest, and byte-compare every native bundle member to the preserved local
source.

**State:** resolved for the checked-in native evidence set.

### P2-V32-HR-B04 — successful `pip check` was represented incorrectly

**Finding.** The first strengthened harvest expected empty `pip check` stdout,
but the frozen pip emits `No broken requirements found.` on success. A real pass
would therefore have been unharvestable despite exit code zero.

**Resolution.** Staging now records `pip_check_returncode`; harvest and schema
require return code `0` and the frozen pip 24.3.1 success line. The complete
known-answer fixture uses that native command behavior.

**State:** resolved locally.

### P2-V32-HR-B05 — harvest trusted unbound submission/bootstrap semantics

**Finding.** The first strengthened harvest still took the contract digest from
the submitted mapping and checked the bootstrap only by path and hash. An exact
but semantically contradictory bootstrap or a submission naming another contract
could therefore contaminate authority.

**Resolution.** Harvest now requires the submitted mapping to equal its source
file bytes, its contract hash to equal the supplied validated contract, exact
submission/bootstrap schemas and zero-result semantics, matching expected and
observed repository identities, clean detached bootstrap, governed roots equal
the contract paths, and a clean exact harvest-time checkout. Planted mismatched-
contract and mismatched-bootstrap worlds return `HARVEST_CANNOT_CHECK`.

**State:** resolved in local known-answer and planted-hostile tests.

### P2-V32-HR-B06 — bootstrap success vocabulary was prefix-open

**Finding.** Prefix matching admitted fabricated `BOOTSTRAP_PASS_*` verdicts.

**Resolution.** Runtime and schema now admit exactly
`BOOTSTRAP_PASS_EXISTING_EXACT_CHECKOUT` or
`BOOTSTRAP_PASS_ATOMICALLY_PROMOTED` and require the canonical GitHub remote.
A planted fabricated success verdict fails closed.

**State:** resolved locally.

### P2-V32-HR-B07 — freeze and FS9-capacity attestations were presence-only

**Finding.** A list-typed but empty `pip_freeze_all` and an absent or insufficient
disk-capacity observation could survive the first strengthened positive check.

**Resolution.** Harvest now parses 31 unique normalized equality lines and
requires exact equality to the locked distribution map. It also requires
nonnegative integer total/used/free values, total equal to used plus free, and
free bytes at or above the contract minimum. Empty-freeze and one-byte-free
mutations both return `HARVEST_CANNOT_CHECK`.

**State:** resolved in planted-hostile tests.
