# SELF-RAKL Research Round 014 — Analogy Discovery Failure Localization

Date: 2026-08-09

Starting `main`: `158f2dca389a1b54c1b3943a950b34f2e4cca545`

Entering status: `ACTIVE_NON_FLAT`.

## 1. Baseline audit

The run began from live `main` and inspected current repository state before selecting the next similarity atom.

Observed baseline:

```text
main = 158f2dca389a1b54c1b3943a950b34f2e4cca545
open issues = 0
open pull requests = 0
Constitution SHA = 4d456ceab32122391c830fe8586766cf0e0037aa
baseline exact-head push test workflow = completed success
latest completed research round = SELF_RAKL_RESEARCH_013
similarity lane = ACTIVE_NON_FLAT
method-assimilation lane = ACTIVE_NON_FLAT
```

The previous similarity rounds had already established typed GLUE/JUMP witnesses, L0-L6 abstraction, erasure ledgers, admissible mapping-capacity control, query/probe families and distinguishing-probe memory. Round 013 then applied those ideas recursively to method assimilation.

The selected non-duplicate atom for this run was therefore:

> Can RAKL tell whether a scientific JUMP failed because the relevant analogue was absent from the corpus, present but not retrieved, retrieved but not structurally recognized, or correctly recognized but invalid when transferred to the target?

This is an implementation and benchmark refinement of `META_N037_RETRIEVAL_RECOGNITION_TRANSFER_SEPARATION`, not a new claim that RAKL invented staged analogy reasoning.

## 2. Frozen benchmark chronology

Before creating `src/rakl/similarity.py`, the run committed:

```text
research/SELF_RAKL_RESEARCH_014_FROZEN_BENCHMARK.json
commit = 10577799d3058e2740ee4d12ee8cd71bf48b276f
```

The benchmark freezes 13 worlds covering:

- analogue absent from the candidate corpus;
- analogue present but not retrieved;
- analogue retrieved but not structurally recognized;
- correct witness with target transfer later refuted;
- multi-view route attribution;
- ranking defect versus complete retrieval failure;
- surface-plausible near-miss negatives;
- positive/near-miss contrast isolating a decisive invariant;
- cross-analogy confirmation;
- false confirmation from a shared surface template;
- domain-homogeneous analogy portfolios;
- hidden answer/relevance-label exposure;
- post-hoc query or abstraction edits.

Hidden relevance labels, query templates, stage definitions and acceptance criteria are frozen before candidate testing.

## 3. Six-role expert panel

Six role-separated passes were fixed before synthesis.

1. **Cognitive-science / analogy expert** — structure mapping, retrieval versus recognition, abstraction, remote analogy and human/LLM error asymmetries.
2. **Knowledge-representation / ontology expert** — typed graph alignment, relation semantics, candidate identity, witness composition and negative edges.
3. **Scientific-information-retrieval expert** — corpus coverage, recall@k, rank, multi-view retrieval, route attribution and matched-budget evaluation.
4. **Applied-mathematics / dynamical-systems expert** — invariants, admissible maps, probe families, nulls, regime restrictions and composition failure.
5. **Computational-creativity / search expert** — domain diversity, remote association, non-greedy candidate portfolios and cross-analogy coverage.
6. **Adversarial scientific-method reviewer** — hidden-answer leakage, post-hoc query adaptation, false confirmation, surface near-misses and authority escalation.

All roles shared one orchestration context and are not counted as independent or mutually blind reviewers.

### Delegation rule used in this round

Each retained finding was jointly reviewed by at least two roles:

| Finding | Primary roles | Adversarial check |
|---|---|---|
| four-gate discovery localization | cognitive analogy + scientific IR | adversarial reviewer checked label leakage and stage rewriting |
| route-attributed retrieval | scientific IR + ontology | adversarial reviewer checked double-credit across routes |
| contrastive near-miss packets | cognitive analogy + applied mathematics | adversarial reviewer required a decisive distinguishing probe |
| cross-analogy motif confirmation | creativity/search + applied mathematics | adversarial reviewer challenged independence and authority leakage |
| support-only similarity witness schema | ontology + applied mathematics | adversarial reviewer verified no active-authority path exists |

## 4. Fresh primary-source projections

### 4.1 Analogical Deep Research / CANA — structure and coverage are explicit retrieval requirements

Chen et al. (2026), `arXiv:2607.13602`, formulate historical analogy search using a surface description and a mechanistic/causal representation. Their ADR-bench shows that deep-research agents can miss mechanism-level analogies, and CANA uses structural decomposition plus iterative cross-analogy confirmation.

The paper's theoretical treatment is particularly relevant because it separates surface non-identifiability from mechanism alignment and formalizes conditions under which multiple confirming analogies increase confidence in a structural position.

