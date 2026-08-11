# Paper 5 internal adversarial review — Round 2: formal methods, security and governance

**Review status:** same-session internal adversarial review. This is not independent peer review.  
**Emphasis:** authority semantics, trusted computing base, self-certification risk, identity/provenance, state migration, evaluator integrity, rollback, prompt-injection/memory poisoning, and whether prose overstates current implementation.

## Overall assessment

The paper's strongest formal contribution is not a proof that self-improvement is safe. It is the explicit separation of proposal generation, evidence resolution, promotion authorization, active deployment attestation and rollback history. The manuscript is much stronger when it states the trusted computing base and names declaration-bound interfaces as current gaps. A reviewer should nevertheless reject any sentence that implies protected assurance is already fully self-resolving in v3. Several deployed evaluators are classifiers over supplied facts; the next hardening step is content-bound resolution of those facts.

## Major concerns

### R2-M1 — Deployment, assurance and promotion status were at risk of being conflated
- **Severity:** Major
- **Blocking:** Yes for self-evolution claims.
- **Axis:** claim-moderation / reproducibility
- **Claim pointer:** statements that v3 or a future version is "validated" because code is on `main` or because an assessor returns an evolution verdict.
- **Evidence pointer:** v3 merge history; Paper 5 Section 5.
- **Concern:** v3 was operationally merged before CI cleanup. More generally, a deployed commit and a scientifically supported method improvement are different predicates.
- **Resolution test:** state the four-way distinction `implemented != deployed != evidence-supported != governed incumbent`; preserve the merge-before-CI incident as operator override evidence; require post-promotion active-main attestation.
- **Status after revision:** RESOLVED in manuscript/upgrade protocol.

### R2-M2 — v3 variant promotion still accepts declaration-bound governance
- **Severity:** Major
- **Blocking:** Yes for autonomous/self-governed incumbent-promotion claims.
- **Axis:** ethical-governance / technical-soundness
- **Claim pointer:** strong language that the variant DAG prevents unsafe self-promotion.
- **Evidence pointer:** `src/rakl/evolution_archive.py::promote_incumbent(... governance_approved: bool)`.
- **Concern:** a caller Boolean is not evidence that a protected governance process approved the exact candidate. The archive correctly requires ASSURED status but does not resolve the governance fact.
- **Resolution test:** replace or wrap the Boolean with a content-bound attestation that resolves exact candidate, parent, assurance verdict, constitution epoch and approving process; preserve the current interface as an explicitly unhardened path until then.
- **Status after revision:** OPEN ENGINEERING GAP, explicitly disclosed. The paper does not claim it is solved.

### R2-M3 — SelfEvolutionAssessor/bootstrap fields are facts asserted to a classifier, not evidence resolvers
- **Severity:** Major
- **Blocking:** Yes if described as proof of assurance blindness, evaluator separation or lineage independence.
- **Axis:** technical-soundness / mechanism-evidence
- **Claim pointer:** fresh assurance is protected by current code.
- **Evidence pointer:** `EvolutionTrial` and `BootstrapTrial` Boolean fields.
- **Concern:** the evaluator is fail-closed given its inputs, but it does not independently observe that the assurance packet was hidden or that evaluator/evidence lineage is independent. A caller can pass `True` unless upstream resolution is separately protected.
- **Resolution test:** distinguish "classifier over observed facts" from "fact resolver"; future promotion-grade path must bind those observations to exact protected artifacts/observers.
- **Status after revision:** DISCLOSED in `PAPER5_IMPLEMENTATION_STATUS.md`; remains a future hardening item.

### R2-M4 — Gluing authority remains partially declaration-bound
- **Severity:** Major
- **Blocking:** Yes for theorem/root authority from v3 gluing.
- **Axis:** technical-soundness
- **Claim pointer:** local verified sections can compose into global solution authority.
- **Evidence pointer:** v3 `LocalSection.verified` path and current transitional rules.
- **Concern:** interface compatibility logic can be sound while the verification predicate for each local section is supplied at too weak an authority level.
- **Resolution test:** bind local-section verification to exact proof/check/evidence certificates before global authority; keep current gluing useful for search/residuals in shadow mode.
- **Status after revision:** OPEN ENGINEERING GAP, explicitly scoped as proposal/shadow.

