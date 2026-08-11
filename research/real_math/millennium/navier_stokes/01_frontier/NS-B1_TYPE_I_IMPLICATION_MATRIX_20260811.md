# NS-B1 source-bound Type-I implication / counterexample matrix

**Atom:** `NS-B1`  
**Authority:** `SOURCE_BOUND_ROUTE_DISCRIMINATION / NO_NEW_NS_THEOREM / ROOT_AUTHORITY_NONE`  
**Purpose:** distinguish proved implications, false proof shortcuts, and genuinely open bridges before any Type-I rigidity candidate is generated.

## Source anchors

1. D. Albritton and T. Barker, *On local Type I singularities of the Navier-Stokes equations and Liouville theorems*, arXiv:1811.00502. Load-bearing items: Theorem 1.1, definitions (1.1)–(1.6), Lemma 2.5, Theorem 1.2.
2. L. Escauriaza, G. Seregin, V. Šverák, *L3,∞-solutions of Navier-Stokes equations and backward uniqueness*, Russian Math. Surveys 58 (2003). Load-bearing role: critical `L^∞_t L^3_x` regularity / backward-uniqueness route.
3. J. Nečas, M. Růžička, V. Šverák, *On Leray's self-similar solutions of the Navier-Stokes equations*, Acta Math. 176 (1996), and T.-P. Tsai, *On Leray's self-similar solutions ... satisfying local energy estimates*, Arch. Ration. Mech. Anal. 143 (1998). Load-bearing role: backward self-similar profile exclusions under their exact profile/integrability hypotheses.
4. G. Koch, N. Nadirashvili, G. Seregin, V. Šverák, *Liouville theorems for the Navier-Stokes equations and applications*, arXiv:0709.3599. Load-bearing role: mild bounded ancient-solution framework and the still-open general 3D classification problem.
5. H. Jia and V. Šverák, *Local-in-space estimates near initial time for weak solutions ... and forward self-similar solutions*, arXiv:1204.0529. Calibration only: self-similarity as a structural form is not itself contradictory; direction, time orientation, data class and decay hypotheses matter.

## Normalized objects

Let `I(v,q)` denote the Albritton–Barker scale-invariant parabolic quantity

`sup_Q [A(Q)+C(Q)+D(Q)+E(Q)]`

with `A,C,D,E` exactly as in their equations (1.1)–(1.5). For the whole-space ancient problem, `Q` ranges over parabolic cylinders compactly contained in `R^3 x (-∞,0)`.

Define the following hypothesis classes.

- `H_I`: `(v,q)` is a non-trivial mild bounded ancient Navier–Stokes solution and `I(v,q)<∞`.
- `H_L3seq`: there are `t_k -> -∞` with `sup_k ||v(t_k)||_{L^3(R^3)}<∞`.
- `H_L3uniform`: `v in L^∞((-∞,0);L^3(R^3))`.
- `H_weakSerrin(p,q)`: the source weak-Lebesgue/Serrin-scale hypothesis used in Albritton–Barker Lemma 2.5.
- `H_SS`: exact backward Leray self-similarity plus the exact profile/local-energy hypotheses required by the cited profile Liouville theorem.
- `H_DSS`: backward discretely self-similar / periodic renormalized orbit.
- `H_GEN`: a general, genuinely non-periodic mild bounded ancient orbit.

## Implication matrix

| Source condition | Target conclusion | State | Exact reason / obstruction |
|---|---|---|---|
| suitable weak Type-I singular point | non-trivial mild bounded ancient solution in `H_I` | **PROVED, source-bound** | Albritton–Barker Theorem 1.1, forward direction under their definitions. |
| non-trivial mild bounded ancient solution in `H_I` | existence of a suitable weak Type-I singular point | **PROVED, source-bound** | Albritton–Barker Theorem 1.1, reverse / blow-down direction. This is not a construction of a Clay singularity from an arbitrary ancient solution lacking `I<∞`. |
| `H_weakSerrin(p,q)` in the source suitable-weak setting | `I<∞` | **PROVED, one direction** | Albritton–Barker Lemma 2.5. The converse is neither stated nor licensed. |
| `H_L3uniform` | `H_L3seq` | **TRIVIAL** | choose any backward sequence. |
| mild ancient + `H_L3seq` | `v=0` | **PROVED, source-bound** | Albritton–Barker Theorem 1.2. |
| `H_I` | `H_L3seq` | **OPEN BRIDGE / NOT SOURCE-LICENSED** | If this were proved, Theorem 1.2 would eliminate the entire Albritton–Barker Type-I ancient class. The source explicitly warns that boundedness of one Type-I formulation is not known to imply the others. |
| `H_I` | `H_L3uniform` | **STRICTLY STRONGER OPEN BRIDGE** | stronger than the preceding bridge; no reason to attack it first. |
| `H_SS` | `v=0` | **PROVED ONLY UNDER PROFILE HYPOTHESES** | Nečas–Růžička–Šverák / Tsai. This cannot be promoted to general Type-I orbit rigidity. |
| `H_I` | `H_SS` | **UNPROVED / STRUCTURALLY UNJUSTIFIED** | finite critical cylinder control supplies no fixed-point theorem for the renormalized flow. |
| `H_I` | `H_DSS` | **UNPROVED** | discrete self-similarity is a special periodic-orbit scenario, not forced by Type-I bounds. Albritton–Barker explicitly identify feasible DSS-type scenarios as open. |
| `H_I` | `H_GEN` excluded | **OPEN CORE RIGIDITY PROBLEM** | equivalent in spirit to excluding the remaining non-trivial Type-I ancient class; no monotonicity/conserved critical quantity is available in the source framework. |
| general mild bounded ancient solution | constant / zero | **OPEN IN 3D** | Koch–Nadirashvili–Seregin–Šverák treat this as a conjectural classification; 2D and special axisymmetric cases are qualitatively easier. |
| fixed-profile self-similar exclusion | full Type-I exclusion | **FALSE AS LOGIC** | a fixed point is only one orbit class; periodic and non-periodic renormalized trajectories remain. |
| full Type-I exclusion | Clay root regularity | **FALSE AS LOGIC** | `NS-B2` Type-II remains a sibling residual. |

