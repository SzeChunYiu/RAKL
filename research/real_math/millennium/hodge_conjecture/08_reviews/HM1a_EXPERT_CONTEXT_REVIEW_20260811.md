# HM1a same-context expert cell — source-bearing decomposition

**Authority:** `SAME_CONTEXT_REVIEW_ONLY / NOT_INDEPENDENT_REVIEW / NO_MATHEMATICAL_CANDIDATE`

**Active atom:** `HM1a` — find a higher-codimension source-producing mechanism for a rational Hodge class, or expose exactly where a proposed decomposition merely relocates the original cycle-map surjectivity obligation.

## 1. Hodge theory / algebraic cycles lead

**Background:** rational Hodge structures, Chow groups, cycle maps, Lefschetz theorems.

**Finding:** the first HM1 discriminator correctly separated source production from target enrichment. Arapura's Leray criterion supplies a stronger calibration for higher codimension: the cohomology is filtered while the source side remains a filtered Chow group, so the route never loses the source category.

**Strongest objection:** a graded cycle-map surjectivity condition can still be exactly as hard as the original Hodge conjecture. A filtration is useful only when some critical pieces are solved or vanish for independent reasons.

**Delegated test:** for every decomposition, list every graded target Hodge piece and mark its source map `KNOWN_SURJECTIVE`, `HODGE_TARGET_ZERO`, or `OPEN_ROOT_LIKE`. Any unlabelled/open piece blocks promotion.

## 2. Motives / algebraic correspondences lead

**Background:** Chow motives, algebraic correspondences, motivated motives, standard conjectures.

**Finding:** Arapura's 2005 moduli examples exhibit the source-producing pattern we want: geometry supplies a dominating correspondence built from a universal sheaf, rather than first postulating realization fullness.

**Strongest objection:** “motivated by” is broader than “there is a Chow correspondence sufficient for this exact alpha.” Abstract André-motive language must still be expanded to the actual algebraic correspondence used at the target step.

**Delegated test:** demand the exact cycle/kernel class, source variety, induced cohomology map, and coverage/equality statement. Mark any inverse Lefschetz or projector not known algebraic.

## 3. Filtered geometry / Leray lead

**Background:** Leray filtration, variations of Hodge structure, localization, hard Lefschetz.

**Finding:** Arapura 2021 provides a concrete source-bearing assembly theorem. The high-information coordinate is **eliminability of critical pieces**: p=0/1 pieces can be solved by known theorems, and a higher piece can sometimes be discharged because its Hodge target vanishes.

**Strongest objection:** a generic fibration may create more difficult local-system Hodge groups than the original problem.

**Delegated test:** score candidate fibrations by whether the number and difficulty of `OPEN_ROOT_LIKE` graded pieces actually decreases after the exact theorem is applied.

## 4. Derived/categorical + arithmetic lead

**Background:** Fourier–Mukai kernels, moduli objects, K-theoretic realizations, spread-out and comparison structures.

**Finding:** categorical methods are strongest when a universal object/kernel is an algebraic geometric source and its Chern/cycle correspondence is explicit. Arithmetic or categorical target constraints alone remain target-enriching.

**Strongest objection:** a categorical Hodge class, period constraint, or special-fiber Tate class can pass many target-side checks while the characteristic-zero Chow witness remains absent.

**Delegated test:** require an actual object/kernel or characteristic-zero cycle plus the precise realization equality. Otherwise classify the route as `TARGET_ENRICHING` or `SOURCE_CATEGORY_RELAXING`.

## 5. Adversarial falsification lead

**Background:** counterexamples, hidden assumptions, theorem-scope and circularity audits.

**Finding:** the cross-Millennium root-bridge stability audit applies as a diagnostic only. HM1a's version of “surrogate survives, root coordinate collapses” is a decomposition whose pieces look controlled while one undisclosed graded source-surjectivity obligation remains equivalent to Hodge.

**Strongest objection:** a criterion can look narrower while quantifying over all Hodge classes in exactly the unsolved critical piece.

**Delegated test:** expand quantifiers and source maps. Falsify a proposed reduction if its only new assumption is “the relevant graded cycle map is surjective” without an independent theorem or vanishing mechanism.

## 6. Formal methods / novelty / learning-control lead

**Background:** typed proof obligations, trace chronology, method applicability, bounded novelty, research-mode control.

**Finding:** the next useful object is a typed `SourceBearingDecompositionCertificate` with six fields:
`source_groups`, `target_Hodge_pieces`, `source_maps`, `discharge_reasons`, `assembly_theorem`, `alpha_reconstruction`.

**Strongest objection:** building a new formal wrapper around a root-equivalent criterion creates bookkeeping, not information.

**Delegated test:** require a measurable epistemic delta: at least one previously open root-level source obligation must be replaced by a proved source construction or a proved zero-Hodge target.

**Learning-mode disposition:** `REFLECTIVE_RESTRUCTURE`, `CONTRASTIVE_DISCRIMINATION`, and `EFFECTUAL_PROBE` remain supported. `ROUTINE_REUSE` is allowed only for the cross root-bridge audit with the recorded DifferenceWitness. `META_METHOD_BASIS_AUDIT` is not justified because the new representation has just produced a distinct source-bearing route family.

## Cell synthesis

The cell unanimously rejects “search for any stronger motivic/categorical property of alpha” as the next move. The next action is to **calibrate a source-bearing decomposition certificate** on published positive and negative/near-miss cases before proposing a theorem.

The most promising verified higher-codimension pattern currently exposed is:

`filtered/correspondence source -> eliminate easy or Hodge-empty pieces -> assemble -> exact alpha source`.

The open research question is not whether such mechanisms exist in special cases—they do—but whether one can construct them with enough generality to reduce an arbitrary `X,alpha` without leaving an `OPEN_ROOT_LIKE` piece.

No expert role claims independent review, novelty, or a Hodge theorem.
