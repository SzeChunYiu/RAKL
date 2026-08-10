# Paper 2 pendulum microtrial — same-context hostile review

Date: 2026-08-10  
Scope: additive microtrial packet, runner, receipts and claim boundary through the
LUNARC execution-contract repair.

## Independence boundary

This review was performed in the same assistant context that implemented the
repair. It is an internal hostile consistency review, **not independent review,
not external peer review and not model-performance evidence**.

## Hostile concerns and resolutions

### P2-MH-H1 — local macOS model path made the Linux execution packet false

**Finding.** The first packet named a user-specific local macOS model snapshot while the
frozen environment was Linux CPU. A semantically valid packet could therefore
never describe the intended LUNARC execution site.

**Resolution.** The snapshot is now fixed at
`/projects/hep/fs9/users/scyiu/RAKL-paper2/models/Qwen--Qwen2.5-0.5B-Instruct/7ae557604adf67be50417f59c2c2f167def9a775`.
The separately bound execution contract places the repository and run outputs
under the same registered FS9 root. Preflight requires model-manifest and
execution-contract snapshot paths to agree and requires model/output paths to be
inside that root. The runner also forbids inference on `cosmos` login nodes and
requires a numeric SLURM job identifier as a syntactic guard.

The exact FS9 path is intentionally public operational metadata needed by this
frozen reproduction contract; it is not a password, token or private credential.
Relocating it requires a newly versioned packet rather than silent substitution.

**State:** resolved at the contract level; the snapshot is still absent and no
execution is claimed.

### P2-MH-H2 — result receipts did not identify the code checkout that ran

**Finding.** Hashing the runner and packet at freeze time did not establish that a
later model call used a clean checkout or identify the exact execution commit and
tree. A dirty checkout could contaminate an otherwise well-formed result receipt.

**Resolution.** Before creating the output directory or invoking the backend, the
runner now requires the frozen repository path, exact LUNARC host prefix, a clean
Git status including untracked files, valid commit/tree hashes and ancestry from
the frozen packet subject. It then writes `run_manifest.json` before any model
output. The manifest binds the packet bytes and canonical identity, every frozen
artifact hash, checkout commit/tree/path, host, model snapshot and output path.
Its exact byte hash is repeated in raw-output, provider, resource and final result
receipts. Hostile tests plant a dirty checkout and verify that neither output nor
backend access occurs.

**State:** resolved for runner-controlled execution.

### P2-MH-H3 — self-enforcement is not an external trust anchor

**Finding.** The runner verifies its own bound source. A malicious replacement
could remove those checks before execution.

**Disposition.** The packet separately binds runner bytes, and the exact clean
checkout commit/tree is recorded for independent reproduction. This narrows but
does not eliminate supply-chain trust. A later external reproduction should
verify the checkout and packet before invoking Python. No independent assurance
claim is made here.

**State:** open external-assurance coordinate; non-blocking for the engineering
microtrial, blocking for independent-reproduction language.

### P2-MH-H4 — arm blinding is limited

**Finding.** Opaque labels prevent the deterministic scorer from receiving arm
names, but output content can still reveal which prompt contained a RAKL context
map. This is not blinded human adjudication.

**Disposition.** The evaluator is a sealed deterministic known-answer function
and receives no condition field. The claim remains a one-task engineering
diagnostic; no protected human-blinding or general causal claim is inferred.

**State:** retained limitation.

### P2-MH-H6 — scoring receipt overstated blinding

**Finding.** The orchestration process had already loaded the blind-id map for
prompt dispatch, so `arm_conditions_visible_during_scoring=false` was not a
defensible process-level statement even though the deterministic evaluator did
not receive a condition field.

**Resolution.** The scorer is now a separate function whose only inputs are
opaque blind ids and raw text. The receipt states only that condition labels are
absent from scorer inputs and score records, while affirmatively recording that
the orchestrator loaded the map before scoring. It explicitly disclaims human or
process-level blinding.

**State:** resolved by implementation separation and claim narrowing.

### P2-MH-H7 — committed chronology was impossible

**Finding.** The previous packet and preflight asserted UTC event times later
than their introducing commit and later than the hostile audit wall clock.

**Resolution.** That packet identity is retained as superseded negative history.
The replacement packet/preflight use observed UTC times, bind the repaired
runner, and enforce strict UTC syntax and order. Reversed or future-dated
freeze/receipt/run times fail before output directory or backend access.

**State:** resolved for the replacement packet; no result access occurred.

### P2-MH-H8 — numeric environment variable is not batch attestation

**Finding.** A numeric `SLURM_JOB_ID` can be injected and does not prove an
`sbatch` allocation or its resource/account/partition contract.

**Disposition.** The current check is now described only as a syntactic guard.
Native execution remains blocked until a separately reviewed, byte-bound batch
wrapper and scheduler receipt are added. No batch-execution assurance is claimed.

**State:** open and blocking for native execution; non-blocking for this frozen
harness/provenance repair.

### P2-MH-H9 — offline policy was not observed host network isolation

**Finding.** `HF_HUB_OFFLINE`, `TRANSFORMERS_OFFLINE` and
`local_files_only=true` constrain the registered Transformers access path, but do
not prove that all host network interfaces were disabled.

**Resolution.** The environment contract now records that host network state is
unobserved and names only the offline Transformers policy. The manuscript makes
no host-level isolation claim.

**State:** resolved by claim narrowing; external network attestation remains an
open assurance coordinate.

### P2-MH-H10 — memory and result-schema authority were overstated

**Finding.** `ru_maxrss` is a process-lifetime high-water mark, not an isolated
per-arm peak. The prior result schema also accepted an arbitrary score object and
could not express cross-record identity constraints.

**Resolution.** Resource fields now name the process high-water RSS observed
after each arm. The bound schema requires the exact nine-field known-answer score
and enforces valid/invalid parse-state implications. Before final receipt write,
a production verifier rejects incomplete or duplicate arms, nested blind-id,
prompt and run-manifest mismatches, and malformed score states.

**State:** resolved for the registered quantity and final-receipt path.

### P2-MH-H5 — exact provider cost is not total cost

**Finding.** Local inference has no provider API transaction, but calling its cost
zero without qualification would omit electricity, hardware, storage, download
and operator costs.

**Disposition.** USD 0 is explicitly limited to provider API charges. All other
coordinates remain unpriced and prohibit a monetary efficiency conclusion.

**State:** resolved by claim narrowing; total-cost comparison remains open.

## Verdict

`INTERNAL_EXECUTION_CONTRACT_REPAIRED__NATIVE_RUN_CANNOT_CHECK`

The additive harness is internally ready to reject wrong paths, dirty checkouts,
unbound artifacts, invalid chronology and incomplete receipts. It is not a
performance result. Native execution additionally requires the reviewed batch
wrapper/scheduler receipt, exact FS9 model snapshot and frozen Python/package
environment, followed by later independent reproduction.

Exact targeted and repository verification is rerun after every material repair
and recorded in GitHub CI for the exact head. These software checks support only
the execution-contract verdict above; they are not native model evidence.
