# RAKL Theoretical Framework

Status: **candidate theory layer, v0.1**  
Date: 2026-08-09  
Scope: additive research formalization; this document does **not** amend the RAKL Constitution.

## 0. What RAKL is being formalized as

RAKL is not defined here as a particular multi-agent topology, prompt template, retrieval stack, or language model.

The theoretical object is an **evidence-governed recursive atlas process for scientific inquiry**.

The central distinction is between:

1. a **proposal process**, which may be stochastic, heuristic, LLM-driven, multi-agent, symbolic, or human;
2. an **epistemic state**, which records what is known, unresolved, contradicted, partially identified, and saturated in explicitly scoped form; and
3. an **authority process**, which determines what evidence permits the epistemic state to change.

This formalization is intended to make the slogan

> **LLM proposes; evidence governs**

an executable research principle rather than a prompting preference.

The main publication claim is deliberately narrower than “RAKL invents autonomous science.” Multi-agent science, active experiment design, falsification, provenance, knowledge graphs, scientific perspectivism, partial identification, belief revision, semantic stopping, and local-to-global consistency all have substantial prior traditions. The candidate contribution is the **joint control law by which these ideas are composed into a recursively self-auditing LLM-mediated research method**.

## 1. Research task

A scoped RAKL inquiry is represented as

\[
\mathcal P=(O,\mathcal Q,\Gamma_0,\mathcal E_0,\mathcal B,\Lambda),
\]

where:

- \(O\) is the target object, process, or method;
- \(\mathcal Q\) is the registered set of quantities of interest, decisions, or scientific questions;
- \(\Gamma_0\) is the initial context and observation boundary;
- \(\mathcal E_0\) is the evidence available at the declared cutoff;
- \(\mathcal B\) is the resource budget;
- \(\Lambda\) is the set of blocking epistemic invariants.

The object must be defined before candidates are compared. A change in population, scale, intervention, observation model, assumptions, or consumer may create a different local scientific question even when the same words are used.

## 2. Epistemic state

At research step \(t\), RAKL maintains a set-valued state

\[
K_t=
(\mathcal A_t,\mathcal V_t,\mathcal O_t,\mathcal F_t,
 \mathcal E_t,\mathcal H^-_t,\mathcal S_t).
\]

The components are:

- \(\mathcal A_t\): a **knowledge atlas** of local source and derived charts;
- \(\mathcal V_t\): surviving representations, hypotheses, mechanisms, bounds, and identified sets;
- \(\mathcal O_t\): registered obstructions, contradictions, residuals, and missing coordinates;
- \(\mathcal F_t\): the frontier of open recursive knowledge fibers;
- \(\mathcal E_t\): an evidence/provenance graph, including assumptions and observation processes;
- \(\mathcal H^-_t\): immutable negative history, including nulls, refutations, rejected equivalences, and failed workflows;
- \(\mathcal S_t\): semantic novelty, route coverage, evidence-lineage, and saturation state.

A RAKL state is therefore not one natural-language “best answer.” It may legitimately contain a plural atlas or a set of empirically indistinguishable mechanisms.

## 3. Local charts and projections

A local scientific chart is

\[
C_i=(U_i,\phi_i,\gamma_i,e_i,\alpha_i),
\]

where:

- \(U_i\) is the facet or subdomain of \(O\) described;
- \(\phi_i\) is the representation, vocabulary, model, or measurement projection;
- \(\gamma_i\) is the context tuple;
- \(e_i\) is the evidence packet and provenance;
- \(\alpha_i\) is the authority scope justified by that evidence.

A source observation can be written

\[
y_i=\pi_i(O\mid \gamma_i).
\]

The same object may have many legitimate projections. Consequently, source disagreement is not treated as whole-object competition until overlap, context, semantics, and observation processes are aligned.

A practical context vector can include:

\[
\gamma_i =
(\text{population},\text{scale},\text{regime},\text{units},
\text{observation},\text{assumptions},\text{intervention},
\text{time},\text{QoI}).
\]

Additional coordinates are opened when a residual shows that the current context is insufficient.

