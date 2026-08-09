# Formal Optimization Semantics

Status: clarification for the RAKL formal specification and manuscript.

Several RAKL equations use `argmax` or `argmin` notation. Unless a specific implementation/experiment proves stronger conditions, these equations define a **research-control objective and admissibility constraints**, not a theorem that a unique exact optimizer exists or can be computed efficiently.

## 1. Context compilation

The idealized objective is

\[
C^*(o)=\arg\max_{C\subseteq V(o)}U(C\mid o)
\]

subject to

\[
M(o)\subseteq C,\qquad Tokens(C)\le B.
\]

The current support implementation uses a deterministic constrained marginal-coverage heuristic rather than claiming to solve an arbitrary NP-hard set-selection objective globally. The scientific invariant is the feasibility boundary:

- mandatory epistemic material must be present;
- token budget must be respected;
- optional zero-marginal filler should not be added;
- infeasible mandatory context returns `CANNOT_COMPILE`.

Any optimality claim for a specific utility class requires a separate proof/benchmark.

## 2. Epistemic cut

The conceptual target

\[
B^*_{\tau}=\arg\min_B Cost(B)
\]

subject to every admissible support route to target \(\tau\) intersecting \(B\) defines what is meant by a minimal/low-cost blocking prerequisite set.

In a finite explicitly represented support graph, standard cut/hitting-set methods can sometimes solve a specified instance exactly. In the general RAKL scientific setting, admissible routes, hyperedges, costs or missing objects may themselves be only partially represented. The implementation may therefore return:

```text
EXACT_MINIMUM_CUT_CERTIFIED
LOW_COST_CUT_CANDIDATE
PARTIALLY_IDENTIFIED_CUT_SET
BLOCKED
CANNOT_CHECK
```

as appropriate. A proposed cut is not scientific evidence that the missing object exists; it is a target-conditioned diagnosis of what currently blocks the registered support routes.

## 3. Action / experiment selection

The information-gain expression

\[
u(a\mid K)=\frac{\lambda_Q I(Q;Y_a\mid K)+\lambda_M Sep(a,V)+\lambda_N E[\Delta N_a]}{Cost(a)}
\]

is a policy family only when the probability model and weights are scientifically justified. RAKL does not claim one universal set of \(\lambda\) values or one globally optimal exploration policy. Without calibrated probabilities, the implementation should use explicit set-valued discriminators, worst-case separation, identified-set shrinkage or other registered non-probabilistic criteria.

## 4. Portfolio control

The exploit/diversify/moonshot/meta split is a governance structure, not a claim that one fixed portfolio allocation is universally optimal. Allocation policies are themselves method objects that can be benchmarked and changed through Self-RAKL.

## 5. Manuscript wording rule

When these formulas appear in the paper, interpret phrases such as “RAKL solves” conservatively as:

> RAKL defines the following constrained objective; the reference implementation uses the declared algorithm/heuristic and reports its scope.

Use “exact optimum” only when the relevant conditions and proof/certificate are actually available.
