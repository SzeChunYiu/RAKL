# Paper II / Pursuit Mechanics

## M1 — Progressive Relational Abstraction (PRA)

### Object

Construct a transferable relational schema from multiple examples rather than assume a one-shot extractor can expose it.

For item \(x_i\), produce abstraction levels

\[
G_i^{(0)},G_i^{(1)},\ldots,G_i^{(L)}.
\]

For pair \((i,j,l)\), construct a partial alignment

\[
\phi_{ij}^{(l)}:G_i^{(l)}\rightharpoonup G_j^{(l)}
\]

subject to typed consistency constraints.

### Schema induction

Given aligned examples \(I\), induce

\[
K=\operatorname{LGG}\{\phi_i(G_i)\}_{i\in I},
\]

where LGG is a declared anti-unification / least-general-generalization operator, not an unconstrained prose summary.

Track

\[
v(K)=
(\mathrm{coverage},
\mathrm{counterexample\ rate},
\mathrm{mapping\ fidelity},
\mathrm{description\ cost},
\mathrm{fresh\ transfer\ yield}).
\]

### Progressive scheduler

Prefer high-alignability comparisons early, then increase abstraction/distance only after a schema survives fresh checks.

Abstraction is not monotone-good. A move \(l\to l+1\) is admitted only when:

- registered query answers/invariants are preserved or explicit losses are declared;
- held-out transfer improves or a specific capability is unlocked;
- near-miss rejection does not cross the harm bound.

Output: `SchemaProposal`, authority floor 0.

Main falsifier: a matched one-shot abstraction parent achieves the same fresh mapping/transfer vector at lower cost.

---

## M2 — Candidate Representation Ecology (CRE)

This extends, not replaces, the existing representation tournament.

Maintain

\[
\mathcal R_t=\{r_1,\ldots,r_k\}.
\]

For registered decisions \(D\), define

\[
\Delta_{ij}=\{q\in D:r_i(q)\neq r_j(q)\}.
\]

Choose a discriminating probe \(a\) maximizing

\[
\operatorname{Disc}(a)=
\mathbb E[\mathrm{load\!-\!bearing\ separation}\mid a]-\lambda c(a).
\]

Statuses:

`ACTIVE`, `DOMINATED_ON_SCOPE`, `INCOMPARABLE`, `CANNOT_CHECK`, `SUPERSEDED_ON_SCOPE`.

No global "best representation" terminal exists.

---

## M3 — Typed Morphism Registry (TMR)

A generic transfer witness must name a morphism family.

For object types \(\tau_s,\tau_t\), register

\[
\mathcal M_{\tau_s,\tau_t}
\]

and validator

\[
V_{\tau}:W_\tau\to
\{\mathrm{LICENSED},\mathrm{REJECTED},\mathrm{CANNOT\_CHECK}\}\times Cert.
\]

A witness is

\[
w=(\tau_s,\tau_t,m,q,P,I,L,B,E)
\]

with morphism \(m\), QoI \(q\), preconditions \(P\), preserved invariants \(I\), forbidden losses \(L\), boundaries \(B\), evidence \(E\).

Candidate families:

- causal exact/uniform abstraction;
- assume-guarantee/refinement maps;
- proof translations;
- algebraic/order homomorphisms;
- dimensional/scaling transformations;
- constraint-preserving maps;
- dynamical conjugacy/approximation;
- generic mechanistic correspondence only when no stronger calculus exists.

Composition \(m_2\circ m_1\) is legal only if types match and every load-bearing obligation transports.

---

## M4 — Explanation / Abduction Competition (EAC)

Generate multiple explanation hypotheses

\[
H=\{h_1,\ldots,h_n\}.
\]

Each explanation exports:

- assumptions;
- covered observations;
- anomalies;
- novel predictions;
- mechanism class;
- alternatives it distinguishes itself from.

Maintain a Pareto frontier over

\[
(\mathrm{coverage},
\mathrm{simplicity},
\mathrm{causal\ adequacy},
\mathrm{novel\ predictive\ content},
\mathrm{anomaly\ burden}).
\]

For every surviving pair, generate a discriminator action.

Explanation is pursuit-only until prediction/experiment evidence arrives.

---

## M5 — Topology-Adaptive Gluing (TAG)

Let \(H\) be the overlap/cover hypergraph.

First compute a topology certificate \(\kappa(H)\).

If a domain-specific theorem certifies that the registered structural class has local-to-global sufficiency, use the cheaper local procedure.

Otherwise use obstruction-retaining gluing.

Important:

\[
\mathrm{acyclicity\ heuristic}\not\Rightarrow\mathrm{global\ validity}.
\]

A topology shortcut is legal only with a theorem/certificate for that object family.

This is a cost mechanic, not a weakening of L2 safety.
