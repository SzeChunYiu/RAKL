# Canonical problem statement — Navier–Stokes existence and smoothness

Authority source: Charles L. Fefferman, *Existence and Smoothness of the Navier–Stokes Equation*, official Clay Mathematics Institute Millennium problem description.

For incompressible flow with viscosity `nu > 0`, velocity `u : R^3 x [0,∞) -> R^3` and pressure `p`, the equations are

`∂_t u + (u·∇)u = nu Δu - ∇p + f`,  
`∇·u = 0`,  
`u(x,0)=u0(x)`.

The official problem allows a proof of any one of four statements:

- **(A) R^3 existence and smoothness:** every smooth divergence-free rapidly decaying `u0`, with `f=0`, has a global smooth bounded-energy solution.
- **(B) periodic existence and smoothness:** every smooth divergence-free periodic `u0`, with `f=0`, has a global smooth periodic solution.
- **(C) R^3 breakdown:** there exist smooth divergence-free rapidly decaying `u0` and smooth rapidly decaying forcing `f` for which no global smooth bounded-energy solution exists.
- **(D) periodic breakdown:** there exist smooth periodic divergence-free `u0` and smooth periodic forcing `f` for which no global smooth periodic solution exists.

This RAKL lane initially pursues positive regularity routes toward (A)/(B). It must not redefine the root problem as weak-solution uniqueness, a conditional regularity criterion, exclusion of one blowup scenario, or numerical evidence.

## Scaling contract

For the unforced equation, if `u` is a solution then

`u_lambda(x,t)=lambda u(lambda x, lambda^2 t)`,  
`p_lambda(x,t)=lambda^2 p(lambda x, lambda^2 t)`.

Thus `||u||_{L_t^p L_x^q}` is scale invariant when `2/p + 3/q = 1`. The Leray energy class `L_t^∞L_x^2 ∩ L_t^2 dot H_x^1` lies at `2/p+3/q=3/2`, hence is supercritical.

## Root authority

Status: `OPEN_NO_SOLUTION_CERTIFICATE`.

A root promotion requires exact statement binding, closed proof DAG, dependency and axiom audit, formal/verifier evidence where supported, isolated recheck, bounded novelty search, and three genuinely isolated mathematical reviews.