### R2-M5 — State fingerprint scope was initially easy to overinterpret
- **Severity:** Major
- **Blocking:** Yes for claims of complete repository/artifact attestation.
- **Axis:** reproducibility
- **Claim pointer:** pre/post state hash proves the exact RAKL world.
- **Evidence pointer:** `state_fingerprint()` / initial metrology prose.
- **Concern:** the v3 state hash is an opaque deterministic hash of value state, not an attestation of arbitrary external files, repositories or legacy epistemic stores. Initial metrology also omitted legacy KnowledgeFibers unless explicitly provided.
- **Resolution test:** document state-hash scope; use unified substrate hash for explicitly supplied legacy fibres; report measurement coverage; reject before/after comparison across different measurement universes.
- **Status after revision:** RESOLVED in `v3_metrology.py` and coverage tests.

### R2-M6 — Prompt/retrieval separation is a policy boundary, not a complete injection defense
- **Severity:** Major
- **Blocking:** No for the architecture paper if scoped; Yes for a claim of robust prompt-injection security.
- **Axis:** ethical-governance / technical-soundness
- **Claim pointer:** external evidence cannot rewrite RAKL's constitution by being retrieved.
- **Evidence pointer:** security section.
- **Concern:** instruction hierarchy and architectural policy reduce semantic authority escalation, but they do not prove that every model/tool invocation resists malicious retrieved instructions.
- **Resolution test:** narrow claim to authority semantics; add hostile retrieval/prompt-injection tests before claiming robust operational resistance.
- **Status after revision:** CLAIM NARROWED. Security section treats this as an attack surface.

### R2-M7 — Rollback of code is not equivalent to rollback of persistent learned state
- **Severity:** Major
- **Blocking:** Yes for a claim of complete reversible evolution.
- **Axis:** reproducibility / data-resource-quality
- **Claim pointer:** previous variants remain rollback targets.
- **Evidence pointer:** variant archive and upgrade protocol.
- **Concern:** reverting the method code may be insufficient if a newer schema or consolidation policy irreversibly transformed persistent state.
- **Resolution test:** versioned state/schema migration, backward compatibility classification, authority non-escalation, rollback migration tests, and explicit irreversibility disclosure.
- **Status after revision:** PROTOCOL SPECIFIED; canonical migration framework not yet implemented.

### R2-M8 — Implementation/proposal/prospective surfaces needed an explicit matrix
- **Severity:** Major
- **Blocking:** Yes for readability/trust if absent.
- **Axis:** writing-clarity / claim-moderation
- **Claim pointer:** phrases such as "we implement" across the manuscript.
- **Evidence pointer:** entire draft.
- **Concern:** Paper 5 combines deployed v3 code, proposal-only Paper 5 instrumentation, documented future hardening and uncollected experiments. Without a status matrix, readers can easily mistake a protocol for a deployed guarantee.
- **Resolution test:** freeze a component-level status matrix and require verbs `implements/proposes/preregisters/requires` to follow status.
- **Status after revision:** RESOLVED in `docs/PAPER5_IMPLEMENTATION_STATUS.md`; manuscript still needs final consistency sweep against it.

## Minor comments

### R2-m1 — Hash security assumptions
State explicitly that content hashes provide identity subject to hash-function and observation integrity, not truth, honesty or cryptographic governance of administrators.

### R2-m2 — Repository administrators remain outside the claimed protection
The paper already acknowledges that sufficiently privileged humans can override gates. Keep this in the main limitations, not only supplement.

### R2-m3 — External services are part of the TCB/dependency boundary
CI, GitHub, model provider and search services should be recorded where material. A failed service is not a scientific refutation.

## Round-2 recommendation posture

**Architecture/governance argument:** ACCEPT for continued review with the explicit implementation-status boundary.  
**Strong autonomous self-promotion claim:** REJECT / not made.  
**Remaining blocking engineering gaps for such a claim:** R2-M2, R2-M3, R2-M4, and migration enforcement in R2-M7.

These open items are acceptable in the current draft only because the manuscript labels them as future hardening rather than completed guarantees.