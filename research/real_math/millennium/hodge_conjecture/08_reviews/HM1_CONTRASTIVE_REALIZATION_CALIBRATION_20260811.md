# HM1 contrastive realization calibration — divisor success vs absolute-Hodge near miss

**Authority:** `SOURCE_BOUND_CONTRASTIVE_DISCRIMINATOR / SAME_CONTEXT_REVIEW_ONLY / NO_MATHEMATICAL_CANDIDATE / ROOT_AUTHORITY_NONE`

**Atom:** `HM1` — for a smooth projective complex variety `X`, codimension `p`, and
`alpha in H^{2p}(X,Q) ∩ H^{p,p}(X,C)`, identify a nonconjectural source-side
construction producing `Z in CH^p(X)_Q` with `cl_Q(Z)=alpha`.

This packet executes the frozen `HM1-E07` discriminator. It does **not** propose a
general Hodge lemma. The purpose is to isolate the exact source-existence theorem
that makes a solved case work and compare it with a structurally close target-side
strengthening that still lacks a Chow preimage theorem.

## Primary-source anchors

1. Pierre Deligne, *The Hodge Conjecture*, official Clay problem description.
   Deligne states the rational root conjecture, gives the codimension-one proof via
   the exponential sequence, explains that progress on motives is blocked by the
   lack of methods to construct interesting algebraic cycles, and notes that Hodge
   classes on abelian varieties are absolutely Hodge and even motivated without
   thereby becoming known algebraic.
2. Pierre Deligne, *Cycles de Hodge absolus et périodes des intégrales des variétés
   abéliennes*, Mémoires SMF 2 (1980), 23–33, DOI `10.24033/msmf.276`.
3. Yves André, *Pour une théorie inconditionnelle des motifs*, Publ. Math. IHÉS 83
   (1996), 5–49.
4. Yves André, *Déformation et spécialisation de cycles motivés*, JIMJ 5 (2006),
   563–603, DOI `10.1017/S1474748005000265`. Its abstract explicitly separates the
   unconditional motivated-cycle deformation statement from the algebraic-cycle
   variant, which follows from the standard conjectures.

## Exact realization maps

### Positive calibration P1 — codimension one

For every smooth projective complex `X`, use the genuine source category of line
bundles/divisors:

`Pic(X) ⊗ Q ≅ CH^1(X)_Q  --c1=cl_Q-->  Hdg^1(X)`

with

`Hdg^1(X) = H^2(X,Q) ∩ H^{1,1}(X,C)
           = Hom_{Q-HS}(Q(0), H^2(X,Q)(1)).`

Let `alpha in Hdg^1(X)`. Choose `m>0` so that `m alpha` is integral modulo torsion.
The exponential exact sequence

`0 -> Z -> O_X -> O_X^* -> 0`

gives the connecting first-Chern-class map `Pic(X)=H^1(X,O_X^*) -> H^2(X,Z)`.
Because a `(1,1)` class maps to zero in the `H^{0,2}` quotient of `H^2(X,O_X)`,
exactness supplies a line bundle `L` with `c1(L)=m alpha`. A meromorphic section
of `L` gives a divisor `D`, hence `(1/m)D in CH^1(X)_Q` realizes `alpha`.

**Load-bearing source theorem:** not merely that `alpha` has a stronger target
property, but exactness of a source-object sequence that turns the Hodge-type
vanishing condition into existence of a line bundle/divisor preimage.

### Near miss N1 — absolute Hodge classes on abelian varieties

For an abelian variety `A` and arbitrary codimension `p`, the root map remains

`CH^p(A)_Q  --cl_Q-->  Hdg^p(A)
             = Hom_{Q-HS}(Q(0), H^{2p}(A,Q)(p)).`

Deligne proves that Hodge classes on abelian varieties are **absolute Hodge**.
Thus one can strengthen the target label

`alpha in Hdg^p(A)  =>  alpha is absolute Hodge`

without constructing any `Z in CH^p(A)_Q`.

The first missing arrow is therefore not comparison stability but

`absolute-Hodge target class  --MISSING-->  Chow source witness`.

A theorem making this arrow surjective for arbitrary abelian varieties and
codimension would in particular solve the Hodge-conjecture image problem on that
class of varieties. The absolute-Hodge upgrade is therefore a genuine structural
near miss: it adds rigidity to the target but supplies no general source-existence
mechanism comparable to the exponential-sequence proof in codimension one.

### Near miss N2 — motivated correspondences

André's motivated category enlarges the source correspondence calculus by formally
adjoining inverse Lefschetz operations. This gives strong unconditional formal
properties, but the source object is then **motivated**, not necessarily a Chow
correspondence. André's deformation work explicitly records the boundary: the
algebraic-cycle deformation variant follows from the standard conjectures, while
the motivated-cycle variant is unconditional.

The first missing arrow is

