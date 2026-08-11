# NS-R001 adversarial atlas A1 — energy-class concentration versus critical control

Authority: `EXACT_SCALING_CALIBRATION / PRE_CANDIDATE_FALSIFIER_INFRASTRUCTURE / NON_SOLUTION_TEST_FIELD / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`

This packet executes the first bounded action selected by the frozen NS-R001 expert cell. It does **not** propose a regularity lemma and it does **not** claim that the fields below solve Navier–Stokes. Its purpose is to make one obstruction executable and reusable before the first solution candidate: **the two Leray energy norms alone cannot control any velocity Serrin-critical norm, nor the corresponding quadratic-pressure critical norm, on the class of smooth divergence-free spacetime fields.** Any viable global-regularity candidate must therefore use additional structure of the true Navier–Stokes evolution.

## Expert-cell dispatch

The same-context cell was re-used with explicit role separation; these are not independent reviews.

- **PDE regularity lead:** audit the velocity and derivative scaling and identify which mixed norms are critical.
- **Harmonic-analysis / pressure lead:** audit the quadratic pressure response `R_i R_j(u_i u_j)` and its critical scaling.
- **Vorticity-geometry lead:** determine what this calibration does *not* test; geometry-specific depletion remains a separate atlas atom.
- **Adversarial falsification lead:** choose a family that keeps both energy-class controls fixed while forcing critical quantities to diverge.
- **Formal-methods lead:** keep the statement restricted to smooth divergence-free test fields; do not infer existence of a Navier–Stokes trajectory with this profile.
- **Novelty / research-value lead:** treat the result as a classical scaling calibration, not new mathematics; its value is route pruning and candidate screening.

Consensus: this is a high-partition pre-candidate screen because it rejects every estimate whose right-hand side depends only on the two energy norms, independent of the proposed notation or interpolation route.

## A1. Exact concentration family

Choose any fixed nonzero

- `phi in C_c^infinity(R^3; R^3)` with `div phi = 0`, and
- `psi in C_c^infinity((0,1))`.

For `lambda >= 1` define

`U_lambda(x,t) = lambda^(3/2) phi(lambda x) psi(lambda^2 t)`.

Every `U_lambda` is smooth, compactly supported in spacetime and divergence-free. It is an **adversarial field family, not a Navier–Stokes solution family**.

For a mixed velocity norm with `m` spatial derivatives,

`||nabla^m U_lambda||_{L_t^p L_x^q}`

scales by

`lambda^(3/2 + m - 3/q - 2/p)`,

with `2/p = 0` for `p = infinity` and `3/q = 0` for `q = infinity`.

### Energy-class controls stay fixed

The two Leray energy norms have exponent zero:

- `L_t^infinity L_x^2`: `3/2 - 3/2 = 0`;
- `L_t^2 dot H_x^1`: `3/2 + 1 - 3/2 - 1 = 0`.

Therefore there are constants depending only on `phi, psi` such that for every `lambda`

`||U_lambda||_{L_t^infinity L_x^2} = C_0`,

`||nabla U_lambda||_{L_t^2 L_x^2} = C_1`.

This realizes concentrated, short-duration bursts while keeping the complete energy-class norm pair unchanged.

### Every velocity Serrin-critical norm diverges

A velocity mixed norm is Navier–Stokes critical when

`2/p + 3/q = 1`.

For every such pair `(p,q)`, the A1 exponent is

`3/2 - 3/q - 2/p = 1/2`.

Hence

`||U_lambda||_{L_t^p L_x^q} = lambda^(1/2) C_{p,q}`

for every finite nonzero base norm. In particular,

`||U_lambda||_{L_t^infinity L_x^3} = lambda^(1/2) ||psi||_infinity ||phi||_3 -> infinity`.

So no finite-valued bound of the form

`critical_velocity_norm(u) <= F(||u||_{L_t^infinity L_x^2}, ||nabla u||_{L_t^2 L_x^2})`

can hold on all smooth divergence-free spacetime fields when the left side is any Serrin-critical velocity norm and `F` depends only on those two energy norms.

This is deliberately narrower than a statement about Navier–Stokes solutions. It proves that **any derivation of critical control must use an equation-specific restriction on admissible energy-class trajectories** rather than functional interpolation of the two energy norms alone.

## A2. Quadratic pressure-response calibration

For a smooth divergence-free field `U`, define the exact quadratic pressure response up to an irrelevant additive function of time by

`P[U] = R_i R_j(U_i U_j)`,

so that

`-Delta P[U] = partial_i partial_j(U_i U_j)`.

