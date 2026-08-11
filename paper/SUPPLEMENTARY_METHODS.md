# Supplementary Methods — Formal Propositions and Proof Sketches

Status: structural/formal support for the RAKL methods paper. These propositions do not prove empirical scientific performance.

## S1. Formal objects

A scoped task is

\[
\mathcal P=(O,\mathcal Q,\Gamma_0,\mathcal E_0,\mathcal B,\Lambda).
\]

The canonical epistemic state is

\[
K_t=(\mathcal A_t,\mathcal T_t,\mathcal V_t,\mathcal E_t,\mathcal U_t,
\mathcal O_t,\mathcal F_t,\mathcal H^-_t,\mathcal S_t,\mathcal G_t^K).
\]

Proposal, verification and update are

\[
G_\theta(K_t,a_t)\to\mathcal P_t,
\]

\[
V(p,e,\gamma)\to\{SUPPORTED,REFUTED,PARTIALLY\_IDENTIFIED,BLOCKED,CANNOT\_CHECK\},
\]

and

\[
K_{t+1}=\mathcal U(K_t,a_t,e_{t+1},V,\mathcal G_t^K).
\]

All propositions below assume that `U` obeys the registered Constitution and mechanic contracts.

---

## S2. Proposition: proposal generation cannot by itself increase canonical authority

**Statement.** Holding \(K_t\), the evidence supplied to \(V\), and governance \(\mathcal G_t^K\) fixed, changing the textual/stochastic output of \(G_\theta\) alone cannot increase canonical scientific authority.

**Proof sketch.** By definition, \(G_\theta\) returns a proposal set \(\mathcal P_t\) but has no direct write path to the canonical authority coordinate. Authority changes are outputs of \(\mathcal U\), and \(\mathcal U\) requires the verification result \(V(p,e,\gamma)\) plus protected governance. A new unsupported proposal can therefore alter the candidate set but cannot create an evidence certificate. Any implementation path that writes canonical authority directly from generated text violates the transition definition.

**Implementation correspondences.** Promotion and support reports expose explicit `grants_*_authority=false` or proposal-only states. Hostile tests verify that support-module success does not activate canonical knowledge.

---

## S3. Proposition: negative history is monotone under a valid update

**Statement.** For valid RAKL updates,

\[
\mathcal H^-_t\subseteq\mathcal H^-_{t+1}.
\]

**Proof sketch.** The update contract permits append and scoped supersession references, not destructive removal of prior null/refutation events. A later positive result can add a new scoped interpretation or supersession edge, but the historical negative object remains in the evidence/history graph with its original context and cutoff. Induction over valid updates gives monotonic addressability of all previous negative records.

**Boundary.** The proposition is about preservation of historical objects, not about monotone belief in their current interpretation.

---

## S4. Proposition: observational equivalence cannot entail mechanism equivalence without an additional rule

**Statement.** A valid certificate for observational equivalence alone does not entail `MECHANISM_EQUIVALENCE`.

**Proof sketch.** Observational equivalence occupies the representation/observation coordinate \(R\), while mechanism equivalence requires the mechanism coordinate \(M\). The authority order is coordinatewise under compatible scope; no default order embedding maps an \(R\)-certificate to an \(M\)-certificate. Therefore an upgrade requires an explicit mechanism-identifying inference rule and evidence, for example interventions or ancestry constraints sufficient to rule out alternative mechanisms.

**Counterexample.** Two latent mechanisms can induce the same observation distribution under a limited measurement operator. This establishes observational equivalence over that probe family but leaves mechanism identity unresolved.

---

## S5. Proposition: pairwise local compatibility is insufficient for unique global identification

**Statement.** Pairwise-compatible local charts do not, in the general RAKL setting, imply that a unique global scientific object is identified.

**Proof sketch.** RAKL distinguishes overlap compatibility, path/cycle coherence, global existence and uniqueness. Even when all tested overlaps are compatible, transition compositions around cycles may be inconsistent, or several distinct global objects may restrict to the same local observations. Unique gluing therefore requires additional conditions beyond pairwise compatibility. This is why the synthesis codomain includes `PLURAL_ATLAS` and `OBSTRUCTED_OR_IDENTIFIED_SET`.

**Relation to prior mathematics.** Under stronger sheaf conditions, compatible local sections can have a unique global gluing. RAKL does not assume those conditions globally; it records when they are or are not evidenced for the scientific charts under study.

---

## S6. Proposition: typed transition paths do not automatically escalate relation type

Let

\[
T_{ij}^{\tau_1,\sigma_1},\qquad T_{jk}^{\tau_2,\sigma_2}
\]

be valid transitions.

**Statement.** The composition can be assigned a relation \(\tau_3\) only when the relation algebra licenses

\[
\tau_2\circ\tau_1\Rightarrow\tau_3
\]

under a non-empty compatible scope and a declared error/invariant composition rule.

**Proof sketch.** Relation labels are evidence-bearing types, not graph-connectivity decorations. If a relation type is not closed under composition, graph reachability alone does not prove the endpoint relation. Approximate maps additionally require an error rule; otherwise accumulated error is undefined. The bridge-composition layer therefore distinguishes navigability from composable transfer hypotheses and target validation.

---

## S7. Derivation: affine covariance transport

For

\[
Y=AX+b,
\]

with \(E[X]=\mu\),

\[
E[Y]=A\mu+b.
\]

Then

\[
\begin{aligned}
\operatorname{Cov}(Y)
&=E[(Y-E[Y])(Y-E[Y])^\top]\\
&=E[A(X-\mu)(X-\mu)^\top A^\top]\\
&=A\,E[(X-\mu)(X-\mu)^\top]A^\top\\
&=A\Sigma A^\top.
\end{aligned}
\]

