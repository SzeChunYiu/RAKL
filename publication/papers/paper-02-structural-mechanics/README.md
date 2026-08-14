# 2 structural mechanics

Self-contained paper package, rescoped 2026-08-14 to its earned claims: the
applicability contract as a specification, the typed-refusal absorption of the
causal-transportability parent (measured), and the instrument-falsifiability
battery with its three preserved negative case studies. No transfer/generality
claim is made; the external-label natural-domain coordinate (n≈48) is stated as
open. Evidence pointers: `research/paper2_six_family_audit_v1/`,
`research/paper2_causal_transport_absorption_v1/`,
`research/paper2_nearest_work_2026/`, `research/paper2_prose_transfer_v1/`,
`research/paper2_controlled_witness_extraction_v1/`.

```
main.tex            # entry point — build with: pdflatex main && bibtex main && pdflatex main x2
sections/*.tex      # chapters
figures/*.pdf .tex  # figures used by \includegraphics (TikZ .tex + rendered .pdf)
figures/scripts/    # scripts that generate the data-driven figures
figures/data/       # vendored input data for those scripts (copies; frozen originals live under research/)
```

Regenerate data-driven figures: `python figures/scripts/<make_*.py>` (reads figures/data/, writes figures/*.pdf).
Figures grant no scientific authority; each states its N and that it is a measurement, not a promotion signal.
