# Open-World Mechanism Discovery and Workspace-Gated Research Cognition

**Status:** implementation contract for RAKL v2.2 hardening  
**Date:** 2026-08-10  
**Scope:** software/formal architecture. This document does not establish empirical superiority, phenomenal consciousness, or absolute open-world completeness.

## 1. Failure being repaired

The Global Workspace miss exposed a class-level failure rather than one missing citation. Recursive search can become **ontology-conditioned closure**: child fibers inherit the parent vocabulary and conceptual neighborhood, so depth increases while genuinely independent discovery directions do not.

RAKL therefore separates:

\[
\boxed{\text{computational access}\neq\text{global coherence}\neq\text{epistemic authority}.}
\]

A workspace may determine what is active. Atlas/gluing logic determines what is coherent. Evidence plus verification determines what may acquire scientific authority.

## 2. Open-World Mechanism Discovery (OWMD)

`src/rakl/open_world_discovery.py` implements a bounded discovery audit around a **capability-owner ledger**.

A required function is represented by a vocabulary-independent signature

\[
\sigma(f)=(I,O,C,R,D,X),
\]

covering inputs, outputs, constraints, relations, dynamics/control behavior, and failure/intervention signatures. A function is not "owned" merely because a subsystem label exists. `CapabilityOwnerRecord` requires mechanism identity, scope, preconditions, postconditions, evidence, tests and failure semantics.

The default route ensemble covers:

1. exact terminology;
2. lexical variants;
3. function-only search;
4. historical precursors;
5. mathematical equivalents;
6. implementation analogues;
7. methodology-inspiration retrieval;
8. citation-neighborhood expansion;
9. literature bridges;
10. adversarial alternatives;
11. freshness;
12. cross-language expansion when applicable.

At least one completed route must be lexically independent of the current core vocabulary. Citation-neighborhood expansion must satisfy its declared stability rule, and every bounded-closure certificate records a freshness cutoff.

`audit_bounded_discovery_closure()` returns only `OPEN` or `BOUNDED_CLOSED`. Absolute open-world completeness is intentionally not representable as a positive result. Closure additionally requires an owner or an explicit open fiber, independent omission review, nearest-work equivalence audit, and preservation of unresolved candidates.

### Candidate assimilation

A retrieved mechanism is classified as one of:

`EQUIVALENT`, `SUBSUMED`, `COMPLEMENTARY`, `CONFLICTING`, `NOVEL_RESIDUAL`, or `UNRESOLVED`.

Prior art that already performs a required function must narrow the RAKL novelty claim; it cannot be relabeled as a RAKL invention.

## 3. Discovery Workspace

Open-world retrieval can still fail if only locally relevant candidates receive attention. `select_discovery_workspace()` therefore uses hard capacity reservations for `REMOTE`, `CHALLENGE`, `HISTORICAL`, and `FRESH` candidates before global-priority fill. A missing reserved partition fails closed rather than silently reallocating all capacity to near/relevant material.

This workspace is a comparison surface, not a truth engine.

## 4. General research workspace

`src/rakl/workspace.py` implements a transient, capacity-bounded selection-and-broadcast layer.

A candidate has:

- a stable item id and canonical content pointer;
- a partition (`CORE`, `CHALLENGE`, `NOVEL`, `HISTORY`);
- a computational priority;
- typed downstream broadcast targets.

The default gate reserves capacity for challenge, novelty and negative/history material. Selection returns an immutable `WorkspaceFrame` containing selected items, a broadcast map and a selection ledger.

The only downstream object directly produced by workspace broadcast is a `WorkspaceProposal`. Neither `WorkspaceFrame` nor `WorkspaceProposal` contains scientific-authority write capability. Canonical promotion remains outside this module and continues to require the repository's verification/promotion gates.

### Non-authority invariant

For any workspace-only transition \(\tau_W\), if no authority certificate passes through the canonical verification/promotion path, then an authority increase is not licensed:

\[
\neg\exists\chi^{\mathrm{auth}}_{t+1}(a)
\Longrightarrow
\alpha_{t+1}(a)\not\succ\alpha_t(a).
\]

The implementation enforces the narrow software side of this claim by construction: workspace operations only select, intervene on, broadcast and generate proposals.

### Coactivation is not gluing

`coactivation_pairs()` returns computational co-presence only. It creates no `CompatibilityWitness`, atlas transition, gluing certificate, truth judgment or authority certificate:

\[
a,b\in W_t \not\Rightarrow a\bowtie b
\quad\text{and}\quad
a,b\in W_t\not\Rightarrow a\vee b\text{ exists}.
\]

### Provenance separation

`CognitiveProvenanceEdge` records which active workspace item affected which downstream proposal under an optional intervention. `EvidentialProvenanceEdge` is a distinct type for evidence-to-claim verification lineage. Computational load-bearing influence is not scientific evidence.

## 5. Lattice terminology boundary

The historical `TypedKnowledgeLattice` implementation stores typed atoms, pairwise compatibility witnesses and constructive paths. Those operations do not by themselves define an order-theoretic lattice.

`src/rakl/compatibility_complex.py` therefore exposes the same object under the semantically precise name `TypedCompatibilityComplex` while retaining `TypedKnowledgeLattice` as a backward-compatible alias.

A future mathematical lattice claim requires a separately scoped partial order plus verified meet/join laws, or a closure operator whose fixed points form a lattice. The J-space result does not supply those obligations: its fixed-\(k\) geometry is defined as a union of cones generated by sparse non-negative combinations of J-lens vectors.

## 6. GWT-OMISSION-01 regression

`tests/test_open_world_discovery.py` contains the executable contract for the hidden-name regression.

The function-only route is given only this family of behavior:

- many processes operate in parallel;
- a small subset is admitted competitively;
- capacity is bounded;
- selected content is broadly reusable;
- active content can persist, be displaced or be evicted;
- intervention on active content can alter later decisions;
- prominence does not establish truth.

The withheld terms include `global workspace`, `consciousness`, `J-space` and `blackboard`. The benchmark passes only when ontology-independent route provenance reaches all registered mechanism classes without leaking withheld names into the independent query.

This unit benchmark validates the **software contract for scoring a hidden-name retrieval run**. It does not claim that a live retriever has already achieved prospective recall on fresh unknown concepts; that remains an empirical validation coordinate.

## 7. Global Workspace/J-space source boundary

The workspace lineage predates RAKL. Relevant prior work includes blackboard control architectures, Global Workspace/Global Neuronal Workspace accounts, the Consciousness Prior, shared neural global-workspace architectures, and the 2026 Jacobian-lens/J-space study.

The 2026 study is used narrowly:

- it studies a functional notion related to access consciousness and takes no position on phenomenal consciousness;
- it reports reportability, directed modulation, internal reasoning, flexible generalization and selectivity;
- for fixed sparsity \(k\), J-space is a union of \(k\)-dimensional cones, not by that definition an order-theoretic lattice;
- it explicitly leaves the mechanism causing a representation to enter J-space uncharacterized.

Therefore RAKL rejects both `J-space = RAKL lattice` and `workspace-like processing => phenomenal consciousness`.

## 8. Closure boundary

This hardening closes a **formal/software ownership gap** for bounded discovery and transient workspace control. It does not close:

- prospective hidden-concept recall on fresh worlds;
- empirical scientific-superiority claims;
- the preregistered matched-workflow experiment;
- fresh self-evolution transfer;
- real-domain case-study validation;
- independent external peer review.

Those remain explicit release/evidence fibers rather than being converted into prose claims.