`motivated correspondence  --MISSING without extra input-->  algebraic/Chow correspondence`.

Calling the left-hand object "motivic" does not discharge the right-hand
algebraization obligation.

## Contrastive expert cell

These are role-separated same-context passes, not independent peer review.

### Algebraic-cycles / Hodge lead
**Background:** Picard groups, Chow groups, Hodge structures, cycle maps.

**Finding:** P1 works because Hodge type is the vanishing condition in an exact
sequence whose preceding term is an actual geometric source object. The useful
analogy is exact source reconstruction, not generic cohomological rigidity.

**Delegated next test:** any higher-codimension proposal must identify the source
object and the exact theorem that produces it; `alpha` having an extra target label
is insufficient.

### Motives / correspondences lead
**Background:** Chow motives, motivated cycles, realization functors, standard
conjectures.

**Finding:** a fullness statement for Betti/Hodge realization is dangerous as a
research objective because Deligne's official description places full faithfulness
of the motive-to-Hodge functor at essentially Hodge-conjecture strength once the
relevant algebraicity assumptions are admitted.

**Delegated next test:** expand every proposed inverse-Lefschetz or projector step
until each operation is either an actual Chow correspondence or an explicitly
registered conjectural/motivated operation.

### Arithmetic / absolute-Hodge lead
**Background:** absolute Hodge cycles, comparison isomorphisms, abelian varieties.

**Finding:** Deligne's theorem is a clean negative calibration for target-label
search: substantial comparison/arithmetic rigidity can be proved while the Chow
preimage remains open.

**Delegated next test:** no arithmetic route advances HM1 unless it adds a proved
characteristic-zero source witness or a proved lift of a special-fiber source
witness.

### Derived / categorical lead
**Background:** Fourier–Mukai kernels, K-theory, Chern characters, moduli of
objects.

**Finding:** the P1 pattern favors routes where an object-existence/moduli theorem
precedes the realization statement. A categorical Hodge lattice without an
object/kernel representability theorem is structurally N1, not P1.

**Delegated next test:** demand an actual object/kernel and a theorem that its
Chern/cycle realization equals the requested class.

### Adversarial falsification lead
**Background:** theorem-scope audit, counterexamples, hidden conjectures.

**Finding:** five route killers are now executable as a checklist:
`TARGET_LABEL_ONLY`, `SOURCE_CATEGORY_SUBSTITUTION`, `ROOT_EQUIVALENT_FULLNESS`,
`HIDDEN_STANDARD_TATE_HODGE`, and `REALIZATION_NOT_SHOWN_EQUAL_TO_ALPHA`.

**Delegated next test:** classify any proposed HM1 route against all five before
proof search.

### Formal-methods / learning-control lead
**Background:** typed interfaces, proof-DAG dependencies, research-mode control.

**Finding:** the useful abstraction is a four-field bridge contract:

`(source object, source-existence theorem, realization map, equality-to-alpha proof)`.

P1 fills all four fields. N1 has only the target property; N2 fills a source field
in the wrong category. This is a sharper representation than "find stronger
properties of Hodge classes."

**Learning-mode disposition:** `CONTRASTIVE_DISCRIMINATION` succeeded in exposing
the missing coordinate. `REFLECTIVE_RESTRUCTURE` remains appropriate; there is
still no evidence for method-basis exhaustion.

## Result

The discriminator separates three logically different route types:

1. **source-producing** — an unconditional theorem constructs an algebraic
   source object and proves its realization equals `alpha` (P1 pattern);
2. **target-enriching** — a theorem proves extra properties of `alpha` but adds no
   Chow preimage theorem (N1 pattern);
3. **source-category-relaxing** — a theorem constructs a witness only after
   enlarging the correspondence category, leaving algebraization open (N2 pattern).

Only type (1), or a type (2)/(3) route with a new proved algebraization arrow,
can close an HM1 proof-DAG edge.

This is a route-classification result for the research process, not a new theorem
in algebraic geometry.

## Residual opened: HM1a — higher-codimension source-exactness gap

Freeze the next search question as:

> Find a non-tautological higher-codimension source-object mechanism whose
> existence theorem is triggered by verifiable structure of a rational Hodge class
> and whose output is an actual element of `CH^p(X)_Q`; or prove that a proposed
> mechanism merely re-encodes realization fullness/Hodge/standard/Tate/period
> algebraicity.

The search should prioritize **source-existence mechanisms** (moduli/object
existence, correspondences from proved source families, obstruction-vanishing
theorems, explicit cycle-producing constructions) rather than accumulating
stronger target labels.

No mathematical candidate for HM1a is authorized until its own current
context/memory/trace gate is frozen if the representation materially changes.

## Authority boundary

`CONTRASTIVE_DISCRIMINATOR_COMPLETED / ROUTE_CLASSIFICATION_ONLY /
NO_GENERAL_SOURCE_LIFT / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`.
