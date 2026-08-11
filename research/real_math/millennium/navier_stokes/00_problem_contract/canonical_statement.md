# Canonical problem contract — 3D incompressible Navier–Stokes

## Official object

For velocity \(u(x,t)\in\mathbb{R}^3\), pressure \(p(x,t)\), viscosity \(\nu>0\), and force \(f(x,t)\), the incompressible Navier–Stokes equations are

\[
\partial_t u + (u\cdot\nabla)u = \nu \Delta u - \nabla p + f,
\qquad
\nabla\cdot u = 0.
\]

The root authority is Charles L. Fefferman's official Clay Mathematics Institute problem description. Its four accepted outcomes (A)–(D) are kept distinct.

## Active positive route

This workspace initially targets official statement **(A)**: for every smooth, divergence-free, rapidly decaying initial velocity \(u_0\) on \(\mathbb{R}^3\), with \(f=0\), there exists a smooth global solution on \(\mathbb{R}^3\times[0,\infty)\) satisfying the bounded-energy condition in the official statement.

A proof of a neighboring statement is not silently treated as (A). In particular, global weak existence, partial regularity, a conditional regularity criterion, or exclusion of one blow-up subclass does not by itself establish (A).

## Blow-up-classification route

Local smooth existence is known. Therefore a failure of the active global-smoothness route would require loss of regularity at a finite time. The blow-up lane studies necessary scenarios for such a failure.

The current atom `NS-B1` is **conditional and Type-I only**:

> Assuming a finite-time Type-I singularity, characterize the parabolically rescaled limit strongly enough to identify and, eventually, close the exact Liouville/rigidity obstruction.

The Navier–Stokes scaling is

\[
u_\lambda(x,t)=\lambda u(\lambda x,\lambda^2 t),
\qquad
p_\lambda(x,t)=\lambda^2 p(\lambda x,\lambda^2 t).
\]

The source-bound Albritton–Barker Type-I framework reduces a Type-I singularity to the existence of a nontrivial mild bounded ancient solution satisfying their registered Type-I decay condition. This is a route reduction, not a root solution.

## Explicit non-success states

The root remains open after any result that does only one of the following:

- excludes exact backward self-similar blow-up;
- excludes discretely self-similar blow-up;
- excludes a Type-I subclass while Type-II remains;
- proves regularity assuming an additional critical norm bound not derived from the Clay hypotheses;
- proves a Liouville theorem for an ancient class not shown to contain every relevant blow-up limit;
- gives finite numerical evidence, a simulated blow-up/no-blow-up result, or a formal asymptotic without a proof;
- proves a statement with mismatched domain, forcing, decay, periodicity, solution class, or quantifiers.

The workspace may also solve the Clay problem by an exact proof of another official accepted outcome (B), (C), or (D), but such a result must be bound to that statement explicitly rather than relabeled as (A).
