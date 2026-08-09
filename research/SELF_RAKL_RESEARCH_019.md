# SELF-RAKL Research Round 019 — Multi-Hop Scientific Bridge Composition

Date: 2026-08-09

Starting `main`: `bdd860681be211959b0f2ba067525d6da8ffbd24`

Entering state: `ACTIVE_NON_FLAT`.

## 1. Baseline and selected atom

Round 018 left all 24 registered framework method surfaces explicit, with zero unclassified high-impact steps but at least one unresolved empirical/trust/benchmark blocker on every surface. `META_N040_MULTI_HOP_ANALOGY_COMPOSITION` remained open since Round 011: RAKL had a theory statement for path certificates, but no executable support contract distinguishing a navigable chain from a genuinely transfer-composable chain.

Selected question:

> When individually valid analogy witnesses form A→B→C→..., what additional conditions are required before RAKL may carry any structure end-to-end without inventing an endpoint relation or target authority?

## 2. Six-role panel

All roles were used as separate reasoning passes in one orchestration context. They are not claimed as independent or mutually blind review.

1. **Cognitive-science / analogy expert** — treated compositional analogy as a distinct cognitive operation from pairwise mapping; required explicit rule/invariant continuity rather than intuitive chaining.
2. **Knowledge-representation / ontology expert** — required exact intermediate-object identity and typed role handoff; rejected endpoint-relation closure for mixed relation classes.
3. **Scientific-information-retrieval expert** — treated multi-hop paths as candidate retrieval/navigation objects and separated path discovery from transfer validity.
4. **Applied-mathematics / dynamical-systems expert** — required common regime and a valid composition rule for any accumulated approximation/error statement.
5. **Computational-creativity / search expert** — retained deeper/diverse paths as discovery candidates, but accepted a Pareto rather than scalar depth objective.
6. **Adversarial scientific-method reviewer** — supplied hostile worlds for invariant drift, QoI drift, role drift, empty global regime, correlated evidence, hidden endpoint labels, post-hoc path selection, error-composition invalidity and authority escalation.

### Material finding delegation

| Finding | Primary roles | Adversarial failure condition |
|---|---|---|
| navigable != composable | cognitive analogy + IR | locally valid hops with no invariant carried through every hop |
| shared-node handoff contract | ontology + cognitive analogy | B identity/roles differ across adjacent witnesses |
| global regime intersection | applied math + ontology | each pair has a regime but the full-path intersection is empty |
| no endpoint relation minting | ontology + adversarial reviewer | mixed local relation types silently become a stronger endpoint claim |
| certified error composition | applied math + adversarial reviewer | pairwise numeric divergences are combined without a theorem/rule that licenses composition |
| path diversity is proposal-space diversity | IR + creativity/search | deeper path increases novelty but loses grounding or validation readiness |

## 3. Fresh external projections

### 3.1 SciNets — depth/diversity and grounding are different coordinates

SciNets (arXiv:2601.09727) frames scientific synthesis as graph-constrained multi-hop reasoning and compares shortest-path, diverse k-shortest, random-walk and RAG-style strategies. Its reported behavioral result is a trade-off: deeper/diverse symbolic paths increase grounding instability, while shortest paths are comparatively stable but conservative.

**RAKL consequence:** path depth/domain distance are discovery coordinates, not evidence authority. Multi-hop search should eventually compete on a Pareto frontier including structural continuity, grounding stability, validation readiness, risk and cost.

### 3.2 CARV — composition is a separate analogy failure axis

CARV (arXiv:2603.27958) extends analogy from one source pair to multiple source pairs, requiring symbolic rule extraction and composition, and reports substantial failure even for strong contemporary multimodal models.

**RAKL consequence:** a pairwise witness benchmark is insufficient evidence for path composition. `META_N040` needs its own hostile worlds and evaluator.

### 3.3 Causal and Compositional Abstraction — maps can have compositional structure