## 4. Typed transition maps and relation algebra

For overlapping charts, RAKL may register a transition relation

\[
T_{ij}^{\tau,\sigma}:
\phi_i(U_i\cap U_j)\rightarrow\phi_j(U_i\cap U_j),
\]

where:

- \(\tau\) is a relationship type;
- \(\sigma\) is the licensed scope;
- the edge carries evidence, assumptions, and uncertainty.

Relationship types include, at minimum:

```text
SEMANTIC_EQUIVALENCE
EXACT_ISOMORPHISM
OBSERVATIONAL_EQUIVALENCE
QOI_EQUIVALENCE
MECHANISM_EQUIVALENCE
APPROXIMATE_REPRESENTATION
VERSION_OF
DERIVED_FROM
POSSIBLE_ALIAS
```

The relation algebra obeys a **non-escalation rule**:

> A path composed of weaker, mixed, or differently scoped relations does not create a stronger equivalence unless an explicit composition argument licenses the upgrade.

Approximation is pairwise by default. Error accumulation, regime change, and context dependence prevent automatic transitive closure.

## 5. Alignment, compatibility, contradiction, and obstruction

For comparison layer \(\ell\), define an alignment predicate

\[
\operatorname{Align}_{\ell}(C_i,C_j)
\]

that is true only when the overlap and all context coordinates relevant at layer \(\ell\) are sufficiently aligned or explicitly translated.

A RAKL contradiction is then stronger than textual disagreement:

\[
\operatorname{Contradict}_{\ell}(C_i,C_j)
=
\operatorname{Overlap}(C_i,C_j)
\land
\operatorname{Align}_{\ell}(C_i,C_j)
\land
\neg \operatorname{Compatible}_{\ell}(C_i,C_j).
\]

An **obstruction** is broader. It includes:

- true contradiction after alignment;
- a missing transition map;
- missing context coordinates;
- non-identifiability;
- incompatible observation processes;
- unresolved identity;
- an uncertainty model too weak to compare the charts;
- a scale or regime boundary across which gluing is not licensed.

The synthesis operator therefore has three legitimate outputs:

\[
\operatorname{Glue}(\mathcal A_t)\in
\{
\text{GLOBAL_FORMALISM},
\text{PLURAL_ATLAS},
\text{OBSTRUCTED_OR_IDENTIFIED_SET}
\}.
\]

RAKL never requires a single global model merely because a report format expects one.

## 6. Authority is scoped, not a scalar confidence score

A scientific statement \(c\) has authority only relative to a claim layer and consumer:

\[
\operatorname{Auth}(c,\ell,q,\gamma).
\]

Examples of authority layers include:

```text
SOURCE_PROJECTION
NORMALIZED_CLAIM
RELATION_SUPPORTED
PREDICTIVE_SURVIVOR
MECHANISTICALLY_DERIVED
IDENTIFIED_OR_BOUNDED
DECISION_USABLE
```

These labels should not be interpreted as one universal total order. For example, a statement can be decision-usable for a robust QoI while its microscopic mechanism remains unidentified.

Model confidence, citation count, or repeated LLM agreement is not an authority transition.

## 7. Proposal channel and evidence channel

Let a proposer be

\[
G_\theta(K_t,a_t)\rightarrow\mathcal P_t,
\]

where \(\mathcal P_t\) can contain candidate decompositions, claims, queries, transition maps, hypotheses, experiments, or method changes.

The proposer may be an LLM, a collection of agents, a symbolic program, a human, or a hybrid. Proposal generation has **no direct canonical write authority**.

Evidence is evaluated by a separate verification operator

\[
V(p,e,\gamma)
\rightarrow
\{
\text{SUPPORTED},
\text{REFUTED},
\text{PARTIALLY_IDENTIFIED},
\text{BLOCKED},
\text{CANNOT_CHECK}
\}.
\]

Canonical state changes are produced by

\[
K_{t+1}
=
\mathcal U(K_t,a_t,e_{t+1},V),
\]

not by \(G_\theta\) alone.

This yields the first proof obligation:

