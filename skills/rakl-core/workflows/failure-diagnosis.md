# Workflow — Failure Diagnosis

Use when a model, method, derivation, data pipeline, experiment, or strategy fails.

## Principle

A failure is not an instruction to try a more complicated model. It is a measurement of where the current object description is incomplete.

## Root-cause ladder

Inspect in order:

```text
R0 source/version/access
R1 schema/parser/units/transformation
R2 clocks/joins/availability/leakage
R3 target/denominator/population/inferential unit
R4 rules/protocol/accounting/settlement
R5 hidden state/censoring/missingness/observation
R6 confounding/identifiability/equivalence
R7 state reduction/projection/functional form
R8 scale/regime/transport/capacity/performativity
R9 numerical/software/simulation/optimization
R10 genuine formalism/mechanism mismatch
```

Do not invent new mechanics before R10 unless an impossibility theorem already proves the current object class inadequate.

## Residual signature

Record what failed:

```text
mean
variance
uncertainty growth
tails
first passage
memory
scale/aggregation
clock/session
proxy/observable
balance/invariants
intervention response
calibration
execution/value
numerical convergence
```

## Recursive response

1. Map the residual to fiber dimensions capable of producing it.
2. Expand those dimensions first.
3. Search alternative vocabulary/mechanisms for those dimensions.
4. Construct at least one distinct competing explanation and one null/observation explanation.
5. Freeze a discriminator where the hypotheses make different predictions.
6. Run known-answer/hostile worlds.
7. Run native/real evidence.
8. Eliminate, bound, or preserve surviving mechanism classes.
9. Recurse on the new residual.

## Prohibited rescue

Never rescue a failed object by:

```text
moving acceptance thresholds after seeing the result
changing population after seeing the result
dropping a falsifier
using a different target without versioning the claim
hiding failed configurations
converting missing evidence into LLM confidence
```