The Riesz transforms are homogeneous of degree zero. Therefore for A1,

`P[U_lambda](x,t) = lambda^3 P[phi](lambda x) psi(lambda^2 t)^2`.

For a mixed pressure norm `L_t^p L_x^q`, the scaling exponent is

`3 - 3/q - 2/p`.

Pressure-critical exponents satisfy

`2/p + 3/q = 2`,

so every critical pressure norm in this family scales like `lambda^1` and therefore diverges whenever the base norm is nonzero. For example,

`||P[U_lambda]||_{L_t^infinity L_x^(3/2)} = lambda C_P`.

Again, this does not construct a Navier–Stokes trajectory. It shows that the nonlocal quadratic pressure operator does not by itself repair the energy-to-critical gap on arbitrary divergence-free histories. A future local argument must use dynamical cancellation, scale propagation, or another true-solution constraint, and must expose how pressure tails are controlled.

## A3. Epsilon-regularity implication

The same family also explains why global energy control cannot automatically produce all-scale Caffarelli–Kohn–Nirenberg smallness. On the natural concentration cylinder `r ~ lambda^(-1)`, the standard scale-invariant velocity quantity

`r^(-2) integral_{Q_r} |U_lambda|^3`

grows like `lambda^(3/2)` when the fixed base profile has nonzero local cubic mass. The analogous pressure quantity with `|P|^(3/2)` has the same growth exponent.

Therefore epsilon-regularity is correctly treated as a **downstream conditional gate**: an additional Navier–Stokes mechanism is needed to prevent energy from concentrating into a critical-scale burst.

## Route-pruning consequence

Atlas A1 rejects the entire candidate family

> “derive a Serrin/endpoint critical bound by a universal inequality involving only `L_t^infinity L_x^2` and `L_t^2 dot H_x^1`, plus generic divergence-free/Calderon–Zygmund structure.”

The rejection scope is exact: **arbitrary smooth divergence-free spacetime fields**. It does not rule out estimates that use the PDE residual, local energy inequality, vorticity transport/stretching geometry, time direction, pressure cancellation tied to the equation, frequency-local flux identities, or another structure specific to true Navier–Stokes solutions.

This scope boundary is essential. Tao's averaged-equation blowup independently reinforces the same research-control lesson at the dynamical level: energy cancellation plus broad harmonic-analysis structure is not enough; a positive proof must exploit finer structure of the true nonlinearity.

## Cheapest regression for future candidates

Before accepting any future NS-R001 critical-self-improvement estimate, perform these checks in order:

1. **Scaling:** substitute the exact Navier–Stokes scaling and verify dimensionless constants.
2. **A1 energy-concentration screen:** if the proof uses only energy-class norm bounds and generic divergence-free/CZ estimates, evaluate its claimed inequality on `U_lambda`; any uniform critical bound must fail as `lambda -> infinity`.
3. **Pressure-tail screen:** identify where the proof uses more than the degree-zero Riesz-transform mapping of `u tensor u`.
4. **True-equation witness:** name the exact identity, sign, transport constraint, flux law, geometric depletion mechanism, or causal evolution property that excludes A1-type arbitrary histories.
5. **Averaged-model screen:** ask whether that load-bearing property is preserved by Tao's averaged nonlinearity. If yes, explain why the route does not transfer to the known averaged blowup construction.

Passing A1 is not evidence of regularity; failing it is a cheap route rejection.

## Residual opened

`NS-R001a`: identify and test the **first true-evolution coordinate** that prevents arbitrary energy-class concentration from behaving like A1. Candidate coordinates remain unpromoted and include scale-local nonlinear flux, vorticity/strain geometry, pressure-mediated cancellation, frequency locality, and causal persistence constraints.

The next atlas atom should stress geometry independently of the energy-scaling screen, preferably with explicit smooth divergence-free fields exhibiting strong local strain/vorticity alignment while separating static geometry from dynamical admissibility.

## Source anchors

- Charles L. Fefferman, official Clay Mathematics Institute Navier–Stokes problem description: root statement and scaling context.
- Caffarelli–Kohn–Nirenberg (1982): epsilon/partial-regularity framework; used only for the downstream-smallness interpretation.
- Escauriaza–Seregin–Sverak (2003): endpoint `L_t^infinity L_x^3` regularity; used as a critical-control target, not as an a priori estimate.
- Terence Tao, *Finite time blowup for an averaged three-dimensional Navier-Stokes equation*, JAMS 29 (2016), arXiv:1402.0290: negative structural calibration showing that energy cancellation plus generic harmonic-analysis structure is insufficient.

No novelty claim is made for the scaling calculation.