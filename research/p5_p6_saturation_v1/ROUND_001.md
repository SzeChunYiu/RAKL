# Paper V–VI RSHEA literature/mechanism saturation — round 001

Status: **NOT_SATURATED**.  This is a proposal/research-routing artifact and grants no scientific or promotion authority.

Frozen repository subject for this pass: `main@e5b1e3fb2c231381ca6eacf7122710a0d5e7f282`.

## Expert cell

- formal theorem proving / mathematical assurance;
- algorithms and search;
- active experimental design / diagnosis;
- metareasoning / portfolio selection;
- adversarial governance and metrology.

## Search families deliberately changed from the earlier pass

1. theorem proving: global premise retrieval, proof-progress prediction, recursive planning/harness design, structure-aware proof mining;
2. computation allocation: rational metareasoning / value of computation / budget-aware reasoning;
3. algorithm portfolios: portfolio construction, generalization/overfitting, robust automatic algorithm selection, solver selection;
4. diagnosis: non-greedy active feature acquisition, jointly informative measurements, decision-oriented acquisition;
5. dynamic search: D* Lite/LPA*, adaptive A* variants, exact parallel SSSP/work-depth tradeoffs;
6. concurrency: modern stateful partial-order reduction and lower bounds.

A new mechanism/parent/counterexample was retained in every major search family, therefore no bounded semantic-flatness claim is licensed.

## Newly retained objects

### VTG / Paper V

**BFS-Prover** (`arXiv:2502.03438`) is a strong simple-search parent: scaled best-first search can be competitive with more complex tree-search schemes.  This reinforces that VTG must demonstrate an incremental residual beyond a properly scaled best-first parent, not merely greedy/local search.

**LeanProgress** (`arXiv:2502.17925`) adds a distinct progress/value coordinate: predict remaining proof progress and use it inside best-first search.  This is directly adjacent to a goal-relative VTG field.  A VTG experiment that omits it cannot tell whether gains come from a new geometry or from ordinary learned proof-progress estimation.

**LeanSearch v2** (`arXiv:2605.13137`) shows global premise retrieval can change proof success under a fixed prover loop.  Retrieval must therefore be either matched/frozen across VTG arms or included as an explicit parent/ablation coordinate.

**REAL-Prover** (`arXiv:2505.20613`) further supports retrieval-augmented Lean proving on harder mathematics; retrieval is not a minor preprocessing detail.

**MerLean-Prover** (`arXiv:2605.26959`) makes the proof plan itself the recursive revision object in a planning/check/Lean harness.  **LEAP** (`arXiv:2606.03303`) likewise uses decomposition, informal blueprints and iterative compiler interaction.  These create a new competing explanation: apparent geometric progress may actually be plan decomposition / representation restructuring.

**PROMISE** (`arXiv:2604.05399`) is a structure-aware proof-mining/search threat: structural proof-state/tactic patterns can support retrieval and adaptation without requiring the exact VTG formalism.

**Decision:** supersede `vtg_lean_geometry_v1` *before execution*.  The next packet must factor search, retrieval, progress estimation and recursive plan/harness effects so that the VTG estimand is genuinely incremental.

### Field construction / selector

**Hydra** (AAAI 2010, DOI `10.1609/aaai.v24i1.7565`) establishes the relevant portfolio principle: iteratively add complementary configurations rather than demand one universally dominant solver.

**Generalization in Portfolio-Based Algorithm Selection** (AAAI 2021, DOI `10.1609/aaai.v35i14.17451`; arXiv `2012.13315`) adds a load-bearing warning: larger portfolios can improve coverage but increase overfitting/generalization risk.

**Towards Robustness and Explainability of Automatic Algorithm Selection** (ICML 2025, PMLR 267) and **Neural Solver Selection for Combinatorial Optimization** (ICML 2025, PMLR 267) add modern selector/robustness parents.

**Decision:** field recovery should target selector regret/generalization and cheapest-useful portfolios, not only a better individual field constructor.  Add a held-out selector-generalization gate and an oracle-portfolio regret coordinate.

### Diagnosis

**Performance Bounds for Active Binary Testing with Information Maximization** (ICML 2024, PMLR 235) shows greedy InfoMax guarantees depend on an availability/separability condition; the current failed greedy diagnosis does not close the broader active-testing family.

