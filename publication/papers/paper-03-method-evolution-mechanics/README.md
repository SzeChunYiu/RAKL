# 3 method evolution mechanics

Self-contained paper package.

```
main.tex            # entry point — build with: pdflatex main && bibtex main && pdflatex main x2
sections/*.tex      # chapters
figures/*.pdf .tex  # figures used by \includegraphics (TikZ .tex + rendered .pdf)
figures/scripts/    # scripts that generate the data-driven figures
figures/data/       # vendored input data for those scripts (copies; frozen originals live under research/)
```

Regenerate data-driven figures: `python figures/scripts/<make_*.py>` (reads figures/data/, writes figures/*.pdf).
Figures grant no scientific authority; each states its N and that it is a measurement, not a promotion signal.
