# RH-SPEC-001 same-context expert review — limit/globalization frontier

Date: 2026-08-11. Authority: `SAME_CONTEXT_REVIEW_ONLY / SOURCE_BOUND_ROUTE_DISCRIMINATION / NO_INDEPENDENT_REVIEW / NO_MATHEMATICAL_CANDIDATE / ROOT_AUTHORITY_NONE`.

This review follows the fresh primary-source audit recorded in `RH_SPEC_001_SOURCE_ADDENDUM_LIMIT_GLOBALIZATION_20260811.md`. The six roles share the same evidence packet and are deliberately **not** independent reviewers.

## Evidence jointly inspected

- Connes–Consani–Moscovici, `arXiv:2511.22755` (2025), especially Theorem 1.1 and the authors' explicit finite-parameter-to-global convergence programme.
- Connes–van Suijlekom, `arXiv:2511.23257` (2025), real-zero theorem for the Fourier transform of an extremal eigenfunction under lower-bounded self-adjoint convolution-form hypotheses.
- Suzuki, `arXiv:2606.09096` (2026), finite-interval self-adjoint realizations and the conjectural `a -> infinity` zeta-spectrum limit.
- Connes, `arXiv:2602.04022` (2026), finite-prime Weil-form approximants and finite-to-infinite convergence strategy.
- Connes–Moscovici, `arXiv:2112.05500` (2021), self-adjoint prolate operator with zeta-related ultraviolet behavior as a hostile calibration.
- Existing frozen `RH-SPEC-001` context, dual-memory review, trace, and de Branges/local-positivity source addendum.

## 1. Analytic-number-theory lead

**Background/role:** explicit formulas, entire functions, zeta zero multiplicities, and exact RH-equivalent criteria.

**Finding:** The new finite-prime operator route already constructs entire approximants whose zeros are real under explicit finite-parameter hypotheses. Therefore the arithmetic question is no longer merely “can one manufacture real spectra?” The target must be the exact `Xi` entire function or its complete zero multiset.

**Strongest objection:** Pointwise convergence of a few low zeros, convergence of counting functions, or arbitrarily high numerical accuracy on every fixed finite prefix does not imply that all zeros of `Xi` are captured. A proof must control zeros on arbitrary compact subsets and prevent zeros from escaping or entering from infinity.

**Delegated requirement:** Any future `RH-SPEC-002` candidate must state an exact target convergence theorem and show why it implies the all-zero RH statement, including multiplicity.

**Vote:** `ACCEPT_NEXT_ATOM / BLOCK_OPERATOR_INVENTION_NOW`.

## 2. Spectral/operator lead

**Background/role:** unbounded self-adjoint operators, quadratic forms, resolvent convergence, spectral stability.

**Finding:** Self-adjointness at each finite cutoff does not by itself determine the spectrum of an infinite-cutoff limit. Different convergence notions preserve different spectral information; strong resolvent convergence in particular can permit spectral instability that local-uniform determinant convergence may rule out in an entire-function representation.

**Strongest objection:** The approximating Hilbert spaces, quadratic forms, ground-state normalizations, and parameters may all vary. Writing `D_n -> D` without a common identification map and a chosen topology is not a theorem.

**Delegated requirement:** Build a topology comparison table: norm resolvent, strong resolvent, Mosco/form convergence, local-uniform regularized determinant convergence, and zero-counting/spectral-measure convergence. For each, state what it does and does not guarantee about isolated eigenvalues, multiplicity, pollution, and the target entire function.

**Vote:** `ACCEPT_LIMIT_STABILITY_ATOM`.

## 3. Trace-formula / Weil-quadratic-form lead

**Background/role:** Weil explicit formula, prime-place decomposition, trace identities and regularization.

**Finding:** The 2025 finite-prime constructions are valuable precisely because they retain arithmetic input from restricted Euler products/Weil forms. But a limit theorem must also prove that the arithmetic objects converge with the correct archimedean term, normalization, and all-prime contribution. Spectral convergence cannot be detached from arithmetic convergence.

**Strongest objection:** A determinant may converge after a normalization chosen post hoc; unless that normalization is fixed source-side and its arithmetic meaning is controlled, the route risks fitting `Xi`.

