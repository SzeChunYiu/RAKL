# RAKL framework paper

Title: **RAKL for Evidence-Governed AI-Assisted Scientific Research**

This is the canonical self-contained publication package. `main.tex` contains the preamble and abstract; every top-level manuscript section/chapter lives as one TeX file in `sections/`. Publication materialization consolidates the two historical multi-part sections so the canonical package has no chapter-fragment dependency.

## Local build

Run:

```bash
python build.py
```

The builder regenerates the receipt-bound demonstration figures from `figures/source_data/`, writes the release build identity, compiles with `latexmk`, and materializes `final.pdf`. Without a supplied release identity the underlying TeX source remains explicitly unbound rather than inventing one.

## Package contents

- `sections/`: canonical section/chapter TeX files and bibliography material.
- `figures/`: publication schematics, figure generator, generated vector/bitmap outputs, and the source receipts needed by the demonstration plots.
- `review/PUBLICATION_READINESS.md`: internal Nature-style readiness record, not independent peer review or journal acceptance.
- `SOURCE_MANIFEST.json`: source-package lineage.
- `final.pdf`: release PDF after the publication gate passes.

## Scientific boundary

The paper is an architecture/formalism, deterministic reference trace and preregistered evaluation release. The latest native staging evidence establishes an auditable real-inference bridge only: it records successful asset staging but zero evaluated model runs/results at the publication cutoff. Same-context saturation, staging success, software-test count and context compression are not evidence of empirical scientific superiority. Matched architecture-by-evidence-access and prospective OWMD claims remain open until their registered evaluations produce valid receipts.
