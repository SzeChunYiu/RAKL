# Paper VI — Orion Scientific Research Engine (capstone)

Self-contained package. Build entry point: `source/main.tex`.
```
source/main.tex          # pdflatex + bibtex x2
source/sections/**/*.tex # chapters
source/figures/*.{tex,pdf}   # TikZ diagrams + demo figures used by \includegraphics
source/figures/scripts/  # figure generators (moved in, repointed to local data)
source/figures/data/     # vendored input receipts (copies; frozen originals under research/)
```
Regenerate demo figures: `python source/figures/scripts/make_demo_figures.py`. Self-contained — no dependency on the legacy top-level `paper/` tree.
