# Atomic LLM Research Lifecycle and Scientific Memory

Status: Round 043 v2 paper companion specification.

## 1. Why this document exists

RAKL is not a prompt template around a language model. It is a stateful research protocol in which the LLM is used at explicitly typed proposal stages while evidence, storage, identity, verification and governance are externalized.

The key engineering distinction is:

```text
raw source != contextual projection != canonical scientific object != derived memory view != active prompt
```

Those objects can carry pointers to one another, but they do not inherit scientific authority merely because they are textually similar.

The executable owner is `src/rakl/research_cycle.py`, whose canonical reference lifecycle currently contains 17 stages.

## 2. The information transformations

Let raw immutable evidence be `e` and the registered operation be `o=(a,f,q,gamma,alpha*,B)`.

### 2.1 Raw evidence

The source bytes are preserved in Tier 0 with immutable identity:

\[
e=(id,bytes,hash,source,cutoff,metadata).
\]

This is evidence storage, not an LLM summary.

### 2.2 Contextual scientific projection

RAKL projects the evidence relative to the scientific question and context:

\[
c=\pi_{q,\gamma}(e).
\]

A projection may identify a claim, measurement, equation, assumption, mechanism fragment, null result or other atomic object. The context `gamma` can contain population, regime, scale, time, units, observation model, intervention, assumptions and QoI.

Projection is therefore a **scientific transformation**: it determines what aspect of a source is being asserted under which conditions.

An LLM may propose the projection, but proposal output is not yet canonical authority.

### 2.3 Normalization

A normalization map

\[
c'=N(c)
\]

can align vocabulary, units, symbols or mathematical coordinates. Normalization is required before claims compete. It may establish representational equivalence but cannot upgrade evidence authority.

Examples:

```text
100 cm -> 1 m
"period" -> registered variable T
percent -> probability
source-specific variable name -> canonical ontology term
```

### 2.4 Identity and lineage

Identity resolution separates exact object identity from ancestry and possible aliasing. Only witnessed `IDENTICAL_TO` collapses canonical identity. `VERSION_OF`, `DERIVED_FROM`, and `POSSIBLE_ALIAS` preserve distinct nodes while recording relationships.

The effective identity object is therefore not just a hash of normalized text. It includes context and evidence lineage.

### 2.5 Provenance binding

Each canonical candidate must retain its source and derivation ancestry:

