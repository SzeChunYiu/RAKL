# HM1a source-producing mechanism matrix — filtration, correspondence, propagation

**Authority:** `SOURCE_BOUND_PRE_CANDIDATE_CONTEXT / NO_MATHEMATICAL_CANDIDATE / ROOT_AUTHORITY_NONE`

**Atom:** `HM1a` — higher-codimension source-exactness. The target is not another stronger label on a rational Hodge class. The target is an independently verifiable mechanism that produces actual Chow-source data and an exact assembly/equality map back to the requested class.

## Primary-source anchors

1. Pierre Deligne, *The Hodge conjecture*, in *The Millennium Prize Problems* (Clay Mathematics Institute, 2006). Root scope: rational Hodge classes on smooth projective complex varieties.
2. Donu Arapura, *Hodge cycles and the Leray filtration*, arXiv:2103.05038 (2021). Theorem 1.2 gives a source-bearing graded-cycle criterion for the Hodge conjecture on the smooth locus of a fibration; Corollary 1.4 reduces the fourfold case to one higher-codimension graded piece, and target Hodge-vanishing can make that remaining surjectivity obligation trivial.
3. Donu Arapura, *Motivation for Hodge cycles*, arXiv:math/0501348 (revised 2005). In special moduli examples, a correspondence dominating the target is built from a universal sheaf and may have a Fourier–Mukai realization; the method transfers Hodge/standard-conjecture information from source curves or surfaces.
4. A. Grothendieck, *Hodge's general conjecture is false for trivial reasons*, Topology 8 (1969), 299–303. Used only as a boundary warning against treating support/coniveau reformulations as automatic source constructors.

## Route matrix

| Route | Source-bearing object | Exact theorem/operation | What can be discharged independently? | First HM1a gap |
|---|---|---|---|---|
| Lefschetz `(1,1)` | line bundle/divisor | exponential exact sequence + Chern class | the `(1,1)` condition kills the obstruction and exactness produces a source | no higher-codimension analogue with the same generality |
| Leray/Chow filtration (Arapura 2021) | `Gr_L^i CH^p(V)` | graded cycle maps plus Hodge exactness and Lefschetz reflections assemble to global Hodge surjectivity | `p=0,1` pieces are known; some higher pieces can be eliminated by proving their Hodge target is zero | arbitrary `X` need not admit a fibration whose remaining critical piece is easier than the root |
| Universal-sheaf / dominating correspondence (Arapura 2005) | algebraic universal sheaf / correspondence in special moduli geometry | correspondence generates/motivates target cohomology from a source whose powers have controlled Hodge theory | source geometry may already satisfy Hodge and the explicit correspondence transports it | no general constructor for arbitrary `X,alpha` |
| Abstract motivated/categorical label | motivated or categorical source in an enlarged category | realization formalism | target structure may become rigid or functorial | Chow algebraization / object representability remains separate |
| H4d1 deformation propagation | existing cycle witness over one fiber | obstruction/formal/algebraization/globalization chain | propagation can be attacked once the witness exists | initial source existence is assumed, not produced |
| Support/coniveau reformulation | support condition / subvariety data | generalized-Hodge-style filtration | may localize where a class could come from | if the support/source-cycle existence assumption already encodes the desired algebraicity, the route is tautological rather than constructive |

## Structural discriminator

The positive higher-codimension pattern is not merely “decompose cohomology.” It is:

`source-bearing decomposition -> independently discharged critical pieces -> exact assembly -> Chow preimage`.

A decomposition has research value only if at least one root-hard obligation is replaced by a strictly cheaper, independently verifiable condition. Two mechanisms in the primary sources show how this can happen:

- **vanishing elimination:** a target graded Hodge piece is proved to contain no Hodge classes, so its cycle-map surjectivity obligation becomes vacuous;
- **source domination:** an explicit algebraic correspondence/kernel maps cohomology from a source family whose Hodge cycle problem is already controlled.

If all surviving graded/source pieces still require the unsolved Hodge-surjectivity statement, the decomposition is a restatement, not progress.

## Cross-lane applicability witness

The cross-Millennium `T-XM-ROOT-BRIDGE-STABILITY-AUDIT` is reused only at its diagnostic authority. The common abstraction is “a valid surrogate/decomposition can lose the root-critical coordinate at an extra bridge.” Here the root-critical coordinate is a Chow source plus exact assembly; there is no continuum scaling variable. The cheapest repeat-failure test is therefore categorical/logical: expand the proposed route until every remaining source-surjectivity obligation is visible, and reject it if one is exactly the original unsolved Hodge image problem in new notation.

## Frozen next discriminator

Before any theorem candidate, calibrate a typed **source-bearing decomposition certificate** with fields:

`(source_groups, target_Hodge_pieces, cycle_or_correspondence_maps, discharged_piece_reasons, assembly_theorem, alpha_reconstruction)`.

Run it on:

1. divisor/Picard exactness;
2. Arapura's Leray fourfold reduction including a Hodge-vanishing case;
3. an Arapura universal-sheaf correspondence example at its published scope;
4. an abstract motivated/categorical route with no Chow algebraization;
5. H4d1 witness propagation, which must fail the initial-source field.

The discriminator succeeds only if it separates genuine source-producing reductions from root-equivalent or wrong-category substitutes.

No theorem candidate is introduced by this matrix.
