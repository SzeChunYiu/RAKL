# Verified Discovery paper

Title: **Verified Discovery: An Assurance Architecture for LLM-Mediated Mathematical Research**

This is the canonical self-contained publication package. `main.tex` is the manuscript entry point; `sections/` contains one TeX file per section/chapter after normalization; `figures/` contains the publication schematics; `build.py` performs the local release build and materializes `final.pdf`.

## Local build

```bash
python build.py
```

A release build binds the exact implementation subject and passing-test count through `build_identity.tex`; the file is generated locally and is not treated as scientific evidence by itself.

## Assurance boundary

The manuscript separates specification fidelity, formal truth, novelty, research value and implementation/checker trust. Proof receipts are meaningful only relative to the registered formal statement, checker/version, assumptions/axioms and isolated recheck. Novelty certificates are cutoff/corpus/search-route/equivalence scoped and defeasible. The assurance failure bound is a set-containment/union-bound statement, not a calibrated probability of theorem truth.

`review/PUBLICATION_READINESS.md` is an internal Nature-style publication-readiness record. It is not independent peer review or journal acceptance.
