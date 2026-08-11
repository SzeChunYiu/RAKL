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

Arms are listed in **execution order**. ORACLE_PROCEDURE_UPPER_BOUND runs first; see
"Arm execution order" below for why, and "ORACLE pass criterion" for the frozen gate.

### 1. ORACLE_PROCEDURE_UPPER_BOUND — runs first
A frozen, family-general checklist is supplied directly. It contains no T-task outcome or evidence identifier. This measures whether the base model can execute the relevant method at all.

This arm is the **capability floor probe**. It is run before any architecture-comparison arm because it is the only arm whose failure invalidates the interpretation of every other arm.

### 2. RESET
Registered S0; no prior experience.

### 3. FAILURE_MEMORY_ONLY
Persist failed TaskEpisodes and failure-lattice entries. A failed episode creates **no reusable Lesson**.

### 4. VERIFIED_DEVELOPMENT_LESSONS
After each D-task output is frozen, a protected evaluator may emit a general method lesson. The lesson must:

- bind the source D-task and output hash;
- bind an evaluator receipt hash;
- contain no transfer-task identifier;
- contain no task-local evidence ID;
- have method authority only;
- grant no scientific authority.

### 5. FULL_RAKL_SELECTIVE
Authorized only after ORACLE passes and the intermediate arms localize the bottleneck. It must use a bounded target-conditioned experience view / problem-fibre route rather than whole-state prompt dumping, with explicit retrieval selection telemetry.

## Arm execution order

Execution order is `ORACLE_PROCEDURE_UPPER_BOUND → RESET → FAILURE_MEMORY_ONLY → VERIFIED_DEVELOPMENT_LESSONS → FULL_RAKL_SELECTIVE`.

This resolves root-cause question 4 (execution capacity) **before** questions 2, 3 and 5. The
questions above are not renumbered: their numbering and `Parent answer:` annotations are the frozen
v1.2 record and stay verbatim. Only the arm execution order changes.

Rationale:

- The registered model for the parent observation is Qwen2.5-0.5B-Instruct. Whether it can execute
  the correct generic procedure **when that procedure is handed to it directly** is unknown.
- If it cannot, then FAILURE_MEMORY_ONLY and VERIFIED_DEVELOPMENT_LESSONS are uninterpretable: a null
  in either arm is consistent with both "RAKL failed to induce the lesson" and "the model could not
  have used the lesson even if perfectly induced." The two cannot be separated after the fact.
- ORACLE is therefore the cheapest observation that discriminates. Every 0.5B run spent on arms 3–5
  before ORACLE resolves produces unreadable output regardless of outcome.
- The escalation target already exists: `research/paper2_microtrial_v4_3/EXECUTION_PACKET_V4_3_20260811.json`
  stages the Qwen2.5-1.5B overlay (`paper2-model-qwen25-1_5b-v4-3`) for exactly this branch. Note that
  packet sets `model_execution_permitted_by_this_packet = false`; execution authority is a separate
  step and is not granted here.

## ORACLE pass criterion

Frozen before execution. The measurement operator is the one already used by the parent observation
(per-arm/phase `success_rate` over `task_count` fresh-transfer tasks); no new scoring is introduced.

**ORACLE passes iff `success_rate >= 2/3` on the FRESH_TRANSFER phase** (at least 2 of the 3 transfer
tasks registered as successes) with the frozen three-instruction checklist supplied directly in context.

This is an **absolute** criterion, not a comparison against RESET. ORACLE is an upper-bound capability
probe, so it may run alone. Consequently:

- The v1.2 RESET row must **not** be used as a concurrent contrast for ORACLE. It was measured before
  the failure-memory / verified-lesson separation landed, so the contexts are not aligned.
- If a relative ORACLE-vs-RESET claim is ever wanted, RESET must be re-run **in the same job** under
  the same contract. Inheriting the frozen v1.2 RESET for that purpose is prohibited.

Threshold rationale (recorded so it is not re-tuned after seeing the result):

