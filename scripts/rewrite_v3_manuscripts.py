from __future__ import annotations

from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PUB = ROOT / "publication" / "papers"
COMPAT = ROOT / "paper" / "papers"
MARKER = "% RAKL_V3_MANUSCRIPT_UPDATE_20260811"


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def replace_abstract(text: str, new_body: str) -> str:
    pattern = re.compile(r"\\begin\{abstract\}.*?\\end\{abstract\}", re.S)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise RuntimeError(f"expected one abstract, found {len(matches)}")
    return pattern.sub("\\begin{abstract}\n" + new_body.strip() + "\n\\end{abstract}", text, count=1)


def insert_after(text: str, anchor: str, addition: str, *, label: str) -> str:
    if addition.strip() in text:
        return text
    if text.count(anchor) != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {text.count(anchor)}")
    return text.replace(anchor, anchor + "\n\n" + addition.strip(), 1)


def insert_before(text: str, anchor: str, addition: str, *, label: str) -> str:
    if addition.strip() in text:
        return text
    if text.count(anchor) != 1:
        raise RuntimeError(f"{label}: expected one anchor, found {text.count(anchor)}")
    return text.replace(anchor, addition.strip() + "\n\n" + anchor, 1)


def append_once(text: str, addition: str) -> str:
    if addition.strip() in text:
        return text
    return text.rstrip() + "\n\n" + addition.strip() + "\n"


def sync(relative: str) -> None:
    src = PUB / relative
    dst = COMPAT / relative
    if dst.parent.exists():
        write(dst, read(src))


# ---------------------------------------------------------------------------
# Paper I — epistemic mechanics becomes the epistemic/authority projection of v3.
# ---------------------------------------------------------------------------
p1 = PUB / "paper-01-epistemic-mechanics"
p1_main = p1 / "main.tex"
p1_text = read(p1_main)
p1_abstract = r"""
Large-language-model research systems can generate hypotheses, search literature, reuse prior experience and coordinate analyses, but none of those capabilities specifies which generated statements are licensed to change a scientific record. RAKL v3 represents the broader research system as a persistent typed external substrate whose epistemic state, task experience, operators, failures, strategies and meta-methods are distinct but overlapping views. This paper isolates the epistemic projection of that substrate and formalizes its authority mechanics. Claims are indexed by context, evidence, uncertainty and provenance; compatibility is mediated by explicit alignments; scientific authority is a partial order over multiple coordinates rather than a scalar score; and proposal-generating models have no direct canonical write authority. We show by a three-context parity construction that pairwise compatibility need not imply higher-order gluing, and that incomparable authority states cannot be faithfully collapsed into one total-order scalar. A capacity-bounded workspace, an experience-conditioned router or a learned procedural lesson may change computational access and search priority without conferring evidential authority. Open-World Mechanism Discovery begins from functional signatures rather than framework terminology and can certify only bounded closure; unrestricted open-world completeness cannot be established from a finite transcript without a complete membership oracle. We define bounded epistemic saturation as a stopping condition for the epistemic view and distinguish it from v3 saturation of operators, experience patterns, paths and meta-methods. The result is a formal account of evidence-governed scientific state inside a recursively learning external substrate, not a claim of empirical superiority, global scientific completeness or self-certified continual learning.
"""
p1_text = replace_abstract(p1_text, p1_abstract)
p1_include_anchor = r"\input{sections/02_compatibility_authority}"
p1_v3_include = r"\input{sections/02b_v3_epistemic_projection}"
if p1_v3_include not in p1_text:
    p1_text = p1_text.replace(p1_include_anchor, p1_include_anchor + "\n" + p1_v3_include, 1)
write(p1_main, p1_text)

