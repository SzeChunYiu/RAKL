# SELF-RAKL Research Round 011 — Similarity Witness Algebra and GLUE/JUMP Separation

Date: 2026-08-09

Starting `main`: `9ad83e15a285e2ee0d09cde51b61a294efdebc12`

Entering global status: `ACTIVE_NON_FLAT`.

## 1. Baseline audit

The run began by checking current `main`, recent commits, open issues and pull requests, Constitution, Round-010 research/receipt, current theory and Apple Principle, research atlas/backlog and current CI evidence.

Observed baseline:

```text
main = 9ad83e15a285e2ee0d09cde51b61a294efdebc12
open issues = 0
open pull requests = 0
Round-010 exact-head test workflow = completed success
Round-010 trusted-parent workflow = skipped, not counted as a passing test
Constitution = unchanged
saturation = ACTIVE_NON_FLAT
```

The priority lane is the newly opened similarity/analogy problem: RAKL must find both additional projections of the same object and structurally useful analogues in distant domains without confusing the two operations.

## 2. Expert panel

Six roles were fixed before synthesis.

1. **Cognitive-science / analogy researcher** — structure mapping, systematicity, retrieval versus recognition and abstraction.
2. **Knowledge-representation / ontology researcher** — typed graphs, relation properties, alignment and compositional edges.
3. **Scientific-information-retrieval researcher** — lexical, embedding, graph, equation and multi-stage retrieval.
4. **Applied mathematics / dynamical-systems researcher** — isomorphism, conjugacy, limits, invariants, regimes and approximation composition.
5. **Computational-creativity / search researcher** — remote association, cross-domain discovery, diversity and non-greedy search portfolios.
6. **Adversarial scientific-method reviewer** — false analogy, broken correspondence, invalid transfer and authority leakage.

These were role-separated sequential passes in the same orchestration context. They are **not** claimed to be mutually blind or independent reviews. The nature-reviewer discipline was used as a reminder to preserve this distinction. The nature-academic-search pattern was used to route across primary literature, current frameworks and deduplicated source traditions rather than relying on one search vocabulary.

## 3. Fresh source projections

### 3.1 Structure mapping and systematicity

Gentner's structure-mapping theory distinguishes analogy from literal similarity by emphasizing mappings of relations rather than object attributes, with systematic connected relational systems preferred over isolated matches. Falkenhainer, Forbus and Gentner's Structure-Mapping Engine operationalizes explicit structural matching. MAC/FAC further separates cheap similarity-based retrieval from expensive structural evaluation and documents the tension that retrieval is often surface-biased even when structural commonality dominates conscious similarity judgment.

**Panel consequence:** RAKL should not ask an embedding to both retrieve and certify an analogy. Retrieval and recognition become separate atomic fibers.

### 3.2 Current evidence that LLMs need explicit cross-domain scaffolding

Larraz and Corma (Nature Communications, 2026) provide a useful controlled case: with identical RAG context, explicit analogical guidance shifted model use toward cross-domain principles and increased successful FCC-class synthesis from 10% to 100% in their experiment. The important projection for RAKL is not the exact effect size as a universal law; it is that *knowledge access and knowledge utilization can be different bottlenecks*.

Shen, Druckmann and Zou (2026) independently show that generating cross-domain analogies based on shared relational structure can increase diversity of scientific solution generation. This reinforces analogy as a search-space expansion mechanism, not evidence that any transferred solution is correct.

### 3.3 Mechanism-centric retrieval and semantic distance

Zhou and Jia's 2026 Mechanism-Centric Cross-Domain Retrieval Framework explicitly decouples topic from mechanism and rewards semantic distance together with mechanistic alignment. This is close prior art to the intuition that useful scientific jumps may be lexically distant but structurally close.

**Novelty consequence:** RAKL must not claim invention of mechanism-centered cross-domain retrieval or semantic-distance-as-serendipity. The differentiating question is how candidate mappings interact with typed atlas relations, negative correspondences, target evidence and authority transitions.

### 3.4 Graph and scientific-agent retrieval

GraphIC (AAAI 2026) shows that reasoning-aware graph representations can outperform text-semantic similarity for retrieving useful multi-step reasoning examples. SciAgents uses ontological knowledge graphs and multi-agent graph reasoning to expose interdisciplinary scientific links. MOOSE-Chem decomposes scientific hypothesis rediscovery into inspiration retrieval, hypothesis generation and hypothesis ranking.

**Panel consequence:** graph/equation/ontology views should be candidate retrieval modules, not hard-coded as the single correct similarity representation.

## 4. Central theoretical result: a similarity claim is a witness

The panel rejected a universal scalar similarity definition.

For a target question `q`, RAKL now treats an atomic object through a multi-layer signature containing entities/roles, relations, causal structure, mechanisms, equations/dynamics, functions, observables, boundary/regime conditions and available interventions.

A relation between objects is represented by an explicit witness:

\[
W_{A\to B}^{\tau,q}=(\phi,P^+,P^-,\Gamma,\Delta,\mathcal E).
\]

The decisive addition is that `P-`, the **known non-preserved structure**, is first-class. A useful analogy should explain not only why two systems match, but exactly where the analogy breaks.

This opens the retained object:

```text
TYPED_SIMILARITY_MAPPING_WITNESS
```

## 5. GLUE and JUMP are different operators

### GLUE

GLUE asks whether local views can alter canonical atlas organization at a specific authority layer. It requires identity, transformation or equivalence evidence and is conservative against false merges.

### JUMP

JUMP searches for structurally useful correspondences across different objects/domains. It is allowed to be adventurous, but its output is a proposal-state object.

The key lifecycle is:

