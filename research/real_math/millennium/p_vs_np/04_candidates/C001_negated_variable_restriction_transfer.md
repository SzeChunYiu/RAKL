# C001 — negated-variable restriction transfer for CLIQUE

**Status:** PROOF_DRAFT / SPECIFICATION_CHECKED_LOCALLY / FORMALIZATION_AND_NOVELTY_UNRESOLVED

This candidate is an intermediate bridge lemma. It is **not** a P-versus-NP solution.

## Definitions

Let `CLIQUE_{n,k}` be the monotone Boolean function on the `binom(n,2)` edge variables of a simple undirected graph on vertex set `[n]`. The output is 1 exactly when the graph contains a `k`-clique.

A De Morgan circuit here has AND/OR gates and permits negation only at input literals. Constants are allowed after restrictions.

For such a circuit `C`, let `T(C)` be the set of edge variables that occur negated anywhere in `C`, and let `t = |T(C)|`.

Let `M(r,k)` denote the minimum size of a **monotone** AND/OR circuit computing `CLIQUE_{r,k}`.

## Claim C001

If a De Morgan circuit `C` of size `s` computes `CLIQUE_{n,k}` and `t = |T(C)|`, then there exists an integer

`r >= floor(n^2 / (2t + n))`

such that, whenever `r >= k`,

`s >= M(r,k)`.

Equivalently, every known lower bound on monotone circuit size for `CLIQUE_{r,k}` transfers immediately to De Morgan circuits for `CLIQUE_{n,k}` whose set of negated edge variables is small enough to leave such an `r` at least `k`.

## Proof draft

Construct a graph `H` on the same `n` vertices. Put an edge `e` in `H` exactly when the corresponding CLIQUE input variable belongs to `T(C)`.

`H` has `t` edges and average degree `2t/n`. By the standard independent-set bound

`alpha(H) >= n^2 / (2t+n)`.

Choose an independent set `U` in `H` of size `r` at least the displayed floor.

Now restrict the original CLIQUE variables as follows.

1. Set every edge variable in `T(C)` to 0.
2. Set every remaining edge variable that is not internal to `U` to 0.
3. Leave the edge variables internal to `U` free.

Because `U` is independent in `H`, no internal edge variable of `U` belongs to `T(C)`. Therefore every negated input literal appearing in `C` has been fixed to a constant by step 1. After simplifying constants, the restricted circuit is a monotone AND/OR circuit in the free internal-edge variables of `U`, and its size is at most `s`.

Under the same restriction, the target function becomes exactly `CLIQUE_{r,k}` when `r >= k`. All edges outside `U` are absent, while every possible edge inside `U` remains a free variable. Hence a `k`-clique exists in the restricted graph exactly when the free graph on `U` contains one.

Thus the restricted circuit is a monotone circuit for `CLIQUE_{r,k}` of size at most `s`. By definition of `M(r,k)`,

`M(r,k) <= s`.

This proves the claim.

## Independent-set sublemma

The bound used above follows, for example, from Caro–Wei plus Cauchy–Schwarz:

`alpha(H) >= sum_v 1/(deg(v)+1) >= n^2 / sum_v(deg(v)+1) = n^2/(2t+n)`.

No complexity-theoretic assumption is used in this sublemma.

## What C001 buys

C001 converts the vague phrase "negation is the gap" into a quantitative parameter. If the negated-variable set is sparse, a large negation-free vertex subset survives and monotone CLIQUE hardness can be inherited on that subset.

## What C001 does not buy

A general circuit can, after De Morgan normalization, depend on negated literals for a large fraction or all of the `binom(n,2)` edge variables. Then `n^2/(2t+n)` may be constant, and C001 gives no asymptotic general-circuit lower bound.

Therefore the residual is precise:

> control the usefulness of **dense negative-literal access**, or replace cardinality `t` by a structural parameter that remains small even when many negated variables occur.

Potential next parameters include vertex cover number, degeneracy, arboricity, matching structure, locality of negative literals in the circuit DAG, or target-relative cancellation rank. Each must be tested against counterexamples before proof search.

## Barrier audit

- Relativization: C001 is a finite combinatorial restriction lemma and is not claimed to cross the root relativization barrier.
- Natural proofs: C001 inherits a restricted monotone lower bound after a syntactic restriction. It is not a general useful/large/constructive property against P/poly.
- Algebrization: not relevant to the lemma itself.

## Promotion blockers

- formal theorem-prover artifact absent;
- primary-literature novelty search absent;
- isolated independent reviews absent;
- strongest monotone lower-bound parent theorem not yet bound to an exact source/version.

Until those are resolved, authority remains `PROOF_DRAFT`.