p1_v3 = r"""
\section{Epistemic mechanics as a projection of the RAKL v3 substrate}
\label{sec:v3-epistemic-projection}

RAKL v3 enlarges the persistent research state without weakening the authority rules developed above. Let
\[
R_t
\]
denote the complete external v3 state and let
\[
K_t=\pi_{\mathrm{epi}}(R_t)
\]
be its epistemic projection: the contextual claims, evidence, compatibility relations, obstructions, uncertainty objects, negative history and governance certificates that can participate in scientific authority. Other typed views of the same persistent state include immutable task episodes, operational tools, failure diagnoses, learned strategy abstractions and Self-RAKL method variants. These views may share identity and lineage, but they do not inherit each other's authority semantics merely because they are co-stored or co-retrieved.

The global object $R_t$ is therefore not asserted to be one order-theoretic lattice. Genuine lattice language remains scoped to substructures for which a closure or meet--join law has actually been established. At the framework level the safe abstraction is a typed relational substrate with specialized authority-owning views. This preserves the distinction established earlier between compatibility complexes, closure systems, provenance graphs and authority posets.

\subsection{Experience can change search without changing scientific authority}

A consequential task attempt in v3 is frozen as an immutable episode before it is interpreted. Let $E_t$ denote the episode ledger and let $\rho_t$ be an experience-conditioned routing policy derived from registered episodes. A future proposal generator may therefore depend on
\[
G_\theta\bigl(K_t,E_t,\rho_t,a_t\bigr),
\]
even when the model weights $\theta$ are unchanged. This is external-state learning: the system can alter which operators, paths or memories are tried first while retaining the original evidence roots.

\begin{proposition}[Experience-routing non-escalation]
Suppose an update to $E_t$ or $\rho_t$ has no certified epistemic-update event in its transition ancestry. Then that update cannot by itself increase any coordinate of the scientific authority state $\alpha(c)$ of a claim $c$.
\end{proposition}

\begin{proof}
Episode storage and routing updates have codomain in experience or computational-policy state. By the proposal non-sovereignty assumption, scientific authority changes only through a separately licensed canonical update carrying the required evidence/governance certificate. Therefore an experience-derived change can affect proposal order or computational access while leaving the epistemic projection invariant until an ordinary verification and promotion transition occurs.
\end{proof}

This proposition is the v3 form of
\[
\text{access}\neq\text{coherence}\neq\text{authority}.
\]
A lesson that often worked can be useful to retrieve; a successful trajectory can be useful to imitate; neither becomes scientific evidence for an external claim merely because it improved task performance.

\subsection{Failure observation, diagnosis and obstruction are different epistemic objects}

The same separation applies to negative experience. A failed task episode establishes that a registered attempt had a non-success outcome under a registered context. It does not establish why the attempt failed. V3 therefore distinguishes
\[
\text{episode}\;\neq\;\text{diagnosis}\;\neq\;\text{reusable obstruction}.
\]
An observed failure can seed competing diagnoses. A causal diagnosis requires discriminating evidence. A reusable boundary lesson requires further scoped verification or fresh transfer. This prevents one unlucky or misspecified run from becoming a global prohibition in the scientific state.

The distinction also protects negative history. The immutable episode remains available even after a diagnosis is superseded. Later evidence can therefore repair the explanation of a failure without rewriting the fact that the failure occurred.

\subsection{Epistemic saturation is one coordinate of vector saturation}

The bounded epistemic saturation developed later in this paper concerns growth of the epistemic projection $K_t$: new evidence, claims, contradictions, relations, mechanism owners, derivations and unresolved scientific fibers. RAKL v3 additionally tracks scoped flatness of operators, experience patterns, obstructions, relations, paths and meta-methods. Let
\[
\mathbf s_t=(s_K,s_O,s_E,s_B,s_R,s_P,s_M)
\]
denote the corresponding saturation vector. Flatness of $s_K$ does not imply flatness of the other coordinates, and flatness of the complete declared vector still does not imply unrestricted completeness of the external world.

A native residual reopens only the coordinates implicated by that residual. Thus a new scientific paper can reopen knowledge saturation without invalidating a stable operator basis, while a repeated method failure can reopen operator or path saturation without retracting an already verified scientific claim. This factorization makes the stopping rule more precise: the epistemic certificate in this paper is a scoped projection of a broader recursive research state, not a global declaration that RAKL has nothing left to learn.
"""
write(p1 / "sections" / "02b_v3_epistemic_projection.tex", MARKER + "\n" + p1_v3.strip() + "\n")

# ---------------------------------------------------------------------------
# Paper II — canonical v3 architecture paper.
# ---------------------------------------------------------------------------
p2 = PUB / "paper-02-rakl-evidence-governed-research" / "source"
p2_main = p2 / "main.tex"
p2_text = read(p2_main)
p2_abstract = r"""
AI research agents can search literature, generate hypotheses and execute analyses, but workflow completion does not determine which statements are licensed to change a scientific record or which past task experiences are safe to reuse. We present RAKL v3, an evidence-governed architecture that treats research as operation over a persistent, typed, recursively evolving external cognitive substrate. The underlying language model may remain weight-frozen while future behaviour changes through accumulated external state. RAKL v3 couples four loops: information to knowledge, problem to solution, experience to method, and RAKL to better RAKL. Immutable TaskEpisode records preserve what actually happened before interpretation; versioned Lessons separate reflection from reusable method authority; problem-conditioned fibres compile knowledge, tools, episodes, failures, strategies and warnings for a target atom; verified local sections must still agree on declared interfaces before a global solution is licensed; and experience-conditioned routing changes search priority without changing scientific authority. Saturation is vector-valued across knowledge, operators, experience patterns, obstructions, relations, paths and meta-methods, while method invention and Self-RAKL evolution remain separately gated. The existing deterministic pendulum trace continues to demonstrate evidence/authority mechanics, not scientific superiority. V3 additionally implements a matched RESET_BASELINE versus LEARNING_ENABLED continual-experience benchmark with uncontaminated fresh transfer, but the architecture alone does not establish a positive transfer gain, high RAKL-triviality, universal continual learning or autonomous scientific invention.
"""
p2_text = replace_abstract(p2_text, p2_abstract)
write(p2_main, p2_text)

