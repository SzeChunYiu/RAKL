# H4d1 same-context expert cell

Authority: `SAME_CONTEXT_REVIEW_ONLY / NOT_INDEPENDENT_REVIEW`.

## 1. Hodge-theory lead

**Background:** variations of Hodge structure, period maps, Hodge loci, Lefschetz-type theorems.

**Finding:** Cattani–Deligne–Kaplan solves algebraicity of the locus where the flat class remains Hodge, not realization of that class by cycles. Treating an algebraic Hodge locus as evidence for algebraic-cycle existence would collapse two distinct objects.

**Strongest objection:** the atom begins with an algebraic witness at `s0`; therefore even a perfect propagation theorem would not prove the root conjecture for an arbitrary Hodge class.

**Recommendation:** keep H4d1 explicitly subordinate to H1; use it to learn the propagation obstruction, not as a root shortcut.

## 2. Algebraic-cycle/deformation lead

**Background:** Hilbert/Chow spaces, cycle classes, normal functions, semiregularity.

**Finding:** the right object is not simply “the Hilbert scheme with class alpha.” Rational Hodge classes may be represented by signed rational combinations. Any exact witness space needs a coefficient-clearing convention and positive/negative effective-cycle bookkeeping, or a Chow/K-theoretic formulation with an explicit realization map.

**Strongest objection:** choosing a convenient effective parameter space can silently strengthen the target.

**Recommendation:** the next discriminator must first define the witness category and class map exactly, then compare its tangent/obstruction theory with the Hodge-locus tangent equations.

## 3. Deformation/obstruction-theory lead

**Background:** cotangent complexes, obstruction maps, formal deformation, algebraization.

**Finding:** semiregularity provides a genuine template: Hodge persistence can kill the image of an obstruction, and injectivity/effectivity of a semiregularity map can turn that into geometric deformation. The load-bearing coordinate is therefore not Hodge-locus algebraicity but the kernel of the obstruction-detection map.

**Strongest objection:** first-order tangent surjectivity can still fail at higher order; formal compatible lifts can still fail to algebraize/globalize.

**Recommendation:** calibrate any future criterion on a three-step ladder: tangent lift -> all-order formal lift -> algebraized/global lift.

## 4. Adversarial falsification lead

**Background:** counterexamples, boundary cases, degeneration/monodromy pathologies.

**Finding:** five cheap falsifiers must precede a lifting theorem: divisor case, semiregular case, non-semiregular witness, rational signed-combination encoding, and monodromy/globalization stress.

**Strongest objection:** a “criterion” that merely restates “there exists a relative algebraic cycle” is vacuous; a criterion that assumes a standard/Hodge/Tate conjecture is circular for the root program.

**Recommendation:** first candidate round should be a criterion *schema* with explicit independent inputs and these five regressions.

## 5. Formal-methods/assurance lead

**Background:** statement binding, typed proof obligations, verifier boundaries.

**Finding:** the atom needs typed maps: base `T`, witness space `W_alpha`, projection `pi: W_alpha -> T`, tangent map, obstruction map, coefficient-clearing convention, and formal-to-algebraic comparison. Without these, “dominates T” is too narrative for later proof checking.

**Strongest objection:** the phrase “cycle realization space” is currently a placeholder family of possible constructions, not a formal object.

**Recommendation:** next action should define a minimal typed interface before any candidate sufficiency criterion is proposed.

## 6. Novelty/research-value lead

**Background:** Hodge-conjecture literature, variational Hodge conjecture, prior-art triage.

**Finding:** H4d1 is a classical variational-Hodge obstruction, not a novelty claim. The new value of this RAKL cycle is the strict separation of base-locus algebraicity, witness deformation, formal lifting, algebraization, and globalization, plus the explicit falsifier ladder.

**Strongest objection:** presenting the decomposition itself as a new theorem would be overclaiming.

**Recommendation:** preserve `NO_NOVELTY_CLAIM`; use the decomposition to select a precise next proof obligation.

## Cell synthesis

Consensus next action: **do not propose a Hodge theorem yet**. Define and calibrate a typed witness-projection interface that can express the divisor/Picard and semiregular solved cases while exposing exactly where higher-codimension/general cycles fail.

Main disagreement: whether the next concrete representation should be Chow-theoretic, Hilbert-pair based after coefficient clearing, or K-theoretic/formal. This remains open and is itself part of the next discriminator.
