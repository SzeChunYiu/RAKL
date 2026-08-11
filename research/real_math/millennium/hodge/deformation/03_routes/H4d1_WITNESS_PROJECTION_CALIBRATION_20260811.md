# H4d1 witness-projection calibration

Date: 2026-08-11

Authority: `SOURCE_BOUND_CALIBRATION / ROUTE_PRUNING_ONLY / NO_THEOREM_CANDIDATE / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`

Root control: issue #86  
Parent atom: `H4d1`

## Question fixed by the parent packet

Let `f : X -> S` be a smooth projective family of complex varieties, let `s0 in S`, and let `alpha` be a flat rational cohomology class that is algebraic on `X_s0`. Let `T` be an irreducible local Hodge-locus branch through `s0` along which `alpha` remains of type `(p,p)`.

The parent atom asks for the weakest independently checkable condition forcing actual algebraic-cycle witnesses for `alpha` to lift along `T`. The strict packet already separated four arrows:

`Hodge-locus membership -> witness lifting -> algebraization -> domination/global continuation`.

This calibration addresses only the **witness-lifting interface** and deliberately does not collapse the later arrows.

## Source-bound facts used in this calibration

1. **Hodge locus is a base-space statement.** Cattani–Deligne–Kaplan prove algebraicity of the locus where a fixed integral Hodge class remains of Hodge type in a geometric variation. This controls the admissible base locus, not existence of algebraic-cycle witnesses over its points.
   - E. Cattani, P. Deligne, A. Kaplan, *On the Locus of Hodge Classes*, arXiv:alg-geom/9402009.

2. **Semiregularity is a genuine obstruction detector in special deformation problems.** Buchweitz–Flenner construct a general semiregularity map and relate it to deformation obstruction theory; Pridham realizes the Buchweitz–Flenner map via derived deformation theory and shows that it annihilates all obstructions in that framework.
   - R.-O. Buchweitz, H. Flenner, *A Semiregularity Map for Modules and Applications to Deformations*, arXiv:math/9912245.
   - J. P. Pridham, *Semiregularity via derived deformation theory*, arXiv:1112.6001.

3. **For a semiregular chosen codimension-one map, Hodge persistence can be equivalent to vanishing of the branch-relative obstruction.** Nishinou identifies the next-order obstruction as a class in the normal-sheaf cohomology and, under semiregularity, proves that persistence of the cycle class as Hodge is equivalent to vanishing of the projected Kodaira–Spencer/relative obstruction class; this yields relative deformation of the chosen map. Nishinou also recalls Bloch's local-complete-intersection result in arbitrary codimension under semiregularity.
   - T. Nishinou, *Deformation of pairs and semiregularity*, arXiv:2009.01651, especially Proposition 6, Remark 7, Lemma 10 and the introduction's statement of Bloch's theorem.

4. **Formal cycle-class deformation is a distinct layer.** Bloch–Esnault–Kerz study a formal deformation problem for rational algebraic cycle classes and relate expected lifting to additional Chow–Künneth-type structure, including abelian-scheme applications. Their result does not by itself identify a single global relative algebraic cycle over an arbitrary Hodge-locus component.
   - S. Bloch, H. Esnault, M. Kerz, *Deformation of algebraic cycle classes in characteristic zero*, arXiv:1310.1773.

These sources are used only at their stated scope. No source above proves the rational Hodge conjecture.

## Typed local witness interface

The calibration rejects the shortcut “take one Hilbert point representing `alpha`,” because the rational Hodge conjecture permits signed rational combinations of irreducible algebraic cycles.

For a **fixed central algebraic witness**

`z0 = sum_i q_i [Z_i]`, with `q_i in Q`,

choose a common denominator `N>0` and integers `m_i=N q_i`. Split the finite support into positive and negative parts. Locally around this chosen witness, use a finite product/disjoint union of relative Hilbert/Chow branches for the selected components, together with the class constraint

`sum_i m_i cl(Z_i(s)) = N alpha_s`.

This is only coefficient-safe **bookkeeping for the chosen finite witness**. It is not a claim that one fixed Hilbert component parametrizes every rational cycle or that every component deforms.

The resulting local interface is recorded abstractly as

`pi_alpha : W_alpha -> T`,

with six separately typed obligations:

1. `COEFFICIENT_CLASS` — the signed integer/rational encoding and the equality of the realized class to `alpha`;
2. `TANGENT` — the differential of `pi_alpha` and the tangent directions of the chosen Hodge branch;
3. `OBSTRUCTION` — the obstruction object for lifting a witness over an infinitesimal base thickening;
4. `FORMAL` — compatible all-order lifts over the relevant Artin/formal thickenings;
5. `ALGEBRAIZATION` — passage from formal data to an actual algebraic family in the chosen witness category;
6. `GLOBAL_CONTINUATION` — domination of the desired irreducible branch after monodromy/component issues are handled.

