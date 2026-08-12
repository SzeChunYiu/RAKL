# RAKL training-time extension: cross-paper research synthesis

**Date:** 2026-08-12  
**Issues:** #455, #456, #457  
**Status:** research synthesis / claim-boundary update. No training-efficacy result is claimed.  
**Publication default:** Paper III primary; do not create a sixth paper unless the mechanism survives the pilot and leaves substantial residual novelty.

## Executive decision

The extension is worth pursuing, but its defensible novelty is **narrower than “learner-conditioned data selection” or “saturation-aware curriculum learning.”** Those functions are substantially occupied by recent work.

The strongest residual RAKL hypothesis is:

> Existing RAKL Paper III already represents transfer through directional, QoI-/boundary-scoped relational `StructuralObject` / `StructuralWitness` objects. Existing external work already performs semantic deduplication, skill-graph selection, online/model-aware data selection, missing-skill targeting, influence-based selection, and dynamic curricula. The proposed extension adds a **learner-specific vector mastery state over the same directional structural substrate**, distinguishing principle acquisition from composition, boundary, representation and cross-domain transfer mastery, and uses that state to reallocate gradient budget while preserving a nonzero repetition/robustness floor. The extension is falsified as a distinct contribution if adaptive RAKL does not beat static RAKL structural curation on fresh structural-OOD cost-to-capability, or if a strongest fair parent explains the same gain without the RAKL structural/boundary/shared-substrate residual.

The immediate paper action is therefore **claim-boundary revision in Paper III**, not a new empirical result claim. Papers I, II and V should receive at most scoped conceptual discussion after the empirical object survives Phase 0/1. Paper IV should not change now.

---

# 1. Internal RAKL mapping

| New concept | Existing RAKL parent | Current surface | New extension needed | Conflict risk |
|---|---|---|---|---|
| Learner-conditioned saturation | Paper I vector saturation | `paper-01.../02b_v3_epistemic_projection.tex` | Separate **training/learner projection**; do not overload epistemic saturation | High if model mastery is conflated with scientific authority |
| Bounded gradient allocation | Paper I workspace + Paper II bounded cognition | `03_workspace.tex`; Paper II `09_bounded_cognition.tex` | Training allocator with mandatory coverage/repetition constraints | Medium; training utility is not workspace utility |
| Structural learning unit | Paper III `StructuralObject` | `src/rakl/structural_types.py`; Paper III §2 | Training annotation/view over existing structure IDs | Low if raw examples remain canonical and structure is derived |
| Directional transfer mastery | Paper III `StructuralWitness` | Paper III §2, transfer gate | Learner-state estimate of whether witnessed relation transfers after weight updates | Medium; witness licenses applicability, not mastery |
| Static structural redundancy | Paper III Training Efficiency + Redundancy hypotheses | Paper III §4–5 | Already present; not new | None; historical parent |
| Adaptive structural curriculum | Paper III training arm | Paper III §5 | Add model-state-dependent structural mastery and `Adaptive - Static RAKL` estimand | High novelty threat from STAT/MATES/etc. |
| Reallocation after flat returns | Paper V saturation / portfolio policy | Paper V §11 | Weight-training analogue with separate scheduler | Medium; Paper V is framework evolution, not weight training |
| Failure -> better allocation policy | Paper V failure ladder + Self-RAKL; #433/#434 search feedback | Paper V §4; `search_policy_learning.py`; `epistemic_evolution.py` | Training-specific diagnosis/counterfactual/policy receipt chain | Low if reused as governance pattern, not same policy object |
| Shared train/inference substrate | Paper III Shared Substrate hypothesis | Paper III §4 | Exact structural ID/role/relation/boundary reuse test | High; ReX/structural-learning work narrows novelty |
| Full cost accounting | Paper III amortization | `src/rakl/amortization.py`; Paper III §4 | Add structure extraction, mastery probes, scheduling overhead, GPU/wall-time | Low |
| Search-engine integration | #433 Epistemic Search Engine | `epistemic_search.py` | Share structural indexes; separate `TrainingAllocator` from search ranker | High if search rank is reused as training authority/utility |

## 1.1 Three projections must remain separate

A useful extension of the v3 state picture is:

