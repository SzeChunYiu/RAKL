# RAKL Similarity & Analogy Algebra

Status: candidate theory layer v0.1, research-only  
Date: 2026-08-09

## 1. Why similarity must be typed

RAKL has two scientifically different discovery problems.

1. **GLUE** asks whether different sources are compatible local views of the same underlying object, representation family, generator, mechanism, observable or QoI.
2. **JUMP** asks whether a different object, often in a distant field, preserves enough relational, causal, dynamical, mathematical, functional or failure structure to generate a useful transfer hypothesis.

These objectives have opposite error asymmetries. GLUE must be conservative because a false merge corrupts the atlas. JUMP can be exploratory because a candidate analogy is not canonical knowledge and can be rejected later. RAKL therefore adopts:

> **Conservative gluing, adventurous jumping, evidence-gated transfer.**

A single embedding similarity or scalar `similar_to` edge cannot represent both.

## 2. Concept signature

For an atomic object `x` under registered question or QoI `q`, define a multi-layer signature

\[
\Sigma_q(x)=(E,R,C,M,D,F,O,B,A),
\]

where:

- `E` — entities, components and typed roles;
- `R` — relations and higher-order relational structure;
- `C` — causal dependencies and interventions;
- `M` — mechanism ancestry;
- `D` — equations, dynamics, invariants, symmetries and asymptotic laws;
- `F` — functions or goals;
- `O` — observables and measurement operators;
- `B` — boundaries, assumptions, scales, regimes and validity conditions;
- `A` — affordances, actions or interventions available on the system.

The signature is not assumed complete. Missing coordinates remain explicit.

## 3. Similarity claims require witnesses

A RAKL similarity claim is not a score. It is a **witnessed, scoped relation**

\[
W_{A\to B}^{\tau,q}
=(\phi, P^+,P^-,\Gamma,\Delta,\mathcal E),
\]

where:

- `tau` is the relation type;
- `q` is the question/QoI under which similarity matters;
- `phi` is an explicit partial mapping between roles, relations, equations or observables;
- `P+` lists preserved structures;
- `P-` lists known non-preserved structures and broken correspondences;
- `Gamma` gives scope, regime and assumptions;
- `Delta` records approximation/error/distortion or unresolved mapping ambiguity;
- `E` is the evidence packet supporting the mapping.

The witness is primary. Any scalar score is only a projection of this richer object.

## 4. Two relation spaces

### 4.1 GLUE relations

GLUE relations may alter canonical organization of the Knowledge Atlas and therefore require strong evidence.

| Relation | Default properties | Required witness | Non-escalation rule |
|---|---|---|---|
| `SAME_OBJECT` | symmetric; transitive only under fixed identity scope | identity/provenance mapping plus compatible context | identity of one scope does not imply identity of another |
| `SAME_ENTITY` | symmetric; scope-typed equivalence | canonical entity identifiers or externally supported alias map | same label is insufficient |
| `EXACT_ISOMORPHISM` | symmetric and composable when maps/scopes compose | invertible structure-preserving map | exact representation identity does not imply mechanism identity |
| `SAME_GENERATOR` | symmetric within declared stochastic/dynamical generator scope | generator equality/equivalence proof | generator equality does not imply same microscopic realization |
| `SAME_MECHANISM` | symmetric only at registered mechanism granularity | mechanism ancestry mapping | predictive agreement is insufficient |
| `SAME_OBSERVABLE` | symmetric under fixed measurement definition | observation-operator alignment | same observable does not imply same latent state |
| `OBSERVATIONALLY_EQUIVALENT` | symmetric; transitive only under the same observation family | equal observational law or bounded equivalence | cannot mint mechanism equivalence |
| `QOI_EQUIVALENT` | symmetric; local to a named QoI and context | same QoI value/distribution within tolerance | cannot be generalized to global equivalence |
| `MATHEMATICALLY_ISOMORPHIC` | equivalence when an actual isomorphism exists | explicit bijective mathematical map | mathematical isomorphism does not prove physical interpretation |
| `TRANSFORMABLE_TO` | directional unless inverse is shown | explicit transformation and domain | transformability is not identity |

