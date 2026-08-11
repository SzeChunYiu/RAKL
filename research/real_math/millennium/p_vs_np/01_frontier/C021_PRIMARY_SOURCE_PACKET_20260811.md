# C021 primary-source packet — 2026-08-11

**Authority:** source-binding packet only. No novelty or root-solution authority.

## Source S1 — cover/intersection complexity

Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 / arXiv:2503.14117 / ACM TOCT 17(2), 2025, DOI `10.1145/3718746`.

Source-level facts used:

- graph intersection complexity counts pairwise intersections while unions of row/column generators are free;
- cover complexity satisfies `rho(A,B) <= D_intersection(A|B)`;
- Boolean circuit complexity is represented in the same discrete-complexity language from literals and their complements.

C021 additionally uses the already-recorded C020 dual-rail compilation from bounded-fanin Boolean gates to set unions/intersections, with both row/column bit polarities available as free unions of stars.

## Source S2 — fast Jacobi symbol

Richard P. Brent and Paul Zimmermann, *An O(M(n) log n) Algorithm for the Jacobi Symbol*, ANTS IX 2010, arXiv:1004.2091, DOI `10.1007/978-3-642-14518-6_10`.

The paper gives a deterministic algorithm computing the Jacobi symbol of `n`-bit integers in time `O(M(n) log n)`, where `M(n)` is the time for `n`-bit integer multiplication.

## Source S3 — integer multiplication

David Harvey and Joris van der Hoeven, *Integer multiplication in time O(n log n)*, Annals of Mathematics 193(2), 2021, 563–617, DOI `10.4007/annals.2021.193.2.4`.

Their main theorem gives `M(n)=O(n log n)` bit operations in the fixed-multitape Turing-machine model with binary input representation.

Combining S2 and S3 yields a Jacobi-symbol machine-time upper bound `T_J(n)=O(n log^2 n)` under the aligned standard bit/Turing model used in C021.

## Source S4 — machine-to-network simulation

Nicholas Pippenger and Michael J. Fischer, *Relations Among Complexity Measures*, JACM 26(2), 1979, 361–381, DOI `10.1145/322123.322138`.

Their simulation result states that `T` steps of an arbitrary machine with one-dimensional tapes can be performed by a combinational logic network of cost `O(T log T)` and delay `O(T)`.

Applied to `T_J(n)=O(n log^2 n)`, this gives a Boolean network of size `O(n log^3 n)`. A fixed bounded-fanin network basis can be translated to De Morgan gates with constant-factor overhead.

## Model-alignment boundary

C021 is deliberately a proof draft because the following source interfaces are not yet formalized in a proof assistant:

1. the precise fixed-multitape machine convention connecting S2's `M(n)` notation to S3;
2. the exact combinational-network gate basis in S4 and its constant-overhead translation to the De Morgan basis used by the set compiler;
3. the binding from the resulting Boolean circuit on valid binary row/column labels to the `[p] x [p]` graph construction.

These are ordinary complexity-theory interfaces, but they remain explicit promotion blockers until formalized or independently proof-checked.