**Acquisition Conditioned Oracle for Nongreedy Active Feature Acquisition** (ICML 2024, PMLR 235) explicitly targets cases where greedy acquisition misses jointly informative feature sets.

**Stochastic Encodings for Active Feature Acquisition** (ICML 2025, PMLR 267) is another non-myopic acquisition family, reasoning over possible unobserved realizations rather than choosing only immediate information gain.

**Towards Cost Sensitive Decision Making** (AISTATS 2025, PMLR 258) aligns even more closely with RAKL's desired QoI: acquire information to improve the downstream decision while balancing acquisition cost.

**Decision:** supersede the diagnosis v2 packet before execution.  The next primary estimand should be *repair/decision risk per total acquisition cost*, with greedy InfoMax only one parent; include non-greedy/joint acquisition and explicit observational-equivalence lower bounds.

### Dynamic/parallel navigation

**D* Lite** (AAAI 2002) is a required incremental heuristic-search parent, but it is not sufficient by itself: **Multipath Adaptive A*** / path-reuse work reports regimes where simpler A*-based reuse can outperform D* Lite.  Dynamic parent choice must therefore itself be regime-aware.

Parallel SSSP is also a deeper parent family than the current exact-field comparison.  Modern exact parallel shortest-path results (e.g. SODA 2023 exact SSSP with near-linear work/square-root depth and SODA 2026 directed-SSSP work-depth tradeoffs) mean a parallel-depth claim must compare against contemporary exact parallel search, not merely serial Dijkstra reinterpreted in span units.

**Decision:** supersede navigation v2 packet before execution.  Require a *cost-vector Pareto parent set* including incremental A*, adaptive A* path reuse, and exact parallel SSSP; a span-only win is insufficient if work/memory is dominated.

### Path quotient / POR

**Revisiting Stateful Partial-Order Reduction** (`arXiv:2411.16921`) is load-bearing in two directions: it gives a stronger practical stateful POR parent and proves a negative complexity result for near-optimal stateful reduction with blocking (unless P=NP).

This changes the target.  `maximal/near-optimal quotient reduction everywhere` should not be the RSHEA objective.  The meaningful target is an *economically useful heuristic reduction with soundness and applicability guarantees*.

**Decision:** supersede path-certification v2 packet before execution; encode the lower bound as a scope limit and benchmark against the modern stateful POR parent rather than generic classical POR alone.

### Cross-mechanic controller / Paper VI

**Rational Metareasoning for Large Language Models** (`arXiv:2410.05563`) explicitly optimizes a value-of-computation objective to avoid unnecessary reasoning cost.

**Static and Dynamic Values of Computation in MCTS** (`arXiv:2002.04335`) gives a non-myopic computation-value view: choose computations by their expected effect on the final decision, including future computations.

**ROI-Reasoning** (`arXiv:2601.03822`) is a 2026 budget-allocation example: predict reasoning cost/utility before spending the compute and allocate a global budget.

These are strong support for the existing Orion issue #535 reframing: the universal object should be a governed **policy over mechanics/computations**, not an assumption that every mechanic runs on every problem.

**Decision:** open/freeze a new `mechanic_value_of_computation_controller_v1` candidate before capstone integration.  It should decide whether to construct a field, retrieve more premises, run another proof-search expansion, acquire a diagnostic intervention, compute a quotient witness, or verify an intermediate object, based on expected decision-relevant gain per total cost under hard safety/applicability gates.

## Saturation verdict

`NOT_SATURATED`.

Reason: this round added all of the following load-bearing semantic objects that were absent or insufficiently represented in the preceding packet universe:

- proof-progress value estimation;
- global premise retrieval as an independent causal coordinate;
- recursive proof-plan/harness revision;
- robust/generalizing algorithm-selection portfolios;
- non-greedy/joint active acquisition;
- decision-risk rather than cause-label diagnosis;
- adaptive-A* path reuse as a dynamic-search parent;
- contemporary exact parallel SSSP parents;
- a stateful-POR complexity lower bound;
- cross-mechanic value-of-computation control.

The next saturation round must use materially different vocabularies/domains again.  No `SATURATED` label is allowed until repeated rounds add no new load-bearing parent, mechanism, representation, counterexample, lower bound, cost coordinate or falsifier and a bounded coverage receipt exists.
