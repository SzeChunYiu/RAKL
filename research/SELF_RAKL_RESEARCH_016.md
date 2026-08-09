# SELF-RAKL Research Round 016 — Real Cross-Domain Retrieval Ground Truth and Corpus Identity

Date: 2026-08-09

Starting `main`: `1ee39b67243e393c257b51a42910675da9565fa4`

Entering status: `ACTIVE_NON_FLAT`.

## 1. Baseline audit

This run began from live repository state and checked current `main`, recent commits, open issues/PRs, Constitution, Round-015 research/receipt, Knowledge Atlas principles, meta-fiber backlog, capability-shaping support and current CI evidence.

Observed baseline:

```text
main = 1ee39b67243e393c257b51a42910675da9565fa4
open issues = 0
open pull requests = 0
Constitution SHA = 4d456ceab32122391c830fe8586766cf0e0037aa
latest completed research round = SELF_RAKL_RESEARCH_015
similarity lane = ACTIVE_NON_FLAT
capability-shaping lane = ACTIVE_NON_FLAT
```

The previous rounds had already formalized GLUE/JUMP witnesses, mapping-capacity controls, retrieval/recognition/transfer separation and AI capability shaping. The highest-value non-duplicate residual was therefore empirical and semantic:

> How can RAKL execute a real far-domain retrieval benchmark without silently treating one benchmark label as proof of retrieval relevance, structural analogy and target-transfer validity at the same time?

This run targets `META_N052_REAL_FAR_DOMAIN_RETRIEVAL_BENCHMARK` and uses it as the first concrete case study for `META_N055_MATCHED_SCAFFOLD_ABLATION_BENCHMARK`.

## 2. Six-role panel

Six role-separated passes were fixed before synthesis.

1. **Cognitive-science / analogy expert** — asks whether designated inspiration is actually evidence of relational/systematic analogy rather than topical usefulness.
2. **Knowledge-representation / ontology expert** — separates label authority layers and benchmark/corpus identity.
3. **Scientific-information-retrieval expert** — owns corpus coverage, recall@k, rank, split identity, top-k fairness and route attribution.
4. **Applied-mathematics / dynamical-systems expert** — requires explicit structural witnesses and refuses to infer isomorphism/causal equivalence from retrieval relevance.
5. **Computational-creativity / search expert** — evaluates whether distant-domain retrieval adds genuinely useful structural diversity rather than distance for its own sake.
6. **Adversarial scientific-method reviewer** — attacks hidden labels, post-hoc abstractions, floating corpus identities, resource confounding and false ground-truth escalation.

All passes shared one orchestration context and are not counted as mutually blind or statistically independent review.

### Delegation and disagreements

| Finding | Primary roles | Disagreement/adversarial condition |
|---|---|---|
| benchmark labels must be factored by authority layer | cognitive analogy + ontology + applied math | IR initially preferred using the dataset gold label directly for end-to-end evaluation; rejected because relevance does not establish structural witness or transfer |
| corpus identity is part of experimental state | IR + ontology | adversarial reviewer required exact revision/artifact identity rather than dataset name or mutable viewer |
| graph/structural routes with extra graph resources are system-level comparisons | capability-shaping logic + IR + adversarial reviewer | creativity role wanted to credit graph retrieval as a better 'AI search algorithm'; panel narrowed this to system gain unless resources are matched |
| domain distance only counts subject to valid witness quality | creativity + applied math | adversarial reviewer rejects novelty credit for remote but structurally weak candidates |
| MIR and IsoSci are complementary charts, not one score | cognitive analogy + IR + ontology | combining them would conflate paper retrieval with isomorphic reasoning/knowledge attribution |

The adversarial falsifier for the central ground-truth split is explicit: if a future independently annotated corpus demonstrates that its retrieval-relevance labels reliably and definitionally entail the exact registered structural relation and the target transfer claim, the separate layers may collapse for that narrowly defined benchmark. Until then they remain distinct.

## 3. Fresh source projections

### 3.1 MIR — real methodology inspiration retrieval

Garikaparthi et al.'s Methodology Inspiration Retrieval (MIR) benchmark provides a real scientific retrieval problem in which research-problem descriptions are linked to methodology inspirations. The accompanying repository includes chronological/time-filtered test artifacts and a methodology adjacency graph used by graph-assisted retrieval.

Exact source pin used in this run:

```text
repository = Anikethh/Methodology-Inspiration-Retrieval
revision = dc0545adffad7cd15c730f4a7bb9388d6440a47c
```

Pinned artifact metadata:

```text
data/test_chronological_df.csv
  blob = ae1d293db3dd755232e527c3f8d58800ba7e06ad
  bytes = 5,169,467

data/full_mag.csv
  blob = eadcb6a1b424ef7037fe69428ecf0b7283374206
  bytes = 7,782,375

data/mir_test_time_based_filtering.csv
  blob = 24bce07828cbbf082f2ccc57199e4a01991f7f25
  bytes = 2,001,385
```

