# RAKL Formal System Specification

Status: **canonical scoped formal specification for the pre-Polymarket reference profile**  
Date: 2026-08-09  
Scope: formal and software architecture. This document does not establish empirical superiority, scientific truth for a target domain, framework saturation, or universal completeness.

## 1. Purpose and closure boundary

RAKL is modeled as an evidence-governed recursive scientific process rather than as one prompt, agent topology, retrieval method, or model family. The objective of this specification is to make every high-impact method surface explicit enough that a real project can expose empirical weaknesses without first exposing an unowned conceptual primitive.

The present closure claim is therefore

\[
\operatorname{FormalClosed}_{\mathcal R}(M)=1,
\]

for a declared reference profile \(\mathcal R\), only if every registered method surface has a typed contract, mathematical semantics where applicable, fail-closed outcomes, an authority boundary, implementation/test references, and an explicit list of empirical coordinates that remain open.

This is intentionally distinct from

\[
\operatorname{EmpiricallyValidated}(M),
\qquad
\operatorname{Saturated}(M),
\qquad
\operatorname{UniversallyComplete}(M).
\]

A new native residual reopens only the affected formal or empirical coordinate.

---

## 2. Research task and researcher state

A scoped research task is

\[
\mathcal P=(O,\mathcal Q,\Gamma_0,\mathcal E_0,\mathcal B,\Lambda),
\]

where \(O\) is the target object, \(\mathcal Q\) the registered scientific questions or quantities of interest, \(\Gamma_0\) the initial context/observation boundary, \(\mathcal E_0\) the evidence available at the declared cutoff, \(\mathcal B\) the resource budget, and \(\Lambda\) the blocking epistemic invariants.

The functional researcher state is

\[
\mathfrak R_t=(K_t,\mathcal Z_t,\Omega_t,\Pi_t,\mathcal G_t,\mathcal M_t,\mathcal X_t,\mathcal R_t),
\]

with explanatory survivors \(\mathcal Z_t\), method/operator repertoire \(\Omega_t\), executive policy \(\Pi_t\), research agenda \(\mathcal G_t\), metacognitive model \(\mathcal M_t\), experience/transfer history \(\mathcal X_t\), and resource state \(\mathcal R_t\).

The epistemic state is

\[
K_t=(\mathcal A_t,\mathcal T_t,\mathcal V_t,\mathcal E_t,\mathcal U_t,
\mathcal O_t,\mathcal F_t,\mathcal H^-_t,\mathcal S_t,\mathcal G^K_t).
\]

The coordinates are:

- \(\mathcal A_t\): source and derived Knowledge Atlas charts;
- \(\mathcal T_t\): typed chart transitions and composition certificates;
- \(\mathcal V_t\): surviving representations, hypotheses, mechanisms and models;
- \(\mathcal E_t\): evidence, provenance, identity and lineage graph;
- \(\mathcal U_t\): uncertainty objects, bounds and identified sets;
- \(\mathcal O_t\): contradictions, obstructions, epistemic cuts and residuals;
- \(\mathcal F_t\): recursive atomic research fibers;
- \(\mathcal H^-_t\): immutable negative/null/refuted/failed history;
- \(\mathcal S_t\): semantic novelty, route coverage and saturation state;
- \(\mathcal G^K_t\): protected governance/evaluator identities relevant to epistemic updates.

The two symbols \(\mathcal G_t\) and \(\mathcal G_t^K\) are deliberately distinct: the first is the research agenda; the second is the governance state protecting admissible epistemic transitions.

---

## 3. Local charts, context and measurement

A local scientific chart is

\[
C_i=(U_i,\phi_i,\gamma_i,e_i,\alpha_i),
\]

with scientific subdomain \(U_i\), representation/coordinate system \(\phi_i\), context \(\gamma_i\), evidence/provenance packet \(e_i\), and scoped authority \(\alpha_i\).

A practical context tuple can contain

\[
\gamma_i=(p,s,r,u,h,a,\iota,t,q),
\]

for population \(p\), scale \(s\), regime \(r\), units \(u\), observation model \(h\), assumptions \(a\), intervention \(\iota\), time/cutoff \(t\), and QoI \(q\). Additional coordinates are opened when residuals show that this context is insufficient.

