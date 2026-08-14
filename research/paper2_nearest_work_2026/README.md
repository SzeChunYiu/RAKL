# Paper II 2026 nearest-work threat audit (#487)

**Status:** `AUDIT_FILLED / RED_THREAT_FOUND / NO_MANUSCRIPT_AUTHORITY`
**Date:** 2026-08-14
**Parents:** #444 empirics, #486 transport v2 (closed via #491), #490 NMI gate

Same-context analysis. Not independent review. Proposes manuscript changes;
edits no manuscript file.

## Headline

The residual novelty claim as currently worded does not survive. **Causal
transportability (Bareinboim & Pearl, 2011–2016) is a RED threat** that occupies
directionality, QoI binding, source preconditions, preserved invariants, target
boundaries, evidence-bearing and fail-closed behaviour — and its FAIL branch is
*stronger* than fail-closed, because Corollary 3 completeness turns refusal into
a certificate of impossibility.

Four residuals survive. See `NOVELTY_THREAT_RANKING.md`.

## Deliverables

| File | Status |
| --- | --- |
| `CLAIM_MATRIX.md` | filled — 30 works across 7 families |
| `NOVELTY_THREAT_RANKING.md` | filled — RED / AMBER / GREEN with surviving residuals |
| `COMPARATOR_REQUIREMENTS.md` | filled — mandatory arms and design constraints |
| `MANUSCRIPT_DIFF_PLAN.md` | filled — delete / narrow / strengthen / add / correct |
| `BIBLIOGRAPHY_PATCH.tex` | filled — 25 entries, all primary-source verified |
| `AUDIT_STATUS.json` | machine-readable terminal |

## Verification standard

Every record was read off a canonical primary source: ACL Anthology, arXiv
`/abs/` pages, Crossref, DBLP, or publisher PDF. No citation is transcribed from
a search-engine summary, and none from the #487 issue body, which was treated
throughout as unverified operator prose.

All eight operator-supplied candidates verified; one year/venue correction (ARN
is TACL 12, **2024**, not TACL 2026) and four dropped subtitles restored.

## Negative results (preserved)

Two targeted searches found nothing, recorded with exact queries in
`AUDIT_STATUS.json`:

1. no CBR mechanism returning an explicit three-way reusable / not-reusable /
   cannot-determine verdict;
2. **no benchmark scoring a three-way accept / reject / abstain decision on a
   transfer** (as opposed to on answerability).

Result 2 is the cleanest open lane for the paper.

## Explicit non-claims

- Surface resemblance to analogy/transfer papers is not residual novelty.
- Transport obligations v2 code (#491) does not clear this audit.
- This audit authorizes no confirmatory empirics and no manuscript edit.
- A filled claim matrix is not independent review.
