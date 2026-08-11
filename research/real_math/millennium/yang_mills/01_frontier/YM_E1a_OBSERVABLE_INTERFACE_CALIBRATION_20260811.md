# YM-E1a observable-interface calibration — 2026-08-11

**Authority:** `PRE_CANDIDATE_CALIBRATION / NO_MATHEMATICAL_CANDIDATE / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`

**Root control:** issue #85.  
**Parent atom:** `YM-E1a` — obtain cutoff-uniform control of renormalized gauge-invariant observable expectations strong enough for a non-trivial OS-compatible compact continuum limit.

This packet executes the already-frozen `NEXT_STEP_PROPOSED` action. It does not propose a continuum theorem.

## Expert cell

These are role-separated same-context analyses, not independent reviews.

1. **Constructive-QFT lead** — asks whether the interface can actually generate continuum Schwinger functions and a reconstruction-quality observable algebra.
2. **Gauge/RG lead** — audits exact gauge invariance, block/refinement maps, source mixing, counterterms and compatibility with multiscale RG.
3. **Adversarial mathematical-physics lead** — searches for support leakage, limit-interchange failure, trivial continuum response and hidden locality assumptions.
4. **Formal-methods lead** — reduces the interface to finite-cutoff objects, explicit maps and falsifiable matrix/derivative obligations.
5. **Novelty/frontier lead** — distinguishes standard generating-functional/renormalization facts from the genuinely missing marked-RG transfer.
6. **Cross-domain transfer lead** — tests the proposal-only instrumentation analogy: if an output matters, carry it as a marked state through the transformation rather than infer it from an unmarked marginal after the fact.

## Exact comparison coordinates

An observable interface is useful only if its role is explicit on all of these coordinates:

1. finite-cutoff definition;
2. exact gauge transformation law;
3. common/refinement embedding across lattice spacings;
4. renormalization and operator-mixing closure;
5. reflection action and positive-half-space support;
6. locality or controlled quasi-locality;
7. topology/mode of continuum convergence;
8. cutoff-uniform bounds strong enough to pass expectations/correlations to the limit;
9. non-triviality/separation witness;
10. cheapest failure test.

## Family A — Wilson loops / loop-cylinder observables

### Strengths

- Exact lattice gauge invariance is built in.
- Finite products of loops supported in a positive Euclidean half-space live naturally inside the fixed-cutoff reflection-positive Wilson framework.
- Loops provide direct geometric probes of holonomy and can be kept as bounded cutoff observables before renormalization.

### Load-bearing defects

- Continuum loop functions have nontrivial perimeter/cusp/intersection renormalization structure; boundedness of the bare lattice trace is therefore not a non-trivial continuum-limit theorem.
- A loop algebra is nonlocal. Even convergence of a separating family of renormalized loops does not automatically supply the local gauge-invariant Schwinger-field algebra required for a Wightman/OS-strength construction.
- Refinement must specify how a physical contour is approximated at every cutoff and how the geometry-dependent renormalization follows that approximation.

### Cheapest falsifiers

1. **trivialization test:** after the proposed normalization, does a fixed physical smooth-loop expectation collapse to a cutoff-independent trivial value or fail to be Cauchy?
2. **geometry-instability test:** do two admissible lattice approximations of the same smooth physical contour require incompatible renormalizations or yield inequivalent limits?
3. **reflection-support test:** does an RG/refinement map force a positive-half-space loop source to acquire terms crossing the reflection plane?

**Calibration vote:** `RETAIN_AS_RP_CORE_PROBE`, not sufficient alone.

## Family B — positive-flow-time local gauge-invariant composites

Representative probes include flowed energy-density/curvature composites at physical flow time `t>0`.

### Strengths

- The Yang–Mills gradient flow is gauge covariant and produces smooth positive-flow-time fields.
- Perturbatively, gauge-invariant positive-flow-time composite correlations are UV finite once the underlying 4D theory is renormalized.
- The physical smoothing scale makes this family attractive for detecting non-trivial continuum response without immediately facing the full `t=0` operator-mixing problem.

### Load-bearing defects

- The perturbative finiteness result assumes an already-renormalized underlying 4D theory; it cannot close constructive existence.
- Fixed `t>0` is not the final local `t=0` field algebra.
- Four-dimensional flow smears in Euclidean time. Standard OS positive-half-space support is therefore not inherited automatically; no reflection-positivity theorem for this use is assumed in this packet.
- Sending `t -> 0` reopens local composite renormalization/mixing obligations.

### Cheapest falsifiers

1. **reflection-leakage test:** show that a positive-time-support functional of the flowed field depends on unflowed variables across the reflection plane at any `t>0`; if so, it cannot be admitted into the OS core without an additional theorem.
2. **two-limit test:** compare `a -> 0` at fixed `t` with a coupled `t=t(a)->0`; failure of a controlled commuting/diagonal limit blocks use as a local-field bridge.
3. **non-triviality-only test:** if the family converges but cannot separate continuum states or recover a local algebra, classify it only as a diagnostic probe.

