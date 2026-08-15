# RAKL Research Machine Workflow v2

**Status:** Self-RAKL challenger specification.  
**Target:** upgrade ordinary problem solving from an LLM-centered workflow into a recursively instrumented research machine.  
**Authority:** workflow/method proposal only until the normal RAKL method-evolution gate promotes it.

## 1. Design claim

RAKL should be modeled as:

```text
scientific state
+ knowledge acquisition
+ representations
+ methods/operators
+ computation/simulation/proof
+ experiment design
+ verification
+ memory
+ metrology
+ self-model
+ governed self-evolution
```

The LLM is a proposer/planner/extractor among these components. It is not the research machine and cannot self-certify scientific or framework authority.

## 2. Recursive control loop

```text
PROBLEM
  -> freeze decision/audit/evidence boundary + observational epoch
  -> candidate question audit (recursive framework audit, pre-commitment)
  -> activate scoped question/QoI
  -> acquire + normalize knowledge
  -> establish bounded KNOWLEDGE saturation
  -> reconstruct Apple object portrait
  -> choose object-level operation
  -> predict expected effect
  -> execute
  -> observe result + cost + residual
  -> update scientific state
  -> update process/self-model
  -> choose next action
       -> continue object work
       -> targeted knowledge refresh
       -> representation/operator/experiment/verifier repair
       -> Self-RAKL when framework evidence warrants
  -> repeat
```

Every consequential transition must be externally reconstructable without requiring hidden chain-of-thought.

## 3. Measurement constitution

Do not create one permanent scalar `RAKL_SCORE`.

Every process surface has a vector containing at least:

```text
quality / task contribution
information or semantic gain
residual transformation
uncertainty / calibration
resource cost
downstream decision effect
failure mode
scope / provenance
```

Metrics are authority-separated:

```text
DESCRIPTIVE
CONTROL_INPUT
EVOLUTION_EVIDENCE
HARD_PROTECTED
```

Controller convenience never upgrades a descriptive/control metric into evolution authority.

## 4. Knowledge-acquisition model

For knowledge round `r`:

```text
K_r = (
  route,
  queries,
  processed sources,
  relevant sources,
  retained semantic objects,
  facet gain,
  mechanism gain,
  context gain,
  contradiction gain,
  falsifier gain,
  blind-spot gain,
  cost,
  evidence pointers
)
```

Important ratios are descriptive/controller candidates only:

```text
semantic_yield_per_source
semantic_yield_per_query
cost_per_retained_semantic_object
corroboration_only_rate
duplicate_rate
contradiction_yield
blind_spot_yield
```

Never infer recall without a defensible reference universe.

## 5. Bounded saturation

A knowledge fiber can move to object work when the current registered search universe is flat:

```text
no recent retained semantic novelty
+ multiple independent route families flat
+ required route-family coverage complete or explicitly blocked
+ no native knowledge residual
+ freshness acceptable
```

This is not global completeness.

A native residual, contradiction, ontology change, representation change, source-coverage defect or freshness event can reopen the knowledge fiber.

## 6. Apple process indicators

### GLUE
- facet coverage gain;
- projection diversity;
- context-coordinate coverage;
- compatibility/context-resolution rate;
- mechanism-edge gain;
- false merge rate;
- unresolved contradiction/interface rate.

### ABSTRACT
- coordinates erased;
- target-relevant erasure violations;
- recoverability of source projections;
- abstraction compression versus information loss.

### JUMP
- witnessed structural mappings;
- novel hypothesis yield;
- disanalogy coverage;
- target transfer success;
- hostile-near-miss/false-transfer rate;
- cost per useful transferred hypothesis.

## 7. Other process indicators

### Search / retrieval
- relevant-hit rate;
- semantic novelty/query;
- missed-key-source diagnostics;
- source identity/authenticity failures;
- lineage diversity;
- cost/new semantic object.

