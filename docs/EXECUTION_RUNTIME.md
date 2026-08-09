# Governed Execution Runtime

Status: supporting implementation; execution provenance and local duplicate-safety contract  
Date: 2026-08-09

## Purpose

The Round-022 reference runtime can compile a deterministic provider-neutral task packet. Round 023 adds the next boundary: execute that packet through a local/provider adapter while preserving enough provenance to know exactly which packet, runner declaration, generation configuration, raw output, attempt history, and failure state were involved.

The execution layer does **not** grant scientific authority to a successful process or model response.

## Execution identity

An invocation identity binds:

```text
execution protocol version
exact task-packet SHA-256
runner ID
model ID and declared version
absolute argv and argv digest
timeout / JSON protocol / retry-safety contract
allowed environment variable names
environment revision declaration
generation configuration
execution nonce
```

The invocation ID is SHA-256 over canonical JSON for this identity object.

Changing the packet, generation configuration, runner command, model/version declaration, or nonce creates a different invocation identity.

## Runner input protocol

The external runner receives canonical JSON on standard input:

```json
{
  "execution_protocol_version": "rakl-execution-v2",
  "invocation_id": "...",
  "task_packet": {"...": "..."},
  "generation_config": {"temperature": 0}
}
```

The exact runner-input bytes are stored in the project content-addressed store and their digest is bound into the terminal receipt.

The receipt labels generation configuration authority as:

```text
DELIVERED_TO_RUNNER_PROTOCOL
```

This means RAKL can demonstrate that the configured values were delivered to the adapter process. It does **not** demonstrate that a hosted model/provider actually honored the settings. Provider-specific attestation remains a separate projection.

## Append-only execution history

Each invocation owns:

```text
.rakl/runs/<invocation-id>/
├── spec.ref
├── receipt.ref
├── active.lock          # only while locally active
└── events/
    ├── 000001.ref
    ├── 000002.ref
    └── ...
```

Each `.ref` points to exact canonical bytes in the existing SHA-256 content store. Events include the previous event digest, producing a tamper-evident append-only chain within the tested local project model.

The state vocabulary is:

```text
PREPARED
RUNNING
COMPLETED
FAILED_PROCESS
FAILED_PROTOCOL
FAILED_START
TIMED_OUT
RECOVERY_REQUIRED
```

## Duplicate-safe recovery boundary

A terminal receipt is immutable. Repeating exactly the same invocation returns the existing receipt and does not execute the external command again.

If a previous process left `RUNNING` history without a terminal receipt, RAKL returns:

```text
RECOVERY_REQUIRED
```

and does not automatically execute the command again because the external effect may already have occurred.

For a `PREPARED` state, a runner declared `retry_safe=true` may begin a new numbered attempt. A non-retry-safe runner remains blocked. Attempt history is preserved.

## Local execution lease

Before crossing the subprocess boundary, RAKL acquires an exclusive local `active.lock` for the invocation ID. A live lease blocks a second local caller before it starts the external runner.

The lease records only:

```text
invocation_id
pid
lease_id
acquired_at_utc
```

It contains no model secret or environment value. A lease whose PID is locally demonstrably dead may be reclaimed. Reclaiming a stale lease never overrides historical `RUNNING` ambiguity.

This is deliberately a **local-process lease**, not a claim of distributed exactly-once execution. Multi-host coordination remains out of scope.

## Environment handling

A runner contract declares environment variable **names** that may be passed. The caller supplies values at execution time. Values are not serialized into the runner contract, events, lease, or receipt.

Because secrets are intentionally not hashed into public receipts, `environment_revision` is a declared identity coordinate rather than cryptographic proof of secret equivalence. Users/adapters must change it when semantically relevant environment configuration changes.

## Subprocess boundary

RAKL executes an argv sequence with `shell=False`. Shell metacharacters supplied as arguments remain literal arguments rather than implicit shell syntax. The runner executable must be an absolute path.

Raw stdout and stderr bytes are stored by SHA-256 before the terminal receipt is committed. Terminal classifications distinguish:

- process could not start;
- process timed out;
- process exited nonzero;
- process exited zero but violated expected JSON protocol;
- process completed the declared adapter protocol.

## User command

```bash
python -m rakl run ./project ./task.json \
  --runner-id local-model \
  --model-id model-name \
  --model-version model-version \
  --exec /absolute/path/to/runner \
  --config-json '{"temperature":0}' \
  --output ./raw-model-output.json
```

Additional repeated `--arg` values are passed literally to the runner. Repeated `--env NAME` values allow only those parent environment variables to cross into the runner. `--retry-safe` must be an explicit adapter contract, not inferred from model name.

## Authority boundary

Every terminal execution receipt contains:

```text
output_authority = PROPOSAL_ONLY
may_promote_canonical_knowledge = false
```

A zero process exit code therefore establishes at most that the declared adapter protocol completed. It does not establish truth, evidence support, mechanism identity, decision authority, or promotion eligibility.

## Remaining gaps

The execution runtime does not yet prove:

- executable bytes correspond to a particular signed/reproducible artifact;
- a hosted provider honored generation settings;
- token budgets match a provider-specific tokenizer;
- exactly-once execution across multiple machines;
- scientific correctness of model output;
- complete OpenTelemetry-style distributed trace export.

These remain explicit child fibers rather than being hidden inside a generic 'agent runtime' claim.