Lorenz and Tull (arXiv:2602.16612) formulate causal abstractions as natural transformations in compositional models, including upward/downward query mappings and component-level abstraction.

**RAKL consequence:** composability is meaningful only relative to a declared map/query semantics. It does not justify generic transitivity across arbitrary RAKL similarity relations.

### 3.4 Compositional abstraction error — the first implementation was too permissive

Rischel and Weichwald (arXiv:2103.15758) explicitly develop an abstraction-error notion with compositional bounds. Their motivation includes the fact that an ordinary divergence such as KL does not generically provide the path-style triangle behavior one might naively assume.

This source exposed a flaw in the first Round-019 implementation: it summed generic per-hop values called `approximation_error_upper_bound` without identifying the error semantics or a composition theorem.

The panel rejected that behavior. Instead of rewriting the frozen benchmark, Round 019 preserved the first tested implementation in history, committed `SELF_RAKL_RESEARCH_019_ERROR_COMPOSITION_ADDENDUM.json`, and built a second tested correction. The corrected support layer requires matching error semantics plus a predeclared certified composition rule before any numerical path bound is accumulated.

### 3.5 Category-theoretic analogy

Recent category-theoretic treatments of analogy use objects/morphisms and constructions such as functors, pullbacks or pushouts to describe structural relations across domains.

**RAKL consequence:** relation composition has formal prior art, but RAKL keeps a conservative default: no endpoint relation is minted unless a relation-specific composition rule is separately registered, proved/scoped and benchmarked.

### 3.6 Open-source inspection

`100hard/SciNets-Core` was inspected as an executable prior-art projection. It builds literature concept graphs, searches structural holes, generates bridge hypotheses and performs adversarial evidence gathering. RAKL does not count graph bridge search itself as novelty.

## 4. Frozen benchmark chronology

Before implementation, Round 019 committed:

```text
research/SELF_RAKL_RESEARCH_019_FROZEN_BENCHMARK.json
commit = afdd5779e0cccb3402e96e9cbc4605d0df13fdf1
```

The benchmark freezes 18 worlds covering valid shared-invariant paths, changing invariants, intermediate identity mismatch, role handoff mismatch, QoI drift, empty full-path regime intersection, broken/unresolved invariants, missing/invalid error bounds, correlated evidence, leakage/post-hoc adaptation, single-hop misuse, mixed-relation endpoint escalation and target pass/refutation.

## 5. First support implementation and exact-head validation

Candidate branch:

```text
self-rakl/round019-bridge-composition
head = fe35a0398836666d8f5bce095ca7a2ee439a76fd
```

Added:

```text
src/rakl/bridge_composition.py
tests/test_bridge_composition.py
public exports in src/rakl/__init__.py
```

Exact candidate workflow:

```text
run = 31316427927
pytest job = 93252324371
conclusion = success
```

The candidate was three commits ahead and zero behind the frozen benchmark head, with only the support module, tests and public export changed. `main` was rechecked at the frozen head before a non-forced fast-forward to the exact tested candidate.

## 6. Same-round adversarial residual and correction

The applied-mathematics and adversarial roles then challenged the generic additive error assumption using the fresh compositional-abstraction source.

This produced a native residual rather than a hidden edit. Round 019 committed:

```text
research/SELF_RAKL_RESEARCH_019_ERROR_COMPOSITION_ADDENDUM.json
commit = ec75c216d67635d1a19c6316cc80f65918d637f2
```

before corrective implementation.

The addendum freezes five hostile worlds:

```text
missing composition rule -> CANNOT_CHECK
mixed error semantics -> REJECT
uncertified generic KL addition -> CANNOT_CHECK
certified matching additive rule -> composable if within tolerance
post-hoc rule selection -> TRIAL_INVALID
```

Corrective candidate:

```text
self-rakl/round019-error-composition-fix
head = a9deecc29ddd91df9c2552d99392d5fc87dc06e0
workflow run = 31316605873
pytest job = 93252773012
conclusion = success
```

