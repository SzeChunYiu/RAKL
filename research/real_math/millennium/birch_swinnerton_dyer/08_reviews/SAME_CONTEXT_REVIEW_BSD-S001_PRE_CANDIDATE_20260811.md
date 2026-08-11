# Same-context pre-candidate review — BSD-S001

**Date:** 2026-08-11  
**Authority:** `SAME_CONTEXT_PRE_CANDIDATE_REVIEW / NOT_INDEPENDENT / NO_THEOREM_AUTHORITY`

## Frozen atom

`BSD-S001`: identify the minimal extra comparison object or identity needed to convert arbitrary-rank p-primary Selmer/Iwasawa structure into both the complex analytic-rank equality and the full global refined BSD leading-term formula.

No mathematical candidate is proposed in this review.

## Role cell

### Arithmetic-geometry lead

**Background:** elliptic curves over number fields, Mordell–Weil groups, descent, Tate–Shafarevich groups, regulators, Tamagawa factors and exact BSD normalization.

**Finding:** the target must be split into at least two proof obligations: equality of algebraic and complex analytic rank, then reconstruction of the refined leading coefficient. The `p^∞`-Selmer group is an arithmetic interface, but its corank can contain a divisible Sha contribution unless that contribution is separately controlled, and one fixed prime does not by itself determine the global Sha order.

**Strongest objection:** a narrative of the form “the main conjecture determines the Selmer group, therefore BSD follows” can hide both the complex analytic-order bridge and the non-`p`/archimedean factors.

**Delegation:** write the exact sequence and premise/output table for every imported Selmer theorem, separating `rank E(Q)`, `corank Sel_{p∞}`, `Sha[p∞]`, and any finiteness hypothesis.

### Iwasawa/Selmer lead

**Background:** Kato and Heegner-point Euler systems, Kolyvagin systems, cyclotomic/anticyclotomic Iwasawa theory, control theorems, Selmer complexes and characteristic/Fitting ideals.

**Finding:** recent refined machinery can encode substantial arbitrary-rank p-primary Selmer structure, which is a materially richer input than a rank-zero/one theorem. But the inspected sources do not turn that structural information into an arbitrary-rank equality with the order of the *complex* L-function at `s=1`.

**Strongest objection:** changing reduction hypotheses, the auxiliary prime, or the chosen Iwasawa tower may expand theorem scope without touching the central analytic–arithmetic closure gap.

**Delegation:** build a theorem input/output matrix: prime/reduction/residual hypotheses, exact main-conjecture strength, arithmetic output, analytic output, rank regime, and which BSD factors remain unbound.

### Complex↔p-adic bridge lead

**Background:** complex and p-adic L-functions, explicit reciprocity laws, p-adic heights, exceptional-zero formulas, regulators and special-value/derivative identities.

**Finding:** rank one works because a derivative can be tied to a concrete arithmetic point/height and then to Selmer control. In higher rank, determinant lines, exterior powers, derived heights or higher explicit reciprocity are natural structural coordinates, but naming such an object is not a comparison theorem.

**Strongest objection:** a p-adic leading term and a complex leading Taylor coefficient are different objects. An interpolation formula at finite-order characters does not automatically identify arbitrary-order vanishing or the required complex regulator.

**Delegation:** search for source-bound higher-rank reciprocity/comparison identities that simultaneously track derivative order, determinant/regulator, local factors and the complex L-value normalization. Reject any proposal that merely replaces a scalar by a determinant without a proved complex comparison.

### Adversarial local-global reviewer

**Background:** local-global principles, Selmer condition pathologies, exceptional primes, counterexample construction and information-sufficiency audits.

**Finding:** the cheapest high-value falsifier is to formalize exactly what information a fixed-p theorem output retains. The full refined BSD target contains coordinates that are not visibly present in a single p-primary summary: other primary parts of Sha and archimedean data are immediate warnings.

**Strongest objection:** those coordinates are not freely variable; deep arithmetic theorems may couple them. Therefore “one p cannot know the answer” is not a proof of insufficiency.

**Delegation:** construct a target-specific projection-sufficiency test. Either prove a reconstruction theorem on the registered elliptic-curve class or isolate a rigorously admissible missing coordinate. Do not promote generic information-theory intuition.

### Formal-methods / assurance lead

**Background:** formal statement alignment, proof DAGs, dependency audits, theorem-prover trust boundaries and evidence authority.

**Finding:** the first formal object should be a typed dependency map, not the full BSD theorem. Each edge must identify whether it is an exact sequence, a proved Iwasawa implication, an explicit reciprocity law, a finiteness input, a p-adic/complex comparison, or an open conjectural bridge.

**Strongest objection:** bundled edges such as “IMC ⇒ BSD” or “Selmer rank = analytic rank” can silently import the target or a neighboring open conjecture.

**Delegation:** make every p-adic BSD, Sha-finiteness, main-conjecture and exceptional-zero premise explicit. The present packet has no proof receipt and no root authority.

### Novelty / research-value lead

**Background:** primary-source theorem search, equivalence checking, higher-rank BSD literature, derived heights and Euler-system frontiers.

**Finding:** “use higher-rank Euler systems” is not yet a research contribution; the live question is which exact output coordinate is missing after the strongest available Selmer theorem. The inspected primary sources motivate determinant/derived structures but do not establish that the sought bridge is absent from all literature.

**Strongest objection:** an apparently new comparison statement may be a restatement of a known equivariant Tamagawa-number, p-adic BSD, derived-height, augmentation-ideal or determinant-line conjecture.

**Delegation:** once the projection audit names the missing coordinate, run a notation-normalized search over higher-rank explicit reciprocity, derived heights, determinant functors, equivariant Tamagawa-number formulations, and p-adic/complex leading-term comparisons before candidate invention.

## Learning-control / breakthrough-mode review

The cell recommends the proposal-only modes `REFLECTIVE_RESTRUCTURE`, `CONTRASTIVE_DISCRIMINATION`, and `EFFECTUAL_PROBE`.

- **Reflective restructure:** replace the coarse question “can Iwasawa theory prove BSD?” by an explicit observation/reconstruction map from the full BSD package to the exact theorem output.
- **Contrastive discrimination:** compare rank zero, rank one, and arbitrary-rank outputs to identify precisely which coordinate first stops being controlled.
- **Effectual probe:** the projection-sufficiency audit can change the information state without pretending to solve the root theorem.

These modes create no mathematical authority.

## Cell synthesis

The six roles agree on **no candidate yet**. The highest-partition next action is `BSD-S001a`: materialize the projection map separating at least

`rank E(Q)`, `corank Sel_{p∞}`, `Sha[p∞]`, other `q`-primary Sha factors, Tamagawa/torsion, regulator/real period, p-adic leading data, and complex Taylor data.

Then force one of two branches:

1. **projection not sufficient under the exact registered hypotheses** — open the missing coordinate as a child atom and search specifically for the theorem that could restore it;
2. **a source-bound reconstruction theorem exists** — bind its exact hypotheses and audit whether they themselves contain an unclosed BSD-equivalent dependency.

Only after the strict context, memory, and trace packet passes should a new mathematical bridge or route-pruning candidate be generated.

## Unresolved warnings

- The current literature scan is bounded and is not a novelty certificate.
- The fixed-p/global distinction is a structural warning, not yet a BSD-local impossibility theorem.
- Rank-one success does not establish that a determinant-level higher-rank analogue exists.
- Finite computations on high-rank curves can calibrate or falsify a proposal but cannot prove the general conjecture.
- Same-context expert roles are not independent mathematical review.