formal = p2 / "sections" / "03_formal" / "part01.tex"
formal_text = read(formal)
formal_anchor = "with Knowledge Atlas charts, typed transitions, survivors, evidence/provenance, uncertainty and identified sets, obstructions/residuals, recursive fibers, immutable negative history, saturation state and protected governance identity."
formal_add = r"""
RAKL v3 places this epistemic state inside a broader persistent value state $R_t$. We write
\begin{equation}
K_t=\pi_{\mathrm{epi}}(R_t),
\end{equation}
where $\pi_{\mathrm{epi}}$ is the authority-preserving epistemic projection. The remaining v3 views contain immutable task episodes, versioned lessons, operational tools, failure diagnoses, strategy/expertise abstractions, vector-saturation state and an optional archive of Self-RAKL variants. The global substrate is a typed relational object, not a claim that all of these views form one mathematical lattice. Specialized stores remain the semantic and authority owners of their objects.

For a replaceable driver with fixed weights $\theta$, one task turn can be written schematically as
\begin{equation}
(S_t,\tau_t)=\operatorname{Driver}_{\theta}(P_t,R_t),
\qquad
R_{t+1}=\operatorname{Learn}(R_t,\tau_t).
\end{equation}
The learning map changes external state rather than silently changing the evidential meaning of $K_t$. In particular, experience-derived routing priors may alter which admissible operator is attempted first, but scientific promotion still passes through the ordinary evidence and governance transitions of the epistemic projection.
"""
formal_text = insert_after(formal_text, formal_anchor, MARKER + "\n" + formal_add, label="paper2 formal v3 state")
write(formal, formal_text)

memory = p2 / "sections" / "04_scientific_memory.tex"
memory_text = read(memory)
memory_anchor = "The distinction between \\emph{scientific projection} and \\emph{compression} is central to RAKL's engineering. Raw source bytes, a contextual scientific claim, a canonical atlas object, a compressed summary and an LLM prompt are different objects with different authority ceilings."
memory_add = r"""
\subsection{Task episodes are a second immutable evidence root}
V3 adds process evidence without conflating it with world evidence. A source record states what an external paper, dataset, instrument or database contained. A \texttt{TaskEpisode} states what the research system actually attempted and observed under a frozen problem signature, fibre snapshot, operator trace, verification record, residual, provenance and resource cost. Both are immutable roots, but they answer different questions.

A lesson is therefore not the replacement for an episode. It is a versioned, scoped abstraction derived from one or more episodes and records its trigger, context, action, expected effects, boundaries, supporting and contradicting episodes, falsifier and validation obligations. Candidate reflection may create such an abstraction, but reusable status requires registered verification plus fresh transfer or proof-backed evidence. Promotion creates a new lesson version rather than mutating either the source episodes or the earlier candidate.

The resulting memory rule is
\begin{equation}
\text{derived lesson}\neq\text{raw trajectory}\neq\text{scientific evidence}.
\end{equation}
A proof-backed lesson may be strongly justified as a procedural abstraction while remaining a lossy summary of the trajectories from which it was learned. Conversely, an episode may be perfectly preserved while supporting no reusable causal lesson at all. This distinction prevents compression, reflection and repeated success from becoming accidental authority shortcuts.
"""
memory_text = insert_after(memory_text, memory_anchor, MARKER + "\n" + memory_add, label="paper2 experience memory")
write(memory, memory_text)

life = p2 / "sections" / "05_atomic_lifecycle.tex"
life_text = read(life)
life_anchor = "The current reference implementation makes 17 stages explicit. This is important for both scientific reasoning and coding-agent use: a user can tell which steps are model-proposed, which are deterministic state operations, and where verification must occur. Table~\\ref{tab:lifecycle} summarizes the public contract; typed inputs/outputs, state read/write sets, failure states and code owners are machine-readable in the implementation."
life_add = r"""
In v3 these 17 stages are best understood as the authority-critical \emph{information-to-knowledge sub-lifecycle} inside a larger recursive task loop. The outer driver registers and atomizes a problem, compiles a target-conditioned fibre, ranks admissible operator paths using symbolic and experiential priors, executes a candidate action, verifies the result, freezes a \texttt{TaskEpisode}, records any residual, glues verified local sections, and only then consolidates reusable lessons or updates the saturation vector. Method invention is reached only after an explicit basis-gap gate, and a repeated meta-residual may open a protected Self-RAKL challenger branch.

This outer loop introduces no new authority shortcut. The fibre is a working view; co-retrieval does not establish compatibility. A successful local section does not establish a global solution until declared interfaces, dependencies, complete atom coverage and verification agree. An observed failure does not establish a causal obstruction. A learned routing prior changes search order only. Thus the 17-stage table remains the audit contract for scientific-state transitions while v3 supplies the persistent experience and problem-solving dynamics around it.
"""
life_text = insert_after(life_text, life_anchor, MARKER + "\n" + life_add, label="paper2 lifecycle v3")
write(life, life_text)

geom = p2 / "sections" / "06_three_geometries.tex"
geom_text = read(geom)
geom_anchor = "The epistemic semantics are nevertheless different. A generic note link means that one author linked two documents. A RAKL edge is a typed scientific witness carrying relation type, context, assumptions, evidence lineage and authority scope. Nodes are not only notes: they may be claims, measurements, assumptions, mechanisms, refutations, identified sets, methods, residuals or experiments. The atlas additionally needs overlays for negative history, contradictions, mechanism ancestry, epistemic cuts, saturation state and active-context token cost. We therefore view an Obsidian-like graph as a promising interface layer, not as the scientific method itself."
geom_add = r"""
V3 sharpens this comparison by distinguishing the complete substrate $R_t$ from its epistemic projection $K_t=\pi_{\mathrm{epi}}(R_t)$. Task episodes, learned lessons, tools, failure diagnoses and architecture variants can all appear in a unified query overlay, but that overlay does not erase their specialized semantics. The human navigation graph is therefore a lossy projection of a lossy-or-lossless collection of specialized views, not the canonical scientific object itself.
"""
geom_text = insert_after(geom_text, geom_anchor, MARKER + "\n" + geom_add, label="paper2 three geometries")
write(geom, geom_text)

