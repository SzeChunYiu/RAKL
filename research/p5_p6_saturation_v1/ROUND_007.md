# Paper V–VI RSHEA literature/mechanism saturation — round 007

Status: **CANONICAL_METHOD_SURFACE_FLAT_ON_REGISTERED_ROUTE_UNIVERSE; OPERATOR/PARENT BASIS NOT SATURATED**.

This round completes the remaining route families mandated by the Self-RAKL workflow. It makes a deliberately narrower saturation statement than global knowledge saturation. No evaluated mechanic outcome is accessed and no authority is granted.

Parent candidate-basis head: `rshea/p5-p6-saturation-round-006@202dcf0a95307f9bfc33779d1205cab7e11b833f`.

## Remaining route families searched

### Creativity / design fixation / incubation / recombination

Jansson & Smith (1991, Design Studies, DOI `10.1016/0142-694X(91)90003-F`) show design fixation as measurable blind adherence to ideas/examples that constrains conceptual design. Sio & Ormerod's 2009 meta-analysis (`10.1037/a0014212`) finds incubation effects are moderator-dependent rather than uniformly beneficial.

**Mapping:** already owned by representation/fixation failure, fixation-reset/context-rotation, exploration/recombination and explicit activation/non-activation conditions. No new canonical method surface.

**Retained detail:** anti-fixation should be triggered by evidence of representation/example anchoring; incubation/context rotation has a cost and should be applied conditionally, not as generic extra reflection.

### Organizational learning / exploration-exploitation / brokerage

March (1991, Organization Science, DOI `10.1287/orsc.2.1.71`) formalizes the exploration/exploitation tension. Burt (2004, AJS, DOI `10.1086/421787`) shows brokerage across structural holes can expose actors to nonredundant ideas.

**Mapping:** already owned by the exploration-exploitation controller, perspective discovery/JUMP, structural-hole brokerage sampler, memory/reuse and portfolio selection. No new canonical surface.

**Retained detail:** brokerage is useful specifically when the current information neighborhood is redundant; exploration should be measured against opportunity cost and exploitation/reuse value.

### Causal identification / partial identification / transportability

Manski's partial-identification programme treats the identified set/bounds as the honest result when assumptions do not point-identify the target. Pearl & Bareinboim's transportability work gives formal conditions for transferring causal/statistical relations between populations and later completeness results.

**Mapping:** already owned by `identify`, identified/bounded sets, structural-witness/applicability checks, mathematical context translation and target-specific validation. No new canonical surface.

**Retained detail:** for causal-transfer subproblems, a generic analogy/witness parent is insufficient when a formal transportability calculus applies; use the strongest formal transportability/identification parent and preserve bounds when transport is not identifiable.

### Scientific method / metascience

Platt's strong-inference programme (Science 1964, DOI `10.1126/science.146.3642.347`) emphasizes multiple competing hypotheses and experiments designed to eliminate alternatives. Nosek et al. (PNAS 2018, DOI `10.1073/pnas.1708274114`) frame preregistration as fixing research questions/analysis plans before observing outcomes.

**Mapping:** already owned by candidate populations, discriminator selection, frozen predictions/evaluators, chronology and negative-history preservation. No new canonical surface.

**Retained detail:** an experiment that merely improves one candidate's fit but does not make live alternatives disagree is weaker than a strong-inference discriminator; exploratory analyses remain allowed but cannot be relabeled preregistered confirmation.

### Scientific visualization / human factors / communication

Cleveland & McGill (JASA 1984, DOI `10.1080/01621459.1984.10478080`) empirically decompose graphical perception into elementary perceptual tasks and use the results to improve quantitative graphical displays.

**Mapping:** primarily observability/reporting and human-review interface, not a new epistemic or solver surface. No new canonical surface.

**Retained detail:** human-facing governance/observability reports should be tested for faithful decoding of the load-bearing comparison, not merely rendered correctly; graphical encoding can introduce human decision error without changing the underlying scientific state.

### Domain workflow 1 — software debugging

Zeller & Hildebrandt's Delta Debugging (IEEE TSE 2002) systematically reduces a failure-inducing input/configuration to a minimal failure-inducing circumstance and isolates differences between passing and failing cases.

**Mapping:** owned by failure diagnosis / gap discovery, but this exposes a **missing concrete operator implementation** rather than a new canonical surface: `FAILURE_CONDITION_MINIMIZATION`.

This operator is useful before broad causal diagnosis when the failure context itself is high dimensional: shrink the active conditions while preserving the exact failure, then diagnose the smaller obstruction.

### Domain workflow 2 — model-based engineering diagnosis

Reiter (Artificial Intelligence 1987, DOI `10.1016/0004-3702(87)90062-2`) formalizes diagnosis from a system description plus observations. de Kleer & Williams (1987, DOI `10.1016/0004-3702(87)90063-4`) extend model-based diagnosis to multiple faults and incremental/sequential diagnosis.

**Mapping:** already owned by mechanic differential diagnosis, competing cause sets, model-based mechanism reasoning, active discriminator selection and identified-set/abstention semantics. No new canonical surface.

**Retained detail:** diagnosis benchmarks must include model-based minimal-diagnosis/hitting-set parents, not only classifiers or information-gain policies.

## Surface-level result

Across the full registered Self-RAKL route universe, every retained mechanism now maps to an existing canonical method surface. This round therefore supports a bounded statement:

`CANONICAL_METHOD_SURFACE_FLAT_ON_REGISTERED_ROUTE_UNIVERSE`.

It does **not** support `KNOWLEDGE_SATURATED`, `LITERATURE_SATURATED`, `OPERATOR_BASIS_SATURATED` or `ALL_PARENTS_FOUND`.

Rounds 001–005 repeatedly found new parents/operators/mechanisms *inside* existing surfaces; round 006 and the non-debugging portions of round 007 mostly sharpened activation conditions. Delta debugging adds a missing implementation/operator under an existing surface, which is why the operator basis remains `NOT_SATURATED` even though the top-level surface inventory is flat.

## Next gate

Before claiming bounded **operator-basis** saturation, implement/freeze the missing operator candidates discovered across the rounds (including failure-condition minimization) or explicitly benchmark/absorb their strongest parents, then run at least one independent repeat coverage pass from different vocabulary that yields no new load-bearing operator/parent/cost/falsifier.