A route passes H4d1 only if it closes every obligation that it uses. Success at an earlier obligation cannot be substituted for a later one.

## Five calibration cases

### C1 — divisor/Picard control

For codimension one, the divisor/line-bundle setting supplies an unusually strong source category and deformation theory. This is a positive control for the principle that a cohomological Hodge condition can coincide with geometric liftability when the witness category has the required exactness/obstruction control.

**Calibration verdict:** `POSITIVE_CONTROL`, but structurally exceptional. Higher codimension cannot inherit Picard representability by analogy alone.

### C2 — semiregular chosen witness

Nishinou's obstruction calculation gives the key local pattern. Given an `m`-th order lift, the next-order obstruction is represented in normal-sheaf cohomology. Under the semiregularity hypothesis, the Hodge-persistence condition detects that obstruction strongly enough to force it to vanish. Iteration then supplies the local relative deformation in the source theorem's scope.

**Calibration verdict:** `POSITIVE_CONDITIONAL_CONTROL`.

**Load-bearing coordinate:** not merely “the class remains Hodge,” but the existence of a sufficiently faithful map from the geometric obstruction space to the cohomological/Hodge obstruction data.

### C3 — non-semiregular hostile control

If the semiregularity detector is not sufficiently injective on the relevant geometric obstruction directions, Hodge persistence can only show that the obstruction lies in the detector kernel. The current method then cannot infer that the geometric obstruction itself vanishes.

This is **not** a claim that every non-semiregular witness fails to deform. It is a route-pruning statement: Hodge persistence by itself does not close the lifting arrow through this mechanism once detector faithfulness is lost.

**Calibration verdict:** `METHOD_INCONCLUSIVE / DETECTOR_GAP_EXPOSED`.

### C4 — rational signed-combination control

A rational class may be represented by a signed finite combination. The local witness interface must therefore preserve the coefficient vector and the class equation across all selected components. A theorem proved only for one effective relative subscheme does not automatically apply to an arbitrary rational witness.

**Calibration verdict:** `COEFFICIENT_SCOPE_GUARD`. Any candidate that silently replaces a rational signed cycle by one effective Hilbert point fails the root coefficient contract.

### C5 — formal-only/globalization stress control

A compatible formal/pro-cycle lift, even if rigorously established, closes only `FORMAL`. The H4d1 root-child still needs an algebraization theorem in the chosen witness category and a separate argument for domination/global continuation over `T`.

**Calibration verdict:** `FORMAL_NOT_GLOBAL`. Bloch–Esnault–Kerz is a useful positive formal analogue under additional structure, not a general globalization theorem for H4d1.

## Expert cell: delegated checks and synthesis

These are role-separated same-context passes, not independent reviews.

### 1. Hodge/VHS lead

**Background:** variations of Hodge structure, infinitesimal period maps, Hodge loci.  
**Delegated check:** determine exactly what information “`alpha` remains `(p,p)` along `T`” supplies.  
**Finding:** it supplies a cohomological compatibility condition on base directions. It does not identify a geometric witness space or prove local surjectivity of its projection.  
**Strongest objection:** a proposed “criterion” could simply restate tangent equations for the Hodge locus.  
**Vote:** `ACCEPT_CALIBRATION / BLOCK_THEOREM_GENERATION` until the geometric detector is independently defined.

### 2. Algebraic-cycle / witness-space lead

**Background:** Chow/Hilbert parameter spaces, cycle classes, rational equivalence.  
**Delegated check:** make the witness interface honest for rational coefficients.  
**Finding:** local bookkeeping can clear denominators and retain a fixed finite signed combination of chosen components; a single effective Hilbert point is insufficient in general.  
**Strongest objection:** the local product of component spaces must not be mistaken for a global fine moduli space of rational cycles.  
**Vote:** `ACCEPT_WITH_SCOPE_GUARD`.

### 3. Deformation/obstruction lead

**Background:** normal-sheaf and derived obstruction theory, semiregularity.  
**Delegated check:** identify the first load-bearing arrow between Hodge persistence and witness lifting.  
**Finding:** Nishinou's calculation isolates a branch-relative obstruction class obtained from the Kodaira–Spencer direction; semiregularity supplies the faithfulness needed to infer its vanishing from the Hodge condition.  
**Strongest objection:** full semiregularity may be much stronger than necessary for one fixed Hodge branch.  
**Vote:** `OPEN_SMALLER_ATOM` on branch-restricted obstruction detection.