An observation is modeled as

\[
y=h(O,\eta,\gamma)+\epsilon,
\]

where \(\eta\) captures instrument/calibration state. Thus instrument, procedure, measurement model, observation operator, measurand and result are not interchangeable concepts.

### 3.1 Exact affine measurement transport

For an affine coordinate transform

\[
Y=AX+b,
\]

with \(E[X]=\mu_X\) and \(\operatorname{Cov}(X)=\Sigma_X\),

\[
\mu_Y=A\mu_X+b.
\]

The covariance follows directly:

\[
\begin{aligned}
\Sigma_Y
&=E[(Y-E[Y])(Y-E[Y])^\top]\\
&=E[A(X-\mu_X)(X-\mu_X)^\top A^\top]\\
&=A\Sigma_XA^\top.
\end{aligned}
\]

This law requires dimension compatibility and a valid covariance matrix; no independence assumption is needed because the full covariance is transported.

### 3.2 Nonlinear first-order uncertainty propagation

For differentiable \(g\) around \(\mu_X\),

\[
g(X)\approx g(\mu_X)+J_g(\mu_X)(X-\mu_X),
\]

hence the first-order delta-method approximation

\[
\Sigma_{g(X)}\approx J_g\Sigma_XJ_g^\top.
\]

This is a local approximation, not an exact nonlinear uncertainty law. Differentiability, local validity and the selected linearization point are explicit assumptions.

For independent scalar standard uncertainties \(u_i\) entering with unit coefficients,

\[
u_c=\sqrt{\sum_i u_i^2}
\]

is licensed only when an explicit independence/uncorrelatedness witness exists. Correlated cases require a covariance model. RAKL never silently substitutes root-sum-square for unknown dependence.

---

## 4. Typed transitions and relation algebra

For overlapping charts,

\[
T_{ij}^{\tau,\sigma}:\phi_i(U_i\cap U_j)\rightarrow\phi_j(U_i\cap U_j),
\]

where \(\tau\) is the relation type and \(\sigma\) the licensed scope. Every transition carries assumptions, evidence and uncertainty/error semantics.

The core relations include exact or scoped forms of semantic equivalence, exact isomorphism, same observable, observational equivalence, QoI equivalence, mechanism equivalence, approximate representation, versioning, derivation and possible aliasing.

A composed transition

\[
T_{ik}=T_{jk}\circ T_{ij}
\]

is licensed only if:

1. codomain/domain interfaces match;
2. the relation algebra explicitly licenses the type composition;
3. the global scope intersection is non-empty;
4. invariant/role handoffs are preserved;
5. evidence lineage remains traceable;
6. approximation/error semantics possess a declared composition rule.

Therefore connectivity does not imply scientific support, and mixed weaker relations cannot silently mint a stronger relation.

---

## 5. Context alignment, contradiction and gluing

For comparison layer \(\ell\), alignment is a predicate

\[
\operatorname{Align}_{\ell}(C_i,C_j),
\]

which is true only after the context coordinates relevant at \(\ell\) are matched or translated.

A scientific contradiction is

\[
\operatorname{Contradict}_{\ell}(C_i,C_j)
=
\operatorname{Overlap}(C_i,C_j)
\land \operatorname{Align}_{\ell}(C_i,C_j)
\land \neg \operatorname{Compatible}_{\ell}(C_i,C_j).
\]

A gluing trial tests, separately:

1. overlap compatibility;
2. path/cycle coherence;
3. existence of a global object;
4. uniqueness/identifiability of that object.

The synthesis result is therefore

\[
\operatorname{Glue}(\mathcal A)
\in\{\text{GLOBAL_FORMALISM},\text{PLURAL_ATLAS},
\text{OBSTRUCTED_OR_IDENTIFIED_SET}\}.
\]

Pairwise agreement does not imply unique global identifiability.

---

## 6. Scientific authority as a partial order

Scientific authority is represented by the coordinate tuple

\[
\alpha(c)=(G_c,R_c,M_c,I_c,D_c),
\]

