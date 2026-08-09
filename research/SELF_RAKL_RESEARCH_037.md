# SELF-RAKL Research Round 037 — Measurement and Instrument Cognition

Date: 2026-08-09  
Parent fiber: `META_N111_MEASUREMENT_INSTRUMENT_COGNITION`  
Status: candidate support improvement; real scientific utility still open

## Live repository start

```text
main = 1803221af7dd9be28652bcbd26aaf62904c0500c
open issues = 0
open PRs = 1 (#8, constructive invention engine on paper/round035-polymarket-crypto-case)
latest completed self-RAKL = Round 036 quant-publication binding
latest full framework inventory = FRAMEWORK_FIBER_INVENTORY_035B + postvalidation delta + Round 036 backlog delta
```

Round 036 remained `ACTIVE_NON_FLAT`; its new publication fibers `META_N114`-`META_N120` are prospective and do not close the framework. The latest inventory explicitly named measurement/instrument-aware `SAME_OBSERVABLE` semantics as a high-priority dependency of `equivalence_similarity` and `generator_transport`.

## Frozen question

Can RAKL distinguish

```text
same/equivalent reported numbers
```

from

```text
same observable under a declared measurement context
```

and distinguish both from

```text
observational equivalence under a frozen probe family
```

without escalating either relation to mechanism or target authority?

The 18-world benchmark was frozen in `SELF_RAKL_RESEARCH_037_MEASUREMENT_FROZEN_BENCHMARK.json` at commit `edbbebe7132319cf696f8415aec9f3d47c8cb414` before implementation.

## Six-role research panel

The roles were separated by question and failure mode; same-orchestration agreement is recorded only as internal triangulation, not independent review.

### 1. Cognitive-science / analogy role

Task: identify the analogy failure caused by treating perceptual/report similarity as object identity.

Finding: the observable channel is part of the analogy context. Equal outputs can be a surface match while the measured property, object, or observation process differs. The role therefore required `SAME_OBSERVABLE` to be a typed relation rather than a score.

Delegated cross-check: ontology/KR role and adversarial role.

### 2. Knowledge-representation / ontology role

Task: determine the minimum entities needed to represent an observation without conflating them.

Finding: W3C SOSA/SSN separates observation, observable property, feature of interest, sensor/system, procedure and result. RAKL should preserve at least the analogous coordinates instead of storing only `(quantity-name, value)`.

Delegated cross-check: scientific-IR role and metrology/applied-math role.

### 3. Scientific-information-retrieval role

Task: ask what metadata must survive retrieval so recognition can later be audited.

Finding: retrieval of a numerical match is not recognition of the same observable. Source projections should retain measurand/property, feature-of-interest, procedure/operator, unit, calibration/traceability, uncertainty and time/regime metadata when available. Missing metadata is a `CANNOT_CHECK` reason rather than permission to infer sameness.

Delegated cross-check: ontology/KR role and adversarial role.

### 4. Applied mathematics / dynamical systems / metrology role

Task: formalize observation-relative equivalence and its quantitative failure conditions.

Finding A: VIM distinguishes measurand, measurement model, indication/result, calibration and traceability. NIST further emphasizes that traceability is a property of the measurement result and that calibration alone does not guarantee traceability or fitness for purpose.

Finding B: recent inverse-problem work shows that identifiability and uncertainty are bounded by sensor layout/experiment design. Therefore observational equivalence must be indexed by an observation/probe family and resolution, not treated as a property of two mechanisms in isolation.

Finding C — corrective finding: the first implementation used `sqrt(u_A^2 + u_B^2)` as a generic comparison uncertainty. That silently assumes a dependence structure. The rule was rejected and an addendum benchmark was frozen before correction. The final support contract accepts only a separately justified uncertainty-combination rule/result.

Delegated cross-check: adversarial reviewer and ontology/KR role.

### 5. Computational-creativity / search role

Task: determine whether measurement semantics can improve JUMP rather than only block it.

