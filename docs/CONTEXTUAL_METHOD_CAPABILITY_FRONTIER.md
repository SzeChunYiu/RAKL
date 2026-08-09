# Contextual, Authority-Scoped Method Capability Frontier

Status: publication/theory layer. This document does not change active routing, promotion, the Constitution, or method-assimilation verdicts.

## 1. Goal

RAKL should be able to learn useful research operators from both its own residuals and external frameworks without becoming one ever-growing monolithic agent.

The target is not:

```text
find every attractive framework
-> concatenate every component
-> call the result stronger
```

The target is:

```text
discover an operator
-> atomize its capability
-> identify context / assumptions / resources / authority
-> normalize and deduplicate
-> preserve incompatibilities
-> evaluate on a frozen fiber-specific packet
-> retain only the justified local capability
```

This is the formal interpretation of **cumulative validated capability acquisition**.

## 2. Prior-art boundary

Several 2026 systems already make broad claims such as "self-evolving skills" or use held-out selection/frontiers.

- **EvoSkill** (`arXiv:2603.02766`) evolves reusable skills through failure analysis and retains agent programs on a Pareto frontier using held-out validation; it also reports zero-shot skill transfer.
- **SkillFoundry** (`arXiv:2604.03964`) mines heterogeneous scientific resources into validated executable skills with scope, I/O, environment assumptions, provenance and tests, and expands/repairs/merges/prunes the library.
- **EvoAgentBench** (`arXiv:2607.05202`) evaluates self-evolution through procedural ability transfer across multiple agentic domains.
- **Red Queen Gödel Machine** (`arXiv:2606.26294`) allows controlled evolution of the evaluator/utility across epochs.

Therefore RAKL must **not** claim novelty from Pareto selection, automatic skill discovery, evolving skill libraries, held-out ability transfer, or evaluator evolution in isolation.

The candidate RAKL contribution is narrower: contextual scientific-method assimilation where comparability, authority and gluing are themselves typed scientific objects.

## 3. Atomic method chart

For an atomic research fiber `f`, represent a validated or candidate operator as

\[
m=(f,\gamma,A,I,O,R,\alpha^+,\alpha^-,E,F,C),
\]

where:

- `gamma` is the valid scientific/task context;
- `A` is the assumption set;
- `I,O` are typed input/output contracts;
- `R` is the required resource envelope (model, tools, token/compute/time budget);
- `alpha+` is the scientific authority the operator may help mint;
- `alpha-` is authority it is forbidden to mint;
- `E` is validation/provenance evidence;
- `F` is known failure/negative history;
- `C` is the vector of registered meta-QoIs and costs.

The operator is a **local chart of method space**, not a globally ranked algorithm.

## 4. Comparability comes before dominance

Two operators are compared only when the registered comparison scope is compatible.

Define a comparison predicate

\[
\operatorname{Comparable}(m_i,m_j;s)
\]

that requires, for scope `s`:

```text
same atomic fiber / requested operation
compatible context coordinates
compatible assumptions or explicit transition witness
same registered consumer / meta-QoI semantics
matched or explicitly normalized resource envelope
compatible authority target
frozen common evaluation packet or licensed transport
```

If this predicate fails, RAKL does **not** force one global winner.

The appropriate state can instead be:

```text
PARALLEL_LOCAL_VIEW
```

or `CANNOT_CHECK` when the comparison itself is underidentified.

## 5. Blocking validity before Pareto optimization

Let the non-blocking objective vector contain quantities such as:

\[
q(m)=(\text{semantic recall},\text{contradiction detection},
\text{information gain},-\text{tokens},-\text{latency},\ldots).
\]

A method enters the candidate frontier only after all blocking invariants applicable to the scope pass:

```text
groundedness
non-fabrication
known-answer correctness
scope/authority honesty
negative-history preservation
reproducibility
causal/decision-time legality
```

No amount of efficiency or task score can Pareto-dominate a method that fails a blocking validity requirement.

Thus the frontier is **validity-gated**, not an ordinary unconstrained multi-objective leaderboard.

## 6. Context-indexed frontier

For fiber `f`, context `gamma`, authority target `alpha`, and resource/reference profile `r`, define the validated set

\[
\mathcal M^{(t)}_{f,\gamma,\alpha,r}.
\]

The local non-dominated subset is

