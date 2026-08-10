# Epistemic Mechanics paper

This directory is the editable long-form TeX project for:

**Epistemic Mechanics: From Linguistic Claims to Evidence-Governed Scientific State**

The manuscript is intentionally modular. Scientific sections are edited independently and the release builder deterministically expands them into one self-contained TeX source for CI/submission.

## Source layout

- `main.tex` — document driver, packages, notation, title/abstract, ordered section inputs.
- `sections/01_introduction_foundations_state.tex` — introduction, neighboring fields, canonical scientific state and transition mechanics.
- `sections/02_compatibility_authority.tex` — typed compatibility, higher-order gluing obstruction, true closure-system lattice conditions, authority partial order and scalar inadequacy.
- `sections/03_workspace.tex` — workspace prior art, constrained selection theorem, proposal-only authority boundary and cognitive/evidential provenance.
- `sections/04_owmd.tex` — Open-World Mechanism Discovery and bounded epistemic saturation.
- `sections/04b_open_world_stopping.tex` — open-world graph-completion and search-stopping prior art discovered during recursive saturation review.
- `sections/05_pendulum_discussion.tex` — exact pendulum derivation, finite-amplitude expansion, typed mechanics trace, discussion, limitations and conclusion.
- `sections/06_appendices.tex` — notation, additional derivations/counterexamples, saturation protocol, implementation correspondence and claim map.
- `sections/07_bibliography.tex` — complete manuscript bibliography; the test suite requires every listed item to be cited.

## Deterministic build

The canonical editable source contains `\input{...}` statements. `paper/build_epistemic_mechanics.py` recursively inlines only local TeX inputs, rejects path escapes/recursion/missing section files, and binds the staged source to the exact evaluated Git subject and observed software-test count.

Example:

```bash
python paper/build_epistemic_mechanics.py \
  --output paper/build/epistemic_mechanics/main.tex \
  --subject-sha "$(git rev-parse HEAD)" \
  --software-tests <passing-test-count>
```

The GitHub Actions publication workflow then compiles the staged source, runs strict warning/citation/reference preflight, requires the long-form paper to have at least 20 pages, renders every page, and uploads the complete review artifact.

## PDF release file

The PDF is a generated release artifact, not the canonical editable source. After the final bounded-saturation review and exact-subject CI pass, the reviewed PDF is materialized alongside the TeX project as `Epistemic_Mechanics.pdf`, with its source/review subject recorded in the release ledger. The modular `.tex` files remain the source of truth.

This two-layer convention matters because the manuscript embeds a source identity. The PDF must never be hand-edited or treated as a substitute for the TeX/review ledger.

## Saturation rule

This paper follows the project-level bounded epistemic saturation rule documented in `docs/EPISTEMIC_SATURATION.md` and implemented in `src/rakl/epistemic_saturation.py`.

A research/review round is not flat merely because no prose was added. It is flat only when no new relevant mechanism, derivation, independent evidence root, contradiction/counterexample, negative result, novelty boundary, assumption/scope correction, unresolved-fiber update, or discovery-route update is found under the frozen basis. New substantive knowledge reopens the paper automatically.

A bounded-saturation verdict is therefore a scoped release certificate, never a claim of unrestricted scientific completeness or completed independent peer review.
