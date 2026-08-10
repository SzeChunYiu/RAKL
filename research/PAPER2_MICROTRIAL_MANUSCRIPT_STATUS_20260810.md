# Paper 2 sealed pendulum microtrial status

Date: 2026-08-10  
Protocol: `PENDULUM_MATCHED_SAME_MODEL_MICROTRIAL_001_EXECUTION_V1`

## Evidence boundary

This lane is a **non-confirmatory engineering microtrial**. It asks whether one
immutable local open model can be run reproducibly on one sealed known-answer
pendulum task under `DIRECT_CORPUS` and `RAKL_CONTEXT`, with identical questions,
seed, evaluator and resource ceilings and with machine-readable output lineage.
It does not establish RAKL superiority, general scientific helpfulness, external
validity or independent review regardless of the eventual arm scores.

The earlier broad Paper 2 architecture-by-evidence programme remains blocked by
fresh confirmatory tasks, fair strong-parent implementations, a protected
task-correctness evaluator, independent replication and complete resource pricing.
This microtrial does not supersede those obligations.

## Frozen execution design

- one sealed eight-source pendulum task;
- seed `17`;
- two arms, `DIRECT_CORPUS` and `RAKL_CONTEXT`;
- exact byte bindings for both materialized prompts, corpus/task, question set,
  evaluator protocol and source, runner, result schema, model and tokenizer
  manifests, execution environment, resource ceiling, blinding map and price
  boundary;
- offline `transformers` inference with `local_files_only=true`,
  `trust_remote_code=false`, no model tools, no retrieval and no repository access
  exposed to the model;
- raw outputs and separate provider/resource receipts saved by opaque blind id;
  scoring occurs before the blind-id map is joined;
- semantic preflight rejects placeholders, missing mandatory source identities,
  hash drift, evaluator drift, unmatched model/tokenizer revisions and resource
  policies that permit tools or retrieval.

## Model footprint and monetary boundary

The registered immutable revision is
`Qwen/Qwen2.5-0.5B-Instruct@7ae557604adf67be50417f59c2c2f167def9a775`
under Apache-2.0. The exact registered model plus tokenizer footprint is
**999,597,690 bytes** (953.291 MiB): 988,110,068 model/config/license bytes and
11,487,622 tokenizer bytes.

No provider API transaction is used, so the registered provider-API charge is
USD 0. This is not a zero-total-cost claim. Network charges, electricity,
hardware depreciation/opportunity cost and operator labour remain explicitly
unpriced and prohibit a monetary efficiency conclusion.

## Current readiness result

The model has **not been downloaded or executed** in this construction pass. The
checked-in preflight receipt is therefore `CANNOT_CHECK`, with zero evaluated
result records. It identifies the absent local snapshot and execution-environment
version mismatches rather than fabricating outputs or treating missing execution
as a null result.

After the exact snapshot and frozen environment are staged, rerun preflight. Only
a `PASS` permits the runner to create model output. Any material change requires a
new packet before output access. The manuscript remains open for empirical closure
after this engineering lane because a one-task diagnostic cannot replace the
matched confirmatory programme.
