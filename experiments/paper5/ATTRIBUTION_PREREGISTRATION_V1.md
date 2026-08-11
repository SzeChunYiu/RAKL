# Paper 5 attribution experiment preregistration v1

**Status:** frozen design proposal only. No run from this packet may be interpreted as preregistered until the final packet hash, task IDs, evaluator hash, model/tool contract, resource ceiling, sham policy, and learned/reset state hashes are completed before execution.  
**Scientific question:** does RAKL improve the behavior of the same underlying LLM, and if so, how much lift comes from static workflow architecture, accumulated experience, and the semantic content of learned memory?

## 1. Registered contrasts

Four arms are evaluated on the same frozen tasks:

1. `MODEL_ONLY`
   - same base model;
   - same allowed external tool classes and source cutoff;
   - no RAKL workflow and no persistent RAKL state;
   - run state must equal the registered stateless sentinel before and after.

2. `RAKL_RESET`
   - full current RAKL workflow;
   - every task starts from the same frozen initial RAKL state;
   - the evaluation run cannot mutate that state.

3. `RAKL_SHAM_MEMORY`
   - same RAKL workflow;
   - same registered memory object-count/token/context budget as the learned arm within each task where feasible;
   - learned relevant objects are replaced by preregistered structurally incompatible controls under the frozen sham policy;
   - every task starts from the same frozen sham state and cannot mutate it.

4. `RAKL_LEARNING`
   - full RAKL workflow;
   - uses one learned state frozen after the separate development sequence;
   - every evaluation task starts independently from exactly that same learned-state hash and cannot write its result into the next evaluation task.

Primary causal contrasts:

```text
TOTAL_LIFT       = RAKL_LEARNING - MODEL_ONLY
EXPERIENCE_LIFT  = RAKL_LEARNING - RAKL_RESET
CONTENT_LIFT     = RAKL_LEARNING - RAKL_SHAM_MEMORY
```

`RAKL_RESET - MODEL_ONLY` is the registered static architecture contrast.

No contrast is allowed to substitute for another. In particular, total lift does not establish an experience effect, and experience lift does not establish that the content of learned memory matters.

## 2. Task strata

Target first complete packet: **120 task units**, frozen before outcome access.

- **40 repeated-family tasks** — same deep structure as development experience under materially changed surface form;
- **40 cross-domain transfer tasks** — changed domain vocabulary/context with an explicit structural mapping available to the benchmark designer but hidden from the solver;
- **40 hostile near-miss tasks** — surface or partial structural similarity where learned experience should be rejected or bounded rather than transferred.

Tasks must be disjoint from development tasks. Exact task IDs and source/evidence cutoff must be frozen in the final packet.

The 120-task target is a planning compromise, not evidence. Under a simple paired binary planning model, 120 tasks gives roughly 80% power at two-sided alpha 0.05 for a net paired success difference of about 15 percentage points when total discordance is about 35%. For a paired continuous score, the corresponding normal-approximation standardized detectable effect is about 0.26. These assumptions are planning approximations; final inference uses the observed paired data and preregistered analysis, not the assumed effect.

## 3. Repeated stochastic runs

Target **3 repeated generations per task-arm condition** when the model/service budget permits. The inferential unit remains the task, not the generation. Per-task arm results are aggregated under the frozen rule before cross-task analysis.

If an exact seed is supported, register the three seeds. If the model service does not guarantee deterministic seeds, register three repeated invocations and block-randomize arm order within each task. Do not treat repeated generations as independent task samples.

If resources make three repetitions infeasible, the packet must be amended and re-frozen before any evaluated outcome is opened; do not silently reduce repetitions after seeing results.

## 4. Sham-memory policy

The sham condition exists to distinguish useful learned content from generic extra context/preprocessing.

The final `sham_policy_hash` must bind the complete construction algorithm and seed. Required properties:

- no target answer or target-specific solution artifact;
- no object whose registered structural signature is an eligible true match for the target;
- object types matched to the learned-memory input where possible (episode vs failure vs lesson vs tool/motif);
- matched or bounded total token budget and retrieved-object count;
- comparable recency/authority metadata distribution where feasible;
- source/evidence-lineage identities preserved as sham controls rather than copied relevant content;
- construction performed before target outputs;
- adversarial audit for accidental semantic equivalence or leakage.

The sham is intentionally not claimed to be a perfect placebo. Report token/object mismatches and run sensitivity analyses. A secondary hard-near-miss sham may be frozen as a separate condition in a later experiment rather than silently altering this primary four-arm design.

## 5. Primary endpoints

### 5.1 Registered task score

A frozen evaluator produces a task score in `[0,1]` from an arm-blinded output. The exact evaluator protocol, rubric, success threshold, parser, and evaluator identity are hashed before runs.

Primary quantitative endpoint:

```text
paired task-level mean score difference
```

for the three causal contrasts above.

### 5.2 Success

Binary success is defined before runs from the registered score threshold plus all mandatory validity gates. It is reported as:

```text
BOTH_SUCCESS
RAKL_ONLY_SUCCESS
BASELINE_ONLY_SUCCESS
BOTH_FAIL
```

for each selected pairwise contrast.

### 5.3 Blocking validity

