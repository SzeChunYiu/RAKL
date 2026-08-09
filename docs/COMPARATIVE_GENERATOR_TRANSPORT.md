# Comparative Generator Transport

Status: research/support method layer v0.1  
Date: 2026-08-09

## 1. Why GLUE and JUMP need LIFT and PROJECT

The Apple Principle is local-to-global: papers and theories are contextual projections of an underlying object. But when the target object remains unresolved, repeatedly searching only for more target-specific views can stall.

RAKL therefore extends the discovery lifecycle to:

```text
GLUE <-> LIFT <-> JUMP <-> PROJECT
```

- **GLUE** aligns compatible local views at a declared abstraction level.
- **LIFT** maps the unresolved target into one or more candidate parent/latent-generator descriptions while recording what is erased.
- **JUMP** searches sibling realizations or distant domains under those generator/abstract descriptions.
- **PROJECT** transports only structure licensed by the shared generator/mechanism witness back into the target as a testable hypothesis.

A JUMP at one level may therefore become a GLUE at a higher level without making the lower-level objects identical.

## 2. Level-indexed relations

Similarity and generator relations are conditioned on question/QoI `q` and abstraction level `L`:

\[
R(A,B\mid q,L).
\]

For one question, apple and banana may be merely `SHARES_CATEGORY_WITH`. For another they may instantiate a common ripening mechanism family. For a mathematical QoI they may share only an abstract feedback schema.

RAKL does not maintain one universal parent tree. Multiple contextual generator charts may coexist.

## 3. Generator relation types and default authority

| Relation | Meaning | Default authority |
|---|---|---|
| `SHARES_CATEGORY_WITH` | common taxonomy/category | discovery hint only |
| `SHARES_PARENT_WITH` | common declared parent concept | retrieval hint only |
| `SHARES_ABSTRACT_SCHEMA_WITH` | common residual-relevant abstract pattern | analogy proposal only |
| `SHARES_MECHANISM_FAMILY_WITH` | common mechanism family with different realizations allowed | transfer hypothesis only after registered query/intervention checks |
| `SHARES_GENERATOR_WITH` | same scoped generator under explicit maps | transfer hypothesis only after generator identity/core/regime/commutation checks |

No relation grants target-domain authority without target evidence.

## 4. LIFT contract

A lift

\[
\alpha_i:X_i\rightarrow G
\]

must record:

```text
instance and domain
generator candidate id
question/QoI
abstraction level L0-L6
mapping pairs
PRESERVED structure
NOT_PRESERVED structure
erased coordinates
instance-specific deviations
validity regime
evidence identities
evidence-lineage identities
environment identity
registered intervention/query probes
commutation result
freeze chronology
```

Abstraction is explicitly lossy. Erased information is not silently recovered by later projection.

## 5. Generator witness via commuting probes

For a strong mechanism/generator relation, source and target must share registered query/intervention semantics. Conceptually, the relevant diagram should agree within the declared tolerance/regime:

```text
concrete source action/result  --LIFT-->  generator action/result
          |                                   |
       source map                           core law
          |                                   |
concrete target hypothesis <--PROJECT-- generator consequence
```

A common equation name, category or embedding neighborhood is insufficient. If a mapped intervention or query fails to commute, the generator transfer is rejected or narrowed.

## 6. Comparative Generator Inference

Instead of forcing all siblings into one theory, RAKL models a candidate family as:

\[
T_i = G + \Delta_i,
\]

where `G` is a predeclared candidate shared core and `Delta_i` contains instance-specific structure.

For a registered core feature set `K_G`, each sibling is classified:

- **SUPPORTED** — every required core feature is explicitly preserved;
- **OUTLIER** — at least one required core feature is explicitly not preserved;
- **UNKNOWN** — evidence does not resolve all required core features.

Outliers and unknowns remain in history. They are not deleted to make the generator look cleaner.

## 7. Evidence ancestry and environment diversity

Source count is not independent evidence count.

