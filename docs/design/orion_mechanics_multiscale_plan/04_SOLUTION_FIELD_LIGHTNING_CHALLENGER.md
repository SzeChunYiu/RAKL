# Solution Field / Lightning Challenger

## 1. Research hypothesis

Instead of expanding candidate paths one by one, construct a **field over a problem-solving representation** such that local field information predicts globally useful next actions.

The ideal property is:

\[
\langle d(a),-\nabla \Phi(z)\rangle > 0
\quad\Longrightarrow\quad
\mathbb E[\Delta R_{\rm root}\mid a] > 0
\]

often enough to reduce search cost.

This is a hypothesis, not an assumption.

## 2. Corrected natural analogy

Negative lightning stepped leaders:

- propagate in discrete steps;
- commonly branch;
- develop structures ahead of the leader tip;
- are governed by local electric-field conditions and evolving conductivity;
- do not precompute a final shortest path.

Dielectric-breakdown models generate branching fractal structures from Laplacian-field-driven growth.

A separate threshold-network model shows that, under particular nonlinear network assumptions, current can concentrate on a minimum-threshold path.

The computational mechanism to learn is therefore:

```text
global boundary constraints
-> field
-> local propagation
-> competing branches
-> reinforcement / conductivity
-> path concentration
```

not “lightning instantly knows the shortest path.”

## 3. Solvability Space

Define a graph or manifold of **actionable solver states**, not generic semantic embeddings.

A state node may encode:

```text
problem state
representation
active atom/fibre
known obligations
residual
method/operator state
verification status
scale
```

Edges are executable solver transitions:

```text
apply operator
change representation
retrieve evidence
split atom
run verifier
invent auxiliary object
change scale
```

## 4. Key distinction: semantic space versus solvability geometry

Do not optimize only:

```text
semantic similarity
```

We need coordinates in which geometry correlates with:

```text
verified cost-to-go
operator applicability
obligation closure
interface compatibility
residual reduction
```

Provisional term:

# Solvability Geometry

A representation \(\phi\) is useful when nearby directions correspond to similar **action consequences**, not merely similar text.

## 5. Four field modes

Implement separately.

### F1 — Exact arrival-time field

For an explicit known graph with nonnegative edge costs, compute exact/near-exact cost-to-go or arrival time.

Purpose:

- unit-test the APIs;
- establish an oracle field;
- quantify distortion of approximate fields.

This is not a novelty claim.

### F2 — Conductive potential field

Create edge conductance \(g_{ij}\).

A simple starting model:

\[
g_{ij}
=
\exp(-\beta c_{ij})
\cdot q_{ij}
\cdot k_{ij}
\]

where:

- \(c_{ij}\): resource cost;
- \(q_{ij}\): estimated action viability in \([0,1]\);
- \(k_{ij}\): compatibility/gating factor.

With target boundary potential fixed, solve a graph Laplacian system:

\[
L_g u=b.
\]

Use current/flux:

\[
I_{ij}=g_{ij}(u_i-u_j)
\]

as a routing signal.

Important: this produces multi-route flow, not necessarily a shortest path.

### F3 — Breakdown front

Maintain a frontier.

At each step:

```text
compute local field
select one or several frontier extensions
apply threshold
branch if uncertainty / comparable flux is high
execute selected extensions
increase/decrease conductance from verified outcomes
repeat
```

This is the closest lightning-inspired algorithmic challenger.

### F4 — Learned progress field

Later, learn:

\[
\widehat \Phi(z)
\approx
\text{verified remaining cost/residual-to-go}.
\]

This can be trained from `MechanicsEpisode` histories.

Only this mode can plausibly amortize expensive global search across future problems.

## 6. Conductance memory

Success should not simply “reward a path.”

Update is scoped:

```text
same structural coordinates?
same representation?
same regime?
same verifier?
same target effect?
```

A simple experimental update:

\[
\log g_e^{t+1}
=
\log g_e^t
+
\eta_+ r_e
-
\eta_- f_e
-
\lambda\,\text{staleness}
\]

