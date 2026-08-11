# RAKL: An Evidence-Governed Recursive Atlas Method for Scientific Research with Large Language Models

**Methods manuscript and preregistered evaluation draft**  
**Author:** Sze Chun Yiu  
**Status:** formal-method content substantially complete; headline empirical result slots remain blocked until exact machine-readable receipts exist.

## Abstract

Large language models can search scientific literature, generate hypotheses, execute analyses and draft research reports, and recent systems have demonstrated increasingly broad autonomous scientific workflows. Their fluency, however, does not itself determine which generated statements deserve scientific authority, whether apparently conflicting studies actually share a context, whether predictive agreement identifies a mechanism, or whether a self-modifying research agent has improved beyond the benchmark it optimized. We introduce **RAKL (Recursive Atomic Knowledge Lattices)**, a candidate evidence-governed methodology for LLM-mediated scientific inquiry. RAKL represents research as controlled updates to an external contextual **Knowledge Atlas** whose local charts carry evidence, scope and scientific-authority certificates. Typed transition maps separate representation, prediction, mechanism, identification and decision claims; incompatible local views can remain a plural atlas or identified set rather than being forcibly merged. Residuals open recursive atomic research fibers, negative evidence is immutable history, and semantic stopping depends on deduplicated novelty and evidence-lineage independence. A bounded context compiler exposes only the epistemically necessary working set to the LLM, allowing the scientific archive to grow without requiring the prompt to grow with it. RAKL also applies its own method to method change: challenge learning, external-method assimilation and constructive invention can generate candidate improvements, but transferable self-evolution requires frozen development tests, protected evaluation and fresh assurance. The reference implementation assigns explicit contracts to 24 research-method surfaces and is evaluated against frozen known-answer and hostile worlds. We preregister two headline empirical tests: whether RAKL improves the scientific behavior of the same base LLM under matched resources, and whether RAKL can diagnose and repair its own missing method capabilities with transfer to fresh tasks. A real quantitative-finance trial will use the framework to construct a descriptive and predictive model of short-horizon cryptocurrency spot movement, with Polymarket strictly downstream of spot-model validation. **[[RESULT:SOFTWARE_VALIDATION]] [[RESULT:MATCHED_WORKFLOW]] [[RESULT:SELF_EVOLUTION]] [[RESULT:SPOT_SCIENCE]]**

## Introduction

Scientific-agent systems are rapidly moving beyond question answering. Co-Scientist uses multi-agent generation, reflection, ranking and hypothesis evolution and has been experimentally validated in biomedical applications [@gottweis2026coscientist]. Robin integrates literature search, hypothesis generation, experiment proposal and data analysis [@ghareeb2026robin]. The AI Scientist-v2 automates experiment design, execution, analysis and manuscript generation using agentic tree search [@yamada2025aiscientistv2], while Kosmos uses a structured world model to sustain long scientific investigations [@mitchener2025kosmos]. SciAgents combines multi-agent reasoning with ontological knowledge graphs [@ghafarollahi2024sciagents], and PaperQA2 demonstrates strong evidence-grounded literature synthesis and contradiction discovery [@skarlinski2024paperqa2]. These systems substantially raise the bar for any claim of novelty based only on search, hypothesis generation, multi-agent debate, long-horizon execution or structured scientific memory.

The remaining problem is more specific. A scientific research system must decide not only *what to generate next* but *what a piece of evidence is allowed to change*. Two papers may use the same words while studying different populations, scales or observation processes. Two models may be observationally indistinguishable while implying different mechanisms. A model can predict a decision-relevant outcome without identifying the underlying generator. Several papers or agents can appear independent while inheriting the same evidence. A null result may be forgotten after enough iterations. A research loop may stop because its token or action budget is exhausted rather than because the scientific search has become semantically flat. A self-modifying agent may improve the very benchmark repeatedly exposed during optimization and call that improvement self-evolution.

We treat these as failures of **epistemic state transition**. The central question is

\[
\textit{given a proposal and new evidence, what scoped change to scientific state is licensed?}
\]

RAKL addresses this question by separating a stochastic proposal process from a persistent evidence-governed state. The language model may generate decompositions, hypotheses, mappings, experiments or method changes, but canonical scientific authority changes only through explicit verification and governance. Scientific knowledge is represented as a contextual atlas of local views rather than a single accumulating answer. This makes several outcomes first class: a global formalism when local views genuinely cohere, a plural atlas when useful local descriptions remain context-dependent, and an identified or obstructed set when the evidence cannot select one global object.