```text
CANDIDATE_BRIDGE
-> WITNESSED_ANALOGY
-> TRANSFER_HYPOTHESIS
-> TARGET_VALIDATED / TARGET_REFUTED / PARTIALLY_IDENTIFIED / CANNOT_CHECK
```

A structurally beautiful analogy without target evidence remains a transfer hypothesis.

This opens:

```text
GLUE_JUMP_AUTHORITY_SEPARATION
ANALOGY_AUTHORITY_LIFECYCLE
```

## 6. Abstraction is lossy and must expose what it erased

The requested L0-L6 abstraction ladder is useful for escaping lexical neighborhoods, but the adversarial reviewer identified a native theoretical risk: domain stripping can remove the exact coordinate that makes an analogy invalid.

RAKL therefore adds an **abstraction erasure ledger**. Every projection toward a more domain-independent schema records removed material/substrate assumptions, units, scales, boundary conditions, causal direction, stochastic structure, conservation laws and intervention semantics.

The abstraction can be used to retrieve distant candidates while remaining insufficient for transfer authority if an erased coordinate is decision-critical.

This opens:

```text
ABSTRACTION_ERASURE_LEDGER
```

## 7. Scientific jumps should not be optimized by one scalar

The initial heuristic `S_deep + alpha * D_surface` is useful but insufficient. It makes the result sensitive to arbitrary weights and can reward meaningless remoteness.

RAKL instead keeps a vector:

\[
J(A,B|q)=
(S_{deep},D_{surface},U_{transfer},E_{readiness},R_{risk},C_{cost}).
\]

Candidate jumps are retained on a Pareto frontier subject to minimum witness constraints. This preserves distinct portfolios:

```text
exploit      nearby + strongly evidenced
 diversify   moderately remote + complementary structure
 moonshot    very remote + strong structural witness + high upside
 meta-RAKL   candidates that improve the search/mapping process itself
```

This opens:

```text
PARETO_SCIENTIFIC_JUMP_FRONTIER
```

## 8. Multi-hop bridge composition is not equivalence closure

The Knowledge Atlas can search through paths such as

\[
A\xrightarrow{\tau_1}B\xrightarrow{\tau_2}C.
\]

But pairwise similarity scores cannot license an `A -> C` transfer. The intermediate role mapping must agree, the relevant invariant must survive every hop, regimes must intersect and approximation/error must accumulate explicitly.

`BRIDGE_TO` is therefore a navigation relation rather than an equivalence class.

This opens:

```text
WITNESSED_MULTI_HOP_BRIDGE_COMPOSITION
```

## 9. Frozen benchmark before implementation

`SELF_RAKL_RESEARCH_011_FROZEN_BENCHMARK.json` was created before any runtime similarity module.

It freezes hostile worlds for:

- coordinate-equivalent GLUE;
- observational equivalence with different mechanisms;
- same-label false entity matches;
- far-domain relational analogy;
- surface false friends;
- equation false friends;
- safe and unsafe abstraction;
- retrieval versus recognition failure localization;
- correct analogy with failed transfer;
- valid and invalid multi-hop composition;
- distance gaming;
- analogy-to-authority leakage.

Primary new meta-QoIs include deep-analogy recall, GLUE precision, witness correctness, erasure completeness, invalid-transfer rate and analogy authority leakage.

No runtime behavior is activated by this benchmark.

## 10. Paper artifact

Two paper-facing artifacts were added:

- `docs/PAPER_SIMILARITY_ANALOGY_SECTION.md`, a manuscript-ready theory module;
- `docs/figures/glue_jump_similarity_plane.svg`, a conceptual schematic explicitly labeled as non-empirical.

The figure separates four regions:

```text
high deep / high surface -> GLUE candidates
high deep / low surface  -> scientific JUMP candidates
low deep / high surface  -> surface false friends
low deep / low surface   -> irrelevant remoteness
```

The figure is explanatory only and must not be presented as measured benchmark data.

## 11. Semantic novelty after deduplication

Retained non-duplicate objects:

1. `TYPED_SIMILARITY_MAPPING_WITNESS`
2. `GLUE_JUMP_AUTHORITY_SEPARATION`
3. `ANALOGY_AUTHORITY_LIFECYCLE`
4. `ABSTRACTION_ERASURE_LEDGER`
5. `PARETO_SCIENTIFIC_JUMP_FRONTIER`
6. `WITNESSED_MULTI_HOP_BRIDGE_COMPOSITION`

Not counted as RAKL novelty:

- analogy and structure mapping;
- systematic relational similarity;
- MAC/FAC coarse-to-fine retrieval;
- graph-based structural retrieval;
- cross-domain analogy for scientific creativity;
- mechanism-centric retrieval;
- semantic distance as a serendipity signal;
- knowledge-graph scientific discovery generally.

Therefore:

```text
RAKL_METHOD = ACTIVE_NON_FLAT
similarity_lane = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

## 12. Next discriminators

Highest-value next work:

1. Implement the smallest **research-only witness data model** against the frozen benchmark, without changing active GLUE behavior unless it improves registered QoIs.
2. Build a retrieval/recognition benchmark corpus where the correct distant source is present but lexically dissimilar, so failure location is objectively measurable.
3. Compare embedding-only, lexical+embedding, graph/reasoning-aware and abstraction-assisted retrieval under the same corpus and budget.
4. Test whether the erasure ledger reduces invalid transfer on hostile same-equation/different-semantics worlds.
5. Construct a paper ablation where removing `P-` (non-preserved correspondences) tests whether LLMs over-transfer analogies.
6. Attack prior art specifically for witnessed analogy lifecycles and typed GLUE/JUMP authority separation before making a novelty claim.

No Constitution or active behavior changed in this round.
