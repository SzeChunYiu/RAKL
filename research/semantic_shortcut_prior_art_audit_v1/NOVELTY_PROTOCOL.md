# Novelty protocol — semantic-shortcut system claim (#403)

**Authority class:** `INTERNAL_PRIOR_ART_AUDIT`  
**Independent external reviewers:** absent (not invented)  
**CAPABLE_MODEL_AVAILABLE:** `NO_REFUTED`  
**Parent internal audit:** `research/FIVE_PAPER_SEMANTIC_SHORTCUT_NOVELTY_AUDIT_20260812.md`

## Audited question

Audit the system-level novelty boundary of the obstruction–transformation semantic shortcut (PR #376). Do **not** ask whether analogy, CBR, proof retrieval, failure repair, skill memory, CEGIS or program synthesis are individually new.

## Phases

1. Freeze claim text, subject SHA, schemas/runtime identities, literature cutoff, databases and inclusion/exclusion rules (`FROZEN_CLAIM.json`).
2. Multi-family search across classical CBR/analogy, structure-aware proof retrieval, CEGIS/property-guided synthesis, agent memory/skills, scientific-discovery agents, meta-reasoning/invention gating, provenance/authority separation (`SEARCH_UNIVERSE.json`, `QUERY_LOG.jsonl`).
3. Component-by-component comparison (`COMPONENT_COMPARISON.json`).
4. Strongest-parent reconstruction attempting to assemble the full contract from nearest parents (`STRONGEST_PARENT_ANALYSIS.md`).
5. Role-separated same-process lenses recorded as INTERNAL only (`REVIEWER_A.json`, `REVIEWER_B.json`). Distinct independent humans are unavailable; do not mint independent novelty authority.
6. Provenance + final receipt (`PROVENANCE_RECEIPT.json`, `FINAL_NOVELTY_RECEIPT.json`).

## Verdict vocabulary

Scoped outcomes only: `SYSTEM_COMBINATION_NOT_FOUND_WITHIN_REGISTERED_SEARCH`, `PARTIALLY_ANTICIPATED`, `MATERIALLY_ANTICIPATED`, `CLAIM_TOO_BROAD`, `CANNOT_CHECK`.

Forbidden absolute wording without extraordinary evidence: globally novel, first ever.

## Kill / narrowing

- One prior system materially contains the whole contract → drop system-level novelty; retain implementation/integration.
- Strongest-parent composition makes claim obvious/standard → narrow to engineering/governance formalization.
- Search coverage inadequate → `CANNOT_CHECK`, not novelty.
- Review independence unavailable → keep `INTERNAL_PRIOR_ART_AUDIT`.