### 4. Derived/formal-methods lead

**Background:** cotangent complexes, derived deformation functors, formal algebraization boundaries.  
**Delegated check:** determine whether a weaker detector can be stated without becoming tautological.  
**Finding:** “injective on the actual obstruction” is vacuous unless the relevant obstruction subspace is defined independently. A useful weaker condition needs a geometrically computable envelope of all branch-generated obstruction classes.  
**Strongest objection:** defining the envelope by “all obstructions that occur” can merely rename the unknown.  
**Vote:** `REVISE_TO_INDEPENDENT_ENVELOPE`.

### 5. Adversarial falsification lead

**Background:** counterexample-first proof auditing and scope failure.  
**Delegated check:** try to break the proposed reduction.  
**Finding:** three immediate failure modes survive: (i) detector kernel, (ii) signed-cycle coefficient loss, and (iii) formal lift without algebraization/global continuation. None is repaired by Hodge-locus algebraicity.  
**Strongest objection:** even a perfect local obstruction detector does not solve the root initial-existence gap because H4d1 starts from an already algebraic witness.  
**Vote:** `ACCEPT_ROUTE_PRUNING / ROOT_AUTHORITY_NONE`.

### 6. Novelty/research-value lead

**Background:** literature-bound route comparison and rediscovery control.  
**Delegated check:** separate established semiregularity facts from the useful new research question.  
**Finding:** the semiregularity implication itself is established literature. The research value lies only in isolating and testing a potentially weaker **branch-restricted** detector condition, not in relabeling known semiregularity as a new theorem.  
**Strongest objection:** a “weak semiregularity” definition can be tautological or already standard under another name.  
**Vote:** `NO_NOVELTY_CLAIM / FRESH_CONTEXT_REQUIRED_FOR_CHILD`.

## Result: sharper residual H4d1a

The five calibrations and six-role review localize the first unresolved lifting coordinate more sharply than “generalize semiregularity.”

### `H4d1a` — branch-restricted semiregularity-envelope problem

For a fixed central lci/suitably derived witness and a fixed Hodge-locus branch `T`, construct an **independently defined, geometrically computable obstruction envelope**

`B_{T,m} subseteq Ob_m`

at each required infinitesimal order such that:

1. every obstruction produced by attempting to lift the chosen witness along `T` lies in `B_{T,m}`;
2. the Hodge/semiregularity detector is injective on `B_{T,m}`;
3. `B_{T,m}` is defined from prior geometric/deformation data, not from the desired vanishing of the obstruction;
4. the condition is demonstrably weaker than full semiregularity on at least one nontrivial calibration family, or else the attempted weakening is recorded as a failure;
5. the construction is stable enough across successive Artin orders to support the `FORMAL` obligation.

If Hodge persistence forces the detector image of the branch-relative obstruction to vanish and (1)–(2) are independently proved, then the obstruction vanishes **within that conditional deformation problem**. That logical implication is elementary; the hard research content is constructing and validating `B_{T,m}` without circularity.

This child atom remains strictly conditional propagation from an already algebraic central witness. Even a complete solution of `H4d1a` would leave `ALGEBRAIZATION`, `GLOBAL_CONTINUATION`, and the root initial-existence problem open.

## Cheapest next falsifiers

Before any H4d1a criterion candidate:

1. freeze a fresh H4d1a context/memory/trace packet;
2. reconstruct the divisor/Picard and semiregular lci cases and identify the smallest known obstruction space actually used by the proof;
3. search for a non-semiregular example where branch geometry forces a proper subspace of the full obstruction group; if no such proper envelope is found, record that the proposed weakening has no evidence of being weaker;
4. test whether the proposed envelope survives the next Artin order rather than only first order;
5. separately retain the formal-to-algebraic and monodromy/globalization residuals instead of hiding them in the lifting lemma.

## Meta-learning observation

The useful re-representation in this cycle was to replace the broad question “does the Hodge class deform algebraically?” by a typed chain in which the Hodge condition is an **observable/base constraint** and the cycle deformation has an independent **witness obstruction**. The failure mode exposed by the hostile calibration is therefore not “Hodge theory is too weak” in general; it is specifically **loss of faithfulness between cohomological compatibility and the geometric obstruction directions actually generated by the chosen branch**.

This observation supports `CONTRASTIVE_DISCRIMINATION` and `REFLECTIVE_RESTRUCTURE` as search modes for this atom. It supplies no mathematical authority.
