# Paper 2 V4.3 native ingest status (job 3476566)

Date: 2026-08-11

## Object / QoI / claim boundary

- Object: sealed pendulum known-answer microtrial, DIRECT_CORPUS vs RAKL_CONTEXT.
- QoI: exact conceptual pass under frozen evaluator `PENDULUM_KNOWN_ANSWER_V2` / unchanged V4.1 exact gate.
- Context: Qwen2.5-1.5B-Instruct (V4.3 staged snapshot), seed 17, execution head `bf94d168…`.
- Authority: adaptive non-confirmatory engineering only. Sealed microtrial authority only. Not independent review. Not #138 experience §B. Not promotional metrics.

## Job

| Job | Harvest | Ingest verdict |
|-----|---------|----------------|
| 3476566 | `HARVEST_V4_3_TASK_SEED_PASS_NONCONFIRMATORY` | `NATIVE_EXECUTION_CHAIN_PASS__ONE_ARM_SCORABLE_NO_EXACT_PASS__1_5B_NO_EXACT_PASS` |

Observed scores (no invented passes; gate unchanged):

| Arm | parse_valid | conceptual | exact_conceptual_pass |
|-----|-------------|------------|------------------------|
| DIRECT_CORPUS | false | n/a (schema field mismatch) | n/a |
| RAKL_CONTEXT | true | 2/5 | false |

`exact_conceptual_pass_arm_count=0`.

Committed mirrors:

- `research/paper2_microtrial_v4_3/native_job_3476566/`
- `research/paper2_microtrial_v4_3/native_bundles/PAPER2_V4_3_NATIVE_JOB_3476566.tar.gz`
- `research/paper2_microtrial_v4_3/PAPER2_V4_3_NATIVE_JOB_3476566_INGEST_RECEIPT_20260811.json`

FS9 source: `/projects/hep/fs9/users/scyiu/RAKL-paper2/{runs,receipts,logs}/v4_3/` (execution head `bf94d168…`).

## Preserved prior V4.3 job 3476564

Harvest on FS9/tip mirror: `HARVEST_V4_3_CANNOT_CHECK` (`submission_packet_parent_mismatch`). Same arm score shape as 3476566 locally (DIRECT parse-null; RAKL 2/5 exact=false) but **not** admitted as a passing native ingest chain. Mirror retained at `native_job_3476564/` + bundle for negative/chronology preservation only.

## Comparison vs V4.2 0.5B (3476540)

| Metric | V4.2 0.5B (3476540) | V4.3 1.5B (3476566) |
|--------|---------------------|---------------------|
| parse_valid arms | 2 | 1 |
| scorable arms | 2 | 1 |
| exact_conceptual_pass_arm_count | 0 | 0 |
| RAKL conceptual | 3/5 | 2/5 |

Larger Instruct model did **not** obtain any exact conceptual passes. Paper-eligible promotional / paired-effect metrics remain **BLOCKED** (sealed microtrial authority only). DIRECT `parse_valid=false` root-cause is owned by a sibling fiber; this ingest does not resubmit and does not soften the gate.