method = p2 / "sections" / "10_method_evolution.tex"
method_text = read(method)
method_anchor = r"\section{Learning and evolving the method}"
method_add = r"""
\subsection{Fast experience recording and slow lesson consolidation}
RAKL v3 inserts an ordinary continual-learning layer below method invention. Every consequential turn freezes the observed result as an immutable \texttt{TaskEpisode} before reflection. A successful or failed trajectory can then influence retrieval statistics, but a reusable method abstraction is a separate, versioned \texttt{Lesson}. Candidate lessons have no operational promotion authority merely because they summarize several runs. Local verification can raise them to a scoped verified state; reusable promotion requires fresh transfer or proof-backed evidence; contradictory episodes remain attached as boundary evidence.

The failure path is deliberately slower than ordinary reflection:
\begin{equation}
\begin{aligned}
\text{non-success episode}
&\to \text{observed-only failure record}
\to \text{diagnosis revision}\\
&\to \text{supported/verified diagnosis}
\to \text{candidate boundary lesson}\\
&\to \text{fresh transfer/proof}
\to \text{reusable obstruction or boundary}.
\end{aligned}
\end{equation}
This prevents one failure from becoming a causal law and allows later evidence to supersede a diagnosis while retaining the original episode.

\subsection{Problem fibres, learned motifs and experience-conditioned routing}
A problem-conditioned fibre may retrieve scientific knowledge, applicable success-derived tools, analogous episodes, relevant failures, strategy motifs, expertise chunks and unresolved warnings. Historical outcomes contribute scoped priors through smoothed success/failure rates, cost, verification debt, boundary risk and a small exploration term. These priors rank admissible operators and paths; they do not alter proof, verification or authority rules.

Repeated successful operator sequences can be induced into candidate strategy motifs. Failures containing the same sequence are retained as contradictory evidence rather than discarded. The same promotion discipline applies: pattern frequency may nominate a strategy, but fresh validation determines whether it becomes a reusable method.

\subsection{Branching Self-RAKL archive}
The protected Self-RAKL comparison remains the gate for architecture-level change, but v3 makes the state history explicitly branching. Variants are recorded as \texttt{INCUMBENT}, \texttt{CHALLENGER}, \texttt{ASSURED}, \texttt{REJECTED} or \texttt{RETIRED}. A challenger that passes fresh assurance becomes \texttt{ASSURED}; it does not automatically become incumbent. Explicit governance is still required for promotion, and the previous incumbent remains available as an assured rollback or task-specialized alternative. Self-improvement evidence is therefore a persistent archive of comparisons, not a destructive rewrite of the method's past.
"""
method_text = insert_after(method_text, method_anchor, MARKER + "\n" + method_add, label="paper2 method v3")
write(method, method_text)

impl = p2 / "sections" / "11_reference_implementation.tex"
impl_text = read(impl)
impl_anchor = "The current reference profile registers exactly 24 high-impact method surfaces: decomposition; routing; search/query generation; source selection/reliability; claim extraction; ontology/terminology normalization; mathematical/context translation; equivalence/similarity; contextual theory gluing; contradiction diagnosis; gap discovery; experiment/query selection; synthesis; memory; review; benchmarking; authority promotion; saturation/stopping; prompting/context policy; capability shaping; software architecture/execution; research portfolio/tree control; objective evolution; and generator transport."
impl_add = r"""
V3 does not replace this surface registry; it provides a persistent substrate that connects several of its previously specialized stores. The stable facade is \texttt{rakl.v3}. Major executable surfaces include \texttt{experience\_substrate.py}, \texttt{experience\_learning.py}, \texttt{experience\_memory.py}, \texttt{failure\_learning.py}, \texttt{problem\_fibre.py}, \texttt{gluing\_learning.py}, \texttt{experience\_policy.py}, \texttt{saturation\_vector.py}, \texttt{problem\_novelty.py}, \texttt{unified\_substrate.py}, \texttt{evolution\_archive.py}, \texttt{experience\_benchmark.py}, \texttt{v3\_runtime.py} and \texttt{driver\_learning.py}. Machine-readable \texttt{TaskEpisode} and \texttt{Lesson} schemas accompany the runtime.

The unified substrate is intentionally a read-only identity/query overlay. Scientific claims remain owned by the epistemic stack, operational lessons by the tool inventory, failures by the failure view, episodes by the experience ledger and method variants by the evolution archive. Cross-view edges make lineage inspectable without transferring authority between stores.
"""
impl_text = insert_after(impl_text, impl_anchor, MARKER + "\n" + impl_add, label="paper2 implementation v3")
write(impl, impl_text)

