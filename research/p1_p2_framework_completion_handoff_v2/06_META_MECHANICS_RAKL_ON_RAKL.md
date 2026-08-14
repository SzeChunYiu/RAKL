# Meta-Mechanics: RAKL Applied to RAKL

## M13 — Parent Assimilation Compiler (PAC)

For strongest parent mechanic \(P\), compile

\[
P=(X_P,A_P,I_P,G_P,C_P)
\]

where:

- \(X_P\): state/object space;
- \(A_P\): assumptions/preconditions;
- \(I_P\): invariants;
- \(G_P\): guarantee;
- \(C_P\): cost model.

### Faithful import

A faithful import is permitted only if the local state satisfies all \(A_P\).

Otherwise the faithful import must fail/return CANNOT_CHECK.

### Adapted import

An adaptation \(T\) maps local states into a domain where a weaker/reinterpreted guarantee is valid:

\[
T:X_R\to X_P'.
\]

RAKL novelty may be claimed only for a measured/proved residual after the strongest parent has been absorbed.

---

## M14 — Negative-Result Revival Operator (NRO)

Given frozen negative epoch

\[
n=(m,p,d,y,g)
\]

with attribution DAG \(g\), find a minimal load-bearing failure cut

\[
K\subseteq V(g).
\]

A valid successor \(m'\) must modify at least one causal node in \(K\).

Changing only:

- significance threshold;
- seed;
- result aggregation;
- post-outcome comparator;
- label interpretation;

does not satisfy material difference.

A successor protocol \(p'\) must be frozen before new outcomes and bind fresh evaluation units whenever tuning used the old units.

Output states:

`REVIVAL_FROZEN`, `REVIVAL_POSITIVE`, `REVIVAL_NEGATIVE`, `IMPOSSIBILITY_CLOSED_SCOPE`.

---

## M15 — Recursive Framework Saturation (RFS)

Let domain families searched through wave \(t\) be \(D_t\), and discovered mechanic classes be \(M_t\).

Growth:

\[
\Delta M_t=M_t\setminus M_{t-1}.
\]

A bounded framework-saturation certificate requires, for \(k\) heterogeneous waves,

\[
\Delta M_{t-k+1}=\cdots=\Delta M_t=\varnothing
\]

plus no new counterexample class / stronger parent that alters an active mechanic.

The certificate binds:

- domain search policy;
- query set;
- source cutoff;
- budget;
- mechanic ontology;
- expiry.

Every newly read work becomes one of:

`ALREADY_ABSORBED`,
`STRONGER_PARENT`,
`NEW_MECHANIC`,
`NEW_REPRESENTATION`,
`COUNTEREXAMPLE`,
`IMPOSSIBILITY_BOUND`,
`NEW_EVALUATOR`,
`COST_BOUNDARY`.

`NEW_MECHANIC` may not remain a literature note: prove it redundant or create a mechanic research packet.

---

## M16 — Mechanic Discovery Gate

Issue #546 gates a proposed mechanic.

Add a pre-gate asking whether the current ontology is itself incomplete.

For every major negative search at least:

1. one field using the same formal object;
2. one field studying analogous human/scientific cognition;
3. one mathematical/algorithmic field with a related optimization/consistency problem;
4. one metrology/evaluation field.

Implementation begins only after both:

`FRAMEWORK_FIBRE_CHECKED`
and
`MECHANIC_RESEARCH_PACKET_VALID`.
