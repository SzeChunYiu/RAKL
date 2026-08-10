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

**Finding.** The first packet named a `/Users/billy/...` model snapshot while the
frozen environment was Linux CPU. A semantically valid packet could therefore
never describe the intended LUNARC execution site.

**Resolution.** The snapshot is now fixed at
`/projects/hep/fs9/users/scyiu/RAKL-paper2/models/Qwen--Qwen2.5-0.5B-Instruct/7ae557604adf67be50417f59c2c2f167def9a775`.
The separately bound execution contract places the repository and run outputs
under the same registered FS9 root. Preflight requires model-manifest and
execution-contract snapshot paths to agree and requires model/output paths to be
inside that root. The runner also forbids inference on `cosmos` login nodes and
requires a numeric SLURM allocation identifier.

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
unbound artifacts and incomplete receipts. It is not a performance result. The
remaining native blockers are the absent exact FS9 model snapshot and frozen
Python/package environment, followed by actual execution and later independent
reproduction.

Fresh verification after this review ran 44 targeted Paper 2 tests and the full
931-test repository suite with no failures. These software checks support only
the execution-contract verdict above; they are not native model evidence.
