# RAKL Publication

This directory is the canonical home for RAKL publication artifacts. Research evidence, experimental data, frozen receipts, discovery logs, and research-status records remain under `research/` so publication material is separated from the research workspace without rewriting provenance history.

## Canonical papers

1. **Paper I — Epistemic Mechanics for Evidence-Governed Scientific Research**  
   Source: `publication/epistemic_mechanics_round050/main.tex`

2. **Paper II — RAKL for Evidence-Governed AI-Assisted Scientific Research**  
   Source: `publication/saturated_epistemic_mechanics/source/main.tex`

3. **Paper III — Directional Structural Witnesses for Fail-Closed Cross-Domain Transfer**  
   Source: `publication/structural_amortization/main_v7.tex`

4. **Paper IV — Verified Discovery: An Assurance Architecture for LLM-Mediated Mathematical Research**  
   Source: `publication/math_research_assurance/main.tex`

Shared manuscript build scripts, release packages, figures, bibliographies, submission/reproducibility material, and publication-review artifacts are colocated here. Paper-review material previously stored at top-level `review/` is now under `publication/review/`.

## Compatibility aliases

The repository retains lightweight Git symlinks `paper -> publication` and `review -> publication/review` so existing CI, scripts, frozen receipts, and historical references continue to resolve. New publication work should use the `publication/` paths above.

Migration performed 11 August 2026.
