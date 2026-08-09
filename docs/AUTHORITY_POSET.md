# RAKL Scientific Authority Poset

Status: theory supplement, v0.1. This document does not amend the Constitution and does not change active runtime behavior.

## 1. Motivation

RAKL already states that scientific authority is scoped rather than a scalar confidence score. The publication theory needs a sharper object because scientific claims can be strong in one sense and weak in another.

Examples:

```text
high predictive validity / weak microscopic mechanism
strong mechanistic ancestry / weak parameter identification
multiple unresolved mechanisms / one robust downstream decision
exact software-content identity / no scientific truth authority
many corroborating papers / one shared evidence lineage
```

A single rank or confidence number cannot faithfully preserve these incomparabilities.

## 2. Scoped authority certificate

For claim/model `c` under scope

\[
s=(O,\gamma,Q,B),
\]

where `O` is the object, `gamma` the scientific context, `Q` the registered consumer/QoI and `B` the evidence cutoff, define an authority certificate

\[
\alpha_s(c)=(G_c,R_c,M_c,I_c,D_c).
\]

The coordinates are not arbitrary numeric scores. Each is a set of explicitly licensed propositions/certificates.

### Grounding coordinate `G`

Examples:

```text
SOURCE_SPAN_SUPPORT(source, span, claim)
EXECUTED_OBSERVATION(run, subject, result)
INDEPENDENT_REPRODUCTION(packet)
PROVENANCE_RESOLVED(entity, lineage)
```

`G` answers which parts of the claim are bound to externally inspectable evidence and provenance.

### Representation/relation coordinate `R`

Examples:

```text
SEMANTIC_EQUIVALENCE(scope)
EXACT_ISOMORPHISM(scope)
OBSERVATIONAL_EQUIVALENCE(observation_operator, scope)
QOI_EQUIVALENCE(qoi, scope)
APPROXIMATE_REPRESENTATION(bound, regime)
```

`R` records licensed translations and equivalence layers. Mixed relation types do not become one stronger relation merely by being connected in a path.

### Mechanism coordinate `M`

Examples:

```text
BUILDING_BLOCK_SUPPORTED(node)
INTERACTION_EDGE_SUPPORTED(u, v)
MECHANISM_ANCESTRY_SUPPORTED(path)
MICRO_TO_EFFECTIVE_MAP_SUPPORTED(scope)
```

`M` is about causal/mechanistic ancestry, not predictive success.

### Identification coordinate `I`

Examples:

```text
POINT_IDENTIFIED(parameter, scope)
SET_IDENTIFIED(object, identified_set, scope)
BOUND_IDENTIFIED(quantity, lower, upper, scope)
NON_IDENTIFIABLE(class, observation_operator)
```

`I` records what the evidence can distinguish, not which model sounds most plausible.

### Decision/QoI coordinate `D`

Examples:

```text
QOI_VALID(q, uncertainty_scope)
DECISION_USABLE(q, action, loss_scope)
ROBUST_DECISION(q, action, survivor_set)
```

`D` may be strong even when mechanism remains unresolved if every surviving model implies the same valid decision.

## 3. Partial order

For two authority states of the same scoped claim, write

\[
\alpha\preceq\beta
\]

when every certificate licensed by `alpha` remains licensed or is strengthened by `beta` on every relevant coordinate under compatible scope.

Operationally this can be represented as componentwise entailment/inclusion:

\[
G_\alpha\preceq G_\beta,\quad
R_\alpha\preceq R_\beta,\quad
M_\alpha\preceq M_\beta,\quad
I_\alpha\preceq I_\beta,\quad
D_\alpha\preceq D_\beta.
\]

Many pairs are intentionally incomparable.

Example:

```text
model A: strong mechanism ancestry, weak decision validation
model B: weak mechanism ancestry, strong robust decision validation
```

Neither globally dominates the other.

## 4. Poset, not assumed lattice

RAKL should not assume that every pair of authority states has a scientifically meaningful join.

If two certificates depend on incompatible assumptions or scopes, a forced least upper bound would erase the obstruction that matters scientifically.

Therefore the publication theory uses **authority poset** rather than `authority lattice` unless a particular subdomain proves valid meet/join operators.

The word `lattice` in Recursive Atomic Knowledge Lattice describes the structured knowledge search space; it does not license arbitrary algebraic joins of epistemic authority.

## 5. Axis-specific non-escalation

Authority transitions are licensed per coordinate.

The default rules include:

\[
\Delta R_{\text{observational}}\not\Rightarrow\Delta M,
\]