Finding: JUMP can search distant systems by observation geometry, measurement model, sensor failure mode, calibration structure or observability residual. This can expose siblings missed by category search. However this is discovery authority only; a shared sensor/observable schema does not imply a shared generator.

Delegated cross-check: cognitive-science role and adversarial role.

### 6. Adversarial scientific-method reviewer

Task: construct false friends and authority leaks.

Required hostile worlds included: equal numbers/different measurands; same property/different feature; incompatible operators; broken/unknown traceability; post-hoc transforms; insufficient uncertainty/resolution; disjoint regimes; hidden discriminator exposure; same observable/different mechanism; and target refutation after a valid measurement relation.

The reviewer also found two implementation-level hazards:

1. globally changing generic `SimilarityWitness` validity for observational relations broke the previously frozen multi-hop bridge evaluator, so the change was rejected. Generic witness validity remains structural; measurement certification is a separate typed handoff.
2. root-sum-square uncertainty composition was unjustified without a dependence contract and was removed.

Both failures remain in Git history and are not rewritten away.

## Role disagreement ledger

### Generic witness versus mandatory measurement certificate

The KR/metrology roles initially preferred making the generic similarity validator fail closed for `SAME_OBSERVABLE` and `OBSERVATIONALLY_EQUIVALENT`. The bridge-composition protected evaluator showed that existing proposal-only path code uses these relation labels as structural hop types. Making the generic validator measurement-aware caused a blocking regression (`test_mixed_relations_never_mint_endpoint_relation`).

Resolution: preserve generic structural witness semantics and add a **separate measurement certificate**. Any future authority-bearing or real measurement-transfer path must require the certificate explicitly; generic bridge navigation remains proposal-only. Integration of that certificate into real generator/atlas/bridge benchmarks remains an open empirical/interface boundary.

### Uncertainty combination

The initial implementation assumed quadrature. Applied-math and adversarial roles rejected the assumption. No role defended a generic composition law after the dependence issue was exposed.

Resolution: the support layer now consumes a predeclared validated uncertainty-combination rule and its result; it does not invent one.

## External source projections

This round used a materially different search route: metrology, sensor ontologies, dynamic measurement software and inverse-problem identifiability.

1. JCGM/BIPM VIM 3, measurand: https://jcgm.bipm.org/vim/en/2.3.html
2. JCGM/BIPM VIM 3, measurement model: https://jcgm.bipm.org/vim/en/2.48.html
3. JCGM/BIPM VIM 3, calibration: https://jcgm.bipm.org/vim/en/2.39.html
4. JCGM/BIPM VIM 3, metrological traceability: https://jcgm.bipm.org/vim/en/2.41.html
5. NIST, Metrological Traceability FAQ and Policy: https://www.nist.gov/metrology/metrological-traceability
6. W3C, Semantic Sensor Network Ontology — 2023 Edition: https://www.w3.org/TR/vocab-ssn-2023/
7. Bakeer, Herbers & Marx (2025), *Sensor Informativeness, Identifiability, and Uncertainty in Bayesian Inverse Problems for Structural Health Monitoring*: https://arxiv.org/abs/2511.16628
8. PTB, measurement-uncertainty software including PyDynamic/GUM2DFT: https://www.ptb.de/cms/en/ptb/fachabteilungen/abt8/fb-84/ag-842/software.html

## Semantic novelty deduplication

Not new to RAKL/the literature:

- measurands;
- measurement models;
- calibration;
- metrological traceability;
- uncertainty budgets;
- sensor/observation ontologies;
- observability/identifiability;
- uncertainty propagation software.

Retained RAKL method objects:

1. `MeasurementSpecification`: a typed measurement context attached to an observation/similarity endpoint.
2. `MeasurementMapping`: a predeclared witness for semantic/unit/model/operator/traceability/uncertainty comparability.
3. measurement-aware `SAME_OBSERVABLE` support that explicitly permits different instruments while refusing mechanism inference.
4. measurement-aware `OBSERVATIONALLY_EQUIVALENT` indexed by frozen probes, tolerance, uncertainty, resolution, regime and common comparison coordinate.
5. explicit separation `generic structural similarity witness != measurement certificate != mechanism identity != target authority`.
6. negative result: generic root-sum-square uncertainty composition is refuted without a declared dependence/composition contract.

This is framework integration and failure suppression; no broad novelty claim is made for measurement science itself.

## Capability shaping

| Atomic operation | Model strength amplified | Weakness constrained | Smallest compensator | Verification oracle | Resource delta | Typed handoff |
|---|---|---|---|---|---|---|
| recognize observable relation | semantic mapping | surface-number conflation | `MeasurementSpecification` + `MeasurementMapping` | M01-M10 hostile worlds | measurement metadata | `MeasurementRelationReport` |
| compare observational predictions | relational/probe reasoning | vague "looks equivalent" judgment | frozen probes + tolerance + resolution | M11-M18 | probe evaluations | proposal-only equivalence/distinguishability |
| uncertainty handling | arithmetic/model reasoning | silent independence/covariance assumption | external validated composition rule/result | MU01-MU04 | uncertainty-model evidence | combined uncertainty with rule provenance |
| cross-unit probes | coordinate translation | comparing untransformed numbers | common-coordinate certificate | MU05 | transform evidence | `CANNOT_CHECK` until coordinate is certified |
| scientific JUMP | broad associative retrieval | taxonomy-only transfer | measurement-schema search keys | future real generator benchmark | metadata/search cost | discovery candidates only |

Attribution remains separated: the implementation primarily targets **failure suppression** and typed handoff quality. Real model-utilization gain, external-resource gain and whole-system scientific gain remain `CANNOT_CHECK` until matched real benchmarks run.

## GLUE / LIFT / JUMP / PROJECT consequence

A measurement relation may participate in GLUE only at the declared observational layer. LIFT may erase instrument identity while preserving measurand/operator/model coordinates, but the erasure must be recorded. JUMP may search siblings sharing observation geometry. PROJECT must reacquire target measurement evidence and a target-domain test.

Thus:

```text
same result
  != same observable
  != observational equivalence under a probe family
  != same mechanism
  != same generator
  != target truth
```

## Implementation chronology and negative history

- `edbbebe...`: 18-world benchmark frozen before implementation.
- first implementation introduced measurement context support.
- candidate `918a79f...` produced 446 passes / 1 failure because the attempted generic fail-closed rule broke a protected bridge-composition behavior. That candidate is not promotable as-is.
- the generic validator change was reverted; measurement certification became a separate typed layer.
- adversarial review then found unjustified quadrature uncertainty composition.
- `3f258f2...`: five-world uncertainty-composition addendum frozen before correction.
- corrected implementation requires a named validated uncertainty-combination rule/result and a common probe coordinate when units differ.

The exact final candidate CI and promotion receipt are recorded separately; no pending or stale run is called passing here.

## Fiber disposition

`META_N111_MEASUREMENT_INSTRUMENT_COGNITION`:

```text
VALIDATED_IMPROVEMENT_SUPPORT_LAYER_REAL_UTILITY_AND_EXECUTED_METROLOGY_OPEN
```

subject to exact-head CI/promotion validation.

New child residual allocated in the first verified-free slot after Round 036:

`META_N121_MEASUREMENT_TRANSFORM_AND_UQ_EXECUTION`

Purpose: execute/verify real calibration chains, uncertainty/covariance models and coordinate transforms rather than trusting externally supplied booleans/results; compare that richer execution against the simpler support-only contract on real scientific packets.

## Saturation

This round is non-flat because it retains new measurement coordinates, a validated false-friend class and a refuted uncertainty-composition assumption. No same-context or independent flat-round credit is earned.

Framework saturation remains prohibited until the broader inventory blockers and required flat/independent rounds are closed.
