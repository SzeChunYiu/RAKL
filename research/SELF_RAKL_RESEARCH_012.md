# SELF-RAKL Research Round 012 — Distinguishability, Mapping Capacity, and Non-Vacuous Similarity

Date: 2026-08-09

Starting `main`: `e39a7d2a6fe9b3c76f2ea68e1b32cdce9cfa8812`

Entering status: `ACTIVE_NON_FLAT`.

## 1. Baseline audit

This run began by checking current `main`, recent commits, open issues and pull requests, the Constitution, Apple/Knowledge-Atlas principles, Round-011 theory, frozen benchmark, late evidence, validation receipt, source atlas, meta-fiber backlog, test inventory and exact-head workflow state.

Observed baseline:

```text
main = e39a7d2a6fe9b3c76f2ea68e1b32cdce9cfa8812
open issues = 0
open pull requests = 0
Constitution sha = 4d456ceab32122391c830fe8586766cf0e0037aa
latest main test workflow = completed success
latest trusted-parent evaluator = skipped, not counted as a pass
similarity lane = ACTIVE_NON_FLAT
same-context flat rounds = 0
independent flat rounds = 0
```

Round 011 established typed similarity witnesses, GLUE/JUMP separation, abstraction erasure ledgers, Pareto jump portfolios and witnessed multi-hop bridges. The next atomic gap is narrower: **a mapping can look explicit yet still be scientifically vacuous if the mapping family is so expressive that almost anything can be aligned.** Likewise, saying two objects are “equivalent under q” is too weak if RAKL does not represent the family of probes capable of distinguishing them.

## 2. Expert panel and delegated review

Six role-separated sequential passes were fixed before synthesis. They share one orchestration context and are not counted as independent reviewers.

1. **Cognitive-science / analogy expert** — tests whether abstraction and mapping preserve systematic relational structure rather than merely relabeling entities.
2. **Knowledge-representation / ontology expert** — specifies typed mapping contracts, query-family scopes and negative/distinguishing edges.
3. **Scientific-information-retrieval expert** — separates permissive candidate retrieval from restrictive scientific certification.
4. **Applied-mathematics / dynamical-systems expert** — analyzes equivalence under observables, interventions and transition laws; imports bisimulation only where the object is genuinely dynamical.
5. **Computational-creativity / search expert** — asks whether capacity control kills useful remote jumps and how to keep exploratory recall high without weakening certification.
6. **Adversarial scientific-method reviewer** — searches for vacuous alignments, post-hoc map-family expansion, unit violations, direction reversals and benchmark gaming.

Material findings were reviewed by at least two roles. The main disagreement was between the creativity/search role, which prefers expressive mappings for discovery, and the ontology/adversarial roles, which require constrained mappings for authority. The resolution is architectural rather than a compromise score: **retrieval may be expressive; certification must be capacity-controlled.**

## 3. Fresh source routes — deliberately different from Round 011

### 3.1 Causal abstraction as a family of explicit transformations

Geiger et al., *Causal Abstraction: A Theoretical Foundation for Mechanistic Interpretability* (JMLR 26, 2025) generalize causal abstraction from hard/soft intervention replacement to arbitrary mechanism transformations. This is useful prior structure for RAKL because it treats cross-level correspondence as a transformation with intervention semantics rather than lexical resemblance.

RAKL consequence: `TRANSFORMABLE_TO` and causal analogies should expose which interventions/queries commute with the mapping, not merely whether two static descriptions align.

### 3.2 Lossy abstraction needs special semantics

Xia and Bareinboim, *Causal Abstraction Inference under Lossy Representations* (ICML 2025), identify a failure of standard abstraction when several low-level interventions collapse to the same high-level intervention but have different effects. Their projected abstraction construction preserves meaningful observational/interventional/counterfactual query translation under lossy representations.

RAKL consequence: the existing erasure ledger is necessary but insufficient. A lossy map must say **which query families survive the projection**. If different low-level interventions collapse with divergent effects, RAKL must retain a partial/projected relation rather than silently claiming causal equivalence.

### 3.3 Unrestricted alignment can make equivalence vacuous

Sutter et al., *The Non-Linear Representation Dilemma: Is Causal Abstraction Enough for Mechanistic Interpretability?* (2025) show that sufficiently unconstrained nonlinear alignment maps can map arbitrary neural networks to arbitrary algorithms under reasonable assumptions, making the abstraction criterion uninformative without assumptions on representation/alignment complexity.

This is the strongest new adversarial projection for RAKL in this round.

RAKL consequence: an explicit mapping witness is not automatically a strong witness. Every relation type needs a **predeclared admissible mapping family** and complexity/structure constraints. Otherwise RAKL can manufacture deep similarity after seeing the pair.

### 3.4 Bisimulation gives an operational local view of dynamical similarity

