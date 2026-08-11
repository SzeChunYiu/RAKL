# C023 primary-source packet — 2026-08-11

**Authority:** source binding and model alignment only. No novelty or root-solution authority.

## S1 — Lokam 2003, spectral-ratio lower bounds in a restricted graph-formula model

Satyanarayana V. Lokam, *Graph Complexity and Slice Functions*, Theory of Computing Systems 36(1), 71–88 (2003), DOI `10.1007/s00224-002-1068-0`.

Load-bearing source fact already bound by C022. Theorem 4.7 lower-bounds depth-3 bipartite-formula size using the monotone spectral ratio

`N / ||A_G||`,

where `A_G` is the `+/-1` incidence matrix. The source obtains the Paley/Hadamard lower-bound scale from large values of this ratio.

C023 does **not** challenge Lokam's restricted-model theorem. It asks whether any universal lower-bound rule for unrestricted cover complexity can depend only and monotonically on the same scalar spectral ratio.

## S2 — Cavalar–Oliveira 2025, unrestricted cover/intersection complexity

Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 / ACM Transactions on Computation Theory 17(2), Article 13 (2025), DOI `10.1145/3718746`.

Relevant source facts:

- cover complexity `rho(G,G_{N,N})` is the unrestricted fusion/cyclic object used by R004;
- `rho <= D_intersection`;
- cover complexity has an exact characterization by cyclic intersection constructions;
- explicit super-logarithmic cover lower bounds would transfer to improved unrestricted Boolean circuit lower bounds.

The source also stresses that unrestricted graph/circuit lower bounds must accommodate reuse/cyclic behavior that is absent from formula-only arguments.

## S3 — merged C012 inner-product upper construction

C012 is already on `main` and is source-derived from Cavalar–Oliveira. For the mod-2 inner-product graph on side size `N=2^t`,

`IP_t = {(x,y) : <x,y> = 1 mod 2}`,

it constructs

`rho(IP_t,G_{N,N}) <= 3t-2 = 3 log_2 N - 2`.

C023 reuses this exact registered upper bound. It does not strengthen C012.

## Elementary matrix facts used by C023

For any real `N x N` matrix `A`,

`||A||_F^2 <= rank(A) ||A||^2 <= N ||A||^2`.

For a `+/-1` matrix, `||A||_F=N`, hence

`||A|| >= sqrt(N)`

and therefore

`N/||A|| <= sqrt(N)`.

For the inner-product graph, its `+/-1` incidence matrix is the negative Walsh-Hadamard matrix. Orthogonality gives

`A_IP A_IP^T = N I`,

so `||A_IP||=sqrt(N)` and the spectral ratio attains the universal maximum `sqrt(N)`.

These facts are proved directly in C023 and checked exactly on small Walsh matrices. They do not require an asymptotic external theorem.

## Source-bound conclusion

Lokam's spectral ratio is powerful for the restricted depth-3 formula model, but the same scalar cannot serve as a monotone universal lower-bound parameter for unrestricted cover complexity. The graph maximizing the ratio already has an `O(log N)` cover construction by C012.

This is route-pruning information only. It does not rule out spectral methods using additional matrix information, non-monotone dependence on the ratio, restrictions to a narrower graph class, or invariants that combine spectrum with reuse-sensitive structure.