No independence assumption is used. The implementation rejects dimension mismatch, nonsymmetric covariance and non-positive-semidefinite covariance.

---

## S8. Derivation and boundary: first-order nonlinear covariance

For differentiable \(g:\mathbb R^n\to\mathbb R^m\), a first-order Taylor expansion around \(\mu\) gives

\[
g(X)\approx g(\mu)+J_g(\mu)(X-\mu).
\]

Hence

\[
\operatorname{Cov}(g(X))\approx J_g(\mu)\Sigma J_g(\mu)^\top.
\]

This is an approximation whose validity depends on local differentiability and whether higher-order terms are negligible over the uncertainty region. The implementation therefore requires a differentiability witness and labels the result as first-order rather than exact.

For scalar independent standard uncertainties with unit coefficients,

\[
u_c^2=\sum_i u_i^2
\]

follows from the covariance of a sum only when cross-covariances vanish. Without an independence/uncorrelatedness witness, RAKL rejects root-sum-square composition and requires a covariance model.

---

## S9. Proposition: mandatory epistemic context prevents silent validity loss from truncation

For operation \(o\), define mandatory set \(M(o)\) and token budget \(B\). The compiler solves

\[
C^*=\arg\max_{C\subseteq V(o)}U(C\mid o)
\]

subject to

\[
M(o)\subseteq C,\qquad Tokens(C)\le B.
\]

**Statement.** If \(Tokens(M(o))>B\), no feasible context exists, so any compiler returning a context that silently omits a mandatory atom violates the registered optimization constraints.

**Consequence.** `CANNOT_COMPILE` is not an implementation inconvenience; it is the mathematically correct infeasibility state under the frozen contract.

---

## S10. Proposition: semantic flatness is not problem closure

Define

\[
\Delta_t^f=\mathcal C_t^f\setminus\mathcal C_{t-1}^f.
\]

**Statement.** \(\Delta_t^f=\varnothing\) establishes only that the most recent search/update added no new retained semantic objects after deduplication. It does not imply that the scientific target is identified or that no unknown fact exists.

**Reason.** The search universe can be incomplete, a required experiment can be unavailable, or a target can remain blocked by an epistemic cut even when the literature search is flat. Strong RAKL saturation therefore also registers route coverage, residual state and independence qualifications.

---

## S11. Proposition: development improvement is insufficient for strong self-evolution evidence

Let \(D\) be optimizer-visible development tasks and \(A\) a fresh assurance set protected from the challenger during optimization.

**Statement.** \(\Delta_D>0\) alone is insufficient for a strong RAKL self-evolution claim.

**Reason.** Adaptive optimization can fit properties of \(D\), and repeated disclosure of assurance scores can adaptively consume \(A\). RAKL therefore requires \(\Delta_A>0\), blocking-invariant preservation, candidate/evaluator separation and assurance freshness for scoped evolution evidence. If \(\Delta_D>0\) and \(\Delta_A<0\), the registered outcome is `META_OVERFIT`.

---

## S12. Proposition: missing-operator diagnosis, identification and validation are different evidence states

**Statement.** Evidence that the current operator basis cannot resolve a localized epistemic cut does not uniquely identify the missing operator family, and identifying a candidate operator family in one development world does not establish transfer.

**Proof sketch.** Several operator families can resolve the same observed residual. The missing-operator benchmark therefore represents `gap_detected`, `candidate_operator_family`, alternative surviving operator families and fresh-transfer outcome as separate coordinates. Only a frozen discriminating world can eliminate alternatives, and only a fresh world can establish transfer beyond the original surface.

---

## S13. Proposition: execution receipt identity detects unregistered subject changes

Let

\[
i=SHA256(Canon(protocol,packet,runner,config,nonce)).
\]

A valid receipt is stored content-addressably and binds the event-chain head.

**Statement.** Any change to a bound component changes the invocation identity, while mutation of a stored event or receipt changes its digest and breaks verification.

**Boundary.** This proves artifact/transport identity under the hashing model. It does not prove that an opaque hosted provider used the claimed internal weights unless the provider exposes independently verifiable evidence.

---

## S14. Definition: scoped formal closure

Let \(\mathcal M\) be the registered method-surface set and \(C(m)\) the mechanic contract for surface \(m\).

\[
FormalClosed_{\mathcal R}(M)=1
\iff
\forall m\in\mathcal M,\exists!C(m):ContractValid(C(m)).
\]

`ContractValid` requires non-empty typed I/O, scientific scope/context, assumptions, state reads/writes, authority effect, non-escalation rules, failure semantics, invariants, mathematical semantics, implementation/test references and empirical-open coordinates.

**Structural proposition.** If the machine checker returns `CLOSED_SCOPED`, then every surface in the *registered* inventory has exactly one contract satisfying those structural fields.

**Non-implication.** The checker does not prove that the inventory is ontologically complete, that any method surface works well on real science, or that the framework is saturated. A real challenge can falsify current formal closure by exposing a necessary unregistered surface or inconsistency.

---

## S15. The 24-surface implementation correspondence

The canonical contracts are executable objects in `src/rakl/method_specs.py`, validated by `src/rakl/formal_contracts.py`. They map each method surface to concrete implementation and hostile-test files. This correspondence prevents the manuscript from adding a conceptual module that has no software owner, while the `empirical_open_coordinates` field prevents a structurally complete contract from masquerading as a validated scientific capability.
