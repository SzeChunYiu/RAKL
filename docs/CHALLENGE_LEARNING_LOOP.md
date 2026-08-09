# Challenge Learning Loop for Self-RAKL

Status: research-only architecture audit; no Constitution change; no authority or promotion effect.
Date: 2026-08-09

## Purpose

RAKL should be judged on two distinct capabilities:

1. whether it can finish a hard real scientific project;
2. whether work on that project causes RAKL to detect weaknesses in its own research method and become measurably better on later tasks.

The current metacognitive layer diagnoses calibration, explanation, ontology and method-basis gaps. A senior researcher also needs **metacognitive control**: selecting what learning action to take after a challenge exposes a weakness.

The engineering target is not simulated emotion or anthropomorphic self-awareness. It is a closed learning-control loop inspired by self-regulated learning, error monitoring, productive failure, curiosity, adaptive help-seeking and cognitive flexibility.

## Functional cycle

For project state `s_t`, target `tau`, current method basis `Omega_t`, and competence state `C_t`, define a challenge episode:

\[
\chi_t=(g_t,a_t,y_t,\hat y_t,e_t,z_t,u_t),
\]

where:

- `g_t` is the challenge goal/standard;
- `a_t` is the attempted research action;
- `y_t` is externally observed outcome/evidence;
- `hat y_t` is the expected outcome or predicted adequacy;
- `e_t` is a typed error/residual;
- `z_t` is causal attribution over why the attempt failed;
- `u_t` is the learning-control action chosen next.

RAKL should cycle through:

```text
FORETHOUGHT
  choose challenge / standard / expected failure signatures
      -> PERFORMANCE
  execute while monitoring cost, confidence and evidence
      -> OUTCOME COMPARISON
  compare observed result with expected result
      -> ERROR ATTRIBUTION
  data? method? representation? missing operator? resource? stochastic noise?
      -> LEARNING CONTROL
  retry / practice / seek help / switch representation / explore / invent / stop
      -> CONSOLIDATION
  extract reusable procedure or negative rule
      -> TRANSFER
  test on new examples / domains / evidence lineages
      -> UPDATED COMPETENCE MODEL
      -> next challenge
```

A verbal reflection without an evidence-linked control change does not count as learning.

## Learning-progress state

Absolute performance is insufficient for selecting what to learn next. Maintain, for capability/fiber `f`, a competence estimate and a learning-progress estimate:

\[
C_t(f)=Q_t(f),
\qquad
LP_t(f)=Q_t(f)-Q_{t-k}(f).
\]

When probabilities or interval estimates are unavailable, `C` and `LP` may be ordinal/set-valued.

This allows the controller to distinguish:

- mastered/easy fibers: high competence, low learning progress;
- learnable frontier: intermediate competence, positive learning progress;
- stuck/unlearnable under current basis: low competence, persistently flat learning progress;
- regressions: negative learning progress.

The research agenda and the self-improvement curriculum are different portfolios. Scientific importance may justify staying on a hard target even when self-learning progress is flat, but flat learning progress should trigger a method-basis or help-seeking audit rather than infinite repetition.

## Productive failure

Failure can be deliberately informative. A challenge may be attempted before importing a known solution when the expected value of revealing the system's missing representation/operator exceeds the cost.

A productive-failure episode receives credit only if it produces at least one of:

```text
new discriminating residual
correct error attribution
new transferable operator candidate
better calibration
better future learning on a related task
```

Repeated failure with no new diagnostic information is not productive and should trigger strategy switching.

## Adaptive help-seeking

Help-seeking is a first-class learning action, not an embarrassment or a fallback hidden from the record.

RAKL should request external expertise/review when:

- an epistemic cut is identified but no incumbent operator resolves it;
- repeated residuals lie outside the current ontology;
- learning progress is flat across multiple internal strategies;
- independent assurance is required;
- the expected cost of continued same-context search exceeds the expected value of a conceptually independent perspective.

Help must preserve provenance and independence metadata. Advice enters as a proposal/evidence source, not as automatic authority.

## Cognitive flexibility / metacontrol

The system needs an explicit persistence-versus-switch policy.

For strategy `m` on fiber `f`, track:

\[
Progress(m,f),\quad Cost(m,f),\quad ResidualNovelty(m,f),\quad FailureRepeat(m,f).
\]

Persist when progress or new discriminating information remains positive. Switch when repeated attempts are semantically equivalent, learning progress is flat, or a different representation/operator has higher expected discrimination per cost.

Strategy switching must not erase the unsuccessful route.

## Error attribution

A senior scientist distinguishes being wrong from knowing *why* the research attempt failed. RAKL should type failure causes at least as:

```text
EVIDENCE_MISSING
MEASUREMENT_OR_CLOCK_ERROR
REPRESENTATION_MISMATCH
ASSUMPTION_FAILURE
INFERENCE_OR_STATISTICAL_ERROR
IMPLEMENTATION_ERROR
RESOURCE_LIMIT
MODEL_CLASS_MISSPECIFICATION
ONTOLOGY_GAP
METHOD_BASIS_GAP
STOCHASTIC_OR_UNIDENTIFIED
EXTERNAL_ENVIRONMENT_SHIFT
```

Attribution is a hypothesis and requires evidence. The system must support multiple surviving causes when not identified.

## Retrieval/rehearsal and skill retention

An external archive does not automatically imply retained capability. Learned operators should periodically be re-executed on varied examples, especially after long inactivity, dependency changes or domain transfer.

A method remains `CURRENTLY_VALIDATED` only within its versioned environment and transfer scope. Failed reactivation opens a skill-drift residual.

## Reflection anti-rumination rule

Reflection should terminate or switch mode when successive reflection rounds produce no new residual, no new causal attribution, no changed action policy and no measurable calibration improvement.

The system should prefer process-focused questions (`what operation should change?`, `what evidence distinguishes the causes?`) over repeated abstract restatements of `why did I fail?`.

## Project-driven self-improvement

During a real project such as `polymarket_crypto`, every project failure can yield two outputs:

\[
(e^{science}, e^{method}).
\]

`e^{science}` updates the domain Knowledge Atlas. `e^{method}` updates only the Self-RAKL learning queue.

A method challenger extracted from the project becomes a validated RAKL capability only after:

```text
project symptom
-> causal weakness diagnosis
-> frozen method discriminator
-> repair / imported mechanism
-> development improvement
-> fresh task transfer
-> fresh assurance
-> promotion
```

Thus the real project is simultaneously a scientific application and a challenge curriculum for the framework.

## Two-axis framework scorecard

Do not collapse the two axes into one scalar.

### Axis A — Project Completion Capability

Measure whether RAKL can move a real project from unresolved state to a scientifically terminal outcome with:

- source/evidence authority;
- complete atomic decomposition;
- valid descriptive/explanatory model;
- predictive model where the target requires prediction;
- uncertainty/identification honesty;
- efficient experiment selection;
- bounded context/runtime;
- reproducible receipts;
- no hidden blocking residual.

### Axis B — Learning Capability

Measure:

- hidden weakness precision/recall;
- correct failure-cause attribution;
- time/actions to diagnose method weakness;
- false invented-weakness rate;
- strategy-switch quality;
- adaptive help-seeking quality;
- learning-progress efficiency;
- fresh-transfer gain after repair;
- cross-domain/cross-model transfer;
- meta-overfit rate;
- negative-history preservation;
- assurance-reserve consumption.

Strong RAKL requires both axes.

## Current architecture assessment

Already represented substantially:

```text
error monitoring / high-confidence error trigger
explanation reconstruction
consider-the-opposite / countermodel request
outside-view independence
ontology-gap and method-basis-gap diagnosis
negative history
evidence-governed self-evolution
experience-to-procedural-skill theory
research agenda / scientific taste theory
```

Still missing or only prospective as an integrated executable cycle:

```text
learning-progress-based self-challenge curriculum
explicit error-attribution engine
metacognitive control / strategy selection after diagnosis
productive-failure policy
adaptive help-seeking policy
persistence-versus-flexibility metacontrol
skill reactivation / drift testing
reflection anti-rumination stopping
project-to-method dual-output accounting
```

These should be treated as one coherent learning-control layer with separately benchmarked submechanisms, rather than nine new decorative psychology labels.
