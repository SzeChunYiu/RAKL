# R003 — circuit-state dual potentials

## Exact finite model

Fix a Boolean gate basis `B`, input count `n`, and source wires consisting of input truth tables and registered constants.

A **circuit state** `S` is the set of truth tables currently available as wires. One gate produces an edge

`S -> S union { g(a,b,...) }`

where `g` is a basis gate and all inputs to the gate are already in `S`.

For a target truth table `f`, the minimum circuit size in this finite model is exactly the shortest-path distance from the source state to the set of states containing `f`.

This statement is elementary and is treated as a calibration identity, not a novelty claim.

## Lower-bound certificate principle

Let `Phi(S)` be any state potential satisfying

`Phi(S') <= Phi(S) + 1`

for every legal one-gate edge `S -> S'`.

If `Phi(S0) = 0` and every state containing target `f` has `Phi(S) >= L`, then every circuit for `f` requires at least `L` gates.

The proof is path telescoping. Along a path of `t` gates, `Phi` can rise by at most `t`, so reaching potential at least `L` requires `t >= L`.

Again, the generic principle is not claimed novel. The research question is whether exact small-instance shortest paths can be used to learn a **compressed symbolic potential family** that remains gate-Lipschitz at arbitrary input length and grows superpolynomially on a structured NP-complete target.

## Why this route is worth testing

A conventional output-only complexity measure often fails because one gate can combine two already-complex wires and because circuit sharing destroys formula-style additivity. A state potential is allowed to depend on the entire reusable wire set, so it can explicitly price sharing and cancellation.

This larger design space is also dangerous. If the compressed potential induces a large efficiently decidable useful property of hard truth tables, the natural-proofs audit must block any unjustified leap to a general circuit lower bound.

## Candidate feature families

These are proposal generators only.

- target-relative coverage of restricted subfunctions;
- Fourier/ANF summaries conditioned on the current wire span;
- certificate complexity or sensitivity profiles after restrictions;
- monotone/nonmonotone cancellation signatures;
- communication matrices of target residuals after conditioning on available wires;
- description-length features of residual truth tables;
- adversarial ensembles chosen after the candidate circuit state rather than globally over all functions.

## Discriminator loop

For every proposed `Phi`:

1. test all one-gate transitions in the exact small-state graph;
2. return the first violating edge as a counterexample;
3. if no finite violation occurs, attempt a symbolic gate-Lipschitz proof;
4. audit natural-proofs/algebrization/relativization exposure;
5. measure target growth;
6. retain only candidates that are both proved gate-Lipschitz and asymptotically nontrivial.

Finite success is computational support only. It cannot promote a scalable theorem.