Tao, Xu and You, *A Theoretical Analysis of State Similarity Between Markov Decision Processes* (arXiv:2512.17265, 2025), establish a generalized bisimulation metric across arbitrary pairs of MDPs with metric properties. Recent behavioral-metric work similarly treats state similarity through future reward/transition behavior rather than appearance.

Roh, Bae and Choi, *PAMD: Structured Adaptive Distances for Bisimulation Representations in Visual Reinforcement Learning* (arXiv:2607.18004, 2026), make a complementary warning: unconstrained pairwise distances can admit degenerate solutions, motivating expressive but structured metrics.

RAKL consequence: for state-transition objects, similarity can use a bisimulation-like local chart: mapped states should agree in registered observables/QoIs and remain similar under mapped transitions/actions. This is **not** promoted to a universal similarity definition; it is one typed relation family inside the atlas.

### 3.5 Abstraction level is itself an experimental variable

Khojasteh et al., *Enhancing Structural Mapping with LLM-derived Abstractions for Analogical Reasoning in Narratives* (arXiv:2603.29997, 2026), introduce YARN, separating LLM-based decomposition/abstraction from structural mapping and testing multiple abstraction levels. Their error analysis still identifies choosing the right abstraction and handling implicit causality as unresolved challenges.

RAKL consequence: the L0-L6 ladder should not assume “more abstract is better.” The abstraction level and map family become registered experimental coordinates; a deeper abstraction can improve retrieval while degrading causal validity.

Open-source projection: Stanford NLP `pyvene` operationalizes intervention-based analyses and causal-abstraction-style workflows. RAKL treats it as an implementation reference for intervention semantics, not as proof that a scientific mapping is identified.

## 4. Central result A — similarity must be indexed by a probe family

Round 011 conditioned similarity on a question/QoI `q`. Round 012 generalizes this to a family of admissible probes/queries `Q`.

For a relation type `tau`, mapping `phi`, tolerances `epsilon_q`, and context `Gamma`, define local query-family equivalence:

\[
A \sim^{\tau,\phi}_{Q,\epsilon,\Gamma} B
\quad\Longleftrightarrow\quad
\forall q\in Q:\; d_q\big(q(A), q^{\phi}(B)\big)\le \epsilon_q.
\]

`Q` may contain observational queries, interventions, perturbations, trajectory probes, failure tests or other relation-appropriate discriminators. Different relation types license different probe families.

This yields an important monotonicity property. For fixed mapping family, context and tolerances, if

\[
Q_1\subseteq Q_2,
\]

then equivalence under `Q2` implies equivalence under `Q1`, but not conversely. **Adding legitimate probes may split an equivalence class; it does not by itself justify merging previously distinct objects.**

This opens:

```text
QUERY_FAMILY_INDEXED_EQUIVALENCE
SIMILARITY_AS_PARTITION_REFINEMENT
```

The ontology and applied-math roles agree this is safer than treating “similarity” as one permanent label. The adversarial role notes that tolerance changes can break monotonicity, so the property is only licensed under fixed thresholds/map contracts.

## 5. Central result B — non-equivalence deserves a positive certificate

RAKL already stores `P-`, broken correspondences, inside a similarity witness. Round 012 adds a stronger object: an explicit **distinguishing-probe certificate**.

\[
D_{A,B}=(q^*,\phi,\delta,\epsilon,\Gamma,\mathcal E),
\]

where the registered probe `q*` demonstrates a discrepancy `delta > epsilon` under the candidate mapping and context.

This is not merely “the analogy failed.” It records exactly **how to tell the objects apart**.

Examples:

- same observational distribution, different response to an intervention;
- same one-step behavior, different multi-step trajectory law;
- same equation form, incompatible units or boundary conditions;
- same surface role labels, reversed causal direction.

Distinguishing certificates are immutable negative history and should improve future routing: a new candidate relation must either respect the old discriminator or explain why its scope changed.

This opens:

```text
DISTINGUISHING_PROBE_CERTIFICATE
```

## 6. Central result C — mapping witnesses need capacity contracts

The Round-011 witness

\[
W=(\phi,P^+,P^-,\Gamma,\Delta,\mathcal E)
\]

is strengthened to carry an admissibility contract

\[
\Lambda^\tau=(\Phi^\tau,K,\mathcal C,N),
\]

where:

- `Phi^tau` is the mapping family allowed for relation type `tau`;
- `K` is a complexity/capacity budget or structural prior;
- `C` contains hard constraints such as types, units, causal roles, topology, monotonicity, sparsity or intervention compatibility when relevant;
- `N` is a null-calibration plan, such as structure-shuffled or role-shuffled controls.

The family must be frozen **before fitting the candidate pair**. Post-hoc widening of `Phi` to rescue a preferred analogy is a benchmark failure.

This creates a two-authority architecture:

```text
DISCOVERY MAP
  may be expressive, approximate and high-recall
  -> proposes candidate bridge

CERTIFICATION MAP
  relation-specific, predeclared, constrained and falsifiable
  -> may support a witnessed relation
```

