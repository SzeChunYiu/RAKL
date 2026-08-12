# Implementer Checklist

## Before coding

- [ ] Checkout/bind to intended baseline SHA.
- [ ] Run full existing unit suite.
- [ ] Save baseline test result.
- [ ] Create `research/mechanics_of_mechanics_v1/`.
- [ ] Record incumbent behavior on selected known worlds.
- [ ] Confirm no new module imports alter runtime defaults.

## Telemetry

- [ ] Add `MechanicsEpisode`.
- [ ] Canonical subject hash.
- [ ] Resource receipt.
- [ ] Serialize to JSONL.
- [ ] Replay test.
- [ ] Negative-history pointer.
- [ ] No chain-of-thought fields.

## Mechanic deficiency

- [ ] Add `MechanicKind`.
- [ ] Add diagnosis verdicts.
- [ ] Add candidate cause object.
- [ ] Add discriminator object.
- [ ] Implement rule-based V0.
- [ ] Ambiguity preserved.
- [ ] `UNKNOWN` path.
- [ ] No authority effects.
- [ ] Tests.

## Mechanics controller

- [ ] `MechanicsDecisionState`.
- [ ] `MetaActionKind`.
- [ ] `MechanicsActionProposal`.
- [ ] `MechanicsPlan`.
- [ ] V0 with keep/change-operator/discriminator.
- [ ] Delegate to existing search controller.
- [ ] Cost ceiling.
- [ ] Root-QoI binding.
- [ ] Tests.

## Representation search

- [ ] `RepresentationEffect`.
- [ ] `RepresentationTransform`.
- [ ] `RepresentationCandidate`.
- [ ] `RepresentationTransitionWitness`.
- [ ] Identity transform always available.
- [ ] Lossy transform blocked from equivalence.
- [ ] Probe suite.
- [ ] Cost receipt.
- [ ] Tests.

## Scale

- [ ] `ScaleState`.
- [ ] `ScaleTransitionWitness`.
- [ ] `CoverageReceipt`.
- [ ] `CoverageScoutPolicy`.
- [ ] Hidden-feature negative control.
- [ ] Coarse/global residual world.
- [ ] Root binding.
- [ ] Tests.

## Solution field

- [ ] `FieldNode`.
- [ ] `FieldEdge`.
- [ ] `FieldBoundaryCondition`.
- [ ] exact arrival field.
- [ ] conductive field.
- [ ] field action ranker.
- [ ] breakdown-front policy.
- [ ] conductance update.
- [ ] branching budget.
- [ ] exploration reserve.
- [ ] disconnected-target handling.
- [ ] total cost accounting.
- [ ] tests.

## Field + representation

- [ ] Same world in >=2 representations.
- [ ] exact oracle cost-to-go.
- [ ] gradient alignment metric.
- [ ] path compression metric.
- [ ] decode verification.
- [ ] false-attractor metric.
- [ ] lift-overhead metric.

## Recursive composition

- [ ] `SolverInterfaceContract`.
- [ ] scale-local child identity.
- [ ] parent invariant.
- [ ] `EMERGENT_COMPOSITION_RESIDUAL`.
- [ ] hierarchical verification schedule.
- [ ] tests for local-pass/root-fail.

## Auxiliary object

- [ ] object kind enum.
- [ ] frozen request.
- [ ] explicit desired effect.
- [ ] falsifiers.
- [ ] candidate freeze chronology.
- [ ] downstream validation.
- [ ] fresh-transfer field.

## Benchmark harness

- [ ] deterministic world generator.
- [ ] seeded runs.
- [ ] baseline implementations.
- [ ] oracle implementation.
- [ ] dev/fresh split.
- [ ] resource matching.
- [ ] mutation tests.
- [ ] summary metrics.
- [ ] family-specific breakdown.
- [ ] raw receipts retained.

## Promotion

- [ ] no default runtime integration before fresh result.
- [ ] atomic ablations.
- [ ] no failed history deletion.
- [ ] scope recorded.
- [ ] result can be `NO_BENEFIT`.
- [ ] ordinary RAKL promotion gates used.
