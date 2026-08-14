# Paper V–VI RSHEA literature/mechanism saturation — round 002

Status: **NOT_SATURATED**. This pass deliberately changed domains and vocabulary again. It grants no scientific or promotion authority and produces no evaluated candidate outcome.

Parent candidate-basis head: `rshea/p5-p6-saturation-round-001@6c62396bd0ae90d9561e3dded360819d9a32a662`.

## Search families changed from round 001

1. real-time / agent-centered heuristic search and online heuristic learning;
2. abstraction-refinement from formal verification rather than static abstraction/quotienting;
3. active diagnosis under adaptive-submodular / correlated-noisy test structure;
4. execution-system reuse/caching inside Lean tactic search;
5. hyper-heuristics operating on a search space of heuristics rather than solution states;
6. multi-objective/version-robust proof optimization.

## Newly retained load-bearing objects

### Proof execution substrate: proof-state snapshotting

`Keep the Proof State Live: Snapshotting for Efficient Tactic Search in Lean 4` (`arXiv:2605.25556`) reports that repeated proof-state reconstruction can dominate per-branch wall time and proposes snapshot/reuse of elaborated proof state. This is structurally different from a better proof-search heuristic.

**Consequence for VTG / solver compilation:** any claim that geometry or search reduces wall time must match the proof-state execution substrate. A treatment may look faster only because a parent repeatedly reconstructs state. Add a snapshot-enabled parent/ablation and charge snapshot construction, memory, invalidation and restore cost. This also links exact structural identity reuse to the theorem-search runtime.

### Online field learning: real-time heuristic search

Real-time heuristic-search work (LRTA*/LSS-LRTA*/RTAA* families) updates heuristic values while solving rather than requiring one precomputed global field. Recent work on **Real-time Cost-algebraic Heuristic Search** extends completeness arguments to domains satisfying cost-algebra axioms, directly connecting this family to Orion's typed path-cost surface. Work on heuristic learning / depression avoidance shows that online correction structure itself matters.

**Consequence for field/navigation:** a field constructor/portfolio benchmark that omits online heuristic learning is incomplete. Add an `ONLINE_LEARNED_FIELD` family that begins with a cheap lower-information heuristic, updates only visited/local regions, and is compared under cumulative multi-episode cost, first-solution latency, convergence, and memory. The exact prebuilt field remains an oracle, not the only meaningful geometry.

### Adaptive abstraction: CEGAR rather than fixed quotient

Clarke et al.'s Counterexample-Guided Abstraction Refinement (CAV 2000, DOI `10.1007/10722167_15`) iteratively refines an abstraction only when an abstract counterexample is spurious. This is a different transformation from selecting one fixed abstraction up front.

**Consequence for navigation quotient / VTG representation lifting:** introduce an adaptive quotient/refinement parent. A spurious abstract route becomes information that refines the representation; it is not merely a failed route to discard. Measure number/cost of refinements, final abstract-state count, concrete verifier calls, and total solve cost. Preserve the rule that spurious abstract routes never mint solution authority.

### Conditional greedy diagnosis: adaptive submodularity and correlated/noisy tests

Adaptive-submodular optimization gives conditions under which greedy adaptive selection has approximation guarantees. `Near-optimal Bayesian Active Learning with Correlated and Noisy Tests` (AISTATS 2017, PMLR 54) develops ECED for correlated/noisy tests using an adaptive-submodular analysis. `Active Detection via Adaptive Submodularity` (ICML 2014, PMLR 32) similarly shows that structural properties of the utility determine whether greedy-like policies are justified.

**Consequence for diagnosis:** do not treat greedy InfoMax as uniformly weak or uniformly strong. The next packet must classify worlds by whether the registered utility/test model satisfies the structural conditions that justify greedy acquisition. Compare greedy, ECED/adaptive-submodular parent, non-greedy ACO/stochastic acquisition and exact finite-horizon oracle. Applicability is itself a learned/verified structural coordinate.

### Hyper-heuristics: selection/generation over heuristic components

Burke et al., *Hyper-heuristics: a survey of the state of the art* (JORS 2013, DOI `10.1057/jors.2013.71`) formalizes a higher-level search object: select or generate heuristics/components rather than directly search the underlying solution space.

**Consequence for the value-of-computation controller:** round 001's controller only selects among frozen computations. Add a separate method-evolution coordinate for composing/generating bounded heuristic configurations from approved components. This must remain proposal-only and pass the normal mechanic packet/evaluation route; controller success cannot self-authorize generated mechanics.

### Multi-objective proof optimization / version robustness

`Lean Refactor` (`arXiv:2605.20244`) treats proof length, compilation cost and version compatibility as competing objectives and uses version-filtered retrieval of refactoring strategies.

**Consequence for path-cost / compilation:** add version robustness and proof-compilation cost as explicit consumer coordinates where relevant. A shorter proof is not necessarily cheaper or more robust. Solver-compilation and certificate-assembly evaluations should preserve a Pareto frontier when no consumer utility justifies scalarization.

## Round 002 saturation verdict

`NOT_SATURATED`.

New retained objects absent from round 001 include:

- proof-state snapshot/reuse as an execution-substrate parent;
- online/local heuristic learning as an alternative to global field construction;
- counterexample-guided abstraction refinement as an adaptive representation mechanism;
- adaptive-submodular applicability conditions and an ECED correlated/noisy-test parent;
- hyper-heuristic generation/composition above fixed mechanic selection;
- proof version-robustness and compilation cost as path/solver coordinates.

Because the candidate basis changed again, no affected round-001 successor may begin implementation until its packet is amended or superseded. The correct status is not failure; it is `BASIS_EXPANDED_BEFORE_EXECUTION`.
