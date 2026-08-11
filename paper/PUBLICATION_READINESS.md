# RAKL five-paper publication readiness

Audit date: 11 August 2026

This document is the publication control panel. It distinguishes **preprint release readiness** from stronger empirical or journal-level claim authority. A missing experiment, independent review or personal author declaration is never converted into a pass by editorial wording.

| Paper | Current honest release form | Machine-checkable gate | Evidence/external gate |
|---|---|---|---|
| 01 — Epistemic Mechanics | formal-methods preprint | exact-head `publication-pdfs` (canonical `publication/papers/`) | independent formal, novelty and editorial review (#41); author metadata beyond title page |
| 02 — RAKL Evidence-Governed Research | methods/reference-architecture + preregistered-evaluation preprint | exact-head CI/build | matched architecture × evidence-access study; V4/V4.1 microtrials are non-confirmatory negatives only (not experience-§B authority); OWMD prospective test; fresh-assurance comparison; reproduction/review |
| 03 — Directional Structural Witnesses | diagnostic-formalism / benchmark-design preprint | exact-head CI/build | #43 annotations/adjudication/provenance; held-out signal gate; then any authorized efficiency experiment. Descriptor READY ≠ training authorized |
| 04 — Verified Discovery | mathematical-research assurance architecture preprint | exact-head tests, hostile packet, staged build, LaTeX/layout/artifact checks | author metadata; external empirical superiority evidence only if later claimed |
| 05 — Experience-Governed Evolution | methods/metrology + preregistered continual-evolution preprint | exact-head CI/build including paper-05 PDF | prospective four-arm attribution and protected Self-RAKL assurance before any 3.1 superiority claim |

## Release rule

A paper may be posted as a public preprint once:

1. its title/abstract/conclusion stay inside the evidence boundary recorded in its `PUBLICATION_STATUS.md`;
2. the exact publication head passes the relevant build and CI workflow;
3. the source package contains only files required for the paper/reproducibility package and no archived/internal material;
4. citations/references resolve and the PDF has no blocking LaTeX/layout defects;
5. author-supplied metadata and declarations are complete;
6. AI-use disclosure is present in the compiled manuscript.

A stronger claim remains blocked when the corresponding evidence does not exist. For Papers 02, 03 and 05 in particular, a clean build is not equivalent to an empirical result.

## Fail-closed reminders (2026-08-11)

- Do **not** invent #43 labels or close #41/#43 without public responses.
- Do **not** treat V4.1 tip harvests (`HARVEST_V4_1_TASK_SEED_PASS_NONCONFIRMATORY`) as experience-§B method authority or promotional arm metrics.
- Paper III cheap-gate numbers (ROC-AUC gain ≈ 0.086, AP gain ≈ 0.097) remain constructed same-session diagnostics; confirmatory gate is still open.

## Author action required

See `shared/editorial/AUTHOR_METADATA_REQUIRED.md`. The repository cannot truthfully invent ORCID, funding, competing interests, acknowledgements or license choice beyond the title-page identity already printed.