**PO-1 — Generation non-authority.**  
Holding the evidence graph and authority rules fixed, arbitrary changes in proposer text cannot by themselves increase the authority of canonical knowledge.

## 8. Negative-history monotonicity

Negative evidence is part of the state rather than discarded scaffolding.

For the append-only negative-history coordinate,

\[
\mathcal H^-_t\subseteq\mathcal H^-_{t+1}.
\]

A later result may supersede the interpretation or scope of a null/refutation, but the earlier event remains addressable with its original context and evidence cutoff.

This prevents a self-improving method from appearing better by forgetting failed ideas, failed experiments, or prior benchmark losses.

## 9. Representation and mechanism

A representation that predicts an observation does not automatically identify a mechanism.

For a mechanistic claim \(m\), RAKL requires a supported ancestry graph of the form

\[
\text{building blocks}
\rightarrow
\text{interactions}
\rightarrow
\text{mechanism}
\rightarrow
\text{mesoscopic state}
\rightarrow
\text{effective law}
\rightarrow
\text{observation/QoI}.
\]

Mechanistic authority is granted only when the required ancestry edges are evidenced or their assumptions are explicit and the unresolved set is reported.

This creates another proof obligation:

**PO-2 — Mechanism non-upgrade.**  
Observational or QoI equivalence alone cannot create `MECHANISM_EQUIVALENCE` or `MECHANISTICALLY_DERIVED` authority.

## 10. Recursive atomic fibers

An unresolved scientific transformation is represented as a fiber

\[
f=(o_f,q_f,\gamma_f,r_f,\operatorname{parent}(f)),
\]

where \(r_f\) is the residual or uncertainty that justifies opening the fiber.

A residual-routing operator

\[
\rho(r,K_t)\subseteq\mathcal F_{t+1}
\]

selects the atomic dimensions capable of producing the residual.

This is the recursive rule:

> Do not expand every possible dimension equally. Recurse into the smallest unresolved transformation whose resolution can change the scientific conclusion or decision.

The same decomposition applies to method steps such as routing, search, extraction, ontology normalization, equivalence detection, experiment design, review, memory, benchmarking, and stopping.

## 11. Action selection

Available actions include:

```text
decompose
search
retrieve source
extract claim
normalize ontology
test equivalence
diagnose contradiction
open gap
request data
design experiment
execute experiment
run adversarial review
synthesize
update memory
benchmark
test saturation
challenge the method
```

When a justified probability model exists, an action can be valued by decision- or QoI-relevant information gain:

\[
u(a\mid K_t)=
\frac{
\lambda_Q I(Q;Y_a\mid K_t)
+
\lambda_M\,\operatorname{Sep}(a,\mathcal V_t)
+
\lambda_N\,\mathbb E[\Delta N_a]
}{
\operatorname{Cost}(a)
}.
\]

When calibrated probabilities are not available, RAKL must not fabricate them. It can instead use set-valued quantities such as expected identified-set shrinkage, worst-case mechanism separation, or elimination of explicit obstructions.

Action selection is constrained by blocking validity invariants, and the research portfolio remains non-greedy across exploit, diversify, moonshot, and meta-RAKL allocations.

RAKL does **not** claim that active learning, Bayesian experimental design, POMDP planning, or surprise-driven exploration are novel. The claim is that these acquisition policies are subordinate modules acting on a typed evidence-governed epistemic state rather than being the epistemic authority themselves.

## 12. Outcome semantics

RAKL distinguishes epistemic outcomes that many research agents collapse into success/failure.

### Positive
Evidence supports a claim at a declared scope. Authority may increase only to the evidenced layer.

### Null
A registered effect or discriminator is not observed. The null enters negative history and can shrink or preserve the survivor set.

### Refuted
Evidence violates a frozen falsifier. The affected candidate is removed from the survivor set for that scope, while the refutation is preserved.

### Partially identified
Evidence narrows the admissible set but does not select one theory/mechanism. The identified set is itself the valid output.

### Blocked
A required assumption, datum, source, permission, or valid evaluator is unavailable. No evidential upgrade is permitted.

