# RAKL v3 Public API

RAKL v3 exposes a stable facade at:

```python
from rakl.v3 import ...
```

Legacy top-level `rakl` exports are intentionally unchanged so existing callers do not need to migrate immediately.

## Core persistent state

```python
from rakl.v3 import RAKLV3State

state = RAKLV3State()
```

`RAKLV3State` combines the persistent external learning views:

```text
ExperienceLedger
ResearchToolInventory
FailureExperienceLattice
SaturationVectorState
EvolutionArchive (optional)
```

## One learning turn

The end-to-end driver adapter is `run_learning_turn()`.

```python
from rakl.v3 import (
    DriverResult,
    DriverTask,
    EpisodeOutcome,
    ProblemAtom,
    RAKLV3State,
    run_learning_turn,
)

atom = ProblemAtom(
    atom_id="A1",
    goal="solve the local obligation",
    context_hash="ctx-1",
    structural_coordinates=("graph", "bridge"),
    desired_effects=("connect",),
)

task = DriverTask(
    task_id="task-1",
    atom=atom,
    problem_signature=("graph", "bridge"),
    timestamp="2026-08-11T08:45:00+00:00",
)

def driver(request):
    # request.fibre contains the target-conditioned knowledge/tools/experience.
    return DriverResult(
        operator_ids=("bridge-op",),
        action_trace=("apply bridge", "verify interface"),
        observation_ids=("obs-1",),
        verification_ids=("verify-1",),
        outcome=EpisodeOutcome.SUCCESS,
        residual_signature=(),
        evidence_pointers=("artifact:run-1",),
        artifact_hash="sha256:run-1",
    )

report = run_learning_turn(
    RAKLV3State(),
    task,
    driver,
    episode_id="episode-1",
)

state = report.state
```

The lifecycle is fixed:

```text
persistent state
-> compile problem fibre
-> call replaceable LLM/agent driver
-> observe result
-> freeze immutable TaskEpisode
-> optionally project non-success into failure memory
-> return evolved external state
```

The driver cannot write a lesson or scientific authority directly.

## Slow consolidation

Use `consolidate_lesson()` after enough outcome-linked evidence exists.

```text
candidate lesson
-> replay / diagnostic episodes
-> registered verification
-> fresh transfer or proof
-> versioned promoted lesson
-> optional ResearchTool projection
```

`CANDIDATE_ONLY`, `CANNOT_CHECK`, and `CONTRADICTED` lessons are not exposed as promoted reusable tools.

## Problem fibres and gluing

Use:

```python
from rakl.v3 import compile_state_fibre, glue_local_sections
```

A fibre may contain knowledge, tools, episodes, failures, motifs, expertise chunks, and warnings. Co-retrieval does not imply compatibility.

A global solution report grants authority only when local sections are mutually compatible, individually verified, and cover the complete registered atom decomposition.

## Experience-conditioned routing

Use:

```python
from rakl.v3 import (
    rank_operators_with_experience,
    rank_paths_with_experience,
    induce_strategy_motifs,
)
```

Historical outcomes affect search priority only. They do not alter verification or promotion rules.

## Saturation and invention readiness

Use:

```python
from rakl.v3 import assess_saturation_vector, assess_invention_readiness
```

Saturation is measured independently across knowledge, operator, experience-pattern, obstruction, relation, path, and meta-method axes. A missing-operator/representation escalation requires bounded flatness plus a stable residual and explicit gap evidence.

## Branching Self-RAKL

Use:

```python
from rakl.v3 import (
    initialize_evolution_archive,
    register_challenger,
    record_evolution_trial,
    promote_incumbent,
)
```

An assurance-passing challenger becomes `ASSURED`; it does not become incumbent automatically. Incumbent replacement requires explicit governance approval and preserves the previous incumbent as an assured rollback/alternative branch.

## Authority boundary

The v3 API preserves these invariants:

```text
ACCESS != COHERENCE != AUTHORITY
Episode != diagnosis != obstruction
Reflection != verification
Co-retrieval != compatibility
Local success != global solution
Experience-conditioned routing != epistemic authority
Derived memory never replaces immutable evidence roots
Being stuck != missing operator
Self-evolution evidence != self-promotion
```