- `3/3` is brittle to a single formatting slip and would over-trigger `MODEL_CAPABILITY_FLOOR`.
- `1/3` is not separable from the partial-credit floor already observed (v1.2 reported `mean_score`
  0.25–0.33 at `success_rate` 0.0).
- `2/3` is two-sided: the model can plausibly clear it or miss it.

`mean_score` and `repeated_failure_rate` are reported alongside as secondary diagnostics to separate
total failure from near-miss. They are **descriptive only** and do not move the verdict.

### Parse-validity guard

An ORACLE failure classifies as `MODEL_CAPABILITY_FLOOR` **only if the outputs are schema/parse valid**.

If the outputs are parse-invalid or the harness failed to register otherwise-correct answers, the
verdict is `INSTRUMENT_DEFECT`: repair the harness and re-run at the same model size. Do not escalate
the model and do not record a capability floor. V4.2 showed a format/gate failure mode that survived
parser repair and is easily mistaken for a capability limit; this guard exists to keep the two apart.

## Frozen generic development lessons

The development-only correction basis is:

1. Calibration: prefer a currently calibrated instrument measuring the registered QoI; reject expired calibration and wrong-instrument evidence.
2. Unit transform: an exact registered unit transformation preserves the underlying measurement; calibration authority does not transfer to uncalibrated alternatives.
3. Context alignment: before contradiction, align object, regime, time/aggregation, measurement operator and QoI; mismatched contexts do not directly refute each other.

These are method instructions, not evidence about T1–T3.

## Decision table

The table is evaluated in arm execution order. The first rows are a **stop rule**: if ORACLE fails
with parse-valid output, no further 0.5B arm is run and the remaining rows are not evaluated.

| Observation | Root-cause classification | Action |
|---|---|---|
| ORACLE fails (`success_rate < 2/3`), outputs parse-invalid | `INSTRUMENT_DEFECT` | repair harness; re-run at same model size; do **not** escalate the model |
| ORACLE fails (`success_rate < 2/3`), outputs parse-valid | `MODEL_CAPABILITY_FLOOR` | **stop spending 0.5B runs**; halt arms 2-5 at this size. **0.5B->1.5B has already been run (job 3476566) and produced zero exact conceptual passes**, so this branch is *not* "use a bigger model". Remaining moves are 3B+, or revisiting the task/gate itself. |
| ORACLE succeeds, VERIFIED fails | `VERIFIED_LESSON_INDUCTION_OR_MATERIALIZATION_FAILURE` | repair lesson extraction/admission/selection in RAKL |
| VERIFIED succeeds, FAILURE_MEMORY_ONLY fails | `VERIFIED_EXPERIENCE_ADDS_VALUE` | verified experience-to-method conversion is what matters; proceed to selective/full RAKL test |
| FAILURE_MEMORY_ONLY and VERIFIED both succeed | `SIMPLER_MEMORY_MAY_SUFFICE` | narrow architecture claim; test cost |
| FULL_RAKL_SELECTIVE improves over verified whole-state prompt **at fewer tokens** | `SELECTIVE_RETRIEVAL_ADDS_VALUE` | retain routing/fibre contribution |
| full RAKL adds no benefit at higher cost | `COST_DOMINATES_BENEFIT` | narrow/disable layer |

`VERIFIED_LESSON_INDUCTION_OR_MATERIALIZATION_FAILURE` keeps both branches in its name. Induction
(no lesson was produced) and materialization (a lesson existed but was never selected into context)
are different defects with different repairs, and the parent observation implicates the second.

### What the parent observation does not establish

Recorded so these rows are not mistakenly treated as already satisfied:

- The v1.2 LEARNING arm improved fresh transfer by `transfer_score_delta = +0.0833` while consuming
  4376 vs 1502 fresh-transfer input tokens - roughly **2.9x the tokens**. That is an improvement at
  *higher* cost and **must not be reported as a `SELECTIVE_RETRIEVAL_ADDS_VALUE` demonstration**. The
  row above requires *fewer* tokens.
