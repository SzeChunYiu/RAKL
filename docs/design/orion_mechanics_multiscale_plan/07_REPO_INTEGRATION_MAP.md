# Repository Integration Map

Planning snapshot: `94a35f168e81c57cb678c8d324f4d6190cb3fc46`.

## 1. `src/rakl/problem_fibre.py`

Current useful objects include:

```text
ProblemAtom
ProblemDecomposition
FibreKnowledgeItem
ProblemFibre
LocalSection
GluingObstruction
GluingReport
compile_problem_fibre
glue_local_sections
```

`ProblemAtom` already provides:

```text
goal
context_hash
structural_coordinates
desired_effects
dependencies
interface_keys
```

### Integration

Use `ProblemAtom` as the unit supplied to mechanic diagnosis and representation search.

Do not create `MechanicsProblemAtom`.

Extend only if a measured need appears.

Potential later additive fields should be introduced through separate sidecar objects first, not by immediately changing the dataclass.

## 2. `src/rakl/search_controller.py`

Current search already:

- uses residuals;
- maps invention operators into operator families;
- preserves a frontier;
- enforces budgets;
- favors operator/residual diversity;
- returns method-basis-gap semantics when registered routes are exhausted.

### Integration

`MechanicsController` wraps it.

```text
MechanicsController
    CHANGE_OPERATOR
        -> existing plan_next_search_round(...)
```

Do not merge the two controllers initially.

Reason: we need an ablation between:

```text
current diverse operator search
vs
meta-mechanic routing
```

## 3. `src/rakl/missing_operator.py`

Current logic already distinguishes:

```text
missing evidence / measurement
implementation failure
method-basis failure
unknown
```

and separates:

```text
gap detection
operator-family identification
fresh transfer
promotion authority
```

### Integration

Do not rename or generalize this module immediately.

Create `mechanic_deficiency.py` above it.

Routing rule:

```text
if diagnosis == METHOD_OPERATOR:
    delegate to missing_operator machinery
```

This preserves old semantics.

## 4. `src/rakl/metacognition.py`

Current auditor can flag:

```text
known weakness
calibration weakness
explanation gap
ontology-gap candidate
method-basis-gap candidate
independent-review requirement
```

### Integration

Use these verdicts as **inputs** to mechanic diagnosis.

Do not let the new module convert self-report into stronger evidence.

## 5. `src/rakl/saturation.py`

Current tracker separates:

- same-context flatness;
- process independence;
- evidence-lineage independence;
- scoped saturation;
- reopen-by-residual;
- diagnostic-only unseen-mass estimates.

### Integration

Add no new saturation certificate initially.

The multiscale layer may emit a:

```text
CoverageChallenge
```

that can reopen a fibre but cannot itself certify saturation.

Later candidate:

```text
MULTISCALE_COVERAGE_RECEIPT
```

only after benchmark evidence.

## 6. `src/rakl/epistemic_search.py`

Use existing scientific search as one meta-action:

```text
CHANGE_RETRIEVAL
GATHER_EVIDENCE
SEARCH_NEGATIVE_HISTORY
SEARCH_METHOD
SEARCH_ANALOGY
```

Do not duplicate crawling/ranking.

The field layer may rank **which retrieval action to call**, not replace source authority.

## 7. `src/rakl/method_specs.py`

Current contracts enumerate atomic mechanics with:

```text
inputs
outputs
mathematical semantics
implementation refs
test refs
empirical open coordinates
authority effect
```

### Integration

Eventually add contracts for:

```text
mechanic_diagnosis
representation_search
scale_policy
solution_field_routing
auxiliary_object_invention
cognitive_budget_routing
```

But only after module APIs stabilize.

The contracts should initially set:

```text
authority_effect = PROPOSAL_ONLY
```

## 8. `src/rakl/v3.py` / `src/rakl/v3_runtime.py`

Do not integrate in phase 1.

Create an opt-in challenger runner under `research/`.

Only wire into runtime after fresh benchmark success and ordinary promotion review.

## 9. Memory / experience modules

Useful existing sources:

```text
experience_substrate
failure_lattice
research_tool_inventory
strategy_motifs
breakthrough_learning
multires_memory
context_compiler
```

### Integration

The mechanics layer should consume them through compiled `ProblemFibre`.

Avoid direct unbounded memory queries from every new mechanic.

## 10. Atlas / gluing

Use current gluing and bridge machinery for cross-representation and cross-scale contracts where possible.

Do not introduce a second mathematical notion of compatibility.

## 11. Suggested research directory

```text
research/mechanics_of_mechanics_v1/
    README.md
    protocol/
    worlds/
    baselines/
    results_dev/
    results_fresh/
    receipts/
```

Later field-specific:

```text
research/solution_field_v1/
```

## 12. Suggested tests

```text
tests/test_mechanic_deficiency.py
tests/test_representation_search.py
tests/test_scale_policy.py
tests/test_solution_field.py
tests/test_auxiliary_object.py
tests/test_mechanics_controller.py
tests/test_mechanics_telemetry.py
tests/test_mechanics_integration_problem_fibre.py
```

Do not put experimental learned-model tests in the deterministic unit suite.
