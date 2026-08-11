# YM-S1a same-context calibration review — 2026-08-11

**Review class:** `ROLE_SEPARATED_SAME_CONTEXT / NOT_INDEPENDENT_REVIEW`

**Subject:** exact finite-dimensional calibration of `restricted_source_decay_not_full_gap` and the resulting refinement of `G4`.

All roles reviewed the same frozen calibration/evidence packet. Their agreement creates no independent-review authority.

## 1. Transfer-matrix / operator-theory lead

**Background:** spectral theorem, positive semigroups/transfer matrices, Euclidean correlation representations.

**Finding:** `T=diag(1,1/2,1/4)` with `A Omega=e2` is an exact counterexample to the unrestricted implication “decay rate of this source >= full spectral gap.” The correlator probes only the spectral measure of `A Omega`; it says nothing about an orthogonal `e1` sector.

**Strongest objection:** a realistic Yang–Mills source algebra may be much richer than one vector.

**Disposition:** `ACCEPT_CALIBRATION`. Repair requires an explicit density/cyclicity/completeness hypothesis plus a common-rate statement over a sufficiently rich family.

## 2. Lattice-gauge / Hamiltonian lead

**Background:** compact-group lattice gauge theory, physical gauge-invariant Hilbert spaces, spin networks/Peter–Weyl bases.

**Finding:** primary fixed-lattice literature materially narrows the residual. Baez 1996 and Burgio et al. 2000 provide fixed-graph/fixed-lattice gauge-invariant basis constructions, so `G4` should not remain the vague question “do complete sources exist?”

**Strongest objection:** basis completeness is kinematic; a rigorous decay estimate may apply only to a much smaller observable class, and expanding from that class can destroy uniform constants.

**Disposition:** `ACCEPT_WITH_REFINEMENT`. Split `G4a` kinematic completeness from `G4b` common-rate analytic coverage.

## 3. RG / asymptotic-freedom lead

**Background:** lattice RG, weak-bare-coupling trajectory, scaling of physical masses.

**Finding:** closing `G4a/G4b` at fixed cutoff is still logically orthogonal to `G5` and `G6`. A fixed-lattice full gap can vanish after inverse-spacing normalization or fail to transport across the coupling trajectory.

**Strongest objection:** work on source visibility can become a local optimization that does not reduce the dominant continuum debt.

**Disposition:** `ACCEPT_AS_CHEAP_ROUTE_PRUNING`; do not spend a long cycle on basis technology unless a concrete decay theorem can be connected to it.

## 4. Confinement / center-sector lead

**Background:** Wilson loops, center symmetry, confinement criteria, flux sectors.

**Finding:** the calibration reinforces the existing projection warning. Suppression of one extended-source/flux sector does not automatically certify the lowest neutral physical excitation.

**Strongest objection:** area-law and loop-algebra results may still participate in a complete source construction when combined with additional operators.

**Disposition:** `ACCEPT`; retain area-law information as a potentially useful facet, not as a standalone full-gap certificate.

## 5. Constructive-QFT / OS-reconstruction lead

**Background:** reflection positivity, reconstruction, continuum Schwinger functions and Hilbert spaces.

**Finding:** fixed-lattice positive transfer matrices are legitimate calibration objects, but continuum source completeness cannot simply be assumed from continuum QFT theorems before the Yang–Mills continuum theory itself is constructed. The root's existence and spectral obligations remain coupled at `G7`.

**Strongest objection:** the eventual continuum local observable algebra may possess much stronger cyclicity properties than a finite chosen source set.

**Disposition:** `ACCEPT_BOUNDARY`; use such properties only once their hypotheses are available in the constructed theory, not circularly.

## 6. Formal methods / novelty / adversarial assurance lead

**Background:** exact statement binding, counterexample-first checks, dependency and novelty boundaries.

**Finding:** the calibration is completely checkable with rational transfer eigenvalues; no numerical approximation is needed. The inference failure is elementary and should be registered as a scoped failure experience, not claimed as novel mathematics.

**Strongest objection:** calling the diagnosis an impossibility theorem would exceed the current formal/novelty authority.

**Disposition:** `ACCEPT_SUPPORTED_FAILURE`. Record `F-YM-S1A-RESTRICTED-SOURCE-HIDDEN-STATE` at `SUPPORTED`, not `VERIFIED_IMPOSSIBILITY`.

## Preserved disagreement

The RG lead assigns lower strategic value to further fixed-lattice source work than the operator/lattice leads. The group resolves this by imposing a stopping condition: the next source-visibility child should be pursued only if it can bind an **existing rigorous decay class** to an explicit complete/dense physical source family. Otherwise rotate to `G3`, `G5`, or `G6` rather than developing basis formalism for its own sake.

## Joint next-action recommendation

1. Register the hidden-state failure and append the public trace.
2. Freeze `G4a/G4b` as distinct obligations.
3. Wait for exact-head CI on the synchronized branch before generating a theorem candidate.
4. Before `YM-S1a1`, freeze a fresh `ResearchMemoryReview` that includes the new failure.
5. Candidate target, if still selected: a narrowly scoped spectral-exclusion lemma with an explicit dense/cyclic source hypothesis and one common rate; immediately test whether a concrete lattice Yang–Mills observable class satisfies its hypotheses.
6. If no concrete complete decay class is available, rotate to a different `YM-S1` child rather than forcing a theorem.