- `total_retrieval_calls = 0.0` on all four arm/phase rows of job 3476548. Selective fibre retrieval
  never ran; the LEARNING arm was whole-state prompt stuffing via `_render_state_for_prompt`.
  **v1.2 therefore never tested the routing/fibre layer at all** and must never be cited as having
  done so, in either direction.
- `transfer_success_delta = 0.0`, and both development deltas are `0.0`. The only moved quantities are
  the partial score above and `transfer_repeat_failure_delta = -0.3333`.


## Microtrial evidence: parse rate is not reasoning

Verified from the V4 microtrial ingest receipts in `research/paper2_microtrial_v4*/`. Every cell below
is read from a committed receipt; `n_seed` is `evaluated_task_seed_unit_count`.

| Generation | Job | Model | DIRECT_CORPUS | RAKL_CONTEXT | n_seed |
|---|---|---|---|---|---|
| V4 | 3475193 | 0.5B | parse-invalid | parse-invalid | 1 |
| V4.1 | 3475212, 3476520, 3476521, 3476524 | 0.5B | parse-invalid | 3/5 | 1 |
| V4.2 | 3476540 | 0.5B | **3/5** | **3/5** | 1 |
| V4.3 | 3476566 | **1.5B** | parse-invalid | **2/5** | 1 |
| V4.3.1 | 3476576 | **1.5B** | **1/5** | **3/5** | 1 |

Three things follow, and they constrain how any later comparison may be reported:

1. **The baseline arm has been scored.** V4.2 job 3476540 reports `parse_valid_arm_count = 2` and
   `scorable_arm_count = 2`, verdict `NATIVE_EXECUTION_CHAIN_PASS__BOTH_ARMS_SCORABLE_NO_EXACT_PASS__CAPABILITY_LIMIT`.
   Any statement that DIRECT_CORPUS has never produced a scorable output in any generation is false and
   must not be repeated.
2. **Two generations have both arms scorable, and they disagree.** V4.2 (0.5B) tied at 3/5 vs 3/5;
   V4.3.1 (1.5B) split 3/5 RAKL vs 1/5 DIRECT. A single-generation claim that the arms score
   identically is superseded and must not be repeated. Neither generation licenses a comparison
   (both report `score_comparison_permitted = False` at n=1), so the honest reading is that the
   direction is unresolved, not that RAKL leads.
3. **V4.3 is a regression, not a continuation.** V4.2 repaired the V4.1 serialization residual and got
   both arms scorable; V4.3 lost DIRECT_CORPUS again with a different error (`model output fields do
   not match the registered answer schema`) and simultaneously dropped RAKL_CONTEXT from 3/5 to 2/5
   while *tripling* model size. The V4.3 parse failure has a findable cause (the 1.5B swap, or a
   v4-2 -> v4-3 schema change) and should be diagnosed as a defect rather than absorbed as a property
   of the baseline.

The table covers every generation that has produced results.

The prompts are not rigged. `research/paper2_microtrial_v4_2/RAKL_CONTEXT_PROMPT.txt` with its
`RAKL CONTEXT MAP` section removed is **byte-identical** to `DIRECT_CORPUS_PROMPT.txt` (1912-byte
insertion; the `OUTPUT SCHEMA` block and everything after it hash the same). The same holds for the
staged V4.3.1 pair, with an identical 1912-byte insertion. The asymmetry is real, not an artefact of
differing output instructions.

### The RAKL arm is shown the answer key, so no arm gap measures reasoning

This constraint dominates every row above and every comparison built on this task.

The `RAKL CONTEXT MAP` block that the RAKL arm receives, and the DIRECT arm does not, answers the
registered questions close to verbatim:

| Registered question asks | The context map already states |
|---|---|
| Q1: whether the first finite-amplitude correction increases or decreases the period | S3 `"projection": "positive first finite-amplitude correction"` |
| Q2: whether S4 / S5 may be treated as direct contradictions | `S4 -> CONTEXT_MISALIGNED_FOR_DIRECT_CONTRADICTION`, `S5 -> CONTEXT_MISALIGNED_FOR_DIRECT_CONTRADICTION` |
| Q3: which source is refuted, which evidence supports mass invariance | `S6 --ALIGNED_REFUTATION--> S2+S7`; S6 `"mass-dependence claim retained as negative history"`, S7 `"controlled support for mass invariance"` |
| Q4: the supporting / context-misaligned / refuted source-id sets | the map *is* those sets, already labelled |

