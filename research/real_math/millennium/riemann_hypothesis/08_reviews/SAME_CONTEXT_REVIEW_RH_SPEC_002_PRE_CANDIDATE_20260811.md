# RH-SPEC-002 same-context expert review — convergence package selection

Date: 2026-08-11. Authority: `SAME_CONTEXT_REVIEW_ONLY / PRE_CANDIDATE / NO_INDEPENDENT_REVIEW / NO_MATHEMATICAL_CANDIDATE / ROOT_AUTHORITY_NONE`.

The six roles share the frozen `RH-SPEC-002` context, source packet, current RAKL success/failure memory review, and the parent operator-bridge matrix.

## 1. Analytic-number-theory / entire-function lead

**Background:** Guinand–Weil explicit formula, entire functions, zero multiplicity and RH-equivalent sign criteria.

**Delegated question:** What is the weakest target-side analytic convergence statement that would genuinely force all `Xi` zeros to be real?

**Finding:** Local-uniform convergence on `C` of a source-normalized family of entire approximants whose zeros are all real is a sharply stated route. On any domain disjoint from the real axis the approximants are zero-free; Hurwitz-type zero stability then prevents a nonzero locally uniform limit from acquiring a nonreal zero. This only helps if the limit is independently proved to be the exact nonzero `Xi`.

**Strongest objection:** Proving convergence of each fixed indexed zero is not the same as local-uniform convergence of the entire functions and does not by itself establish complete zero transport or multiplicity.

**Vote:** `PREFER_ENTIRE_FUNCTION_TARGET / REQUIRE_ARITHMETIC_LIMIT_PROOF`.

## 2. Spectral/operator-theory lead

**Background:** self-adjoint extensions, unbounded-operator domains, resolvents, compact spectral approximation.

**Delegated question:** Can operator convergence replace determinant convergence?

**Finding:** Not without additional structure. A named common-space/varying-space topology, domain identification and a no-pollution/compactness theorem are required. Norm-resolvent convergence is much stronger than strong-resolvent convergence; form/Mosco convergence is valuable for operator existence but cannot be silently promoted to complete spectral exactness.

**Strongest objection:** The current RH approximants vary in cutoff/subspace and potentially in Hilbert-space structure. An undefined `D_n -> D` statement is not actionable.

**Vote:** `KEEP_OPERATOR_TOPOLOGY_AS_SECOND_ROUTE / NO_GENERIC_CONVERGENCE_CLAIM`.

## 3. Weil-form / trace-determinant lead

**Background:** explicit formula, quadratic forms, regularized determinants, prime/archimedean decomposition.

**Delegated question:** What must travel with the spectral limit?

**Finding:** The all-prime/archimedean arithmetic identity and determinant normalization. Spectral convergence to some self-adjoint limit is irrelevant unless the limit is bound to `Xi` or the exact Weil explicit formula.

**Strongest objection:** A normalization chosen after inspecting known zeta zeros can manufacture convergence and is circular.

**Vote:** `BIND_NORMALIZATION_AND_ARITHMETIC_BEFORE_ZERO_TESTS`.

## 4. Adversarial functional-analysis lead

**Background:** spectral pollution, projection methods, weak-limit pathologies, order-of-limits counterexamples.

**Delegated question:** What is the cheapest discriminator before any positive convergence lemma?

**Finding:** Build a hostile atlas. At minimum include:
- finite self-adjoint projections with a spurious eigenvalue in a spectral gap;
- an eigenvalue that escapes to infinity while finite prefixes look stable;
- multiplicity splitting/merging under an insufficient topology;
- two-parameter limits whose iterated limits disagree;
- an entire-function sequence that matches an arbitrarily long finite zero prefix but fails locally uniformly to the target.

**Strongest objection:** Pollution examples from unrelated operators cannot directly refute the actual RH family; they only falsify insufficient **generic convergence packages**.

**Vote:** `EFFECTUAL_PROBE_FIRST`.

## 5. Formal-methods / assurance lead

**Background:** typed proof obligations, exact identity binding, machine-audited pre-candidate chronology.

**Delegated question:** What must be frozen before candidate generation?

**Finding:** The child context and dual-memory review are now explicit. The next-step trace should select the hostile topology-calibration suite, not a theorem. A later convergence candidate must have a typed identity containing: approximant family, parameter net/order, comparison maps, normalization, convergence topology, compactness/uniformity hypotheses, spectral target, multiplicity clause, no-pollution clause, and arithmetic target identity.

**Strongest objection:** “regularized determinants converge” without norm/normalization/domain data is under-specified.

**Vote:** `PASS_PRE_CANDIDATE_ONLY / BLOCK_UNTYPED_CANDIDATE`.

## 6. Novelty / research-value / breakthrough-control lead

**Background:** frontier mapping, rediscovery control, structural analogy, exploration/exploitation policy.

**Delegated question:** Which mode gives the most information now?

**Finding:** `CONTRASTIVE_DISCRIMINATION` plus `EFFECTUAL_PROBE`: compare convergence topologies on known-answer good/bad examples. A bounded `FIXATION_RESET` is justified against further finite-operator invention because two independent recent RH programmes already expose the same global-limit residual.

**Strongest objection:** The observation that convergence is missing is already explicit in primary literature and is not new mathematics.

**Vote:** `ACCEPT_CALIBRATION_PROGRAM / NO_NOVELTY_CLAIM`.

## Joint decision

Before any `RH-SPEC-002` mathematical candidate, run a **limit-stability calibration suite** partitioning at least four convergence packages:

1. local-uniform convergence of normalized entire determinants;
2. norm-resolvent convergence with compact/spectral-exactness control;
3. strong-resolvent or Mosco/form convergence without extra compactness;
4. compact-by-compact zero-multiset / spectral-measure convergence.

Each package must be tested against explicit pollution, escape, multiplicity and two-parameter-order counterexamples. The expected discriminator is whether the package is:

- `TOO_WEAK` — admits a known-answer false spectral transport;
- `SUFFICIENT_BUT_UNPROVABLE_FROM_CURRENT_RH_DATA`;
- `PLAUSIBLY_MATCHED_TO_RH_APPROXIMANTS`;
- or `CIRCULAR/RH_EQUIVALENT_IF_ASSUMED`.

Only a package surviving the hostile suite and matched to the actual arithmetic approximants may become a later theorem candidate.

Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
