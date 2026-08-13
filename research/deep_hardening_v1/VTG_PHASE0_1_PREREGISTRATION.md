# Verified Transformation Geometry — Phase 0/1 preregistration

## Root question

> Does verifier-defined mathematical reachability admit a nontrivially useful **local or bounded-local navigation geometry** on held-out theorem families after all geometry-construction and verification cost is charged?

## Claim boundary

Not:

```text
all mathematics has a simple geometry
all proofs become easy
a shortest proof is efficiently computable
low energy/similarity implies truth
```

Target:

> In a frozen bounded Lean environment, a specified geometry constructed without hidden-route leakage improves verified theorem success and/or total search cost against strong registered controls on fresh theorem families using only local/bounded-local solver information.

## Phase 0: exact bounded universe

Freeze:

- `C_gold`: evaluator-only complete materialized transition/proof information;
- `B_visible`: solver-visible map with hidden routes/intermediate gold labels removed;
- `C_train` / `C_dev`: geometry construction/selection support;
- `C_fresh`: theorem-family-disjoint fresh evaluation.

Each state binds environment/kernel, theorem/spec, context/goals/metavariables, representation and allowed operator basis. Every validated transition has replay/kernel receipt.

No LLM solving in Phase 0.

## Candidate geometries / parents

At minimum include or explicitly justify early elimination of:

```text
no-geometry BFS/best-first
exact graph-distance oracle (evaluator only)
hand structural heuristic
Euclidean embedding
hyperbolic embedding
directed/quasimetric embedding
reachability/successor representation
strong learned proof-progress baseline
multi-chart atlas
quotient-aware geometry
```

## Policies

```text
P1 strict greedy
P2 top-k bounded branching
P3 best-first using geometry
P4 bidirectional / obligation-aware navigation where semantics permit
```

Primary local-navigability surface: `N(k,B)` rather than one-step action accuracy.

## Leakage prohibitions

Construction/selection must not consume fresh hidden proof path, hidden intermediate lemma labels, fresh evaluator shortest distance, answer-key embeddings, future map edges or fresh outcome labels.

Behavior policy/sampling/label sources are part of the learning receipt because observational support can bias a learned reachability field.

## Metrics

- verified theorem success;
- states expanded;
- tactic/verifier calls;
- wall/compute cost;
- geometry construction/storage cost;
- route/proof length stretch;
- false-descent rate;
- local-minimum rate;
- branching required / `N(k,B)`;
- support/OOD failure;
- cross-family transfer;
- leakage audit;
- amortized value under expected reuse and invalidation horizon.

## Phase-1 terminals

```text
NO_USEFUL_LOCAL_GEOMETRY_IN_REGISTERED_SCOPE
LOCALLY_INFORMATIVE_NOT_GREEDILY_NAVIGABLE
ATLAS_NAVIGABILITY_SUPPORTED_GLOBAL_GEOMETRY_UNSUPPORTED
USEFUL_LOCAL_GEOMETRY_SUPPORTED_IN_REGISTERED_SCOPE
```

Only the final three are possible positive characterizations; none implies a universal geometry.

## Kill rule

If no geometry improves closed-loop verified performance/total cost over the strongest search/control after construction cost, stop VTG dynamics work in the registered scope.

## Dynamics gate

Flow, diffusion, Physarum-like conductance, path-integral weighting, stochastic sampling and related dynamics enter **only after** useful geometry exists. They are separately compared to best-first/MCTS/equality-saturation controls.
