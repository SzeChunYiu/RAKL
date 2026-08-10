# Epistemic Mechanics — bounded saturation ledger

**Date:** 2026-08-10  
**Branch:** `epistemic-mechanics-longform-v1`  
**Status:** two consecutive substantively flat discovery/review rounds achieved after the most recent claim-changing assimilation. Exact-subject CI, render review and Nature-skills publication review remain separate release gates.

This ledger applies the project rule “accumulate knowledge until it stops growing” to the long-form *Epistemic Mechanics* manuscript. “Stops growing” means that deliberately different expansion passes no longer change any registered substantive epistemic coordinate under the frozen saturation basis. It does **not** mean unrestricted scientific completeness.

## Frozen saturation basis

- basis id: `epistemic-mechanics-longform-v1`
- scope: long-form *Epistemic Mechanics* paper plus supporting RAKL epistemic-saturation framework
- identity policy: `claim-mechanism-evidence-v1`
- discovery family: `owmd-v1+operator-order-v1`
- novelty policy: `nearest-work-equivalence-v1`
- evidence policy: `typed-authority-v1`
- basis fingerprint: `f492101689233e60d04b3691ecdf6df3e7b1ab6ca0028db4c6936cddf82d7942`
- freshness cutoff: 2026-08-10

The substantive growth vector is ordered as:

`(mechanisms, derivations, independent evidence roots, contradictions/counterexamples, negative results, novelty-boundary updates, assumption/scope updates, unresolved-fiber updates, discovery-route updates)`.

Representation-only edits are tracked separately and do not count as epistemic growth.

## Non-flat assimilation rounds

### EM-GROW-01 — long-form theory reconstruction

**Result:** non-flat.

The former short formal note was expanded into the primary theory paper. New state included the closure-system lattice theorem, three-context parity obstruction, scalar-inadequacy theorem, workspace optimization theorem, finite-basis saturation theorem, exact pendulum derivation and a broad foundations/prior-art map. The paper was split into modular TeX sections and the build was made deterministic.

### EM-GROW-02 — open-world graph and search-stopping route

**Result:** non-flat.

Open-world knowledge-graph completion and modern systematic-review stopping work changed the paper's stopping interpretation. The manuscript now distinguishes an unknown fact from a false fact and distinguishes raw document recall from decision-relevant evidence sufficiency. Fixed-point provenance with negation further narrowed the novelty boundary around provenance and saturation.

### EM-GROW-03 — claim/evidence provenance route

**Result:** non-flat.

Claim-level provenance, structured scientific-evidence representations, provenance verification, open-domain scientific claim verification and claim/evidence scholarly interfaces were assimilated. The paper now explicitly states that RAKL does not invent claim decomposition, claim provenance, evidence attribution, source retrieval or support/refute classification.

### EM-GROW-04 — mathematical-equivalent / FCA route

**Result:** non-flat.

The nearest-work search found retrieval-grounded Formal Concept Analysis with counterexample-driven verified knowledge expansion (Yang & Lee, arXiv:2607.01773), plus older local-to-global consistency and lattice-based knowledge-representation lineages. This forced a sharper novelty boundary: closure-based verified knowledge expansion is prior art; RAKL's contribution lies in the added evidence-authority, obstruction, workspace, open-world-route and saturation-governance composition.

### EM-GROW-05 — agent-native publishing route

**Result:** non-flat.

Traxia (arXiv:2606.08256) occupies verifiable agent-native scientific artefacts, provenance, contradiction handling and structured publication/review. The paper now treats these functions as prior art and narrows its contribution to controlled scientific-state transition and the multidimensional authority/saturation discipline. Traxia's composite confidence score also sharpened the distinction between a policy scalar and the underlying partial epistemic order.

### EM-GROW-06 — recursive-state termination route

**Result:** non-flat.

Guha et al., *State Representation and Termination for Recursive Reasoning Systems* (arXiv:2605.06690), and the companion *Consolidation-Expansion Operator Mechanics* (arXiv:2605.09968) directly occupy explicit reasoning-state + order-sensitive stopping. This discovery changed the framework itself: `OperatorOrderAudit` was added to `src/rakl/epistemic_saturation.py`, the JSON schema and tests. A bounded saturation certificate now fails if reversing expansion/consolidation changes any substantive growth coordinate.

The same round assimilated Epistemic State Replication (arXiv:2607.09748) as prior art for immutable evidence / stochastic belief separation and the 2026 PNAS trustworthiness framework as an external multidimensional trustworthiness lineage.

## Consecutive flat rounds

### EM-FLAT-01 — label-masked termination/saturation perturbation

**Question:** With framework labels removed, can another mechanism be found that changes the registered function owner or novelty boundary for persistent evidence state + expansion/consolidation + endogenous stopping?

**Routes:** exact and functional paraphrase, historical “saturation” terminology, recursive-reasoning termination, fixed-point/consolidation variants.

**Outcome:** substantively flat. Results either returned the already-assimilated Guha/OpMech lineage or older uses of “saturation” that did not change a mechanism owner, theorem assumption, evidence root, contradiction, novelty boundary, scope, unresolved fiber or required discovery route.

**Growth vector:** `(0,0,0,0,0,0,0,0,0)`.

### EM-FLAT-02 — adversarial multidimensional-authority / local-to-global route

**Question:** Can a mature formalism subsume either (a) the paper's local-to-global obstruction boundary or (b) its claim that multidimensional epistemic authority cannot be faithfully replaced by a single total-order scalar?

**Routes:** modern local/global consistency, evidence/assurance confidence, partial-order and multidimensional trustworthiness terminology.

**Outcome:** substantively flat. Atserias & Kolaitis, *Consistency of Relations over Monoids* (JACM 72(3), 2025, DOI `10.1145/3721855`) gives a substantially deeper local-to-global consistency theory, but it reinforces rather than changes the already registered Dechter/sheaf/local-global lineage and the paper's deliberately modest parity counterexample. Bloomfield & Rushby's *Assessing Confidence with Assurance 2.0* (arXiv:2205.04522) explicitly argues that confidence is not one attribute and separates positive, negative and residual doubts; this independently supports, but does not alter, the paper's existing multidimensional-authority boundary or scalar-impossibility theorem.

Neither result changed the paper's mechanism ownership, theorem statements, evidence roots needed for its claims, novelty boundary, scope assumptions, unresolved fibers or discovery-route obligations. Adding them merely to increase citation count would be bibliographic growth without epistemic growth, so they are recorded in this audit rather than forced into the manuscript.

**Growth vector:** `(0,0,0,0,0,0,0,0,0)`.

## Operator-order perturbation

The final saturation suffix also requires the expansion/consolidation perturbation introduced after EM-GROW-06. For the final claim/evidence/novelty map, reversing the order of the literature-expansion pass and the formal consolidation pass changed representation/order metadata but did not change any of the nine substantive growth coordinates after all EM-GROW-06 repairs were assimilated. The structured record is stored in `research/EPISTEMIC_MECHANICS_SATURATION_v1.json`.

This is an internal same-context audit, not an independent external replication. Its role is to prevent one scheduling of the research loop from masquerading as convergence.

## Saturation decision

The manuscript has reached the project's **bounded epistemic saturation candidate** condition: two consecutive heterogeneous passes produced zero substantive growth under the frozen basis, the nearest-work boundary has been adversarially updated, and the operator-order perturbation is substantively stable.

This ledger does not itself authorize release. The saturated source must still satisfy exact-subject software tests, bibliography/source guards, strict PDF preflight, render inspection and a final Nature-skills review. Any substantive change found by those gates resets the flat-round suffix and reopens saturation.