This resolves the panel disagreement. RAKL does not suppress imagination; it prevents imaginative alignment capacity from laundering itself into evidence.

This opens:

```text
ADMISSIBLE_MAPPING_CAPACITY_CONTROL
DISCOVERY_CERTIFICATION_MAP_SEPARATION
```

## 7. Dynamical similarity is future-behavioral, not snapshot similarity

For objects with genuine state-transition semantics, define a specialized dynamical relation. At minimum, mapped states must agree on registered immediate observables/QoIs and their mapped successor distributions must remain similar under the registered action/intervention family.

Conceptually:

\[
d(s,t)\approx d_O(O(s),O(t)) + \gamma\,D\big(T(\cdot|s),T^{\phi}(\cdot|t)\big).
\]

The exact metric is domain-specific and replaceable. The retained principle is that **same snapshot is not same dynamics** and one-step equivalence does not automatically imply trajectory equivalence.

This opens:

```text
DYNAMICAL_BEHAVIORAL_REFINEMENT_VIEW
```

The adversarial reviewer rejects making bisimulation a universal RAKL relation: it depends on a transition/action semantics that many scientific objects do not possess. It therefore remains a local view in the Knowledge Atlas.

## 8. Active discrimination becomes part of similarity research

Once RAKL has candidate mappings `M={m1,...,mk}`, the next search/experiment can be chosen to maximize expected refinement of the candidate partition rather than merely to accumulate more descriptions.

A probe is valuable when it separates mappings that are currently observationally indistinguishable. This connects similarity directly to RAKL's existing discriminator principle:

```text
candidate mappings
-> identify shared equivalence class under current probes
-> choose cheapest high-information distinguishing probe
-> execute/search
-> split or retain class
-> preserve the discriminator result
```

No new generic information-gain scalar is activated. Exact utility depends on domain and available probabilities; set-valued mechanism separation remains valid when probabilities are not justified.

## 9. Frozen Round-012 benchmark

`research/SELF_RAKL_RESEARCH_012_FROZEN_BENCHMARK.json` was frozen before any Round-012 runtime implementation. It adds hostile worlds for:

- observational equivalence but interventional difference;
- nested probe-family refinement;
- arbitrary nonlinear mapping vacuity;
- unit-violating alignments;
- structure-shuffled nulls;
- lossy intervention collapse;
- same snapshot but divergent dynamics;
- one-step agreement with multi-step divergence;
- causal-direction false friends;
- immutable distinguishing certificates.

Registered new meta-QoIs include vacuous-mapping acceptance, distinguishing-probe recall, refinement correctness, dynamic false merges and mapping-constraint violations.

No active similarity behavior changed in this round.

## 10. Semantic novelty after deduplication

Retained Round-012 objects:

1. `QUERY_FAMILY_INDEXED_EQUIVALENCE`
2. `SIMILARITY_AS_PARTITION_REFINEMENT`
3. `DISTINGUISHING_PROBE_CERTIFICATE`
4. `ADMISSIBLE_MAPPING_CAPACITY_CONTROL`
5. `DISCOVERY_CERTIFICATION_MAP_SEPARATION`
6. `DYNAMICAL_BEHAVIORAL_REFINEMENT_VIEW`

Not counted as RAKL novelty:

- causal abstraction;
- projected/lossy causal abstraction;
- bisimulation and bisimulation metrics;
- structured/adaptive behavioral metrics;
- abstraction-assisted structural mapping;
- intervention libraries;
- the general warning that unrestricted representation mappings can be vacuous.

The RAKL candidate contribution is narrower: integrating relation-specific admissible mapping contracts and explicit distinguishing-probe history into the evidence-governed GLUE/JUMP atlas, while keeping discovery mappings more expressive than certification mappings.

Saturation remains:

```text
RAKL_METHOD = ACTIVE_NON_FLAT
similarity_lane = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

The round is non-flat because six non-duplicate objects survive the Round-011 ontology and create new executable falsifiers.

## 11. Next discriminators

Highest-value next work:

1. Implement a **research-only witness schema** containing `relation_type`, `probe_family`, `mapping_family`, hard mapping constraints, preserved/broken correspondences and distinguishing certificates.
2. Execute Round-011 and Round-012 frozen worlds against the schema validator before any active GLUE/JUMP integration.
3. Build a small benchmark comparing unrestricted LLM-generated mappings versus predeclared constrained mapping families on shuffled/null and unit/causal-role false friends.
4. Add a retrieval-vs-certification ablation: allow the same expressive retriever in both arms, but constrain only the certification witness.
5. For dynamical worlds, compare snapshot/equation similarity against transition-aware behavioral refinement.
6. Add paper language explaining that **similarity is what survives a declared family of attempts to distinguish two objects under an admissible map**, not an intrinsic scalar property.
7. Search prior art specifically for query-family-indexed scientific equivalence plus explicit negative/distinguishing certificates before making a novelty claim.

No Constitution, source module, workflow, evaluator, promotion gate, test, or active similarity behavior was changed in this round.
