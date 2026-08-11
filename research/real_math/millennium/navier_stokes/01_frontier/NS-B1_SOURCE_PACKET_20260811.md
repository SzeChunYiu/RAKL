# NS-B1 source packet — Type-I blow-up to ancient-solution classification

**Authority:** source-bound context only; no new theorem candidate.

**Root control:** issue #83.

## 1. Exact local object

The active route is the unforced whole-space Clay statement (A). The conditional atom `NS-B1` asks what a **Type-I finite-time singularity**, if one exists, forces after parabolic zooming.

The scaling
\[
u_\lambda(x,t)=\lambda u(\lambda x,\lambda^2 t),\qquad
p_\lambda(x,t)=\lambda^2p(\lambda x,\lambda^2t)
\]
preserves the 3D Navier–Stokes equations. A classification argument must therefore track scale-invariant local velocity, gradient, and pressure quantities; compactness topology; the local energy inequality; and persistence of nontriviality/singularity.

## 2. Primary source anchors and exact use

### Fefferman — official Clay statement

Charles L. Fefferman, *Existence and smoothness of the Navier–Stokes equation*, Clay Mathematics Institute official problem description.

Use here: exact root statement, admissible initial data/forcing/domain, smoothness and bounded-energy target, and the fact that the Clay problem distinguishes four accepted outcomes (A)–(D). This packet chooses (A) as the active positive route and does not weaken it.

### Caffarelli–Kohn–Nirenberg (1982)

L. Caffarelli, R. Kohn, L. Nirenberg, *Partial regularity of suitable weak solutions of the Navier–Stokes equations*, **Comm. Pure Appl. Math. 35** (1982), DOI `10.1002/cpa.3160350604`.

Use here: suitable weak solutions, local-energy structure, and epsilon-regularity/partial-regularity machinery. Boundary: bounded Type-I quantities are not automatically epsilon-small.

### Nečas–Růžička–Šverák (1996)

J. Nečas, M. Růžička, V. Šverák, *On Leray's self-similar solutions of the Navier–Stokes equations*, **Acta Math. 176** (1996), DOI `10.1007/BF02551584`.

Use here: exact backward self-similar blow-up can be reduced to a stationary profile and ruled out under the paper's profile hypotheses. Boundary: a generic Type-I ancient trajectory need not be stationary in rescaled time.

### Tsai (1998)

T.-P. Tsai, *On Leray's self-similar solutions of the Navier–Stokes equations satisfying local energy estimates*, **Arch. Rational Mech. Anal. 143** (1998), DOI `10.1007/s002050050099`.

Use here: stronger source-bound exclusion of Leray self-similar solutions under broad local-energy-type assumptions. Boundary: still a self-similar/profile theorem, not a theorem for every bounded ancient trajectory.

### Escauriaza–Seregin–Šverák (2003)

L. Escauriaza, G. Seregin, V. Šverák, *L_{3,∞}-solutions of Navier–Stokes equations and backward uniqueness*, **Russian Math. Surveys 58** (2003), DOI `10.1070/RM2003v058n02ABEH000609`.

Use here: the scale-critical `L^∞_t L^3_x` regularity/backward-uniqueness route. Boundary: generic Type-I local-energy boundedness is not the same as the required critical `L^3` control.

### Koch–Nadirashvili–Seregin–Šverák (2009)

G. Koch, N. Nadirashvili, G. Seregin, V. Šverák, *Liouville theorems for the Navier–Stokes equations and applications*, **Acta Math. 203** (2009), DOI `10.1007/s11511-009-0039-6`.

Use here: bounded ancient solutions as the natural rigidity object. The paper proves Liouville results in 2D and restricted 3D settings and makes clear that the general 3D bounded-ancient problem is beyond those methods. Boundary: no general 3D bounded-ancient Liouville theorem may be assumed.

### Albritton–Barker (2019)

D. Albritton, T. Barker, *On local Type I singularities of the Navier–Stokes equations and Liouville theorems*, **J. Math. Fluid Mech. 21**, 43 (2019), DOI `10.1007/s00021-019-0448-z`.

Use here: the first load-bearing route reduction. Their Theorem 1.1 gives an equivalence between a Type-I singular point of a suitable weak solution and the existence of a nontrivial mild bounded ancient solution satisfying their registered Type-I decay condition `I<∞`. Their paper also separates multiple Type-I formulations and warns that boundedness of one formulation does not automatically imply the others. They prove stronger rigidity under additional critical weak-`L^p`/`L^3`-type hypotheses.

Boundary: the equivalence **does not** itself exclude Type-I singularities; it identifies the ancient object that must be classified.

## 3. Representation map

Use logarithmic self-similar time around a hypothetical blow-up point only as a representation, not as a theorem:

| Blow-up representation | Renormalized-flow object | Existing rigidity coverage |
|---|---|---|
| Exact backward self-similarity | fixed point / stationary profile | strong classical exclusions under stated hypotheses |
| Discrete self-similarity | periodic orbit | only source-specific classes; do not import fixed-point proofs |
| Generic Type-I ancient limit | complete bounded trajectory | general 3D rigidity remains open |
| Type-II singularity | may escape Type-I compactness class | outside `NS-B1` |

The key logical gap is therefore not “prove self-similar profiles are zero.” That route is already heavily constrained by prior work. The open transfer question is: **which additional property is inherited by every Type-I ancient limit and is strong enough for a valid rigidity theorem?**

## 4. Hostile assumptions audit

Any future candidate must explicitly audit:

1. **Compactness topology.** What converges strongly enough to pass the nonlinear term and preserve the relevant critical quantity?
2. **Nontriviality.** Why does the singular core not disappear under weak convergence?
3. **Pressure.** How is nonlocal pressure localized, normalized, and passed to the limit?
4. **Far field.** Which decay/integrability properties survive zooming, and which are lost?
5. **Orbit type.** Why would a generic bounded ancient trajectory be stationary or periodic?
6. **Criticality.** Does a bounded scale-invariant quantity really imply the exact `L^3`, weak-`L^p`, vorticity, or energy hypothesis used by the desired theorem?
7. **Type-II boundary.** Even a complete Type-I exclusion leaves a separate route-level residual.

## 5. Counterexample/adversarial calibration

Forward self-similar and discretely self-similar Navier–Stokes solutions exist in source-valid settings. They are not backward blow-up counterexamples, but they decisively falsify the informal inference “scale invariance by itself forces triviality.” Thus every future rigidity argument must identify the backward-time, ancient, energy, integrability, or decay hypothesis that actually carries the contradiction.

The analogous search failure to avoid is **fixed-point fixation**: proving a theorem for stationary rescaled profiles and silently treating it as a theorem for all Type-I trajectories.

## 6. Candidate-independent next discriminator

Before inventing a new Liouville theorem, build a source-bound implication/counterexample matrix whose rows include at least:

- Albritton–Barker `I<∞` Type-I decay;
- scale-invariant weak-`L^p` Type-I conditions;
- `L^∞_t L^3_x` or ancient sequence-`L^3` control;
- exact self-similarity;
- discrete self-similarity;
- bounded mild ancient solutions;
- far-field decay/integrability assumptions;
- local-energy/pressure hypotheses;
- existing Liouville conclusions.

Each implication is tagged `PROVED`, `REFUTED`, `UNKNOWN`, or `NOT_SAME_OBJECT`, with the exact primary source. The next theorem candidate may be selected only after this matrix exposes the smallest genuinely open bridge.

## 7. Current authority

`SOURCE_BOUND_PRE_CANDIDATE_CONTEXT / NO_NEW_THEOREM / ROOT_AUTHORITY_NONE`
