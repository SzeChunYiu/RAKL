# RAKL: An Evidence-Governed Recursive Atlas Method for Scientific Research with Large Language Models

**Article draft — methods and preregistered evaluation version**  
**Author:** Sze Chun Yiu  
**Status:** manuscript-ready structure; empirical result fields remain unresolved until exact machine-readable receipts exist.

## Abstract

Large language models can search literature, generate hypotheses, execute analyses and draft scientific reports, yet fluent generation does not determine which claims deserve scientific authority. We introduce RAKL, a candidate formal methodology for evidence-governed LLM scientific inquiry. RAKL represents research as a recursively expandable atlas of context-scoped knowledge objects rather than a single mutable answer. Typed transitions separate representation, prediction, mechanism, identification and decision authority; incompatible local views may remain plural rather than being forcibly merged. Residuals drive atomic inquiry, negative evidence is retained, search stops under semantic and evidence-lineage criteria, and the complete scientific state is externalized while each LLM operation receives a bounded epistemic working set. RAKL applies the same protocol to changes in its own method, requiring frozen development tests and fresh assurance before transferable self-improvement is claimed. We preregister matched workflow and self-evolution experiments and a real quant-finance case study on multiscale cryptocurrency spot movement. **[RESULTS_PENDING]**

## Introduction

Autonomous scientific systems increasingly automate literature retrieval, hypothesis generation, experiment planning, data analysis and manuscript production. The resulting systems can be productive while still committing failures that are easy to miss when evaluation focuses only on the final answer: incompatible studies may be compared without aligning their populations or observation processes; predictive success may be described as mechanistic identification; copied evidence may be counted as independent corroboration; a failed idea may reappear after enough iterations; a research agent may stop because it has exhausted a budget rather than because the scientific search has become flat; and a self-modifying agent may optimize against the evaluator used to declare its own improvement.

These are not primarily generation problems. They are problems of **epistemic state transition**: given a proposed claim, experiment, synthesis or method change, what evidence licenses a change in the scientific state, with what scope and what authority?

RAKL addresses this question by treating scientific research as a controlled transformation of a persistent external state. Papers and datasets are decomposed into atomic contextual objects rather than treated as globally competing wholes. Objects are connected by typed transition relations whose validity depends on scope, assumptions and evidence. Local views are glued only when the required transitions cohere; otherwise the output remains a plural atlas, an identified set or an explicit obstruction. A language model may propose a transition, but it does not authorize that transition.

The method is recursive in two senses. First, unresolved residuals are decomposed into smaller research fibers until the relevant uncertainty can be tested or honestly classified as blocked or unidentified. Second, RAKL treats its own research procedure as another scientific object: candidate method improvements can arise from internal failures or from atomic mechanisms extracted from external research frameworks, but promotion requires frozen tests, protected evaluation and transfer to fresh tasks.

The framework is engineered for ordinary LLMs rather than assuming an unbounded context window. The full research archive remains append-only and reconstructable, while a context compiler materializes only the smallest epistemically sufficient working set for the current operation. Thus knowledge can grow without prompt length growing with it.

We evaluate two claims separately. **Method self-evolution:** can RAKL diagnose and repair missing research capabilities in a way that transfers beyond the task used to design the repair? **Scientific capability shaping:** under matched model, evidence, tools and resource budgets, does wrapping the same LLM in RAKL improve scientific research outcomes and reduce registered epistemic failures? The real application is a preregistered quantitative-finance programme that constructs a multiscale descriptive and predictive model of 5- and 15-minute cryptocurrency spot movement. Polymarket is used only as a downstream transformation/application after the spot law is independently validated.

## RAKL as a computational scientific method

### Researcher state

We model the functional research state as

\[
\mathfrak R_t=(K_t,\mathcal Z_t,\Omega_t,\Pi_t,\mathcal G_t,\mathcal M_t,\mathcal X_t,\mathcal R_t),
\]

where `K_t` is the evidence-governed Knowledge Atlas; `Z_t` is the set of viable explanatory or world models; `Omega_t` is the repertoire of research operators and procedural skills; `Pi_t` is the executive policy selecting the next operation; `G_t` is the research agenda; `M_t` is the metacognitive model of the system's own limits; `X_t` stores experience trajectories and transfer evidence; and `R_t` represents tools, compute, time, context and collaborators.

This separates factual memory from explanatory models and from procedural ability. A system that has stored a paper has not necessarily acquired the ability that an experienced researcher gained by learning when a method works, what it assumes and how it fails.

### Contextual Knowledge Atlas

A local scientific chart is

\[
C_i=(U_i,\phi_i,\gamma_i,e_i,\alpha_i),
\]

