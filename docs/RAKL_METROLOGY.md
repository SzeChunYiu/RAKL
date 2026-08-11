# RAKL Metrology: Measuring Growth, Learning, Process Quality, and Causal Assistance

**Status:** proposal-only metrology contract for Paper 5 and future RAKL 3.x evaluation.  
**Scientific purpose:** distinguish genuine framework learning and framework-caused research improvement from raw archive growth, extra compute, or the base LLM solving tasks unaided.  
**Authority:** metrics describe system behavior. They do not mint theorem, tool, review, or framework-promotion authority.

## 1. Why RAKL needs metrology

A recursive research framework cannot justify itself by saying that its archive became larger or that an LLM eventually solved a task. Both observations are compatible with a useless framework:

```text
more nodes may mean more duplicated junk
more memory may mean more irrelevant context
more research steps may mean more wasted search
better answers may come from the base LLM rather than RAKL
```

RAKL therefore separates four measurement questions:

1. **state growth** — what new canonical structure entered the system?
2. **process quality** — did individual RAKL operators perform their intended role?
3. **learning effect** — did accumulated experience change future behavior in a useful way?
4. **causal assistance** — did RAKL improve outcomes relative to the same underlying model without the relevant RAKL component/state?

No single scalar is sufficient. RAKL reports a vector of quantities plus hard validity invariants.

## 2. The lattice-growth vector

RAKL v3 already tracks seven saturation/novelty axes. Use the same coordinates for growth:

\[
 g_t=(\Delta K_t,\Delta O_t,\Delta E_t,\Delta B_t,\Delta R_t,\Delta P_t,\Delta M_t),
\]

where:

- `K` = retained knowledge/epistemic novelty;
- `O` = retained operator/tool novelty;
- `E` = retained experience-pattern novelty;
- `B` = retained obstruction/boundary novelty;
- `R` = retained relation/bridge/compatibility novelty;
- `P` = retained successful path/strategy-composition novelty;
- `M` = retained meta-method/framework novelty.

`retained` is load-bearing. Raw artifact additions do not count unless identity/supersession logic says they add canonical semantic structure.

### 2.1 Raw structure counts

At state `t`, report:

```text
node_count_by_SubstrateKind
edge_count_by_SubstrateRelation
episode_count
lesson_count
lesson_count_by_authority
tool_count_by_kind
tool_count_by_authority
failure_count_by_diagnosis_status
failure_count_by_method_family
failure_count_by_mode
RAKL_variant_count_by_status
unresolved_link_count
```

These are inventory measurements, not learning claims.

### 2.2 Retained semantic growth

For each axis `j`:

```text
retained_novelty_j(t)
cumulative_retained_novelty_j(T)
novelty_rounds_since_last_gain_j
independent_route_families_since_last_gain_j
residual_reopen_count_j
```

The `NoveltyRound.retained_novelty` values, not commit count or paper count, are the canonical first implementation of this measurement.

### 2.3 Growth quality ratios

Report descriptive ratios separately rather than combining them into one score:

```text
novelty_retention_ratio
  = retained semantic additions / raw proposed additions

lineage_coverage
  = derived canonical objects with valid source lineage / derived canonical objects

orphan_ratio
  = canonical nodes without a licensed semantic/use/provenance relation / canonical nodes

supersession_preservation_rate
  = superseded objects retained with lineage / all supersessions

unresolved_link_rate
  = unresolved common-substrate links / attempted cross-view links
```

A system that grows rapidly but has low lineage coverage or high orphan rate is not learning cleanly.

## 3. Experience-to-method conversion metrics

RAKL's fast loop stores episodes. Its slow loop attempts to convert repeated evidence into bounded lessons and reusable tools. Quantify each conversion.

### 3.1 Episode outcome profile

```text
success_rate
partial_success_rate
failure_rate
blocked_rate
unknown_rate
mean_episode_cost
median_episode_cost
cost_by_outcome
```

### 3.2 Lesson yield

```text
candidate_lesson_count
verified_local_lesson_count
conditionally_reusable_lesson_count
proof_backed_lesson_count
contradicted_lesson_count
superseded_lesson_count

lesson_proposal_yield
  = lessons proposed / consequential episodes

lesson_validation_yield
  = lessons reaching reusable authority / candidate lessons
```

A low lesson-proposal yield may indicate weak abstraction. An extremely high yield may indicate over-generalization. Neither is intrinsically good.

