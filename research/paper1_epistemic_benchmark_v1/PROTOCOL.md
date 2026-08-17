# Paper I adversarial epistemic-governance publication bundle (#489)

Status: `POSITIVE_SCOPED_PROJECTION_SUFFICIENCY_V2`

This directory is the machine-readable publication bundle requested by #489. The canonical executable instrument is `src/rakl/epistemic_projection_benchmark_v2.py`; the development history, preserved v1 negative, repaired-v2 notes, and human-readable protocol remain under `research/paper1_adversarial_epistemic_benchmark_v1/`.

## Scientific question

Does a typed scientific-authority state retain decision-relevant distinctions that plausible compressed scientific-agent states erase, while still permitting legitimate updates rather than succeeding by blanket refusal?

## Design

- 28 constructed cases across 14 hostile/legitimate-update families.
- `TransitionRequest` is candidate-visible and separate from the governance decision.
- `CASES.jsonl` carries the case inputs/overrides but not gold decisions.
- `GOLD_TRANSITIONS.jsonl` is the separate answer key.
- family, case, gold, and answer labels are absent from all comparator projections.
- comparators include text memory, provenance-only, scalar confidence, pairwise compatibility, majority/reviewer vote, simple transactional state, a stronger ATMS+PROV+revision diagnostic parent, and RAKL typed authority.
- objective known-answer state transitions; no LLM judge.
- legitimate supersession is included so blanket refusal is not a safe strategy.

## Primary result

`RESULTS.json` records the exact executable audit: the simple compressed projections have identifiable upper bound 16/28 (0.5714), the stronger ATMS+PROV+revision diagnostic reaches 19/28 (0.6786), and RAKL typed authority reaches 28/28 (1.0) with zero ambiguous projected states. The registered ten-coordinate authority basis is sufficient and each coordinate is individually necessary on its paired witness in the current panel.

## Boundary

This is a positive, scoped representational/decision-sufficiency result. It is not a theorem that arbitrary extensible ATMS, PROV, belief-revision, argumentation, rule-engine, or language-reasoning systems cannot encode the missing semantics. It is also not the separately frozen 96-case live-model production-ingress assurance study, which remains a successor under #592.

`FINAL_RECEIPT.json` is the #489 closure receipt. `tests/test_paper1_epistemic_benchmark_publication_bundle.py` binds this bundle back to the executable v2 source and fails on drift.
