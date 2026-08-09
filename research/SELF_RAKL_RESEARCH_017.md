# SELF-RAKL Research Round 017 — Comparative Generator Inference and LIFT/JUMP/PROJECT Transport

Date: 2026-08-09

Starting `main`: `58881dda74ebc2a3fe9ed22ddda98d4d31d25cdb`

Entering status: `ACTIVE_NON_FLAT`.

## 1. Baseline audit

Live repository audit before selecting the atom:

```text
main = 58881dda74ebc2a3fe9ed22ddda98d4d31d25cdb
open issues = 0
open pull requests = 0
Constitution SHA = 4d456ceab32122391c830fe8586766cf0e0037aa
latest completed research round = SELF_RAKL_RESEARCH_016
exact-head push test workflow = completed success
trusted-parent evaluator = skipped, not counted as a passing test
similarity lane = ACTIVE_NON_FLAT
```

Round 016 left real MIR route execution blocked on artifact transport, but the user supplied a materially new residual: when apple-specific understanding stalls, RAKL should be able to LIFT to a candidate shared generator, search sibling realizations such as banana, and PROJECT only the generator-level structure back into apple. The central atomic question became:

> How can RAKL distinguish a weak shared category from a scientifically useful shared generator, and how can repeated sibling evidence support a latent generator without hiding correlated ancestry, outliers, regime failures or target-transfer failure?

## 2. Six-role panel

1. **Cognitive-science / analogy expert** — treated abstraction level as a search coordinate and emphasized that a JUMP at one level can become a GLUE at a higher level.
2. **Knowledge-representation / ontology expert** — rejected a single universal parent tree; favored multiple candidate parent/generator charts and concept-lattice style organization.
3. **Scientific-information-retrieval expert** — required sibling retrieval to remain separate from generator recognition and target transfer, and proposed generator-conditioned retrieval routes rather than only broader keywords.
4. **Applied-mathematics / dynamical-systems expert** — required explicit preserved cores, overlapping regimes and intervention/query commutation for strong generator claims.
5. **Computational-creativity / search expert** — favored non-greedy portfolios of candidate generators and sibling realizations, with instance deviations retained rather than forcing one template.
6. **Adversarial scientific-method reviewer** — attacked category-to-mechanism escalation, correlated evidence ancestry, post-hoc generator definitions, outlier suppression and target-authority leakage.

These were role-separated passes in one orchestration context and are not claimed as independent reviewers.

### Delegation and disagreements

| Finding | Primary roles | Adversarial failure condition |
|---|---|---|
| `GLUE <-> LIFT <-> JUMP <-> PROJECT` lifecycle | cognitive analogy + ontology | fails if changing level merely renames the objects without preserving the residual-relevant structure |
| intervention/query commutation for generator evidence | applied math + ontology | fails if mapped interventions have incompatible effects or semantics |
| evidence-lineage diversity must be recorded | adversarial + IR | fails if multiple papers share one intellectual/data lineage and are counted as independent corroboration |
| generator + instance deviation rather than hard merge | creativity + applied math | fails if the alleged shared core does not survive the registered sibling set/regimes |
| candidate-parent lattice instead of one taxonomy | ontology + creativity | fails if candidate parents are unconstrained semantic abstractions with no discriminating tests |
| invariance across heterogeneous environments | applied math + adversarial | fails when the claimed core changes under a legitimate environment/intervention where it should remain invariant |

## 3. Fresh cross-domain projections

### 3.1 Causal abstraction: generator maps should respect interventions

Rubenstein et al., *Causal Consistency of Structural Equation Models* (`arXiv:1707.00819`), formalize consistency across levels by requiring agreement about intervention effects. Lorenz and Tull, *Causal and Compositional Abstraction* (`arXiv:2602.16612`, 2026), generalize low/high-level abstraction using compositional/categorical structure and distinguish upward and downward mappings of queries/interventions.

**RAKL assimilation:** a strong `SHARES_GENERATOR_WITH` claim should not be certified by common labels or equation form alone. Registered intervention/query semantics must commute through the instance-to-generator maps within the claimed regime. This is prior art at the causal-abstraction level; RAKL's role is to integrate it into the GLUE/LIFT/JUMP/PROJECT authority lifecycle.

### 3.2 Causal transfer: heterogeneous environments can reveal a stable generator

