# Paper II ExperienceBenchmark root-cause diagnostic

**Status:** `ADAPTIVE_AFTER_3476548 / ROOT_CAUSE_ONLY / NO_RETROACTIVE_REINTERPRETATION / NO_SCIENTIFIC_AUTHORITY`

**Issue:** #238

## Frozen parent observation

The parent observation is `paper2-experience-benchmark-v1_2`, job `3476548`:

- 12/12 schema-valid;
- RESET and LEARNING chronology valid;
- 0 registered successes in both arms;
- LEARNING fresh-transfer score delta small and non-promotional;
- learned state changed across D1→D3;
- LEARNING transfer prompts consumed substantially more tokens than RESET;
- no external retrieval/tool calls were exercised.

The parent result remains a valid scoped negative under Qwen2.5-0.5B-Instruct. This protocol does not modify or reinterpret it.

## Root-cause questions

Resolve these in order:

1. **Persistence:** does development state actually change? Parent answer: yes.
2. **Corrective information:** does development produce a verified transferable method lesson? Parent answer: no.
3. **Selective materialization:** is relevant experience selected rather than all state dumped into context? Parent answer: no.
4. **Execution capacity:** can the base model follow a correct generic procedure if supplied directly? Unknown.
5. **Incremental value:** after 1–4 are satisfied, does learned experience improve fresh transfer? Unknown.

## Diagnostic arms

### RESET
Registered S0; no prior experience.

### FAILURE_MEMORY_ONLY
Persist failed TaskEpisodes and failure-lattice entries. A failed episode creates **no reusable Lesson**.

### VERIFIED_DEVELOPMENT_LESSONS
After each D-task output is frozen, a protected evaluator may emit a general method lesson. The lesson must:

- bind the source D-task and output hash;
- bind an evaluator receipt hash;
- contain no transfer-task identifier;
- contain no task-local evidence ID;
- have method authority only;
- grant no scientific authority.

### ORACLE_PROCEDURE_UPPER_BOUND
A frozen, family-general checklist is supplied directly. It contains no T-task outcome or evidence identifier. This measures whether the 0.5B model can execute the relevant method at all.

### FULL_RAKL_SELECTIVE
Authorized only after the first four arms localize the bottleneck. It must use a bounded target-conditioned experience view / problem-fibre route rather than whole-state prompt dumping, with explicit retrieval selection telemetry.

## Frozen generic development lessons

The development-only correction basis is:

1. Calibration: prefer a currently calibrated instrument measuring the registered QoI; reject expired calibration and wrong-instrument evidence.
2. Unit transform: an exact registered unit transformation preserves the underlying measurement; calibration authority does not transfer to uncalibrated alternatives.
3. Context alignment: before contradiction, align object, regime, time/aggregation, measurement operator and QoI; mismatched contexts do not directly refute each other.

These are method instructions, not evidence about T1–T3.

## Decision table

| Observation | Root-cause classification | Action |
|---|---|---|
| ORACLE fails at floor | `MODEL_CAPABILITY_FLOOR` | stop 0.5B architecture comparisons; freeze stronger-model packet |
| ORACLE succeeds, VERIFIED fails | `VERIFIED_LESSON_INDUCTION_OR_MATERIALIZATION_FAILURE` | repair lesson extraction/admission/selection |
| VERIFIED succeeds, FAILURE_MEMORY_ONLY fails | `VERIFIED_EXPERIENCE_ADDS_VALUE` | proceed to selective/full RAKL test |
| FAILURE_MEMORY_ONLY and VERIFIED both succeed | `SIMPLER_MEMORY_MAY_SUFFICE` | narrow architecture claim; test cost |
| FULL_RAKL_SELECTIVE improves over verified whole-state prompt | `SELECTIVE_RETRIEVAL_ADDS_VALUE` | retain routing/fibre contribution |
| full RAKL adds no benefit at higher cost | `COST_DOMINATES_BENEFIT` | narrow/disable layer |

## Chronology invariants

- D output bytes freeze before any D feedback is constructed.
- T1–T3 sealed answers remain inaccessible until each T output is frozen.
- Every transfer task starts independently from one frozen post-development state for its arm.
- No transfer output teaches a later transfer task.
- Any change to task/evaluator/model/resource contract after outcome inspection creates a new protocol version.

## Historical preservation

v1, v1.1 and v1.2 remain immutable process history. In particular, do not replace the v1.2 result with a rerun and call it the same experiment.

## Implementation slice in this PR

`src/rakl/paper2_experience_root_cause.py` provides:

- failure-only episode persistence without pseudo-Lesson creation;
- protected verified-development lesson admission;
- leakage guards on transfer IDs and task-local evidence IDs;
- bounded selective lesson/failure materialization for diagnostic use;
- the frozen oracle upper-bound procedure.

`tests/test_paper2_experience_root_cause.py` locks those semantics.

No model execution is claimed by this slice.
