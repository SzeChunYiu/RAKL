# RH-SPEC-001 source addendum — finite-to-global spectral limit frontier

Accessed 2026-08-11. Authority: `SOURCE_CONTEXT_ONLY / PRE_CANDIDATE_ROUTE_DISCRIMINATION / NO_THEOREM_OR_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`.

This addendum records a material frontier update discovered after the original `RH-SPEC-001` `MathContextFiber` was frozen. It does **not** revise that frozen context identity and cannot authorize a mathematical candidate. Its purpose is to sharpen the candidate-independent operator-bridge obligation matrix and determine which fresh child context should be opened next.

## 1. Connes–Consani–Moscovici 2025: self-adjoint finite-prime spectral approximants

**Alain Connes, Caterina Consani, Henri Moscovici, _Zeta Spectral Triples_, arXiv:2511.22755 (2025).**

For fixed parameters `lambda,N`, the paper constructs rank-one perturbations `D_log^(lambda,N)` of a scaling spectral triple from a restriction of the Weil quadratic form. Under the explicitly stated hypotheses that the smallest eigenvalue of the truncated Weil form is simple and its ground state is even, Theorem 1.1 proves:

- self-adjointness of the exact rank-one-perturbed operator on its stated direct-sum Hilbert space;
- a regularized determinant proportional to the Fourier transform of the ground state;
- reality of every zero of that approximant entire function and equality of those zeros with the spectrum of the approximant operator.

This matters because `SELF_ADJOINTNESS` is no longer the only or even the most informative generic obstruction for this route family. The source itself states that the numerical spectra appear to converge toward zeta zeros as `N,lambda -> infinity`, and that **a rigorous proof of that convergence would establish RH**. It also identifies convergence of suitably normalized regularized determinants toward the Riemann `Xi` function as a natural analytic route to that goal.

### Exact remaining bridge exposed

The source therefore separates two levels that must not be conflated:

1. **finite/restricted real-zero operator theorem** — rigorous under the stated finite-parameter hypotheses;
2. **global Xi/zeta spectral identification** — requires a rigorous limit theorem.

A strict RAKL route must track the simple/even ground-state hypotheses across the approximating family, specify the joint `N,lambda` limiting regime and normalization, and prove a topology strong enough to rule out missing zeros, spurious spectral points, multiplicity loss, and order-of-limits artifacts.

## 2. Connes–van Suijlekom 2025: the real-zero mechanism is a theorem, not the arithmetic bridge

**Alain Connes and Walter D. van Suijlekom, _Quadratic Forms, Real Zeros and Echoes of the Spectral Action_, arXiv:2511.23257 (2025).**

The paper proves a general real-zero theorem for a lower-bounded self-adjoint convolution-type quadratic form on a finite interval when its lowest spectral value is simple and isolated with an even eigenfunction. The Fourier transform of that eigenfunction then has only real zeros.

### Exact transfer lesson

This is a serious solved **local mechanism**: once the exact operator hypotheses hold, real zeros follow structurally. It does not itself prove that the resulting entire functions converge to `Xi`, nor that the limiting zero multiset is the zeta zero multiset.

Consequently, inventing another finite self-adjoint operator has lower information value than attacking the arithmetic/global convergence bridge for already available operator families.

## 3. Suzuki 2026: an independent operator route reaches the same limit bottleneck

**Masatoshi Suzuki, _Weil's quadratic form via the screw function_, arXiv:2606.09096 (2026).**

Suzuki develops a continuous-function framework for the Weil quadratic form and formulates a conjecture that a self-adjoint operator whose eigenvalues are the imaginary parts of the nontrivial zeta zeros is obtained, as `a -> infinity`, from self-adjoint operators arising from nonlocal realizations of a first-order differential operator on finite intervals `[-a,a]`. The paper states that its proved results are unconditional; the target spectral-limit statement is conjectural.

### Cross-route convergence diagnosis

The Connes–Consani–Moscovici and Suzuki constructions are technically different, yet both expose the same abstract missing coordinate:

`rigorous finite/restricted self-adjoint realizations -> controlled global limit -> exact complete zeta spectrum`.

This repeated residual is evidence for a **research-control convergence**, not for RH. It justifies opening a fresh child atom around limit stability/completeness rather than generating another unrelated operator.

## 4. Connes 2026 survey/original finite-prime approximation

**Alain Connes, _The Riemann Hypothesis: Past, Present and a Letter Through Time_, arXiv:2602.04022 (2026).**

Within a survey, Connes presents an original finite-prime extremization of a restriction of Weil's quadratic form. The resulting approximating values lie on the critical line and numerically approximate many low zeta zeros with very high accuracy. The paper explicitly frames finite-to-infinite convergence as a potential proof strategy rather than a completed proof.

This provides another calibration for the same warning: **real, extremely accurate finite approximants are not root evidence without the global convergence theorem.**

## 5. Hostile calibration: self-adjoint + zeta asymptotics is still insufficient

**Alain Connes and Henri Moscovici, _Prolate spheroidal operator and Zeta_, arXiv:2112.05500 (2021).**

The paper gives a legitimate self-adjoint prolate-related operator whose ultraviolet spectral behavior reproduces that of squared zeta-zero ordinates. This remains a useful negative control: exact self-adjointness plus striking zeta asymptotics does not supply exact prime-power/archimedean matching or complete Hilbert–Polya spectral equality.

## 6. Refined bridge obligations

The source audit requires separating the prior `GLOBALIZATION_OR_PARAMETER_CONTINUATION` row into at least two non-compensatory questions:

1. **globalization / parameter continuation** — can the restricted finite-place/finite-interval/finite-prime construction be defined with uniform hypotheses throughout the target regime?
2. **limit topology / spectral-pollution control** — does the chosen convergence notion actually transport the complete target zero/spectral multiset with multiplicity and no spurious or escaped points?

Potential target topologies are not interchangeable. Local-uniform convergence of normalized entire determinants, norm/strong resolvent convergence of self-adjoint operators, graph or Mosco convergence of forms, and convergence of spectral measures each preserve different information. A future candidate must name the topology and prove the exact theorem that makes it sufficient.

## 7. Proposed next child atom — no candidate yet

The source audit selects the following **pre-candidate child question**:

`RH-SPEC-002 — SPECTRAL_LIMIT_GLOBALIZATION`

> Identify the weakest independently checkable convergence package for finite/restricted self-adjoint RH approximants that suffices to transport real approximant zeros/spectra to the complete `Xi` zero multiset with multiplicity, while excluding spectral pollution, escaped/missing zeros, order-of-limits ambiguity, and RH-equivalent assumptions.

Before any theorem candidate is proposed for `RH-SPEC-002`, it requires its own freshly frozen `MathContextFiber`, solved/near-solved operator-limit analogues, method-transfer matrix, cross-domain analogy scan, same-context expert review, dual success/failure memory review, and hash-chained pre-candidate trace.

Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
