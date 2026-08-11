# Same-context review — RH-ANA-001 Li-prefix calibration

**Review type:** role-separated same-context research review. These passes are not independent peer review and create no root authority.

**Subject:** `CAL-RH-LI-PREFIX-001`, the exact synthetic quartet calibration with `rho=1/4+100 i`.

## 1. Analytic-number-theory lead

**Background / role.** Classical zeta/L-function theory; owns the exact RH statement, Li criterion scope, and distinction between an equivalent infinite criterion and a finite computational prefix.

**Evidence inspected.** Li 1997; Bombieri–Lagarias 1999; the exact calibration receipt and negative-history note.

**Finding.** Li positivity is an all-index requirement. The observed `1..626` positive / `627` negative pattern is therefore a legitimate counterexample to the *finite-prefix sufficiency inference* in the synthetic-multiset calibration world, not a counterexample to Li's criterion.

**Strongest objection.** The quartet is not the actual zeta zero multiset and does not encode the prime-side arithmetic constraints of zeta.

**Falsifier attempted.** Check whether the claimed conclusion can be weakened to a statement solely about finite-prefix logic. It can: the result requires only the exact quartet transform and signs.

**Residual uncertainty.** Which zeta-specific identity, recurrence, tail estimate, or prime-side inequality could control all indices without smuggling in RH-equivalent zero information?

**Vote:** `ACCEPT_SCOPED_CALIBRATION`.

## 2. Explicit-formula / criteria lead

**Background / role.** Weil explicit formula, Li/Bombieri–Lagarias criteria, prime–zero duality; owns representation equivalences and admissible transfer boundaries.

**Evidence inspected.** The pre-candidate method-transfer matrix, Li/Bombieri–Lagarias source scope, quartet formula `Lambda_n(Q)=4-2 Re(z^n+z^{-n})`.

**Finding.** The calibration usefully separates an exact criterion from a finite projection of that criterion. It provides no prime-side positivity mechanism and therefore cannot be promoted into a zeta theorem.

**Strongest objection.** A real proof might combine finitely many computed coefficients with an independent zeta-specific tail theorem, in which case this falsifier would not apply to the full argument.

**Falsifier attempted.** Restrict the negative conclusion to methods lacking a separately proved uniform tail/all-index bridge. Under that scope the quartet remains decisive.

**Residual uncertainty.** Whether the cheapest next representation is Li coefficients themselves or a Weil/prime-side quadratic form from which all-index control can be derived.

**Vote:** `ACCEPT_WITH_SCOPE_GUARD`.

## 3. Functional-analysis / uniformity lead

**Background / role.** Hilbert/Banach-space approximation, closure and compactness; owns finite-to-infinite inference and uniformity obligations.

**Evidence inspected.** Exact sign sequence through 627 and the Nyman–Beurling/Li contrast in the frozen context fiber.

**Finding.** The failure is structurally a projection/closure gap: positivity on a finite coordinate projection does not control an infinite cone without an additional compactness, monotonicity, coercivity, recurrence, or tail argument. The calibration is a concrete witness of delayed detectability.

**Strongest objection.** One synthetic delayed failure does not quantify how large a prefix might be needed under stronger zeta-specific constraints.

**Falsifier attempted.** Treat the result only as a logical no-go for prefix-only certification, not as a quantitative lower bound for zeta verification.

**Residual uncertainty.** Whether there is any non-circular zeta-specific coercive structure strong enough to propagate a finite base region to all `n`.

**Vote:** `ACCEPT_SCOPED_CALIBRATION`.

## 4. Adversarial falsification lead

**Background / role.** Counterexample construction and hostile theorem auditing; owns cheapest failure cases, symmetry checks and overclaim detection.

**Evidence inspected.** The exact rational checker, the quartet closure under conjugation and `rho -> 1-rho`, and the sign transition at 627.

**Finding.** Choosing an off-critical zero with large imaginary part is an effective delayed-detection stress case. The checker must retain exact arithmetic because the signs near the transition are small.

**Strongest objection.** A coding or algebraic error in reciprocal pairing could manufacture the delayed sign change.

**Falsifier attempted.** Independently audit the transform identities: for `z=1-1/rho`, the four quartet transforms are `z`, `conj(z)`, `1/z`, `1/conj(z)`. The implemented recurrence follows this identity exactly.

**Residual uncertainty.** The benchmark family should later be broadened over `beta,gamma` to distinguish accidental one-parameter behavior from the general finite-prefix blind spot.

**Vote:** `ACCEPT_AND_RETAIN_AS_REGRESSION`.

## 5. Formal / computational methods lead

**Background / role.** Exact arithmetic, reproducibility, trace integrity and machine-checkable obligations.

**Evidence inspected.** `li_prefix_quartet_calibration.py`, calibration JSON, exact-fraction hashes, strict pre-candidate trace and current RAKL gate implementation.

**Finding.** Sign authority is exact: `fractions.Fraction` is used throughout the recurrence and floating point appears only in human-readable approximations. The regression should recompute the fractions and hashes, validate the new tool/failure records, and audit the appended research trace.

**Strongest objection.** Committed approximate decimals must never be treated as the proof of sign.

**Falsifier attempted.** Require tests to assert the exact rational inequalities first and only then compare receipt hashes.

**Residual uncertainty.** This is a finite exact computation, so it validates only the calibration statement, not RH.

**Vote:** `ACCEPT_PENDING_EXACT_HEAD_REGRESSION`.

## 6. Novelty / research-policy lead

**Background / role.** Prior-art boundaries, research-value assessment, fixation control and cross-problem memory governance.

**Evidence inspected.** Source packet, Li/Bombieri–Lagarias criteria, current RH and P-vs-NP memories, and the selected pre-candidate decision rationale.

**Finding.** The mathematical phenomenon is expected from the all-index nature of Li's criterion and is retained with `NO_NOVELTY_CLAIM`. Its value is operational: RAKL has earned its first RH-specific failure experience and a reusable exact falsifier, and the next search atom can be sharpened from “prove Li positivity” to “find a zeta-specific all-index propagation/tail mechanism.”

**Strongest objection.** Rephrasing a known logical limitation as a new theorem would inflate research authority.

**Falsifier attempted.** Remove all novelty language and ask whether the result still changes the search policy. It does: prefix-extension work without a uniform bridge is now explicitly low-information.

**Residual uncertainty.** A fresh RH-ANA-002 context must query the new tool/failure before any inequality candidate, and any cross-Millennium analogy requires a DifferenceWitness.

**Vote:** `ACCEPT_AS_SEARCH-CONTROL_MILESTONE`.

## Cell synthesis

The six lenses agree on a narrow but useful result: the exact quartet is a **known-answer falsifier for finite-prefix Li certification**, not evidence against RH and not a proof candidate. The strongest surviving objection—absence of zeta-specific arithmetic structure—is incorporated directly into the child atom rather than hand-waved away.

**Next atom:** `RH-ANA-002` — identify and falsify the weakest zeta-specific mechanism capable of proving or propagating Li positivity uniformly for all coefficient indices, preferably through an explicit-formula / prime-side representation with a rigorous tail bound and no RH-equivalent hidden assumption.

**Overall vote:** `ACCEPT_SCOPED_CALIBRATION / ROOT_REMAINS_OPEN / SAME_CONTEXT_REVIEW_ONLY`.