RAKL is recursive in two dimensions. First, unresolved residuals open smaller research fibers until the uncertainty that can change the target conclusion is isolated. Second, the same method can be applied to RAKL itself. Failures can reveal weaknesses in the current method basis; external frameworks can contribute atomic candidate operators; constructive invention can propose operators that do not yet exist. None of these proposal routes is allowed to promote itself. A method change earns only scoped self-evolution evidence when improvement transfers to fresh assurance while protected validity criteria remain unchanged.

A second engineering requirement follows from this architecture. If an LLM had to reread the complete scientific history on every step, an ever-growing Knowledge Atlas would make the method unusable for ordinary models. RAKL therefore separates canonical archive growth from active context. The archive can remain append-only and multi-resolution, while a context compiler selects a bounded working projection containing mandatory epistemic material such as the current target, assumptions, falsifiers, relevant negative history, contradiction sides, mechanism ancestry and evaluator identity. Mandatory overflow returns `CANNOT_COMPILE`; it is not repaired by silent truncation.

This paper makes five candidate contributions.

1. **A projection-first scientific state.** Scientific sources are represented as scoped local charts. Context and observation are aligned before claims compete.
2. **An obstruction-aware transition calculus.** Typed maps separate local compatibility, path coherence, global existence and global identifiability. Non-gluing is retained as information.
3. **A multi-axis scientific-authority discipline.** Grounding, representation, mechanism, identification and decision authority are separate certificate coordinates with explicit non-escalation rules.
4. **A recursive, bounded and self-auditing research control system.** Residual-driven fibers, immutable negative history, evidence-lineage saturation, bounded epistemic contexts, metacognitive challenge learning and governed method evolution are coupled in one state-update architecture.
5. **A falsifiable evaluation programme.** The method is assessed using selective known-answer ablations, matched same-model research workflows, fresh-assurance self-evolution and a real quant-finance scientific problem rather than only final-answer quality.

We do **not** claim novelty for multi-agent scientific workflows, knowledge graphs, local-to-global mathematics, provenance, memory tiers, prompt compression, active experiment design, causal discovery, falsification, program evolution or reusable agent skills in isolation. The candidate contribution is the evidence-governed composition rule connecting them.

## Related work and novelty boundary

### Autonomous scientific agents

Current AI-scientist systems already cover much of the workflow that earlier generations of RAKL might otherwise have claimed as distinctive. Co-Scientist continuously generates, critiques and evolves hypotheses and scales scientific reasoning with test-time compute [@gottweis2026coscientist]. Robin integrates literature and data-analysis agents across an experimental discovery cycle [@ghareeb2026robin]. The AI Scientist-v2 performs end-to-end machine-learning research with experiment-manager tree search [@yamada2025aiscientistv2]. Kosmos uses a structured shared world model to preserve coherence over long scientific runs [@mitchener2025kosmos]. SciAgents combines ontological knowledge graphs with multi-agent exploration [@ghafarollahi2024sciagents], and PaperQA2 demonstrates that agentic evidence retrieval and synthesis can reach or exceed expert performance on several literature tasks [@skarlinski2024paperqa2]. Accordingly, RAKL is not positioned as the first system to automate science, maintain structured research state, find contradictions, or iteratively improve hypotheses.

### Self-improving agents and reusable skills

Self-modification and skill evolution are also established research directions. Darwin Gödel Machine iteratively modifies agent code and empirically selects improved descendants [@zhang2025dgm]. EvoSkill analyzes failures and evolves reusable skills while retaining a Pareto frontier under held-out validation [@alzubi2026evoskill]. SkillFoundry extracts executable skills from heterogeneous scientific resources and evolves the resulting library [@shen2026skillfoundry]. EvoAgentBench argues that self-evolution should be measured by procedural ability transfer rather than aggregate improvement on previously exposed tasks [@gao2026evoagentbench], and the recent FinEvo-Bench studies longitudinal self-evolution in professional financial workflows [@deng2026finevobench]. RAKL therefore does not claim novelty for recursive code change, failure-driven skill creation, held-out skill selection, or transfer evaluation by themselves. Its narrower claim is that method improvement is itself treated as a scientific claim with protected evidence, authority and assurance boundaries.

### Prediction, mechanism and causal reasoning

CausaLab explicitly evaluates both task prediction and recovery of a hidden structural causal mechanism and shows that high predictive performance can coexist with substantially weaker mechanism recovery [@yang2026causalab]. This supports a central RAKL non-escalation rule: observational or predictive success cannot silently mint mechanism authority. RAKL generalizes this separation beyond causal graphs by treating representation, mechanism, identification and decision authority as different certificate coordinates.

