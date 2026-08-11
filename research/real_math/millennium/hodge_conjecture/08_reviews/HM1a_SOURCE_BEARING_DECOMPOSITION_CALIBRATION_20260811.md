# HM1a source-bearing decomposition calibration

**Authority:** `SOURCE_BOUND_ROUTE_CALIBRATION / SAME_CONTEXT_REVIEW_ONLY / NO_HODGE_THEOREM / ROOT_AUTHORITY_NONE`

**Atom:** `HM1a`.

This executes the frozen pre-candidate discriminator without proposing a new Hodge theorem. The question is whether a typed source-bearing decomposition screen can distinguish genuine cycle-producing reductions from decompositions that merely relocate the same unsolved surjectivity.

## Certificate interface

For a target Hodge class problem, record:

1. `source_groups` — actual Chow groups or source varieties/categories with verified algebraic-cycle authority;
2. `target_Hodge_pieces` — the Hodge pieces to be covered;
3. `source_maps` — exact cycle/correspondence maps into those pieces;
4. `discharge_reasons` — for every target piece: `KNOWN_SURJECTIVE`, `HODGE_TARGET_ZERO`, or `OPEN_ROOT_LIKE`;
5. `assembly_theorem` — the exact theorem recombining the pieces;
6. `alpha_reconstruction` — how the original class is recovered from source cycles.

A route fails the screen if any root-relevant piece is `OPEN_ROOT_LIKE` and no independently stronger theorem shrinks it.

## Calibration P1 — divisor/Picard

The codimension-one case fills every field: the source is `Pic(X)⊗Q = CH^1(X)_Q`; the Chern-class map is the realization; the exponential exact sequence gives source existence for `(1,1)` classes; and the resulting divisor reconstructs the class.

**Verdict:** `SOURCE_PRODUCING / PASS`.

## Calibration P2 — Leray-filtered Chow source (Arapura 2021)

For a smooth projective fibration restricted to its smooth locus `V -> U`, Arapura defines a Leray filtration on rational Chow groups by pulling back the cohomological Leray filtration. The graded cycle maps

`Gr_L^i CH^p(V) -> H^i(U, R^{2p-i} f_* Q)`

land in Hodge cycles. Theorem 1.2 proves that surjectivity on a specified lower-left region `Q` is sufficient for the Hodge conjecture on `V`; the proof then propagates the coverage to the remaining pieces using exactness and Lefschetz-type reflections.

The decisive calibration is Corollary 1.4 for fourfolds: after the codimension-zero/one pieces are discharged by standard results, only one higher-codimension graded piece remains; if the Hodge subspace of that target is zero, its cycle-map surjectivity is vacuous and the Hodge conjecture follows.

This is a genuine **source-bearing decomposition** because the domain of every positive obligation remains a graded Chow group. More importantly, it demonstrates a non-tautological way to gain information: a difficult source-surjectivity obligation can disappear because the corresponding target has no Hodge classes.

**Verdict:** `SOURCE_BEARING_DECOMPOSITION / PASS_AT_PUBLISHED_SCOPE`.

**Boundary:** applying the theorem to arbitrary `X` is not automatic. If the remaining critical graded map is simply assumed surjective, the root difficulty has only been relocated.

## Calibration P3 — explicit dominating correspondence (Arapura 2005)

Arapura's motivation framework checks special moduli examples by building a correspondence dominating the target. In the examples highlighted in the paper, the correspondence is built from the universal sheaf and can sometimes be viewed as Fourier–Mukai-type. This gives an actual geometric interface from source curves/surfaces to target cohomology and permits Hodge-conjecture checks for special targets.

**Verdict:** `SOURCE_DOMINATION / PASS_AT_PUBLISHED_SCOPE`.

**Boundary:** the existence of such a universal kernel/correspondence is special geometry, not a constructor for arbitrary `X,alpha`.

## Calibration N1 — abstract motivated/categorical enrichment

A target may sit in a well-behaved motivated or categorical realization while the required source operation is not established as a Chow correspondence/object whose cycle class equals `alpha`.

**Verdict:** `SOURCE_CATEGORY_RELAXING / FAIL_INITIAL_CHOW_SOURCE`.

## Calibration N2 — deformation propagation H4d1

H4d1 can analyze whether a known algebraic witness lifts through formal, algebraization, and globalization stages in a family. Its own strict packet explicitly assumes an initial algebraic witness.

**Verdict:** `PROPAGATION_ONLY / FAIL_INITIAL_SOURCE`.

## Calibration N3 — unpruned graded decomposition

Suppose one writes a filtration and an assembly theorem but leaves a critical target piece whose only proposed discharge is “the corresponding graded Chow cycle map is surjective,” with no independent theorem, source constructor, or Hodge-vanishing result.

The decomposition is logically valid as a re-expression, but it has not reduced the active source-existence obligation.

**Verdict:** `OPEN_ROOT_LIKE_PIECE / NO_EPISTEMIC_CONTRACTION`.

This is not an impossibility theorem. A later theorem may genuinely prove that graded map surjective.

## Expert-cell cross-check

- **Hodge/cycles:** PASS; source category and rational coefficients remain explicit.
- **Motives/correspondences:** PASS with warning; universal-sheaf examples are scoped and abstract motivation is not silently called Chow.
- **Leray/filtered geometry:** PASS; the critical new coordinate is independently eliminable Hodge pieces.
- **Categorical/arithmetic:** PASS with warning; no target-side rigidity is promoted to source existence.
- **Adversarial:** PASS; `OPEN_ROOT_LIKE` catches circular/relocated surjectivity.
- **Formal/learning-control:** PASS as a diagnostic representation only; no theorem authority is created.

## Information gain

The previous HM1 bridge contract had four fields:

`source object -> source-existence theorem -> realization map -> equality-to-alpha`.

HM1a adds a second valid architecture for higher codimension:

`source-bearing decomposition -> source-realized or Hodge-empty critical pieces -> exact assembly -> alpha reconstruction`.

This exposes a new search axis: **critical-piece elimination**. The task is no longer “make alpha more motivic.” It is to find geometry that either constructs sources for the critical Hodge pieces or proves those pieces contain no Hodge classes.

## Residual opened: HM1b — source-span / Hodge-empty-complement constructor

Find an independently checkable geometric mechanism that, for a materially broader class of smooth projective `X` (ultimately arbitrary `X` if the root is to close), produces a decomposition in which every rational Hodge class lies in:

- the image of explicit algebraic correspondences/cycle-source maps from controlled source varieties; plus
- a complementary Hodge piece proved to have zero rational Hodge classes;

with an exact assembly theorem back to `H^{2p}(X,Q)`.

Or prove for a proposed mechanism that an `OPEN_ROOT_LIKE` critical piece necessarily remains at the tested scope.

This is a new research atom, not a Hodge theorem.
