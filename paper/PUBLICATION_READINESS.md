# RAKL four-paper publication readiness

Audit date: 11 August 2026

This document is the publication control panel. It distinguishes **preprint release readiness** from stronger empirical or journal-level claim authority. A missing experiment, independent review or personal author declaration is never converted into a pass by editorial wording.

| Paper | Current honest release form | Machine-fixable gate | Evidence/external gate |
|---|---|---|---|
| 01 — Epistemic Mechanics | formal-methods preprint | exact-head CI/build after migration | independent formal, novelty and editorial review; author metadata |
| 02 — RAKL Evidence-Governed Research | methods/reference-architecture + preregistered-evaluation preprint | exact-head CI/build | matched architecture × evidence-access study, OWMD prospective test, fresh-assurance comparison, reproduction/review; author metadata |
| 03 — Directional Structural Witnesses | diagnostic-formalism / benchmark-design preprint | exact-head CI/build | frozen strong semantic control execution, external annotations/adjudication, held-out signal gate, then any authorized efficiency experiment; author metadata |
| 04 — Verified Discovery | mathematical-research assurance architecture preprint | exact-head tests, hostile packet, staged build, LaTeX/layout/artifact checks | author metadata; external empirical superiority evidence only if later claimed |

## Release rule

A paper may be posted as a public preprint once:

1. its title/abstract/conclusion stay inside the evidence boundary recorded in its `PUBLICATION_STATUS.md`;
2. the exact publication head passes the relevant build and CI workflow;
3. the source package contains only files required for the paper/reproducibility package and no archived/internal material;
4. citations/references resolve and the PDF has no blocking LaTeX/layout defects;
5. author-supplied metadata and declarations are complete.

A stronger claim remains blocked when the corresponding evidence does not exist. For Papers 02 and 03 in particular, a clean build is not equivalent to an empirical result.

## Author action required

See `shared/editorial/AUTHOR_METADATA_REQUIRED.md`. The repository cannot truthfully invent affiliation, ORCID, funding, competing interests, acknowledgements, corresponding email or license choice.