with domain `U_i`, representation `phi_i`, context `gamma_i`, evidence/provenance `e_i` and scoped authority `alpha_i`. A transition

\[
T_{ij}^{\tau,\sigma}:\phi_i(U_i\cap U_j)\rightarrow\phi_j(U_i\cap U_j)
\]

must declare relation type `tau`, scope `sigma`, assumptions and evidence. Pairwise agreement is insufficient to establish a unique global object: RAKL separately tests overlap compatibility, path/cycle coherence, global existence and global identifiability.

When local views do not glue, RAKL preserves the obstruction rather than averaging it away. The output may therefore be a global formalism, a plural atlas or an obstructed/identified-set description.

### Scientific authority is multi-axis

RAKL represents authority as a partial order rather than one confidence score. For claim `c`,

\[
\alpha(c)=(G_c,R_c,M_c,I_c,D_c),
\]

where the coordinates represent grounding/provenance, representation/relation, mechanism, identification/bounding and decision authority. Cross-axis escalation requires an explicit inference rule and evidence. Consequently, observational equivalence does not mint mechanism identity, formal validity does not establish empirical truth of the premises, decision robustness does not establish mechanism, and citation multiplicity does not create independent evidence.

### Evidence-governed update

A language model proposes candidates

\[
G_\theta(K_t,a_t)\rightarrow\mathcal P_t,
\]

but a verification layer classifies each candidate from evidence and scope. Canonical state changes occur through

\[
K_{t+1}=\mathcal U(K_t,a_t,e_{t+1},V,\mathcal G_t).
\]

Negative history is monotone:

\[
\mathcal H^-_t\subseteq\mathcal H^-_{t+1}.
\]

A refuted or blocked route may be superseded by later evidence but cannot silently disappear.

### Goal-conditioned inquiry and missing scientific structure

Given target `tau`, RAKL searches for an authority-valid support subgraph rather than maximizing the size of the knowledge base. If no lawful route exists, the method seeks the smallest epistemic cut set whose unresolved elements block every admissible route. A missing element can be an unknown measurement, mechanism, transition, parameter or formal relation; it can also expose a missing **reasoning operator** in the current method basis. The latter becomes a method-basis-gap candidate and enters the self-RAKL protocol rather than being accepted by introspection alone.

### Active experiments and stopping

For an action `a`, RAKL prefers high decision-relevant information gain or mechanism separation per cost. When calibrated probabilities are justified, Bayesian information gain can be used. Otherwise the method uses set-valued identification shrinkage or worst-case separation rather than fabricating priors.

Search saturation is semantic and lineage-aware. Rephrased duplicates do not count as novelty, and repeated analyses sharing the same evidence ancestry do not count as independent flat rounds. A native residual reopens the implicated fiber.

## Bounded scientific cognition

The canonical archive may grow without bound, but the model context is compiled per operation. RAKL distinguishes a mandatory epistemic set—active target, assumptions, falsifiers, relevant negative history, both sides of a contradiction, authority prerequisites and lineage—from optional contextual material. If mandatory evidence cannot fit the model's budget, the correct outcome is `CANNOT_COMPILE`, not truncation.

Hierarchical summaries are reconstructable views, not replacements for raw evidence. Compact states therefore carry source pointers and explicit erasure metadata. We evaluate this design using a compression-reconstruction curve `Q_rec(rho)` measuring held-out scientific performance as active context is reduced.

## Learning methods from experience and from other systems

RAKL can acquire candidate methods endogenously from its own failures or exogenously from external frameworks. External systems are decomposed into atomic operators rather than imported wholesale. An operator declares inputs, outputs, valid context, assumptions, provenance, failure modes, authority it may and may not create, transition maps and benchmark identity.

A candidate may be equivalent to an incumbent, remain a parallel local view under different assumptions, qualify only for shadow testing, or be blocked/rejected. Method accumulation therefore expands a **context-indexed validated capability frontier** rather than constructing one monolithic super-agent.

Experience becomes ability only after transfer. A successful trajectory can be consolidated into a candidate procedure, but the procedure is not treated as learned capability until it succeeds on new tasks and, for a strong self-evolution claim, on fresh assurance hidden from the proposer.

## Governed self-evolution

For incumbent method `M_t` and challenger `M_{t+1}`, a positive development delta

\[
\Delta_D>0
\]

is local optimization. RAKL records scoped evolution evidence only when a fresh assurance delta is also positive and the candidate identity, negative history, resource comparability, frozen chronology and evaluator separation are clean.

We explicitly classify development gains that regress on transfer as `META_OVERFIT`. Repeated exposure to the same assurance set consumes its evidential value; later generations require a fresh or rotated reserve.

