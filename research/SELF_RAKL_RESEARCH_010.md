# SELF-RAKL Research Round 010 — Authority Poset and Novelty Narrowing

Date: 2026-08-09

Initial observed `main`: `40562e2039a1f88dfdd520f65c7d5301f5d2990b`

Concurrent/rebased `main`: `fb05e43a7c742f5e96a871d05d9ede3690ad4bf0`

Entering global status after deduplicating the concurrent Round-009 theory commit: `ACTIVE_NON_FLAT`.

## Frozen expert panel

1. **Formal epistemologist** — evidence authority, belief revision and partial identification. Task: determine whether scientific authority is total, scalar, or partially ordered.
2. **Philosophy-of-science researcher** — prediction versus explanation/mechanism and underdetermination. Task: identify invalid cross-layer authority upgrades.
3. **Mathematical structures researcher** — order theory and typed relations. Task: define the minimum order structure without assuming unjustified lattice joins.
4. **Autonomous-science researcher** — 2026 agent verification and scientific-agent literature. Task: search for systems that already separate proposal, evidence and commitment.
5. **Hostile novelty reviewer** — fresh prior-art attack. Task: refute or narrow RAKL publication claims rather than support them.

## 1. Concurrency result

During this run, `main` moved from the Round-008 validation commit to `fb05e43...`, which added the Round-009 theoretical framework and paper claim registry.

The stale tree was not pushed. The new head was fetched, the theory was re-read, and planned artifacts were semantically deduplicated against the concurrent work.

This prevented a duplicate/stale theory commit and is itself consistent with the repository's subject/concurrency discipline.

## 2. Fresh prior art materially narrows the theory claim

A new August 2026 source, **The LLM Proposes, the Executive Disposes** (arXiv:2608.04066), explicitly gives a deterministic executive ownership of belief/commitment while an LLM files typed proposals.

Other recent work independently narrows generic evidence-governance claims:

- **Evidence-Graded Decision Authorization** licenses claim/action types according to evidence level;
- **EG-VAR** makes a formal kernel the sole minter of Verified claims descending from attested tool calls, with abstention otherwise;
- **GAVEL** binds atomic subclaims to exact evidence units and applies mechanized citation/span scrutiny;
- agent-provenance work surveys evidence tracing from retrieval/tool/memory units to claims and actions.

Therefore:

> `LLM proposes; evidence governs` remains a RAKL constitutional invariant, but it is not a defensible standalone novelty claim.

The Round-009 T002 claim is preserved as a formal RAKL obligation and narrowed explicitly in `RAKL_PAPER_THEORY_CLAIM_REGISTRY_002.json`.

## 3. Surviving theoretical residual: scientific authority is a poset

Round 009 already says authority is scoped and not one confidence score. The unresolved atomic question is what structure replaces the scalar.

The panel found that the cleanest current theory is a scoped authority certificate

\[
\alpha_s(c)=(G_c,R_c,M_c,I_c,D_c),
\]

where the coordinates encode certified grounding/provenance, representation/relation, mechanistic ancestry, identification/bounding and decision/QoI authority.

These are sets of licensed propositions/certificates rather than arbitrary scores.

For the same scoped claim, authority states are ordered componentwise when one state's certificates are all preserved/strengthened by the other. Cross-coordinate tradeoffs create incomparability.

Examples:

```text
predictive black box:
  strong D, possibly strong G
  weak/empty M

mechanistic but non-identified model:
  strong M
  set-valued I

robust decision across multiple mechanisms:
  strong D for one Q
  unresolved M/I
```

This opens `META_N035_MULTI_AXIS_SCIENTIFIC_AUTHORITY_POSET`.

## 4. Why the theory uses a poset, not automatically a lattice

RAKL should not assume that every pair of authority states has a scientifically meaningful join.

If two certificates rely on incompatible contexts or assumptions, forcing a least upper bound would erase the obstruction.

This matters especially because the project name includes `Knowledge Lattice`: the knowledge search space may be lattice-like while epistemic authority remains only partially ordered in general.

A lattice structure can be claimed only for a subspace where valid meet/join operators are actually proved.

## 5. Axis-specific certificate minting

The evidence gate is refined conceptually to issue certificates only on the axis it establishes.

Default non-escalation examples:

\[
\Delta R_{obs}\not\Rightarrow\Delta M,
\]

\[
\Delta D\not\Rightarrow\Delta M,
\]

\[
\Delta M\not\Rightarrow\Delta I.
\]

An evidence source that proves artifact identity can strengthen grounding/provenance without proving the scientific contents of the artifact.

A cross-axis transition requires an explicit inference rule with assumptions and target scope.

## 6. Important distinction: active authority is not monotone

A new refutation can withdraw a previously active certificate. Therefore the active authority vector/poset state need not increase monotonically.

The monotone object is negative/supersession history:

\[
\mathcal H^-_t\subseteq\mathcal H^-_{t+1}.
\]

This separates rational scientific correction from evidence deletion.

## 7. Publication claim registry update

The original registry remains unchanged. Registry 002 supersedes it by narrowing claims under the new evidence cutoff.

Most importantly:

- T002 is reclassified as `FORMAL_RAKL_OBLIGATION_PRIOR_ART_OVERLAP_STRONG_NOT_NOVELTY`;
- T001 remains only a conjunction-level method novelty hypothesis;
- new T009 registers `MULTI_AXIS_SCIENTIFIC_AUTHORITY` as a candidate theory contribution with its own prior-art and empirical falsifiers.

This is novelty revision by evidence rather than rhetorical defense.

## 8. Semantic novelty after deduplication

Retained non-duplicate objects:

1. `MULTI_AXIS_SCIENTIFIC_AUTHORITY_POSET`
2. `AUTHORITY_POSET_NOT_ASSUMED_LATTICE`
3. `AXIS_SPECIFIC_CERTIFICATE_MINTING`
4. `PROPOSAL_AUTHORITY_NOVELTY_NARROWING`

The generic proposer/evidence split, atomic evidence binding, verified-claim minting and provenance tracing are not counted as new.

Therefore:

```text
RAKL_METHOD = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

No saturation counter advances.

## 9. No runtime activation this round

This is a theory/research-only change.

No Constitution, source module, test, evaluator workflow, promotion gate or active authority API is modified.

The new poset must face a frozen benchmark before any runtime representation replaces or augments current authority semantics.

## 10. Next discriminator

Freeze N035 known-answer worlds before implementation:

1. predictive black-box versus mechanism authority;
2. mechanistic derivation with set identification;
3. decision closure across unresolved mechanisms;
4. artifact identity without truth authority;
5. observational/QoI equivalence without mechanism upgrade;
6. refutation that removes active authority while preserving history.

Primary metric for N033 should add **cross-axis authority leakage rate**.

If a simpler scoped-label system matches the poset on all frozen worlds, preserve the null and keep the poset as explanatory paper notation rather than runtime complexity.
