# Self-RAKL Round 022 — Provider-Neutral Reference Runtime

Date: 2026-08-09  
Starting main: `0a851009f6ddd8ffc0a39bc51645343ba684bef8`  
Class: A supporting implementation plus research  
Constitutional change: none

## Residual

RAKL had increasingly strong scientific-control modules, bounded context, and reconstructable memory metadata, but a reviewer or ordinary user still lacked one executable vertical slice connecting project initialization, exact payload storage, model capability requirements, task-packet compilation, diagnostics, replay, and a package entrypoint. This made the method harder to reproduce than its theory suggested.

## Expert panel

The round used six role-separated passes in one orchestration context. They are not counted as independent review:

1. agent-runtime architecture — state/checkpoint and execution boundaries;
2. research-software engineering — installability and artifact evaluation;
3. LLM systems — provider-neutral capability contracts;
4. storage/provenance — immutable payload identity and tamper detection;
5. reliability/observability — diagnostics and deterministic replay;
6. adversarial reproducibility — fresh-install, corruption, overflow and unsafe-ID worlds.

## Frozen decision

`research/SELF_RAKL_RESEARCH_022_FROZEN_BENCHMARK.json` was committed before implementation. The round explicitly avoided changing `pyproject.toml`, protected workflows/evaluators, scientific promotion semantics, or model-provider APIs.

## Architecture retained after deduplication

### 1. Model-externalized project state

The LLM is a replaceable compute component. Canonical project state belongs to the runtime. A task packet may be replayed to different compatible models without transferring authority to the model.

### 2. Provider-neutral capability profile

The baseline `ordinary-8k` profile requires a declared 8192-token context window, instruction following, and parseable JSON. Native tool calling is not required because tools may be mediated outside the model. Unknown required capabilities yield `CANNOT_CHECK`; known shortfalls yield `INCOMPATIBLE`.

This is engineering infrastructure, not a novelty claim.

### 3. Content-addressed canonical payload store

Exact source bytes are stored under SHA-256 identity. Equal bytes deduplicate; existing objects are verified before reuse; corrupt existing objects are not silently repaired. Logical record IDs are hashed before becoming metadata filenames, so record naming cannot create nested project paths.

### 4. Deterministic epistemic task packet

The existing bounded context compiler selects a task-specific epistemic working set. Selected payloads are materialized with exact digests, strict UTF-8 decoding, the declared reference profile, operation/question, and an explicit proposal-only authority boundary. Identical project state and task arguments produce canonical timestamp-free JSON.

### 5. Fail-closed project diagnostics

`doctor` verifies manifest/profile validity, record-index identity, referenced payload existence, and SHA-256 integrity. Missing or tampered evidence makes the project unhealthy; diagnostics do not silently repair scientific evidence.

### 6. Executable reviewer-facing workflow

`python -m rakl` now provides `profiles`, `check-profile`, `init`, `ingest`, `doctor`, `status`, and `packet`. A minimal example is in `examples/minimal/`.

## Negative history from this same round

The first implementation candidate `9bca56f2949cac83351bb00037f38150b653f78b` failed its exact GitHub Actions run: 2 failed, 267 passed. The failure was not hidden. `_print_json` bound `sys.stdout` at function-definition/import time, so in-process CLI capture could bypass the current stream. Runtime state transitions had reached the expected values, but the CLI was not test-isolated/replay-friendly.

The fix changed output binding to resolve `sys.stdout` at call time. Candidate `ade737802cd8f326a6c054cdfb56b5106c927328` then passed 269 tests. A subsequent non-editable installation conformance test was added without modifying packaging metadata; candidate `df182c42e5bda8a3a1502f01cea5e5bdaa572f3f` passed 270 tests, including installation to an isolated target and execution of `python -m rakl profiles` from the installed artifact.

## Prior-art boundary

The following are not claimed as RAKL inventions:

- normalized agent execution/accounting/trajectory protocols;
- durable workflow checkpointing;
- content-addressed storage;
- command-line packaging;
- provider-neutral capability contracts;
- independently executable artifact reproduction;
- structured experiment logs and raw archives.

BenchAgent reinforces matched execution and accounting for fair agent comparisons. LangGraph documents checkpointed durable execution. ArtifactCopilot and Artisan reinforce executable research artifacts and independently reproducible scripts. Python Packaging specifications define installed entry points. These constrain the paper to treat this runtime as reproducibility infrastructure supporting the RAKL method rather than headline novelty.

## Measured scope

Software evidence demonstrates the frozen support contract on GitHub Actions. It does not yet demonstrate:

- real-model scientific performance across the reference-profile matrix;
- model-specific token-count calibration;
- durable multi-step retries/checkpoints after process crashes;
- automated claim/evidence extraction;
- evaluator dependency closure;
- real comparative scientific superiority of RAKL.

## Newly exposed residuals

- `META_N080_PROVIDER_ADAPTER_EXECUTION_RECEIPT`: provider/local-runner adapters must bind model/version, decoding parameters, task-packet digest, outputs, tools, latency/cost and retry history without granting authority.
- `META_N081_TOKENIZER_BUDGET_CALIBRATION`: declared token costs are currently externally supplied; reference profiles need tokenizer-specific measurement or conservative bound policies.
- `META_N082_RELEASE_ARTIFACT_IDENTITY`: publication release should bind source revision, built wheel/sdist, benchmark packet, paper and checksums in one manifest.
- `META_N019_DURABLE_RESEARCH_EXECUTION` remains open for crash-safe multi-step replay.

## Saturation

State: `ACTIVE_NON_FLAT`. The round retained a runnable provider-neutral vertical slice and revealed new execution/tokenization/release residuals. Same-context flat rounds and independent flat rounds remain zero.

## Next AI outcomes

- Positive: freeze N080 before implementing an adapter/run ledger; then test against a deterministic fake runner and at least one real local/hosted model if accessible.
- Null: if ordinary external scripts plus task packets provide equal replay/audit quality at lower complexity, keep the core runtime thin and document the null.
- Refuted: if a frozen world shows the project/runtime can lose mandatory evidence, alias distinct bytes, or self-promote model output, preserve the counterexample and block release.
- Partial-ID: if model capability or token limit cannot be established, retain `CANNOT_CHECK`; do not infer compatibility from model name.
- Blocked: if fresh-install or execution environment cannot be reproduced, keep user-package closure open.
- Transport: if `main` advances before promotion, rebuild on the new head without force and preserve this benchmark plus failed-candidate history.