\[
\mathcal F^{(t)}_{f,\gamma,\alpha,r}
=\operatorname{ND}(\mathcal M^{(t)}_{f,\gamma,\alpha,r}).
\]

This indexation is crucial. A literature-retrieval policy optimized for broad recall may coexist with another optimized for exact primary-source provenance. A formal verifier may dominate for formalizable deductions but be inapplicable to empirical source truth. A falsification policy may be useful for measurable rival hypotheses while an identified-set policy is needed when available evidence cannot identify one mechanism.

These are complementary charts, not necessarily contestants in one global ranking.

## 7. Assimilation dispositions

A newly discovered internal or external method can receive one of the following *theoretical* frontier dispositions after ordinary RAKL assimilation and evaluation:

```text
DOMINATES_LOCAL_INCUMBENT
    validated in the same comparison scope and non-dominated with a strict gain

ADDS_FRONTIER_POINT
    validated tradeoff or capability not dominated in that local scope

EQUIVALENT_TO_INCUMBENT
    semantic/operator duplicate; retain provenance, not fake method diversity

PARALLEL_LOCAL_VIEW
    useful but assumptions/context/authority do not glue with the incumbent

BLOCK / REJECT
    violates a blocking invariant or resurrects an unrepaired failed mechanism

CANNOT_CHECK
    identity, transition, resource normalization or evidence is insufficient
```

These names are not active runtime verdicts in this round. Runtime adoption requires a separately frozen benchmark.

## 8. Frontier growth is not monotonic truth

RAKL should not promise that the frontier can only grow.

New evidence can refute an operator, expose shared evidence ancestry, reveal hidden cost, or invalidate a transition witness. In that case the **active validated frontier may shrink or change**.

What remains monotonic is the historical evidence record:

```text
past validation
past null
past refutation
past assumptions
past supersession
```

A removed operator remains addressable as negative/superseded history.

## 9. External-framework learning loop

The external assimilation loop is:

```text
framework/source discovery
        ↓
atomic operator extraction
        ↓
source projection + provenance
        ↓
ontology/interface normalization
        ↓
semantic equivalence deduplication
        ↓
authority decontamination
        ↓
context / assumption / resource compatibility
        ↓
transition witness into target RAKL fiber
        ↓
frozen shadow benchmark
        ↓
local frontier disposition
        ↓
existing governed promotion
```

This lets RAKL learn, for example, one system's retrieval operator, another system's falsification strategy, another's structured world-state representation, and another's formal verification practice without importing the whole architecture or its unsupported authority assumptions.

## 10. Context efficiency

The method atlas can grow without making every LLM prompt grow.

Only compact operator descriptors and routing metadata need remain in the always-available index. The bounded-context compiler materializes the selected operator contract, its relevant assumptions/falsifiers, and the current task evidence on demand.

Thus:

\[
\text{growing method atlas}\neq\text{growing active prompt}.
\]

This is necessary if ordinary LLMs are to use a cumulatively improving RAKL package.

## 11. Required future benchmark

Before implementing runtime frontier maintenance/routing, freeze known-answer worlds covering at least:

1. same fiber/context, one method strictly dominates;
2. same validity, genuine cost/quality tradeoff -> two frontier points;
3. apparent winner that violates a blocking invariant -> excluded;
4. different assumptions -> parallel local views, not a winner;
5. different authority target -> no global comparison;
6. resource mismatch without normalization -> `CANNOT_CHECK`;
7. semantically duplicate external operator -> deduplicate;
8. newly refuted frontier member -> withdraw active status but preserve history;
9. stronger method only on development, not fresh assurance -> no strong evolution claim;
10. uncontrolled component aggregation versus governed contextual composition.

The primary empirical question is not whether a Pareto set can be computed. It is whether **contextual, authority-preserving method acquisition** reduces epistemic failure and cost relative to static curation and uncontrolled aggregation.

## 12. Paper claim boundary

Safe current wording:

> **RAKL treats external and internally generated research methods as contextual method charts. It can evaluate candidate operators under typed assumptions and authority scopes, while a proposed context-indexed capability frontier provides a principled target for cumulative method acquisition. Runtime frontier routing remains a preregistered future experiment.**

Do not currently claim that RAKL has empirically realized every strength of all other frameworks, or that the frontier mechanism is uniquely novel.