**Reviewed by:** cognitive analogy + applied mathematics + creativity/search.

**RAKL consequence:** mechanism-aligned retrieval and cross-analogy confirmation are prior art. RAKL should use them as candidate method modules while adding its own authority and provenance constraints. Cross-analogy agreement remains proposal evidence, not target validation.

### 4.2 ResearchBench — scientific discovery benefits from task decomposition

Liu et al. (Findings of ACL 2026) separate scientific discovery into inspiration retrieval, hypothesis composition and hypothesis ranking over a multi-discipline benchmark.

**Reviewed by:** scientific IR + adversarial method review.

**RAKL consequence:** stage-decomposed scientific-discovery evaluation is prior art. The new internal requirement is narrower: expose corpus coverage before retrieval and preserve stage-localized negative evidence so a downstream success cannot rewrite an upstream miss.

### 4.3 Relational analogy evaluation — plausible semantic distractors are not enough

Das and Balke (INLG 2025) evaluate complex analogies with semantically plausible alternatives and distinguish relational overlap from embedding/context similarity and prototypicality.

**Reviewed by:** cognitive analogy + ontology.

**RAKL consequence:** the mapper should be evaluated on relation preservation, not the same semantic score used for candidate retrieval. Surface-plausible near-misses become a required hostile test family.

### 4.4 A3E — multi-stage analogy annotation is executable prior art

Zhang and Lyu (Findings of ACL 2025) introduce a multi-stage structure-mapping based analogy annotation framework and release code/data at `zhangxjohn/A3E`.

**Reviewed by:** ontology + cognitive analogy.

**RAKL consequence:** multi-stage LLM analogy annotation itself is prior art. Recognition remains a replaceable RAKL module behind a frozen interface.

### 4.5 YARN — abstraction level is an experimental coordinate

Khojasteh et al. (2026), `arXiv:2603.29997`, provide an open pipeline that decomposes narratives into units, constructs abstractions at multiple levels and performs local/global structural mapping. Their error analysis identifies abstraction-level choice and implicit causality as continuing challenges. The open repository `mhkhojaste/narrative-analogy` exposes the pipeline stages directly.

**Reviewed by:** cognitive analogy + ontology + scientific IR.

**RAKL consequence:** the L0-L6 ladder should not assume that more abstraction is monotonically better. Retrieval route and abstraction level should be logged so incremental recall can be measured.

### 4.6 SG-RAG — structural retrieval is an alternative route, not a universal replacement

Xie et al. (ACL 2026) formulate a structure-guided retrieval problem and use embedding-based subgraph matching to satisfy complex structural query conditions.

**Reviewed by:** scientific IR + ontology + applied mathematics.

**RAKL consequence:** graph/subgraph matching is a valid candidate JUMP retriever, but it must compete under the same frozen corpus, top-k and model budget rather than being assumed superior.

## 5. Main disagreement: what counts as retrieval success?

The scientific-IR role initially proposed ordinary recall@k as the main diagnostic. The cognitive and adversarial roles objected that this can hide two important distinctions:

1. the designated analogue may not exist in the corpus at all;
2. a surface neighbor can outrank the deep analogue while the deep analogue still remains in top-k.

The panel therefore adopted four gates:

```text
CORPUS AVAILABILITY
        ↓
RETRIEVAL
        ↓
WITNESS CONSTRUCTION / RECOGNITION
        ↓
TARGET TRANSFER TEST
```

and separates ranking defects from total retrieval failure.

This retains the existing RAKL rule:

```text
retrieval != recognition != transfer != target authority
```

while adding the missing corpus-coverage coordinate.

## 6. Retrieval route attribution

A candidate may be surfaced by:

```text
lexical query
embedding similarity
domain-stripped relational query
graph/subgraph retrieval
equation/invariant retrieval
other declared route
```

Round 014 records the route that actually produced each candidate. If lexical and embedding retrieval both miss a distant analogue but a relational abstraction retrieves it, only the successful route receives incremental-recall credit.

This yields the internal object:

```text
RETRIEVAL_ROUTE_ATTRIBUTION
```

The adversarial reviewer explicitly rejected counting the same retrieved candidate as multiple independent analogy witnesses merely because several routes returned it.

## 7. Contrastive near-misses

Random negatives are often too easy. Round 014 therefore adds benchmark worlds where a negative candidate shares terminology, roles and much of the graph but differs on one decisive coordinate:

```text
causal direction
unit/type compatibility
regime
intervention semantics
required invariant
```

A strong recognition module should identify the failed coordinate and emit a `DistinguishingProbeCertificate` rather than only a low scalar score.

Contrastive and near-miss learning are established ideas, so this is not counted as a RAKL novelty claim. The RAKL-specific purpose is preserving the decisive failed probe as immutable negative atlas history.

## 8. Cross-analogy confirmation is proposal-only

