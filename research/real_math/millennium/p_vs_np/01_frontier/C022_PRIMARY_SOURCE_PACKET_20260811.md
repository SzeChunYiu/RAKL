# C022 primary-source packet — 2026-08-11

**Authority:** literature/source binding only. No novelty or root-solution authority.

## S1 — Lokam 2003, restricted graph-formula lower bounds

Satyanarayana V. Lokam, *Graph Complexity and Slice Functions*, Theory of Computing Systems 36(1), 71–88 (2003), DOI `10.1007/s00224-002-1068-0`.

Institutional record: University of Michigan Deep Blue handle `2027.42/42364` (record lists the deposited PDF `30360071.pdf`).

Technical source facts used by C022:

- Section 2 defines bipartite-formula complexity using complete bipartite row/column generators and union/intersection.
- Section 4 studies depth-3 bipartite formulas.
- Theorem 4.7 lower-bounds depth-3 bipartite-formula size for an `N x N` graph `G` in terms of the operator norm of its `+/-1` incidence matrix `A_G`:

  `Omega(log^3(N/||A_G||) / loglog^5(N/||A_G||))`.

- Corollary 4.8 specializes this to Hadamard-incidence graphs and notes Paley-type bipartite graphs as examples, giving `Omega((log N)^3/(loglog N)^5)`.

The article's proof uses sign-representing matrices and Forster's rank bound. C022 does not reproduce or strengthen that source theorem; it derives the exact operator norm needed to apply Theorem 4.7 directly to the repository's already frozen `QR_p` graph.

## S2 — Cavalar–Oliveira 2025, unrestricted intersection/cover complexity

Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ACM Transactions on Computation Theory 17(2), 2025, DOI `10.1145/3718746`; ECCC TR25-033; arXiv `2503.14117`.

Source-level facts already bound in the R004 ledger and reused here:

- graph intersection complexity permits reuse through an unrestricted construction DAG while charging intersections and treating unions according to the discrete-complexity model;
- cover complexity satisfies `rho(A,B) <= D_intersection(A|B) <= rho(A,B)^2`;
- cover complexity has an exact characterization through cyclic discrete constructions, making cycles/reuse part of the relevant unrestricted obstruction;
- explicit super-logarithmic graph-cover lower bounds would transfer to improved Boolean circuit lower bounds.

## S3 — merged C021 source chain

C021, already present on main before C022, source-binds an unrestricted upper construction for the exact graph

`QR_p={(x,y): y-x is a nonzero quadratic residue mod p}`

and derives

`D_intersection(QR_p | G_{p,p}) = O(log p * (log log p)^3)`.

Its external chain is Brent–Zimmermann 2010 (Jacobi), Harvey–van der Hoeven 2021 (integer multiplication), Pippenger–Fischer 1979 (machine-to-network simulation), and Cavalar–Oliveira 2025 (graph intersection/fusion). C022 does not alter those dependencies or their proof-draft model-alignment blockers.

## Derived mathematics in C022

The exact spectral calculation for the repository's `QR_p` matrix is proved inside C022 rather than imported from a secondary source. It uses only elementary quadratic-character correlation:

- `A_p=C_p-I`, with `C_p(x,y)=chi(y-x)`;
- `C_p C_p^T=pI-J`;
- `C_p^T=chi(-1)C_p`;
- therefore `||A_p||=sqrt(p+1)` for `p=3 mod 4`, and `||A_p||=sqrt(p)+1` for `p=1 mod 4`.

A finite exact regression script checks the Gram-matrix identities for small primes. Those checks are specification/calibration evidence only.

## Source-bound conclusion

Lokam's depth-3 lower bound applies to the exact C019–C021 graph once the derived norm bound is inserted. This yields a restricted-model lower bound

`L3_B(QR_p)=Omega((log p)^3/(loglog p)^5)`

while C021 gives an unrestricted intersection upper bound only a polylog-log factor above `log p`.

The resulting asymptotic model gap is route information, not a lower bound on cover complexity and not a new-mathematics claim.