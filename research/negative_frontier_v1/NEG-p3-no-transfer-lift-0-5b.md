# `NEGATIVE_NO_TRANSFER_SUCCESS_LIFT_UNDER_0_5B`

**Paper:** III  
**Class:** `IMMUTABLE_HISTORY`  
**In current manuscript:** yes  
**Artifact immutable:** yes

## Where the manuscript states it

- `publication/papers/paper-03-method-evolution-mechanics/sections/07a_current_precursor_result.tex:6`
- `publication/papers/paper-03-method-evolution-mechanics/sections/02a_terminology_and_measurement_scope.tex:39`
- `publication/papers/paper-03-method-evolution-mechanics/sections/04a_implementation_status.tex:27`

## Receipt

- **`receipt_path`:** `research/paper2_experience_benchmark_v1_2/native_job_3476548/VALIDATION_RECEIPT.json` — **verified present**
- supporting: `research/paper2_experience_benchmark_v1_2/native_job_3476548/README.md`
- supporting: `research/orion_p1_p4_closure_v2/P3_EXPERIENCE_PROTOCOL_FREEZE.json`
- supporting: `research/orion_p1_p4_closure_v2/P3_STRUCTURED_EXPERIENCE_ACTION_RECEIPT.json`

## What happened

Frozen v1.2 RESET-versus-LEARNING packet, native job 3476548: twelve of twelve schema-valid records with the intended chronology. On the staged Qwen2.5-0.5B-Instruct model both arms achieved zero registered successes on both development and fresh-transfer tasks. Development score delta zero; the small partial-score difference on fresh transfer does not satisfy the registered success criterion. The earlier v1 and v1.1 executions remain in the lineage as prompt-interface failures rather than being pooled with the interpretable v1.2 result.

## One-stage attribution

capability. At 0.5B the base model cannot clear the task threshold, so learning effects are unidentifiable there (the MODEL_CAPABILITY_FLOOR semantics of 02a:37).

## Lever

The manuscript does not revive this record. It changes the dependency graph instead: the required ORION experience-to-action transition is now the typed structured-state mechanic held to a repaired, demonstrably falsifiable gate. 'Nothing in the later RSHEA loop relabels these records as positive' (07a:7).

## Class justification

Explicitly immutable in the manuscript. The v1/v1.1 prompt-interface failures are likewise preserved and must not be pooled.

---

*Index: [`CORE.md`](CORE.md). Machine record: `INVENTORY.json`.*