```text
canonical/raw corpus + scientific state + experience state
                |
                +--> epistemic projection       : what is scientifically licensed?
                +--> search/routing projection  : what should be inspected next?
                +--> training projection        : what should receive gradient budget next?
```

The three projections may share identities and lineage, but they must not share authority semantics.

Let the complete state be `R_t`, scientific authority projection `K_t = pi_epi(R_t)`, search state `Q_t = pi_search(R_t)`, and a proposed training state

`L_t = pi_train(R_t, theta_t)`.

`L_t` is explicitly learner-dependent because `theta_t` matters. A later model state may invalidate a previous saturation decision without changing any scientific claim in `K_t`.

Hard invariant:

```text
training utility != search rank != scientific authority
```

A high-value training example may be scientifically weak; a highly authoritative source may be redundant for a learner; a centrally cited source may be useful for search but add almost no independent structural exposure.

---

# 2. Strongest prior-art matrix

Threat level is to the **proposed residual claim**, not to RAKL generally.

| Parent | Year | Core function | Learner-state dependent? | Structural/compositional? | Main novelty threat to RAKL | Threat |
|---|---:|---|---|---|---|---|
| Skill-It | 2023 | learned skill dependencies + online skill sampling | Yes, sequential/adaptive | Skill dependency graph | occupies ordered skills and adaptive allocation | **Critical** |
| MASS | 2025 | mathematical skill graph data selection | Mostly static selection | Skill graph | occupies static graph-aware structural-ish curation | **Critical** |
| MATES | 2024 | model-aware influence model updated from local probes | Yes | Relationships only indirectly | occupies evolving model-state-aware pretraining selection | **Critical** |
| Group-MATES | 2025 | relational/group influence selection over trajectories | Yes | relational data influence / clusters | threatens any “relation-aware + model-aware selection” wording | **Critical** |
| STAT | 2026 | missing-skill profile; adaptive selection/synthesis after saturation | Yes, explicitly | Skill labels/combinations | closest threat to “learner-conditioned saturation” | **Critical** |
| ADO | 2025 | online data-distribution optimization during training | Yes | domain/group level | occupies online adaptive allocation | High |
| Aioli | 2025 | online data-mixture parameter estimation | Yes | group/domain level | occupies dynamic mixture learning | High |
| Spaced Scheduled Training (Sst) | 2025 | model-informed adaptive example selection from evolving perplexity | Yes | no explicit RAKL structure | occupies learner-specific dynamic selection | High |
| Rho-1 | 2024 | selective token loss via excess/reference loss | Model/reference dependent | token-level, not structural | strong utility proxy and efficiency baseline | High |
| D4 | 2023 | document dedup + diversification; intelligent repetition | No learner-specific state | embedding/document | refutes “repetition is waste” simplification | High |
| SemDeDup | 2023 | semantic deduplication | No | semantic | baseline for surface/semantic redundancy | Medium |
| LESS | 2024 | optimizer-aware gradient similarity/influence for targeted tuning | Target-model/gradient aware | capability examples, not explicit boundaries | threatens marginal-utility proxy claims | High |
| PDS / optimal-control data selection | 2025 | selection tied to training dynamics via PMP | Yes in formulation | no RAKL structural object | theoretical parent for allocation control | High |
| Quad / influence + diversity | 2025 | influential and diverse pretraining selection | Model/influence dependent | cluster relations | shows influence must be coupled with coverage/diversity | Medium–High |
| Online reweighting vs offline curation | 2026 | online reweighting for changing model/data | Yes | group/sample level | reinforces that adaptivity itself is occupied | High |
| Evolved Sampling | 2025/26 | dynamic selection from loss dynamics | Yes | no explicit relational structure | dynamic training-efficiency baseline | Medium–High |
| STEPS | 2026 | skill-taxonomy guided compositional data synthesis | Partly, via target needs | Explicit skill composition | major threat to “composition-aware curriculum” novelty | **Critical for composition** |
| Learning Composable CoT | 2025/26 | training atomic skills in composable formats | No online mastery state | Explicit compositional structure | shows composition requires representation/training-format treatment | High |
| Power-law compositional curriculum | 2026 | distribution shape can improve compositional reasoning | Distribution-level | Explicit skill composition | warns against naive uniform reallocation after saturation | High |
| Shortest-path generalization study | 2026 | controlled separation of data coverage / length scaling / training effects | Diagnostic | Composable sequential structure | informs controlled generator and capability limits | Medium |
| Chen et al., structural information in LMs | 2026 | emergence and test-time use of abstract structure | Learner representation measured | Explicit structure | threatens broad train/inference structural-unification claim | **Critical for shared substrate** |
| ReX | 2026 | reusable latent experiences + dynamic composition into adapters | Input-conditioned | latent skills/composition | threatens “same reusable experience across weight adaptation” framing | High |
| SkillGraph | 2026 | dependency-aware graph retrieval for agent skills | inference-time | explicit dependency graph | threatens general structural skill retrieval novelty | Medium |
| GraSP | 2026 | executable DAG skill composition with dependencies and repair | inference-time | explicit causal skill graph | threatens generic “structured composition” novelty | High |
| DoReMi | 2023 | proxy-based domain reweighting via excess loss / group DRO | proxy-adaptive, then static large run | domain groups | data-mixture efficiency baseline | Medium |
| Cognitive spacing / retrieval-practice experiments | 2010–2020+ | spacing, retrieval, variable practice improve retention/transfer | learner/performance dependent | not LLM structural formalism | defeats zero-repetition/mastery simplification | High conceptual guardrail |