Multiple papers may share:

```text
one originating theory
one dataset
one benchmark
one codebase
one review article
one conceptual template
```

RAKL therefore records **evidence-lineage identities** separately from documents/domains. Repeated support from one lineage is `CORRELATED_SUPPORT_ONLY`.

Environment diversity is a second coordinate. A candidate generator supported across distinct evidence lineages and materially different environments can be more informative because environment variation can discriminate stable from accidental structure. Even then the result is only `CORROBORATED_GENERATOR_PROPOSAL_ONLY` until stronger evidence establishes the generator.

## 8. Candidate-parent lattice

When stuck, RAKL should not ask for one parent and commit greedily. It should generate a non-greedy set of residual-relevant candidate parents/generators, for example:

```text
apple
  -> fruit
  -> climacteric ripening system
  -> porous biological tissue
  -> viscoelastic cellular solid
  -> generic feedback/state-transition system
```

Each is a different chart with different transfer implications. Shared-attribute/concept-lattice methods can help generate candidate parents, but causal/mechanistic authority still requires the stronger RAKL witness.

## 9. Search when stuck

A generator-aware search loop is:

```text
1. localize unresolved target residual
2. identify which target-specific coordinates the residual depends on
3. relax irrelevant coordinates and retain an erasure ledger
4. generate several candidate parents/generators
5. retrieve sibling realizations for each candidate
6. LIFT sibling theories to the candidate generator
7. test core/regime/intervention/query compatibility
8. preserve correlated lineages, outliers and unknown siblings
9. PROJECT only licensed generator consequences back into target
10. freeze target falsifier and test
11. update both target and generator hypotheses
```

This is a search architecture, not a guarantee that a useful sibling exists.

## 10. Relation to existing similarity algebra

The existing RAKL similarity witness remains primary for pairwise mapping. Comparative Generator Transport adds three coordinates that were missing:

1. explicit level-changing LIFT/PROJECT operations;
2. a typed authority boundary between category/parent/schema/mechanism/generator relations;
3. comparative family evidence with lineage, environment, outlier and unknown preservation.

`retrieval != recognition != generator witness != projected transfer != target authority` remains mandatory.

## 11. Adversarial failure modes

```text
CATEGORY_ESCALATION         shared taxonomy treated as mechanism evidence
PARENT_OVERCOMMIT           one ontology parent treated as the only valid generator
GENERATOR_NAME_EQUIVOCATION same generator label used for different scoped laws
COMMUTATION_FAILURE         mapped interventions/queries disagree
REGIME_COLLAPSE             siblings compared outside common validity scope
LINEAGE_PSEUDOREPLICATION   correlated papers counted as independent confirmation
OUTLIER_ERASURE             conflicting sibling removed after seeing outcomes
UNKNOWN_AS_SUPPORT          missing core evidence silently counted as preservation
POSTHOC_CORE_EDIT           generator definition changed after sibling outcomes
PROJECT_OVERREACH           target claim contains structure erased during LIFT
TARGET_AUTHORITY_LEAK       successful source/generator witness treated as target evidence
```

## 12. Benchmark requirement

Real validation must compare at least:

```text
direct target-only search
single-parent greedy LIFT
multi-parent/lattice LIFT
sibling generator search
PROJECT with and without intervention/query checks
```

under matched model, task, evaluator and resource budgets. Include true generators, competing generators, category-only false parents, abstract-schema false friends, regime exceptions, correlated evidence lineages, outliers, unknown siblings and target refutations.

If generator-mediated search does not improve valid target transfer or discrimination at acceptable cost, it remains optional complexity.

## 13. Novelty boundary

RAKL does not claim novelty for causal abstraction, invariant transfer, hierarchical/multitask sharing, phylogenetic dependence correction or Formal Concept Analysis. The candidate contribution is their evidence-governed integration into the Apple/Knowledge-Atlas lifecycle with typed relation authority, immutable negative history and target-validation separation.
