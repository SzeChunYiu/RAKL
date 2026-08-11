# C023 — Hadamard extremality rules out monotone spectral-ratio lower bounds for unrestricted cover complexity

**Status:** `SOURCE_BOUND_DERIVED_ROUTE_PRUNING / EXACT_LINEAR_ALGEBRA / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`

C023 sharpens the C022 residual. C022 showed that Lokam's operator-norm lower-bound scale for depth-3 bipartite formulas cannot be transplanted directly to unrestricted cover complexity on the quadratic-residue graph. C023 proves a broader no-go statement. Any **universal lower-bound certificate depending only and monotonically on the scalar ratio `N/||A_G||`** is capped at the logarithmic scale for unrestricted cover complexity.

This is not a P-versus-NP solution, not a super-logarithmic lower bound, and not claimed to be new mathematics.

## Definition

For a non-trivial square bipartite graph `G subseteq [N] x [N]`, let `A_G` be its `+/-1` incidence matrix,

- `A_G(x,y)=+1` when `(x,y)` is an edge;
- `A_G(x,y)=-1` otherwise.

Define its scalar spectral ratio

`r(G) = N / ||A_G||`,

where `||.||` is operator norm.

## Lemma C023-L1 — universal spectral-ratio ceiling

For every `N x N` `+/-1` matrix `A`,

`N / ||A|| <= sqrt(N)`.

### Proof

The Frobenius norm satisfies

`||A||_F^2 <= rank(A) ||A||^2`.

For a `+/-1` `N x N` matrix,

`||A||_F^2 = N^2`

and `rank(A) <= N`. Therefore

`N^2 <= N ||A||^2`,

so `||A|| >= sqrt(N)` and hence `N/||A|| <= sqrt(N)`.

## Lemma C023-L2 — inner product attains the ceiling with logarithmic cover complexity

Let `N=2^t` and let

`IP_t = {(x,y) in {0,1}^t x {0,1}^t : <x,y> = 1 mod 2}`.

Its sign incidence matrix is

`A_IP(x,y) = -(-1)^{<x,y>}`,

the negative Walsh-Hadamard matrix. Orthogonality gives

`A_IP A_IP^T = N I`.

Therefore

`||A_IP|| = sqrt(N)`

and

`r(IP_t)=sqrt(N)`,

which is the maximum allowed by C023-L1.

Merged C012 gives the explicit unrestricted-cover upper bound

`rho(IP_t,G_{N,N}) <= 3t-2 = 3 log_2 N - 2`.

Thus a graph maximizing the scalar spectral ratio already has logarithmic unrestricted cover complexity.

## Proposition C023-P — monotone spectral-ratio-only lower bounds cannot prove super-log cover complexity

Fix a side size `N=2^t`. Suppose a proposed universal lower-bound rule has the form

`rho(G,G_{N,N}) >= F_N(r(G))`

for every non-trivial square bipartite graph `G`, where `F_N:[1,sqrt(N)] -> R_{>=0}` is nondecreasing.

Then for every such `G`,

`F_N(r(G)) <= 3 log_2 N - 2`.

### Proof

By C023-L1,

`r(G) <= sqrt(N)`.

Since `F_N` is nondecreasing,

`F_N(r(G)) <= F_N(sqrt(N))`.

Apply the assumed universal lower-bound rule to `IP_t`. By C023-L2,

`F_N(sqrt(N)) <= rho(IP_t,G_{N,N}) <= 3 log_2 N - 2`.

Combining the inequalities proves the proposition.

## Research consequence

The active O9d12a2a search cannot be solved by taking Lokam's scalar hardness parameter `N/||A_G||`, or any monotone reparameterization of that scalar, and proving that it lower-bounds unrestricted cover complexity. The obstruction is not merely that QR has an unexpectedly efficient construction. The **maximum possible value** of the scalar parameter is already achieved by the mod-2 inner-product graph, which has an explicit logarithmic cover construction.

This formally retires a broad class of operator-norm-only candidate invariants before more effort is spent trying to make them fusion-stable.

## Scope boundary

C023 does **not** rule out:

- spectral invariants using the full singular-value/eigenvalue profile rather than only `||A_G||`;
- a spectral quantity combined with arithmetic, communication, geometric, or semi-filter structure;
- non-monotone dependence on the scalar ratio;
- lower bounds restricted to a graph class that excludes the inner-product family for an independently justified reason;
- matrix invariants that explicitly track reuse/cyclic fusion rather than only the final sign matrix.

It also does not imply that QR has logarithmic cover complexity. C021's best registered QR upper bound remains `O(log p (log log p)^3)`.

## Counterexample-first executable check

`05_falsification/hadamard_spectral_extremal_check.py` constructs the exact sign matrix of `IP_t` for small `t` and verifies

`A_IP A_IP^T = 2^t I`.

This checks the statement binding and exact extremal Gram identity only. It does not certify C012's asymptotic cover construction or theorem authority.

## Five-role same-context research-cell review

### Complexity theory

**Vote: ACCEPT AS ROUTE PRUNING.** The proof is elementary and the conclusion is exactly scoped to universal lower bounds depending monotonically only on `N/||A_G||`. It is stronger than re-running the QR-specific contradiction because it uses an extremal spectral graph with an already merged logarithmic cover construction.

### Meta-complexity

**Vote: ACCEPT WITH ROOT SCOPE ZERO.** This narrows the unrestricted-circuit route but has no MCSP magnification consequence and supplies no root lower bound.

### Adversarial proof review

**Vote: ACCEPT AFTER SCOPE RESTRICTION.** The monotonicity and scalar-only hypotheses are load-bearing. Dropping either invalidates the no-go. In particular, C023 must not be paraphrased as saying that all spectral methods fail.

### Formal methods

**Vote: REVISE BEFORE VERIFIED_LEMMA.** The Gram identity has an exact finite checker, but there is no theorem-prover artifact, dependency/axiom receipt, or isolated kernel recheck. The Frobenius inequality and the C012 dependency remain paper-level proof edges.

### Novelty and research value

**Vote: ACCEPT ONLY WITH `NO_NOVELTY_CLAIM`.** The mathematics is a short synthesis of standard matrix norm inequalities and the merged C012 construction. Its value is search-space reduction. A dedicated prior-art search would be required before any standalone novelty claim.

This review is same-context and is **not independent review**.

## Typed residuals

1. **O9d12a2a1 — non-scalar reuse-stable invariant.** Search for an invariant that incorporates more than the top singular value and has an explicit per-fusion budget.
2. **O9d12a2a2 — structure-conditioned spectral invariant.** If spectrum is retained, state the extra structural condition that excludes the inner-product counterexample and prove that the condition itself survives/restricts cyclic fusion.
3. **O9d12a1 — QR upper-bound attack remains active.** Independently try to remove C021's `(log log p)^3` factor.

## Promotion blockers

- no theorem-prover artifact;
- no isolated proof recheck;
- no bounded novelty certificate;
- no genuinely independent reviews;
- root impact is route pruning only.

Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.