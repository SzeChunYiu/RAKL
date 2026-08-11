from __future__ import annotations

# Documentation-only migration manifest. The actual closeout move is performed
# as a git tree operation so blob/tree identities are preserved exactly.
LEGACY_TOP_LEVEL = [
    "CITATION_ASSIMILATION_043.md", "FIGURE_PLAN.md", "FIGURE_QUALITY_STANDARD.md",
    "RAKL_MANUSCRIPT.md", "REFERENCE_VERIFICATION.md", "REFERENCE_VERIFICATION_043.md",
    "RELATED_WORK_MATRIX.md", "ROUND044_V2_1_PAPER_DELTA.md", "SAME_CONTEXT_REVIEW_042.md",
    "SUBMISSION_PLAN.md", "SUPPLEMENTARY_METHODS.md", "TERMINOLOGY_LEDGER.md",
    "arxiv", "arxiv_release_2026-08-10", "arxiv_release_v2_2026-08-10",
    "build_epistemic_mechanics.py", "build_math_research_assurance.py",
    "build_saturated_epistemic_mechanics.py", "build_v2_1_source.py", "build_v2_2_source.py",
    "epistemic_mechanics", "epistemic_mechanics_round050", "figures",
    "finalize_release_layout.py", "generate_demo_figures.py", "math_research_assurance",
    "references.bib", "references_round043_additions.bib", "saturated_epistemic_mechanics",
    "structural_amortization",
]

if __name__ == "__main__":
    print("\n".join(LEGACY_TOP_LEVEL))
