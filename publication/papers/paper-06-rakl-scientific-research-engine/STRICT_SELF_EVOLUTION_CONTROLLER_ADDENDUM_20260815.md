# Paper VI / Self-RAKL — canonical strict controller boundary (2026-08-15)

This addendum supersedes any implication that the versioned `meta_evolution*` modules are interchangeable current entrypoints. They remain immutable research/replay surfaces. The **current orchestration entrypoint** is:

```text
src/rakl/self_evolution_controller.py
CURRENT_SELF_EVOLUTION_CONTROLLER
```

The controller accepts only strict V4/V5 content-addressed objects for load-bearing planning, credit and evaluator-governance inputs. In particular:

- historical `DiagnosisBoundEvolutionPortrait` inputs are explicitly type-rejected;
- historical free-scope contextual-credit policies are explicitly type-rejected;
- historical/display-name evaluator identities are explicitly type-rejected;
- strict contextual credit is keyed by operator-contract digest × target layer × canonical context digest and cross-context transport requires an exact witness;
- strict evaluator governance requires exact Git subject identity plus content-addressed evaluator/dependency/metric/benchmark/environment/cutoff identities;
- invalid and CANNOT_CHECK candidates are removed before soft Pareto comparison.

The controller delegates these mechanics to `meta_evolution_v5`; it does not reimplement a competing diagnosis, credit, governance or frontier policy. It has no method that changes scientific authority and no automatic method-promotion operation. A positive controller result means at most that a challenger may enter the already-existing protected method gate.

This is the final local integration boundary. The remaining trust root is external: local code cannot self-certify that an external evaluator, benchmark, actor, GPU run or corpus truly corresponds to the bytes represented by a supplied digest. That mapping requires external provenance/attestation and is intentionally outside the self-evolution controller.
