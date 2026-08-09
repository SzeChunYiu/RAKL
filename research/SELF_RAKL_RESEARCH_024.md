# Self-RAKL Round 024 — Governed Execution Provenance and Recovery

Date: 2026-08-09  
Starting main: `2a62dd2ed868a127ffb01b28bfcda9847740750e`  
Class: A supporting implementation plus research  
Constitutional change: none

## Transport history

This engineering lane began from Round-022 head `80d3d79...`. Its original execution benchmark and later semantic addendum were frozen before implementation, and final stale candidate `979401504dece32c64483c25faaaaa4a172f8247` passed 291 tests. Before promotion, `main` advanced by two independent research-only commits that used the Round-023 ledger filenames. The green candidate was not force-promoted and none of its benchmark expectations were changed.

Round 024 re-registers the exact execution/recovery acceptance conditions on the new main before rebuilding the implementation. The transport event is preserved as process evidence rather than silently resolving the namespace collision.

## Problem

The reference runtime could compile deterministic LLM task packets but needed a reproducible boundary around actual adapter/model execution. The required engineering object is an invocation whose input identity, runner declaration, configuration delivery, raw output, attempt/recovery history, and authority boundary remain independently inspectable.

## Architecture

The implementation adds:

- packet-bound invocation IDs;
- canonical runner input envelope with exact parsed task packet and generation configuration;
- SHA-256 storage of the exact runner-input bytes;
- append-only, content-addressed execution events linked by previous-event digest;
- exact stdout/stderr archival before final receipt commitment;
- immutable terminal receipts;
- replay of completed identical invocations without re-executing the command;
- explicit `PREPARED`, `RUNNING`, terminal failure and `RECOVERY_REQUIRED` states;
- local same-invocation lease to prevent overlapping external execution;
- stale-lease reclamation only after local PID-liveness evidence, followed by the same historical-state checks;
- allowlisted environment names while secret values stay out of receipts/lease/events;
- argv execution with `shell=False` and absolute executable path;
- `PROPOSAL_ONLY` authority for all model/adapter output.

Generation configuration is certified only as `DELIVERED_TO_RUNNER_PROTOCOL`. RAKL does not infer that a hosted model actually honored those settings.

## Evidence

The transported stale final candidate passed 291 tests. The rebased Round-024 implementation uses the same tested code blobs on top of the independent semantic-closure commits and must pass its own exact-SHA CI before promotion.

## Prior-art boundary

Observability-driven agent harness engineering, OpenTelemetry tracing, standard subprocess security/timeout semantics and durable workflow checkpointing are established. RAKL does not claim traces, locks, idempotency, checkpointing or execution receipts as novel. Their role is to make the scientific method executable without allowing execution success to mint scientific authority.

## Remaining gaps

This is not distributed exactly-once execution, provider infrastructure attestation, exact tokenizer accounting, provider compliance proof, or a workflow-DAG engine. Those remain separate fibers.

## Saturation

`ACTIVE_NON_FLAT`; same-context and independent flat counters remain zero because execution provenance adds new validated structure while tokenization, artifact identity, evaluator dependencies, provider attestation and real scientific benchmarking remain open.
