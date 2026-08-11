# C022 — the quadratic-residue graph is depth-3 hard but unrestricted-intersection easy

**Status:** `SOURCE_BOUND_DERIVED_ROUTE_PRUNING / EXACT_SPECTRAL_LEMMA / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`

C022 is a model-separation checkpoint for the R004 graph-cover lane. It is not a P-versus-NP solution and is not claimed to be new mathematics.

## Frozen graph

For every odd prime `p`, let

`QR_p = {(x,y) in Z_p x Z_p : y-x is a nonzero quadratic residue mod p}`.

This is exactly the graph used by C019–C021. Let `A_p` be its `+/-1` incidence matrix:

- `A_p(x,y)=+1` on an edge of `QR_p`;
- `A_p(x,y)=-1` on a non-edge, including `x=y`.

Let `L3_B(QR_p)` be Lokam's depth-3 bipartite-formula complexity with complete bipartite row/column generators and union/intersection operations.

## C022-L1 — exact operator norm of the QR sign matrix

Let `chi` be the quadratic character on `F_p`, extended by `chi(0)=0`, and let

`C_p(x,y)=chi(y-x)`.

Then

`A_p = C_p - I`.

The character-correlation identity gives

`C_p C_p^T = p I - J`,

where `J` is the all-ones matrix. Also

`C_p^T = chi(-1) C_p`.

Therefore:

- if `p == 3 mod 4`, then `chi(-1)=-1` and
  `A_p A_p^T = (p+1)I-J`, so `||A_p|| = sqrt(p+1)`;
- if `p == 1 mod 4`, then `chi(-1)=+1`, `C_p` is symmetric, is zero on the all-ones vector, and has eigenvalues `+sqrt(p)` or `-sqrt(p)` on its orthogonal complement. Hence `A_p=C_p-I` has operator norm `sqrt(p)+1`.

Thus in every case

`||A_p|| <= sqrt(p)+1`.

### Self-contained proof of the correlation identity

For distinct `a,b`, translation and nonzero scaling reduce

`sum_y chi(y-a)chi(y-b)`

to

`S = sum_t chi(t(t-1))`.

Count pairs `(t,z)` satisfying `z^2=t(t-1)`. The number of `z` for each `t` is `1+chi(t(t-1))`, so the total is `p+S`.

After the invertible change `u=2t-1`, `v=2z`, the equation becomes

`u^2-v^2=1`, equivalently `(u-v)(u+v)=1`.

For each nonzero `r in F_p`, there is exactly one solution

`u-v=r`, `u+v=r^(-1)`.

Hence there are `p-1` pairs, so `p+S=p-1` and `S=-1`. The diagonal correlation is `p-1`. This proves `C_p C_p^T=pI-J`.

## C022-L2 — Lokam's depth-3 lower bound applies to this exact QR graph

Lokam's Theorem 4.7 states that for an `N x N` bipartite graph `G` with `+/-1` incidence matrix `A_G`, every depth-3 bipartite formula has size at least

`Omega( log^3(N/||A_G||) / loglog^5(N/||A_G||) )`.

Applying C022-L1 with `N=p` gives

`p / ||A_p|| = Omega(sqrt(p))`.

Therefore

`L3_B(QR_p) = Omega( (log p)^3 / (log log p)^5 )`.

This binds the classical spectral/sign-rank lower-bound mechanism to the exact C019–C021 quadratic-residue relation. It does not rely on identifying `QR_p` with an unspecified sibling called merely "Paley-type".

## C022-L3 — explicit asymptotic depth/reuse separation

C021 gives the proof-draft unrestricted intersection upper bound

`D_intersection(QR_p | G_{p,p}) = O(log p * (log log p)^3)`.

Cavalar–Oliveira give

`rho(QR_p,G_{p,p}) <= D_intersection(QR_p | G_{p,p})`.

Combining with C022-L2 yields the model-separation inequality

`L3_B(QR_p) / D_intersection(QR_p) = Omega( (log p)^2 / (log log p)^8 )`,

up to the source/model-alignment qualifications already frozen in C021. The same lower ratio holds with `rho` in the denominator whenever the nontrivial cover complexity is positive, because `rho <= D_intersection`.

The ratio tends to infinity.

## Research consequence

The Paley/quadratic-residue family is not merely a candidate with attractive pseudorandom spectral structure. Its spectral structure already supports a super-logarithmic lower bound in a restricted graph-formula model, while the same exact relation admits a near-log unrestricted intersection construction.

Therefore the active obstruction is now sharper:

> identify an invariant that survives unrestricted reuse/cyclic fusion, rather than reusing a depth-3 formula invariant whose strength is demonstrably lost when depth and reuse are released.

In particular, operator norm / sign-rank arguments cannot simply be transferred at the Lokam depth-3 scale to `rho`, because C021 supplies a strictly smaller asymptotic upper bound for the same graph.

## What this does not prove

C022 does not lower-bound `rho(QR_p)` above the logarithmic baseline. It does not lower-bound unrestricted Boolean circuit size. It does not establish that the remaining C021 upper bound is tight. It does not prove that no spectral information can ever contribute to a cover lower bound; only a scale-preserving direct transfer of the existing depth-3 argument is ruled out by the explicit upper bound.

## Next residuals

1. **O9d12a2a — reuse-stable invariant.** Find a preserving-semi-filter or cyclic-construction invariant that is monotone under the exact fusion operations and is not annihilated by unrestricted reuse.
2. **O9d12a1 — upper-bound sharpening remains active.** Independently try to reduce C021's `O(log p (log log p)^3)` upper bound to `O(log p)`.
3. **O9d12a2b — depth reduction discriminator.** Determine whether a small cover/cyclic construction for `QR_p` can be transformed into a restricted formula under any additional structural hypothesis strong enough for Lokam's bound to become informative.

## Assurance boundary

- C022-L1 is a self-contained proof draft with finite exact regression checks.
- C022-L2 is source-bound to Lokam 2003, Theorem 4.7.
- C022-L3 also depends on the already merged C021 source/model chain and Cavalar–Oliveira's fusion inequalities.
- No theorem-prover artifact, isolated proof recheck, bounded novelty certificate, or genuinely independent review exists.
- The five-role review in this increment is same-context only.

Root status remains `OPEN_NO_SOLUTION_CERTIFICATE`.