# RAKL Publication Workspace

This directory is the canonical publication workspace. Research evidence, experiments, frozen receipts, discovery logs and scientific working state remain under `research/`.

## Canonical papers

- `papers/paper-01-epistemic-mechanics/` — **Epistemic Mechanics for Evidence-Governed Scientific Research**
- `papers/paper-02-rakl-evidence-governed-research/` — **RAKL for Evidence-Governed AI-Assisted Scientific Research**
- `papers/paper-03-directional-structural-witnesses/` — **Directional Structural Witnesses for Fail-Closed Cross-Domain Transfer**
- `papers/paper-04-verified-discovery/` — **Verified Discovery: An Assurance Architecture for LLM-Mediated Mathematical Research**

Each paper directory contains a `PUBLICATION_STATUS.md` that separates what can be published now from stronger claims that remain evidence-gated.

## Other publication material

- `reviews/` — active external-review/annotation solicitation packages.
- `shared/` — current cross-paper editorial standards, figure guidance, references and terminology material.
- `archive/` — superseded manuscript drafts, old arXiv/release packages, legacy sources and historical editorial/audit material. Archive contents remain immutable historical evidence; they are not canonical submission sources.

## Path policy

Do not introduce symlinks under `paper/` or `publishing/`. Reader-facing canonical sources live under `publication/`. Historical CI/receipt paths under `paper/` are real files (not link farms); new work should prefer `publication/papers/...`, `publication/reviews/...`, `publication/shared/...` and `publication/archive/...`.

## Publication policy

A public preprint may be released when its manuscript truthfully states its current evidence boundary and the exact-head build/CI package is clean. Stronger empirical or journal-level claims remain blocked whenever the corresponding result, independent-review or reproduction evidence does not exist. Missing evidence is never filled by prose.