## 2.1 The most dangerous parent: STAT

STAT is the strongest direct novelty threat because it already uses a learner-specific Missing-Skill-Profile, observes saturation under vanilla SFT, and adaptively selects or synthesizes examples targeting missing skills.

Therefore RAKL must **not** claim:

- first learner-conditioned curriculum;
- first missing-skill targeting;
- first saturation-aware adaptive training;
- first model-state-specific example allocation.

The residual difference must be executable and empirical:

1. RAKL's unit is a directional relational structure, not a free skill label.
2. It is QoI- and boundary-scoped.
3. It explicitly records non-preserved properties and hostile near-misses.
4. Mastery is vector-valued across principle/composition/boundary/representation/transfer.
5. The **same structural identity** is tested at inference in a witnessed transfer gate.
6. The adaptive mechanism must beat **static RAKL**, not just random/full-data training.

## 2.2 Important anti-novelty result: MATES / Group-MATES

MATES directly studies evolving data preferences during pretraining and continuously updates a model-aware data-influence model. Group-MATES adds relational/group influence. This blocks any novelty wording that equates RAKL's contribution with “the model's current state changes which data are useful.”

RAKL must show that *which structural coordinate remains unsaturated* predicts transferable gain beyond strong influence/model-aware selection.

## 2.3 Important guardrail: D4 and repetition literature

D4 reports that intelligent repetition can outperform random one-pass exposure. Controlled transformer work also reports benefits from repeated examples. Human-learning experiments show repeated retrieval, varied examples and spacing can improve retention/transfer.

So RAKL should not model saturation as:

```text
mastered structure -> never show it again
```

The safer mechanism is:

```text
mastered principle coordinate
-> reduce equivalent exposure weight
-> preserve minimum repetition / forgetting / robustness floor
-> preferentially allocate extra budget to novel composition/boundary/representation/transfer coordinates
```

This is a resource-allocation policy, not destructive deduplication.

---

# 3. Revised formal object

## 3.1 Do not start with `Epistemic Marginal Utility`

The phrase is attractive but risky inside RAKL because “epistemic” already denotes scientific-authority/evidence mechanics. A training example can have high learning utility without high scientific authority.

Provisional safer term:

**Structural Training Marginal Utility (STMU)**.

Do not standardize the term until the pilot supports the object.

## 3.2 Structural mastery must be vector-valued

For registered structural object `s`, define a provisional learner-conditioned state:

```text
M_t(s) = (
    m_principle,
    m_composition,
    m_boundary,
    m_representation,
    m_transfer,
    m_retention
)
```

where each coordinate is estimated by a **frozen probe family**, not introspection alone.

Interpretation:

- `m_principle`: base relational rule / invariant acquisition;
- `m_composition`: use of the structure in registered multi-structure compositions;
- `m_boundary`: correct behavior under boundary/regime changes and semantic near-misses;
- `m_representation`: invariance across notation/modality/surface encoding;
- `m_transfer`: structure-known/domain-new performance;
- `m_retention`: resistance to forgetting after training moves elsewhere.

