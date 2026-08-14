# Paper V–VI RSHEA literature/mechanism saturation — round 009

Status: **BOUNDED_OPERATOR_FAMILY_FLAT; IMPLEMENTATION/EVIDENCE BASIS NOT CLOSED**.

This is the required post-round-008 adversarial neighborhood repeat. Search vocabulary changed again to automated program repair, abductive explanation, abstract interpretation and diagnosis/hitting-set duality. No evaluated mechanic outcome is accessed and no authority is granted.

Parent repeat head: `rshea/p5-p6-saturation-round-008@4448110c4f30b7441e99dfe808dbd101b749051d`.

## Adversarial alternate families and mappings

### Automated program repair

GenProg/search-based repair and Angelix/symbolic patch synthesis generate repairs after localizing a failing program region and validating candidate patches. Modern counterexample-guided program-repair work explicitly combines MaxSAT-style localization with a CEGIS loop.

**Mapping:** no new operator family. The workflow decomposes into already-retained operators/surfaces:

1. failure/fault localization or conflict/correction analysis;
2. candidate repair/mechanism synthesis;
3. verifier/counterexample refinement;
4. original-target validation and regression/fresh checks.

Genetic/search-based repair, symbolic repair and CEGIS repair become strongest parent implementations for repair-synthesis subproblems rather than a new canonical operator class.

### Abductive explanation / diagnostic reasoning

Abductive diagnosis computes parsimonious explanations for observations; minimal diagnoses can be derived using conflict sets and hitting sets under explicit background theories.

**Mapping:** no new operator family beyond the already frozen model-based diagnosis + minimal conflict/correction analysis + active acquisition/diagnosability surfaces. Abductive versus consistency-based diagnosis becomes an explicit representation/semantics choice inside that family.

### Abstract interpretation

Cousot & Cousot's abstract interpretation provides a lattice/fixpoint framework for sound approximation of program semantics.

**Mapping:** no new operator family beyond representation abstraction/coarse-graining, simulation/bisimulation, CEGAR refinement and typed approximation budgets. It is a load-bearing formal parent for any claim of a new sound abstract state space.

### Hitting-set / diagnosis duality

Conflict-directed model-based diagnosis makes diagnoses minimal hitting sets of conflicts, with later work exploiting the duality computationally.

**Mapping:** no new operator family beyond `MINIMAL_CONFLICT_CORRECTION_ANALYSIS`, model-based diagnosis and verified failure-constraint compilation. It sharpens the exact interface: conflicts are explanations of inconsistency; hitting sets/corrections are repair hypotheses; inductive constraints require a separate proof obligation.

## Bounded flatness conclusion

Rounds 007–009 now provide:

- one full registered route-universe sweep;
- one independent alternate-vocabulary repeat that found the missing conflict/correction operator;
- one additional adversarial neighborhood repeat after that operator was frozen, which added only stronger parent implementations/semantic refinements and **no new operator family**.

Therefore a bounded statement is licensed:

`OPERATOR_FAMILY_FLAT_ON_REGISTERED_ROUTE_AND_REPEAT_UNIVERSE`.

This statement is scoped to the route/query families recorded in rounds 001–009. It does **not** mean:

- all literature has been read;
- no future paper can add a useful mechanism;
- all operator implementations exist;
- all strongest parents are implemented;
- any mechanic is empirically useful;
- Paper V/VI are promotion-complete.

The remaining work is now implementation/evidence, not broad taxonomy expansion: absorb or implement the strongest parents/operators already found, execute frozen development/fresh-assurance packets, and reopen perspective discovery only when a result exposes a new residual or later search adds a genuinely new family.