evalp = p2 / "sections" / "13_preregistered_evaluation.tex"
eval_text = read(evalp)
eval_anchor = r"\section{Preregistered empirical evaluation}"
eval_add = r"""
\subsection{Immediate v3 gate: matched continual-experience transfer}
The first empirical question introduced specifically by v3 is narrower than general research-agent superiority: does persistent external experience improve the same underlying model on fresh tasks when resources and task exposure are matched? The executable benchmark therefore compares two arms,
\[
\texttt{RESET\_BASELINE}
\qquad\text{and}\qquad
\texttt{LEARNING\_ENABLED},
\]
across a sequential development phase followed by fresh transfer. Every baseline task starts from the same initial state and may not mutate it. The learning arm forms one continuous state-hash chain through the development sequence. After development, the learned state is frozen, and every transfer task starts independently from that same frozen state; transfer task $T_1$ cannot teach $T_2$.

The packet freezes model identity, prompts, resource ceiling, tools, evaluator protocol, initial state, task order and transfer set before execution. It fails closed on state-chain breaks, baseline mutation, transfer contamination, resource-ceiling violations or task/arm mismatch. Reported outcomes include success, registered score, repeated-failure rate, model and preprocessing tokens, tool/retrieval calls and wall time. A positive transfer delta is an observed benchmark result only; the report is structurally incapable of granting a global capability claim.

The hostile near-miss stratum is essential. A learning architecture that always reuses prior lessons can improve repeated-task scores while becoming less safe out of scope. V3 therefore makes invalid transfer and false-lesson reuse direct falsifiers alongside positive transfer and reduced repeated failure.

\subsection{RAKL-triviality as structural novelty metrology}
Verified solutions are also classified by the strongest genuinely new problem-solving structure they required: \texttt{STORED}, \texttt{RAKL\_TRIVIAL}, \texttt{TRANSFER\_NOVEL}, \texttt{REPRESENTATION\_NOVEL}, \texttt{OPERATOR\_NOVEL}, \texttt{ONTOLOGY\_NOVEL} or \texttt{UNRESOLVED}. This does not rank intelligence. It asks whether a solution was retrieved, composed from existing resources, transferred by a witnessed mapping, or required a new representation, operator or ontology.

The resulting zero-invention and strict RAKL-trivial rates make a previously qualitative hypothesis measurable: as the substrate grows, does the rate of genuinely new problem-solving primitives decline on a declared task distribution? The implementation supplies the metrology, not the answer. A high RAKL-triviality claim requires empirical benchmark data and remains open in this paper.
"""
eval_text = insert_after(eval_text, eval_anchor, MARKER + "\n" + eval_add, label="paper2 evaluation v3")
write(evalp, eval_text)

sat = p2 / "sections" / "14_manuscript_saturation.tex"
sat_text = read(sat)
sat_anchor = r"\section{Manuscript saturation as a framework specialization}"
sat_add = r"""
\paragraph{Relation to v3 vector saturation.}
The v3 substrate tracks bounded flatness separately across knowledge, operator, experience-pattern, obstruction, relation, path and meta-method axes. Manuscript saturation is a publication projection of primarily the knowledge/relation/obstruction coordinates plus explicit proof and review obligations. A flat manuscript therefore does not imply that operator learning, experience consolidation or Self-RAKL evolution is flat, and a new method episode does not automatically reopen the manuscript unless it changes a publication-relevant semantic object. This separation prevents a living learning system from making every task episode a mandatory paper revision while still requiring any materially changed claim or evidence boundary to reopen the publication projection.
"""
sat_text = insert_after(sat_text, sat_anchor, MARKER + "\n" + sat_add, label="paper2 saturation v3")
write(sat, sat_text)

# ---------------------------------------------------------------------------
# Paper III — transfer witness becomes the v3 experience-transfer relation.
# ---------------------------------------------------------------------------
p3 = PUB / "paper-03-directional-structural-witnesses"
p3_main = p3 / "main.tex"
p3_text = read(p3_main)
p3_abstract = r"""
RAKL v3 can persist task episodes, consolidate scoped lessons and reuse experience without changing the underlying model weights, but the existence of a shared experience substrate does not determine when cross-domain reuse is valid. We study the transfer relation itself. A directional structural witness records context, quantity of interest, role mappings, preserved invariants, non-preserved properties, target boundaries, evidence and uncertainty, and is intended to license or reject movement of an episode, lesson or operator into a new problem fibre. In a deterministic conformance suite, the witness gate makes the intended decision on all six constructed Q2/Q3 cases across queue stability, positive feedback and threshold cascades; a deliberately semantic-only rule fails all six. We then froze and ran a leave-one-family-out diagnostic on 44 internally proposed Q1--Q4 pairs across 11 families. Witness features improved ROC-AUC by 0.086 and average precision by 0.097 over the strongest frozen lexical/tag controls, with Q2 true accept 1.00 and Q3 false accept 0.00. These are constructed, same-session proposal labels and do not establish an advantage over a modern content encoder. A fresh 16-item natural-domain source set and an opaque external-annotation packet are frozen, but zero external judgements or adjudications have been received; the exact strong semantic model asset is also not staged. The paper therefore treats the witness as a reproducible, fail-closed transfer formalism and a candidate evidential basis for v3 TRANSFER_NOVEL classifications, not as proof of natural cross-domain generalization, training-data efficiency or a universally valid learned skill substrate.
"""
p3_text = replace_abstract(p3_text, p3_abstract)
p3_anchor = r"\input{sections/02b_directionality_evidence}"
p3_inc = r"\input{sections/02c_v3_experience_transfer}"
if p3_inc not in p3_text:
    p3_text = p3_text.replace(p3_anchor, p3_anchor + "\n" + p3_inc, 1)