**Calibration vote:** `RETAIN_AS_UV_REGULAR_DIAGNOSTIC`, not OS-core authority.

## Family C — source-inserted generating functional

For a finite cutoff `a` and a finite family of gauge-invariant observables `O_i^(a)`, introduce a bookkeeping source

`F_a(J) = log < exp(sum_i J_i O_i^(a)) >_a - log <1>_a`,

or the corresponding normalized generating functional. The source is not a new physical interaction here; derivatives at `J=0` encode connected observable correlations.

### Strengths

- Exact gauge invariance is retained when every source coordinate couples to a gauge-invariant observable.
- It converts “control all observable expectations” into a marked-RG problem: carry `J`, source mixing and derivative estimates through each scale.
- Wilson loops and local/flowed composites can coexist as different coordinates rather than forcing one family to serve every role.
- Uniform holomorphy/differentiability in a cutoff-independent neighborhood of `J=0`, together with convergence, would turn correlation convergence into an explicit derivative problem rather than an after-the-fact inference.

### Load-bearing defects

- Uniform analyticity is itself a strong theorem obligation; writing `F_a(J)` does not prove it.
- RG can generate an enlarging source/operator basis. Uncontrolled source-sector dimension or mixing is a direct closure failure.
- Reflection positivity must be checked on the correlation algebra generated by admissible positive-half-space source observables; arbitrary source deformations need not preserve a positivity interpretation.
- A finite source family cannot by itself establish the full local observable algebra. A graded/separating family and compatibility across grades would eventually be required.

### Cheapest falsifiers

1. **one-step source-closure test:** differentiate one exact RG step at `J=0`; if the insertion generates an uncontrolled family of new operators/supports, finite/controlled closure fails immediately.
2. **uniform-derivative test:** identify whether the source derivative bound picks up a factor diverging with the UV depth or inverse lattice spacing.
3. **reflection-cone test:** on a finite set of positive-half-space source observables, form the reflection Gram matrix `G_ij=<Theta O_i O_j>`; any proposed renormalization/mixing map must preserve positive semidefiniteness at the exact cutoff level and under the proposed limit.
4. **trivial-response test:** after renormalization, if every first/second derivative relevant to a purported separating family converges to the Gaussian/trivial value forced by the normalization, the interface has not established non-trivial Yang–Mills.

**Calibration vote:** `SELECT_AS_INTERFACE_WRAPPER`, not a theorem candidate.

## Cell synthesis

The three “families” should not be treated as mutually exclusive competitors. The strongest representation is a **two-stratum observable system carried by a source-marked RG wrapper**:

- **Stratum RP:** renormalized Wilson-loop / loop-cylinder observables whose unrenormalized cutoff representatives have exact gauge invariance and controlled positive-half-space support. Their job is to anchor fixed-cutoff reflection positivity and gauge-invariant separation.
- **Stratum UV diagnostic:** positive-flow-time local gauge-invariant composites. Their job is to test continuum response, scale dependence and non-triviality with reduced UV singularity. They receive no OS-core authority until reflection/support and `t -> 0` bridges are separately proved.
- **Wrapper:** a finite, then graded, source-generating functional whose derivatives expose exactly how observable insertions transform and mix under the RG.

This re-representation prevents three recurring category errors:

1. treating unmarked effective-action control as observable control;
2. treating a UV-finite probe as automatically reflection-positive/local;
3. treating a reflection-positive nonlocal loop family as automatically sufficient for a local reconstructed QFT.

## Newly exposed child atom

`YM-E1a1` — **marked one-step RG closure**.

Before any theorem candidate is generated, freeze a fresh context/memory/trace packet for this child question:

> For a finite source family of positive-half-space gauge-invariant lattice observables, can one exact Balaban-style RG step be extended to a marked/source sector with an explicit renormalization/mixing map, controlled support enlargement, and derivative bounds whose constants do not already diverge with the UV depth?

The first source family should be deliberately small and adversarially chosen. A smooth simple Wilson-loop/cylinder insertion is the default RP-core calibration; a positive-flow-time composite may be carried in parallel only as a diagnostic source coordinate.

### Branching discriminator

- **If controlled source closure fails at one step:** record the exact generated operator/support family as a failure-cause atom; do not attempt a full multiscale theorem.
- **If closure exists but constants grow per step:** open the amortization/uniformity atom before iterating.
- **If one-step closure and scale-neutral bounds survive:** only then is a multiscale marked-RG candidate worth generating under a fresh strict packet.

## Authority after calibration

`YM-E1a` remains open. No continuum measure, OS reconstruction, non-trivial 4D theory, correlation decay theorem, or mass gap has been proved. The calibration only reduces the next research question from “control gauge-invariant observables” to the falsifiable source-marked one-step RG closure problem above.