The MIR artifact bytes could not be ingested in this automation runtime through the available transport path, so **no MIR retrieval route was actually executed in Round 016**. Repository revision and artifact identities were observed; retrieval performance remains `CANNOT_CHECK`.

Panel consequence: MIR becomes a real retrieval-relevance benchmark, not automatic structural-analogy ground truth.

### 3.2 IsoSci — structural isomorphism and reasoning-versus-knowledge attribution

IsoSci provides paired cross-domain scientific problems designed around structural isomorphism and explicitly studies whether apparent cross-domain reasoning gains instead come from domain-knowledge retrieval. This is useful for a different axis from MIR.

A source-identity audit after freezing the Round-016 benchmark exposed an error in the initially recorded dataset reference. The currently observed Hugging Face dataset is:

```text
isosci/isosci
```

It is gated, and exact immutable dataset-file identity was not established in this run. The frozen benchmark is therefore not silently edited; `SELF_RAKL_RESEARCH_016_BENCHMARK_ERRATUM.json` preserves the original error and requires a newly frozen corrected IsoSci execution packet.

Panel consequence: IsoSci is a candidate structural-reasoning/knowledge-attribution chart, not a paper-inspiration retrieval label source.

## 4. Central result: benchmark ground truth must be factorized

Define three evaluator-side labels for a candidate source `s` and target problem `t`:

\[
Y_R(s,t) = \text{retrieval relevance},
\]

\[
Y_S(s,t; q,\phi,\Gamma) = \text{valid typed structural witness},
\]

and

\[
Y_T(s,t; h) = \text{target-domain validation of transferred claim }h.
\]

RAKL must not assume

\[
Y_R = Y_S = Y_T.
\]

A paper can be a useful methodology inspiration while failing a strict structural analogy relation. A structurally valid analogy can generate a transfer that fails in the target because of a material, scale, intervention or boundary condition. Conversely, a target result may be useful without proving mechanism identity.

This yields the retained internal object:

```text
BENCHMARK_GROUND_TRUTH_FACTORIZATION
```

and an authority rule:

```text
retrieval relevance
  != structural witness validity
  != target transfer validity
```

## 5. Corpus identity is an epistemic coordinate

A benchmark name is not a frozen corpus.

A valid route trial must identify at least:

```text
corpus id
source repository/dataset identity
immutable revision
artifact path
content hash/blob identity
split/task packet
query packet
top-k
model + model configuration
output contract
evaluator
resource set
hidden-label policy
```

A viewer outage, schema-cast failure or transport failure cannot silently redefine the corpus or license substitution with a nearby snapshot.

This yields:

```text
CORPUS_ARTIFACT_IDENTITY_CONTRACT
VIEWER_TRANSPORT_DOES_NOT_REDEFINE_CORPUS
```

The IsoSci reference error found in this same run is a native demonstration of why this coordinate matters. The mistake is preserved rather than erased.

## 6. Coverage must be separated from retrieval recall

For designated source set `G` and frozen candidate corpus `C`, define corpus coverage

\[
\mathrm{coverage}(G,C)=\frac{|G\cap C|}{|G|}.
\]

Retrieval recall should then be conditional on sources that are actually available in the frozen corpus:

\[
\mathrm{recall@k}_{\mathrm{conditional}}
=
\frac{|R_k\cap G\cap C|}{|G\cap C|}.
\]

If a designated source is absent from `C`, that is a **corpus coverage failure**, not a retriever failure. This distinction was previously theoretical in RAKL's four-gate analogy diagnostic; Round 016 now gives it a real-benchmark contract and executable metrics.

## 7. Matched retrieval-route capability attribution

A route comparison is meaningful only under a matched non-route contract.

For routes such as

```text
LEXICAL
EMBEDDING
DOMAIN_STRIPPED_RELATIONAL
GRAPH_OR_STRUCTURAL
```

freeze the same:

```text
corpus/revision/artifact
task packet
query packet
top-k
base model/config
output contract
evaluator
hidden-label policy
```

Resource sets are separate experimental coordinates. If a graph route adds a methodology graph/index not available to the baseline, an improvement is a **system-level gain with resource delta**, not pure model-utilization amplification.

This is the first direct application of Round-015 capability shaping to the similarity lane.

Retained object:

```text
MATCHED_RETRIEVAL_ROUTE_RESOURCE_ATTRIBUTION
```

## 8. Frozen benchmark chronology

Before any Round-016 implementation, the following was committed to `main`:

```text
research/SELF_RAKL_RESEARCH_016_FROZEN_BENCHMARK.json
commit = f32cbe43fc4411ca2d2c1788aaa67d5c82321528
```

The benchmark freezes 17 hostile worlds covering corpus identity, split/model/top-k mismatch, hidden labels, post-hoc abstractions, declared and undeclared resource differences, retrieval-relevance/structure/transfer escalation, false friends, distance gaming, duplicate-route credit, corpus absence, reasoning-versus-knowledge attribution and viewer transport failure.

