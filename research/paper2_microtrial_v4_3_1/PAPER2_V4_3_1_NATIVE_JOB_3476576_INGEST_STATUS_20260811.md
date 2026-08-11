# Paper 2 V4.3.1 native ingest status (job 3476576)

Date: 2026-08-11

## Object / QoI / claim boundary

- Object: sealed pendulum known-answer microtrial, DIRECT_CORPUS vs RAKL_CONTEXT.
- QoI: exact conceptual pass under frozen evaluator / unchanged exact gate.
- Context: Qwen2.5-1.5B-Instruct (V4.3 staged snapshot), seed 17, execution head `242a393…` (V4.3.1 serialization repair).
- Authority: adaptive non-confirmatory engineering only. Sealed microtrial authority only. Not independent review. Not #138 experience §B. Not promotional metrics. Not a 1.5B improvement claim.

## Job

| Job | Harvest | Ingest verdict |
|-----|---------|----------------|
| 3476576 | `HARVEST_V4_3_1_TASK_SEED_PASS_NONCONFIRMATORY` | `NATIVE_EXECUTION_CHAIN_PASS__BOTH_ARMS_SCORABLE_NO_EXACT_PASS__SERIALIZATION_REPAIR_STILL_ZERO_EXACT` |

Observed scores (no invented passes; gate unchanged):

| Arm | parse_valid | conceptual | exact_conceptual_pass |
|-----|-------------|------------|------------------------|
| DIRECT_CORPUS | true | 1/5 | false |
| RAKL_CONTEXT | true | 3/5 | false |

`exact_conceptual_pass_arm_count=0`.

Committed mirrors:

- `research/paper2_microtrial_v4_3_1/native_job_3476576/`
- `research/paper2_microtrial_v4_3_1/native_bundles/PAPER2_V4_3_1_NATIVE_JOB_3476576.tar.gz`
- `research/paper2_microtrial_v4_3_1/PAPER2_V4_3_1_NATIVE_JOB_3476576_INGEST_RECEIPT_20260811.json`

FS9 source: `/projects/hep/fs9/users/scyiu/RAKL-paper2/{runs,receipts,logs}/v4_3_1/` (execution head `242a393…`).

## Preserved prior V4.3 job 3476566

Parent ingest remains the DIRECT schema-envelope parse-null residual (`parse_valid_arm_count=1`, RAKL 2/5, exact=0). V4.3.1 repair is serialization-only (registered-envelope unwrap / flat materialize); it does not rewrite 3476566 negative history.

## Comparison

| Metric | V4.2 0.5B (3476540) | V4.3 1.5B (3476566) | V4.3.1 1.5B (3476576) |
|--------|---------------------|---------------------|------------------------|
| parse_valid arms | 2 | 1 | 2 |
| scorable arms | 2 | 1 | 2 |
| exact_conceptual_pass_arm_count | 0 | 0 | 0 |
| DIRECT conceptual | 3/5 | n/a (parse-null) | 1/5 |
| RAKL conceptual | 3/5 | 2/5 | 3/5 |

Both-parse restoration is not an exact-pass or 1.5B improvement claim. Paper-eligible promotional / paired-effect metrics remain **BLOCKED**.