## Counterexample-first functional calibration: `I` is not a global-L3 norm by itself

This probe is deliberately **not** a Navier–Stokes counterexample. It tests only whether the numerical definitions of `A,C,D,E` can, without using the PDE, force a global `L^3` time slice.

Choose a non-zero divergence-free `psi in C_c^∞(B(0,rho);R^3)` with `rho<1/8`. For `s=-t>0`, set

`L(s)=1+sqrt(1+s)`, `a(s)=1/L(s)`,

and define the locally finite smooth field

`u(x,t)=sum_{n in Z} a(-t) psi(x - n L(-t)e_1)`, `q(x,t)=0`.

Because `L(s)>=2` and the supports are small, the translated bumps are disjoint. Therefore, for every fixed `t<0`,

`||u(t)||_3^3 = sum_{n in Z} a(-t)^3 ||psi||_3^3 = +∞`.

Nevertheless the scale-invariant **functional** quantity `I(u,0)` is finite. The key uniform count is

`N(B(x,r),s) <= C(1+r/L(s))`

for unit-or-larger radii. A complete bound splits radii at `r=1`:

- `0<r<1`: disjointness and bounded `u,∇u` give local spatial integrals `O(r^3)`, hence `A=O(r^2)`, `C=O(r^3)`, `E=O(r^4)`, `D=0`.
- `r>=1`: one bump contributes `O(L^-2)` to both `L^2` mass and gradient energy and `O(L^-3)` to `L^3` mass. Thus spatial integrals are bounded by constants times `L^-2(1+r/L)` for `|u|^2,|∇u|^2` and `L^-3(1+r/L)` for `|u|^3`.
- For every `s_0>=0`,
  `∫_{s_0}^{s_0+r^2} L(s)^-1 ds <= 2r`,
  while `∫ L^-2 ds / r` is uniformly bounded and `∫ L^-3 ds` is uniformly bounded. These estimates make `A,C,E` uniformly bounded over all parabolic cylinders; `D=0`.

So there is **no purely functional embedding**

`I(v,q)<∞  =>  existence of a globally L^3-bounded backward time slice`

on arbitrary smooth bounded divergence-free fields. Any proof of the `H_I -> H_L3seq` bridge for mild ancient Navier–Stokes solutions must use an equation-specific ingredient (evolution, pressure relation, local energy inequality, ancient mild representation, singularity persistence, or a new rigidity mechanism), not only the definitions of the scale-invariant norms.

This calibration is a route-pruning statement, not a Navier–Stokes theorem and not a novelty claim.

## Expert-cell disposition

The six roles agree on the following partition.

1. **PDE / partial-regularity lead:** the highest-value exact bridge is `H_I -> H_L3seq` or a strictly weaker source-valid Liouville trigger; do not generalize a fixed-profile theorem.
2. **Scaling / compactness lead:** the bump-train calibration removes norm-only interpolation as a credible proof family; any surviving bridge must control spatial tail escape under the PDE.
3. **Vorticity / geometry lead:** vorticity alignment is not yet licensed as the missing property because no universal scale-invariant depletion estimate has been frozen.
4. **Adversarial falsification lead:** the next candidate must be tested against fixed, DSS, genuinely non-periodic, spatially sparse/intermittent and far-field-escaping orbit classes.
5. **Formal-methods lead:** do not encode an `I -> L3` edge as a theorem. Open a child atom whose success contract names the missing dynamics-specific tail/trace mechanism.
6. **Novelty / frontier lead:** the matrix is source normalization and route pruning; no novelty claim. Any future theorem must be searched against Type-I, ancient-solution, Lorentz/Morrey and backward-uniqueness literature before promotion.

## Selected next atom

`NS-B1a` is sharpened to:

> **Dynamics-specific Type-I trace/tail bridge.** For a mild bounded ancient 3D Navier–Stokes solution with `I<∞`, identify the weakest equation-specific inherited property that either (i) yields a backward sequence with uniformly bounded global `L^3`, activating Albritton–Barker Theorem 1.2, or (ii) activates an equally source-valid Liouville theorem without assuming fixed/DSS orbit structure.

The first child obligation is to separate **local parabolic control** from **global spatial tail tightness**. No theorem candidate for `NS-B1a` is authorized until a fresh child context, dual-memory review, expert review and hash-chained pre-candidate trace are frozen.
