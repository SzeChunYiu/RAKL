# Yang–Mills root problem contract

**Authority:** official Clay/Jaffe–Witten statement binding  
**Control issue:** #85  
**Root status:** `OPEN_NO_SOLUTION_CERTIFICATE`

## Informal target

For every compact simple gauge group `G`, establish a nontrivial quantum Yang–Mills theory on four-dimensional Euclidean/Minkowski spacetime with mathematical axioms at least as strong as those required by the official Jaffe–Witten description, and prove a finite positive mass gap `Δ>0` above the vacuum.

Official source:

- Arthur Jaffe and Edward Witten, *Quantum Yang–Mills Theory*, Clay Mathematics Institute: `https://www.claymath.org/wp-content/uploads/2022/06/yangmills.pdf`

## Root success contract

A root candidate must simultaneously bind and close:

1. **Gauge-group scope.** The quantifiers match the official compact-simple-group statement.
2. **Continuum existence.** The construction is genuinely four-dimensional continuum QFT, not only a fixed lattice/cutoff model.
3. **Nontriviality.** The limiting theory is not a free/trivial theory obtained by an uncontrolled limit.
4. **Axiomatic QFT.** The exact Wightman/OS-strength properties, locality/positivity/covariance, and reconstruction dependencies used by the claim are explicit.
5. **Ultraviolet behavior.** The construction is compatible with the short-distance asymptotic-freedom/renormalization requirements in the official problem description.
6. **Physical Hilbert space.** Gauge constraints/quotients and the vacuum sector are explicitly identified.
7. **Mass gap.** The reconstructed Hamiltonian has vacuum at zero and no spectrum in `(0,Δ)` for some finite `Δ>0`.
8. **Limit uniformity.** Any lattice/finite-volume route controls the thermodynamic and continuum limits in the exact physical units needed by the gap claim.
9. **Proof closure.** Every proof-critical dependency is closed, with no hidden numerical leap, unregistered axiom, conjectural bridge, or unchecked interchange of limits.
10. **Assurance.** Formal/verifier/dependency/axiom audits, isolated recheck where supported, bounded novelty search, and three genuinely isolated mathematical reviews pass.

No one item compensates for another.

## Explicit non-solutions

The following can be important intermediate results but are not root certificates by themselves:

- a positive transfer matrix at fixed lattice spacing;
- a Poincaré/log-Sobolev gap for a Langevin/Markov generator;
- exponential decay for a restricted observable class without spectral-completeness proof;
- Wilson-loop area law or confinement in an extended/center-sensitive sector;
- a strong-coupling mass/correlation gap at fixed cutoff;
- ultraviolet RG/asymptotic-freedom control without infrared mass generation;
- numerical continuum extrapolation of glueball masses;
- a continuum mass-gap argument without a constructed nontrivial QFT satisfying the required axioms.

## Spectral-lane unit invariant

If the exact lattice construction yields a one-step transfer matrix with the convention `T_a = exp(-a H_a)`, then the physical excitation energy associated with an eigenvalue ratio is

`E_1-E_0 = -a^{-1} log(lambda_1/lambda_0)`.

This formula is **not** assumed globally until the chosen transfer-matrix convention, Euclidean time step, Hilbert space, and normalization are bound. Its role is to prevent a dimensional mistake: a finite positive physical continuum gap normally corresponds to a dimensionless one-step exponent of order `a`, not to an `a`-independent dimensionless lower bound.
