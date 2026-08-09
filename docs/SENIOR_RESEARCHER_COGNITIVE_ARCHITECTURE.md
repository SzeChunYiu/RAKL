# Senior Researcher Cognitive Architecture for RAKL

Status: candidate theory and engineering architecture; research-only; does not amend the Constitution.
Date: 2026-08-09

## 1. Goal

RAKL should not literally imitate biological neurons. The engineering target is the functional organization of a mature research scientist: a system that accumulates evidence across years of reading and experimentation, compresses that experience into reusable concepts and procedures, chooses worthwhile questions, notices anomalies and blind spots, constructs explanations in its own canonical language, designs discriminating experiments, and revises itself when evidence defeats it.

The core distinction is between four things that are often collapsed in LLM systems:

1. **declarative epistemic memory** — what evidence-supported scientific objects are known;
2. **generative explanatory state** — what models/mechanisms can reconstruct and predict the observations;
3. **procedural research memory** — what operations/strategies have been learned and transferred;
4. **executive and metacognitive control** — what to investigate next, where to spend resources, and when the current method basis is inadequate.

RAKL already implements substantial parts of (1), (3), and metacognitive monitoring. This document makes the whole functional state explicit so future engineering can test missing coordinates rather than anthropomorphizing the LLM.

## 2. Researcher state

Define the RAKL researcher state

\[
\mathfrak R_t =
(K_t,\mathcal Z_t,\Omega_t,\Pi_t,\mathcal G_t,\mathcal M_t,\mathcal X_t,\mathcal R_t),
\]

where:

- \(K_t\): evidence-governed Knowledge Atlas, provenance, authority, negative history, saturation and open residuals;
- \(\mathcal Z_t\): surviving **generative/explanatory models** of the target world, explicitly set-valued when not identified;
- \(\Omega_t\): validated **method/operator repertoire**: retrieval, decomposition, falsification, experiment design, analogy, formal checks, synthesis, review, etc.;
- \(\Pi_t\): research control policy/router mapping a task state to admissible operations;
- \(\mathcal G_t\): research agenda/goal portfolio, including target value, tractability, unresolved importance and opportunity cost;
- \(\mathcal M_t\): metacognitive model of calibration, known weaknesses, ontology gaps and operator-basis gaps;
- \(\mathcal X_t\): experience memory containing executed trajectories, successful and failed procedures, and transfer evidence;
- \(\mathcal R_t\): resource/environment state: tools, data, compute, time, context budget, permissions and collaborators/review channels.

No coordinate is a scalar 'intelligence' score.

## 3. Object-level research loop

For a registered target \(\tau\), the executive policy chooses an admissible action

\[
a_t \sim \Pi_t(\cdot\mid \mathfrak R_t,\tau),
\]

subject to blocking validity constraints \(\Lambda\).

The action interacts with the information environment and produces an observation/evidence packet

\[
e_{t+1}\sim \mathcal E(a_t\mid O,\gamma_t).
\]

A verifier determines the licensed epistemic effect

\[
V(e_{t+1},K_t,\gamma_t)\rightarrow
\{SUPPORTED,REFUTED,PARTIALLY\_IDENTIFIED,BLOCKED,CANNOT\_CHECK\}.
\]

The canonical state update is

\[
K_{t+1}=\mathcal U_K(K_t,a_t,e_{t+1},V),
\]

while the explanatory survivor set is updated separately:

\[
\mathcal Z_{t+1}
=
\{z\in\mathcal Z_t\cup\mathcal Z_{new}: z\text{ remains compatible with }K_{t+1}\}.
\]

Proposal generation cannot directly mint authority in either state.

## 4. Experience-to-ability consolidation

A senior scientist does not merely remember papers. Repeated experience becomes reusable procedure.

Represent an executed research episode as

\[
x_t=(s_t,a_t,e_{t+1},o_t,c_t),
\]

where `s` is the pre-action state, `a` the operation, `e` the observed evidence, `o` the outcome and `c` the measured cost.

A consolidation operator proposes a reusable procedure

\[
\operatorname{Consolidate}(x_{1:t})\rightarrow \omega^*.
\]

The candidate \(\omega^*\) is not a learned ability until it transfers. It enters the normal Self-RAKL protocol:

\[
\omega^*\xrightarrow{development}\xrightarrow{held\text{-}out\ transfer}\xrightarrow{fresh\ assurance}\Omega_{t+1}.
\]

Failure, meta-overfit and negative transfer remain in \(\mathcal X_t\) and negative history.

This is the formal bridge from 'experience' to 'ability'.

## 5. Generative understanding and 'own language'

Retrieval is not equivalent to understanding. RAKL should test whether a compact canonical state can reconstruct explanations and predictions without replaying the full source corpus.

For a learned representation \(C_\rho(K_t)\) at compression level \(\rho\), define held-out reconstruction quality

\[
Q_{rec}(\rho)=
Q\big(\operatorname{Reconstruct}(C_\rho(K_t)),Y_{heldout}\big).
\]

The **compression-reconstruction curve** \(Q_{rec}(\rho)\) measures how aggressively source context can be compressed while preserving evidence-sensitive scientific capability.

