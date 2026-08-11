# C024 — fractional semi-filter packing

**Atom:** `O9d12a2a1`  
**Date:** 2026-08-11  
**Candidate authority:** `SOURCE_BOUND_DERIVED_RELAXATION / EXACT_FINITE_COMBINATORICS / NO_NOVELTY_CLAIM / ROOT_AUTHORITY_NONE`

## Motivation

The strict O9d12a2a1 packet asks for a non-scalar object tied directly to the legal fusion operation. Cavalar–Oliveira define the cover graph

\[
\Phi_{A,B}=(V_{\rm pairs},V_{\rm filters},E)
\]

and identify \(\rho(A,B)\) with the minimum set cover of `V_filters` by neighbourhoods of vertices in `V_pairs`. Their Theorem 30 further identifies \(\rho(A,B)\) exactly with cyclic intersection complexity.

This suggests transferring the standard fractional-cover relaxation rather than guessing another graph statistic.

## Candidate definition

Define the **fractional cover complexity**

\[
\rho_{\rm frac}(A,B)
:=
\min \sum_{p\in V_{\rm pairs}} x_p
\]

subject to

\[
x_p\ge 0,
\qquad
\sum_{p\sim F}x_p\ge 1
\quad\text{for every }F\in V_{\rm filters}.
\]

The LP dual is

\[
\rho_{\rm frac}(A,B)
=
\max \sum_{F\in V_{\rm filters}} y_F
\]

subject to

\[
y_F\ge 0,
\qquad
\sum_{F:\,p\sim F} y_F\le 1
\quad\text{for every }p\in V_{\rm pairs}.
\]

A dual-feasible vector `y` is the non-scalar research object: it is a weighted distribution over semi-filters whose total mass is the lower-bound certificate.

## Local law

Every integral cover is a feasible fractional cover by taking `x_p in {0,1}`. Hence

\[
\rho_{\rm frac}(A,B)\le \rho(A,B).
\]

Using Cavalar–Oliveira Theorem 30,

\[
\boxed{\rho_{\rm frac}(A,B)\le \rho(A,B)=D^{\rm cyclic}_{\cap}(A\mid B).}
\]

Equivalently, for any dual-feasible `y`, every legal pair/fusion covers at most one unit of `y`-mass. Therefore a cyclic construction with `t` counted intersections can only eliminate at most `t` units of such mass, and

\[
D^{\rm cyclic}_{\cap}(A\mid B)\ge \sum_F y_F.
\]

This exactly satisfies the desired candidate-independent one-fusion budget. Free unions require no additional accounting because the certificate lives on the cover graph/fusion pairs rather than on a chosen acyclic construction sequence.

## Novelty boundary

This is **not claimed as a new mathematical method**. Fractional covers and LP duality are classical, and Karchmer–Kushilevitz–Nisan explicitly studied fractional-cover relaxations in communication complexity. C024 is a transfer of that mechanism to the Cavalar–Oliveira cover graph.

## Adversarial calibration: `G_NEQ`

The candidate passes its local-law obligation but loses an unbounded logarithmic factor on the paper's own simple lower-bound example.

Let `N=2^n` and let `G_NEQ` be the bipartite graph of unequal pairs. Cavalar–Oliveira Proposition 40 proves

\[
\rho(G_{\rm NEQ},G_{N,N})=n=\log_2 N.
\]

For this target the universe `U=G_NEQ^c` is the diagonal, which we identify with `[N]`. For every subset `S subseteq [N]`, let

\[
E_S=\{(i,i):i\in S\},\qquad H_S=U\setminus E_S.
\]

Assign the pair `(E_S,H_S)` fractional weight

\[
x_S=\frac{2}{2^N}.
\]

Fix any semi-filter `F` above an edge `(u,v) in G_NEQ`, where `u != v`. Being above `(u,v)` forces `F` to contain the two generator traces `{(u,u)}` and `{(v,v)}`. If `S` separates `u` and `v`, upward closure gives both `E_S in F` and `H_S in F`, while `E_S cap H_S=emptyset` is not in a semi-filter. Hence `(E_S,H_S)` covers `F`.

Exactly half of all subsets `S` separate two fixed distinct elements, so the fractional mass covering `F` is

\[
2^{N-1}\cdot \frac{2}{2^N}=1.
\]

Thus the assignment is feasible and

\[
\boxed{\rho_{\rm frac}(G_{\rm NEQ},G_{N,N})\le 2}
\]

while the exact cover complexity is `log_2 N`.

Therefore

\[
\frac{\rho(G_{\rm NEQ},G_{N,N})}
{\rho_{\rm frac}(G_{\rm NEQ},G_{N,N})}
\ge \frac{\log_2 N}{2}.
\]

The plain fractional relaxation does not even recover the known logarithmic benchmark asymptotically.

## Diagnosis

The failure is not that the local one-fusion law is false; that law is exact. The failure is **loss of cross-fusion correlation/integrality**. Fractional weights let many mutually incompatible cuts share responsibility for one semi-filter. An actual cyclic construction must choose a finite integral collection of pairs that works simultaneously for every semi-filter.

This identifies a sharper child obstruction:

> `O9d12a2a1a`: construct a correlation-sensitive lift of semi-filter packing that retains a bounded per-fusion budget but does not collapse from `log N` to `O(1)` on `G_NEQ`.

Candidate next families include lifted/hierarchical set-cover relaxations, entropy/information certificates over joint pair choices, or other correlation-sensitive packings. No such successor is proposed here; it requires a fresh strict context packet.

## Method-memory consequences

**Success side:** retain fractional semi-filter packing as a scoped tool for cheap lower-bound certificates, because any explicit dual-feasible weighting is automatically a valid lower bound.

**Failure side:** record `F-C024-FRACTIONAL-INTEGRALITY-GAP`: plain independent fractional weighting can lose an unbounded logarithmic factor even on `G_NEQ`; any future fractional/convex relaxation must carry a difference witness explaining how it restores correlation across multiple pair choices.

## Sources

- Bruno P. Cavalar and Igor C. Oliveira, *Boolean Circuit Complexity and Two-Dimensional Cover Problems*, ECCC TR25-033 / ACM TOCT 17(2), 2025: Definition 21, cover-graph set-cover interpretation, Theorem 30, Proposition 40.
- Mauricio Karchmer, Eyal Kushilevitz, and Noam Nisan, *Fractional Covers and Communication Complexity*, SIAM Journal on Discrete Mathematics: prior fractional-cover/LP method context.
