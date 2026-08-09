# Paper Insert — Metacognitive Self-Diagnosis and Method Completeness

Status: paper-ready drafting support. Psychology-to-RAKL mappings are design hypotheses unless backed by the registered RAKL benchmark.

## Motivation

Recursive self-improvement is incomplete if the method can only optimize weaknesses already represented in its current ontology. RAKL therefore introduces a **metacognitive method-completeness layer** whose purpose is not to ask an LLM for a subjective description of its weaknesses, but to detect mismatches among predicted competence, external outcomes, explanatory reconstruction, independent outside review, target reachability, and the incumbent residual/operator taxonomy.

## Psychology-inspired design without anthropomorphism

Human metacognition provides useful source mechanisms but not a literal model of LLM cognition. Empirical psychology shows that confidence can track error yet is imperfect; metacognitive performance can be domain-specific; people exhibit a bias blind spot; requiring mechanistic explanation can reveal an illusion of explanatory depth; explicit consider-the-opposite instructions can outperform generic debiasing requests; self-distancing can improve reasoning about self-relevant conflicts; and outcome feedback can improve calibration without necessarily improving sensitivity. Recent LLM work similarly reports a knowing-doing gap in which self-knowledge does not reliably translate into appropriate agentic control.

RAKL therefore externalizes the monitor-control boundary. The model may generate confidence, explanations, countermodels, or weakness hypotheses, but a separate system layer decides whether external evidence warrants reopening a fiber, demanding independent review, or creating a new ontology/operator challenger.

## Formal audit

Let the current method basis be `Omega_t`. A metacognitive diagnostic is

\[
d_t=\mathcal M(K_t,\Omega_t,a_t,e_t),
\]

where `e_t` includes external outcome evidence when the audit depends on correctness. A controller maps the diagnostic to a follow-up action but cannot directly increase scientific authority:

\[
\mathcal C(d_t)\in
\{
\text{NO_AUDIT},
\text{KNOWN_WEAKNESS},
\text{CALIBRATION_WEAKNESS},
\text{EXPLANATION_GAP},
\text{ONTOLOGY_GAP_CANDIDATE},
\text{METHOD_BASIS_GAP_CANDIDATE},
\text{INDEPENDENT_REVIEW_REQUIRED},
\text{CANNOT_CHECK}
\}.
\]

A candidate ontology or method-basis gap is a proposal to open a new Self-RAKL fiber, not evidence that the proposed missing category/operator is correct.

## Explanation-depth challenge

For a registered authority target with required explanation elements `R`, RAKL requests a reconstruction and records produced elements `P`. The gap

\[
G_{exp}=R\setminus P
\]

is a direct diagnostic of what the current account cannot reconstruct. The rubric is frozen before evaluation to prevent the proposer from weakening the explanation standard after observing its response.

## Countermodel challenge

Generic reflection is not credited as adversarial review. When bias or premature closure is a risk, RAKL requires an explicit alternative account, its differing assumptions, and a possible discriminator. A phrase such as "I considered that I might be wrong" has no special evidential status.

## Domain-scoped calibration

Metacognitive calibration is stored by method fiber/context rather than globally:

\[
Cal(m,f,\gamma).
\]

Evidence that a model recognizes its retrieval failures cannot establish that it recognizes mechanism-identification failures. Unmeasured transfer remains `CANNOT_CHECK`.

## Triggered rather than continuous reflection

The metacognitive audit is event-triggered. High-confidence errors, repeated unclassified residuals, explanation-reconstruction failures, target unreachability, domain transfer, and high-value checkpoints can open an audit. Low-value uncertainty can be ignored when reflection cost exceeds the registered failure risk. This is important because reflection itself consumes context, latency, and cognitive/compute budget and should face the same decision-relevant value-per-cost rule as other RAKL actions.

## Operational intellectual humility

RAKL does not model humility as a personality label. It implements revisability: external evidence can downgrade active authority; `CANNOT_CHECK` is permitted; negative evidence is preserved; and a challenger can reopen the method's own ontology. The empirical claim is behavioral and auditable rather than anthropomorphic.

## Headline experiment

Construct hidden-world method tasks in which the incumbent RAKL basis omits a weakness class or operator. Compare matched-cost ordinary self-reflection, generic critic/debate, feedback-only calibration, structured RAKL metacognitive audits, and audits plus independent outside review.

A successful result requires not merely more criticism but selective diagnosis:

- known failures should be routed to known fibers;
- one surprising error should not become an ontology invention;
- repeated unclassifiable failures should trigger an ontology challenge;
- unreachable targets whose cut is covered by an incumbent operator should not trigger operator invention;
- unreachable targets whose identified cut lies outside the incumbent basis should trigger a method-basis challenger;
- explanation gaps should identify the missing registered explanatory elements;
- domain calibration must not be globalized;
- all repairs remain subject to frozen Self-RAKL evaluation.

## Novelty boundary

Metacognition, self-explanation, consider-the-opposite debiasing, outside-view reasoning, feedback calibration, and external confidence control are prior ideas. The candidate RAKL contribution is their **integration into a scientific-method ontology-completeness process tied to target reachability, typed authority, residual routing, negative history, independent evidence lineage, and governed method promotion**.

The contribution is falsified or demoted if a prior method is semantically equivalent after normalization, or if the structured audit fails to discover held-out missing weakness/operator classes better than simpler reflection at matched cost.
