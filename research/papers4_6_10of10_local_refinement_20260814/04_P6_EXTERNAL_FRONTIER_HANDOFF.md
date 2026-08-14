# Paper VI external handoff — capstone frontier + competitor assimilation

## Reframe the capstone

Paper VI should not rely on “persistent memory + research lifecycle + self-evolution” as standalone novelty. Contemporary research-agent systems already contain substantial versions of those functions.

The strongest capstone question is instead:

> Under matched or explicitly classified resources, does Orion occupy or create a defensible scientific-capability/validity/cost frontier, and can it learn a competitor mechanic from a measured loss and improve on fresh tasks without weakening protected authority/provenance invariants?

This combines Papers I–III into one falsifiable system claim.

## Freeze before any evaluated external-system output

Create:

```text
research/external_research_agents/epoch_2026_08_v1/
  PROTOCOL.md
  SYSTEM_REGISTRY.json
  VERSION_MANIFEST.json
  BENCHMARK_MANIFEST.json
  MODEL_NORMALIZATION.json
  RESOURCE_CONTRACT.json
  NORMALIZATION_ADAPTERS/
  METRIC_REGISTRY.json
  STATISTICAL_PLAN.json
  CONTAMINATION_EXCLUSIONS.json
```

Freeze exact version/date/commit/provider and configuration for every external system.

Initial systems/classes to audit from primary sources before the freeze include:

- AutoSci;
- EvoScientist;
- ARIS;
- AI Scientist v2 where reproducible;
- Agent Laboratory;
- a strong deep-research/retrieval agent;
- any later system found during the bounded 2026 freshness scan **before** evaluated outputs.

Do not add a system after seeing that Orion wins/loses in the epoch.

## Public benchmark tiers

Freeze at least one benchmark from each scientifically distinct class when feasible:

### Literature / research retrieval

Use a current open scientific/deep-research benchmark with source/citation scoring.

### Scientific execution

Use a benchmark with executable/program-level scoring and resource accounting, e.g. the current ScienceAgentBench-class task family.

### Agentic scientific reasoning

Use an agent-agnostic/stepwise-verified arena such as SciAgentArena-class tasks where implementation access permits.

### Broad scientific-agent lifecycle

Use AstaBench-class tasks/subsets when the frozen agent interface is compatible.

Public benchmark protocol/evaluator must remain unchanged unless an adapter changes syntax only. Store every adapter hash.

## Three comparison tracks — never conflate them

### Track 1: model-normalized architecture comparison

Where feasible:

```text
same model/revision
same sampling
same evidence cutoff
same tools
same token/model/tool/wall envelope
```

This is the only track that can approach a causal harness/architecture interpretation.

### Track 2: native best-practice systems

Run systems in their documented/recommended configuration under a declared resource envelope.

This answers practical whole-system performance. Model/tool differences are part of the system and must not be attributed solely to architecture.

### Track 3: function-matched component comparisons

Compare specific surfaces:

```text
retrieval
planning/search
scientific execution
claim/evidence binding
persistent memory
negative-history reuse
method learning
verification/assurance
self-evolution
```

Classify external implementation fidelity:

```text
EXACT_REPRODUCTION
BLACK_BOX_PUBLIC_SYSTEM
FUNCTION_MATCHED_APPROXIMATION
CONCEPTUAL_ONLY
CANNOT_COMPARE_FAIRLY
```

## Required Orion arms

Where task-compatible, freeze:

```text
MODEL_ONLY
STRONG_STRUCTURED_PROMPT
SIMPLE_RESEARCH_LOOP
RETRIEVAL_TOOLS_BASELINE
STRONG_EXTERNAL_AGENT + SAME MODEL/TOOLS  # only when feasible
RAKL_RESET
RAKL_SHAM_MEMORY
RAKL_PERSISTENT / supported learned state
ORION_CURRENT
ORION_CHALLENGER  # only after epoch-1 weakness freeze
```

For integrated solver domains also include the strongest specialized solver. A general agent does not get credit for beating a deliberately weak specialist.

## Metric vector

Use the existing RAKL competence tensor as the starting measurement schema, not one score:

```text
V validity / authority discipline
E evidence use and revision
D discovery
X explanation/mechanism
P experimental planning/discrimination
G gap/metacognitive diagnosis
L learning/transfer/evolution
R robustness/reproducibility
C total cost/efficiency
```