A scalar mastery score is permitted only as a derived reporting summary. It must not erase a low coordinate.

Key nonimplication:

```text
mastered(A) + mastered(B) != mastered(A+B)
```

and:

```text
high in-domain principle accuracy != cross-domain transfer mastery
```

## 3.3 Learner-conditioned structural redundancy

For example `x` mapped to structural object(s) `s(x)`, learner-conditioned redundancy should be defined relative to the current state:

```text
R_t(x | theta_t, M_t)
```

not as a static pairwise property.

The same example may be high-value at `t0` and low-value at `t1`; a new boundary/composition of an otherwise mastered principle may become high-value again.

## 3.4 Structural Training Marginal Utility

Do not assume one scalar is observable. First define a vector of prospective effects:

```text
DeltaQ_t(x) = (
    delta_principle_transfer,
    delta_composition,
    delta_boundary,
    delta_representation,
    delta_cross_domain,
    delta_retention,
    -delta_negative_transfer
)
```

and a full cost vector:

```text
C_t(x) = (
    extraction_cost,
    annotation_or_generation_cost,
    mastery_probe_cost,
    selection_cost,
    forward_backward_FLOPs,
    wall_time,
    memory_cost,
    verification_cost
)
```

Only later test whether a useful scalar utility can be preregistered.

Potential empirical proxies, ordered from strongest/most expensive to cheaper/weaker:

1. actual held-out transfer-probe change after controlled micro-updates;
2. validation-gradient / probe-gradient alignment;
3. influence estimates such as MATES/LESS-style local probes;
4. change in structural probe representations;
5. loss/perplexity/surprise;
6. raw gradient norm.

Loss alone should be a baseline, not the RAKL mastery definition.

## 3.5 Saturation is a scoped, stale-able receipt

A future `TrainingSaturationReceipt` should bind at least:

- exact model/weights hash or checkpoint identity;
- optimizer state identity;
- structure ID and relevant composition/boundary/representation/transfer coordinates;
- frozen probe-suite hash;
- exposure history / diversity history;
- current mastery vector with uncertainty;
- marginal-gain estimate with uncertainty;
- minimum repetition / retention floor;
- forgetting-risk state;
- chronology (`frozen_before_allocation_change`);
- expiry/staleness rule after enough parameter updates.

The receipt must be invalidated or refreshed when `theta_t` moves materially. It never grants scientific authority.

---

# 4. Failure-driven adaptive training: connect to Self-RAKL, do not invent random curricula

The most important architecture connection is the same one now being added to search-policy learning:

```text
failure_t
-> typed diagnosis_t
-> bounded intervention/policy challenger_(t+1)
-> fresh assurance
```

For training, a flat or failed transfer result must **not** directly trigger a new sampling heuristic.

## 4.1 Required failure taxonomy

At minimum distinguish:

- `SAME_STRUCTURE_SATURATED`
- `COMPOSITION_GAP`
- `BOUNDARY_GAP`
- `REPRESENTATION_GAP`
- `TRANSFER_DOMAIN_GAP`
- `RETENTION_FORGETTING_GAP`
- `MODEL_OPTIMIZATION_FLOOR`
- `STRUCTURE_EXTRACTION_DEFECT`
- `PROBE_INSTRUMENT_DEFECT`
- `DATA_QUALITY_DEFECT`
- `INSUFFICIENT_POWER`

These diagnoses imply different interventions. A composition failure should not simply increase more isolated-principle examples.

## 4.2 Counterfactual repair before policy promotion

Mirror the search root-cause contract:

1. freeze a failed structural/probe case;
2. hold model, optimizer, candidate pool and compute envelope fixed;
3. alter exactly one registered allocation mechanism;
4. require the matched intervention to move the registered failure QoI in development;
5. issue a root-cause/allocation certificate;
6. build a challenger scheduler;
7. test on disjoint fresh structures/compositions;
8. promote/reject/narrow through Self-RAKL tournament governance.

This prevents:

```text
bad batch -> new clever curriculum -> same benchmark retest -> victory
```

## 4.3 Training-policy evolution is not scientific-authority evolution

Even if a scheduler learns that a source family produces high transfer gain, that does not increase the scientific authority of the source claims.

