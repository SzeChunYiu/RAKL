# Measurement-aware similarity

RAKL treats a reported value as the output of a measurement context, not as a self-identifying observable.

The support layer introduced for `META_N111_MEASUREMENT_INSTRUMENT_COGNITION` adds a measurement certificate for `SAME_OBSERVABLE` and `OBSERVATIONALLY_EQUIVALENT`.  The existing generic `SimilarityWitness` remains a structural record used by bridge/navigation code; it is **not** by itself a measurement certificate.

## Measurement object

A comparison is indexed by the declared question/QoI and by two `MeasurementSpecification` objects containing at least:

- measurand;
- feature of interest;
- unit/coordinate;
- measurement model;
- observation operator;
- procedure and instrument identity;
- calibration chain and traceability reference where required;
- measurement uncertainty and resolution;
- validity regime and phenomenon scope.

This follows the metrological distinction between a quantity intended to be measured, the model used to infer it, instrument indications, calibration, a measurement result and its uncertainty.  It also mirrors SOSA/SSN's separation of observation, observable property, feature of interest, sensor/procedure and result.

## `SAME_OBSERVABLE`

`SAME_OBSERVABLE(A,B | q,L)` is only a scoped proposal when all relevant measurement coordinates are common or connected by a predeclared witnessed map. Equal numerical results are neither necessary nor sufficient.

A valid support report preserves, at minimum, a compatible measurand/feature pair, unit or invertible unit transform, measurement model/operator compatibility, non-disjoint regime/phenomenon scope, calibration/traceability validity where required, and an explicit uncertainty-combination contract. Different instrument identities may remain `NOT_PRESERVED`.

The relation does **not** imply:

- `SAME_MECHANISM`;
- `SAME_GENERATOR`;
- target-domain truth;
- scientific authority.

It is symmetric only when the declared maps are valid in both directions. It is not generally transitive: chained calibration/model/operator transforms require their own end-to-end witness and uncertainty contract.

## `OBSERVATIONALLY_EQUIVALENT`

`OBSERVATIONALLY_EQUIVALENT(A,B | q,L,O,P,epsilon)` is stronger than a syntactically valid similarity witness but weaker than mechanism identity. It means the two candidates are not separated by a **frozen** discriminating probe family `P` under the declared observation context `O` and tolerance `epsilon`, with measurement capability sufficient to resolve that tolerance.

The v1 support contract requires:

1. a valid measurement-aware comparison;
2. a pre-result frozen probe family;
3. a positive equivalence tolerance;
4. a separately justified combined uncertainty smaller than or equal to that tolerance;
5. sufficient instrument resolution;
6. probe predictions in a common comparison coordinate if units differ;
7. no frozen probe whose predicted outputs differ by more than the tolerance.

A separating probe returns `OBSERVATIONALLY_DISTINGUISHABLE`. Missing operator, traceability, uncertainty-combination, probe, or coordinate evidence returns `CANNOT_CHECK` rather than a negative scientific claim.

Observational equivalence is always relative to the declared probe family. It is therefore not mechanism identity and is not generally transitive, especially under tolerance accumulation or changing observation operators.

## Uncertainty-composition correction

The first Round-037 support candidate used

`u_compare = sqrt(u_A^2 + u_B^2)`.

Adversarial review rejected that as a generic rule because it silently assumes a dependence/covariance structure. The failed candidate remains in Git history. The promoted candidate performs **no generic uncertainty composition**. Instead `MeasurementMapping` must carry a predeclared rule identifier, its separately checked validity state, and the resulting combined standard uncertainty. If those are unavailable, RAKL returns `CANNOT_CHECK`.

This is the same discipline used for multi-hop bridge error composition: numbers do not acquire a valid composition law merely because they have the same label.

## GLUE / LIFT / JUMP / PROJECT

- **GLUE:** measurement-aware relations may align observational projections at the declared measurement layer. They cannot glue mechanisms merely because results agree.
- **LIFT:** a residual may lift from an instrument-specific result to a measurement schema such as measurand + observation operator + uncertainty model. The erasure ledger must record instrument/procedure details that were dropped.
- **JUMP:** search may use a shared measurement schema, sensor failure mode or observability structure to find distant systems. This is discovery authority only.
- **PROJECT:** transported structure must re-enter the target through a target measurement certificate and target test. A source calibration or observational equivalence does not transfer target authority.

A JUMP can therefore find a sibling with the same observation geometry while a subsequent GLUE still fails because calibration, regime, or uncertainty semantics differ.

## Source projections and prior art

Round 037 deliberately searched metrology, sensor ontologies and inverse-problem observability rather than more analogy literature.

- JCGM/BIPM VIM 3 defines a measurand, measurement model, calibration and metrological traceability; traceability belongs to a measurement result and depends on a documented calibration chain with uncertainty.
- NIST's metrological-traceability policy stresses that calibration of an instrument alone is insufficient and that traceability does not guarantee fitness for purpose.
- W3C SOSA/SSN 2023 distinguishes observations, observable properties, features of interest, sensors/procedures and results.
- Bakeer, Herbers and Marx (2025) show in a real structural-health inverse problem that recoverable parameters and uncertainty depend on sensor layout and experimental design, reinforcing that an observation channel constrains identifiability.
- PTB's open-source dynamic-metrology tooling, including PyDynamic/GUM2DFT, is prior art for explicit propagation of measurement uncertainty through transformations.

These sources narrow novelty claims. RAKL does not claim invention of measurands, calibration, traceability, observation ontologies, observability, or uncertainty propagation. The retained framework contribution is the evidence-governed placement of those coordinates inside typed similarity/transport contracts while keeping representation, observation, mechanism and target authority separate.

## Remaining boundary

This support layer validates **contracts supplied to it**. It does not yet execute calibration chains, validate an external uncertainty model, transform probe values between units, estimate covariance, or prove real scientific transfer utility. Those are explicit blockers, not implied by passing unit tests.