Before promotion, every paper claim must name its observable and comparison.

Hard protected coordinates include at minimum:

```text
authority leakage = 0 on planted blockers
evaluation/assurance contamination = 0
provenance chronology violation = 0
fabricated source identity = 0
hidden evaluator rewrite = 0
```

Soft task gains cannot compensate for a hard failure.

## Statistical protocol

Independent unit = task/case, not model call.

Freeze:

```text
primary QoI vector
MDE / noninferiority / harm boundaries
sample/family allocation
paired analysis where valid
cluster handling
multiplicity
stopping rule
missing/invalid semantics
resource ceiling
```

Report symmetric paired outcomes:

```text
BOTH_SUCCESS
ORION_ONLY_SUCCESS
BASELINE_ONLY_SUCCESS
BOTH_FAIL
```

`BASELINE_ONLY_SUCCESS` is RAKL interference evidence, not noise to discard.

## Epoch 1 — benchmark the incumbent without repairing it

Run the frozen systems and produce:

```text
SYSTEM_CAPABILITY_MATRIX_V1
PARETO_FRONTIER_V1
COST_MATRIX_V1
PAIRWISE_INFERENCE_V1
WEAKNESS_MAP_V1
```

For every meaningful Orion loss, localize the earliest plausible layer:

```text
MODEL_INTERFACE
SOURCE_RETRIEVAL
DECOMPOSITION
REPRESENTATION
PLANNING
CODE_EXECUTION
EVIDENCE_BINDING
MEMORY_RETRIEVAL
LESSON_INDUCTION
FAILURE_RECOVERY
AUTHORITY_GOVERNANCE
SYNTHESIS
RESOURCE_DOMINATION
CANNOT_LOCALIZE
```

No Orion repair may use the sealed epoch-2 tasks.

## Competitor-mechanic assimilation — the Paper-VI flagship experiment

Choose the highest-value measured weakness by a rule frozen before reading detailed candidate repairs.

Then:

```text
competitor advantage
-> inspect exact source mechanism
-> separate generic prior art from source-specific detail
-> produce RAKL DifferenceWitness
-> faithful transfer challenger
-> adapted RAKL-native challenger if source assumptions fail
-> development benchmark
-> freeze survivor
-> fresh assurance epoch 2
```

Required comparison in epoch 2:

```text
ORION_INCUMBENT
ORION_CHALLENGER
WINNING_EXTERNAL_PARENT
BASE_MODEL / SIMPLE_PARENT
```

Promotion only if fresh results improve the registered weakness without unacceptable regressions.

Strong terminal:

```text
EXTERNAL_FRONTIER_ASSIMILATION_SUPPORTED
```

meaning a competitor mechanic was correctly identified, transferred/adapted, and produced a fresh scoped frontier improvement.

Valid negative terminals include:

```text
COMPETITOR_ADVANTAGE_SUPPORTED
SIMPLER_PARENT_SUFFICIENT
TRANSFER_DID_NOT_GENERALIZE
RESOURCE_SCALING_NOT_METHOD_EVOLUTION
RAKL_CHALLENGER_OVERFIT
CAPABILITY_SAFETY_TRADEOFF_UNRESOLVED
CANNOT_COMPARE_FAIRLY
```

These can still make a rigorous Paper VI if the manuscript is narrowed to the supported result.

## Component-to-capstone rule

Do not allow full-system performance to retroactively validate an individual component.

Before `capstone_integrated_solver_v1`, each constituent component must be either:

```text
formal/production conformance closed at its authority boundary
PROMOTE_TO_MECHANIC
PROMOTE_CONDITIONALLY with explicit supported regime and fallback
retired/superseded with immutable negative history
```

The capstone paper may report a component as present but not as empirically useful when its own residual is unearned.

## Paper-VI reader-facing changes after execution

The results section should be organized around:

1. external comparison taxonomy;
2. Pareto frontier, not universal ranking;
3. exact process surface where Orion is better/worse;
4. matched ablations explaining which component matters;
5. competitor assimilation case;
6. fresh epoch-2 result;
7. hard safety + cost + reproducibility;
8. explicit domains/tasks where no conclusion is licensed.

Do not duplicate Papers I–V result tables; cite their frozen receipts and use Paper VI for integration-level causal evidence.