Rojas-Carulla et al., *Invariant Models for Causal Transfer Learning* (JMLR 2018), use conditional invariance across tasks/environments for transfer. Madaleno et al., *Bayesian Hierarchical Invariant Prediction* (CLeaR/PMLR 2026), combine hierarchical Bayes with explicit testing of mechanism invariance under heterogeneous data.

**RAKL assimilation:** sibling diversity is not merely noise. Deliberately varied environments can become discriminating probes for a hidden generator. A generator that survives only one narrow sibling/context receives weaker status than one whose registered core remains invariant across materially different environments.

### 3.3 Robust multitask learning: shared representation plus instance deviations

Tian, Gu and Feng, *Learning from Similar Linear Representations: Adaptivity, Minimaxity, and Robustness* (JMLR 2025), explicitly study tasks with similar but not identical representations and outlier tasks rather than assuming exact sharing.

**RAKL assimilation:** do not force `T_apple = T_banana = G`. Prefer the structural pattern

```text
T_i = G + Delta_i
```

where `G` is a candidate shared core and `Delta_i` records instance-specific deviations. Outlier siblings remain visible negative evidence instead of being averaged away.

### 3.4 Comparative biology: sibling evidence is not automatically independent

Phylogenetic comparative methodology exists because observations from related species can be statistically dependent through shared ancestry. Recent work continues to emphasize joint treatment of character evolution and diversification/non-independence (e.g. *Evolving View of Character Macroevolution*, Systematic Biology 2026).

**RAKL assimilation:** multiple analogy/generator witnesses that descend from one paper family, dataset, benchmark, method template or conceptual lineage cannot be counted as independent corroboration. Round 017 therefore tracks evidence-lineage identities separately from source count and environment count.

### 3.5 Formal Concept Analysis: there may be many valid parents

Formal Concept Analysis constructs concept lattices from objects and their shared attributes rather than forcing one taxonomy. Recent FCA work continues to use lattices to expose commonality, variability and exception-tolerant concepts.

**RAKL assimilation:** an apple residual may lift simultaneously toward `fruit`, `ripening system`, `porous biological tissue`, `viscoelastic cellular solid`, or another residual-relevant parent. RAKL should maintain a portfolio/lattice of candidate generators and discriminate them, rather than choosing one universal ontology parent prematurely.

## 4. Central result: JUMP at one level can become GLUE at another

For question/QoI `q` and abstraction level `L`, relation claims should be indexed as

\[
R(A,B\mid q,L).
\]

At L1, apple and banana are different domain objects. At a higher residual-relevant level, both may become local realizations of the same candidate generator. Therefore:

```text
JUMP at L_k
    -> LIFT
    -> candidate generator G at L_{k+1..6}
    -> GLUE sibling projections of G
    -> PROJECT surviving generator structure back to target
```

This does not make the lower-level objects identical.

## 5. Generator relation authority is typed

Round 017 adds the following relation family:

```text
SHARES_CATEGORY_WITH
SHARES_PARENT_WITH
SHARES_ABSTRACT_SCHEMA_WITH
SHARES_MECHANISM_FAMILY_WITH
SHARES_GENERATOR_WITH
```

They have deliberately different default authority:

```text
shared category       -> discovery hint only
shared parent         -> retrieval hint only
shared abstract schema-> analogy proposal only
shared mechanism family -> transfer hypothesis only after mapped query/intervention checks
shared generator      -> transfer hypothesis only after generator identity, core, regime and commutation checks
```

No relation grants target-domain authority by itself.

## 6. Comparative Generator Inference

A candidate generator `G` is tested across sibling lifts `alpha_i : X_i -> G` using a predeclared core `K_G`.

Each sibling is classified separately:

```text
SUPPORTED  all registered core features are preserved
OUTLIER    at least one registered core feature is explicitly NOT_PRESERVED
UNKNOWN    available evidence does not resolve every required core feature
```

Corroboration additionally records:

```text
evidence lineage diversity
environment diversity
abstraction level
question/QoI
regime
instance-specific deviations
erasure ledger
```

Support from one evidence lineage is `CORRELATED_SUPPORT_ONLY`, even if many papers repeat it. Support across multiple lineages and multiple environments can become `CORROBORATED_GENERATOR_PROPOSAL_ONLY`; this still does not prove the generator true.

## 7. Frozen benchmark and implementation

Before implementation, `research/SELF_RAKL_RESEARCH_017_FROZEN_BENCHMARK.json` was committed at:

```text
5d00e25d47d6f3b0971a6f9945eb7151fd84d9c8
```

The 18 frozen worlds include category-only false transfer, weak parent relations, abstract-schema-only analogy, commuting and non-commuting interventions, regime mismatch, abstraction-level mismatch, core contradiction, correlated lineage support, multi-lineage/environment corroboration, outliers, unknown siblings, target refutation, hidden-label leakage and post-hoc generator expansion.

Candidate implementation:

```text
src/rakl/generator_transport.py
tests/test_generator_transport.py
src/rakl/__init__.py
candidate head = bbe4d8f3b9158e3ec1c2702dbd9397045f982229
```

The unchanged repository `test` workflow executed on the exact candidate head and completed successfully, including `pytest` (workflow run `31311360315`, job `93239568864`). The candidate was ahead-only by three commits, changed only the new module/tests/export, and protected evaluator/workflow inputs were unchanged. `main` was rechecked at the frozen benchmark head and non-forced fast-forwarded to the exact tested candidate.

The support layer is research-only. It cannot activate a search route, prove a real generator, promote canonical scientific knowledge or turn a target-test result into authority without the existing promotion/evidence rules.

## 8. Retained semantic objects

1. `LEVEL_INDEXED_RELATION_R(A,B|q,L)`
2. `GLUE_LIFT_JUMP_PROJECT_LIFECYCLE`
3. `INTERVENTION_QUERY_COMMUTING_GENERATOR_WITNESS`
4. `GENERATOR_PLUS_INSTANCE_DEVIATION_MODEL`
5. `EVIDENCE_LINEAGE_DIVERSITY_FOR_GENERATOR_CORROBORATION`
6. `CANDIDATE_PARENT_GENERATOR_LATTICE`
7. `HETEROGENEOUS_ENVIRONMENT_GENERATOR_DISCRIMINATION`
8. `OUTLIER_AND_UNKNOWN_SIBLING_PRESERVATION`

These are internal method objects. Causal abstraction, invariance, hierarchical/multitask sharing, phylogenetic non-independence and concept lattices are prior art and are not claimed individually as RAKL inventions.

## 9. Saturation state

```text
RAKL_METHOD = ACTIVE_NON_FLAT
similarity_generator_lane = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

The lane is non-flat because generator-level relation typing, evidence-lineage dependence, outlier-preserving comparative inference and executable LIFT/PROJECT contracts are new retained coordinates. Real scientific generator discovery has not yet been benchmarked.

## 10. Next discriminators

Highest-value new empirical fiber:

```text
META_N068_REAL_COMPARATIVE_GENERATOR_BENCHMARK
```

Freeze real sibling systems with known/contested parent mechanisms and false-parent controls, then test whether LIFT + sibling retrieval + generator recognition + PROJECT improves target hypothesis quality over direct target-only search under matched model/resource budgets.

Continue in parallel:

- `META_N060_REAL_MIR_ROUTE_EXECUTION` when pinned MIR bytes become available;
- `META_N064_EVIDENCE_LINEAGE_DEPENDENCE` with explicit evidence ancestry rather than source count;
- `META_N067_HETEROGENEOUS_ENVIRONMENT_GENERATOR_INVARIANCE` using intervention/environment variation;
- `META_N065_PARTIAL_POOLING_GENERATOR_DEVIATIONS` to determine when a generator core plus `Delta_i` outperforms hard GLUE or no sharing;
- `META_N066_CANDIDATE_PARENT_LATTICE_SEARCH` to compare one-parent greedy lifting against non-greedy candidate-generator portfolios.

### Result branches for the next AI

**Positive:** retain only generator operators that improve frozen valid-transfer or discrimination QoIs without blocking regressions.

**Null:** if direct target-only search matches LIFT/JUMP/PROJECT at lower cost, keep generator transport optional and preserve the null.

**Refuted:** if intervention commutation or lineage-aware family assessment rejects known valid generators, preserve the counterexamples and revise the support contract before active use.

**Partial-ID:** if only some generator coordinates are identifiable, transport only those coordinates and leave the remainder UNKNOWN/NOT_PRESERVED.

**Blocked:** if real sibling corpora, intervention semantics or target tests cannot be pinned, report `CANNOT_CHECK` rather than using category labels as surrogate truth.

**Transport:** if `main` moves during a future candidate evaluation, rebuild against current main without changing the frozen benchmark predictions.

The Constitution remains unchanged.