Likewise, source authority may be a **minimum data-quality constraint**, but should not be multiplied into a generic training-utility score without an explicit policy.

---

# 5. Connection to the Epistemic Search Engine / “Google for science”

The search-engine analogy extends usefully to training if we preserve distinct decision layers.

## 5.1 Shared infrastructure

Reusable across search and training:

- raw corpus preservation;
- canonical content IDs;
- structural IDs / roles / relations / invariants / boundaries;
- lexical / semantic / structural indexes;
- citation/derivation lineage;
- duplicate/root-echo detection;
- negative-result/failure indexes;
- freshness/supersession metadata;
- bounded candidate materialization.

## 5.2 Different controllers

```text
EpistemicRanker:
    which source/candidate should research inspect next?

TrainingAllocator:
    which registered example/structural coordinate should receive gradient budget next?

ScientificAuthorityProjection:
    what claim/authority transition is licensed by evidence?
```

Do not reuse `graph_centrality`, popularity, retrieval frequency or training frequency as authority.

## 5.3 Training analogue of anti-epistemic-spam

The new search layer's anti-echo rules suggest a training-specific exposure audit:

- canonical duplicates do not count as independent exposures;
- same evidence-root repetitions are not diversity;
- many surface variants of one structure do not count as structural coverage;
- generated paraphrases should be grouped by structural/lineage identity;
- benchmark-target leakage is forbidden;
- repeated examples may remain intentionally scheduled for retention but are labeled as repeated exposure, not new structure.

---

# 6. Cheapest falsifiable experiment

## Phase 0 — known-world structural generator

Do **not** start with a large model or natural scientific literature.

Build a generator with exact latent ground truth over independent factors:

- principle `P`;
- composition graph `C`;
- boundary/regime `B`;
- representation `R`;
- transfer/domain shell `T`;
- surface/numeric variation `V`.

Recommended first families:

1. small algebra/rule systems;
2. graph flow / matching / shortest-path constraints;
3. unit/coordinate transformations;
4. finite-state/semiautomata compositions;
5. simple conservation/balance systems.

Gold structure must be assigned by the generator/verifier, not an LLM judge.

### Generator validity checks

- surface wording cannot leak structure label;
- valid/invalid cases share templates where possible;
- structure label is computed from executable relation, not perturbation name;
- coordinate-ablated twins test whether the classifier merely reads generator artifacts;
- task partitions are chronology-bound before learner outcomes.

## Phase 1 — structural exposure curves

For each structural family, train with controlled exposure count `n`:

```text
1, 2, 4, 8, 16, 32, 64, ...
```

At each checkpoint measure six mastery coordinates.

Then compare the marginal value of the next equal-cost example when it is:

- another same-structure/surface-varied example;
- a new representation;
- a new boundary;
- a new domain shell;
- a new composition;
- a hostile semantic near-miss.

The central mechanism is supported only if the **relative** value of equivalent repetition falls after principle mastery while unsaturated coordinates remain valuable.

Do not require monotonic decline. Composition or boundary changes may produce gain spikes.

## Phase 2 — matched allocation arms

At equal total compute:

- **A — Uniform/random**
- **B — Semantic diversity/dedup** (D4/SemDeDup-style)
- **C — Strong adaptive parent** (STAT or MATES depending task representation; Skill-It/MASS where faithful)
- **D — Static RAKL structural curation**
- **E — Adaptive RAKL structural mastery scheduler**
- optional **F — loss/perplexity-only adaptive scheduler**
- optional **G — influence-only scheduler**

### Primary estimand

```text
E - D
```

This is the only contrast that establishes the **learner-conditioned extension beyond existing Paper III**.

### Parent-residual estimands

```text
E - C
E - F
E - G
```

These identify whether RAKL adds anything beyond missing-skill, loss-based or influence-based selection.

## Phase 3 — composition/boundary test

Train on atomic structures and selected compositions. Hold out:

- novel pair compositions;
- novel deeper compositions;
- boundary flips;
- representation changes;
- domain-new shells;
- semantic-near / structure-wrong decoys.

A scheduler that saves tokens but harms composition or boundary robustness fails the strong claim.

## Phase 4 — retention / repetition floor

After an apparent saturation point, redirect most budget away from the structure but vary a minimum repetition schedule.

