# Test and Benchmark Plan

## 1. Test layers

```text
L0 static/type/input validation
L1 deterministic unit tests
L2 property tests
L3 known-world mechanic benchmarks
L4 integration tests with current Orion
L5 fixed-model repeated trials
L6 fresh transfer
L7 external/independent assurance
```

A later layer does not replace earlier layers.

## 2. Unit tests: mechanic deficiency

Required cases:

```text
test_missing_measurement_routes_to_evidence
test_known_operator_can_resolve_does_not_open_new_gap
test_multiple_causes_remain_partially_identified
test_discriminator_required_before_claiming_cause
test_unknown_residual_does_not_invent_mechanic
test_diagnosis_never_grants_authority
```

## 3. Representation tests

```text
test_exact_reversible_transform_preserves_qoi
test_lossy_transform_records_nonpreservation
test_decoder_failure_blocks_candidate
test_representation_effect_is_proposal_only
test_representation_probe_cost_is_accounted
test_representation_cycle_detected
```

## 4. Scale tests

```text
test_refine_contract_preserves_root_qoi_reference
test_coarsen_records_loss
test_hidden_feature_defeats_residual_only_refiner
test_global_scout_recovers_hidden_feature
test_local_flatness_never_global_saturates_without_coverage
```

## 5. Field tests

### Algebraic

```text
conductance > 0
boundary values fixed
flux sign consistent with potentials
disconnected target handled
zero/negative cost rejected where invalid
field hash deterministic
```

### Path

```text
exact arrival field recovers oracle path
conductive field can distribute over multiple routes
branching policy respects budget
failed route lowers scoped conductance
failure history remains stored
```

### Cost

```text
field construction cost included
field cannot report speedup using only path-extraction cost
```

## 6. Composition tests

```text
all_children_valid_interfaces_valid_root_valid
all_children_valid_interface_conflict_root_blocked
missing_declared_interface_blocked
emergent_parent_failure_not_misattributed_to_child
hierarchical_verifier_false_negative_measured
```

## 7. Property tests

Use generated small graphs/decompositions.

Properties:

### P1 — Proposal non-escalation

For every new routing object:

```text
grants_scientific_authority == False
```

### P2 — Root traceability

Every action plan can reconstruct its root problem and QoI.

### P3 — Negative-history monotonicity

Failure record count never decreases after append-only updates.

### P4 — Cost monotonicity

Adding an executed action cannot reduce recorded consumed cost.

### P5 — Exact field correctness

For small nonnegative-cost graphs, exact field route equals a reference shortest-path solver.

### P6 — Scale parent linkage

Every non-root scale has exactly one declared parent transition.

## 8. Known-world families

### W1 — Hidden narrow feature

Purpose: punish local-flatness stopping.

### W2 — Global slow residual

Purpose: punish endless local refinement.

### W3 — Wrong representation

One chart gives huge branching; another makes solution linear/local.

### W4 — Misleading representation

A seductive lift destroys a constraint.

### W5 — Mechanic routing

Task label determines which specialist has advantage.

### W6 — Interface compounding

All local modules pass; interfaces probabilistically/deterministically fail.

### W7 — Auxiliary object

Direct search is exponential-ish in generated size; supplied/discovered helper makes it short.

### W8 — Dynamic route failure

Initially best field path becomes invalid; measure recovery.

### W9 — Search-versus-field

Explicit graph where field construction is cheap.

### W10 — Field circularity

Graph where constructing useful potentials requires essentially complete search.

A correct system should recognize no net gain.

## 9. Fixed-model trials

When LLM generation is introduced:

- freeze model/checkpoint;
- freeze prompts/system configuration;
- isolate each replicate;
- freeze benchmark before runs;
- prevent fresh-set examples from entering memory/retrieval;
- preserve failed outputs.

Report confidence intervals over task-level paired differences.

## 10. Primary metrics

### End-to-end

```text
verified_root_success
verified_root_progress
total_cost
time_to_verified_resolution
```

### Diagnosis

```text
mechanic_cause_recall
mechanic_cause_precision
partial_identification_rate
wrong_discriminator_rate
```

### Representation

```text
representation_selection_regret
path_compression
decode_failure
preservation_violation
```

### Field

```text
gradient_action_rank_correlation
path_stretch
false_attractor_rate
field_build_cost
branch_entropy
recovery_after_failure
```

### Scale

```text
hidden_facet_miss_rate
unnecessary_refinement_cost
coverage_recall
coarsening_regret
```

### Composition

```text
local_pass_root_fail
interface_failure_recall
false_interface_rejection
root_false_accept
```

## 11. Comparators

Always include relevant simple baselines.

Field tasks:

```text
uniform-cost
A*
greedy local
beam
```

Mechanics routing:

```text
fixed incumbent
uniform random mechanic
best fixed mechanic
oracle mechanic
```

Representation:

```text
original only
random transform
oracle transform
```

Scale:

```text
fixed coarse
fixed fine
residual-only adaptive
adaptive + scout
oracle scale
```

## 12. Statistical plan

Prefer paired task-level comparisons.

Report:

```text
paired mean/median differences
bootstrap CI
win/tie/loss counts
cost-success Pareto frontier
effect by task family
```

Do not hide family-specific regressions inside one mean.

## 13. Mutation tests

Deliberately break:

```text
authority gate
root binding
cost accounting
negative-history append rule
representation-preservation check
coverage scout
interface check
```

The benchmark should detect the mutation.

If not, the evaluation is not measuring the intended invariant.
