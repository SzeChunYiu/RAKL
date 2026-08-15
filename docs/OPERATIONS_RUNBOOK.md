# ORION operations runbook

Eleven procedures an operator actually runs. Every command below was executed and its real
exit code recorded in `research/orion_engineering_closure_v1/RUNBOOK_DRILL_V1.json`
(procedure ids `P01`–`P11` match this file). Steps needing infrastructure this repository
does not provision are marked `NOT_EXECUTABLE_LOCALLY` there with the specific missing
dependency named — never silently reported as passing. Bash blocks are verbatim modulo `$VAR`
substitution; Python blocks show the shape, and the exact scripts the drill executed are in the
drill file's `command` fields.

## Setup

```bash
export ORION_PY=/path/to/python          # a 3.11+ interpreter
export PYTHONPATH=/path/to/rakl/src      # unless the package is installed
export ORION_PROJECT=/path/to/project    # the project root you operate on
```

## Exit codes

| code | meaning | source |
|---|---|---|
| 0 | success | all commands |
| 2 | typed runtime error (refusal, integrity violation, bad input) | `python -m rakl` |
| 3 † | model capability declaration incompatible | `check-profile` |
| 4 | project unhealthy | `doctor` |
| 5 | packet `CANNOT_COMPILE` / `CANNOT_MATERIALIZE` | `packet` |
| 6 | execution not `COMPLETED` | `run` |
| 7 † | packet over token budget | `certify-packet` |
| 8 | release manifest `FAILED` | `verify-release` |
| 2 / 3 / 64 | provenance `REJECTED` / `CANNOT_CHECK` / usage | `scripts/verify_release_provenance.py` |
| 1 / 3 | doctor overall `FAIL` / `CANNOT_CHECK` | the P11 doctor snippet |

† read from `src/rakl/cli.py`, not exercised by the drill; every other code here came from an
actual recorded run. `CANNOT_CHECK` is never folded into success — it gets its own code.

## P01 — deploy

Verify artifact identity *before* deploying: a release you cannot name by digest is one you
cannot roll back to.

```bash
"$ORION_PY" -m rakl profiles                                   # runtime imports, profiles load
"$ORION_PY" -m rakl release-manifest "$RELEASE_ROOT" \
    --source-revision "$(git rev-parse HEAD)" \
    --artifact RELEASE_TARBALL:orion.tar --output release-manifest.json
"$ORION_PY" -m rakl verify-release "$RELEASE_ROOT" release-manifest.json
```

Expect `VERIFIED` and exit 0. On exit 8 read `issues[]`: `artifact_digest_mismatch` means
the tree moved after the manifest was cut — re-cut it, do not edit the manifest.
The deploy itself needs provisioned infrastructure (PostgreSQL, OTLP collector, identity
provider, secret manager) and is not executable here.

## P02 — initialize

```bash
"$ORION_PY" -m rakl init "$ORION_PROJECT" --project-id orion-drill --profile ordinary-8k
```

Exit 0 prints the project status; re-running with the same id is idempotent. A *different*
`--project-id` exits 2 (`existing project manifest is incompatible; refusing to rewrite`) —
that refusal is correct, so point at a different root instead.

## P03 — ingest

```bash
"$ORION_PY" -m rakl ingest "$ORION_PROJECT" evidence.md \
    --record-id evidence:drill:1 --tokens 120 --kind SOURCE_PROJECTION \
    --coverage drill_evidence --fiber E20 --mandatory
```

Exit 0 prints the record envelope with its `payload_sha256`. Re-ingesting identical bytes
under the same `record-id` is idempotent. Re-binding that id to *different* content exits 2
(`record_id is immutable`) — mint a new record id.

## P04 — research

```bash
"$ORION_PY" -m rakl packet "$ORION_PROJECT" --operation SATURATION_SCAN \
    --question "what evidence covers the drill?" --require drill_evidence \
    --output packet.json
"$ORION_PY" -m rakl run "$ORION_PROJECT" packet.json --runner-id drill-runner \
    --model-id local-echo --model-version 0 --exec /bin/bash --arg ./echo_adapter.sh \
    --output run-output.json
```

`packet` exits 0 with `verdict: READY`. A required coverage atom nothing supplies exits 5
with `CANNOT_COMPILE` — ingest the missing evidence rather than dropping the requirement.
`run` exits 0 with an execution receipt binding the runner, model id/version, argv and an
event-chain head; exit 6 means the execution did not reach `COMPLETED`. Runner output is
proposal-only and mints no authority.

## P05 — inspect status

```bash
"$ORION_PY" -m rakl status "$ORION_PROJECT"
"$ORION_PY" -m rakl doctor "$ORION_PROJECT"
```

`doctor` exits 0 when `healthy: true` and 4 with a typed `issues[]` otherwise
(`missing_payload:*`, `payload_integrity_failure:*`, `record_index_invalid:*`); a non-project
directory exits 2 (`not a RAKL project`) — an error, not health.

## P06 — recover an ambiguous activity