Compare:

- zero revisits;
- low floor;
- spaced floor;
- mixed/varied revisit;
- uniform continued repetition.

Measure forgetting, calibration and transfer.

This is required by both D4-style results and learning-science evidence.

## Phase 5 — shared substrate

Freeze the trained model. Reuse the exact registered structure IDs/roles/relations/invariants/boundaries in Paper III inference-time retrieval/witnessing.

Strong unification requires:

```text
same structural identity family used for training allocation
AND
same identity family used for inference transfer
```

If a separate latent skill representation is required, report two mechanisms.

---

# 7. Measurement and inference

## 7.1 Primary endpoint

**Cost to frozen structural-OOD capability target**.

Report:

- tokens-to-target;
- examples-to-target;
- FLOPs-to-target;
- GPU-hours-to-target;
- wall-clock-to-target;
- total preprocessing/selection/probe cost.

A run that trains on fewer tokens but consumes more total compute after structural extraction/probing is not an efficiency win.

## 7.2 Secondary endpoints

- novel-composition accuracy;
- boundary/regime robustness;
- semantic-decoy rejection;
- representation invariance;
- cross-domain transfer;
- calibration;
- forgetting/retention;
- variance across seeds;
- training stability.

## 7.3 Inference states

Use typed result states rather than sign-only claims:

- `DISTINGUISHABLE_BENEFIT`
- `DISTINGUISHABLE_HARM`
- `MEASURED_BUT_INDISTINGUISHABLE`
- `UNDERPOWERED`
- `CANNOT_IDENTIFY`
- `INVALID_CONTAMINATED`

Predeclare MDE / precision target and stop rules before confirmatory access.

---

# 8. What the literature changes in the proposed mechanism

## 8.1 Replace “mastered -> remove” with “mastered coordinate -> reallocate marginal budget”

Repetition may still support robustness, retention, invariant representations and optimization stability. Therefore the scheduler should reduce **marginal allocation**, not assert zero utility.

## 8.2 Replace one saturation scalar with a mastery vector

STAT already owns missing-skill profiles. RAKL's residual strength is the finer directional structural decomposition: a principle can be mastered while a boundary, composition or transfer coordinate remains unsaturated.

## 8.3 Add influence/model-aware parents directly, not only skill graphs

Paper III's current baseline set should be updated to include at least one model-aware parent (MATES/Group-MATES or a faithful equivalent) and one explicit learner-saturation/missing-skill parent (STAT) in addition to Skill-It/MASS.

## 8.4 Do not assume uniformization is good

Recent compositional work indicates distribution asymmetry can aid learning. Reallocation should therefore optimize a measured cost/capability objective under coverage/retention constraints; it should not aim to equalize exposure counts across structures.

## 8.5 Treat composition representation as a mechanism, not only a data label

Composable-CoT and related work show that examples of atomic skills do not automatically teach composition. The RAKL generator/evaluator must represent compositions explicitly and measure whether the scheduler selects examples whose **relational interfaces** are missing, not simply high-loss atomic tasks.

---

# 9. Cross-paper revision memo

## Paper I — Epistemic Mechanics

**Action now:** no canonical efficacy change. Keep publication scope stable.

**Potential later discussion-only addition after Phase 0/1:** introduce a separate learner/training projection as an example of why computational/model state and scientific authority must remain separate.

Safe future statement:

> The same canonical substrate may admit a learner-conditioned training projection whose priorities depend on model parameters; changes in that projection alter gradient allocation but do not by themselves change scientific authority.

Do **not** make training efficiency part of Paper I's contribution.

## Paper II — Whole-framework architecture

**Action now:** no main architectural claim change; record the optional extension in roadmap/research material.

**Potential later theory extension:**

```text
external-state RAKL: theta_(t+1) = theta_t
training-time extension: theta_(t+1) != theta_t
```

Both can share canonical structural IDs and authority boundaries, but the weight-updating path needs separate training-state, checkpoint and optimizer provenance.

Do not imply that current v3 continual learning already changes weights.

## Paper III — primary owner

**Action now:** revise nearest-work and hypothesis wording under #456.

Required changes:

