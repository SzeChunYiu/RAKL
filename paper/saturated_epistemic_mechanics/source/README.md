# RAKL saturated epistemic-mechanics paper source

This directory is the chaptered source for the Round-050 manuscript. `main.tex` contains the preamble and abstract; every top-level manuscript section lives in `sections/`.

## Build

Without `build_identity.tex`, the source compiles with an explicit `UNBOUND` implementation identity. A release build supplies `build_identity.tex` containing the exact implementation subject SHA and passing-test count, then runs:

```bash
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error main.tex
```

The `release/` sibling directory is generated only after the implementation/source commit is fixed. It contains the exact bound TeX source and reviewed PDF.

## Scientific boundary

The paper is a methods/formalism/preregistration release. Same-context manuscript saturation is not independent peer review, open-world completeness, or evidence of empirical scientific superiority.
