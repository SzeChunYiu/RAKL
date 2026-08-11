# RH-ANA-001 same-context expert review — pre-candidate

Authority: `SAME_CONTEXT_REVIEW_ONLY / NOT_INDEPENDENT`

This cell reviewed the same frozen context and source packet. It is deliberately role-separated but does not satisfy any independent-review requirement.

## 1. Analytic number theory lead

**Background:** zeta/L-functions, explicit formulas, zero-density and mollifier methods.

**Delegated questions:** freeze the exact root/criterion semantics; identify which analytic steps are genuinely partial progress rather than equivalent restatements; audit zero-sum and Mellin conventions.

**Finding:** Weil's explicit-formula sign criterion is the best first common coordinate because it keeps both prime-side and zero-side structure visible. Li and Nyman–Beurling are useful contrastive coordinates, while mollifier results are genuine partial successes. The dominant danger is proving a formula whose sign assumption is simply RH in disguise.

**Strongest objection:** a “manifestly negative” decomposition may silently encode off-critical-zero exclusion in a transform, boundary condition, or positivity premise.

**Vote:** `ACCEPT_PRE_CANDIDATE_CONTEXT`; no proof candidate yet.

## 2. Functional analysis / approximation lead

**Background:** Hilbert-space closure, quadratic forms, dense subspaces, Mellin/Fourier transforms.

**Delegated questions:** test whether a smaller test class could legitimately replace Weil's full class; compare the Nyman–Beurling closure obstruction with Weil sign control.

**Finding:** restricting to a convenient finite-parameter or compactly supported subclass is only useful if a separate continuity/density theorem preserves the full sign criterion. Nyman–Beurling similarly warns that good finite approximants are not closure membership without uniform limiting control.

**Strongest objection:** finite-dimensional numerics or a signed identity on a hand-picked test family can look decisive while losing the universal quantifier that carries RH.

**Vote:** `REVISE_ANY_RESTRICTED_TEST_CLASS_UNTIL_DENSITY_PROVED`.

## 3. Criteria / representation lead

**Background:** Li coefficients, Nyman–Beurling–Báez-Duarte criteria, prime-zero equivalent formulations.

**Delegated questions:** determine whether switching representation lowers the proof burden; isolate common residuals across criteria.

**Finding:** the common unresolved coordinate is infinite uniformity: all admissible Weil autocorrelations, all Li coefficients, or convergence through the full Nyman closure. Representation change alone is not progress. A useful move must expose a sub-obligation strictly cheaper than the original universal statement.

**Strongest objection:** an exact equivalent criterion can produce a large amount of technically correct work with zero epistemic contraction.

**Vote:** `ACCEPT_CONTRASTIVE_USE / REJECT_REFORMULATION_AS_PROGRESS`.

## 4. Adversarial falsification lead

**Background:** counterexample design, known-answer worlds, asymptotic and finite-to-infinite failure modes.

**Delegated questions:** design the cheapest falsifier before any inequality is proposed.

**Finding:** the next useful artifact should be a criterion-localization benchmark with synthetic symmetric off-critical zero configurations and finite-prefix/test-subclass regressions. It should verify that any claimed mechanism detects a planted off-line contribution and does not infer universality from finite success.

**Strongest objection:** a synthetic-zero world is only a validator of the reasoning mechanism; it is not evidence that actual zeta zeros behave that way.

**Vote:** `ACCEPT_EFFECTUAL_PROBE`.

## 5. Formal methods / verifier-trust lead

**Background:** formal statement alignment, exact domains, convergence and dependency audits.

**Delegated questions:** list proof-critical definitions that must be frozen before candidate generation.

**Finding:** any later Weil-side candidate must bind the exact class `W`, Mellin-transform convention, multiplicative autocorrelation including complex conjugation convention, two moment constraints, sign orientation, prime-power sum, archimedean integral, and zero-sum limiting order. Any Li/Nyman candidate needs equally exact sequence/space conventions.

**Strongest objection:** a correct inequality for a neighboring normalization or smaller domain can be mistaken for RH-equivalent progress.

**Vote:** `BLOCK_THEOREM_PROMOTION_UNTIL_EXACT_FORMALIZATION`.

## 6. Novelty / research-value / breakthrough-policy lead

**Background:** structural prior-art comparison, research strategy, metacognitive mode selection.

**Delegated questions:** distinguish known criteria from new research; choose search mode without granting authority to heuristics.

**Finding:** Weil, Li, Nyman–Beurling, and mollifier programs are established prior art. The current value is the strict comparison and localization benchmark, not novelty. Recommended proposal modes are `REFLECTIVE_RESTRUCTURE`, `CONTRASTIVE_DISCRIMINATION`, and an `EFFECTUAL_PROBE`; unconstrained recombination is premature. The signal-processing signed-energy analogy survives only as a proposal compressor with an explicit residual-sign validation obligation.

**Strongest objection:** a cosmetically new decomposition may be an algebraic rewrite of Weil/Li and should be fingerprinted against known criteria before being called new.

**Vote:** `ACCEPT_PRE_CANDIDATE_STRATEGY / NOVELTY_NONE`.

## Cell synthesis

The cell agrees on one next action and preserves the remaining disagreement about eventual route choice.

**Selected next action:** machine-audit the context, memory and trace packet; only if all gates pass, build a representation-neutral known-answer/falsifier harness that exposes finite-to-infinite leaps, restricted-test-class loss, circular sign assumptions, and planted off-critical contributions. Use that benchmark to define the first genuinely localized residual before proposing any new inequality or proof mechanism.

**Alternatives deferred:** direct Weil inequality invention; Li recurrence invention; Nyman finite-approximant optimization; immediate mollifier extension.

**Why:** the selected probe has higher partition power and lower verification debt. It can eliminate whole families of false-progress arguments without pretending to move the root theorem.

Root authority remains `OPEN_NO_SOLUTION_CERTIFICATE`.