An activity whose worker died *after* starting an external effect and *before* writing its
receipt is `RECOVERY_REQUIRED`. There is deliberately no automatic retry: the engine cannot
know whether the effect happened.

```python
from rakl.engineering_workflow_workers import SqliteWorkerWorkflowEngine
engine = SqliteWorkerWorkflowEngine("workflow.sqlite3")
result = engine.claim("wf:release", "act:publish", worker_id="worker-b", now=NOW, ttl=30)
print(result.verdict.value, result.reason)          # RECOVERY_REQUIRED
print(engine.activity("wf:release", "act:publish")) # status, attempts, effect_started, receipt
print(engine.verify_history("wf:release"))          # hash chain must be True
for event in engine.events("wf:release"):
    print(event["sequence"], event["kind"], event["payload"])
```

Read `EFFECT_STARTED` and the absence of `ACTIVITY_COMPLETED`, then establish out-of-band
whether the external effect landed. Re-claiming does not clear the state; recording the
resolution is an operator action. If `verify_history` is False, stop — the log was tampered
with and nothing downstream of it is trustworthy.

## P07 — backup

```python
from rakl.engineering_ops import take_backup
manifest = take_backup(PROJECT_ROOT, backup_id="bk-1", created_at="2026-08-15T00:00:00+00:00")
# persist manifest.backup_id, created_at, entries and manifest_digest as JSON
```

The manifest digest binds its entries, so an edited manifest raises on load. Keep it with the
copied bytes — a backup you cannot verify is not a backup.

## P08 — restore

Restore into an **empty** root, then verify byte-for-byte.

```python
from rakl.engineering_ops import BackupManifest, verify_restore
verdict, offenders = verify_restore(RESTORE_ROOT, manifest)   # EXACT, ()
```

`EXACT` is the only acceptable outcome. `MISSING_BLOB` / `CORRUPTED_BLOB` name the offending
paths; `MANIFEST_TAMPERED` means the manifest no longer binds its entries — treat that backup
as lost and fall back to an older one.

## P09 — upgrade

```python
from rakl.engineering_migration import build_import_receipt, compare_migration_parity
report = compare_migration_parity(source_state, target_state)   # MATCH before cutover
receipt = build_import_receipt(..., parity_report=report, ...)  # refuses non-MATCH parity
```

Cut over only on `MATCH`. `MISMATCH` means the target is not the source; `CANNOT_CHECK` means
parity could not be computed and is *not* permission to proceed. Historical stores stay as
evidence — imported rows are not rewritten to look native. Running the schema migration
against the target backend needs a provisioned backend and is not executable here.

## P10 — rollback

Data plane first: restore the last verified backup into an empty root (P08) and confirm
`EXACT`. Then redeploy the previous **digest-pinned** image — that digest comes from the
provenance record verified in P11, never from a mutable tag. The image half needs a registry
and the deployed environment; it is not executable here.

## P11 — diagnose

```bash
"$ORION_PY" - <<'PY'
from rakl.engineering_doctor_probes import ProbeContext, build_doctor, render_report
ctx = ProbeContext(now=NOW, object_store_root=..., expected_object_digests=(...),
                   workflow_db_path=..., backup_manifest=..., backup_restore_root=...,
                   stored_status=..., database_path=..., semantic_store=..., semantic_index=...,
                   provenance=..., artifact_bytes=..., secret_store=..., required_secret_names=(...))
print(render_report(build_doctor(ctx).run()))
PY
"$ORION_PY" scripts/verify_release_provenance.py --provenance provenance.json \
    --artifact "$RELEASE_ROOT/orion.tar" --identities identities.json \
    --root "$RELEASE_ROOT" --expect-commit "$(git rev-parse HEAD)"
```

Read the doctor line by line: `FAIL` is a confirmed broken subsystem and outranks everything;
`DEGRADED` is inside a threshold breach (index lag, expired lease, stale backup); `CANNOT_CHECK`
means that subsystem was **not** inspected — wire the missing handle before believing the
report. `OK` only ever follows an inspection that actually happened. Exit the snippet 1 on
`FAIL`, **3** on `CANNOT_CHECK` and 0 otherwise — a doctor run that inspected nothing must not
be green in CI.

The provenance gate exits 0 `VERIFIED`, 2 `REJECTED` with typed reasons
(`MISSING_PROVENANCE_FIELD`, `MUTABLE_TAG_WITHOUT_DIGEST`, `ARTIFACT_MISMATCH`,
`PROVENANCE_COMMIT_MISMATCH`, `STALE_BENCHMARK_IDENTITY`, `STALE_EVALUATOR_IDENTITY`,
`UNVERIFIED_DEPLOYMENT_ARTIFACT`, `DEPLOYMENT_ARTIFACT_DIGEST_MISMATCH`), 3 `CANNOT_CHECK`
when an input was absent or malformed, and 64 on a usage error. Run it with no arguments and
it exits 3, not 0 — a release nobody described has not been verified. Nothing in this runbook
grants scientific authority; it reports engineering artifact and subsystem state only.