write(p3_main, p3_text)

p3_v3 = r"""
\section{Directional witnesses as RAKL v3 experience-transfer relations}
\label{sec:v3-transfer}

RAKL v3 makes experience persistence an implemented architectural fact but leaves transfer validity as an evidence question. A source \texttt{TaskEpisode} says what happened in one registered context. A versioned \texttt{Lesson} is a scoped abstraction over one or more episodes. Neither object is automatically applicable to a new target. The role of the directional structural witness is to supply an explicit candidate relation
\[
W_{s\rightarrow t}^{(q)}:
(E_s,L_s,\gamma_s)
\rightsquigarrow
(P_t,q,\gamma_t)
\]
whose obligations state which roles and invariants are preserved, which properties are not preserved, and which target boundaries would invalidate reuse.

This makes the witness directional in two senses. First, the target quantity of interest determines which source structure is load-bearing. Second, a valid mapping from source to target need not license the reverse mapping because scope, information loss or boundary conditions can be asymmetric. A witness is therefore not an embedding similarity score and not an equivalence class over tasks.

\subsection{Transfer can alter search priority without creating authority}
When a witness passes the registered structural and boundary gate, v3 may use the linked episode or lesson to increase retrieval priority, activate an already promoted tool, or place an operator path earlier in the search queue. The permitted inference is
\[
\text{witnessed applicability}
\Rightarrow
\text{eligible experience reuse},
\]
not
\[
\text{witnessed applicability}
\Rightarrow
\text{scientific claim true}.
\]
Scientific authority remains owned by the target problem's verification path. This is the cross-domain specialization of the framework invariant that experience-conditioned routing is not epistemic authority.

\subsection{Negative transfer is learned through an evidence ladder}
A failed transfer attempt first creates a non-success task episode. It does not immediately establish that the witness class, operator or source lesson is invalid. The system records the failure as observed-only, then permits competing diagnoses such as context mismatch, broken invariant, implementation defect, missing evidence or an unrelated downstream failure. Only discriminating evidence can promote a supported diagnosis, and only fresh replay/transfer can turn that diagnosis into a reusable boundary lesson.

The resulting discipline prevents one near-miss from becoming a global blacklist while still allowing repeated boundary-sensitive failures to improve later routing. It also makes negative-transfer history addressable: a future witness can explicitly inherit a known non-preserved property or target boundary rather than merely receiving a lower opaque score.

\subsection{Connection to RAKL-triviality}
V3 classifies a verified solution as \texttt{TRANSFER\_NOVEL} when no new primitive was invented but pre-existing problem-solving structure was transported into a new context by an explicit mapping witness. The directional witness studied here is a candidate evidence object for that classification. A solution should receive \texttt{TRANSFER\_NOVEL} only when the transfer relation is explicit, the target solution is independently verified, and resource ancestry shows that no new representation/operator/ontology was required.

This gives Paper III a narrower post-v3 claim. The framework already possesses a persistent experience substrate; this paper does not claim novelty for persistence itself. It asks whether one scientifically scoped, boundary-aware relation can make cross-domain reuse safer and more measurable than semantic resemblance alone. The natural-domain, strong-control and independent-annotation gates remain necessary before that question can receive an empirical answer.
"""
write(p3 / "sections" / "02c_v3_experience_transfer.tex", MARKER + "\n" + p3_v3.strip() + "\n")

near = p3 / "sections" / "01b_shared_experience_nearest_work.tex"
near_text = read(near)
near_add = r"""
\paragraph{Post-v3 residual.}
RAKL v3 now implements the persistent episode/lesson/tool substrate that earlier drafts treated as part of the broader motivation. That implementation narrows the paper rather than strengthening its empirical claim. The remaining question is whether the directional witness is a useful \emph{transfer-validity relation} inside such a substrate. Persistence, lesson consolidation and shared retrieval are therefore architectural premises supplied by the framework; boundary-sensitive cross-domain licensing remains the scientific object tested here.
"""
near_text = append_once(near_text, MARKER + "\n" + near_add)
write(near, near_text)

p3_eval = p3 / "sections" / "05_evaluation_plan.tex"
p3_eval_text = read(p3_eval)
p3_eval_add = r"""
\subsection{RAKL v3 fresh-transfer evaluation}
The downstream v3 experiment separates memory persistence from transfer validity. Both arms use the same underlying model, tools and frozen development experiences. A semantic-control arm retrieves and reuses candidate past experience using the strongest feasible content model; the witness arm applies the directional structural/boundary gate before the same promoted lessons or operators can influence routing. Every fresh-transfer task starts independently from the same frozen post-development state so one transfer case cannot teach the next.

Primary outcomes are target-task success/score, invalid-transfer or false-lesson reuse, repeated-failure rate, Q2 true accept, Q3 false accept and total resource use. Hostile near-misses are mandatory because an always-reuse policy can improve repeated-family tasks while increasing out-of-scope failures. A positive result requires material value beyond the strong content control under the same target verification rules; target scientific correctness cannot be inferred from the witness decision itself.

This experiment is distinct from the optional training-data redundancy hypothesis. Even if witness-gated experience reuse improves fresh inference, no claim about training-data efficiency follows without the separately authorized training experiment and full cost-to-capability accounting.
"""
p3_eval_text = append_once(p3_eval_text, MARKER + "\n" + p3_eval_add)
write(p3_eval, p3_eval_text)