### Local views, provenance and plural knowledge

Local-to-global consistency is a longstanding mathematical idea. Recent work uses sheaf conditions to formalize multi-view consistency in systems engineering [@gibson2026sheaves]. RAKL does not claim to invent gluing mathematics; it uses local-to-global reasoning as one projection inside a broader scientific update discipline and, crucially, allows an explicit `PLURAL_ATLAS` or `OBSTRUCTED_OR_IDENTIFIED_SET` output when gluing prerequisites fail. Provenance research similarly distinguishes attributed statements from global factual commitment. DEC, for example, groups provenance-homogeneous claims into cognitive worlds so disagreement need not collapse into inconsistency [@vitali2026provenance]. RAKL's candidate contribution is the integration of such scoped provenance with typed scientific authority, mechanism ancestry, residual routing and governed state updates.

### Memory and context efficiency

Hierarchical external memory and context reduction are also prior art. MemGPT frames extended LLM operation as virtual memory management [@packer2023memgpt]. RAPTOR organizes recursive summaries into a multi-resolution retrieval tree [@sarthi2024raptor]. LLMLingua compresses prompts to reduce inference cost [@jiang2023llmlingua], while RECOMP performs selective compression of retrieved evidence and can omit irrelevant augmentation [@xu2023recomp]. RAKL therefore does not claim hierarchical memory or compression as novel. Its narrower context contribution is a mandatory epistemic retention contract: negative history, falsifiers, contradiction sides, authority prerequisites and relevant mechanism ancestry cannot be dropped merely because a compression policy ranks them low; if they do not fit, the operation fails closed.

## Formal method

### Task and researcher state

A scoped inquiry is

\[
\mathcal P=(O,\mathcal Q,\Gamma_0,\mathcal E_0,\mathcal B,\Lambda),
\]

where \(O\) is the target object, \(\mathcal Q\) the registered scientific questions or quantities of interest, \(\Gamma_0\) the context and observation boundary, \(\mathcal E_0\) the evidence available at the declared cutoff, \(\mathcal B\) the resource budget and \(\Lambda\) the blocking epistemic invariants.

The functional researcher state is

\[
\mathfrak R_t=(K_t,\mathcal Z_t,\Omega_t,\Pi_t,\mathcal G_t,\mathcal M_t,\mathcal X_t,\mathcal R_t),
\]

separating the canonical scientific state \(K_t\), surviving explanatory/world models \(\mathcal Z_t\), reusable research operators \(\Omega_t\), executive policy \(\Pi_t\), research agenda \(\mathcal G_t\), metacognitive state \(\mathcal M_t\), experience/transfer history \(\mathcal X_t\), and resources \(\mathcal R_t\).

The epistemic state is

\[
K_t=(\mathcal A_t,\mathcal T_t,\mathcal V_t,\mathcal E_t,\mathcal U_t,
\mathcal O_t,\mathcal F_t,\mathcal H^-_t,\mathcal S_t,\mathcal G_t^K).
\]

The coordinates respectively store the Knowledge Atlas, typed transitions, survivor set, evidence/provenance graph, uncertainty and identified sets, obstructions/residuals, recursive fibers, negative history, saturation state and protected governance identities. The full formal specification and derivations are given in `docs/FORMAL_SYSTEM_SPECIFICATION.md`.

### Local scientific charts and projection before competition

A local chart is

\[
C_i=(U_i,\phi_i,\gamma_i,e_i,\alpha_i).
\]

The same latent object can legitimately produce different observations under different populations, scales, measurement operators, assumptions or QoIs. A source observation can therefore be written

\[
y_i=\pi_i(O\mid\gamma_i).
\]

RAKL first asks whether two local claims describe overlapping objects under sufficiently aligned contexts. Only then can their compatibility or contradiction be evaluated. This prevents a common literature-synthesis failure in which papers are ranked as mutually exclusive theories despite studying different projections.

### Typed transitions, contradiction and non-forced gluing

For overlapping charts, a transition has the form

\[
T_{ij}^{\tau,\sigma}:\phi_i(U_i\cap U_j)\rightarrow\phi_j(U_i\cap U_j),
\]

where \(\tau\) is the relation type and \(\sigma\) the licensed scope. Transitions carry assumptions, evidence and error semantics. Composition requires domain/range compatibility, a licensed relation composition, non-empty scope intersection, valid role handoffs, traceable evidence lineage and an explicit error-composition law where approximation is present.

At comparison layer \(\ell\), contradiction is