where \(G\) covers grounding/provenance, \(R\) representation/relation, \(M\) mechanism ancestry, \(I\) identification/bounding, and \(D\) decision/QoI usability.

Each coordinate is a set of scoped certificates rather than a scalar confidence. For two claims under compatible scope,

\[
\alpha_1\preceq\alpha_2
\]

only when every relevant certificate coordinate of \(\alpha_1\) is contained in or entailed by the corresponding coordinate of \(\alpha_2\).

The structure is therefore a **poset**, not automatically a lattice. A join can be obstructed by incompatible populations, assumptions, observation operators or contexts.

Cross-axis non-escalation rules include

\[
R\not\Rightarrow M,\qquad D\not\Rightarrow M,\qquad M\not\Rightarrow I,
\]

and provenance/citation multiplicity does not imply truth or independent evidence.

---

## 7. Proposal, verification and canonical update

A proposer is

\[
G_\theta(K_t,a_t)\rightarrow\mathcal P_t.
\]

It may be an LLM, human, symbolic system or hybrid. It has no direct canonical write authority.

Verification is

\[
V(p,e,\gamma)
\rightarrow
\{\text{SUPPORTED},\text{REFUTED},\text{PARTIALLY_IDENTIFIED},
\text{BLOCKED},\text{CANNOT_CHECK}\}.
\]

Canonical update is

\[
K_{t+1}=\mathcal U(K_t,a_t,e_{t+1},V,\mathcal G^K_t).
\]

The update obeys at least:

\[
\mathcal H^-_t\subseteq\mathcal H^-_{t+1},
\]

and all evidence/provenance identities used by the update remain addressable after supersession.

An authority increase requires a certificate-producing evidence gate. A proposal, repeated model agreement, or a successful support-module unit test is not such a gate.

---

## 8. Recursive atomic fibers and goal-conditioned reachability

An unresolved transformation is represented by

\[
f=(o_f,q_f,\gamma_f,r_f,\operatorname{parent}(f)).
\]

Residual routing

\[
\rho(r,K_t)\subseteq\mathcal F_{t+1}
\]

opens only the dimensions capable of changing the current target conclusion.

Given target \(\tau=(q,\alpha^*,\gamma)\), RAKL searches for an authority-valid support hypergraph from existing evidence to \(\tau\). If no admissible support structure exists, the method seeks an epistemic cut

\[
B^*_{\tau}
=\arg\min_B \operatorname{Cost}(B)
\]

subject to every admissible support route to \(\tau\) intersecting \(B\).

A cut element can represent missing evidence, measurement, context, transition, mechanism, formal lemma or reasoning operator.

Gap detection, operator-family identification and fresh transfer are distinct events. A missing-operator support layer may diagnose

\[
\omega^*\notin\Omega_t,
\]

but cannot activate \(\omega^*\) without separate validation.

### 8.1 Recursive framework audit (vertical recursion over the fibers)

Each fiber additionally carries an **audit projection**

\[
\pi_{\mathrm{audit}}(f)=
(Q_f,\Phi_f,D_f,I_f,M_f,V_f,R_f,\chi_f),
\]

whose components are the question candidates \(Q_f\), framework candidates \(\Phi_f\), decomposition candidates \(D_f\), interface contracts \(I_f\), measurement contracts \(M_f\), evaluator epoch \(V_f\), responsibility-hypothesis set \(R_f\subseteq\{\)QUESTION, FRAMEWORK, DECOMPOSITION, INTERFACE, ATOM, MEASUREMENT, EVALUATOR, EVIDENCE, METHOD\(\}\), and closure state \(\chi_f\). The projection is read off the existing fiber; it is not a second authority architecture.

A material residual with \(|R_f|>1\) admits no revision: a discriminator must first separate the responsibility levels. Revision actions are pursuit-state changes only (question reframe, framework challenge, split, merge, interface repair, measurement revision, evaluator audit, descend, ascend) and never change scientific authority, which remains governed by §7.

**Provisional atomicity.** An atom is atomic only relative to a registered target, split family, evaluator epoch and evidence cutoff:

\[
\operatorname{atomic}(f;\tau,\sigma,V,t_{\operatorname{cut}}),
\]

never absolutely. There is no ATOM-PROVEN-FOREVER terminal. A receipt is issued only when all five admissibility conditions hold over the registered split family: no admissible split yields materially different target predictions, different authority prerequisites, or a different optimal decision action; no child falsifier exposes a hidden mixed regime; and the split interface burden reveals no omitted structure. A condition that was not established fails closed --- an unchecked split family is an unrun check, not evidence of atomicity.

**Question and framework adequacy.** Candidate selection is governed by adequacy *vectors*, never a scalar score. A question is assessed on decision relevance, scope clarity, alternative distinguishability, falsifiability/boundability, measurement availability, identifiability, parent-formulation coverage, nondegeneracy and resource feasibility; a framework is assessed *for a target* on target and alternative expressibility, discriminating predictions, interface validity, measurement grounding, uncertainty semantics, decision sufficiency, residual localizability, fresh transfer and complexity/cost. Coordinates are noncompensatory: a hard failure on one is fatal regardless of the others, and an unrated coordinate is reported as an unrun check rather than counted as a pass. A framework portfolio registers the direct/minimal, canonical-domain, strongest-retrieved and current-compiled parents before selection; a synthesized challenger is admissible only where those parents leave a residual and never discharges the obligation to register them.

**Interface contracts.** A parent--child interface binds the discharged parent obligation, inherited inputs, returned outputs, assumptions, scope, units/representation, uncertainty composition, failure/CANNOT_CHECK semantics, and the authority that may and may not transport across the boundary. Authority transport is fail closed: what is not explicitly licensed does not transport, so a child cannot silently update its parent by omission.

**Ancestor challenge.** Descendant failures may reopen the lowest responsible ancestor. Ascent requires a supported parent challenge and at least two distinct failed local repair families:

\[
\text{ascend} \iff c_{\mathrm{par}} \wedge |\Sigma_{\mathrm{failed}}|\ge 2.
\]

The challenge itself is a packet, not a tally of failures: child identity, residual identity, local causes tested, distinct failed local repair families, fresh evidence epochs, the implicated parent coordinate, a local-versus-parent discriminator, and cost. Repeated raw failure establishes only that the local level is not responsible; the discriminator is what separates parent from child, and escalation is inadmissible without it.

Ancestor supersession stales dependent descendant closure certificates; evidence identities remain addressable (no negative-history deletion).

**Bounded node closure.** A node stops as STOP_BOUNDED only when its closure coordinates pass and no material open residual remains at the registered cutoff; a resource bound with the audit still open yields CANNOT_CHECK, which is neither solver failure nor a scientific terminal. The full NODE-CLOSED-AT-REGISTERED-CUTOFF assessment is eight-coordinate: the active question is decision-sufficient under registered challengers, the framework is not dominated by a registered parent or challenger, the decomposition passes its split/merge/coverage checks, interfaces are complete, measurement and evaluator are valid, the target is solved to the required authority or its blocker is typed, no native decision-relevant residual remains, and further optional audit has no registered material value. Closure is decision- and cutoff-relative, never global completeness. A resource cap arriving while any coordinate is still open is CANNOT-CHECK-RESOURCE-BOUND --- never rounded down to open, never rounded up to closed.

Reference implementation: `src/rakl/recursive_framework_audit.py`; frozen known-world benchmark: `research/recursive_framework_audit_v1/`.

---

## 9. Action and experiment selection

When a calibrated probability model is justified, a candidate action can be valued as

\[
u(a\mid K_t)=
\frac{
\lambda_Q I(Q;Y_a\mid K_t)
+\lambda_M\operatorname{Sep}(a,\mathcal V_t)
+\lambda_N E[\Delta N_a]
}{\operatorname{Cost}(a)}.
\]

The weights and probability model must be declared. RAKL does not manufacture priors merely to make this expression computable.

Without calibrated probabilities, action selection uses set-valued alternatives such as

\[
\Delta W(a)=W(\mathcal U_t)-\sup_y W(\mathcal U_{t+1}(y,a)),
\]

