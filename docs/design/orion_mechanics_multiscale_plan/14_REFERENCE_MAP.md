# Reference Map: Parents as Mechanism Data

This file is not a novelty claim. It records useful parent mechanisms and the exact lesson Orion should extract.

## Lightning leader physics

### Hill et al. (2011), high-speed video observations of a lightning stepped leader

Source:
https://doi.org/10.1029/2011JD015818

Learn:

- negative stepped leaders advance in steps;
- space stems/leaders can form ahead of the main tip;
- propagation is not a precomputed globally known path.

Do not infer:

- lightning solves generic shortest-path problems.

### Wang et al. (2019), branching behavior in natural lightning leaders

Source:
https://doi.org/10.1016/j.jastp.2018.12.010

Learn:

- branching tips are observed in negative leaders;
- multiple local growth candidates can coexist.

### Syssoev et al. (2020), numerical stepping and branching

Source:
https://doi.org/10.1029/2019JD031360

Learn:

- local field thresholds, streamer/space-leader dynamics and evolving conductivity can generate stepping/branching.

## Dielectric breakdown / Laplacian growth

### Niemeyer, Pietronero & Wiesmann (1984), Fractal Dimension of Dielectric Breakdown

Source:
https://doi.org/10.1103/PhysRevLett.52.1033

Learn:

- stochastic growth driven by a field can generate branching fractal structures;
- scale structure can emerge from a simple local rule plus a global field.

## Threshold path concentration

### Blanchini et al. (2021), A threshold mechanism ensures minimum-path flow in lightning discharge

Source:
https://doi.org/10.1038/s41598-020-79463-z

Learn:

- under a specified nonlinear threshold network, current can concentrate along a minimum-threshold path.

Boundary:

- this is a model under defined assumptions, not evidence that natural lightning universally computes shortest paths.

## Physarum

### Nakagaki, Yamada & Tóth (2000), Maze-solving by an amoeboid organism

Source:
https://doi.org/10.1038/35035159

### Tero, Kobayashi & Nakagaki (2007), adaptive transport network model

Source:
https://doi.org/10.1016/j.jtbi.2006.07.015

Learn:

- distributed flow can reinforce useful channels;
- topology adapts from flux;
- path formation can emerge through local feedback.

Orion extraction:

```text
verified progress flux
-> scoped conductance update
```

not literal biological imitation.

## Ant System

### Dorigo, Maniezzo & Colorni (1996)

Source:
https://doi.org/10.1109/3477.484436

Learn:

- positive feedback;
- distributed candidate construction;
- exploration versus reinforcement;
- risk of premature convergence.

Useful as a negative/positive parent for conductance memory.

## Fast Marching / Eikonal

### Sethian (1996), A fast marching level set method for monotonically advancing fronts

Source:
https://doi.org/10.1073/pnas.93.4.1591

Learn:

- compute an arrival-time field;
- recover path/front behavior from local updates consistent with a global PDE;
- a field representation can make path information locally accessible.

Boundary:

- relies on strong mathematical structure; generic research problems do not automatically satisfy an Eikonal equation.

## Diffusion geometry

### Coifman & Lafon (2006), Diffusion Maps

Source:
https://doi.org/10.1016/j.acha.2006.04.006

Learn:

- a diffusion process can define multiscale geometry;
- representation geometry can expose structure not obvious in raw coordinates.

Orion question:

- can a diffusion-like metric be built from action consequences / solver transitions rather than data similarity?

## Convex lifting

### Candès, Strohmer & Voroninski (2011), PhaseLift

Source:
https://arxiv.org/abs/1109.4499

Learn:

- a difficult nonconvex/combinatorial-looking formulation may become tractable in a lifted representation;
- lifting cost is real and can be large.

Orion extraction:

```text
search for representation transforms whose downstream solver is dramatically simpler
```

## Koopman-style lifting

### Brunton et al. (2016), finite linear representations of nonlinear dynamics

Source:
https://doi.org/10.1371/journal.pone.0150171

### Korda & Mezić (2016), linear predictors / MPC via lifted observables

Source:
https://arxiv.org/abs/1611.03537

Learn:

- a nonlinear problem can become approximately linear under suitable observables;
- finding the right observables is itself a central challenge.

This maps extremely well to representation-search research.

## Current AI: per-task paradigm routing

### Select-then-Solve (2026)

Source:
https://arxiv.org/abs/2604.06753

Learn:

- no fixed reasoning paradigm need dominate;
- per-task selection can recover part of the oracle gap.

Orion should go beyond selecting a small named paradigm set and diagnose which **mechanic coordinate** is deficient.

## Current AI: latent planning

### Thoughts-as-Planning (2026)

Source:
https://arxiv.org/abs/2605.28842

Learn:

- planning over latent semantic representations is an active research direction;
- multi-scale edit/planning spaces are plausible.

Boundary:

- latent reasoning alone does not provide Orion's evidence, authority, composition or missing-mechanic semantics.

## Theorem proving: progress heuristic

### LeanProgress (2025)

Source:
https://arxiv.org/abs/2502.17925

Learn:

- learned proof-progress signals can improve best-first proof search.

Orion question:

- can progress be represented as a more general field over heterogeneous solver actions?

## Theorem proving: global premise retrieval

### LeanSearch v2 (2026)

Source:
https://arxiv.org/abs/2605.13137

Learn:

- retrieving a *set* of jointly useful premises differs from one-step similarity retrieval;
- iterative sketch/retrieve/reflect can improve downstream proving.

This is relevant to backward obligation fronts and interaction-space search.

## Current RAKL/Orion parent surfaces

Planning snapshot:

```text
commit 94a35f168e81c57cb678c8d324f4d6190cb3fc46
```

Relevant existing modules:

```text
src/rakl/problem_fibre.py
src/rakl/search_controller.py
src/rakl/missing_operator.py
src/rakl/metacognition.py
src/rakl/saturation.py
src/rakl/epistemic_search.py
src/rakl/method_specs.py
src/rakl/v3_runtime.py
```

These should be extended, wrapped and benchmarked—not duplicated.
