# H4d1 source/context packet — deformation lifting from Hodge locus to algebraic cycles

Date frozen: 2026-08-11
Base `main`: `539487f52126c21f6cb80c6127f4bdf67fae27c2`
Persistent root control: GitHub issue #86.

## Exact root boundary

The root target is the rational Hodge conjecture for smooth projective complex algebraic varieties: a rational class of Hodge type `(p,p)` in `H^{2p}(X,Q)` should be a rational linear combination of codimension-`p` algebraic cycle classes.

This packet does **not** replace the root by the integral Hodge conjecture, generalized Hodge conjecture, Tate conjecture, a standard conjecture, a variational statement, or a statement only for a restricted family.

## Selected atom H4d1

Let `f: X -> S` be a smooth projective family of complex algebraic varieties, let `s0 in S`, and let `alpha` be a locally flat rational cohomology class that is algebraic on `X_{s0}`. Let `T` be an irreducible component (or a local irreducible branch) of the locus on which the parallel transport of `alpha` remains of Hodge type `(p,p)`.

The atom is **not** to invent a lifting theorem yet. It is to identify the smallest checkable condition under which the class-constrained algebraic-cycle realization space has a component dominating `T`, while distinguishing:

1. the Hodge condition on the transported cohomology class;
2. existence of an algebraic cycle realizing that class on each fiber;
3. deformation of a chosen cycle/witness;
4. rational linear combinations versus one effective Hilbert/Chow point;
5. formal deformation versus algebraization/globalization.

This is the cycle-witness lifting gap inside root atom `H4`.

## Primary/authoritative source findings

### S1 — official root scope

Pierre Deligne's official Clay problem description states the rational cycle-class target for smooth projective complex varieties. The divisor (`p=1`) case is classical via Lefschetz `(1,1)`; the general problem is open.

Anchors:
- https://www.claymath.org/millennium/hodge-conjecture/
- https://publications.ias.edu/deligne/paper/437

### S2 — Hodge-locus algebraicity is a base-locus theorem, not a cycle-production theorem

Cattani–Deligne–Kaplan prove that, in a smooth projective family, the locus where a fixed integral class remains of Hodge type is algebraic. This is a crucial solved analogue for the **base geometry** of `T`, but it does not construct an algebraic cycle representing the class.

Anchors:
- https://arxiv.org/abs/alg-geom/9402009
- https://publications.ias.edu/node/416

### S3 — the Hodge locus can have rich distribution without solving witness lifting

Baldi–Klingler–Ullmo study the distribution of Hodge loci in polarizable integral variations and obtain strong algebraicity/finiteness results in parts of the high-level regime, while also exhibiting dense behavior in low-level regimes under their hypotheses. This strengthens the warning that geometry of the Hodge locus itself is not synonymous with algebraic-cycle realization.

Anchors:
- https://arxiv.org/abs/2107.08838
- Inventiones Mathematicae 235 (2024), 441–487.

### S4 — semiregularity is a genuine local bridge in special deformation problems

Buchweitz–Flenner construct a generalized semiregularity map and explain consequences for deformation theory and the variational Hodge conjecture. Nishinou proves a relative deformation criterion for semiregular maps whose images are divisors: under the stated hypotheses, relative deformation is equivalent to persistence of the Hodge condition. These are solved/near-solved contexts in which an obstruction-theoretic bridge from cohomology to geometry can be made precise.

Anchors:
- https://arxiv.org/abs/math/9912245
- https://arxiv.org/abs/2009.01651

### S5 — formal cycle-class deformation can be controlled under additional structure

Bloch–Esnault–Kerz study a formal deformation problem for rational algebraic cycle classes in characteristic zero motivated by Grothendieck's variational Hodge conjecture; they relate expected deformations to Chow–Künneth structure and obtain applications including abelian schemes. This is a near-solved context, but formal pro-classes and structural hypotheses cannot be silently promoted to an actual global relative cycle dominating an arbitrary Hodge-locus component.

Anchor:
- https://arxiv.org/abs/1310.1773

## Structural separation learned this cycle

The strongest verified information gain is a **four-layer separation**:

`Hodge-locus membership -> infinitesimal/formal witness lift -> algebraization of the witness -> domination/global continuation over T`.

Known theorems address different arrows. Collapsing them into one statement is a recurrent route-risk.

## Authority

`SOURCE_BOUND_CONTEXT_ONLY / STRICT_PRE_CANDIDATE / NO_MATHEMATICAL_CANDIDATE / ROOT_AUTHORITY_NONE`.

The next action is a falsifier/calibration program for the lifting criterion space, not a theorem claim.
