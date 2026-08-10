# Round 046 Nature-skills publication / figure review

Date: 2026-08-10

Status: internal same-context pre-submission review; repairs applied, final exact-subject validation pending. This is **not independent peer review** and does not represent Nature/editor acceptance.

Nature-skills source revision: `Yuan1z0825/nature-skills@a816314de0bb985e7034886e01596059522255b9`.

## Review objective

Round 045 reviewed the new metrology, storage and matched-workflow logic. Round 046 asks a different question: has that logic been integrated into one exact publication artifact without source drift, misleading plots, layout defects or evaluator/corpus mismatches?

The review used the `nature-figure` claim-first/render-first contract and the `nature-reviewer` separation between blocking major issues, minor presentation issues and an explicit recommendation. Because the environment does not provide isolated reviewer contexts, all verdicts remain same-context internal gates.

## Publication artifact examined

Parent artifact: reviewed V2 source reconstructed exactly from `paper/arxiv_release_v2_2026-08-10/`, SHA-256 `4adec2bb256775823dde3b5f520a9ef599c4fe95078121a513ce71e301ac5302`.

V2.1 is generated as a deterministic patch over that exact source by `paper/build_v2_1_source.py`; every edit must match exactly one parent-source anchor. The stale `paper/arxiv/main.tex` is not used as the V2.1 publication parent.

## Major findings and repairs

### R46-M1. Publication source drift

**Finding.** The live `paper/arxiv/main.tex` still represented an older 598-test source and could not be used as the V2 parent without silently discarding the reviewed V2 manuscript.

**Risk.** Rebuilding from that file would make the paper and code appear synchronized while actually regressing sections, citations and validation records.

**Repair.** `paper/build_v2_1_source.py` now reconstructs the exact reviewed V2 source, verifies its SHA-256, applies only exact-anchor deltas, and dynamically binds the generated manuscript to the exact Git subject and observed passing-test count. The release staging function copies the publication figures beside that exact source.

**Disposition.** Closed in code; final exact-subject build still required after this review record is committed.

### R46-M2. Quantitative figures mixed geometry, value and presentation prose

**Finding.** The original known-answer growth panel encouraged readers to read cumulative semantic-object counts as the main progress metric. The first Matplotlib redesign then introduced crowded event text below panel a and redundant figure-level prose.

**Risk.** A visually dominant scalar or crowded annotation can undo the formal separation between graph growth and scientific value.

**Repair.** Figure 5 now uses three separate panels: basis-bound atlas geometry, target access (cuts/support paths), and independent evidence roots. Round events are explained in the manuscript caption; x-axis labels are only `R0`--`R3`. Figure 6 separately displays prompt working-set size, physical evidence storage and exact-refetch logical-vs-physical growth. Both are generated from immutable receipts and export PDF/SVG/PNG plus machine-readable source data.

**Disposition.** Closed after direct PNG/PDF visual review; final manuscript embedding still requires exact-subject render inspection.

### R46-M3. Arrow-associated text degraded the conceptual schematics

**Finding.** Several TikZ figures attached process/relation wording directly to arrows.

**Risk.** The result was visually busy and made the meaning of a connector dependent on tiny text embedded in the path.

**Repair.** Figures 1--3 move process/relation semantics into standalone text blocks/keys. Repository tests reject TikZ `\draw` paths carrying inline text nodes and reject Matplotlib arrow callouts (`arrowprops`, `FancyArrow`, `ConnectionPatch`). Structural arrows remain allowed but carry no prose.

**Disposition.** Closed and regression-tested.

### R46-M4. Full manuscript render exposed a bibliography orphan page

**Finding.** Adding four scoped prior-art references increased the first V2.1 render from 23 to 25 pages; page 25 contained only three bibliography entries and large unused whitespace.

**Risk.** The nearly empty final page looked like an unfinished layout rather than a deliberate publication artifact.

**Repair.** Only the bibliography typography is reduced to `\small`; main text and figures retain their original size. The compact bibliography setting is part of the deterministic V2.1 patch and is regression-tested.

**Disposition.** Repair applied; exact final page count/visual balance must be rechecked on the final subject.

### R46-M5. Matched pendulum microtrial evaluator referenced a non-existent corpus concept

**Finding.** The preregistered microtrial asked whether a source measuring “time to reach a specified angle” contradicted an oscillation-period source, but the frozen eight-source pendulum corpus contains no time-to-angle measurement. The original required-support source set also mixed unrelated source roles.

**Risk.** The sealed evaluator would have judged model outputs against a question that could not be answered from the registered evidence, invalidating the comparison while appearing formally frozen.

**Repair.** The microtrial now asks only about distinctions actually present in `src/rakl/mini_research_demo.py::_sources`: the small-angle approximation, finite-amplitude correction, Earth/Moon and regime alignment, ideal mass invariance and the refuted mass-dependence claim. `PendulumStructuredAnswer` V2 separates supporting, context-misaligned and refuted source roles. The evaluator checks five conceptual coordinates, support recall/precision, misalignment recall and refutation recall/precision. `validate_pendulum_evaluator_sources()` fails before any model call if a required evaluator source is absent. A preregistration regression test binds every evaluator source ID and question family to the frozen source world.

**Disposition.** Logic and preregistration repaired; exact branch CI required before closure.

## Minor comments

1. The V2.1 manuscript correctly calls MDL and information bottleneck intellectual-lineage analogies; do not later upgrade those citations into claims that RAKL solves either objective without new implementation/evidence.
2. The basis identifier or an equivalent frozen-basis statement should remain visible whenever longitudinal atlas-volume/density numbers are shown outside the paper.
3. Figure 6 should not be described as production storage benchmarking; it is a deterministic reference-backend trace.
4. The exact same-model microtrial remains a diagnostic bridge only, even after execution. It is not the preregistered multi-domain matched-workflow result.
5. No “ready for Nature” language is licensed by same-context internal review. A clean internal gate means ready to release the scoped methods/preregistration artifact for public/external review.

## Current recommendation

**Recommendation: minor revision / final validation.**

The manuscript logic, plotting strategy and evaluator contracts now address the blocking issues found in Rounds 045--046. Publication readiness remains contingent on one exact final subject satisfying all of the following simultaneously:

1. complete test suite passes and the manuscript records that exact count;
2. deterministic metrology and archive receipts reconstruct exactly;
3. V2.1 source is generated from the exact reviewed V2 parent and bound to the exact final Git SHA;
4. LaTeX compiles without blocking overflow/float/citation/reference warnings;
5. every PDF page is rendered and visually inspected after the compact bibliography and final plot revision;
6. quantitative figures remain receipt-bound and arrow-callout free;
7. the repaired microtrial preregistration/evaluator corpus-binding tests pass;
8. public claims continue to state that empirical superiority, fresh self-evolution transfer and the real quant-science result remain open.

A subsequent final review round may return `READY_FOR_PUBLIC_METHODS_PREREGISTRATION_RELEASE` only if those gates are all clean on one exact subject.
