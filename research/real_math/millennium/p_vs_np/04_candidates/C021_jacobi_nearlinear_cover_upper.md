# C021 — Jacobi algorithms give a near-linear-log full-cover upper bound for quadratic-residue graphs

**Status:** `PROOF_DRAFT / NEARLINEAR_LOG_FULL_COVER_UPPER_BOUND / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`

C021 sharpens C020. It is an upper-bound/route-pruning result and is not a P-versus-NP solution.

## Statement

For every odd prime `p`, let `n=ceil(log2 p)` and

`QR_p = {(x,y) in Z_p x Z_p : y-x is a nonzero quadratic residue mod p}`.

Then

`D_intersection(QR_p | G_{p,p}) = O(n log^3 n)`

and hence

`rho(QR_p,G_{p,p}) = O(n log^3 n)`.

Equivalently,

`rho(QR_p,G_{p,p}) = O(log p * (log log p)^3)`.

All logarithm bases are immaterial to the asymptotic statement.

## Lemma C021-L1 — adjacency is a Jacobi predicate

For an odd prime `p` and `d in Z_p`, the Jacobi symbol `(d|p)` equals the Legendre symbol. It is `0` exactly for `d=0`; for nonzero `d`, it is `+1` exactly when `d` is a quadratic residue modulo `p`.

Therefore, with

`d = y-x mod p`,

we have

`(x,y) in QR_p  iff  Jacobi(d,p)=+1`.

Computing `d` from the valid `n`-bit row/column labels costs `O(n)` ordinary bounded-fanin Boolean gates by the elementary ripple-carry modular subtraction already used in C020.

## Lemma C021-L2 — Jacobi has machine time O(n log^2 n)

Brent and Zimmermann give a deterministic Jacobi-symbol algorithm with running time

`O(M(n) log n)`,

where `M(n)` is the time to multiply two `n`-bit integers.

Harvey and van der Hoeven prove

`M(n)=O(n log n)`

in the fixed-multitape Turing-machine bit model.

Substitution yields

`T_J(n)=O(n log^2 n)`.

This source interface is retained as an explicit model-alignment dependency rather than silently treated as a formal theorem inside RAKL.

## Lemma C021-L3 — Jacobi has Boolean network size O(n log^3 n)

Pippenger and Fischer prove that `T` steps of an arbitrary machine with one-dimensional tapes can be performed by a combinational logic network of cost

`O(T log T)`.

Applying this to `T=T_J(n)=O(n log^2 n)` gives network cost

`O(n log^2 n * log(n log^2 n)) = O(n log^3 n)`.

The network uses a fixed finite bounded-fanin Boolean basis. Every fixed bounded-fanin Boolean gate can be replaced by a constant-size De Morgan subcircuit. Therefore there is a De Morgan circuit of size

`O(n log^3 n)`

for the predicate `Jacobi(d,p)=+1` on the valid labels.

## Lemma C021-L4 — Boolean network to graph intersection construction

Inside the ambient space `[p] x [p]`, each predicate asserting a particular row-label bit or its complement is a union of row stars. Each column-label bit or its complement is a union of column stars. Since graph intersection complexity counts intersections and unions are free, all input literal rails cost zero intersections.

Use the C020 dual-rail compilation. For every Boolean wire maintain both its positive and negative set-valued rail.

- `AND` uses one intersection for the positive rail and a union for the negative rail.
- `OR` uses a union for the positive rail and one intersection for the negative rail.
- `NOT` swaps rails.

Thus a De Morgan circuit of size `s` compiles to a graph construction using `O(s)` intersections. Applying C021-L3 yields

`D_intersection(QR_p | G_{p,p}) = O(n log^3 n)`.

Cavalar–Oliveira's fusion inequality

`rho <= D_intersection`

then gives the claimed cover upper bound.

## Non-power-of-two boundary

No padded vertices are introduced. The ambient graph contains only rows and columns labelled by integers `0,...,p-1`. The bit-predicate generator unions are taken only over these valid rows/columns. The Boolean network is therefore evaluated only on valid label pairs. C021 makes no claim about padded labels in `{0,1}^n` outside this range.

## Counterexample-first check

`05_falsification/jacobi_cover_spec.py` implements a simple specification-level Jacobi algorithm and exhaustively checks, for small odd primes, that

`Jacobi((y-x) mod p,p)=+1`

matches direct nonzero quadratic-residue membership. This checks the statement binding and zero-difference boundary only. It does not validate the fast asymptotic algorithm or prove an asymptotic circuit upper bound.

## What C021 buys

C020 gave a cubic-log upper envelope using Euler exponentiation. C021 reduces that to

`O(log p * (log log p)^3)`.

Hence full GF(2) rank, density, distinct rows/columns, and linear arboricity coexist with a cover construction that is only a polylog-log factor above the logarithmic scale targeted by R004.

## What C021 does not buy

C021 does not prove `rho(QR_p)=O(log p)`. Therefore it does not refute the possibility that the family has super-logarithmic cover complexity.

It also gives no lower bound for unrestricted Boolean circuits. The root P-versus-NP problem receives no theorem authority from this upper bound.

## Generic explicitness screen

The proof exposes a reusable route constraint.

If a bipartite graph family on `N x N` vertices has an adjacency predicate computable by De Morgan circuits of size `s(log N)`, then the same bit-predicate/dual-rail construction yields

`rho(G_N) <= D_intersection(G_N) = O(s(log N))`.

In particular, an adjacency family with `O(log N)` Boolean circuits is automatically disqualified as a super-log cover target. Future R004 candidate screening must record the adjacency-circuit upper bound before investing in cover lower-bound invariants.

## Promotion blockers

- exact source-model alignment has not been formalized;
- bounded-fanin network to De Morgan translation is not proof-assistant checked;
- no formalization witness, proof receipt, dependency/axiom audit, or isolated kernel recheck exists;
- no bounded novelty certificate exists;
- no genuinely independent reviewer reports exist.

Authority remains `PROOF_DRAFT`.