The following are non-compensatory and block a strong assistance claim for the affected packet/arm as specified by the evaluator:

- target/evaluator leakage;
- wrong task identity;
- state leakage across fresh-transfer tasks;
- invalid authority escalation where the task includes authority semantics;
- source cutoff violation;
- resource ceiling violation;
- corrupted/missing output identity;
- sham-memory answer leakage;
- candidate/evaluator hash mismatch.

Performance gain cannot compensate for a blocking integrity failure.

## 6. Secondary endpoints

- repeated structural-failure rate;
- false-transfer / hostile-near-miss acceptance rate;
- unsupported scope-escalation rate;
- root-coordinate surrogate error rate where applicable;
- local-success/global-gluing-failure rate where applicable;
- model input/output tokens;
- preprocessing model tokens;
- tool calls;
- external retrieval calls;
- wall time;
- candidates/routes attempted where instrumented;
- time/cycles to first decisive falsifier where instrumented;
- fraction of tasks where RAKL memory/gates observably changed the selected action.

Secondary endpoints do not replace the primary contrasts.

## 7. Multiplicity

The three primary score contrasts are a fixed family. Use Holm family-wise error control at alpha 0.05 for confirmatory interpretation unless the final packet freezes a stricter hierarchical gate before runs.

Stratum-specific results are secondary/heterogeneity analyses unless separately powered and preregistered. Do not choose the best stratum after outcomes and call it the primary result.

## 8. Paired analysis and uncertainty

Primary unit: task.

For continuous registered score:
- compute paired task-level differences;
- report mean/median difference, effect size and 95% uncertainty interval;
- use a preregistered paired permutation/bootstrap or equivalent paired model robust to the score distribution.

For binary success:
- report the paired 2x2 outcome counts;
- use a paired binary analysis such as exact/asymptotic McNemar inference as appropriate;
- report effect size (paired success-rate difference) and uncertainty, not p-values alone.

If sufficient family structure exists, a preregistered hierarchical model may be added as a secondary analysis to distinguish within-family from cross-family effects.

## 9. Run order and temporal drift

Within each task/repetition block, randomize the four arm execution order under a frozen randomization seed. This reduces systematic model-service/time drift across arms.

Record:
- exact request time;
- public model ID/revision if available;
- model/provider response metadata available to the harness;
- tool versions/policies;
- external source cutoff;
- exact framework and task state hashes.

A material model revision or evaluator change during the packet triggers a preregistered integrity decision: either block the packet or split it into separately labelled conditions. Never pool silently across a detected model/evaluator epoch change.

## 10. Resource matching

All arms share one registered resource ceiling. Actual usage is reported, not merely the ceiling.

A task success is not automatically an efficiency gain if the RAKL arm uses substantially more resources. Resource-normalized secondary analyses report score/success together with token, retrieval, tool and time differences.

The sham arm should match memory/context budget as closely as feasible. Any systematic mismatch is an explicit limitation/sensitivity variable.

## 11. Development and evaluation separation

The learned state is produced only by a separately frozen development sequence. Evaluation task outputs do not update the frozen learned state.

Development may inspect its own results and tune the challenger within the development protocol. The confirmatory evaluation packet is frozen only after the method candidate is frozen. A stronger framework-evolution claim additionally requires a fresh assurance packet hidden from the proposer and evaluator separation under the existing SelfEvolutionAssessor / bootstrap rules.

## 12. Stopping rules

No efficacy early stopping in the 120-task confirmatory packet.

Permitted early stop reasons:
- task/evaluator leakage;
- state contamination;
- sham leakage;
- model/evaluator epoch change that the protocol declares incompatible;
- resource-system failure that prevents matched execution;
- protected validity/security failure requiring containment.

Stopping for an integrity failure must preserve all runs completed before the stop.

## 13. Claim table

| Claim | Minimum evidence |
|---|---|
| RAKL total assistance | material `RAKL_LEARNING - MODEL_ONLY` primary effect with clean validity/resources |
| static architecture helps | material `RAKL_RESET - MODEL_ONLY` effect |
| accumulated experience helps | material `RAKL_LEARNING - RAKL_RESET` effect |
| learned memory content matters | material `RAKL_LEARNING - RAKL_SHAM_MEMORY` effect |
| transfer generalizes | fresh cross-domain stratum effect without hostile-near-miss regression |
| RAKL reduces repeated mistakes | lower repeated-failure rate without false-transfer/validity regression |
| a new RAKL version is better | separate parent/challenger development gain + fresh protected assurance + governed promotion evidence |

## 14. What would falsify the headline assistance hypothesis?

For the registered task distribution, evidence against useful total assistance includes:
- materially negative total score/success lift;
- more `BASELINE_ONLY_SUCCESS` than `RAKL_ONLY_SUCCESS` at a material level;
- similar performance but materially greater resource cost with no preregistered safety gain;
- any blocking validity/integrity regression that makes the apparent gain unsafe to interpret.

Evidence against the experience-specific hypothesis includes no material learning-vs-reset gain or a negative gain.

Evidence against the memory-content hypothesis includes learned memory failing to outperform the preregistered sham condition.

A null or negative result is a valid outcome and must remain in the Paper 5 longitudinal record.