1. explicitly concede novelty for generic adaptive/model-aware/saturation/skill-based selection;
2. add STAT, MATES/Group-MATES, ADO/Sst/Rho-1 and relevant compositional parents;
3. rename the extension claim to learner-conditioned **directional structural mastery/saturation**;
4. make `Adaptive RAKL - Static RAKL` the critical new estimand;
5. add repetition/retention floor and composition/boundary guardrails;
6. distinguish extension hypothesis from current evidence;
7. require exact shared-substrate identity at inference.

Suggested revised hypothesis:

> **Learner-conditioned structural allocation.** In a training distribution with surface-diverse structural redundancy, an adaptive scheduler conditioned on a frozen learner-specific mastery vector over registered relational structures reaches a preregistered structural-OOD capability target at lower total cost than static RAKL structural curation and the strongest faithful model-aware/skill-aware parent, while meeting registered composition, boundary, retention and negative-transfer constraints.

This is falsified if adaptive RAKL fails to beat static RAKL distinguishably, or if any gain is fully explained by a simpler parent mechanism.

## Paper IV — Verified Discovery

**Action now:** no change.

Only revisit if a direct mathematical-training experiment demonstrates that the scheduler changes verified mathematical-research capability. Conceptual analogy to avoiding repeated rediscovery is insufficient.

## Paper V — Experience-governed evolution

**Action now:** discussion/roadmap only after the pilot; do not present weight training as existing Self-RAKL behavior.

Strong conceptual bridge:

```text
flat return / failure
-> typed diagnosis
-> bounded resource-allocation challenger
-> fresh assurance
-> promote / reject / narrow
```

This is the same governance law across search policy, framework evolution and future training allocation, while the state being changed differs.

Potential Paper V message if supported:

> Self-RAKL can evolve not only research/search policies but also a separately governed training-allocation policy, with fresh assurance preventing repeated development-set tuning from becoming canonical method evolution.

---

# 10. Framework implementation plan

Do not modify `StructuralObject` destructively.

Add derived/proposal-only training surfaces first:

## `TrainingStructuralAnnotation`

Binds:

- raw example ID;
- one or more structural object IDs;
- composition/interface IDs;
- boundary variant IDs;
- representation family;
- domain shell;
- extraction method/evidence;
- chronology and uncertainty.

## `StructuralMasteryState`

Checkpoint-bound six-coordinate state with probe identities and uncertainty.

## `TrainingSaturationReceipt`

Content-bound checkpoint + structure + probe + exposure + uncertainty + repetition-floor receipt. Grants no scientific authority.

## `TrainingAllocationPolicy`

Versioned policy controlling candidate/materialization/repetition budget. Separate from `SearchPolicy`.

## `TrainingFailureDiagnosis`

Typed cause of flat/harmful learning result. Must distinguish model floor and instrument defect from true structural saturation.

## `TrainingPolicyUpdateProposal`

Allow-listed, diagnosis-bound challenger. No arbitrary caller deltas.

## `TrainingTournamentAssessment`

Reuses #434 Self-RAKL governance semantics: disjoint fresh assurance, typed inference, strongest parent control, resource-only gain rejection, hard-regression rejection, and promotion eligibility only.

### Noninterference requirement

All training surfaces must expose:

```text
grants_scientific_authority == False
```

Training may change `theta`; it does not rewrite evidence roots or claim authority.

---

# 11. Publication decision rule

Default decision today:

**Cross-paper extension, Paper III primary.**

Do not create Paper VI now.

A separate paper becomes justified only if the experiments establish a distinct empirical/theoretical object beyond Paper III's existing structural-curation programme, for example:

1. reproducible learner-conditioned structural exposure curves with a nontrivial law;
2. a mastery estimator that predicts future transfer gain substantially beyond loss/influence/missing-skill parents;
3. adaptive RAKL > static RAKL and > strongest parent on fresh held-out structures;
4. shared train/inference structural identities provide measurable benefit;
5. a general theorem or robust empirical law linking structural exposure, mastery coordinates and transfer/cost.

If only the scheduler works as a stronger implementation of Paper III's static hypothesis, absorb it into Paper III.

If the scheduler does not beat static RAKL, learner-conditioned saturation is **unsupported as an added mechanism** and should not be spun into a sixth paper.

---

# 12. Immediate next steps

