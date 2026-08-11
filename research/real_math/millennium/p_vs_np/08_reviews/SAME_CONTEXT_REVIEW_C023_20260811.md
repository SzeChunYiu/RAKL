# Same-context five-role review — C023

**Independence status:** `SAME_CONTEXT_ONLY`. This document is an internal adversarial research-cell review. It is not independent peer review and does not satisfy the three-isolated-review gate.

## Frozen claim under review

For `N=2^t`, define `r(G)=N/||A_G||` for the `+/-1` incidence matrix of a square bipartite graph. If a universal unrestricted-cover lower-bound rule has the form

`rho(G)>=F_N(r(G))`

with `F_N` nondecreasing, then that rule cannot certify more than

`3 log_2 N - 2`

for any graph. The reason is that `r(G)<=sqrt(N)` universally, while the mod-2 inner-product graph attains `sqrt(N)` and merged C012 gives it cover complexity at most `3 log_2 N-2`.

## Complexity-theory lens

**Vote: ACCEPT_ROUTE_PRUNING.** The proof is short and exact. It turns C022's QR-specific warning into a universal obstruction for monotone top-singular-value-only lower-bound templates.

**Concern CT-M1:** The claim must remain about `N/||A||` as a scalar. It does not rule out full-spectrum, tensor, communication, arithmetic, or semi-filter invariants.

**Resolution test:** keep every route consequence explicitly conditioned on scalar-only monotone dependence.

## Meta-complexity lens

**Vote: ACCEPT_ROOT_SCOPE_ZERO.** C023 improves search efficiency in the unrestricted-circuit lane but supplies no MCSP threshold transport and no P-versus-NP implication by itself.

**Strongest counter-hypothesis:** a useful invariant may combine spectrum with a structural promise and therefore survive C023.

**Attempted falsifier:** inner product was selected precisely because it maximizes the spectral ratio while remaining cover-easy. This kills the unconditioned scalar template but not structure-conditioned variants.

## Adversarial proof-review lens

**Vote: ACCEPT_AFTER_SCOPE_RESTRICTION.** The load-bearing steps are:

1. `||A||_F^2<=rank(A)||A||^2`;
2. every sign matrix has `||A||_F^2=N^2` and rank at most `N`;
3. the odd-inner-product sign matrix is negative Walsh-Hadamard, so its Gram matrix is `NI`;
4. C012 supplies the exact `3t-2` cover upper bound;
5. monotonicity of `F_N` is essential.

No hidden asymptotic limit or random-matrix claim is required.

**Blocking concern for stronger wording:** a non-monotone function of the scalar ratio is not excluded. Neither is a lower bound defined only on a restricted graph class.

## Formal-methods lens

**Vote: REVISE_BEFORE_VERIFIED_LEMMA.** The finite checker exactly verifies the Walsh-Hadamard Gram identity on bounded widths and the sign convention. It does not formalize the Frobenius/rank inequality, C012, or the universal quantifier over all graphs.

**Resolution test:** formalize the linear-algebra lemma and import or reprove C012 in the same proof environment before promoting beyond source-bound proof draft.

## Novelty/research-value lens

**Vote: ACCEPT_NO_NOVELTY_CLAIM.** The components are elementary or previously merged. The potentially useful contribution is the explicit no-go formulation for this new 2025 cover-complexity research route. A bounded prior-art search is still required before any novelty claim.

**Research value:** high as a cheap route filter. Any future proposal whose only hardness coordinate is top spectral norm should be rejected immediately unless it names and proves an additional fusion-relevant structural condition.

# Synthesis

All five roles accept C023 as bounded route pruning. No role supports theorem-authority or novelty promotion. The main residual is not to improve the top-singular-value calculation, but to invent a non-scalar or structure-sensitive invariant with a proved per-fusion budget.

Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.
