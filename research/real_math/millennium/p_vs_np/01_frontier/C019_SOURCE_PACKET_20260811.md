# C019 source packet — quadratic-residue difference family

**Cutoff:** 2026-08-11  
**Authority:** source context only; no novelty certificate.

## Primary source S1 — active graph-cover route

Bruno P. Cavalar and Igor C. Oliveira, **Boolean Circuit Complexity and Two-Dimensional Cover Problems**, ECCC TR25-033 (18 March 2025), ACM Transactions on Computation Theory 17(2), Article 13 (2025), DOI `10.1145/3718746`.

Relevant source statements used by R004/C019:

- cover complexity `rho(A,B)` is bounded above by intersection complexity and characterizes cyclic intersection complexity;
- random square bipartite graphs have cover complexity `Theta(N)`;
- explicit `C log N` graph/intersection lower bounds transfer to corresponding linear Boolean-circuit lower bounds with constant `C` in the construction of Remark 14;
- the source leaves matching or strengthening known explicit unrestricted Boolean-circuit lower bounds through this framework open.

Primary retrieval route during this pass: ECCC report page and ECCC PDF for TR25-033.

## Primary source S2 — Paley-tournament family definition

Dermot McCarthy and Mason Springfield, **Transitive subtournaments of k-th Power Paley Digraphs and improved lower bounds for Ramsey numbers**, arXiv:2311.02135 (2023).

The paper defines the Paley tournament for `q == 3 mod 4` on `F_q` by

`a -> b iff b-a is a nonzero square`,

and generalizes the relation to higher-power residues. C019 uses the `q=p` prime, `k=2` relation as a bipartite adjacency predicate.

## Bounded novelty/search routes

Queries run at the 2026-08-11 cutoff included combinations of:

- `cover complexity Paley graph`;
- `cover complexity Paley tournament`;
- `two-dimensional cover Paley`;
- `cyclic intersection complexity Paley`;
- `Paley tournament adjacency GF(2) rank`;
- `quadratic residue circulant rank GF(2)`.

The search recovered the active Cavalar–Oliveira paper and Paley/difference-set literature, but no primary source was identified in this bounded pass that states the exact C019 graph-cover question or a super-log/full-cover bound for `QR_p`.

This absence is not evidence of global novelty. C019 therefore carries `NO_NOVELTY_CLAIM`.

## Classical dependencies used in the proof draft

C019-L1 also uses standard algebra/number-theory facts:

- circulant invertibility via `gcd(a(X),X^p-1)`;
- the supplementary quadratic-residue law `(2/p)=-1` for `p == 3 mod 8`;
- Frobenius squaring in characteristic two;
- the geometric-series identity for nontrivial `p`-th roots of unity.

These are proof dependencies, not novelty anchors. A formal promotion would require them to be bound in the formal dependency graph rather than merely cited as standard.