\[
p(c')=(source\ pins,span/selector,lineage,transform\ ancestry).
\]

The exact raw payload remains rehydratable even if later working contexts use summaries.

### 2.6 Atlas insertion

After the required gate, the normalized provenance-bound object enters the contextual Knowledge Atlas as a typed node. RAKL then creates or tests typed relations such as equivalence, contextual compatibility, contradiction, derivation, mechanism ancestry, refutation, transition and analogy.

An edge is not merely a hyperlink. It has relation type, scope, assumptions, evidence and authority semantics.

### 2.7 Derived memory views

To operate efficiently, RAKL can materialize a view

\[
v=T(S)
\]

from source set `S`.

A derived view must carry:

```text
source pins
transform identity
canonical roots
representation-level authority ceiling
```

A lossless view may additionally have a reconstruction witness. A lossy view must declare an erasure ledger.

Therefore:

\[
Lossy(v)=1 \Rightarrow CanonicalTruth(v)=0.
\]

Compression is a **storage/materialization transformation**, not a scientific projection and not a truth operation.

### 2.8 Retrieval/index space

Tier-1 indexes may use lexical keys, graph indexes, semantic vectors/embeddings, materialized summaries or other retrieval structures. These are rebuildable navigation structures. Their geometry does not define scientific identity and does not mint scientific authority.

A useful implementation rule is:

```text
embedding-near != scientifically equivalent
embedding-far  != scientifically incompatible
```

Similarity becomes scientifically useful only after a typed witness and context check.

### 2.9 Bounded working context

Given candidate material `V(o)` and mandatory epistemic set `M(o)`, the compiler targets

\[
C^*(o)=\arg\max_{C\subseteq V(o)} U(C\mid o)
\]

subject to

\[
M(o)\subseteq C,\qquad Tokens(C)\le B.
\]

The current implementation uses deterministic marginal weighted coverage per token. It does not claim a globally optimal arbitrary utility solution.

Mandatory objects can include the target/scope, assumptions, falsifiers, relevant negative history, both sides of contradictions, authority prerequisites, mechanism ancestry and evaluator identity.

If mandatory material cannot fit:

```text
CANNOT_COMPILE
```

is the correct result. The framework must not hide scientific evidence to make a prompt fit.

### 2.10 LLM prompt

Only Tier 3 is sent to the replaceable LLM. The prompt contains a bounded representation of the active research operation, not the full research archive.

This is the main scaling objective:

\[
\frac{\partial E[Tokens_{active}]}{\partial N_{irrelevant\ archive}}\approx0
\]

while mandatory scientific recall remains one.

### 2.11 Proposal

The LLM may propose:

```text
claim
context map
equation
mechanism
analogy
experiment
query
synthesis
method operator
```

The proposal is written to proposal workspace and has proposal authority only.

### 2.12 Verification

External verification tests the proposal against source evidence, registered assumptions, falsifiers, model-criticism probes, assumption-sensitivity worlds, benchmarks or new experiments.

Strong scientific verification that relied on a lossy view must rehydrate the necessary canonical roots before accepting a claim.

### 2.13 Canonical update

Only a licensed verification result may update canonical epistemic state. The LLM does not directly mutate the authoritative state because it generated fluent output.

Nulls, refutations and failures are appended to negative history rather than deleted.

### 2.14 Residual diagnosis

An unresolved discrepancy becomes a typed residual:

```text
missing evidence
missing context
measurement failure
contradiction
model inadequacy
partial identification
method-basis gap
implementation defect
```

Residuals drive the next atomic fiber rather than being treated as embarrassment to remove from the record.

### 2.15 Next-action control

The controller can search, acquire evidence, design an experiment, change representation, seek independent help, assimilate an external method, construct a new mechanism or stop a flat route.

### 2.16 Saturation

RAKL records semantic novelty after identity resolution and tracks evidence lineage independently from process independence. Rephrased duplicates therefore do not create novelty, and multiple analyses of the same underlying evidence do not create independent flat rounds.

### 2.17 Experience consolidation

A completed research trajectory can become a **candidate procedural skill**, but one successful trajectory is not automatically learned ability. Transfer and fresh assurance are required before a strong reusable/self-evolution claim.

## 3. Canonical 17-stage lifecycle

| # | Stage | LLM role | Primary storage | Authority effect |
|---|---|---|---|---|
| 1 | `REGISTER_TASK` | none | Tier 0 | none |
| 2 | `INGEST_EVIDENCE` | none | Tier 0 | none |
| 3 | `DECOMPOSE_SOURCE` | may propose | Tier 1 workspace | proposal only |
| 4 | `PROJECT_CONTEXT` | may propose | Tier 1 workspace | representation only |
| 5 | `NORMALIZE_OBJECT` | may propose | Tier 1 index/view | representation only |
| 6 | `RESOLVE_IDENTITY` | no authority role | Tier 0 identity ledger | none |
| 7 | `BIND_PROVENANCE` | no authority role | Tier 0 | external verification required |
| 8 | `UPDATE_ATLAS` | no direct mutation by proposer | Tier 0 | gated canonical update |
| 9 | `MAP_RELATIONS` | may propose relation | Tier 0 | external verification required |
| 10 | `COMPILE_WORKING_CONTEXT` | none | Tier 2 | none |
| 11 | `GENERATE_PROPOSAL` | primary proposer | Tier 3 -> proposal workspace | proposal only |
| 12 | `VERIFY_PROPOSAL` | not final authority | Tier 0 verification ledger | external verification required |
| 13 | `CANONICAL_UPDATE` | none | Tier 0 | gated canonical update |
| 14 | `DIAGNOSE_RESIDUAL` | may propose diagnosis | Tier 0 | proposal only |
| 15 | `SELECT_NEXT_ACTION` | may propose action | method memory | proposal only |
| 16 | `CHECK_SATURATION` | none | Tier 0 | external verification required |
| 17 | `CONSOLIDATE_METHOD_EXPERIENCE` | may propose skill | method memory | proposal only |

The precise typed inputs/outputs, read/write sets, failure states and implementation owners are executable in `stage_contracts()`.

## 4. What is actually compressed?

RAKL does **not** replace the canonical archive with a compressed latent representation.

Compression can occur at several derivative layers:

1. duplicate/identity normalization reduces redundant **semantic objects** while retaining all source lineage;
2. lossless views reduce representation redundancy and are reconstructable;
3. lossy views summarize or abstract information but retain source pointers plus erasure metadata;
4. target-conditioned context compilation selects only a small working subset;
5. method experience can be consolidated into reusable procedural candidates after transfer testing.

The canonical archive remains the authority root.

This design lets RAKL maximize available knowledge without requiring an LLM to reread the complete archive on every operation.

## 5. Relationship to vector/embedding spaces

If a future deployment uses embeddings, the embedding map is best written as

\[
z=E(v)
\]

for retrieval/navigation only. A nearest-neighbour relation in `z` is not a canonical Knowledge Atlas relation. It is a candidate route that must be converted back into typed objects and checked under RAKL semantics.

Thus RAKL can exploit modern vector search while keeping scientific identity and authority in an explicit symbolic/provenance layer.

## 6. Relation to Obsidian-style knowledge maps

An Obsidian graph is a useful UI analogy: a global graph provides orientation; a local graph gives a target-centred neighbourhood; backlinks make incoming relations navigable.

RAKL adds scientific semantics that a generic note graph does not supply:

```text
node type
context/population/scale
source provenance
scientific authority coordinates
negative history
edge relation type
edge evidence
compatibility and contradiction status
mechanism ancestry
epistemic cuts
target support paths
saturation state
active-context/token overlay
```

A future `RAKL Atlas UI` can therefore borrow the interaction model of graph-note tools without confusing a user-authored hyperlink with an evidence-bearing scientific transition.

## 7. Engineering demonstration

`src/rakl/mini_research_demo.py` executes a deterministic known-answer pendulum world. It emits a machine-readable receipt showing raw-source count, projection/deduplication counts, atlas growth, relation witnesses, negative history, support-path opening, token reduction, memory-view lineage and semantic saturation.

The demo deliberately uses zero LLM calls. Its purpose is to validate the mechanics independently of stochastic model behavior. The later matched LLM and `polymarket_crypto` experiments test whether those mechanics improve real scientific work.