The creativity role proposed using multiple distant analogies to infer robust cross-domain motifs. The applied-mathematics role accepted this only with explicit source-domain diversity and warned that repeated sources may be correlated. The adversarial reviewer further noted that common templates, common training data or shared evidence ancestry can manufacture apparent confirmation.

The support API therefore provides only:

```text
CORROBORATED_PROPOSAL_ONLY
```

for shared preserved structure across valid witnesses from distinct source domains.

It deliberately cannot produce target validation.

This partially assimilates the cross-analogy idea from CANA while adding RAKL's non-escalation boundary. The stronger independence problem remains open as `META_N051_CROSS_ANALOGY_CONFIRMATION_INDEPENDENCE`.

## 9. Supporting implementation

`src/rakl/similarity.py` adds immutable research-only contracts:

```text
SimilarityRelation
MappingAdmissibility
ProbeFamily
SimilarityWitness
DistinguishingProbeCertificate
WitnessReport
AnalogyDiscoveryObservation
AnalogyDiscoveryReport
StructuralMotifReport
```

and three operations:

```text
validate_similarity_witness
diagnose_analogy_discovery
corroborate_structural_motif
```

The witness validator operationalizes earlier Round-011/012 requirements:

- mapping and probe-family identity must be present;
- mapping-family chronology must be known and predeclared;
- null calibration must be observed;
- declared constraint violations reject certification;
- preserved and non-preserved structure cannot contradict each other;
- causal analogy requires a causal-direction constraint;
- mathematical isomorphism requires type/unit compatibility control.

The discovery diagnostic localizes corpus, retrieval, recognition and transfer outcomes and invalidates trials with hidden-answer exposure or post-hoc query adaptation.

No API in this module can activate routing, promote canonical knowledge or change `main`.

## 10. Hostile tests

`tests/test_similarity.py` covers:

- valid frozen witness contracts;
- post-hoc mapping-family rejection;
- unit/constraint violation rejection;
- mathematical isomorphism without type/unit control;
- corpus absence versus retriever miss;
- retrieved-but-unmapped recognition failure;
- witnessed analogy remaining proposal-only;
- target-transfer refutation preserving the structural witness;
- hidden-answer leakage;
- post-hoc query modification;
- cross-domain motif corroboration remaining proposal-only;
- same-domain repetition not being treated as cross-domain confirmation;
- witness immutability.

An intermediate branch head containing the implementation and hostile tests completed the repository `test` workflow successfully before the final research receipt was staged. This is supporting evidence only; promotion still requires the exact final candidate head to pass.

## 11. Semantic novelty after deduplication

### Prior art / not counted as novelty

- mechanism-aligned analogy retrieval;
- cross-analogy confirmation;
- scientific inspiration retrieval as a distinct subtask;
- multi-stage analogy annotation;
- abstraction-assisted structural mapping;
- graph/subgraph structural retrieval;
- relational-overlap analogy evaluation;
- contrastive or near-miss negatives.

### Retained RAKL internal objects

1. `CORPUS_RETRIEVAL_RECOGNITION_TRANSFER_QUADRIPARTITION`
2. `RETRIEVAL_ROUTE_ATTRIBUTION`
3. `ANALOGY_TRIAL_LEAKAGE_SENTINELS`
4. `CROSS_ANALOGY_MOTIF_PROPOSAL_ONLY`

These are retained as useful RAKL control objects. They are **not yet claimed as individually novel scientific contributions**.

## 12. Saturation verdict

```text
RAKL_METHOD = ACTIVE_NON_FLAT
similarity_lane = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

The reason is operational rather than rhetorical: a new frozen benchmark and executable support layer now make stage-localized failure testable, but the central empirical question remains unanswered because no real far-domain paper corpus has yet been run under matched routes.

## 13. Next discriminators

Highest priority is now:

```text
META_N052_REAL_FAR_DOMAIN_RETRIEVAL_BENCHMARK
```

Required next experiment:

1. freeze a real scientific-paper corpus containing expert-validated far-domain analogues and surface-plausible near-misses;
2. hide relevance labels from all retrieval and mapping modules;
3. compare lexical, embedding, domain-stripped relational and graph/structural routes under the same top-k and model budget;
4. separately score corpus coverage, recall/rank, witness correctness, near-miss rejection and target-transfer validity;
5. preserve route-specific nulls and negative mappings;
6. do not activate richer retrieval if lexical+embedding matches it under the frozen budget.

Secondary next work:

- `META_N049` route attribution and corpus coverage;
- `META_N050` contrastive analogy negatives;
- `META_N051` independence-aware cross-analogy confirmation;
- continue `META_N043` mapping-capacity/vacuity controls;
- continue adversarial prior-art review before any headline novelty claim.

The Constitution remains unchanged.
