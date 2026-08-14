# Paper V–VI RSHEA literature/mechanism saturation — round 003

Status: **NOT_SATURATED**. This pass changed domains again: reinforcement-learning predictive representations, behavioral state metrics, hierarchical control and formal active diagnosability. No candidate outcomes are accessed and no authority is granted.

Parent candidate-basis head: `rshea/p5-p6-saturation-round-002@6876824155871527f3fa5175cc627e8a32f7535c`.

## Newly retained load-bearing objects

### Predictive geometry rather than goal-specific field construction

Peter Dayan's **successor representation** (1993) represents expected future state occupancy under a policy. It is a predictive map of dynamics rather than a field tied to one terminal goal. Barreto et al.'s **successor features + generalized policy improvement** later separates reusable dynamics/features from task reward and reuses policies across related objectives.

This attacks a core assumption in the current field lane: rebuilding one goal-conditioned potential may be the wrong reusable object when many QoIs/tasks share dynamics but change their objective.

**New alternative:** `PREDICTIVE_DYNAMICS_FIELD` — learn/cache a task-independent predictive transition representation and derive goal/QoI values on demand. Compare its construction/reuse/update cost with goal-specific fields, online LRTA-style learned heuristics, PDB/CEGAR parents and no-field search. Measure transfer when the goal/QoI changes but the transition substrate is fixed.

### Behavioral distances: bisimulation metrics

Bisimulation metrics for MDPs assign distance according to differences in immediate outcomes and future transition behavior, rather than surface/coordinate similarity. Representation-discovery work uses those metrics to build state features/abstractions.

This is a direct parent/threat to Orion's proposed solvability geometry: a useful geometry should be compared against a behaviorally grounded metric where the registered world admits one.

**Consequence for VTG/navigation quotient:** add bisimulation/simulation-metric parents on stochastic or transition-model-known families. If a standard behavioral metric explains the routing gain, absorb it rather than claim a new geometry.

### Policy caches / generalized policy improvement

Successor-feature work also suggests a portfolio structure that is not merely `choose one solver`: cache policies/skills and combine their value functions for a new objective via generalized policy improvement.

**Consequence for field selector / value-of-computation controller:** distinguish *algorithm selection* from *policy/value recombination*. A field/controller can reuse a basis of predictive policies even when no single cached policy is optimal for the new goal.

### Formal active diagnosability

Work on active diagnosis of discrete-event systems formalizes whether controllable actions can drive a partially observed system to a diagnosable belief state. `Diagnosability Planning for Controllable Discrete Event Systems` explicitly searches for action sequences that transform an initially ambiguous belief state into one where diagnosis becomes possible. N-diagnosability/active diagnoser work similarly distinguishes passive insufficiency from controllable information-gathering.

This supplies a stronger exact parent/lower-bound family than generic Bayesian acquisition on finite automata.

**Consequence for diagnosis:** before optimizing expected information/decision risk, classify whether the fault/repair partition is actively diagnosable under the allowed intervention set and safety constraints. If it is not, the correct terminal is an impossibility/identified-set result in that scope, not endless acquisition-policy search.

### Hierarchical actions / temporally extended transformations

Hierarchical control (e.g. feudal/hierarchical RL) provides a different solution to long paths: alter the action basis with temporally extended or higher-level commands rather than only improve navigation over primitive steps.

**Consequence for Paper V/VI mechanics:** a poor geometry may be exposing the wrong operator basis. Add a representation/operator-basis challenge before concluding that local navigation itself is weak. For proof search this corresponds to tactics/lemmas/macros/subproofs as higher-level transitions; for general problem solving it corresponds to verified reusable transformations/options.

## Round 003 saturation verdict

`NOT_SATURATED`.

New retained objects not present in rounds 001–002:

- task-independent predictive dynamics geometry (successor representation/features);
- generalized policy improvement / policy-value recombination;
- behavioral/bisimulation metrics as a geometry/abstraction parent;
- formal active-diagnosability planning and impossibility conditions;
- hierarchical/temporally extended operator-basis change.

These are not synonyms for the existing packets. They change what the reusable object is (predictive dynamics vs goal field), what distance means (behavioral equivalence), what reuse means (policy recombination), and when diagnosis is possible (active diagnosability). Therefore the affected candidate basis expands again before implementation.
