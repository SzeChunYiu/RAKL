# Self-RAKL Round 023 — Governed Execution Provenance and Recovery

Date: 2026-08-09  
Starting main: `80d3d79cd5fcd8cb5dcbdc1443e940e8ca5d8518`  
Class: A supporting implementation plus research  
Constitutional change: none

## Engineering residual

Round 022 made RAKL installable as a provider-neutral project/task-packet runtime. A publishable artifact still lacked a trustworthy boundary between a deterministic RAKL task packet and an actual model/adapter process. Without that boundary, a researcher could not answer several basic reproducibility questions:

- Which exact task packet was executed?
- Which runner/model/version/configuration was declared?
- What raw bytes did the process emit?
- Did a retry execute the same expensive or side-effecting call twice?
- Was a timeout, process failure, protocol failure, or start failure conflated with a scientific null result?
- Did a zero exit code accidentally acquire scientific authority?

## Panel

Six same-context engineering lenses were used and are not counted as independent review:

1. agent runtime / state-machine architecture;
2. reliability and idempotency engineering;
3. execution security / subprocess boundary;
4. provenance and content-addressed artifact identity;
5. observability and trace architecture;
6. adversarial reproducibility review.

## Frozen benchmark

`research/SELF_RAKL_RESEARCH_023_FROZEN_BENCHMARK.json` was committed before implementation. It freezes 15 worlds covering success, replay, packet/config identity, timeout, process/protocol/start failures, PREPARED and RUNNING recovery, secret handling, literal argv, tamper detection, proposal-only authority, and CLI execution.

The first support implementation reached `f32460207e01c56db1dcb0279bce21814bf510e9` and passed 287 tests. The round then found two native semantic residuals **after** that green result:

1. generation configuration was part of invocation identity/receipt but not forced through the child-process input protocol;
2. event refs made races detectable but no explicit same-invocation local lease prevented two callers from crossing the external-execution boundary concurrently.

The addendum `research/SELF_RAKL_RESEARCH_023_EXECUTION_SEMANTICS_ADDENDUM.json` was frozen before correcting either residual.

## Retained architecture

### Packet-bound execution identity

An invocation is identified by canonical execution protocol, exact task-packet SHA-256, runner/model/version/argv contract, timeout/protocol/retry policy, environment-name/revision declaration, generation configuration, and execution nonce.

### Canonical runner envelope

The child adapter receives canonical JSON containing:

```text
execution protocol version
invocation id
task packet object
generation configuration
```

The exact envelope bytes are content-addressed and the digest is stored in the receipt. The receipt claims only `DELIVERED_TO_RUNNER_PROTOCOL`, not that a hosted provider/model obeyed the generation settings.

### Append-only event chain

`PREPARED`, `RUNNING`, and terminal/recovery states are serialized as canonical content-addressed events. Each event carries the previous event digest. Per-invocation `.ref` files preserve ordering and make tampering or missing objects diagnosable within the tested local storage model.

### Terminal receipt replay

A completed/failed terminal invocation gets an immutable content-addressed receipt. Repeating the exact invocation returns that receipt without starting the command again.

### Recovery semantics

A historical `RUNNING` state without terminal evidence always returns `RECOVERY_REQUIRED`; RAKL will not guess that the side effect did not occur. A `PREPARED` state may start a new attempt only for an explicitly retry-safe runner. All attempts remain in history.

### Local execution lease

Before execution, one local process must own `<run>/active.lock`. A live PID blocks a second caller. A locally demonstrably dead PID permits stale-lease reclamation, but subsequent state-machine checks still block any historical `RUNNING` ambiguity.

This is local duplicate-safety, not distributed exactly-once semantics.

### Raw output provenance

Exact stdout/stderr bytes are placed into the same SHA-256 canonical store before final receipt commitment. Start failures have no fabricated raw output objects. Timeout/process/protocol failures are distinct execution states.

### Secret boundary

Runner contracts and receipts include allowed environment variable **names** and an environment revision declaration, not secret values. Values are supplied only to the child process. This is a confidentiality choice and means environment revision remains a declared coordinate rather than cryptographic equivalence of secrets.

### Authority boundary

Every receipt preserves:

```text
output_authority = PROPOSAL_ONLY
may_promote_canonical_knowledge = false
```

A successful process therefore cannot self-promote scientific knowledge.

## External projections and novelty narrowing

Agentic Harness Engineering, OpenTelemetry, Python subprocess semantics, and durable agent checkpointing all show that observability, explicit execution state, safe process boundaries, and recovery are established engineering traditions. RAKL does not claim execution receipts, traces, retries, content-addressed logs, or local locking as novel.

The RAKL-specific scientific question remains whether combining execution provenance with explicit proposal-only authority, evidence governance, negative history, contextual task-packet compilation and separately controlled promotion improves process integrity in scientific-agent benchmarks.

## Executed support evidence

- Pre-addendum CLI-support SHA `f32460207e01c56db1dcb0279bce21814bf510e9`: 287 tests passed.
- Corrected addendum SHA `6d73324091fa4e8303d25b9d897f087ce6ee9f2e`: 291 tests passed in 6.73 s.

The addendum tests include a synchronized concurrent-call world in which the first local process holds the invocation lease while the second caller attempts the same identity; exactly one external counter increment is observed.

## Explicit non-closure

This round does not establish:

- distributed exactly-once execution;
- cryptographic identity of hosted provider infrastructure;
- executable-byte/image attestation;
- exact provider tokenizer accounting;
- model compliance with delivered generation settings;
- scientific correctness of output;
- automatic claim/evidence promotion;
- workflow-DAG crash recovery beyond one invocation.

These become separate fibers rather than being hidden under the phrase 'durable agent'.

## New residuals

- `META_N083_DISTRIBUTED_EXECUTION_COORDINATION`
- `META_N084_RUNNER_ARTIFACT_AND_ENVIRONMENT_ATTESTATION`
- `META_N085_EXECUTION_TRACE_EXPORT_AND_OBSERVABILITY`
- `META_N081_TOKENIZER_BUDGET_CALIBRATION` remains high priority
- `META_N082_RELEASE_ARTIFACT_IDENTITY` remains high priority

## Saturation

`ACTIVE_NON_FLAT`. Same-context flat rounds = 0; independent flat rounds = 0. The run added new executable semantics and new native residuals.

## Next outcomes

Positive: freeze tokenizer or release-artifact worlds before implementing either.  
Null: if richer execution tracing does not improve audit/recovery beyond canonical packet/output hashes, keep tracing thin.  
Refuted: any duplicate external execution in a frozen local same-invocation world blocks this execution contract.  
Partial-ID: hosted runner implementation/configuration remains externally attested or partially identified.  
Blocked: inaccessible provider identity or tokenization stays `CANNOT_CHECK`.  
Transport: if `main` moves before promotion, rebuild without force while retaining benchmark/addendum history.
