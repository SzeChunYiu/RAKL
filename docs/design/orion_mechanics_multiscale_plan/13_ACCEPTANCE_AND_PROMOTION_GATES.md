# Acceptance and Promotion Gates

## 1. Scientific state versus software state

A module can be:

```text
IMPLEMENTED
TESTED
BENCHMARKED
```

without being:

```text
SUPPORTED_AS_IMPROVEMENT
PROMOTED_TO_DEFAULT
SCIENTIFICALLY_VALIDATED_BROADLY
```

Keep these separate.

## 2. Mechanic deficiency gate

Possible outcomes:

```text
DIAGNOSIS_SIGNAL_SUPPORTED
DIAGNOSIS_UNINFORMATIVE
CAUSES_PARTIALLY_IDENTIFIED
DIAGNOSIS_OVERFIT
```

Do not promote routing if better labels do not improve decisions.

## 3. Representation gate

```text
REPRESENTATION_EFFECT_SUPPORTED
REPRESENTATION_USEFUL_ONLY_WITH_ORACLE_SELECTION
REPRESENTATION_COST_FAILURE
REPRESENTATION_PRESERVATION_FAILURE
NO_MEASURABLE_REPRESENTATION_GAIN
```

## 4. Field gate

```text
FIELD_ROUTING_UTILITY_SUPPORTED
FIELD_DIRECTION_USEFUL_EFFICIENCY_UNPROVEN
FIELD_CONSTRUCTION_COST_FAILURE
FIELD_FALSE_ATTRACTOR_FAILURE
FIELD_REQUIRES_ORACLE_REPRESENTATION
FIELD_COMPLEXITY_NOT_EARNED
```

## 5. Multiscale gate

```text
ADAPTIVE_SCALE_UTILITY_SUPPORTED
SCOUT_REQUIRED_FOR_SAFE_SCALE_CONTROL
OVERREFINEMENT_COST_FAILURE
FIXED_SCALE_MATCHES_CHALLENGER
```

## 6. Composition gate

```text
CONTRACTED_COMPOSITION_REDUCES_ROOT_FALSE_ACCEPT
VERIFICATION_OVERCONSERVATIVE
INTERFACE_COMPLEXITY_NOT_EARNED
EMERGENT_RESIDUAL_DETECTION_SUPPORTED
```

## 7. Full mechanics controller gate

Require all:

```text
matched resource ceiling
root-level outcome measured
no authority leakage
negative history preserved
fresh benchmark frozen
development/fresh separation
incumbent baseline executed
atomic ablations executed
```

## 8. Promotion rule

If full challenger wins but only representation search is responsible:

```text
promote representation mechanic
do not promote full architecture
```

If multiple atoms interact synergistically, require an interaction ablation.

## 9. Fresh-transfer requirement

At least one fresh benchmark should shift surface realization while retaining the intended deep mechanic.

Examples:

```text
renamed states/operators
different graph topology distribution
different domain skin
new theorem family with same structural transformation
new simulator parameters
```

## 10. Claim ladder

### Level 0

```text
implemented
```

### Level 1

```text
deterministic correctness on synthetic worlds
```

### Level 2

```text
development benchmark utility
```

### Level 3

```text
fresh scoped utility
```

### Level 4

```text
cross-domain transfer of the mechanic
```

### Level 5

```text
independent external assurance / broader scientific claim
```

Do not skip levels by rhetoric.

## 11. Minimum promotion receipt

A promoted mechanic should have a receipt containing:

```text
subject/version hash
incumbent hash
benchmark hash
fresh-set hash
resource contract
primary metrics
negative metrics
ablation results
failure cases
scope
review/independence status
```