\[
\operatorname{Contradict}_{\ell}(C_i,C_j)=
\operatorname{Overlap}(C_i,C_j)
\land \operatorname{Align}_{\ell}(C_i,C_j)
\land \neg\operatorname{Compatible}_{\ell}(C_i,C_j).
\]

A gluing trial separates four questions: whether local overlaps are compatible, whether transition paths/cycles are coherent, whether a global object exists, and whether it is uniquely identified. Consequently,

\[
\operatorname{Glue}(\mathcal A)
\in\{\text{GLOBAL_FORMALISM},\text{PLURAL_ATLAS},
\text{OBSTRUCTED_OR_IDENTIFIED_SET}\}.
\]

RAKL therefore does not force a single synthesis simply because a reporting interface expects one.

### Scientific authority is multi-axis

For claim \(c\), scientific authority is represented as

\[
\alpha(c)=(G_c,R_c,M_c,I_c,D_c),
\]

covering grounding/provenance, representation/relation, mechanism ancestry, identification/bounding and decision/QoI usability. Coordinates are scoped certificate sets rather than one confidence score. Under compatible scope, \(\alpha_1\preceq\alpha_2\) only if each relevant certificate coordinate of \(\alpha_1\) is contained in or entailed by the corresponding coordinate of \(\alpha_2\).

The structure is a partial order, not automatically a mathematical lattice. Incompatible assumptions, populations or observation operators can obstruct a join. Cross-axis non-escalation rules include

\[
R\not\Rightarrow M,\qquad
D\not\Rightarrow M,\qquad
M\not\Rightarrow I.
\]

Thus observational equivalence cannot establish mechanism identity, robust decision performance cannot establish the microscopic mechanism, and mechanistic plausibility cannot establish point identification. Provenance and citation count likewise do not create truth or independent evidence.

### Proposal, evidence and canonical update

The proposal channel is

\[
G_\theta(K_t,a_t)\rightarrow\mathcal P_t,
\]

where the proposer can be an LLM, symbolic program, human or hybrid. Proposal generation has no direct canonical authority.

Verification is

\[
V(p,e,\gamma)
\rightarrow
\{\text{SUPPORTED},\text{REFUTED},\text{PARTIALLY_IDENTIFIED},
\text{BLOCKED},\text{CANNOT_CHECK}\}.
\]

Canonical scientific state changes through

\[
K_{t+1}=\mathcal U(K_t,a_t,e_{t+1},V,\mathcal G_t^K),
\]

subject to protected invariants. In particular,

\[
\mathcal H^-_t\subseteq\mathcal H^-_{t+1}.
\]

A later result can supersede the interpretation or scope of a null/refutation, but the historical event and original evidence remain addressable.

### Mechanism ancestry

A representation that predicts an observation is not automatically a mechanism. Mechanistic authority requires a supported ancestry such as

\[
\text{building blocks}\to\text{interactions}\to\text{mechanism}
\to\text{mesoscopic state}\to\text{effective law}\to\text{observation/QoI}.
\]

If available observations cannot distinguish several mechanisms, the correct scientific output is the identified set or bound, not a model-selected mechanism label.

### Measurement, coordinate translation and uncertainty

An observation is represented as

\[
y=h(O,\eta,\gamma)+\epsilon,
\]

where \(\eta\) includes instrument and calibration state. This prevents two measurements from being equated solely because their numerical outputs have similar names.

For an affine transform \(Y=AX+b\),

\[
\mu_Y=A\mu_X+b,
\qquad
\Sigma_Y=A\Sigma_XA^\top.
\]

The covariance law follows directly from the definition of covariance and requires no independence assumption when the full covariance matrix is supplied. For a differentiable nonlinear map \(g\), RAKL can use the first-order approximation

\[
\Sigma_{g(X)}\approx J_g\Sigma_XJ_g^\top,
\]

but the differentiability and local-linearization assumptions remain explicit. Root-sum-square combination of scalar uncertainties is permitted only with an explicit independence/uncorrelatedness witness. These operations are executable in the reference implementation rather than being prose-only metrology rules.

### Residual-driven decomposition, support paths and epistemic cuts

An atomic research fiber is

\[
f=(o_f,q_f,\gamma_f,r_f,\operatorname{parent}(f)),
\]

where \(r_f\) is the residual that justifies opening the fiber. RAKL does not recursively expand every possible dimension. It seeks the smallest unresolved transformation capable of changing the scientific target.

For target \(\tau=(q,\alpha^*,\gamma)\), the method searches for an authority-valid support subgraph or hypergraph. If no licensed path exists, RAKL seeks a minimal or otherwise cost-efficient epistemic cut