**Delegated requirement:** `RH-SPEC-002` must bind operator convergence to arithmetic-form/determinant convergence, with normalization and order of limits frozen before evaluated zero comparisons.

**Vote:** `ACCEPT_WITH_ARITHMETIC_BINDING`.

## 4. Adversarial functional-analysis lead

**Background/role:** pathological operator limits, spectral pollution, noncompactness, changing domains, and counterexample design.

**Finding:** The cheapest falsifiers are now limit pathologies, not exotic new operators. Known-answer models can be built where every approximant is self-adjoint with real spectrum yet eigenvalues escape, pollute gaps, lose multiplicity, or converge under a topology too weak to identify the target spectrum.

**Strongest objection:** The simple/even ground-state hypotheses in the 2025 theorem are finite-parameter assumptions; a global proof must establish them along the required cofinal family or replace them with a theorem that does not need them.

**Delegated requirement:** Before any positive convergence theorem, build a hostile atlas for:
- spectral pollution under weak/strong convergence;
- order-of-limits noncommutation;
- disappearing isolated eigenvalues;
- determinant normalizations with misleading finite-prefix convergence;
- failure of simple/even ground-state stability.

**Vote:** `ACCEPT_EFFECTUAL_FALSIFIER_FIRST`.

## 5. Formal-methods lead

**Background/role:** exact statement binding, machine-auditable obligation DAGs, theorem-dependency separation.

**Finding:** The bridge can be made substantially more machine-auditable than “prove the approximants converge.” The child atom should be decomposed into typed obligations: common identification maps, topology, compactness/uniform bound, normalization, spectral completeness, multiplicity, no-pollution, and arithmetic target equality.

**Strongest objection:** “Convergence of spectra” is ambiguous and can hide several inequivalent statements.

**Delegated requirement:** Freeze a new `MathContextFiber` for `RH-SPEC-002` and a typed proof-DAG before any convergence lemma is proposed. The current `RH-SPEC-001` source addenda do not retroactively alter its frozen context identity.

**Vote:** `ACCEPT_PRE_CANDIDATE_CHILD_ONLY`.

## 6. Novelty / research-value / learning-control lead

**Background/role:** prior-art boundary, rediscovery risk, information-gain routing, RAKL breakthrough-control discipline.

**Finding:** The 2025 and 2026 primary papers themselves already identify rigorous convergence as missing, so “the hard part is convergence” is not a novelty claim. The useful RAKL contribution in this cycle is narrower: the common obligation matrix shows that multiple modern operator families have independently moved the frontier past generic self-adjointness and into a shared spectral-limit/completeness bottleneck.

**Strongest objection:** Do not mislabel this route-pruning synthesis as new mathematics.

**Breakthrough-mode decision:** retain `REFLECTIVE_RESTRUCTURE`, `CONTRASTIVE_DISCRIMINATION`, and `EFFECTUAL_PROBE`. Add `FIXATION_RESET` only in the bounded sense of stopping the search for yet another finite self-adjoint operator until the limit/completeness bottleneck is tested. No method-basis exhaustion claim is justified.

**Vote:** `ACCEPT_ROUTE_NARROWING / NO_NOVELTY_CLAIM`.

## Joint decision

The expert cell unanimously selects `RH-SPEC-002 — SPECTRAL_LIMIT_GLOBALIZATION` as the **next pre-candidate child atom**, subject to a fresh strict context/memory/trace packet.

The first action in that child should not be a proof idea. It should be a **known-answer limit-stability calibration suite** that compares convergence topologies and exhibits counterexamples where self-adjoint approximants fail to transport complete spectra. Only after those calibrations and a fresh `plan_math_research` pass may a concrete convergence theorem candidate be generated.

The following candidate families remain blocked under the current `RH-SPEC-001` identity:
- a new `H=xp` boundary condition;
- a fitted kernel/determinant using known zeros;
- a claim based on GUE/counting/UV asymptotics;
- a direct assertion that the 2025 or 2026 finite/restricted operators converge globally;
- a canonical-system positivity assertion whose required positivity is RH-equivalent.

Root status: `OPEN_NO_SOLUTION_CERTIFICATE`.
