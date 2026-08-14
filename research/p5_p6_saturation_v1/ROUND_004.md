# Paper V–VI RSHEA literature/mechanism saturation — round 004

Status: **NOT_SATURATED**. This pass changes domains to incremental programming systems, SAT/CSP conflict learning and planning nogoods. It generates no evaluated mechanic outcome and grants no authority.

Parent candidate-basis head: `rshea/p5-p6-saturation-round-003@81e3dce33e197c85b709b5ec827ea4320e80a959`.

## Newly retained load-bearing objects

### Demand-driven incremental computation / dynamic dependence graphs

Self-adjusting computation maintains explicit dependency information so a change can propagate only through affected computations. **Adapton** (PLDI 2014) further makes this demand-driven and composable rather than eagerly recomputing every dependency.

This is more general than the current ad hoc `lazy repair` story. A field, quotient, theorem-search cache, compiled solver representation or verification result can be treated as a dependency-tracked derived object whose invalidation is propagated from changed premises, operators, goals or environment versions.

**Consequence:** add a general `DEPENDENCY_TRACKED_INCREMENTAL_RECOMPUTATION` parent to dynamic field/navigation and verified solver compilation. The experiment must compare full rebuild, hand-coded local repair and demand-driven dependence propagation. Measure dependency-graph construction/memory, invalidation precision/recall, recomputed work, stale-use error and total end-to-end cost.

### Conflict-driven clause / nogood learning

GRASP (Marques-Silva & Sakallah, IEEE TC 1999) established conflict analysis and conflict-induced clauses as a way for SAT search to learn from failures. Planning work on **State Space Search Nogood Learning** adapts conflict-directed learning to reachability/state-space search and learns dead-end detectors that can refute entire future search subtrees.

This is a different use of negative history from Orion's current failure lattice. A failure record is descriptive memory; a sound learned nogood is an *active constraint* on future search.

**New candidate:** `VERIFIED_FAILURE_CONSTRAINT_COMPILATION`.

Input must be a failure/refutation with an exact logical/operational scope and a machine-checkable explanation/unsat-core/conflict witness. Output is a scoped pruning constraint/nogood that may reject future candidate states only when the target scope/preconditions match. A mere failed attempt, heuristic dead end, correlation, timeout or `CANNOT_CHECK` can never become a pruning constraint.

### Failure-driven explanation-based learning

Work unifying intelligent backtracking and failure-driven explanation-based learning in constraint satisfaction/planning shows the broader mechanism: explain why a branch fails, regress/generalize that explanation to the appropriate search context, and reuse it to avoid equivalent failures.

**Consequence for RAKL:** diagnosis should not stop at a cause label. When a failure explanation is sound enough, ask whether it can be compiled into:

- a pruning constraint/nogood;
- a restored precondition for a reusable tool;
- a representation/refinement obligation;
- an operator-selection warning.

These have different authority and reuse semantics and must not be collapsed.

## Round 004 saturation verdict

`NOT_SATURATED`.

New retained semantic objects not present in rounds 001–003:

- dependency-tracked/demand-driven recomputation as a general incremental substrate;
- conflict/nogood learning as executable negative knowledge;
- sound failure-explanation regression/generalization;
- an explicit distinction between descriptive failure memory and authority-bearing scoped pruning constraints.

This materially expands the mechanics of learning from failure, dynamic repair and solver compilation. Implementation remains blocked until the new parent/candidate basis is packet-bound.
