# RAKL four-paper publication series

This directory now has four canonical publication packages. Historical material remains temporarily in legacy paths only for compatibility while the closeout branch verifies exact-source builds; the canonical packages below are the publication sources of record.

| Paper | Canonical package | Title | Publication claim boundary |
|---|---|---|---|
| I | `paper1_epistemic_mechanics/` | *Epistemic Mechanics for Evidence-Governed Scientific Research* | Formal epistemic mechanics; no empirical-superiority or global-completeness claim. |
| II | `paper2_rakl_framework/` | *RAKL for Evidence-Governed AI-Assisted Scientific Research* | Architecture, deterministic trace and preregistered evaluation; no unmatched empirical-superiority claim. |
| III | `paper3_structural_amortization/` | *Directional Structural Witnesses for Fail-Closed Cross-Domain Transfer* | Constructed/internal conformance evidence; the independent-annotation/efficiency claim remains explicitly unlicensed. |
| IV | `paper4_verified_discovery/` | *Verified Discovery: An Assurance Architecture for LLM-Mediated Mathematical Research* | Formal assurance architecture; bounded novelty only; no autonomous-mathematician superiority claim. |

Each canonical package is required to contain `main.tex`, section/chapter TeX sources, a local `build.py`, `figures/`, `review/`, and a release `final.pdf` produced from the exact reviewed commit. `PUBLICATION_MANIFEST.json` is the machine-readable release map.

## Review standard

The closeout uses the workflow principles from `Yuan1z0825/nature-skills`: literature saturation, claim/evidence checking, reference verification, figure completeness, Nature-style writing/polishing, and reviewer passes over originality, importance, interdisciplinarity, technical soundness and readability. Because this execution environment does not provide isolated reviewer subagents, the three review passes are **internal Nature-style passes**, not independent peer review. Publication readiness means zero known blocking concerns after the registered passes, tests and PDF preflight; it does not mean journal acceptance or infallibility.
