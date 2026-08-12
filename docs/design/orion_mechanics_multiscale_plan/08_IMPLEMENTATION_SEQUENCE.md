# Implementation Sequence

The order is designed to minimize architecture lock-in and maximize falsifiability.

# Phase 0 — Freeze the incumbent

## Build

Create:

```text
research/mechanics_of_mechanics_v1/INCUMBENT_SNAPSHOT.md
```

Record:

```text
git SHA
Python/package version
current method version
current test command
baseline benchmark commands
model/tool configuration where relevant
```

## Exit

A reproducible baseline run exists before new code affects results.

---

# Phase 1 — Mechanics telemetry only

Implement:

```text
mechanics_telemetry.py
```

No controller changes.

Record current search decisions as `MechanicsEpisode`-like data.

## Goal

Learn whether current observable state is sufficient to explain failures.

## Exit

- deterministic serialization;
- subject hashes;
- resource receipts;
- no authority mutation;
- unit tests.

---

# Phase 2 — Mechanic deficiency object

Implement:

```text
mechanic_deficiency.py
```

V0 rules should be explicit.

Example rules:

```text
missing required measurement
    -> EVIDENCE

same unresolved cut survives multiple operators
    -> METHOD_OPERATOR or REPRESENTATION candidate

all children pass but glue fails
    -> COMPOSITION_INTERFACE

local flatness + uncovered scout regions
    -> SCALE / STOPPING

verifier rejects decoded representation path
    -> REPRESENTATION or VERIFICATION
```

Use set-valued ambiguity when multiple causes survive.

## Exit

On synthetic labelled cases:

- no hidden answer leakage;
- cause recall measurable;
- ambiguous cases remain ambiguous.

---

# Phase 3 — Meta-controller shell

Implement:

```text
mechanics_controller.py
```

Only three actions initially:

```text
KEEP_MECHANIC
CHANGE_OPERATOR
RUN_DISCRIMINATOR
```

Delegate `CHANGE_OPERATOR` to current search controller.

## Reason

This gives a baseline architecture before adding representation/scale/field complexity.

## Exit

End-to-end deterministic cases pass.

---

# Phase 4 — Representation search

Implement:

```text
representation_search.py
```

Start with hand-written exact transforms in synthetic domains.

Do not use an LLM generator yet.

Test whether the controller can select among representations with known downstream cost.

## Exit

Representation choice beats fixed representation on at least one registered family and loses/gets rejected correctly on another.

---

# Phase 5 — Scale policy

Implement:

```text
scale_policy.py
```

Required pieces:

```text
ScaleState
ScaleTransitionWitness
CoverageReceipt
CoverageScoutPolicy
```

Build hidden-feature worlds.

## Critical test

A residual-only refiner must fail the hidden-feature case.

The exploration/scout challenger must recover it.

This negative control is mandatory.

---

# Phase 6 — Explicit solution field

Implement:

```text
solution_field.py
```

Order:

1. exact shortest-cost / arrival field on explicit graphs;
2. conductive Laplacian field;
3. branching breakdown front;
4. conductance update from verified outcomes.

Do not add learning yet.

## Exit

All field algorithms have:

```text
known oracle comparison
cost accounting
failure semantics
deterministic replay
```

---

# Phase 7 — Field + representation interaction

Test:

```text
same problem
same solver
different representation
```

Measure whether a representation can make field routing dramatically easier.

This is the first direct test of:

> Is there a representation space where the path to solution becomes locally visible?

## Exit

Report:

```text
representation construction cost
field quality
search compression
decode validity
root success
```

---

# Phase 8 — Recursive multiscale + interfaces

Add:

```text
ScaleTransitionWitness
SolverInterfaceContract
EmergentCompositionResidual
hierarchical verification schedule
```

Integrate with `ProblemDecomposition` and `LocalSection`.

## Exit

Synthetic modular worlds distinguish:

```text
local success
interface success
root success
```

with no authority leakage.

---

# Phase 9 — Auxiliary object invention

Implement the object/request/evaluation framework.

First use enumerated candidates or deterministic generators.

Later permit LLM proposal.

## Exit

A helper object can be credited only when:

```text
frozen request
frozen candidate semantics
verified downstream effect
fresh transfer case
```

---

# Phase 10 — Learned mechanics policy

Only after earlier phases.

Candidates:

```text
mechanic diagnosis classifier
meta-action value model
representation-effect predictor
learned field/value initializer
conductance prior
```

Training data:

```text
MechanicsEpisode
```

Fresh benchmark must be sealed.

---

# Phase 11 — Runtime challenger

Create an opt-in orchestration path.

Do not make default.

Possible surface:

```python
run_mechanics_challenger(...)
```

which wraps current runtime.

---

# Phase 12 — Promotion decision

Compare:

```text
incumbent
incumbent + telemetry only
incumbent + diagnosis
incumbent + representation
incumbent + scale
incumbent + field
full challenger
```

If only one atom helps, promote that atom.

Do not require the full grand architecture to survive intact.
