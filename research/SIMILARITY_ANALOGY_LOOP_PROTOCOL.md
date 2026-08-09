# RAKL Similarity, Analogy, and Scientific-Jump Research Lane

Status: repository-owned recurring research protocol  
Date: 2026-08-09  
Priority: active until semantically saturated

This file makes the current similarity/analogy research lane recoverable from GitHub alone. External schedulers are transport; this repository is the durable specification of what the lane is trying to learn, how it must be reviewed, and what evidence is required before behavior changes.

The lane extends, rather than replaces, `docs/APPLE_PRINCIPLE.md`, `docs/SIMILARITY_ANALOGY_ALGEBRA.md`, `research/SELF_RAKL_RESEARCH_011.md`, and the frozen Round-011 benchmark.

## 1. The Apple Principle has two discovery operators

RAKL must solve two different problems.

### GLUE — more views of the same apple

Ask whether different papers, models, measurements, equations, or descriptions are compatible local projections of the same underlying object, entity, generator, mechanism, observable family, or quantity of interest.

GLUE is conservative because a false merge corrupts the Knowledge Atlas.

### JUMP — different objects preserving useful apple structure

Once an object has been reconstructed well enough to expose its relational, causal, mechanistic, dynamical, mathematical, functional, observational, regime, and failure structure, temporarily abstract away its domain identity and ask:

> Where else in science does this structure occur?

The target may use unrelated vocabulary and may belong to a distant discipline. JUMP is deliberately adventurous, but a jump remains a proposal until an explicit mapping witness is constructed and the transferred claim is validated in the target domain.

The operating asymmetry is:

> **Conservative gluing + adventurous jumping + evidence-gated transfer.**

## 2. Similarity is contextual and typed

There is no universal similarity relation. Every similarity claim is conditioned on a registered question or QoI `q`.

For an atomic object `x`, RAKL may represent

\[
\Sigma_q(x)=(E,R,C,M,D,F,O,B,A),
\]

where the coordinates include entities/roles, relations, causal dependencies, mechanisms, equations/dynamics/invariants, functions, observables, boundaries/regimes/assumptions, and affordances/interventions.

For diagnostics, a pair may expose a similarity fingerprint with at least:

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

The fingerprint is not authority. The primary object is the explicit mapping witness described in `docs/SIMILARITY_ANALOGY_ALGEBRA.md`.

A valid witness must state both what is preserved and what is not preserved, together with scope/regime, approximation or ambiguity, evidence, and falsifiers. A scalar score may rank candidates but must never replace the witness.

## 3. Relation algebra to maintain

The lane must continuously refine typed relations such as:

```text
SAME_OBJECT
SAME_ENTITY
EXACT_ISOMORPHISM
SAME_GENERATOR
SAME_MECHANISM
SAME_OBSERVABLE
OBSERVATIONALLY_EQUIVALENT
QOI_EQUIVALENT
APPROXIMATELY_EQUIVALENT
ASYMPTOTICALLY_EQUIVALENT
MATHEMATICALLY_ISOMORPHIC
TRANSFORMABLE_TO
RELATIONALLY_ANALOGOUS
CAUSALLY_ANALOGOUS
DYNAMICALLY_EQUIVALENT
FUNCTIONALLY_ANALOGOUS
SAME_FAILURE_MODE
SAME_REGIME_STRUCTURE
DUAL_OF
LIMIT_OF
GENERALIZES
SPECIAL_CASE_OF
BRIDGE_TO
```

For every relation, maintain or derive:

- source and target types;
- required mapping witnesses;
- preserved structure;
- allowed non-preserved structure;
- regime and assumption constraints;
- evidence requirements;
- confidence semantics;
- symmetry, transitivity, directionality, and explicit non-properties;
- legal composition rules;
- falsifiers;
- GLUE, JUMP, or dual-space authority.

Mathematical equivalence must not silently escalate into physical/mechanistic identity. Observational equivalence must not mint mechanism equivalence. QoI equivalence is local to the named decision or quantity.

## 4. Six-role expert panel is mandatory for this lane

Every material similarity-lane research round uses six role-separated review passes. These may be sequential AI roles in one orchestration context; they must not be misrepresented as independent humans or mutually blind reviewers unless they actually are.

