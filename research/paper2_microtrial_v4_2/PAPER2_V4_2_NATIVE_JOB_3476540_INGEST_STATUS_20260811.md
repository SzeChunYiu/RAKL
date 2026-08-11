# Paper 2 V4.2 native ingest status (job 3476540)

Date: 2026-08-11

## Object / QoI / claim boundary

- Object: sealed pendulum known-answer microtrial, DIRECT_CORPUS vs RAKL_CONTEXT.
- QoI: exact conceptual pass under frozen evaluator `PENDULUM_KNOWN_ANSWER_V2`.
- Context: Qwen2.5-0.5B-Instruct @ 7ae5576, seed 17, V4.2 field-polarity prompts, unchanged V4.1 normalizer/gate.
- Authority: adaptive non-confirmatory engineering only. Not independent review. Not #138 experience §B. Not promotional metrics.

## Job

| Job | Verdict |
|-----|---------|
| 3476540 | `NATIVE_EXECUTION_CHAIN_PASS__BOTH_ARMS_SCORABLE_NO_EXACT_PASS__CAPABILITY_LIMIT` |

Observed: both arms `parse_valid` / scorable; both conceptual 3/5; `exact_conceptual_pass_arm_count=0`.

Committed mirrors:

- `research/paper2_microtrial_v4_2/native_job_3476540/`
- `research/paper2_microtrial_v4_2/native_bundles/PAPER2_V4_2_NATIVE_JOB_3476540.tar.gz`
- `research/paper2_microtrial_v4_2/PAPER2_V4_2_NATIVE_JOB_3476540_INGEST_RECEIPT_20260811.json`

FS9 source: `/projects/hep/fs9/users/scyiu/RAKL-paper2/{runs,receipts,logs}/v4_2/` (execution head `11f2ecbd…`).

## Larger-model discriminator

**BLOCKED.** V4.2 submit/execution contracts hard-bind the staged 0.5B snapshot path and model manifest. Scripts do not support a larger Instruct model without a new frozen staging/model packet. Softening `exact_conceptual_pass` is forbidden. No successor job submitted in this fiber.