# ---------------------------------------------------------------------------
# Paper IV — mathematical assurance becomes a v3 specialization.
# ---------------------------------------------------------------------------
p4 = PUB / "paper-04-verified-discovery"
p4_main = p4 / "main.tex"
p4_text = read(p4_main)
p4_abstract = r"""
Large language models can solve difficult mathematical exercises and increasingly operate inside formal proof systems, yet exercise solving is not the same task as mathematical research. RAKL v3 adds persistent external task experience, versioned procedural lessons and experience-conditioned routing, creating a new assurance question: how can a system learn which mathematical moves to try without allowing past success, repeated failure or model confidence to become mathematical authority? We present a mathematical-research assurance layer that separates five coordinates: specification alignment, theorem truth, novelty, research value and verifier trust. Proof attempts are preserved as immutable task episodes; failed search remains distinct from impossibility; reusable proof lessons and strategy motifs are proposal-side abstractions; and experience may reprioritize proof routes but cannot promote theorem truth. Formal proofs remain bound to exact statement hashes and audited for axioms and verifier identity, while novelty remains a bounded, cutoff-scoped and defeasible certificate. Under a sound checker and fail-closed update rule, generator hallucinations or experience-derived routing cannot by themselves promote a false theorem. Verified lemma checkpointing converts many local generator errors into rejected branches and search cost, subject to specification and verifier-trust assumptions. The result is a v3 specialization for auditable mathematical discovery, not an autonomous-mathematician claim, a proof that repeated search failure implies impossibility, or evidence of universal discovery superiority.
"""
p4_text = replace_abstract(p4_text, p4_abstract)

p4_v3 = r"""
\section{Experience-governed mathematical search in RAKL v3}

The v3 substrate distinguishes the mathematical research state from the system's accumulated task experience. A consequential conjecture test, representation change, tactic sequence, proof attempt or counterexample search can be frozen as a task episode containing the problem signature, relevant fibre snapshot, operators, action trace, observations, verification events, outcome, residual, provenance and cost. The episode records what happened; it does not certify why it happened.

A reusable mathematical lesson is a separate versioned object. It may encode a trigger such as a proof-state pattern, a scoped action such as changing representation or attempting a lemma family, expected effects, boundaries, supporting and contradicting episodes, a falsifier and validation obligations. Reflection can propose such a lesson, but proof-backed or fresh-transfer evidence is required before it is treated as reusable method state. The source episodes remain immutable even when a later lesson supersedes an earlier abstraction.

Experience may also alter the order in which admissible proof operators or paths are attempted. Let $\rho_t$ be a routing policy derived from previous episodes. Then the proposal process may be written schematically as
\[
a_t\sim G_\theta(\mathfrak M_t,E_t,\rho_t),
\]
where $E_t$ is the episode ledger. This changes search, not truth authority.

\begin{proposition}[Experience cannot promote theorem truth]
Assume theorem promotion requires an accepted proof artifact for the exact registered formal statement under an admitted verifier-trust profile. Then no update consisting only of task-episode storage, lesson consolidation or experience-conditioned routing can promote an unproved theorem.
\end{proposition}

\begin{proof}
Episode, lesson and routing updates have codomain in experience or search-policy state. By assumption, theorem promotion has an additional necessary premise: an accepted proof artifact bound to the registered statement and trust profile. Therefore experience can change which proof attempts are generated or prioritized but cannot satisfy the missing theorem-promotion premise by itself.
\end{proof}

\subsection{Failed search is not impossibility}
A failed proof attempt creates negative search history. It does not establish that the theorem is false, that no proof exists in the registered logic, or that a required operator is missing. A counterexample may refute a universal statement; a machine-checked impossibility theorem may establish a scoped negative result; ordinary search failure establishes neither. V3 therefore retains the ladder
\[
\text{failed episode}
\to\text{candidate diagnosis}
\to\text{discriminating evidence}
\to\text{verified boundary lesson},
\]
with no shortcut from repeated frustration to mathematical authority.

\subsection{Proof strategy motifs remain lossy abstractions}
Repeated successful operator sequences may nominate reusable strategy motifs. Such motifs can be valuable for retrieval and planning, especially in long proof DAGs with recurring bottlenecks, but they remain summaries of trajectories. A proof-backed lesson can be reliable as a method while still erasing local branch structure from the underlying episodes. The original trajectories and verification receipts therefore remain addressable whenever a later audit needs to reconstruct what was actually checked.
"""
p4_text = insert_before(p4_text, r"\section{Counterexample-first search}", MARKER + "\n" + p4_v3, label="paper4 v3 experience section")