\[
B^*_{\tau}=\arg\min_B \operatorname{Cost}(B)
\]

subject to every admissible support route intersecting \(B\). A cut can expose missing evidence, context, measurement, transition, mechanism, formal lemma or method operator. Detecting a gap, identifying the missing operator family and showing fresh transfer of that operator are treated as different evidential events.

### Experiment and query selection

When calibrated probabilities exist, a candidate action can be scored using decision/QoI information gain, mechanism separation and semantic novelty per cost:

\[
u(a\mid K_t)=
\frac{
\lambda_Q I(Q;Y_a\mid K_t)+
\lambda_M\operatorname{Sep}(a,\mathcal V_t)+
\lambda_N E[\Delta N_a]
}{\operatorname{Cost}(a)}.
\]

When calibrated probabilities are not available, RAKL does not fabricate them. It instead uses set-valued criteria such as worst-case mechanism separation or expected identified-set shrinkage. Research allocation remains non-greedy across exploit, diversify, moonshot and meta-method branches.

### Bounded epistemic context

For operation

\[
o=(a,f,q,\gamma,\alpha^*,B),
\]

let \(M(o)\) denote the mandatory epistemic material, including the current target and scope, assumptions, falsifiers, relevant negative history, contradiction sides, mechanism ancestry and evaluator/benchmark identity. The context compiler solves

\[
C^*(o)=\arg\max_{C\subseteq V(o)}U(C\mid o)
\]

subject to

\[
M(o)\subseteq C,
\qquad
\operatorname{Tokens}(C)\le B.
\]

If \(\operatorname{Tokens}(M(o))>B\), the result is `CANNOT_COMPILE`. Compact summaries are reconstructable projections with source pointers and erasure metadata, not promoted truth. This architecture deliberately builds on, rather than claims invention of, hierarchical memory and prompt compression [@packer2023memgpt; @sarthi2024raptor; @jiang2023llmlingua; @xu2023recomp].

### Semantic saturation

For fiber \(f\), define

\[
\mathcal C_t^f=\operatorname{Canon}(\text{retained scoped semantic objects through }t)
\]

and

\[
\Delta_t^f=\mathcal C_t^f\setminus\mathcal C_{t-1}^f.
\]

A round is flat only after typed deduplication when \(\Delta_t^f=\varnothing\) and it creates no material contradiction, discriminator, data requirement or native residual. Independent flatness additionally requires process and evidence-lineage independence. A new native residual reopens the affected fiber. Saturation is therefore a stopping claim about a registered search universe, not a proof that reality contains no unknown facts.

## Learning and evolving the research method

### Challenge Learning

RAKL's metacognitive layer distinguishes diagnosing a weakness from choosing how to learn from it. A project failure is first attributed to a candidate cause such as missing evidence, implementation defect, stochastic uncertainty, poor strategy, ontology gap or method-basis gap. The Challenge Learning controller can recommend persistence, strategy switching, independent help, evidence acquisition, implementation repair, discriminating tests, operator invention/assimilation or stopping reflection. These are control recommendations only; they do not promote a repair.

A learning-progress signal

\[
LP_t(f)=Q_t(f)-Q_{t-k}(f)
\]

can help distinguish useful persistence from flat repeated effort. Low competence with positive learning progress favors continued practice; low competence with flat progress is evidence for strategy change rather than indefinite repetition.

### Learning from external frameworks

RAKL can decompose an external method into an atomic operator contract

\[
C_m=(I_m,O_m,\gamma_m,A_m,P_m,F_m,\alpha_m^+,\alpha_m^-,T_m,B_m),
\]

which records typed inputs/outputs, valid context, assumptions, preconditions, failures, authority it may and may not create, transitions and benchmark identity. Candidate operators can be equivalent to an incumbent, remain parallel under different contexts, enter shadow evaluation, or be blocked/rejected. RAKL thus attempts to accumulate **validated compatible capabilities**, not to import a framework's reputation or force all methods into one global pipeline.

### Constructive invention

When the current method or theory basis cannot resolve a registered residual, RAKL can construct candidate new formal objects. Invention is deliberately proposal-only. A candidate theory must state its variables, interactions, observation map, limiting cases, assumptions, predictions and falsifiers before target evidence can authorize it. A theory that fits an exploratory dataset but cannot survive structural checks or fresh target validation remains an invention candidate rather than scientific knowledge.

### Governed self-evolution