1. **#456:** revise Paper III nearest-work / training hypothesis wording now; no efficacy claims.
2. Freeze a 20–40 parent claim matrix as a machine-readable artifact under #455.
3. Implement Phase-0 generator and exact structural labels/verifiers.
4. Freeze mastery probes before adaptive scheduler results.
5. Run exposure curves first; do not implement a complex scheduler until the curve shows a measurable state-dependent residual.
6. If Phase 1 is positive, implement the smallest `TrainingAllocationPolicy` with one diagnosis-driven update family.
7. Compare static vs adaptive RAKL before scaling models.
8. Only after the mechanism survives, consider scoped conceptual edits to Papers I/II/V.

---

# 13. Primary-source prior-art reading list used for this synthesis

The following are nearest or mechanism-defining parents and should be captured in the structured novelty matrix before publication claims:

- Chen et al., **Skill-It! A Data-Driven Skills Framework for Understanding and Training Language Models**, NeurIPS 2023, arXiv:2307.14430.
- Xie et al., **DoReMi: Optimizing Data Mixtures Speeds Up Language Model Pretraining**, 2023, arXiv:2305.10429.
- Tirumala et al., **D4: Improving LLM Pretraining via Document De-Duplication and Diversification**, NeurIPS 2023, arXiv:2308.12284.
- Abbas et al., **SemDeDup: Data-efficient learning at web-scale through semantic deduplication**, 2023.
- Lin et al., **Rho-1: Not All Tokens Are What You Need**, 2024, arXiv:2404.07965.
- Xia et al., **LESS: Selecting Influential Data for Targeted Instruction Tuning**, 2024, arXiv:2402.04333.
- Yu et al., **MATES: Model-Aware Data Selection for Efficient Pretraining with Data Influence Models**, 2024, arXiv:2406.06046.
- Li et al., **MASS: Mathematical Data Selection via Skill Graphs for Pretraining Large Language Models**, ICML 2025, arXiv:2503.14917.
- Jiang et al., **Adaptive Data Optimization: Dynamic Sample Selection with Scaling Laws**, ICLR 2025.
- Gu et al., **Data Selection via Optimal Control for Language Models**, ICLR 2025.
- Chen et al., **Aioli: A Unified Optimization Framework for Language Model Data Mixing**, 2025.
- El Hattami et al., **Spaced Scheduling for Large Language Model Training**, TMLR 2025.
- Yu et al., **Group-Level Data Selection for Efficient Pretraining / Group-MATES**, NeurIPS 2025.
- He et al., **STAT: Skill-Targeted Adaptive Training**, ICLR 2026, arXiv:2510.10023.
- Zhao et al., **Rethinking Data Curation in LLM Training: Online Reweighting Offers Better Generalization than Offline Methods**, 2026.
- Wei et al., **Towards Compositional Generalization of LLMs via Skill Taxonomy Guided Data Synthesis (STEPS)**, 2026, arXiv:2601.03676.
- Wang et al., **The Power of Power Law: Asymmetry Enables Compositional Reasoning**, 2026.
- Yin et al., **Learning Composable Chains-of-Thought**, 2025/2026.
- Tong et al., **Generalization in LLM Problem Solving: The Case of the Shortest Path**, ICLR 2026.
- Chen et al., **On the Emergence and Test-Time Use of Structural Information in Large Language Models**, ACL 2026, arXiv:2601.17869.
- Ling et al., **Reusable Experiences: Latent Routing and Modular Composition in LLMs**, ACL 2026.
- Wu et al., **SkillGraph: Dependency-Aware Retrieval for Compositional Agent Skills**, 2026.
- Xia et al., **GraSP: Graph-Structured Skill Compositions for LLM Agents**, 2026, arXiv:2604.17870.
- Butler, **Repeated testing produces superior transfer of learning relative to repeated studying**, 2010.
- Butler et al., **Retrieving and applying knowledge to different examples promotes transfer of learning**, 2017.
- Wang et al., **Spaced cognitive training promotes training transfer**, 2014.
- Tabibian-style/model-based adaptive practice literature represented here by **Optimizing practice scheduling requires quantitative tracking of individual item performance**, 2020.

The literature set is not itself a global novelty certificate. Before a strong paper claim, freeze exact bibliographic identities and a structured row-by-row claim matrix under #455.
