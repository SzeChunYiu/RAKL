# Meta-evolution v2 — control semantics for Papers IV–VI

Base: `main@e17eaa5498701ed25aa765f4952baaa46f177524`.

Frozen counterexample packet: `META_EVOLUTION_V2_FROZEN_BENCHMARK.json` was committed before the implementation.

Implementation challenger: `src/rakl/meta_evolution_v2.py`.

Tests: `tests/test_meta_evolution_v2.py`.

Nothing in this lane replaces the current production/meta-evolution controller or grants promotion authority.

## Why a successor is needed

Self-RAKL 044 correctly made implementation, workflow, operators, representation, ontology, topology, evaluator, meta-policy and mutation language mutable while keeping the Constitution externally gated. The remaining problem is **information loss between those layers**.

A system is not mature merely because it can mutate more of itself. It is mature when it knows what evidence is required before choosing *which part* to mutate and when it can demonstrate that the evaluator authorizing the change did not co-adapt to the candidate outcome.

## M2.1 Diagnosis before mutation

Current ingredients already exist:

```text
MechanicDiagnosisVerdict.DISCRIMINATOR_REQUIRED
refine_diagnosis_with_discriminator(...)
plan_self_evolution(EvolutionPortrait(causes=...))
```

But the planner takes the causes, not the verdict.

V2 introduces `DiagnosisBoundEvolutionPortrait`.

Rules:

```text
CANNOT_CHECK                     -> RUN_DISCRIMINATOR / register one
DISCRIMINATOR_REQUIRED           -> RUN_DISCRIMINATOR
PARTIALLY_IDENTIFIED across >1 mutation layer -> RUN_DISCRIMINATOR
MECHANIC_GAP_IDENTIFIED          -> mutation routing allowed
NO_GAP                           -> KEEP_INCUMBENT
```

If several surviving causes are different names but all map to the same bounded mutation layer, a layer-local proposal may still be allowed; it must not claim the finer causal attribution.

This is the controller-level consumer for Active Fibre Discriminator / VOI-style mechanics: information acquisition can dominate mutation when the action choice depends on the missing cause identity.

## M2.2 Outer assurance is an object, not a bit

Current higher-order governance asks only:

```text
outer_assurance_frozen: bool
```

V2 requires:

```text
OuterAssuranceBinding
- assurance_id
- exact subject_sha
- evaluator_id
- benchmark_hash
- frozen_before_candidate_outcome
- candidate_outcomes_used_to_define_evaluator
```

For evaluator, meta-policy and mutation-language candidates:

```text
missing binding                       -> BLOCK
subject mismatch                      -> BLOCK
not frozen before candidate outcome   -> BLOCK
candidate outcome used to define evaluator -> BLOCK
outer evaluator == target/inner evaluator -> BLOCK
otherwise -> candidate may ENTER the existing protected promotion gate
```

Passing this gate still does not itself promote the candidate.

### Epoch rule

Within one self-evolution evidence epoch:

```text
subject/evaluator/benchmark/metric/resource contract = fixed
```

If the evaluator changes, close the epoch. The new evaluator defines a new epoch and needs an outer-assurance transition. Do not splice scores across the boundary as though the ruler were unchanged.

This is compatible with the repo's trusted-parent evaluator and protected-input migration rules, but it is a distinct control object: protected-file identity alone does not establish benchmark sufficiency or scientific validity.

## M2.3 Mutation credit is contextual

Current `MutationPolicy` assigns one weight per operator.

V2 uses:

```text
(operator_id, target_layer, scope_key) -> weight
```

Example:

```text
representation_reset succeeds for
paper4 / REPRESENTATION / structural-learning
```

This evidence does **not** change the prior for:

```text
representation_reset on
paper5 / SEARCH_OPERATOR / verified-math
```

Cross-scope credit requires a separately registered transfer/assimilation result. The point is not to forbid transfer; it is to stop transfer being free.

## M2.4 Escalation counts distinct failed hypotheses

Raw attempt count is not epistemic diversity.

V2 represents failed evidence as:

```text
FailureEpochIdentity(epoch_id, family_id)
```

Only distinct `family_id`s contribute to the incumbent broadening thresholds.

Thus:

```text
same family, 3 reruns -> effective failed-family count 1
three materially different families -> count 3
```

A future stronger version should also weight evidence by fresh-assurance quality and parent comparability, but the minimum v2 repair removes the obvious duplicate-count failure.

## M2.5 Validity before frontier

Current `CandidateDelta` is intentionally a soft improvement vector:

```text
quality, cost, latency, robustness, complexity
```

The surrounding theory says blocking validity comes first. V2 makes this explicit in the local selection API:

```text
ValidatedCandidateDelta(
    CandidateDelta(...),
    blocking_validity = PASS | FAIL | CANNOT_CHECK
)
```

Only `PASS` candidates enter ordinary Pareto comparison. `FAIL` or `CANNOT_CHECK` cannot survive because of excellent soft metrics.

## Relation to Papers IV–VI

### Paper IV

A learned allocator candidate enters self-evolution only after the Paper-IV information/policy question localizes the deficit. A representation-state failure and an allocation-policy failure are different mutation layers.

### Paper V

A theorem prover/search candidate is not the same object as a mathematical-research assurance candidate. Proof-search gains cannot update the authority/promotion evaluator unless the corresponding assurance lane passes its own product/trust tests.

### Paper VI

Paper VI should execute this recursively:

```text
fixed audited epoch
-> incumbent/external comparison
-> weakness diagnosis
-> discriminator if needed
-> smallest-layer mutation
-> development
-> fresh assurance under unchanged evaluator
-> validity-gated frontier update
```

If evaluator evolution is proposed:

```text
close epoch
-> outer-assured evaluator candidate
-> benchmark/evaluator replay on anchor set
-> new evaluator epoch
```

## Falsifiers for v2 itself

The v2 controller should be rejected/narrowed if a stronger benchmark shows that:

- discriminator-first routing costs more than broad mutation without reducing wrong-layer/harm events in the applicable regime;
- context-scoped mutation credit prevents legitimate transfer that a registered transport could have predicted;
- distinct-family counting delays necessary escalation without reducing duplicate-driven escalation;
- the outer-assurance binding does not catch evaluator self-conditioning or creates a meaningless naming-only separation;
- validity gating duplicates an already-sovereign upstream gate without preventing any reachable failure mode.

These are future empirical questions. The current v2 benchmark is conformance/counterexample work only.