\[
\Delta D\not\Rightarrow\Delta M,
\]

\[
\Delta M\not\Rightarrow\Delta I,
\]

\[
\Delta G\not\Rightarrow\Delta M,
\]

and

\[
\text{more citations}\not\Rightarrow\text{more independent evidence authority}.
\]

A cross-axis transition is legal only when a registered inference rule states its assumptions, required evidence and target scope.

## 6. Evidence gate as certificate minter

An LLM or other proposer may request an authority upgrade, but it cannot mint the certificate.

For proposed certificate `z` on axis `k`, define

\[
V_k(z;E,s)\in\{\text{SUPPORTED},\text{REFUTED},\text{PARTIAL},\text{CANNOT\_CHECK}\}.
\]

Only `SUPPORTED` or explicitly scoped `PARTIAL` outcomes can change the active authority coordinate, and only to the demonstrated scope.

Recent evidence-gated agent frameworks make it especially important not to claim this generic proposal/verification separation as uniquely RAKL. RAKL's candidate contribution is the scientific **multi-axis** authority object and how it composes with the Knowledge Atlas, typed relation algebra, identified sets, semantic-lineage saturation and Self-RAKL governance.

## 7. Refutation and history

The active authority certificate is not monotone: new evidence can refute a previously licensed statement.

What is monotone is the history of authority events.

If a certificate is withdrawn, the ledger records:

```text
certificate issued
supporting evidence and scope
refuting/superseding evidence
withdrawal or narrowing event
new active certificate
```

Thus:

\[
\mathcal H^-_t\subseteq\mathcal H^-_{t+1}
\]

can hold even though active authority decreases.

## 8. Four known-answer examples

### 8.1 Predictive black box

A model predicts a QoI accurately on untouched data.

Permitted:

```text
G: external predictive evidence
D: scoped QoI/decision certificate if calibration/loss conditions pass
```

Not automatically permitted:

```text
M: microscopic mechanism authority
```

### 8.2 Mechanistic but unidentified model

A mechanistic derivation is physically coherent, but two parameter regimes induce the same observations.

Permitted:

```text
M: supported ancestry
I: set identification / non-identifiability
```

Not permitted:

```text
I: unique parameter identification
```

### 8.3 Decision closure without mechanism closure

Let survivor set `H` contain several mechanisms and suppose

\[
\forall h\in H,\quad d_Q(h)=d^*.
\]

RAKL may add

```text
D: ROBUST_DECISION(Q, d*, H)
```

without adding mechanism-identification authority.

### 8.4 Exact bytes are not scientific truth

A content hash proves two artifacts have identical bytes.

This can strengthen a provenance/identity certificate in `G` or a representation certificate in `R`. It does not by itself establish that any scientific assertion inside the bytes is true, mechanistic, identified or decision-usable.

## 9. Scalar-compression warning

A scalar confidence score can produce a linear extension of some authority comparisons, but it necessarily discards the distinction between scientific incomparability and ordinary ranking.

Therefore scalar confidence may be retained as a local heuristic within a coordinate, but it must never be the canonical cross-coordinate authority object.

## 10. Candidate proof and benchmark obligations

### AP-1 — Coordinate non-escalation

Evidence that changes only one coordinate cannot raise another coordinate without a registered cross-axis inference rule.

### AP-2 — Incomparability preservation

Known-answer worlds with mechanism/decision tradeoffs must not be collapsed to a false global rank when the consumer requires both dimensions.

### AP-3 — Decision-without-mechanism closure

If all survivors yield the same admissible decision, `D` may close while `M`/`I` remain unresolved.

### AP-4 — Refutation traceability

Withdrawing authority cannot erase the historical certificate and its evidence.

### AP-5 — Relation-scope containment

An `R` certificate at QoI or observational scope cannot silently become a global or mechanism certificate.

### AP-6 — Evidence-lineage containment

Resolving two supposedly independent evidence packets to shared ancestry cannot increase any independence-based authority certificate.

## 11. Publication boundary

Do **not** claim as RAKL inventions:

- evidence-gated output authorization;
- deterministic executives that separate LLM proposals from committed state;
- tool-attested or formally verified claims;
- atomic claim-to-evidence contracts;
- provenance-bearing agent traces.

The paper can instead test the narrower hypothesis:

> A multi-axis, partially ordered scientific authority state reduces cross-layer epistemic leakage when integrated with RAKL's local-view atlas, typed gluing rules, identified-set semantics, semantic-lineage saturation and governed self-improvement.

That hypothesis remains open until adversarial prior-art review and matched ablation benchmarks are completed.