1. **Cognitive-science / analogy expert** — structure mapping, systematicity, retrieval versus recognition, abstraction, remote analogy.
2. **Knowledge-representation / ontology expert** — typed graphs, ontology alignment, equivalence classes, relation algebra, composition.
3. **Scientific-information-retrieval expert** — lexical, semantic, graph, equation, causal and multi-stage retrieval; recall/precision tradeoffs.
4. **Applied-mathematics / dynamical-systems expert** — equations, invariants, symmetries, conjugacy, duality, limits, asymptotics, regimes and error propagation.
5. **Computational-creativity / search expert** — controlled domain distance, diversity, bridge discovery, non-greedy exploration and search portfolios.
6. **Adversarial scientific-method reviewer** — false analogy, broken correspondence, invalid transfer, omitted variables, authority leakage and decisive falsifiers.

Each material finding should be examined by at least two relevant roles. Disagreements must be recorded rather than averaged away. The adversarial reviewer must state what observation, counterexample, regime violation, or broken mapping would invalidate the proposed correspondence.

## 5. Abstraction ladder: remove nouns without removing science

Every atomic object may be projected through multiple abstraction levels:

```text
L0 exact wording / terminology
L1 domain concept
L2 functional description
L3 causal / mechanistic schema
L4 relational / typed graph
L5 mathematical / dynamical schema
L6 domain-independent structural pattern
```

The purpose is to escape the semantic neighborhood. A domain-specific statement can be transformed into a role-and-relation schema, searched in foreign vocabularies, and then re-instantiated into candidate domains.

A useful operational technique is controlled noun removal: replace domain entities with typed roles while preserving predicates, direction, constraints, units where essential, invariants, boundary conditions, stochastic assumptions, and intervention semantics.

Example pattern:

```text
domain statement
-> functional statement
-> causal schema
-> relational graph
-> mathematical/invariant schema
-> domain-independent pattern
-> foreign-domain re-instantiation
-> candidate retrieval
```

Abstraction is lossy. Every level transition therefore carries an **erasure ledger** recording what was removed. If an erased coordinate can change the transfer conclusion, the abstraction can support retrieval but cannot authorize transfer.

## 6. Retrieval and recognition are different atomic problems

RAKL must not assume that a model able to recognize a deep analogy when two examples are shown together can also retrieve the distant analogue from a large corpus.

Use a coarse-to-fine architecture:

### Broad divergent retrieval

Search independent views, including:

- exact and alternative terminology;
- semantic embeddings;
- ontology/entity graphs;
- causal/mechanistic schemas;
- equations and invariant signatures;
- relational/reasoning graphs;
- citation ancestry;
- failure-mode and regime signatures;
- L2-L6 domain-stripped queries;
- adjacent-domain and deliberately alien-domain vocabulary.

This stage optimizes recall and diversity.

### Structural recognition

For a much smaller candidate set, build explicit witnesses and test role consistency, relation preservation, systematic connected structure, causal orientation, equation/boundary compatibility, regime overlap, approximation error, and non-preserved correspondences.

### Transfer proposal

Generate only the hypothesis, algorithm, intervention, experiment, or inference licensed by the preserved part of the witness.

### Target validation

Freeze falsifiers before target testing. Source-domain analogy is not target-domain evidence.

The analogy lifecycle remains:

```text
CANDIDATE_BRIDGE
-> WITNESSED_ANALOGY
-> TRANSFER_HYPOTHESIS
-> TARGET_VALIDATED / TARGET_REFUTED / TARGET_PARTIALLY_IDENTIFIED / BLOCKED / CANNOT_CHECK
```

## 7. A scientific jump is deep closeness plus useful distance

Ordinary nearest-neighbor similarity drives the system back toward papers already using the same vocabulary. RAKL should deliberately preserve deep structure while allowing or rewarding surface/domain distance.

A diagnostic scalar such as

\[
S_{deep}+\alpha D_{surface}
\]

may be useful, but the default research object is multi-objective:

\[
J(A,B\mid q)=
(S_{deep},D_{surface},U_{transfer},E_{readiness},R_{risk},C_{cost}).
\]

Maintain non-dominated candidates on a Pareto frontier subject to minimum structural-witness constraints. Random remoteness receives no novelty credit.

The portfolio should preserve distinct lanes rather than greedily select one neighborhood:

```text
exploit      nearby, strongly evidenced mappings
diversify    moderately distant, complementary structure
moonshot     very distant, strong witness, high potential transfer value
meta-RAKL    candidates that improve retrieval/mapping itself
```

## 8. Multi-hop bridge search

Some useful concepts are not directly similar.

RAKL may search paths such as:

\[
A\xrightarrow{\tau_1}B\xrightarrow{\tau_2}C.
\]

Each hop must state the invariant or structure it preserves. Composition is legal only when intermediate roles are compatible, scope/regimes intersect, approximation/error is accumulated, and the transferable inference survives the path.

`BRIDGE_TO` is navigation, not equivalence. Pairwise similarity scores must never create automatic transitive closure.