### Decomposition
- obstruction localization;
- useful child-fiber rate;
- dependency/interface completeness;
- unnecessary decomposition.

### Routing
- selected route calibration;
- route regret when estimable;
- saturated-route retry rate;
- route-switch latency;
- applicability-block rate.

### Experiment/discriminator selection
- expected/observed information gain;
- survivor reduction;
- identified-set shrinkage;
- decision effect;
- cost to decisive falsifier.

### Verification
- clean PASS;
- planted FAIL;
- structural CANNOT_CHECK;
- false-positive/false-negative;
- exact-subject/chronology binding.

### Synthesis
- source-claim recoverability;
- contradiction preservation;
- residual preservation;
- false global glue;
- scope overclaim/retraction.

### Memory
- relevant retrieval recall under a bound universe;
- missed-relevant-memory;
- stale-memory error;
- successful/failed reuse;
- context budget/cost.

### Self-model
- Brier score / calibration error;
- predicted versus observed process gain;
- diagnosis hit rate;
- intervention success;
- uncertainty and abstention quality.

### Self-evolution
- development gain;
- fresh transfer gain;
- hard regressions;
- meta-overfit;
- mutation/operator success by context;
- evolution resource cost;
- transferable capability gain per evolution cost.

## 8. Model/tool tiering including quantized models

The research machine should select models and tools by measured role fitness rather than prestige or size.

Low-cost/quantized/local models may be useful for:

```text
source triage
query/vocabulary expansion
candidate extraction
duplicate classification
routine normalization
shadow control
large ablation sweeps
```

Consequential extraction remains source-bound and verifiable.

Record at minimum:

```text
model identity/revision
quantization/precision
inference engine
prompt/harness identity
tool policy
resource ceiling
```

Model/tool changes create a new observational epoch unless matched controls restore comparability.

## 9. Recursive Self-RAKL

Treat each RAKL process surface as a research object.

```text
measure surface
-> detect persistent bottleneck
-> read best practices across multiple domains
-> Apple GLUE compatible mechanisms
-> ABSTRACT common principle
-> JUMP to alien domains
-> construct challenger
-> freeze benchmark/evaluator
-> matched development
-> fresh assurance
-> reject / retain / governed promotion
-> measure again
```

A bottleneck is supported by process evidence, not by one anecdotal failure.

## 10. Implementation map

- `skills/rakl-core/workflows/problem-solving.md`: operational lifecycle.
- `skills/rakl-core/workflows/literature-absorption.md`: quantified reading/saturation.
- `src/rakl/research_machine_workflow.py`: bounded knowledge-control adapter.
- `src/rakl/saturation_vector.py`: existing semantic flatness authority.
- `src/rakl/v3_metrology.py`: existing process telemetry/metrology.
- `src/rakl/evolution_trace.py`: metric/epoch/self-model lineage.
- `src/rakl/meta_controller.py`: quantified meta-control/shadow routing.
- `src/rakl/self_hosting_runtime.py`: governed framework escalation.
- `docs/RAKL_METROLOGY.md`: canonical measurement contract.

Do not duplicate these authority systems.

## 11. Acceptance requirements

The workflow challenger must prove at least:

1. semantic novelty prevents premature literature stopping;
2. paper count cannot create saturation;
3. multiple independent route families are required;
4. residual/freshness events reopen only relevant knowledge search;
5. local object iterations reuse persistent knowledge rather than forcing complete rereads;
6. every consequential process has observable state/cost/residual identity;
7. hard-protected metrics cannot be averaged into a soft score;
8. Self-RAKL opens only on supported framework/process evidence;
9. real-repo regression tests remain green;
10. future matched problem-solving benchmarks can compare outcome and resource effects.

## 12. Claim boundary

Passing workflow/controller tests shows that the control semantics are executable and fail closed.

It does **not** establish that RAKL solves more scientific problems. That requires matched native problem-solving evidence with fresh tasks and preserved hard invariants.