A strong scientific representation has high reconstruction quality at small working-set size while retaining source pointers and uncertainty. Compression does not erase provenance.

## 6. Research agenda and scientific taste

RAKL currently performs best when a target is registered. A senior scientist also chooses which target is worth pursuing. This is a distinct missing capability.

For candidate research goal `g`, maintain a multi-objective value profile

\[
\mathbf v(g)=
(I_g,N_g,T_g,D_g,C_g,R_g),
\]

where:

- \(I_g\): expected decision/scientific importance;
- \(N_g\): semantic novelty or unresolvedness;
- \(T_g\): tractability under current tools/evidence;
- \(D_g\): expected discriminatory leverage over viable theories;
- \(C_g\): cost;
- \(R_g\): scientific/ethical/operational risk.

Do not collapse these into one universal weighted score. Maintain a context-indexed Pareto agenda and expose trade-offs. Calibrated probabilities may support expected-value calculations; otherwise use ordinal/set-valued rankings.

## 7. Anomaly and surprise sensitivity

A mature researcher notices residuals that do not fit the current explanatory basis. Define an explanatory residual

\[
r_t = y_t-\hat y(\mathcal Z_t)
\]

only when the observable and error semantics make subtraction meaningful. More generally use a typed incompatibility object

\[
\operatorname{Residual}(e_t,\mathcal Z_t,K_t).
\]

Residual priority is determined by its potential to change the target, distinguish mechanisms, expose an ontology gap, or reopen a saturated fiber, not merely by numerical magnitude.

## 8. Mental simulation and counterfactual world models

A senior scientist asks 'what would I observe if this mechanism were true?' RAKL should make this explicit.

For candidate mechanism \(z\), action/intervention \(a\), and context \(\gamma\), define a prediction set

\[
\mathcal Y(z,a,\gamma),
\]

possibly set-valued under partial identification. Experiment design chooses actions that maximize separation between survivor prediction sets subject to cost and validity constraints.

When justified probabilities exist, use information gain. Otherwise use worst-case set separation or identified-set shrinkage.

## 9. Tacit/procedural research knowledge

Expert research contains procedural details not naturally represented as scientific claims: how to debug an assay, which preprocessing step is fragile, which literature query reveals a hidden vocabulary, how to detect a misleading plot, when a simulation is numerically unstable.

RAKL should represent such experience as versioned method operators with:

```text
trigger
preconditions
input/output contract
resource requirements
failure modes
verification contract
transfer evidence
negative history
```

Procedural knowledge has method authority, not scientific-truth authority.

## 10. Executive control and multi-timescale planning

Research occurs on several horizons:

```text
operation -> fiber -> experiment series -> project -> research programme
```

RAKL therefore needs hierarchical planning where local actions are conditioned on parent goals and opportunity costs. A stuck local fiber may be paused rather than endlessly optimized if another route has higher decision-relevant leverage.

The executive should periodically perform global reconstruction after local decomposition:

\[
DECOMPOSE \leftrightarrow RECONSTRUCT.
\]

This guards against local-fiber myopia.

## 11. Social epistemology and collaboration

Senior scientists use collaborators, reviewers and domain experts as external cognitive resources. RAKL already distinguishes same-context reflection from independent review; the full architecture should also model reviewer specialization, evidence-lineage dependence, conceptual-basis diversity, conflicts of interest and handoff contracts.

Social agreement cannot mint authority by vote. It can produce new evidence, objections, methods and perspectives that enter the same evidence-governed state transition.

## 12. Measurement and instrumentation cognition

A major remaining scientific layer is explicit reasoning about measurement itself. A claimed latent object `O` is observed through an operator

\[
y = h(O,\eta,\gamma)+\epsilon,
\]

where `h` is the measurement/observation process, `eta` contains instrument/calibration state and `epsilon` describes registered noise/error semantics.

RAKL should distinguish uncertainty about the object from uncertainty introduced by measurement, preprocessing or calibration. A new instrument can change identifiability without changing the underlying theory.

## 13. Proposed complete functional stack

A mature RAKL reference architecture therefore has:

```text
EVIDENCE / KNOWLEDGE ATLAS
        <->
GENERATIVE EXPLANATORY MODEL SET
        <->
PROCEDURAL METHOD / SKILL ATLAS
        <->
EXECUTIVE AGENDA + RESOURCE CONTROLLER
        <->
METACOGNITIVE MONITOR + METHOD COMPLETENESS
        <->
TOOLS / EXPERIMENTS / DATA / HUMAN REVIEW
```

The LLM is a replaceable proposer and transformation engine inside this stack, not the persistent brain state itself.

## 14. Current major missing fibers

The most material incompletely engineered functions are:

- agenda formation / research taste;
- explanation compression and held-out reconstruction;
- explicit mental simulation / counterfactual prediction-set engine;
- procedural experience consolidation into transferable operators;
- measurement/instrument model and calibration reasoning;
- hierarchical multi-timescale research programme control;
- social/collaboration routing with conceptual-basis independence;
- prospective hidden-weakness discovery rather than retrospective diagnosis.

Each must receive its own frozen benchmark before activation.