## Quantitative evaluation

We evaluate RAKL through a context-indexed competence vector

\[
\mathbf Q(A,M;d,f,t,b,c)=(V,E,D,X,P,G,L,R,C),
\]

covering epistemic validity, evidence uptake/revision, discovery, explanation/mechanism, experiment planning, metacognition/gap discovery, learning/self-evolution, robustness/reproducibility and engineering efficiency. No weighted score may compensate for a blocking validity violation.

Primary process metrics include unsupported authority upgrades, false contradiction/merge rates, counterevidence uptake, negative-history recall, hidden-gap precision/recall, experiment separation per cost, false saturation and context/token cost.

## Preregistered experiments

### Experiment 1: known-answer and hostile scientific worlds

We use worlds in which representation equivalence, context mismatch, contradiction, partial identification, shared evidence lineage and missing evidence are known by construction. Selective ablations test whether removing each RAKL mechanism increases its registered failure mode.

**Result:** `[[RESULT:E1_KNOWN_ANSWER]]`

### Experiment 2: matched research workflows

With the same base LLM, evidence cutoff, tools, hidden outcomes and resource budget, we compare direct prompting, retrieval-augmented research, a strong generic agentic workflow, fixed RAKL and self-evolving RAKL.

The real task is the construction and validation of a descriptive and predictive cryptocurrency spot-movement framework.

**Result:** `[[RESULT:E3_MATCHED_WORKFLOW]]`

### Experiment 3: governed self-evolution

We reconstruct hidden scientific-method defects from real quant-research failures, including leakage, null misspecification, missing replication, multiple-testing errors, estimand mismatch and clock/topology overreach. The system must diagnose the missing capability without receiving its label, freeze a discriminator before repair, and transfer the resulting method to fresh assurance tasks.

**Result:** `[[RESULT:E4_SELF_EVOLUTION]]`

### Experiment 4: real quant-finance scientific case

The application uses a history-resolved microstructure lane and a global crypto-state lane to describe and predict 5- and 15-minute spot movement. On identical causal rows the primary bridge estimand is

\[
\Delta_{joint}=\min(R_D,R_G)-R_{DG}.
\]

The spot result is evaluated with strictly proper predictive scores, calibration, transport and projective/path consistency. Prediction-market quantities are downstream and cannot validate the spot model.

**Result:** `[[RESULT:E2_SPOT_PREDICTIVE]]`

## Discussion

RAKL is not proposed as a new retrieval algorithm, multi-agent architecture, falsification procedure, experiment-design theory, knowledge graph, memory system or program-evolution algorithm in isolation. Its candidate contribution is the composition of these activities under an explicit scientific authority model: context before competition, typed non-escalating transitions, obstruction-preserving synthesis, immutable negative history, semantic/evidence-lineage stopping, bounded working context and governed method evolution.

The self-evolution claim is intentionally stronger than code mutation and weaker than global recursive self-improvement. A RAKL generation has evolved only for the scope in which its improved research capability transfers under fresh assurance. Failed, blocked and overfit generations remain part of the method lineage.

The quant-finance case provides a difficult real test because it combines high-frequency clocks, nonstationarity, hidden state, heavy tails, cross-asset dependence, causal availability and a long negative-result history. A successful predictive result would not establish a unique microscopic market mechanism; conversely, a predictive null can still leave a useful descriptive atlas and method-evolution result.

## Limitations and falsifiers

RAKL loses its empirical case if simpler workflows match its registered scientific-process performance at lower cost without higher validity failures. Its self-evolution claim fails if development gains do not transfer to fresh tasks. Its knowledge architecture is unnecessary if ablations do not selectively increase the failure modes they were designed to prevent. Its novelty claim narrows if adversarial review finds a pre-existing methodology semantically equivalent to the integrated transition discipline after terminology normalization.

Independent reviewers, different model backbones and fresh evidence lineages remain necessary because same-context reflection cannot establish independent assurance.

## Data, code and AI-use statements

**Code and reproducibility:** final submission will bind the RAKL source revision, quant-application revision, benchmark packets, result receipts, figures/tables and manuscript through cryptographic artifact manifests.

**Data:** the final statement will identify the exact source revisions, redistribution constraints and deterministic transformation manifests used by the quant application.

**LLM use:** language models are research tools and are not authors. The final Methods/Disclosure section will identify substantive model-assisted research, coding and drafting roles and the evidence-governance controls applied to them.

## Result-slot policy

Any token of the form `[[RESULT:...]]` is a blocking unresolved result. It may be replaced only by a table/figure/text fragment generated from an immutable machine-readable result receipt whose subject, population, code, evaluator and preregistration identities are verified.
