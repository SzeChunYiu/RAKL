# Round 047 — Open-world discovery and workspace hardening review

**Date:** 2026-08-10  
**Status:** same-context internal technical review. Not independent peer review.

## Review group

This round uses three fixed lenses with non-overlapping primary responsibilities.

1. **Formal-methods / knowledge-representation lens.** Audits type boundaries, lattice terminology, theorem preconditions, countermodels and novelty claims.
2. **Systems / verification lens.** Audits capability ownership, fail-closed behavior, capacity reservations, proposal-only permissions, provenance separation and regression coverage.
3. **Scientific-editorial / prior-art lens.** Audits Global Workspace and retrieval lineage, claim-local citations, source dates, J-space boundaries and publication scope.

The lenses share the final evidence ledger, so this is coordinated internal review rather than mutually blind external review.

## Findings and delegation

### R47-F1 — The current `TypedKnowledgeLattice` name overstates its implemented mathematics

**Formal finding.** The class stores typed atoms, pairwise compatibility witnesses and constructive paths; it does not implement a scoped partial order or meet/join laws. Calling that object an order-theoretic lattice would be unsupported.

**Systems repair.** Add `TypedCompatibilityComplex` as the preferred semantic name while keeping the historical class as a backward-compatible alias.

**Editorial repair.** Both manuscripts must state that "lattice" is reserved for proved local closure/poset structures and that J-space's union-of-cones geometry does not repair this gap.

**Disposition:** closed at terminology/API level; no new order-theoretic lattice theorem is claimed.

### R47-F2 — External discovery had route diversity but no complete owner/closure contract

**Formal finding.** The existing `discovery_coverage.py` safeguard is useful but cannot certify the v0.2 OWMD obligations: owner completeness, function signatures, lexical independence, historical/mathematical/methodological/citation/bridge/freshness routes, or explicit unresolved fibers.

**Systems repair.** Add `open_world_discovery.py`, the owner ledger, functional signature, bounded-closure audit, hidden-name scoring and discovery-workspace reservations.

**Editorial repair.** Replace "saturation" language with "bounded discovery closure" where the expanded contract is intended. Preserve the Obsidian and GWT misses as failure history rather than success anecdotes.

**Disposition:** closed as software/formal contract; prospective hidden-concept recall remains empirical.

### R47-F3 — A transient global workspace could accidentally become an authority channel

**Formal finding.** Computational access, atlas coherence and scientific authority are non-equivalent state coordinates.

**Systems repair.** `workspace.py` emits only immutable frames and `WorkspaceProposal` objects, reserves challenge/novel/history capacity, and keeps cognitive and evidential provenance in distinct types. It exposes no canonical update or authority mutator.

**Editorial repair.** State the non-authority result as a transition/write-capability theorem, not as evidence that the selected content is true.

**Disposition:** closed for the reference software transition surface; whole-system canonical promotion remains governed by the existing verification/promotion path.

### R47-F4 — GWT/J-space relation needed source-bound limits

**Source finding.** The 2026 Transformer Circuits work was published 6 July 2026; the arXiv posting is dated 16 July 2026. The paper explicitly focuses on functional access, takes no position on phenomenal consciousness, defines fixed-k J-space as a union of k-dimensional cones, and states that the mechanism causing representations to enter J-space has not been characterized.

**Editorial repair.** Cite the Transformer Circuits publication and arXiv identifier without conflating their dates. Reject `J-space = RAKL lattice` and any inference from workspace-like function to phenomenal consciousness.

**Disposition:** closed.

### R47-F5 — Publication closure must remain scoped

**Finding.** The current branch still has unexecuted matched-workflow, fresh self-evolution and real-science validation coordinates. Same-context review also cannot satisfy an independent-review gate.

**Repair.** The release language is "public methods/formalism/preregistration artifact", not empirical scientific-superiority certification or journal acceptance.

**Disposition:** scope boundary retained; those empirical fibers remain open.

## Internal recommendation before CI

**Proceed to exact-subject CI and PR review.** The hardening is publishable as a scoped methods/formalism release if and only if the branch's exact-subject test and LaTeX gates are green. Any failing software or manuscript build reopens this recommendation.