p4_integrate = r"""
The v3 framework makes this specialization explicit. The mathematical state $\mathfrak M_t$ is one authority-owning view inside a broader persistent RAKL state whose episode ledger, lessons, tools, failure view and method variants can influence retrieval and planning without inheriting theorem authority. Mathematical proof receipts remain owned by the assurance layer; a unified substrate edge can show that a lesson was derived from a proof episode or that a tool succeeded on a task, but that lineage edge does not replace the proof artifact.
"""
p4_text = insert_after(p4_text, r"\section{RAKL integration}", MARKER + "\n" + p4_integrate, label="paper4 RAKL integration v3")

p4_sat = r"""
\section{Vector saturation and invention boundaries for mathematical research}

RAKL v3 separates several reasons a mathematical search may appear exhausted. Literature/knowledge routes, proof operators, recurring experience patterns, known obstructions, structural relations, successful composition paths and meta-methods can become locally flat at different times. Let
\[
\mathbf s^{\mathrm{math}}_t=(s_K,s_O,s_E,s_B,s_R,s_P,s_M)
\]
be the corresponding scoped saturation vector for a registered mathematical project. Flatness of $s_P$ says that declared proof-path route families added no retained path novelty in the active window; it does not prove the theorem unprovable. Flatness of $s_K$ says the registered novelty/literature routes were locally flat; it does not prove global novelty. Flatness of all declared coordinates remains bounded by their route families, cutoffs and resource envelope.

This distinction also gates invention. Being stuck does not establish a missing proof operator or representation. Escalation to representation/operator invention requires repeated stable residuals, exclusion of ordinary failures, bounded-flat relevant knowledge/operator/path routes, exhausted registered transfer routes and explicit evidence of a basis gap. Candidate invention then remains proposal-side until independent proof or protected assurance shows that the new operation closes the registered gap without violating theorem or verifier-trust invariants.

The architecture therefore permits aggressive creative search while making a negative claim difficult to mint. ``No proof found'', ``no known method retrieved'', ``representation gap suspected'' and ``impossibility proved'' are four different states with different evidence obligations.
"""
p4_text = insert_before(p4_text, r"\section{Preregistered evaluation}", MARKER + "\n" + p4_sat, label="paper4 vector saturation")

p4_conc = r"""
\paragraph{V3 interpretation.}
The framework can now accumulate and reuse mathematical task experience while keeping the proof/novelty/value authority coordinates separate. This strengthens the practical search architecture but not the theorem claim: future success may improve because the system remembers better routes, and future failure may become less repetitive because it remembers better boundaries, yet every promoted theorem still depends on the registered proof and verifier-trust chain. The scientific question left open is whether this experience substrate improves fresh mathematical-research outcomes under matched resources without increasing specification, novelty or trust failures.
"""
p4_text = insert_after(p4_text, r"\section{Conclusion}", MARKER + "\n" + p4_conc, label="paper4 conclusion v3")
write(p4_main, p4_text)

# ---------------------------------------------------------------------------
# Update reader-facing series map.
# ---------------------------------------------------------------------------
readme = ROOT / "publication" / "README.md"
readme_text = read(readme)
series = r"""
## RAKL v3 paper roles

The four papers are intentionally non-overlapping after the v3 refactor:

1. **Paper I — Epistemic Mechanics** formalizes the epistemic/authority projection of the broader v3 substrate.
2. **Paper II — RAKL for Evidence-Governed AI-Assisted Scientific Research** is the canonical whole-framework v3 architecture and evaluation paper.
3. **Paper III — Directional Structural Witnesses** studies the boundary-aware relation that may license cross-domain reuse of stored experience.
4. **Paper IV — Verified Discovery** specializes v3 to mathematical research, where experience may guide search but theorem authority remains verifier-gated.

The v3 implementation establishes software/formal architecture, not empirical superiority, universal continual-learning gain, high RAKL-triviality, autonomous scientific invention or absolute completeness.
"""
readme_text = append_once(readme_text, MARKER + "\n" + series)
write(readme, readme_text)

# Keep compatibility publication copies synchronized without reintroducing links.
for rel in (
    "paper-01-epistemic-mechanics/main.tex",
    "paper-01-epistemic-mechanics/sections/02b_v3_epistemic_projection.tex",
    "paper-02-rakl-evidence-governed-research/source/main.tex",
    "paper-02-rakl-evidence-governed-research/source/sections/03_formal/part01.tex",
    "paper-02-rakl-evidence-governed-research/source/sections/04_scientific_memory.tex",
    "paper-02-rakl-evidence-governed-research/source/sections/05_atomic_lifecycle.tex",
    "paper-02-rakl-evidence-governed-research/source/sections/06_three_geometries.tex",
    "paper-02-rakl-evidence-governed-research/source/sections/10_method_evolution.tex",
    "paper-02-rakl-evidence-governed-research/source/sections/11_reference_implementation.tex",
    "paper-02-rakl-evidence-governed-research/source/sections/13_preregistered_evaluation.tex",
    "paper-02-rakl-evidence-governed-research/source/sections/14_manuscript_saturation.tex",
    "paper-03-directional-structural-witnesses/main.tex",
    "paper-03-directional-structural-witnesses/sections/01b_shared_experience_nearest_work.tex",
    "paper-03-directional-structural-witnesses/sections/02c_v3_experience_transfer.tex",
    "paper-03-directional-structural-witnesses/sections/05_evaluation_plan.tex",
    "paper-04-verified-discovery/main.tex",
):
    sync(rel)

print("RAKL v3 manuscript rewrite complete")