## 9. Benchmarks must separate discovery, mapping, and transfer

Before promoting a runtime similarity/analogy method, freeze benchmark cases and meta-QoIs. The benchmark family should include at least:

- same-object / different-description GLUE;
- near-domain analogy;
- far-domain structural analogy with near-zero lexical overlap;
- equation-level equivalence under symbol renaming or coordinate transformation;
- causal-schema transfer;
- regime-limited equivalence;
- same failure mode across domains;
- misleading high-surface matches;
- equation false friends where form matches but semantics/boundaries do not;
- safe versus unsafe abstraction;
- retrieval-versus-recognition separation;
- correct analogy followed by failed target transfer;
- valid and invalid multi-hop bridge composition;
- distance gaming;
- analogy-to-authority leakage.

Measure at least:

```text
deep-analogy retrieval recall
GLUE precision / false-merge rate
mapping-witness correctness
preserved/non-preserved correspondence completeness
erasure-ledger completeness
regime/falsifier completeness
novelty/domain distance
transfer utility
invalid-transfer rate
calibration
analogy-authority leakage
cost/budget
```

Negative, null, refuted, partial-identification, and blocked results must be retained.

## 10. Recurring loop protocol

On every recurring run:

1. Fetch current `main`, recent commits, open issues/PRs, Constitution, SELF_RAKL ledger, Knowledge Atlas, saturation state, tests, frozen benchmarks, and prior receipts.
2. Select a materially different atomic angle of the same similarity/analogy problem. Do not repeat the same papers, examples, or abstraction without a new discriminator.
3. Convene the six-role panel and delegate material findings across roles.
4. Search current primary literature and high-quality open-source frameworks from multiple vocabularies/domains.
5. Extract source projections and deduplicate equivalent ideas before counting novelty.
6. Update the external-framework/semantic-novelty ledger and the relevant meta-fibers.
7. Design the smallest discriminating benchmark, query, experiment, ablation, or hostile case that can separate surviving explanations.
8. Freeze benchmark/meta-QoIs before observing implementation results.
9. Implement only the smallest research or code change needed to test the hypothesis.
10. Run all accessible relevant tests and record exact outcomes. Never call an unexecuted workflow a passing test.
11. Preserve supersession and negative history.
12. Commit safe research ledgers, docs, tests, code, and machine-readable receipts to `main` when repository governance permits.
13. Leave instructions for the next run under positive, null, refuted, partially identified, blocked, and transport-failure branches.

A new native residual or benchmark failure reopens the implicated fiber.

## 11. Saturation and stopping

Do not stop merely because one search vocabulary is flat. Track separately:

```text
required route coverage
same-context plateau
independent flat rounds
new benchmark/native residuals
```

A similarity sub-fiber is semantically flat only after deduplication across materially independent routes. Until then, successive runs should attack the same core problem from non-duplicative atomic angles.

If no meaningful semantic or implementation improvement is found, update a saturation receipt only when there is new measured evidence. Do not create cosmetic commits.

The recurring lane should remain enabled unless the user explicitly asks to pause or stop it.

## 12. Promotion and constitutional safety

The lane is research-first.

- Class A implementation or Class B workflow changes may be promoted only after the frozen benchmark, relevant tests, and blocking evidence invariants pass under the repository's governance rules.
- Do not weaken falsifiers or acceptance thresholds after seeing results.
- If execution is unavailable, record `CANNOT_CHECK` and do not activate unverified behavior.
- Constitutional changes are Class C: record them as explicit amendment proposals with independent/adversarial review; do not silently mutate the active axioms.
- Preserve the core rule: **LLM proposes; evidence governs.**

## 13. Canonical conceptual loop

The Apple Principle now supports both reconstruction and controlled imagination:

```text
GLUE
many local descriptions
-> explicit projection/context alignment
-> reconstructed deeper object

ABSTRACT
reconstructed object
-> typed roles/relations/mechanisms/invariants
-> L0-L6 projections + erasure ledger

JUMP
abstract structure
-> distant-domain retrieval
-> explicit structural witness
-> transfer hypothesis

TEST
frozen falsifier
-> target evidence
-> validate / refute / partially identify / block

GLUE AGAIN
new evidence
-> updated Knowledge Atlas
-> new residuals
-> recurse
```

In compact form:

\[
\boxed{
\text{GLUE}\to\text{ABSTRACT}\to\text{JUMP}\to\text{TRANSFER}\to\text{TEST}\to\text{GLUE}
}
\]

This is the intended engineering interpretation of scientific imagination in RAKL: not unrestricted association, but controlled relaxation of identity while preserving explicit structure and falsifiable transfer constraints.