### 3.3 Tool yield and reuse

```text
research_tool_count
new_tools_per_100_episodes
successful_reuse_count_per_tool
failed_reuse_count_per_tool
tool_applicability_block_rate
tool_target_validation_pass_rate
cross_context_reuse_breadth
cross_domain_reuse_breadth
```

For a tool `o`:

\[
\mathrm{ReuseSuccess}(o)=\frac{N_{\text{validated successful reuse}}}{N_{\text{eligible attempted reuse}}}.
\]

Do not count retrieval alone as successful reuse.

### 3.4 Failure-learning maturity

```text
observed_only_failure_count
hypothesis_diagnosis_count
supported_diagnosis_count
verified_impossibility_count
superseded_diagnosis_count
median_episode_to_supported_diagnosis_latency
median_supported_diagnosis_to_resolution_latency
obstruction_resolution_rate
repeat_failure_rate
```

The repeated-failure metric is central:

\[
R_F=\frac{\#\{\text{failures whose structural signature occurred before}\}}{\#\{\text{failures}\}}.
\]

A learning system should reduce `R_F` on fresh tasks without increasing invalid transfer.

## 4. Quantifying every RAKL process

`src/rakl/method_specs.py` defines the canonical process surfaces. Every consequential invocation should emit a proposal-only `ProcessTelemetry` record with universal fields:

```text
invocation_id
process_surface
task_id
episode_id
input_state_hash
input_fibre_hash
output_hash
outcome                 # success / partial / failure / blocked / cannot_check
cost                    # normalized registered resource cost
residual_before
residual_after
retained_novelty_vector
retrieved_ids
selected_ids
rejected_ids
verification_ids
evidence_pointers
timestamp
```

Universal process metrics:

```text
invocation_count
valid_completion_rate
blocked_rate
cannot_check_rate
mean_cost
median_cost
retained_novelty_per_invocation
retained_novelty_per_cost
mean_residual_contraction
repeat_failure_rate
downstream_reuse_rate
```

Process-specific metrics follow.

### 4.1 Decomposition

```text
mean_branching_factor
median_problem_atom_depth
atom_reopen_rate
atom_closure_rate
parent_residual_coverage
missing_interface_discovered_late_rate
overfragmentation_rate
underdecomposition_rate
```

`overfragmentation` must be operationally defined before use, for example child atoms that add no independent discriminator or whose interfaces require immediate recombination. `underdecomposition` may be measured by repeated downstream failures whose diagnosis is a previously hidden mixed obstruction.

### 4.2 Routing

```text
route_family_diversity
saturated_route_retry_rate
route_switch_latency_after_supported_failure
realized_residual_contraction_by_route
cost_per_decisive_route
experience_changed_route_rate
```

### 4.3 Search-query generation

```text
retrieval_calls_per_episode
unique_relevant_hit_rate
duplicate_hit_rate
new_source_yield
new_claim_yield
search_cost_per_retained_novelty
```

### 4.4 Source selection reliability

```text
primary_source_fraction
source_identity_verified_fraction
source_lineage_independence_rate
stale_or_superseded_source_rate
source_scope_mismatch_rate
retraction_or_status_correction_rate
```

### 4.5 Claim extraction

```text
exact_selector_binding_rate
claim_atomicity_pass_rate
unsupported_claim_rate
claim_scope_correction_rate
claim_to_evidence_lineage_coverage
```

### 4.6 Ontology and terminology normalization

```text
semantic_duplicate_collapse_rate
false_merge_rate
unresolved_identity_rate
later_identity_revision_rate
```

### 4.7 Mathematical/context translation

```text
translation_certificate_pass_rate
broken_assumption_detection_rate
hidden_unit_or_normalization_error_rate
target_validation_success_rate
```

### 4.8 Equivalence/similarity and structural transfer

```text
transfer_accept_rate
validated_transfer_success_rate
hostile_near_miss_rejection_rate
false_transfer_rate
DifferenceWitness_completeness_rate
cross_domain_transfer_breadth
```

False transfer is a primary safety metric. Positive transfer without near-miss rejection is not evidence of robust transfer.

### 4.9 Contextual theory gluing

```text
local_section_success_rate
local_section_verification_rate
complete_coverage_rate
interface_conflict_detection_rate
missing_interface_detection_rate
global_gluing_success_rate
false_global_authority_rate
local_success_global_failure_rate
```

The last metric measures one recurring hard-problem pattern directly:

\[
G_{LG}=P(\text{global failure}\mid\text{all selected local sections succeed}).
\]

### 4.10 Contradiction diagnosis

```text
contradiction_vs_context_difference_accuracy
later_supported_diagnosis_rate
diagnosis_revision_rate
time_to_supported_diagnosis
```

Accuracy is assessed only when later evidence supplies a stronger adjudication label.

### 4.11 Gap discovery

```text
residual_localization_rate
next_action_hits_implicated_axis_rate
hidden_gap_discovery_rate
residual_relabel_without_contraction_rate
```

### 4.12 Experiment / discriminator selection

```text
decisive_discriminator_rate
cost_per_decisive_result
candidate_family_pruned_per_discriminator
false_reassurance_rate
```

When calibrated probability models are available, add realized information gain. Otherwise use set reduction and residual contraction rather than fabricated entropy estimates.

### 4.13 Synthesis

```text
coverage_receipt_completeness
unresolved_residual_preservation_rate
overclaim_rate
later_retraction_or_scope_narrowing_rate
cross_lane_retrieval_miss_rate
```

### 4.14 Memory

For a **bound search universe** with relevance labels from later audit/review:

```text
retrieval_precision
retrieval_recall
missed_relevant_memory_rate
irrelevant_memory_rate
stale_memory_rate
retrieved_but_unused_rate
memory_changed_action_rate
context_tokens_per_useful_memory
```

A narrative `no relevant memory exists` is not measurable unless the search universe is bound. `RAKL#119` exists because this requirement was missing in one cross-problem synthesis.

### 4.15 Review

```text
blocking_defect_detection_rate
pre_promotion_defect_capture_rate
post_promotion_escape_rate
false_block_rate
independence_qualification_rate
same_context_mislabel_rate
```

### 4.16 Benchmarking

```text
valid_packet_rate
resource_match_rate
state_leakage_rate
assurance_contamination_rate
missing_task_rate
identity_mismatch_rate
```

### 4.17 Authority promotion

Hard target:

```text
invalid_promotion_rate = 0
```

Also report:

```text
process_violation_count
cannot_check_promotion_count
exact_candidate_CI_binding_rate
postpromotion_attestation_rate
operator_override_count
rollback_count
```

### 4.18 Saturation stopping

```text
axis_flatness_duration
false_saturation_rate
post_flat_novelty_reopen_rate
unnecessary_continuation_rate
residual_reopen_correct_axis_rate
```

A practical false-saturation audit asks whether retained novelty appears soon after an axis was declared flat under a route family that should have been covered.

### 4.19 Prompting/context policy

```text
mandatory_atom_recall_rate
context_overflow_rate
context_token_utilization
useful_context_fraction
performance_vs_context_size
context_rehydration_success_rate
```

### 4.20 Capability shaping

See the causal-assistance benchmark below. Do not infer framework benefit from task success alone.

### 4.21 Software architecture execution

```text
exact_replay_success_rate
receipt_validation_rate
artifact_hash_mismatch_rate
CI_exact_subject_pass_rate
post_merge_regression_rate
mean_time_or_cycles_to_recovery
```

### 4.22 Research portfolio tree

```text
branch_family_diversity
budget_share_by_exploit_diversify_moonshot_meta
retained_novelty_yield_by_budget_class
residual_contraction_by_budget_class
premature_abandonment_rate
fixation_rate
```

### 4.23 Objective evolution

```text
objective_change_count
protected_invariant_violation_rate
proxy_regression_rate
fresh_transfer_gain_after_objective_change
rollback_rate
```

### 4.24 Generator transport

```text
transport_candidate_count
validated_transport_count
partial_identification_count
refuted_transport_count
false_transfer_rate
multi_hop_composition_success_rate
```

## 5. Residual contraction as a common progress coordinate

A hard research task often has no scalar objective before solution. RAKL therefore measures progress by the registered residual set.

Let `B_t` be the set of active independently meaningful blockers/obligations for an atom. A simple set contraction is

\[
C_t = |B_t|-|B_{t+1}|.
\]

This is only valid when blockers are semantically canonical and not removed by renaming. More generally report a vector:

```text
resolved blockers
newly exposed blockers
unchanged blockers
reopened blockers
blocked/unknown blockers
```

A step that replaces one vague blocker with three precise independent blockers may have negative scalar contraction but high epistemic value. Therefore retain both the count and the typed transformation.

## 6. Measuring whether RAKL helped rather than the LLM alone

This is the central causal-attribution problem.

### 6.1 Four benchmark arms

For a frozen task packet and matched underlying model/tool/resource contract, use:

```text
MODEL_ONLY
  same base LLM and permitted external tools, no RAKL workflow or persistent RAKL state

RAKL_RESET
  RAKL workflow present, but every task starts from the same initial RAKL state

RAKL_SHAM_MEMORY
  same RAKL workflow and matched memory/context/retrieval budget, but relevant learned memory is replaced by irrelevant or structurally mismatched registered controls

RAKL_LEARNING
  full RAKL workflow with persistent development experience and frozen learned state for transfer
```

These arms estimate different effects.

### 6.2 Lift vectors

For any registered outcome metric `m`:

\[
\Delta_{\text{architecture}}(m)=m(\text{RAKL_RESET})-m(\text{MODEL_ONLY}),
\]

\[
\Delta_{\text{experience}}(m)=m(\text{RAKL_LEARNING})-m(\text{RAKL_RESET}),
\]

\[
\Delta_{\text{content}}(m)=m(\text{RAKL_LEARNING})-m(\text{RAKL_SHAM_MEMORY}),
\]

\[
\Delta_{\text{total}}(m)=m(\text{RAKL_LEARNING})-m(\text{MODEL_ONLY}).
\]

No one delta is `the RAKL score`.

### 6.3 Paired outcome categories

For each task compare the same base-model configuration under two arms:

```text
BOTH_SUCCESS
RAKL_ONLY_SUCCESS
BASELINE_ONLY_SUCCESS
BOTH_FAIL
```

`RAKL_ONLY_SUCCESS` is the strongest simple evidence of assistance. `BASELINE_ONLY_SUCCESS` is direct evidence of RAKL harm/interference and must be reported symmetrically.

### 6.4 Efficiency assistance

RAKL can help even when both arms succeed. Measure:

```text
token_delta
tool_call_delta
retrieval_call_delta
wall_time_delta
candidate_count_delta
failed_route_count_delta
time_to_first_decisive_falsifier_delta
```

A task is not credited as a capability win if RAKL merely spends substantially more resources to reach the same result unless the paper explicitly claims a quality/safety tradeoff and quantifies it.

### 6.5 Safety/epistemic assistance

RAKL may reduce false progress even when it does not raise solution rate:

```text
false_theorem_or_candidate_rate
unsupported_scope_escalation_rate
root_coordinate_surrogate_error_rate
invalid_transfer_rate
false_global_gluing_rate
chronology_violation_rate
source_scope_error_rate
```

For open research this may be a more sensitive early metric than final problem solution.

## 7. Decision-level RAKL contribution witnesses

Population-level benchmark deltas establish overall causal effects. To understand mechanism, every consequential RAKL intervention should be able to emit a proposal-only contribution witness:

```text
witness_id
episode_id
intervention_surface        # retrieval/routing/gate/falsifier/gluing/etc.
consulted_object_ids
selected_object_ids
counterfactual_or_pre_RAKL_action_rank
post_RAKL_action_rank
chosen_action_id
decision_changed
predicted_effect
observed_effect
evidence_pointers
```

Examples:

- failure memory demoted a route the model initially ranked first;
- a retrieved tool promoted a cross-domain method;
- a root-coordinate preservation gate blocked a seductive surrogate;
- a gluing check converted a set of local successes into a scoped interface residual;
- saturation analysis triggered representation search rather than another same-family retry.

A contribution witness documents mechanism. It is not a causal proof unless a matched replay/ablation supports it.

## 8. Component ablations and leave-one-memory-out replay

To determine which RAKL component caused a gain, run matched ablations where feasible:

```text
full RAKL
-minus failure memory
-minus success-tool memory
-minus experience-conditioned routing
-minus problem-fibre compilation
-minus gluing checks
-minus saturation/invention gate
-minus one specific high-impact lesson/tool
```

For successful episodes, a content-bound leave-one-memory-out replay can test whether removing a specific lesson/tool changes route choice or outcome.

LLM nondeterminism means one replay is not enough for a strong claim. Use repeated seeds/sampling settings where possible and report the distribution of effects.

## 9. Statistical unit and dependence

Do not treat tokens, tool calls, or every agent thought as independent samples.

Recommended units:

- **task** for parent/challenger or RAKL/baseline outcome comparisons;
- **episode** for process and failure metrics;
- **problem family/domain** for transfer generalization;
- **framework version** for evolution claims.

Development episodes are temporally dependent because state learns across them. Fresh-transfer tasks must all start from the same frozen learned state so T1 cannot teach T2.

Use paired analyses for matched tasks. Report effect sizes and uncertainty. For binary paired success, report paired contingency counts and an appropriate paired test or interval. For scores/costs, report paired differences and bootstrap/permutation or model-based uncertainty appropriate to the sampling design. Hierarchical analyses across problem families are preferable when enough data exist.

## 10. Preventing metric gaming

Metrics become dangerous once optimized.

Rules:

1. no single scalar controls promotion;
2. hard authority/integrity invariants are non-compensatory;
3. metric definitions and thresholds freeze before challenger results;
4. evaluator code/hash is protected from the challenger it judges;
5. raw storage growth is never an improvement metric;
6. novelty must be retained semantic novelty, not file/object count;
7. fresh assurance is hidden and exposure-budgeted;
8. hostile near-misses measure over-transfer;
9. regressions are published alongside gains;
10. a metric that is materially changed by an upgrade requires a separately governed evaluator migration.

## 11. Recommended Paper 5 figures

### Figure 1 — RAKL growth vector over time

Seven lines or stacked panels showing cumulative retained novelty in `K,O,E,B,R,P,M`, annotated with framework versions.

### Figure 2 — Experience conversion funnel

```text
episodes -> supported diagnoses/lessons -> reusable tools/motifs -> successful fresh reuses
```

Show contradictions/supersessions rather than deleting them.

### Figure 3 — Failure-family learning curve

Repeated-failure rate by cycle/version, with major process failures labeled.

### Figure 4 — RAKL attribution benchmark

Paired outcome/score/cost deltas for MODEL_ONLY, RAKL_RESET, RAKL_SHAM_MEMORY and RAKL_LEARNING.

### Figure 5 — Component ablation

Contribution of memory, routing, fibre compilation, gluing and saturation to registered metrics.

### Figure 6 — Process dashboard

For every canonical method surface, show invocation count, valid completion, cost, retained novelty yield and residual contraction.

### Figure 7 — Version evolution DAG

RAKL 3.0 -> challengers -> assured/rejected/rolled-back variants, with exact evidence packets and meta-QoI deltas on edges.

## 12. Minimum dashboard for every RAKL research cycle

Until richer process telemetry is implemented, every consequential cycle should at least report:

```text
exact framework method version and Git SHA
exact pre-state fingerprint
exact post-state fingerprint
active atom/problem signature
process surfaces invoked
fibre snapshot hash
retrieved tools/failures/episodes/motifs
selected and rejected methods
outcome and registered score if defined
residual before/after
retained novelty vector g_t
episode cost/resources
new episode IDs
new lesson/failure/tool/obstruction IDs
successful reuse IDs
saturation axes reopened/flattened
trace/provenance/gate status
```

This turns a qualitative autonomous research log into a measurable longitudinal experiment.

## 13. Interpretation rules

Never conclude `RAKL learned` from one of the following alone:

```text
repository grew
node count grew
token use grew
agent produced more prose
more issues/PRs appeared
more lessons were proposed
one task was solved
an LLM said RAKL helped
```

Stronger evidence requires:

```text
retained semantic state growth
+ traceable downstream reuse or decision effect
+ matched baseline comparison
+ fresh transfer where generalization is claimed
+ no compensating authority/validity regression
```

The strongest version-level claim additionally requires protected fresh assurance and governed promotion.

## 14. Immediate engineering implications

Paper 5 and RAKL 3.1 should treat the following as concrete metrology work items:

1. add a read-only `v3_metrology` module that reports state portraits, growth deltas and process aggregates;
2. add a machine-readable `ProcessTelemetry` schema bound to `method_specs.py` surface names;
3. extend the current two-arm experience benchmark to a separate four-arm causal-attribution benchmark rather than changing its frozen semantics in place;
4. add contribution-witness records for experience-conditioned routing and gate interventions;
5. implement cross-problem coverage receipts so retrieval recall can be measured against a bound universe;
6. make every autonomous RAKL_math cycle emit the minimum dashboard fields above;
7. preserve all metric snapshots by exact method version so Paper 5 can show longitudinal curves rather than retrospective narrative summaries.

The metrology layer is observational and proposal-only. A metric implementation must not gain authority over the process it measures simply because it lives inside the same package.