For incumbent method \(M_t\) and challenger \(M'\), a development improvement

\[
\Delta_D=q_D(M')-q_D(M_t)>0
\]

is local optimization. Strong scoped evolution evidence additionally requires fresh assurance improvement

\[
\Delta_A=q_A(M')-q_A(M_t)>0,
\]

with frozen candidate/evaluator chronology, matched resources, preserved negative history and all blocking validity criteria clean. Repeated optimizer-visible exposure consumes an assurance set's evidential value, consistent with the broader adaptive-data-analysis problem [@dwork2015reusable]. Development gain accompanied by assurance regression is classified `META_OVERFIT`.

This design is intentionally narrower than generic recursive self-improvement. DGM, EvoSkill, SkillFoundry and EvoAgentBench already demonstrate or benchmark important forms of agent modification, reusable skill acquisition and transfer [@zhang2025dgm; @alzubi2026evoskill; @shen2026skillfoundry; @gao2026evoagentbench]. RAKL's claim is that method change remains subordinate to the same evidence and authority rules as any other scientific claim.

## Reproducible execution and formal closure

A model invocation binds the task-packet digest, runner contract, generation configuration and execution nonce into

\[
\operatorname{invocation\_id}
=\operatorname{SHA256}(\operatorname{Canon}(\text{execution spec})).
\]

Execution events form an append-only hash chain and terminal outputs are content-addressed receipts with proposal-only authority. Ambiguous interrupted execution does not automatically retry after a possible external side effect. Runtime attestation separately records executable bytes, Python/platform identity and a privacy-preserving fingerprint of the explicitly declared environment.

The present reference profile registers exactly 24 high-impact method surfaces: decomposition; routing; search/query generation; source selection/reliability; claim extraction; ontology/terminology normalization; mathematical/context translation; equivalence/similarity; contextual theory gluing; contradiction diagnosis; gap discovery; experiment/query selection; synthesis; memory; review; benchmarking; authority promotion; saturation/stopping; prompting/context policy; capability shaping; software architecture/execution; research portfolio/tree control; objective evolution; and generator transport.

For method surface \(m\), let \(C(m)\) be its formal contract. Scoped formal closure is

\[
\operatorname{FormalClosed}_{\mathcal R}(M)
=\mathbf 1\!\left[
\forall m\in\mathcal M,\;\exists!C(m):\operatorname{ContractValid}(C(m))
\right].
\]

`ContractValid` requires typed inputs/outputs, context, assumptions, state read/write sets, authority effect, non-escalation rules, failure semantics, invariants, mathematical semantics, implementation/test references and explicit empirical-open coordinates. This is a structural software/formal claim only. It does not establish empirical performance or framework saturation; a real-project residual that exposes a missing necessary surface reopens the affected closure coordinate.

## Quantitative evaluation model

We evaluate RAKL with a context-indexed competence vector

\[
\mathbf Q(A,M;d,f,t,b,c)=(V,E,D,X,P,G,L,R,C),
\]

where the coordinates represent epistemic validity, evidence uptake/revision, discovery, explanatory/mechanistic competence, experiment planning, metacognition/gap discovery, learning/self-evolution, robustness/reproducibility and computational/context efficiency. The vector is not collapsed into one compensatory score when doing so would allow predictive or efficiency gains to hide a blocking validity failure.

Example process metrics include:

- unsupported authority-upgrade rate;
- false contradiction and false merge rates;
- counterevidence uptake after decisive refutation;
- negative-history recall;
- hidden-gap/operator precision and recall;
- experiment discrimination or identified-set shrinkage per cost;
- false-saturation rate;
- active-context tokens and mandatory-context recall;
- fresh-assurance gain and meta-overfit frequency.

## Preregistered evaluation programme

### Experiment 1: known-answer and hostile scientific worlds

The first layer uses synthetic/constructed worlds in which the correct relation, context, mechanism status, evidence lineage, missing information or failure state is known. These tests answer whether the implementation obeys the formal contract rather than whether RAKL is empirically superior in science.

Selective ablations are important. Removing context alignment should preferentially increase false contradictions; removing the authority poset should increase mechanism/identification leakage; removing negative history should resurrect refuted routes; removing lineage-aware saturation should create false independence; removing metacognitive completeness should reduce hidden-gap detection. If an ablation does not selectively worsen the failure mode the mechanism was designed to prevent, that mechanism's contribution is weakened.

**Current software-contract result:** [[RESULT:SOFTWARE_VALIDATION]]

### Experiment 2: matched scientific-research workflows

The same base LLM will be evaluated under matched evidence cutoff, tools, hidden outcomes and resource budget across:

1. direct strong prompting;
2. retrieval-augmented LLM research;
3. a strong generic agentic research workflow;
4. fixed RAKL;
5. self-evolving RAKL.

The primary comparison is not only final answer accuracy. We will measure hidden scientific-defect detection, authority leakage, counterevidence uptake, negative-history recovery, experiment discrimination per cost, final held-out scientific performance, token/tool cost and wall time. The workflow claim fails if simpler conditions match RAKL's registered process and final-model performance at lower cost without more blocking validity failures.

**Result:** [[RESULT:MATCHED_WORKFLOW]]

### Experiment 3: governed self-evolution

Sealed method-defect worlds are reconstructed from real research failures while withholding the defect label. Candidate development classes include nuisance leakage, wrong correspondence nulls, missing replication, multiple-testing errors, estimand mismatch and causal-clock overreach. The system must diagnose the missing capability, freeze the discriminator before repair, implement or assimilate a candidate operator, and demonstrate transfer to a fresh assurance task.

Generic reflection, unconstrained self-editing, development-only evolution and governed RAKL will be compared under matched resources. If simpler reflection/self-editing matches fresh transfer at lower cost without additional blocking failures, the governed self-evolution layer has not earned its complexity.

**Result:** [[RESULT:SELF_EVOLUTION]]

### Experiment 4: real quant-finance scientific case

The real application is the existing `polymarket_crypto` research programme. The causal scientific order is intentionally spot-first:

\[
\text{spot evidence}
\to\text{descriptive multiscale spot law}
\to\text{predictive 5m/15m spot-path law}
\to\text{oracle/contract transform}
\to\text{downstream Polymarket application}.
\]

Polymarket information is excluded from the primary spot model and cannot repair a failed spot-science result.

The descriptive target covers return/displacement distributions, volatility and volatility-of-volatility, tails/jumps, activity/duration, continuation/reversal/memory, local microstructure/liquidity, global crypto state, cross-asset/venue dependence and observation/clock state. Full descriptive closure means every registered coordinate has a scoped result or explicit admissible null/partial-ID/block state; it does not require every microscopic mechanism to be point identified.

The predictive target is a future spot-path distribution at 5 and 15 minutes. On identical causal rows, a central bridge estimand is

\[
\Delta_{joint}=\min(R_D,R_G)-R_{DG},
\]

where \(R_D\), \(R_G\) and \(R_{DG}\) are strictly proper predictive risks for microstructure-only, global-only and joint states. A positive joint claim requires a preregistered material threshold and positive multiplicity-aware lower confidence bound on untouched or forward evidence, together with calibration and transport checks. A simpler lawful parent winning is a valid scientific result.

The exploratory programme is permitted to fit high-capacity, even deliberately overfit, **teacher** models to reveal latent structure. Teacher performance has proposal authority only. RAKL then probes dependencies, ablates nuisance features, extracts candidate state variables/interactions, formulates mathematical successors and confirms only frozen descendants on untouched data. This treats overfit models as instruments for hypothesis discovery rather than confirmation evidence.

The quant project also tests Self-RAKL: each project failure can generate both a scientific residual and a method residual. A method change counts as improvement only if it helps on a fresh scientific challenge.

**Result:** [[RESULT:SPOT_SCIENCE]]

## Figure strategy

The paper's six primary display items are preregistered in `paper/FIGURE_PLAN.md`.

1. **RAKL computational researcher architecture.** Functional researcher state, evidence-governed cognition and challenge-learning loop.
2. **Contextual Knowledge Atlas and target path.** Atomic source projections, typed transitions, non-forced gluing and epistemic cut.
3. **Authority non-escalation and selective ablations.** Authority poset plus data-dependent ablation grid.
4. **Governed self-evolution lineage.** Development vs fresh assurance, failed generations and cost.
5. **Bounded scientific cognition.** Archive/context separation plus the matched compression-reconstruction curve.
6. **Real quant-finance trial.** Spot descriptive atlas, predictive tournament, transport/calibration and method-version evolution; Polymarket shown only downstream.

Concept schematics remain editable vector artifacts. Every data-dependent panel will be generated from immutable result receipts and source-data tables; no final headline number is manually entered into a plot.

## Discussion

### What RAKL is intended to add

The strongest RAKL claim is not that an LLM can behave like a scientist by adding more agents or more tools. Rather, RAKL specifies a control plane for *scientific authority*: what kind of statement has been established, under what scope, by what evidence, through what transition, and what a new observation is allowed to change. This allows the same LLM to be replaceable. The research archive, evidence lineage, method repertoire, negative history and governance state live outside the model.

The framework also treats scientific methods as objects of scientific inquiry. A useful external capability can be decomposed and tested without inheriting the source framework's unsupported authority. An internal failure can reveal a missing method operator, but diagnosing the gap is not the same as identifying or validating its repair. This distinction is central to the intended self-evolution result.

### Why a senior-researcher analogy is useful but limited

RAKL is inspired by functional properties of experienced researchers: accumulated literature knowledge, compressed explanatory models, procedural skill, research taste, experiment selection, error monitoring, strategy switching, help seeking and learning from failed attempts. It is not a biological brain model and does not require simulated emotion or subjective self-awareness. Human-like terms are translated into operational controls. Intellectual humility becomes evidence-triggered revision; curiosity becomes information gain or learning-progress-driven exploration; reflection becomes metacognitive diagnosis plus a costed control decision; experience becomes a candidate skill only after transfer.

### Failure modes that remain possible

Formal closure does not eliminate scientific failure. The method can still retrieve poor evidence, miss a hidden context coordinate, choose an uninformative experiment, overfit a scientific or method-development benchmark, or fail to discover a necessary operator. The purpose of the architecture is to make those failures observable, typed and recoverable rather than to guarantee that they never occur.

The real-project trial is therefore part of the framework definition process. If `polymarket_crypto` exposes a high-impact operation that is not represented by the 24 current surfaces, the correct outcome is to reopen scoped formal closure, register the missing surface and prospectively test the repair. A framework that cannot discover every weakness in advance can still be scientifically useful if it can turn encountered challenge into measurable later improvement.

### Novelty risk

Many individual RAKL mechanisms have close prior art. Local-to-global consistency, provenance, partial identification, active experiment design, hierarchical memory, self-improving agents and reusable skills are established areas. The novelty claim is therefore intentionally conjunctive and vulnerable to semantic prior-art discovery. If an existing methodology is found to instantiate the same integrated epistemic transition discipline after terminology normalization, the novelty claim must narrow rather than be defended by naming differences.

## Limitations and falsifiers

The paper registers several direct falsifiers.

1. **Complexity falsifier.** If direct prompting, RAG or a simpler agent workflow matches RAKL on registered scientific-process and final-task outcomes at lower cost without more blocking validity failures, the added framework complexity is not justified.
2. **Component falsifier.** If removing a RAKL mechanism does not selectively increase the failure class it was designed to prevent, that mechanism's causal contribution is unsupported.
3. **Self-evolution falsifier.** If method changes improve only development tasks, or generic reflection/self-editing matches fresh transfer more cheaply and safely, the strong self-evolution claim fails.
4. **Context falsifier.** If similarity top-k or another simpler context policy matches RAKL on mandatory evidence retention, quality and cost under matched budgets, the complex context compiler has not shown value.
5. **Quant-science falsifier.** If the registered information set contains no material 5m/15m predictive information after causal controls, RAKL cannot declare a predictive law by continued model search. It must report the ceiling or identify the missing observable needed to reopen the question.
6. **Novelty falsifier.** A semantically equivalent prior methodology narrows the novelty claim regardless of terminology.

## Reproducibility, data and AI-use statements

**Code and artifacts.** The repository maintains content-addressed execution receipts, release-artifact manifests, exact-subject CI, frozen benchmark artifacts and negative-history records. The final submission package will bind the RAKL source revision, quant-application revision, benchmark/task packets, model/run identifiers, data/transformation manifests, result receipts, figure source data, manuscript source and rendered artifact.

**Data.** The methods framework itself is data-independent. The real quant-finance paper will document exact market-data sources, acquisition/cutoff rules, clock semantics, redistribution constraints and deterministic transformations.

**AI use.** Language models are used as research, coding and drafting tools and are not authors. Proposal generation is separated from canonical evidence authority in the method itself. The final submission will disclose substantive LLM-assisted activities and the verification controls used for them.

**Independent review.** Same-context simulated expert roles are not counted as independent review. Before top-tier journal submission, the exact manuscript/result artifact requires independent methodological/novelty review, quant/statistical review and fresh-machine artifact reproduction.

## Current evidence boundary

At this stage, the framework has a scoped formal specification and an executable reference implementation with frozen support-level hostile tests. The four bracketed result fields in the abstract and evaluation sections remain blocking. They can be replaced only by text or figures generated from immutable, subject-bound result receipts. Until the matched workflow, fresh-assurance self-evolution and real spot-science experiments are executed, the paper may claim a candidate formal methodology and software-contract validation but not empirical superiority in scientific discovery.

## References

Bibliographic metadata are maintained in `paper/references.bib` and should be rendered by the final LaTeX build rather than duplicated manually here.
