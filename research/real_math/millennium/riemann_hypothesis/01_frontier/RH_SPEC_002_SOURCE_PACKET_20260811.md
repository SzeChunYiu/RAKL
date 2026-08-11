# RH-SPEC-002 source packet — spectral-limit stability and pollution

Date: 2026-08-11. Authority: `PRIMARY_SOURCE_CONTEXT / PRE_CANDIDATE / NO_MATHEMATICAL_CANDIDATE / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`.

## Root-coupled question

`RH-SPEC-002` asks for the weakest independently checkable finite-to-global convergence package that can transport real finite/restricted RH approximant zeros or spectra to the **complete** zero multiset of the Riemann `Xi` function, including multiplicity, without spectral pollution, missing/escaped zeros, noncommuting limits, or circular normalization.

This packet is a source-to-obligation map, not a proof.

## S1 — finite-prime self-adjoint spectral triples

**Alain Connes, Caterina Consani, Henri Moscovici, _Zeta Spectral Triples_, arXiv:2511.22755 (2025).**

Theorem 1.1, under the source's explicit hypotheses that the smallest eigenvalue of the finite restriction `QW_lambda^N` is simple and its ground-state eigenvector is even, proves for the associated rank-one operator:

- self-adjointness on the stated direct-sum Hilbert space;
- a regularized determinant proportional to the ground-state Fourier transform;
- the entire-function zeros are real and coincide with the approximant operator spectrum.

The paper explicitly states that numerical spectra appear to converge toward zeta zeros as `N,lambda -> infinity`, that a rigorous proof of this convergence would establish RH, and that convergence of suitably normalized regularized determinants toward `Xi` is a natural route.

**Bound obligation:** finite-stage self-adjointness/real zeros are source-supported; joint-limit convergence, hypothesis stability, normalization, and exact `Xi` identification remain open.

## S2 — general real-zero theorem

**Alain Connes and Walter D. van Suijlekom, _Quadratic Forms, Real Zeros and Echoes of the Spectral Action_, arXiv:2511.23257 (2025).**

For a lower-bounded self-adjoint convolution-type operator on a finite interval with a simple isolated lowest eigenvalue and an even eigenfunction, the paper proves that the Fourier transform of that eigenfunction has only real zeros. The proof uses finite-dimensional structure and Hurwitz zero stability.

**Bound obligation:** a legitimate real-zero transport mechanism exists once the operator hypotheses and local-uniform analytic limit are available; it does not prove arithmetic convergence to `Xi`.

## S3 — independent finite-interval self-adjoint limit programme

**Masatoshi Suzuki, _Weil's quadratic form via the screw function_, arXiv:2606.09096 (2026).**

The paper gives an unconditional continuous-function framework for the Weil quadratic form and formulates a conjecture that the self-adjoint operator whose eigenvalues are the imaginary parts of the nontrivial zeta zeros arises as the `a -> infinity` limit of self-adjoint operators from nonlocal first-order differential realizations on `[-a,a]`.

**Bound obligation:** again the finite-stage operator structure is available while the global operator/spectral limit remains the conjectural bridge.

## S4 — hostile spectral-pollution source

**Michael Levitin and Eugene Shargorodsky, _Spectral pollution and second order relative spectra for self-adjoint operators_, arXiv:math/0212087; IMA J. Numer. Anal. 24 (2004), 393–416.**

The paper studies spurious spectral values produced by projection methods for self-adjoint operators and gives model examples plus a second-order relative-spectrum strategy.

**Bound obligation:** self-adjoint finite/projected approximants can produce misleading spectral information. An RH operator-convergence theorem must state hypotheses that exclude the relevant pollution mechanism rather than infer exactness from finite-stage self-adjointness.

## S5 — abstract pollution localization/avoidance

**Mathieu Lewin and Eric Séré, _Spectral Pollution and How to Avoid It (With Applications to Dirac and Periodic Schrödinger Operators)_, arXiv:0812.2153.**

This work gives abstract results locating pollution for Galerkin bases and studies structural constraints that eliminate it in important self-adjoint quantum operators.

**Bound obligation:** no-pollution is a theorem with assumptions, not a generic property of self-adjoint approximation. The target RH family must satisfy its own exact analogue of those assumptions.

## S6 — cross-Millennium structural analogue on current main

`research/real_math/millennium/yang_mills/01_frontier/YM-S1_GAP_TRANSPORT_OBLIGATION_MATRIX_20260811.md`

The Yang–Mills spectral lane independently decomposes “finite-regulator gap -> continuum mass gap” into fixed-cutoff, uniformity, source completeness, physical scaling, and continuum spectral-identification obligations.

**Bound transfer:** only the finite-to-global obligation structure transfers. No Yang–Mills theorem, physical scaling law, or mass-gap statement is imported into RH.

## Exact route comparison

| Route | Finite/restricted object | What is already rigorous | Missing root-coupled limit |
|---|---|---|---|
| CCM 2025 | finite-prime / finite-dimensional Weil-form spectral triple | conditional finite-stage self-adjointness; determinant formula; real approximant zeros = approximant spectrum | prove cofinal/joint convergence and exact normalized determinant/zero-set limit `Xi` |
| CvS 2025 | convolution-form extremal eigenfunction | real-zero theorem under exact lower-bounded self-adjoint/simple/even hypotheses | show the RH arithmetic approximants satisfy hypotheses and converge to `Xi` |
| Suzuki 2026 | finite-interval nonlocal first-order self-adjoint realizations | finite-interval framework, unconditional source results | prove the `a -> infinity` limiting operator and exact zeta spectrum |
| generic Galerkin | projections of self-adjoint operator | many finite matrices are self-adjoint | pollution/escape possible without extra structure |

## Fail-closed source conclusions

1. `SELF_ADJOINT_AT_EACH_CUTOFF` is insufficient.
2. `FINITE_PREFIX_ZETA_ACCURACY` is insufficient.
3. `ZERO_COUNTING_OR_UV_ASYMPTOTICS` is insufficient.
4. `STRONG_RESOLVENT` or `MOSCO` language without a spectral-exactness theorem is insufficient.
5. `LOCAL_UNIFORM_DETERMINANT_CONVERGENCE_TO_XI`, if independently proved for real-rooted approximants with fixed source-side normalization and nonzero exact limit, is qualitatively strong enough to make Hurwitz zero stability relevant; the hard step is proving that convergence from the arithmetic construction.
6. A future candidate must bind the approximating family, comparison maps, normalization, topology, compactness/uniformity, multiplicity, all-prime/archimedean arithmetic limit, and the finite-stage simple/even hypotheses.

Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