Consequences, which are governance constraints and not interpretations:

- **A RAKL-over-DIRECT gap on this task cannot support a reasoning or architecture claim.** The arms
  do not differ only in retrieval machinery; they differ in whether the answers were supplied. The
  V4.3.1 3/5-vs-1/5 split is consistent with answer exposure alone and must never be reported as
  RAKL capability.
- **The V4.2 tie is the more informative cell.** RAKL scored 3/5 while holding the answer key and did
  not beat a baseline that did not. Read as an upper bound this is a negative signal about the arm,
  not a positive one.
- **No arm reaches 5/5 in any generation, including with the answer key in context.** That bears
  directly on `MODEL_CAPABILITY_FLOOR` and is not repaired by model size: both 1.5B generations still
  report `exact_conceptual_pass_arm_count = 0`.
- Any future comparison intended to measure retrieval or experience must first remove answer content
  from the RAKL arm's context, or hold it equal across arms. Until then the arm contrast is
  `CANNOT_CHECK` for reasoning, whatever the scores do.

This is the same defect class as the Paper III cheap-gate precedent, where the witness features were
the label restated. It is recorded here so the ladder is not run on a task whose RAKL arm cannot
produce a negative result for the reason the ladder is testing.

### Required reporting: two quantities per arm, never blended

Any comparison of arms must report both, separately:

- **(a) format-compliance / parse rate** — fraction of runs whose output satisfies the registered
  answer schema;
- **(b) reasoning score conditional on parse** — the conceptual score computed only over parse-valid
  runs.

Rules:

- A single blended number is prohibited. It lets format compliance masquerade as reasoning, which the
  table above shows is the live failure mode, not a hypothetical one.
- If RAKL's only measurable benefit is that the model emits parseable JSON, that is a **formatting
  effect** and must be reported as such. It is not a research-capability claim and grants no
  scientific authority.
- Do **not** resolve the censoring by silently scoring a parse failure as 0. That converts an
  instrument defect into a reasoning result. Report the parse failure as a parse failure in (a) and
  exclude the run from (b).
- Parse failure is `null`/unscorable in (b), which censors an arm out of the comparison. Report the
  censoring explicitly rather than letting a missing cell read as an absent effect.

### Power is the first-order blocker

Every generation above has `evaluated_task_seed_unit_count = 1`. V4.2 had two scorable arms and *still*
recorded `arm_comparison_estimable = False` and `score_comparison_permitted = False`. The reason no A/B
result exists is therefore **power (n=1)**, with parse censoring as a real but second-order defect.
Sizing that comparison is owned by #247; this protocol only fixes how it must be reported.

## Chronology invariants

- D output bytes freeze before any D feedback is constructed.
- T1–T3 sealed answers remain inaccessible until each T output is frozen.
- Every transfer task starts independently from one frozen post-development state for its arm.
- No transfer output teaches a later transfer task.
- Any change to task/evaluator/model/resource contract after outcome inspection creates a new protocol version.

## Amendment record

This version reorders the arm execution ladder to put ORACLE_PROCEDURE_UPPER_BOUND first and freezes
the ORACLE pass criterion.

The reorder is made **before any run has executed against this protocol**. At the time of the change
the only artifacts referencing it are the protocol document itself, `src/rakl/paper2_experience_root_cause.py`
and `tests/test_paper2_experience_root_cause.py`; there is no receipt, run directory or harvest bound
to it. The chronology invariant "any change to task/evaluator/model/resource contract after outcome
inspection creates a new protocol version" is therefore not triggered: no outcome has been inspected.

The frozen parent observation (job 3476548) is unchanged and is not reinterpreted by this amendment.


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
