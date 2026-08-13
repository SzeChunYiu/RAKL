# Paper I projection benchmark v2 repair findings

Base: `c3ae5e02013756b22920e4e7c9ae0e11fe31e7fc`.

## V1 defect

`src/rakl/epistemic_projection_benchmark.py` sets `transition_type = family.family_id` and exposes `transition_type` to every comparator. When that family label is removed, identical substantive states can require different gold actions: the common safe/base state is `PROMOTE` in most families but `HOLD` in the supersession cases and `RESTRICT_SCOPE` in the negative-history case; `superseded=True` is `REVOKE` in F10 but `SUPERSEDE` in F15. F01 and F14 are duplicate evidence-support twins.

Therefore v1 is not suitable as flagship evidence without the family-labelled-task scope. Preserve it as negative history rather than rewriting it.

## V2 contract

1. Replace family-coded `transition_type` with an explicit, non-answer-bearing transition request (`PROMOTE_CLAIM`, `PROMOTE_MECHANISM`, `PROMOTE_IDENTIFICATION`, `PROMOTE_NOVELTY`, `REACTIVATE_CLAIM`, `SUPERSEDE_CLAIM`, `RESOLVE_CONTRADICTION`).
2. Score a separate governance decision (`ALLOW`, `DENY`, `RESTRICT`, `CANNOT_CHECK`).
3. Require gold to be a deterministic function of substantive state plus explicit request after all family/case IDs are stripped.
4. Split cases into non-authority invariance tests, decision-sufficiency twins, and legitimate-update controls.
5. Deduplicate F01/F14.
6. Add a cross-family collision audit with all answer-semantic metadata removed.

## Strong-parent correction

The v1 comparator set is too weak for a novelty claim. V2 must add a generous composite parent representing capabilities already established by assumption-based truth maintenance, provenance, and belief revision: context/inconsistency tracking, provenance/independence, supersession/revision, and negative-history retention. Relevant parents include de Kleer, *An assumption-based TMS*, Artificial Intelligence 28(2), 1986, DOI 10.1016/0004-3702(86)90080-9; Alchourron, Gardenfors & Makinson, *On the logic of theory change*, JSL 50(2), 1985, DOI 10.2307/2274239; and W3C PROV-O (2013). Dung-style argumentation is another required behavioural parent for contested claims.

Paper I novelty must therefore be a residual in scientific authority/action semantics, not generic provenance, contradiction handling, context switching, or belief revision.

## Constructive v2 result from the repaired case algebra

A coherent 28-case development panel (14 families) was constructed locally under the above contract. No identical substantive-state+request pair has conflicting gold. A 10-coordinate authority basis is sufficient and each coordinate is individually necessary by a registered decision twin: `evidence_support`, `global_gluing`, `context_match`, `evidence_independence`, `mechanism_support`, `identification_support`, `novelty_checked`, `cannot_check`, `negative_history_retained`, `superseding_evidence`.

Representation upper bounds on this repaired panel: simple scalar/text/provenance/pairwise/vote/transactional controls `0.5714`; generous ATMS+PROV+revision abstraction `0.6786`; typed authority state `1.0`. These are development representation bounds only, not behavioural or natural-domain evidence.

## Next executable gate

Do not promote the v2 representation result by itself. The flagship Paper I mechanism gate must use equal-information behavioural controls on opaque cases and test whether the typed authority transition semantics reduce invalid canonical updates while retaining legitimate promotion/supersession. A general-purpose rule engine that is manually given the exact RAKL decision rule is an expressiveness oracle, not a fair competing architecture; if it matches, the residual is governance schema/traceability rather than decision power.