for an identified-set width functional \(W\), or a worst-case separation score

\[
\operatorname{Sep}_{\min}(a)=
\min_{m_i\neq m_j\in\mathcal V_t}
 d\!\left(P(Y_a\mid m_i),P(Y_a\mid m_j)\right).
\]

The portfolio is non-greedy across exploit, diversify, moonshot and meta-method actions.

### 9.1 Audit computations and value-of-audit

Recursive framework audit is itself an action-selection problem. The audit operator chooses among solve-at-current-representation, refine downward, and challenge an ancestor abstraction; its selection is a pure function of the audited node and residual (§8.1), with priority ordering that fails closed: an invalid evaluator outranks an external trust root, which outranks a resource bound with open audit (CANNOT_CHECK), which outranks revision.

Value-of-audit stopping applies the same discipline as §9: an audit computation is selected when its expected decision improvement justifies its cost, and `STOP_BOUNDED` is licensed only when closure coordinates pass with no material open residual at the registered cutoff. Where calibrated probabilities exist the rule is explicit, \(\mathrm{VOA}(a)=E[U^{*}_{\text{after }a}\mid K]-U^{*}_{\text{now}}-\operatorname{Cost}(a)\), and only a strictly positive value opens the node; utility here is decision quality under the hard invariants, not truth probability. Where they do not exist, the fallback is mandatory trigger, then worst-case decision separation, then registered priority, then cost --- an audit that cannot separate the decision is not opened, and a missing probability is refused rather than replaced by an invented prior. Registered mandatory triggers (invalid evaluator, authority-leak risk, unresolved contradiction, unreachable target, repeated unclassified residual, distinct failed local repairs, interface glue failure, measurement-model failure, high-stakes domain transfer, and a challenger that changes the decision) make an audit obligatory regardless of its computed value. Conformance of these control semantics is instrument evidence only; it is not evidence that recursion improves fresh-task outcomes (that requires the separately frozen RFC-v1 utility benchmark).

---

## 10. Mechanism claims and ancestry

Predictive fit is not mechanism evidence by itself. A mechanistic claim requires a supported ancestry chain such as

\[
\text{building blocks}\to\text{interactions}\to\text{mechanism}
\to\text{mesoscopic state}\to\text{effective law}\to\text{observation/QoI}.
\]

Missing ancestry produces a bound, partial identification or explicit mechanism set rather than an automatic mechanism upgrade.

Constructive invention may propose new states, interactions, equations or observation maps. An invented formalism remains a proposal until limiting cases, dimensional/structural checks, discriminating predictions and target-domain evidence pass.

---

## 11. Memory and bounded epistemic context

Canonical storage and active model context are different resources.

For operation

\[
o=(a,f,q,\gamma,\alpha^*,B),
\]

let \(M(o)\) be mandatory epistemic material, including the active QoI, scope, falsifiers, relevant negative history, contradiction sides, authority prerequisites, mechanism ancestry and evaluator/benchmark identity.

The context compiler solves

\[
C^*(o)=\arg\max_{C\subseteq V(o)}U(C\mid o)
\]

subject to

\[
M(o)\subseteq C,\qquad \operatorname{Tokens}(C)\le B.
\]

If

\[
\operatorname{Tokens}(M(o))>B,
\]

then the result is `CANNOT_COMPILE`. Silent truncation is forbidden.

Compact views are projections with raw-source pointers and erasure metadata. They do not replace canonical evidence.

---

## 12. Semantic and evidence-lineage saturation

For fiber \(f\), let

\[
\mathcal C_t^f=\operatorname{Canon}(\text{retained scoped semantic objects through }t),
\]

and

\[
\Delta_t^f=\mathcal C_t^f\setminus\mathcal C_{t-1}^f.
\]

A semantic round is flat only when \(\Delta_t^f=\varnothing\) after typed deduplication and no new material contradiction, discriminator, data requirement or native residual appears.

Independent-flat credit additionally requires process independence and evidence-lineage independence. Multiple agents or papers sharing the same underlying evidence do not create multiple independent confirmations.

Saturation is a stopping statement about a declared search universe, not a theorem that reality contains no unknown knowledge.

