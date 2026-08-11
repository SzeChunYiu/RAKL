# HM1 pre-candidate bridge audit and same-context expert review

**Authority:** `STRICT_PRE_CANDIDATE / SAME_CONTEXT_REVIEW_ONLY / NO_MATHEMATICAL_CANDIDATE / ROOT_AUTHORITY_NONE`

## Atomic object

For smooth projective complex `X`, codimension `p`, and
`alpha ∈ Hdg^p(X)=H^{2p}(X,Q)∩H^{p,p}(X,C)`, HM1 asks for an exact nonconjectural
source-object criterion producing `Z∈CH^p(X)_Q` with `cl(Z)=alpha`.

The central representation is **realization lifting**: a Hodge class is target-side
data; root progress requires a source-side algebraic object/correspondence whose
realization is exactly that class.

## Source-bound bridge audit

| Route | What is genuinely supplied | Missing arrow / falsifier | HM1 status |
|---|---|---|---|
| Chow motives | exact language for algebraic cycles/correspondences and realization | surjectivity onto arbitrary Hodge morphisms is essentially the root unless a new construction is given | `EQUIVALENT_TO_ROOT` |
| Absolute Hodge | stronger arithmetic/comparison stability | absolute-Hodge -> Chow cycle is not a general theorem; Deligne's abelian-variety result is the contrastive warning | `TARGET_LABEL_ONLY` until lift exists |
| André motivated motives | motivated correspondences with strong formal behavior | motivated -> algebraic; audit every formally adjoined Lefschetz inverse | `OPEN_BRIDGE` |
| Hodge loci | algebraic locus where a class remains Hodge | locus algebraicity -> cycle on each fiber | `SEMANTIC_MISMATCH` |
| Algebraic-correspondence motivation | actual correspondences/universal kernels in successful examples | arbitrary `X,alpha` must be in the image of a source with verified Hodge surjectivity | `SPECIAL_CASE_TOOL` |
| Derived/categorical | actual object/kernel when representability/moduli theorem holds | arbitrary Hodge class -> actual object -> geometric cycle | `SPECIAL_CASE_TOOL` |
| Arithmetic reduction | extra Galois/Tate structure | special-fiber algebraicity and lift back are separate bridges | `TWO_BRIDGE_GAP` |
| Period rigidity | strong target constraints | period condition -> concrete Chow witness | `NO_GENERAL_BRIDGE` |

Primary anchors are the Clay/Deligne official problem description; Deligne's
*Hodge Cycles, Motives, and Shimura Varieties*; Cattani–Deligne–Kaplan;
André 1996 and 2006; Arapura 2006; Perry's 2-Calabi–Yau result; and
Atiyah–Hirzebruch's integral counterexample work.

## Expert cell

### 1. Algebraic-cycles / Hodge lead
**Background:** Hodge structures, Chow groups, cycle maps, positive and negative boundary cases.

Finding: HM1 is an image problem. The decisive datum is not a stronger property of
`alpha` but a geometric preimage. Lefschetz `(1,1)` succeeds because a line
bundle/divisor is an actual object-level lift.

Strongest objection: integral Hodge is stronger than the root and false in general;
Atiyah–Hirzebruch makes coefficient discipline non-negotiable.

Delegated test: every route must end with an explicit `Z` and the equality `cl(Z)=alpha`.

### 2. Motives / correspondences lead
**Background:** Chow motives, standard conjectures, André motivated motives.

Finding: motivated motives are useful precisely because the correspondence category
is enlarged. This gives formal control but changes what counts as a source witness.

Strongest objection: treating a motivated correspondence as algebraic can hide the
standard conjecture on algebraicity of Lefschetz-type operators. André's deformation
paper explicitly separates motivated and algebraic variants.

Delegated test: expand a proposed motivated construction and mark the first operation
without a verified Chow correspondence.

### 3. Derived / categorical lead
**Background:** Fourier–Mukai transforms, K-theory/Chern character, moduli of objects.

Finding: categorical routes have real force when an actual object/kernel exists.
Arapura and Perry provide special-case patterns where algebraic correspondences or
moduli constructions create source witnesses.

Strongest objection: a class in a categorical Hodge lattice is not automatically the
class of an object.

Delegated test: require category, object/kernel, realization map back to `X`, and
class equality before transfer.

### 4. Arithmetic / absolute-Hodge / periods lead
**Background:** comparison isomorphisms, absolute Hodge cycles, spread-out and reduction.

Finding: absolute-Hodge or period rigidity strengthens target-side structure but does
not construct a Chow preimage. Reduction routes have two independent bridges:
algebraicity after reduction and justified return to characteristic zero.

Strongest objection: Tate or period conjectures can be smuggled in as unnamed
reconstruction steps.

Delegated test: label every arithmetic arrow `PROVED`, `CONDITIONAL`, or `MISSING`.

### 5. Adversarial falsification lead
**Background:** theorem-scope audit, counterexamples, hidden assumptions.

Five cheap falsifiers precede proof search:
1. coefficient mismatch;
2. source-category substitution (motivated/categorical called algebraic);
3. Hodge-locus-vs-cycle semantic mismatch;
4. realization-fullness/representability gap;
5. hidden standard/Tate/period/Hodge conjecture.

Finding: motive vocabulary can otherwise turn a tautological reformulation into
apparent progress.

### 6. Formal methods / novelty / learning-control lead
**Background:** exact category/functor specifications, dependency DAGs, novelty,
metacognitive routing.

Finding: the first formal object should be a bridge contract:
`source category -> realization map -> target class -> source witness`.
No Hodge-local strict tool or failure exists yet.

Learning modes: `REFLECTIVE_RESTRUCTURE`, `CONTRASTIVE_DISCRIMINATION`,
`EFFECTUAL_PROBE`. This is the first strict Hodge cycle, so fixation-reset or
method-basis exhaustion is not justified.

## Cross-Millennium memory review

The P-vs-NP success-tool inventory and failure lattice were inspected. Their registered
structural scope is cyclic-intersection/graph-cover complexity, so HM1 records
`NO_RELEVANT_MATCH` rather than pretending those tools or failures transfer. Future
cross-Millennium transfer requires a target-specific applicability or DifferenceWitness.

## Synthesis

The group recommends **no mathematical candidate yet**. The strongest new information
is a route-pruning criterion:

> A motive/categorical/arithmetic route does not advance HM1 merely by giving `alpha`
> a stronger target-side label. It must exhibit a theorem-backed source object or
> correspondence and prove its realization is `alpha`.

This is a research-control conclusion, not a theorem about Hodge classes.

## Next discriminator

After the strict packet audits pass, select one **proved positive family** and one
**near miss**. Instantiate the exact realization Hom-map in both. Identify the
source-object theorem that makes the positive case work and the first missing
hypothesis in the near miss. Only then may a general mathematical candidate be
proposed.

## Unresolved warnings

- a Chow-motive Hom reformulation may be exactly equivalent to Hodge and create no leverage;
- motivated/absolute/categorical classes are not automatically algebraic;
- special categorical moduli theorems may rely on low-dimensional deformation hypotheses;
- arithmetic routes can fail at either Tate algebraicity or lifting;
- same-context roles are not independent peer review.
