# RAKL v3 Evaluation Contracts

RAKL v3 separates **architecture**, **learning evidence**, and **capability claims**.

The software can accumulate experience, change future routing, induce candidate methods, and branch Self-RAKL variants. None of those operations by themselves prove that the system became better on fresh tasks.

This document defines two machine-oriented evaluation questions:

1. how much of a problem distribution is solvable without inventing new problem-solving structure?;
2. does persistent RAKL experience improve the same underlying LLM on matched fresh tasks?

## 1. RAKL-triviality and structural novelty

`src/rakl/problem_novelty.py` classifies a **verified solution** by the strongest genuinely new structure it required.

```text
STORED
RAKL_TRIVIAL
TRANSFER_NOVEL
REPRESENTATION_NOVEL
OPERATOR_NOVEL
ONTOLOGY_NOVEL
UNRESOLVED
```

The ordering is intentionally not an intelligence ranking. It is an ancestry classification.

### STORED

The exact verified solution was already registered and retrieved.

### RAKL_TRIVIAL

The solution was not stored as one answer, but every required resource/operator was already present and the solution was obtained by composition.

### TRANSFER_NOVEL

An explicit mapping witness transported pre-existing problem-solving structure into a new context/domain. The application is novel, but no new primitive was invented.

### REPRESENTATION_NOVEL

The solution required a newly introduced representation, bridge, invariant coordinate system, or equivalent representational object, but no new transformation operator.

### OPERATOR_NOVEL

At least one genuinely new transformation/operator was required.

### ONTOLOGY_NOVEL

The framework's schema/ontology itself had to be extended to express the solution process.

### UNRESOLVED

The solution is unverified or its resource ancestry is too incomplete to support a novelty classification.

## 2. Zero-invention rate

The structural rank used by the metrology is:

```text
STORED               0
RAKL_TRIVIAL          0
TRANSFER_NOVEL        0
REPRESENTATION_NOVEL  1
OPERATOR_NOVEL        2
ONTOLOGY_NOVEL        3
UNRESOLVED           -1
```

Rank `0` means that no newly invented problem-solving primitive was required.

For a solved benchmark distribution `D`, RAKL reports:

```text
zero_invention_rate
strict_rakl_trivial_rate
stored_count
transfer_novel_count
representation_novel_count
operator_novel_count
ontology_novel_count
unresolved_count
```

This operationalizes the hypothesis that the space of reusable human problem-solving methods may saturate faster than the space of problems.

The hypothesis is not assumed true. It becomes an empirical curve as RAKL's operator/strategy atlas grows.

## 3. Matched repeated-task experience benchmark

`src/rakl/experience_benchmark.py` reuses the repository's existing matched-model and resource-ceiling contracts from `matched_microtrial.py`.

The benchmark has two arms:

```text
RESET_BASELINE
LEARNING_ENABLED
```

and two phases:

```text
DEVELOPMENT_SEQUENCE
FRESH_TRANSFER
```

### RESET_BASELINE

Every task starts from the exact same registered initial RAKL state, and the state is required to remain unchanged after the task.

This represents the same LLM/workflow without cumulative experience learning.

### LEARNING_ENABLED development sequence

Tasks run sequentially:

```text
S0 --task D1--> S1 --task D2--> S2 --task D3--> ... --> Sn
```

The validator checks the state hashes form one uninterrupted chronology.

### FRESH_TRANSFER

After development, state `Sn` is frozen.

Every transfer task starts independently from **the same** `Sn`:

```text
Sn --T1--> result1
Sn --T2--> result2
Sn --T3--> result3
```

The state produced by `T1` may not be used as the starting point for `T2`. This prevents transfer results from being contaminated by learning on earlier transfer cases.

The baseline transfer arm continues to start from `S0`.

## 4. Matching requirements

A valid packet freezes before execution:

```text
benchmark id
model id/revision
temperature
seed
system prompt hash
max output tokens
resource ceiling
tool policy id
output schema id
evaluator protocol hash
initial state hash
development task order
fresh transfer task set
```

Every run is checked against the same registered resource ceiling using the existing `TrialResourceUsage` / `TrialResourceCeiling` validator.

A packet fails closed on:

```text
missing or duplicate tasks
wrong arm count
phase mismatch
resource-ceiling violation
baseline state mutation
learning chronology break
wrong frozen post-development state hash
transfer task starting from a previous transfer result
duplicate run identity
```

## 5. Reported metrics

For each arm and phase:

```text
task count
success rate
mean registered score
repeated-failure rate
total model tokens
total preprocessing-model tokens
total tool calls
total retrieval calls
total wall time
```

The paired report computes:

```text
development_success_delta
development_score_delta
transfer_success_delta
transfer_score_delta
transfer_repeat_failure_delta
```

A positive transfer delta is an observed benchmark result, not a universal capability claim.

The report property `grants_global_capability_claim` is hard-coded false.

## 6. Repeated-failure metric

A central purpose of the v3 architecture is to stop repeating structurally equivalent failures.

Within one arm/phase, the benchmark records failure signatures in task order and measures the fraction of failures whose signature has already occurred earlier in that same sequence.

A learning system should ideally show:

```text
transfer_repeat_failure_delta < 0
```

without trading that improvement for worse accuracy, validity, or excessive resources.

## 7. From benchmark to Self-RAKL evidence

The experience benchmark is descriptive evidence.

A Self-RAKL architecture promotion should use its frozen development/transfer deltas as input to the existing protected `EvolutionTrial` / `SelfEvolutionAssessor` path, alongside:

```text
blocking invariant checks
candidate identity
resource comparability
history preservation
fresh blind assurance
evaluator separation
```

Thus:

```text
experience benchmark gain
!= automatic method promotion
```

The benchmark can motivate or support a challenger; the evolution authority layer decides whether the evidence is strong enough for a scoped architecture claim.

## 8. Recommended first v3 empirical packet

Use at least three task strata:

```text
A. repeated-family tasks
   Same deep structure with changed surface form.

B. transfer tasks
   Different domain vocabulary but explicit structural correspondence.

C. hostile near-miss tasks
   Superficially similar tasks where a learned lesson should NOT transfer.
```

This allows measurement of both positive transfer and false lesson reuse.

Recommended primary metrics:

```text
fresh-transfer success delta
fresh-transfer score delta
repeat-failure delta
invalid-transfer / false-lesson rate
resource-normalized gain
```

The hostile near-miss stratum is particularly important: a memory system that always reuses past lessons can look good on repeated tasks while becoming dangerously overconfident outside their scope.

## 9. Relationship to saturation

Problem novelty and experience learning should also update the v3 saturation vector.

Examples:

```text
new verified fact                  -> KNOWLEDGE novelty
new reusable operator              -> OPERATOR novelty
new recurring trajectory pattern   -> EXPERIENCE_PATTERN novelty
new failure boundary               -> OBSTRUCTION novelty
new compatibility/bridge relation  -> RELATION novelty
new successful composition path    -> PATH novelty
new RAKL method policy              -> META_METHOD novelty
```

A zero-invention solution can still add path/experience novelty.

Therefore:

```text
RAKL-trivial problem != zero learning value
```

A problem may require no new primitive while teaching RAKL a much better way to retrieve, order, or compose existing primitives.