**Semantic saturation is not formulation closure.** A fiber may be semantically saturated within its current formulation (§12) while its formulation is still open: the question, framework, decomposition, interface, measurement or evaluator may each carry a material residual (§8.1). Semantic saturation licenses no claim about the formulation; formulation closure is the separate, cutoff-relative STOP_BOUNDED state of the audit projection, and ancestor supersession stales it.

---

## 13. Experience, challenge learning and method acquisition

A research trajectory element is

\[
x_t=(s_t,a_t,e_{t+1},o_t,c_t).
\]

Experience consolidation proposes

\[
\operatorname{Consolidate}(x_{1:t})\rightarrow\omega^*,
\]

where \(\omega^*\) is a candidate reusable operator. It becomes validated ability only after transfer.

A simple learning-progress signal for method/fiber \(f\) is

\[
LP_t(f)=Q_t(f)-Q_{t-k}(f).
\]

Challenge control can therefore distinguish persistence, strategy switching, help seeking, evidence acquisition, implementation repair, new-operator invention/assimilation and stopping reflection.

Failure attribution precedes self-modification. A missing datum, stochastic miss or implementation defect is not automatically a method-basis failure.

---

## 14. External method assimilation and constructive invention

An external atomic operator contract is

\[
C_m=(I_m,O_m,\gamma_m,A_m,P_m,F_m,\alpha_m^+,\alpha_m^-,T_m,B_m),
\]

encoding inputs, outputs, context, assumptions, preconditions, failure modes, authority it may/may-not create, transitions and benchmark identity.

Assimilation outcomes are scoped and include equivalence to an incumbent, parallel local view, shadow eligibility, block, reject and cannot-check. No external framework reputation is imported as epistemic authority.

Constructive invention searches over candidate theories under a positive-goal contract but remains proposal-only until independently evidenced. Candidate diversity or objective score is not scientific validation.

---

## 15. Governed self-evolution