where:

- `r_e`: verified positive root contribution;
- `f_e`: verified failure/obstruction signal.

Negative conductance updates are not deletion. Failure records remain append-only.

## 7. Branching rule

Do not collapse immediately to one path.

Possible rule:

```text
if top_flux / second_flux > concentration_threshold:
    extend top branch
else:
    extend K diverse branches subject to budget
```

Always reserve an exploration branch if coverage is incomplete.

## 8. Bidirectional fields

Many problems have useful target-side structure.

Build:

```text
forward frontier:
    what can I do from current state?

backward obligation frontier:
    what must be true for the target to be verified?
```

Intersect them.

For theorem proving:

```text
forward: executable tactic states
backward: required lemmas / goal decompositions
```

For science:

```text
forward: available evidence/actions
backward: obligations of the requested claim
```

## 9. Representation lifting

The deepest challenger is not the field alone.

It is:

\[
P
\stackrel{\phi}{\longrightarrow}
Z
\stackrel{\Phi}{\longrightarrow}
\text{local flow}
\stackrel{\pi}{\longrightarrow}
\text{executable path in }P.
\]

The problem may be hard in original coordinates but easy in a lifted representation.

This pattern has parents in:

- convex lifting;
- Koopman-style linearizing observables;
- kernel/feature methods;
- diffusion geometry;
- dynamic programming/value functions;
- Fast Marching/Eikonal methods.

Orion's question is whether a **problem-solving** lift can be discovered and validated automatically.

## 10. Avoid circularity

The main failure mode:

> computing a perfect field may be as hard as solving the problem.

Therefore every field benchmark must report:

```text
field construction cost
field update cost
path extraction cost
execution cost
verification cost
total
```

A field that saves 1,000 graph expansions but costs 10,000 equivalent expansions to construct fails.

## 11. Path recovery and certificates

The field proposes a route; the original domain verifies it.

```text
field-space path
-> decode executable actions
-> execute
-> verify in original semantics
```

If decoding is incomplete:

```text
FIELD_ROUTE_NOT_EXECUTABLE
```

If execution fails:

```text
FIELD_FALSE_ATTRACTOR
```

If a route succeeds but costs more:

```text
FIELD_DIRECTION_VALID_EFFICIENCY_UNPROVEN
```

## 12. Initial deterministic benchmark

### World generator

Generate graphs with:

```text
node features
edge action types
edge true costs
edge hidden validity
target set
alternative representations
```

Create task families:

1. smooth cost field;
2. deceptive local minimum;
3. sparse shortcut;
4. multiple comparable paths;
5. dynamic edge failure;
6. hidden target-relevant coordinate;
7. representation lift that linearizes path;
8. lift that destroys useful locality;
9. hierarchical graph with interface gates;
10. stochastic observations but deterministic ground truth.

### Baselines

```text
uniform-cost search
A*
greedy local heuristic
beam search
current Orion operator router
conductive field
breakdown front
field + exploration
field + representation lift
oracle cost-to-go field
```

## 13. Metrics

```text
solve_rate
verified_root_success
total_cost
graph_expansions
path_stretch
field_construction_cost
gradient_alignment
false_attractor_rate
dead_end_rate
branching_factor
exploration_coverage
conductance_lock_in_rate
recovery_after_edge_failure
representation_gain
fresh_transfer_gain
```

### Gradient alignment

For state \(z\), let recommended action be \(a_\Phi\).

Measure rank correlation between field-implied ordering and true one-step verified value.

### Path compression

\[
\text{compression}
=
\frac{\text{search cost in original representation}}
{\text{search cost after lift + field overhead}}.
\]

This is a direct test of the user's “find the path quickly in representation space” idea.

## 14. Promotion boundary

Even if this works:

```text
field useful for routing
-X-> field proves correctness
```

The scientific claim should initially be:

> In registered task families, a specified solvability-field construction reduced verified solution cost relative to registered baselines under matched resources.

Nothing broader.