The correction was two commits ahead and zero behind the addendum head and modified only `src/rakl/bridge_composition.py` and `tests/test_bridge_composition.py`. It was promoted by non-forced fast-forward after rechecking `main`.

## 7. Executable path contract

A path is `COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY` only when all relevant gates pass:

```text
all local typed witnesses valid
adjacent object identity exact
shared-node roles compatible
question/QoI fixed in v1
at least one declared invariant preserved on every hop
no carried invariant is NOT_PRESERVED
full-path regime intersection non-empty
evidence lineage recorded
matching error semantics declared
predeclared error-composition rule certified
certified accumulated bound within frozen tolerance
```

Otherwise the system distinguishes `NAVIGABLE_ONLY`, `REJECT`, `CANNOT_CHECK`, or `TRIAL_INVALID` rather than collapsing failures.

No path report can mint an endpoint `SimilarityRelation` or grant target authority.

## 8. Main disagreement: should valid local hops compose by default?

The creativity/IR passes favored permissive graph navigation because intermediate concepts can expose remote literatures. The ontology/applied-math/adversarial passes rejected interpreting navigability as scientific transfer.

Resolution:

```text
permissive candidate navigation
+
conservative transfer composition
```

This preserves discovery breadth without allowing a long path to launder weak or changing semantics into authority.

## 9. Semantic novelty after deduplication

### Prior art / not counted as RAKL novelty

- multi-hop graph-constrained scientific synthesis;
- structural-hole bridge discovery;
- compositional analogy benchmarks;
- category-theoretic composition/analogy;
- compositional causal abstraction;
- compositional abstraction error bounds.

### Retained RAKL control objects

1. `NAVIGABLE_VS_COMPOSABLE_BRIDGE_SEPARATION`
2. `INVARIANT_CONTINUITY_CERTIFICATE`
3. `SHARED_NODE_ROLE_HANDOFF`
4. `FULL_PATH_REGIME_INTERSECTION`
5. `CERTIFIED_ERROR_COMPOSITION_SEMANTICS`
6. `NO_ENDPOINT_RELATION_MINTING`
7. `PATH_TARGET_AUTHORITY_BOUNDARY`
8. `CORRELATED_PATH_EVIDENCE_FLAG`

These are useful internal evidence-governance objects; no individual scientific novelty claim is made yet.

## 10. Capability-shaping interpretation

The bridge contract externalizes a weakness of LLM reasoning: local plausibility can be chained into an unsupported global narrative. RAKL uses the model for candidate bridge generation but externalizes path identity, role handoff, invariant continuity, regimes, error semantics, lineage and target validation into explicit contracts.

The support layer itself does not prove that richer scaffolding improves real research. A real matched ablation remains required.

## 11. Saturation verdict

```text
RAKL_METHOD = ACTIVE_NON_FLAT
similarity_generator_lane = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
FRAMEWORK_SATURATION_CERTIFICATE = NOT_ALLOWED
```

Round 019 retained genuinely new executable semantic coordinates and also found/fixed a native same-round residual. This is the opposite of semantic flatness.

## 12. Next discriminators

Highest priority new bridge-specific experiment:

```text
META_N073_REAL_MULTI_HOP_SCIENTIFIC_BRIDGE_BENCHMARK
```

Required experiment:

1. freeze real scientific A→B→C packets with expert-validated useful and false bridges;
2. include near-miss junction identities, changing invariants, incompatible regimes, mixed relation classes and evidence ancestry;
3. compare pairwise-only path validation against the full path certificate under the same model, corpus, evidence and cost budget;
4. score bridge navigation recall separately from composable-transfer precision and target utility;
5. preserve nulls/refutations;
6. keep the simpler pairwise/navigation method if the full contract does not improve real transfer precision or failure localization.

Secondary work: continue `META_N039_PARETO_SCIENTIFIC_JUMP_PORTFOLIO` using path depth/diversity versus grounding/risk/cost, and consider a narrowly scoped future relation-composition registry only for relation classes with formal composition proofs.