### Transport failure
Retrieval, compute, API, or execution infrastructure fails. This is an operational outcome, not scientific evidence for or against the hypothesis.

## 13. Semantic saturation

For fiber \(f\), let

\[
\mathcal C_t^f
=
\operatorname{Canon}(\text{retained semantic objects through }t),
\]

where canonicalization is typed and scoped.

The semantic increment is

\[
\Delta_t^f=
\mathcal C_t^f\setminus\mathcal C_{t-1}^f.
\]

A round is flat only after deduplication when \(\Delta_t^f=\varnothing\) and it creates no new material contradiction, discriminator, data requirement, or native residual.

A strong scoped saturation certificate additionally requires:

1. registered route coverage;
2. a registered same-context plateau;
3. genuinely process-independent flat rounds;
4. evidence-lineage-qualified independence rather than paper/agent count;
5. no unregistered contradiction;
6. frozen semantic and evidence cutoffs.

A new native residual invalidates the affected local certificate and reopens the fiber.

Saturation is a stopping claim about the **current knowledge-search process**, not a proof that reality contains no unknown facts.

## 14. Self-RAKL as a second-order research process

Let \(M_t\) denote the active RAKL method. Self-RAKL treats \(M_t\) as another research object.

A proposer may generate a challenger \(M'\), but activation requires a frozen evaluation packet \(B\), protected blocking criteria \(\Lambda\), and an evaluator outside the challenger's write authority.

For a Class-B method change,

\[
\operatorname{Promote}(M')
\Rightarrow
\left[
\bigwedge_{\lambda\in\Lambda}\operatorname{Pass}_\lambda(M')
\right]
\land
\left[
\exists q\in\mathcal Q_{\text{meta}}:
\Delta q(M',M_t)>0
\right].
\]

A candidate cannot establish the validity of a weakened evaluator merely by causing that evaluator to pass.

Constitutional changes remain proposals requiring separate amendment governance.

## 15. Theory-level invariants and proof obligations

The following are not claims that RAKL is scientifically correct in every domain. They are properties the formalism and implementation should be able to prove or falsify.

| ID | Invariant / obligation | Required kind of evidence |
|---|---|---|
| PO-1 | Proposal generation alone cannot increase canonical authority. | Formal transition definition + hostile implementation tests |
| PO-2 | Predictive/observational agreement cannot silently create mechanistic authority. | Typed relation algebra + known-answer counterexamples |
| PO-3 | Mixed relation types/scopes cannot yield a stronger transitive equivalence without an explicit composition license. | Algebraic proof + metamorphic tests |
| PO-4 | Incompatible aligned local charts remain an obstruction or identified set rather than being forced into one global model. | Formal gluing rule + known-answer plural worlds |
| PO-5 | Null/refuted history remains addressable after all later updates. | Append-only provenance invariant + replay test |
| PO-6 | Adding evidence of shared ancestry/aliasing cannot manufacture extra independent saturation credit. | Lineage theorem/algorithm + hostile alias worlds |
| PO-7 | Missing external evidence yields `CANNOT_CHECK`/partial authority rather than model-confidence substitution. | Fail-closed validator tests |
| PO-8 | A native residual reopens every saturation certificate whose scope can produce that residual. | Scope-routing rule + long-horizon benchmark |
| PO-9 | A self-modifying challenger cannot gain authority solely from an evaluator it controls. | Trusted-evaluator boundary + evaluator-gaming benchmark |

Some obligations can become mathematical propositions once all operators are fully specified. Others are empirical properties of the research system.

## 16. Candidate novelty envelope

The publication claim should be evaluated at two levels.

### 16.1 Ingredients that RAKL should explicitly treat as prior art

RAKL should not claim priority for:

- perspectival or plural scientific representation;
- local-to-global consistency or obstruction ideas;
- belief revision;
- partial identification and decision under ambiguity;
- knowledge graphs and ontology harmonization;
- provenance and evidence tracing;
- multi-agent scientific workflows;
- iterative hypothesis/experiment loops;
- falsification;
- active learning, Bayesian design, surprise search, or POMDP planning;
- semantic stopping in iterative agents;
- self-improving software or agents in general.

### 16.2 Candidate method-level contribution

The candidate contribution is the **integrated epistemic transition discipline** consisting of all of the following:

1. **projection/context before competition**;
2. a **typed local-view atlas** with explicit transition maps and non-forced gluing;
3. a **scoped authority system** separating representation, prediction, mechanism, identification, and decision authority;
4. an **LLM proposal channel with no direct canonical authority**, separated from the evidence/verification channel;
5. **residual-driven recursive atomic fibers**, including recursion over the method itself;
6. **negative-history-preserving updates**;
7. **semantic and evidence-lineage-aware saturation**;
8. **pre-registered, externally governed self-modification**.

The novelty claim is weakened or refuted if prior work, before the registered evidence cutoff, is found to implement a semantically equivalent integrated method under different terminology.

The paper should therefore avoid “first system to…” language unless an independent novelty review supports it.

## 17. Closest prior traditions and what remains different

The theoretical neighborhood currently includes:

- scientific perspectivism/model pluralism: supports partial, situated representations;
- sheaf/local-to-global methods: formalize local compatibility and obstruction;
- belief revision: formalizes rational state change under new information;
- partial identification: legitimizes identified sets instead of arbitrary point choices;
- goal-oriented experimental design and belief-space planning: optimize informative actions;
- autonomous scientific agents: automate hypothesis, literature, experimentation, and reporting;
- falsification agents: enforce statistical or experimental challenges to hypotheses;
- provenance-aware scientific knowledge systems: normalize and trace literature-derived knowledge;
- grounded-versus-belief planning systems: separate predictions from facts needed for commitment.

RAKL's theory must therefore earn its contribution through the **joint state representation, authority transitions, recursive residual policy, stopping certificate, and self-governance**, not through renaming any one of these traditions.

## 18. Empirical predictions of the theory

Relative to agent workflows that lack the corresponding control, RAKL predicts lower rates of:

- false contradictions caused by context mismatch;
- false equivalence caused by notation or representation confusion;
- false mechanism claims from predictive fit;
- unsupported canonical claims;
- loss of null/refuted evidence over long runs;
- premature stopping caused by paper-count or same-context convergence;
- duplicated “independent” evidence caused by shared lineage;
- self-evaluation gaming during method improvement.

RAKL may incur additional time, token, and verification cost. A publishable result therefore requires showing that the epistemic gains survive cost-matched comparisons or are justified by blocking-validity improvements.

## 19. Falsifiers for the RAKL method paper

The central method claim should be considered weakened or refuted if any of the following occurs:

1. a prior system is shown, after semantic normalization, to implement the same integrated epistemic control law;
2. RAKL fails known-answer worlds for its defining invariants;
3. ablating the proposed epistemic controls does not measurably worsen the relevant failure modes;
4. apparent gains disappear after controlling for base model, tools, search budget, or evaluator access;
5. RAKL mainly improves prose/reports while process-level evidence handling remains unchanged;
6. the method's stopping certificate systematically terminates before materially new independent semantic objects are found;
7. self-RAKL repeatedly improves benchmark scores by evaluator adaptation rather than research-method improvement;
8. the overhead of the method dominates while producing no blocking-validity or decision-quality benefit.

These falsifiers must not be weakened after observing results.

## 20. Paper-level scientific claim

The defensible target claim is:

> **RAKL is a candidate formal scientific research methodology for LLM-mediated inquiry in which language models propose research actions and representations, while a typed, context-scoped, provenance-bearing epistemic state and externally governed verification process determine what can become knowledge, what remains partially identified, where inquiry recurses, and when a local research fiber may stop.**

The paper must separately establish:

1. **conceptual distinctness** from semantically equivalent prior methods;
2. **formal coherence** of the state/update/stopping rules;
3. **implementation fidelity** to the formal rules;
4. **empirical utility** on known-answer, adversarial, and native scientific tasks.

Only the conjunction supports a strong “new scientific research method” claim.