### 4.2 JUMP relations

JUMP relations generate hypotheses and search routes. They do **not** directly merge atlas objects or create scientific authority.

| Relation | Default properties | Required witness | Default transfer status |
|---|---|---|---|
| `RELATIONALLY_ANALOGOUS` | not assumed transitive | role/relation mapping with systematic connected structure | proposal only |
| `CAUSALLY_ANALOGOUS` | directional transfer; not assumed transitive | mapped causal graph and intervention semantics | proposal only |
| `DYNAMICALLY_EQUIVALENT` | exact only when conjugacy/equivalence is proved; otherwise scoped analogy | state/evolution map plus regime | proposal or GLUE only at proved layer |
| `FUNCTIONALLY_ANALOGOUS` | not assumed transitive | same registered function with different realization allowed | proposal only |
| `SAME_FAILURE_MODE` | not assumed transitive | failure signature and triggering-condition map | proposal only |
| `SAME_REGIME_STRUCTURE` | scoped and generally non-transitive | phase/regime-transition correspondence | proposal only |
| `ASYMPTOTICALLY_EQUIVALENT` | composition requires compatible limits and error control | limit map plus remainder/error statement | local relation only |
| `APPROXIMATELY_EQUIVALENT` | pairwise by default | tolerance, metric, regime and error bound | local relation only |
| `DUAL_OF` | properties depend on the declared duality | explicit duality map | no generic closure |
| `LIMIT_OF` | directional | limiting operation and assumptions | no generic inverse |
| `GENERALIZES` | directional; transitivity requires definition/scope compatibility | inclusion/specialization map | no automatic authority upgrade |
| `SPECIAL_CASE_OF` | inverse of a licensed `GENERALIZES` edge | parameter/restriction map | no automatic authority upgrade |
| `BRIDGE_TO` | directional path-level search relation | one or more witnessed intermediate mappings | retrieval/navigation only |

A relation may live in both spaces only when its authority is explicitly scoped. For example, a proved mathematical isomorphism may GLUE two mathematical representations while simultaneously serving as a JUMP bridge between physically different systems.

## 5. Retrieval is not recognition is not transfer is not validation

RAKL separates four gates:

```text
DISCOVER candidate
  -> WITNESS structural correspondence
  -> PROPOSE transferable inference/intervention
  -> VALIDATE in the target domain
```

States are:

```text
CANDIDATE_BRIDGE
WITNESSED_ANALOGY
TRANSFER_HYPOTHESIS
TARGET_VALIDATED
TARGET_REFUTED
TARGET_PARTIALLY_IDENTIFIED
BLOCKED
CANNOT_CHECK
```

Failure at each gate is recorded separately. A distant paper may be present in the corpus but not retrieved. A retrieved paper may fail structural mapping. A valid structural mapping may suggest an intervention that fails because a target-specific constraint was omitted. None of these are the same failure.

This lifecycle enforces the constitutional rule `LLM proposes; evidence governs`: analogy proposes; target evidence authorizes.

## 6. Abstraction ladder and erasure ledger

Every atomic concept can be projected through a controlled abstraction ladder:

```text
L0 exact wording / terminology
L1 domain concept
L2 functional description
L3 causal or mechanistic schema
L4 relational / typed graph
L5 mathematical / dynamical schema
L6 domain-independent structural pattern
```

Abstraction is itself a lossy transformation. Each step therefore carries an **erasure ledger**:

```text
removed entities
removed material/substrate assumptions
removed scale and units
removed boundary conditions
removed causal direction
removed stochastic structure
removed conservation laws
removed intervention semantics
```

A domain-stripped query is allowed to increase recall, but transfer cannot be authorized when an erased coordinate could change the target conclusion. The ladder is therefore a retrieval instrument, not an epistemic shortcut.

## 7. Coarse-to-fine search architecture

RAKL separates broad candidate generation from expensive structural recognition.

### Stage A — multi-view retrieval

Retrieve from multiple projections independently:

- lexical and terminology variants;
- semantic embeddings;
- ontology/entity graphs;
- causal/mechanism schemas;
- equation and invariant signatures;
- reasoning/relational graphs;
- citation ancestry;
- failure/regime signatures;
- domain-stripped L2-L6 queries.

This stage optimizes recall and diversity.

### Stage B — structural mapping

For the smaller candidate set, construct explicit witnesses and test:

- one-to-one role consistency where required;
- relation preservation;
- higher-order/systematic connected structure;
- causal orientation;
- equation/boundary compatibility;
- regime overlap;
- preserved and non-preserved correspondences.

### Stage C — transfer analysis

Generate only the inference, experiment, algorithm or intervention actually supported by the preserved part of the mapping.

### Stage D — target validation

Freeze falsifiers before testing the transferred hypothesis. A successful source-domain analogy is not target-domain evidence.

## 8. Scientific jump selection is multi-objective

A single score such as

\[
S_{deep}+\alpha D_{surface}
\]

is useful as a diagnostic but can be gamed by extreme remoteness or arbitrary weights. RAKL instead keeps a **Scientific Jump Vector**

\[
J(A,B\mid q)=
(S_{deep},D_{surface},U_{transfer},E_{readiness},R_{risk},C_{cost}).
\]

Here:

- `S_deep` — preserved relational/causal/mathematical structure;
- `D_surface` — lexical/domain distance;
- `U_transfer` — expected decision-relevant transfer value;
- `E_readiness` — availability of evidence needed to test the transfer;
- `R_risk` — false-analogy / omitted-coordinate risk;
- `C_cost` — search, mapping and validation cost.

Candidate jumps are maintained on a **Pareto frontier** subject to minimum structural-witness constraints. This prevents one arbitrary scalar from erasing meaningful tradeoffs.

## 9. Multi-hop bridges

A useful jump may require

\[
A\xrightarrow{\tau_1}B\xrightarrow{\tau_2}C.
\]

RAKL does not infer `A tau C` automatically. A path certificate must state:

1. the invariant preserved on every hop;
2. whether the mapped roles at the shared node `B` are compatible;
3. accumulated approximation/error;
4. scope/regime intersection;
5. which transfer claims survive composition.

`BRIDGE_TO` therefore denotes navigability, not equivalence. A broken intermediate correspondence invalidates the composed transfer even when each pair looks individually plausible.

## 10. Similarity fingerprint

For diagnostics, each witnessed pair may expose a vector rather than one number:

```text
identity
attribute
relational
causal
mechanistic
dynamical
mathematical
functional
observational
regime
failure
transformational
```

The fingerprint is always conditioned on `q` and accompanied by the mapping witness. High mathematical similarity and low mechanism similarity is a valid result, not a contradiction.

## 11. Main adversarial failure modes

```text
SURFACE_FALSE_FRIEND       words look similar, deep structure differs
EQUATION_FALSE_FRIEND      equations share form, semantics/boundaries differ
ABSTRACTION_OVERSTRIP      domain stripping removes a decision-critical coordinate
ROLE_COLLAPSE              distinct causal roles mapped to one target role
DIRECTION_FLIP             causal or temporal orientation is reversed
REGIME_LEAK                analogy applied outside mapped validity regime
TRANSFER_OVERREACH         inference exceeds preserved structure
BRIDGE_COMPOSITION_LEAK    multi-hop path silently changes the invariant
ANALOGY_AUTHORITY_LEAK     candidate analogy promoted as evidence
DISTANCE_GAMING            remoteness rewarded despite weak transfer value
```

Negative analogy results are retained because rejected bridges improve future retrieval and calibration.

## 12. Paper-level claim

RAKL does not claim novelty for analogy, structure mapping, graph retrieval, semantic distance rewards or cross-domain hypothesis generation individually. The candidate contribution is narrower:

> RAKL treats similarity as a witnessed, typed and scoped relation inside an evidence-governed scientific atlas, explicitly separates conservative gluing from exploratory jumping, preserves abstraction losses and broken correspondences, and prevents analogical transfer from acquiring target-domain authority before validation.

This claim remains provisional until adversarial prior-art review and benchmark execution are complete.
