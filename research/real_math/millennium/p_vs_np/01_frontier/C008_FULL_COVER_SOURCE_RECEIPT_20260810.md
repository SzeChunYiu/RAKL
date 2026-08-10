# C008 primary-source receipt — full graph cover complexity

**Cutoff:** 2026-08-10
**Authority:** SOURCE BINDING ONLY

## Primary source

Bruno Pasqualotto Cavalar and Igor Carboni Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, Electronic Colloquium on Computational Complexity, Report TR25-033, 2025.

## Definitions bound for C008

C008 uses the source's graph-complexity specialization of the fusion/cover framework.

- A semi-filter is a nonempty upward-closed family `F subseteq 2^U` with `emptyset notin F`.
- For a subset problem `A subseteq B`, a semi-filter is above `w in A` when every `b in B` containing `w` has `b intersect U` in `F`, where `U=B\A`. In the bipartite graph specialization, the row and column complement fibres of a graph edge are required members.
- `F` preserves a pair `(E,H)` when `E,H in F` implies `E intersect H in F`.
- Cover complexity `rho(A,B)` is the minimum number of pairs for which no semi-filter above an element of `A` preserves all pairs.

The source specializes this to bipartite graph cover complexity and proves

`rho(G,G_{N,N}) <= D_cap(G | G_{N,N})`,

so full cover lower bounds can lower-bound graph intersection complexity.

## Canonical comparison

The source also defines canonical semi-filters for bipartite graphs and uses canonical cover complexity as a lower bound on full graph cover complexity. For the explicit calibration graph

`G_NEQ = {(u,v): u != v}`

with `N=2^n`, the source proves

`rho_can(G_NEQ) = rho(G_NEQ,G_{N,N}) = D_cap(G_NEQ | G_{N,N}) = log_2 N`.

This equality is a calibration property of `G_NEQ`, not a theorem that canonical and full cover complexity coincide for every graph.

## Transference boundary

The source explains that a `C log N` lower bound on graph intersection complexity for an explicit graph transfers to a related explicit Boolean function with a same-factor linear lower bound, up to an additive constant, on the number of AND/OR gates.

C008 does **not** meet that asymptotic premise. It only supplies a finite `N=3` example with

`rho_can(G)=1 < rho(G,G_{3,3})=2`.

No circuit lower bound is promoted from the finite separator.

## Novelty boundary

The primary source was checked for the definitions, canonical lower-bound relation, and `G_NEQ` equality calibration. C008's exact five-edge `3 x 3` separator is a locally derived result and is not attributed to the source.

No claim is made that this finite separator is absent from the wider graph-cover, fusion, lattice, or communication-complexity literature. Novelty remains `UNRESOLVED` pending a bounded multi-corpus structural search.
