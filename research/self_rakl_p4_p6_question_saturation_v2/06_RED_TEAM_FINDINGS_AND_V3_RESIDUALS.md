# Red-team findings on meta-evolution v2

This file was written **after** the v2 frozen benchmark and implementation. It therefore does not amend the v2 freeze. It records successor residuals for a future version.

## R1 — discriminator required != discriminator selected well

V2 correctly blocks mutation when diagnosis says `DISCRIMINATOR_REQUIRED`, but it does not choose among discriminators by decision value/cost.

Do not add a duplicate selector here. Existing work already owns this space:

- `research/unified_problem_solving_v1/diagnosis_active_successor.py` implements a leakage-free sequential diagnosis research lane;
- `research/mechanic_research_packets_v1/PAPER5_PAPER6_SUCCESSORS.json` contains `diagnosis_discriminating_intervention_v2` with stronger parents including information-gain diagnosis, myopic value-of-information and a finite-horizon Bayes oracle.

Required integration question:

> Can the meta-evolution planner consume that diagnosis/discriminator policy so the next information-acquisition action is selected by expected decision change per total cost, rather than merely exposing a RUN_DISCRIMINATOR action?

Status: `EXISTING_LANE_TO_COMPOSE`, not a new mechanic proposal.

## R2 — contextual scope keys are still opaque strings

V2 prevents free global credit by indexing mutation credit with `scope_key`, but a caller could evade negative history by renaming an equivalent scope.

Future repair should use a content-bound context object or canonical context digest containing at least:

```text
paper/fibre or consumer
QoI semantics
population/domain/regime
resource/evaluator epoch
assumptions/evidence cutoff
```

Credit transport between distinct context digests should require an explicit transition/assimilation witness.

Status: `V3_CANDIDATE_IDENTITY_GAP`.

## R3 — distinct failure-family ids can be gamed by renaming

V2 replaces raw failure counts with distinct `family_id`s. This blocks exact duplicate reruns but does not prove two differently named families are semantically different.

A future escalation receipt should bind a canonical mutation-family signature or DifferenceWitness such as:

```text
target layer
operator/mechanism class
changed contract fields
preserved fields
predicted causal effect
falsifier family
```

Three aliases of one mechanism must count once.

Status: `V3_CANDIDATE_SEMANTIC_DEDUP_GAP`.

## R4 — outer evaluator identity can be naming-only unless content bound

V2 requires `outer_assurance.evaluator_id != target_evaluator_id`, exact subject, benchmark hash and pre-outcome chronology. The API assumes evaluator identity is itself content-bound; it does not prove that property.

A production successor should bind at least:

```text
evaluator source/content hash
dependency/environment identity
metric/specification hash
benchmark/artifact hash
evidence-lineage key
parent/supersession relation
```

A different label on identical/self-conditioned evaluator content is not independence.

This should compose with:

- `src/rakl/parent_evaluator.py`;
- `docs/EVALUATOR_DEPENDENCY_PINNING.md`;
- `docs/EVALUATOR_INTEGRITY_MERGE_ORDER_INCIDENT_710.md`.

Status: `V3_CANDIDATE_OUTER_ASSURANCE_IDENTITY_GAP`.

## R5 — validity-gated Pareto must be on the live selection path

The v2 wrapper proves a local API property. It does not establish that every production/self-evolution caller uses the wrapper.

Promotion requires a call-graph/integration proof or tests showing no direct soft-Pareto path can bypass the blocking validity gate.

Status: `LIVE_WIRING_GAP`.

## R6 — question saturation needs a cost of inquiry

The current question audits are non-scalar and sign-robust, but Self-RAKL still needs a principled way to choose which open question to execute first under limited compute. The repository has agenda/value and VOI candidate mechanics; the correct next step is to bind question priority to **expected decision change / falsification leverage / cost**, not “novelty” or paper number.

Status: `COMPOSE_WITH_EXISTING_AGENDA_VOI_LANES`.

## Red-team conclusion

Meta-evolution v2 is a useful **information-preservation challenger**, not a complete recursive-improvement architecture. It should pass/fail its frozen counterexamples first. Any v3 work must receive its own pre-implementation freeze and must not rewrite the v2 packet after seeing CI/results.