The benchmark contains the now-known incorrect IsoSci dataset reference. It remains immutable historical evidence. The correction lives in a separate erratum rather than rewriting the frozen prediction packet.

## 9. Supporting implementation

A candidate branch from the frozen benchmark head added:

```text
src/rakl/retrieval_benchmark.py
tests/test_retrieval_benchmark.py
src/rakl/__init__.py
```

Support API objects include:

```text
CorpusArtifactIdentity
GroundTruthFactorization
RetrievalRouteTrial
RetrievalRouteReport
RouteComparisonReport
```

with operations:

```text
validate_corpus_artifact
validate_ground_truth_factorization
evaluate_retrieval_route_trial
compare_retrieval_routes
```

The module is research/evaluation support only. It cannot activate a retrieval route, promote canonical knowledge, establish intrinsic model improvement or validate a target transfer.

Hostile tests cover:

- unpinned/unobserved corpus identity;
- collapsed ground-truth authority;
- retrieval-only scoped labels;
- coverage versus retrieval recall;
- MRR;
- hidden labels;
- post-hoc query edits;
- unexecuted routes (`CANNOT_CHECK`);
- top-k overflow;
- duplicate ranked candidates;
- model/corpus/top-k mismatches;
- declared and undeclared resource deltas;
- object immutability.

Exact candidate head:

```text
1cf4445c177874c2ae2b6bc1995581b2fdf7ce69
```

The unchanged repository `test` workflow executed on this exact head and completed successfully, including `pytest`. Comparison to frozen `main` showed the candidate was ahead-only by three commits and changed only the new support module, tests and public export. `main` was rechecked at the frozen benchmark head and then non-forced fast-forwarded to the exact tested candidate SHA.

## 10. What was not executed

This distinction is critical.

Round 016 did **not** execute MIR lexical, embedding, domain-stripped relational or graph retrieval against the real corpus because the artifact bytes were not available through the accessible runtime transport.

Therefore these remain unmeasured:

```text
real MIR recall@k
real MIR MRR
route-specific incremental recall
recognition precision on retrieved MIR papers
valid-witness rate on MIR inspirations
near-miss rejection on MIR
transfer utility from MIR analogies
cost per valid real witness
```

The support contract passed software tests; the scientific retrieval hypothesis did not yet receive empirical confirmation.

## 11. Semantic novelty after deduplication

### Prior art / not counted as RAKL novelty

- methodology inspiration retrieval;
- graph-assisted scientific retrieval;
- cross-domain structural analogy;
- isomorphic-problem evaluation;
- reasoning-versus-retrieval decomposition;
- recall@k/MRR;
- matched benchmark evaluation generally;
- retrieval/recognition/transfer stage separation generally.

### Retained RAKL internal objects

1. `BENCHMARK_GROUND_TRUTH_FACTORIZATION`
2. `CORPUS_ARTIFACT_IDENTITY_CONTRACT`
3. `MATCHED_RETRIEVAL_ROUTE_RESOURCE_ATTRIBUTION`
4. `RETRIEVAL_COVERAGE_RECALL_SEPARATION_REAL_BENCHMARK`
5. `VIEWER_TRANSPORT_DOES_NOT_REDEFINE_CORPUS`

These are useful method-control objects. No headline novelty claim is made for them in this round.

## 12. Saturation verdict

```text
RAKL_METHOD = ACTIVE_NON_FLAT
similarity_lane = ACTIVE_NON_FLAT
capability_shaping_lane = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

The lane is not flat because a new empirical coordinate—ground-truth factorization plus immutable corpus identity—was retained and implemented. But the core real-retrieval performance question remains unresolved.

## 13. Next discriminators

Highest priority:

```text
META_N060_REAL_MIR_ROUTE_EXECUTION
```

Required next experiment:

1. obtain the exact pinned MIR artifact bytes reproducibly;
2. freeze a query/task packet and hidden evaluator labels;
3. execute lexical and embedding baselines first;
4. execute domain-stripped relational and graph/structural routes with matched top-k/model/evaluator;
5. explicitly record any resource delta;
6. separately score corpus coverage, retrieval rank, structural-witness validity and target transfer;
7. preserve false friends and route-specific nulls;
8. keep the simpler route if richer routes do not improve registered valid-witness QoIs after cost.

Secondary work:

- `META_N058_BENCHMARK_GROUND_TRUTH_FACTORIZATION`: build separate structural-witness annotation/evaluator packets rather than borrowing MIR relevance labels;
- `META_N055_MATCHED_SCAFFOLD_ABLATION_BENCHMARK`: use MIR route comparison as the first real capability-shaping ablation;
- `META_N061_ISOSCI_REASONING_KNOWLEDGE_AXIS`: freeze a corrected gated IsoSci packet only after exact dataset identity/access is established;
- continue `META_N050_CONTRASTIVE_ANALOGY_NEGATIVES` and `META_N043_MAPPING_CAPACITY_AND_VACUITY_CONTROL`.

No Constitution change occurred.