Let \(M_t\) be the active method and \(M'\) a challenger. Development improvement

\[
\Delta_D=q_D(M')-q_D(M_t)>0
\]

is only local optimization.

For a strong scoped evolution claim, RAKL requires a fresh assurance improvement

\[
\Delta_A=q_A(M')-q_A(M_t)>0,
\]

with matched resources, protected blocking invariants, frozen candidate/evaluator chronology, preserved negative history and an assurance set not adaptively consumed by repeated optimizer-visible reuse.

A development gain with assurance regression is `META_OVERFIT`.

For Class-B method changes,

\[
\operatorname{Promote}(M')
\Rightarrow
\left[\bigwedge_{\lambda\in\Lambda}\operatorname{Pass}_\lambda(M')\right]
\land
\left[\exists q\in Q_{meta}:\Delta q>0\right],
\]

while the evaluator and protected criteria remain outside challenger write authority. Constitutional changes remain proposal-only pending separate governance.

---

## 16. Execution and reproducibility identity

A model invocation is defined by a canonical execution specification containing the task-packet digest, runner contract, generation configuration and nonce. Its identity is

\[
\operatorname{invocation\_id}
=\operatorname{SHA256}(\operatorname{Canon}(\text{execution spec})).
\]

Execution events form a hash chain

\[
h_n=\operatorname{SHA256}(e_n\,\|\,h_{n-1}),
\]

with a content-addressed terminal receipt. A completed identical invocation replays the immutable receipt rather than silently re-executing.

If an invocation was observed as `RUNNING` and may have crossed an external side-effect boundary, recovery fails closed rather than assuming a retry is safe.

Runtime attestation separately binds observed executable bytes and a privacy-preserving fingerprint of declared environment variables. These are reproducibility certificates, not scientific truth.

---

## 17. The 24 method surfaces

The current reference profile owns exactly the following high-impact method surfaces:

1. decomposition;
2. routing;
3. search/query generation;
4. source selection/reliability;
5. claim extraction;
6. ontology/terminology normalization;
7. mathematical/context translation;
8. equivalence/similarity;
9. contextual theory gluing;
10. contradiction diagnosis;
11. gap discovery;
12. experiment/query selection;
13. synthesis;
14. memory;
15. review;
16. benchmarking;
17. authority promotion;
18. saturation/stopping;
19. prompting/context policy;
20. capability shaping;
21. software architecture/execution;
22. research portfolio/tree control;
23. objective evolution;
24. generator transport.

Their machine-checkable contracts live in `src/rakl/method_specs.py` and are validated by `src/rakl/formal_contracts.py`. Each contract explicitly lists inputs, outputs, scope, assumptions, state read/write coordinates, authority effect, non-escalation rules, failure semantics, invariants, mathematical semantics, implementation/tests and empirical open coordinates.

No contract is permitted to hide unresolved empirical work in order to obtain formal closure.

---

## 18. Proof and hostile-test obligations

The core proof/test obligations are:

- **PO-1 Generation non-authority**: proposer text alone cannot increase canonical authority.
- **PO-2 Mechanism non-upgrade**: predictive/observational agreement cannot mint mechanism authority.
- **PO-3 Typed non-escalation**: mixed relation types/scopes cannot create stronger equivalence without a composition license.
- **PO-4 Non-forced gluing**: incompatible local views remain plural/obstructed.
- **PO-5 Negative-history monotonicity**: prior null/refuted states remain addressable.
- **PO-6 Conservative lineage saturation**: shared evidence ancestry cannot count as independent saturation.
- **PO-7 Missing-evidence honesty**: absent required evidence produces blocked/cannot-check outcomes.
- **PO-8 Residual reopening**: a new native residual invalidates the affected local closure certificate.
- **PO-9 Meta-evaluator separation**: a challenger cannot establish its own validity by weakening its evaluator.
- **PO-10 Measurement non-escalation**: measurement equivalence cannot imply mechanism identity.
- **PO-11 Uncertainty-assumption visibility**: uncertainty composition requires its mathematical assumptions to be explicit.
- **PO-12 Formal-closure honesty**: scoped formal closure never implies empirical validation or saturation.

The Round-041 frozen hostile benchmark additionally checks silent context truncation, covariance/transform misuse, runtime identity gaps, registry drift, self-promotion and hidden empirical blockers.

---

## 19. Scoped formal closure theorem for the reference profile

Let \(\mathcal M\) be the registered set of required method surfaces and let \(C(m)\) be the mechanic contract for surface \(m\). Define

\[
\operatorname{ContractValid}(C)
\]

as the conjunction of non-empty typed I/O, scope/context, assumptions, state read/write sets, authority effect, non-escalation rules, failure semantics, invariants, mathematical semantics, implementation/test references and explicit empirical-open coordinates.

Then the executable closure predicate is

\[
\operatorname{FormalClosed}_{\mathcal R}(M)
=\mathbf 1\left[
\forall m\in\mathcal M,\;\exists! C(m):\operatorname{ContractValid}(C(m))
\right].
\]

The predicate is structural. It proves only that, under the current inventory, no registered high-impact surface is unowned or specification-empty. It does **not** prove that any surface performs well on a real scientific project.

A new project residual \(r\) induces

\[
\operatorname{FormalClosed}_{\mathcal R}(M)\rightarrow 0
\]

for the affected scope if \(r\) demonstrates that a necessary surface/operator is absent or that a stated contract is inconsistent. This is the formal bridge between current closure and future self-improvement during the Polymarket trial.

---

## 20. Current empirical-open coordinates

The framework is formally specified enough to begin the controlled real-project trial, but major empirical coordinates remain deliberately open, including:

- same-model hidden missing-operator discovery accuracy;
- real contextual atlas gluing and multi-hop bridge utility;
- matched context-policy efficiency;
- long-horizon memory and skill consolidation;
- independent semantic review quality;
- matched workflow capability shaping;
- fresh-assurance self-evolution;
- real measurement-transform/metrology packets;
- long-running external runner/recovery behavior;
- the complete `polymarket_crypto` descriptive and predictive spot-science programme.

Those are experiments, not missing definitions. The Polymarket project is therefore the next source of native residuals rather than a reason to continue expanding the abstract ontology indefinitely.
