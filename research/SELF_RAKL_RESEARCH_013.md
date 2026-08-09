# SELF-RAKL Research Round 013 — Evidence-Governed Method Assimilation

Date: 2026-08-09

Starting `main`: `959899f3689b29bba97e5172c9071888473f511f`

Entering status: `ACTIVE_NON_FLAT`.

## 1. Baseline audit and concurrency history

The work originally began while `main` was `e39a7d2a6fe9b3c76f2ea68e1b32cdce9cfa8812`. A method-assimilation benchmark was frozen on branch `self-rakl/round-012-assimilation` at commit `87dfe4e2fdd77f0610a164532e38ce383ed82e56`, implementation was staged, and exact branch-head CI for stale candidate `49d6b81cd7f798ab48cb21f420a8faccde56d0ee` completed successfully.

Before promotion, `main` advanced independently through Round-012 similarity research to `959899f3689b29bba97e5172c9071888473f511f`. RAKL therefore refused to move `main` to the stale candidate. No force update occurred.

The current run then restarted from the live head and re-audited:

```text
main = 959899f3689b29bba97e5172c9071888473f511f
open issues = 0
open pull requests = 0
Constitution SHA = 4d456ceab32122391c830fe8586766cf0e0037aa
baseline test workflow = completed success
baseline trusted-parent workflow = skipped, not counted as a pass
Round-012 similarity lane = ACTIVE_NON_FLAT
```

Because Round 012 was now occupied, the assimilation lane was renumbered to Round 013 and new meta-fiber IDs begin at N046. The Round-013 benchmark copies the already-frozen behavioral predictions without changing thresholds or falsifiers; only transport identity, round number and starting main are changed.

## 2. Research object

The user asked RAKL to learn from many external scientific-research systems and recursively upgrade itself while applying, rather than naming, the underlying knowledge.

The resulting meta-object is:

> How can RAKL assimilate useful external method operators without importing unsupported epistemic authority, double-counting equivalent methods, erasing failed method history, or forcing incompatible methods into one global workflow?

## 3. Frozen expert panel

Six role-separated passes were fixed before synthesis.

1. **Scientific workflow / component architect** — modular interfaces, orchestration, lifecycle and dependency boundaries.
2. **Formal methods / contract researcher** — assume-guarantee contracts, fail-closed validation and composition obligations.
3. **Agent skill-ecosystem maintainer** — skill discovery, versioning, validation, technical debt and retirement.
4. **Scientific epistemologist** — claim scope, provenance, representation-versus-mechanism and authority leakage.
5. **Adversarial benchmark reviewer** — hostile imports, candidate self-report, negative-history replay, false equivalence and forced fusion.
6. **Methods-paper reviewer** — novelty boundary and which claims belong in a publishable scientific-method contribution.

These passes shared one orchestration context. They improve coverage but are **not** counted as independent or mutually blind review.

## 4. Fresh external projections

### 4.1 SkillOps — library-time maintenance is its own problem

SkillOps (arXiv:2605.13716) treats skills as typed contracts and manages a skill ecosystem over utility, compatibility, risk and validation.

**Consequence:** typed skill contracts and skill-library maintenance are prior art. RAKL must not claim modular contracts themselves as novel.

### 4.2 SkillFoundry — scientific artifacts can be compiled into validated skills

SkillFoundry (arXiv:2604.03964) converts heterogeneous scientific resources into skills carrying scope, I/O, environment assumptions, provenance and tests, then expands, repairs, merges or prunes the library.

**Consequence:** scientific resource-to-skill compilation and validated skill evolution are prior art. RAKL's distinct question is what epistemic transition, if any, an imported operator may authorize.

### 4.3 HASP — skills can be executable interventions

HASP (arXiv:2605.17734) turns skills into executable program functions that intervene in failure-prone states and evolve under validation.

**Consequence:** executable capability is separated from epistemic authority. A component may change an execution trace without being licensed to mint stronger scientific claims.

### 4.4 SkillSmith — co-evolution and anti-pattern memory

SkillSmith (arXiv:2606.01314) co-evolves skills and tools, models complementarity/conflict and preserves failure anti-patterns with causal attributions and remedies.

**Consequence:** anti-pattern memory corroborates, rather than originates, RAKL's negative-history principle. A failed method rediscovered under a new label should not receive fresh authority merely because its name changed.

### 4.5 S1-NexusAgent — dynamic scientific tool retrieval and trajectory distillation

S1-NexusAgent (arXiv:2602.01550) dynamically retrieves heterogeneous scientific tools and distills successful trajectories into reusable Scientific Skills.

**Consequence:** dynamic routing and trajectory-to-skill distillation are candidate method modules. They remain subject to matched evaluation and cannot write canonical scientific authority directly.

### 4.6 Scientific Agent Skills and nature-skills — versioning, raw archives and review boundaries

The current K-Dense scientific-agent-skills repository exposes provenance/version practices and warns that imported skills may execute code or access network/files. The current nature-skills repository uses small routed modules, multi-source fallback, deduplication, a raw archive boundary and explicit freeze-before-synthesis reviewer discipline.

**Consequence:** source version, dependency identity, raw-versus-promoted knowledge and review isolation belong in the assimilation contract. Fixed scoring weights and repository defaults remain local implementation choices rather than universal epistemic law.

## 5. Central refinement: external method reputation is not an assimilation certificate

The panel rejected the naive lifecycle:

```text
external framework looks strong
-> copy component
-> put it in the active pipeline
```

Instead, one external atomic method operator receives the contract

\[
C_m=(I_m,O_m,\gamma_m,A_m,P_m,F_m,\alpha_m^+,\alpha_m^-,T_m,B_m),
\]

where:

- `I/O` are input/output schemas;
- `gamma` is context scope;
- `A` contains assumptions;
- `P` contains provenance and dependencies;
- `F` contains failure modes;
- `alpha+` is authority the operator may mint;
- `alpha-` is authority it must not mint;
- `T` names an explicit transition into the target RAKL fiber;
- `B` names the frozen benchmark.

This yields `METHOD_OPERATOR_AUTHORITY_ENVELOPE`.

## 6. Authority decontamination precedes method competition

External capabilities are normalized to the authority actually justified by their evidence before comparison or composition.

Forbidden silent upgrades include:

```text
retrieval              -> atomic claim support
prediction              -> mechanism identification
formal proof            -> empirical truth of premises
agent consensus         -> independent evidence
memory entry            -> canonical knowledge
citation multiplicity   -> independent evidence lineage
```

If requested authority lies outside `may_mint` or inside `must_not_mint`, the proposed assimilation is rejected before shadow testing.

## 7. Assimilation requires a transition witness

Interface resemblance is not sufficient. RAKL requires an evidence-bearing map

\[
T_{m\rightarrow f}: O_m \rightarrow I_f.
\]

The map identifies how representation, context, assumptions, provenance and authority are preserved or transformed.

Missing transition evidence yields `CANNOT_CHECK`; refuted transition evidence yields `BLOCK`.

This yields `ASSIMILATION_TRANSITION_WITNESS`.

## 8. External methods form an atlas too

The Knowledge Atlas applies recursively to RAKL's method library.

Three legitimate non-active synthesis results are:

```text
EQUIVALENT_TO_INCUMBENT
PARALLEL_LOCAL_VIEW
ELIGIBLE_FOR_SHADOW
```

An equivalent operator is deduplicated instead of increasing method count. A locally valid but assumption-incompatible operator remains a parallel method chart instead of being forced into the incumbent pipeline or globally rejected.

This yields `PARALLEL_METHOD_ATLAS_VIEW`.

## 9. Negative method history acts as a veto signal

If a proposed operator semantically matches a preserved failed anti-pattern, the default result is `REJECT`. A future re-entry must carry explicit supersession evidence in a separately frozen evaluation.

This yields `ASSIMILATION_NEGATIVE_HISTORY_VETO`, a recursive consequence of existing immutable negative history rather than a new constitutional axiom.

## 10. Frozen benchmark before implementation

The original assimilation worlds were frozen before implementation on the stale branch. After `main` advanced independently, Round 013 reproduced those worlds without changing behavioral predictions, thresholds or falsifiers and committed the transport-renumbered benchmark as `13e883e6a1f7acecccec034ffb153d8542adf130` before recreating `src/rakl/assimilation.py`.

The 15 worlds test:

- clean shadow eligibility;
- self-contradictory authority contracts;
- requested authority outside the allowed envelope;
- missing provenance;
- candidate self-report;
- absent and refuted transition maps;
- unfrozen benchmark;
- unknown authority scope;
- incomplete assumptions/context;
- semantic equivalence deduplication;
- incompatible but locally valid parallel views;
- known negative-history replay;
- unknown comparison status.

Registered meta-QoIs are authority-leakage rejection, `CANNOT_CHECK` honesty, parallel-view preservation, semantic deduplication, negative-history replay rejection and clean shadow-eligibility precision.

## 11. Supporting implementation

`src/rakl/assimilation.py` adds:

```text
MethodOperatorContract
AssimilationEvidence
AssimilationVerdict
AssimilationReport
evaluate_method_assimilation
```

The evaluator can return:

```text
ELIGIBLE_FOR_SHADOW
EQUIVALENT_TO_INCUMBENT
PARALLEL_LOCAL_VIEW
BLOCK
REJECT
CANNOT_CHECK
```

It deliberately has **no `ACTIVE` verdict**. A clean operator only becomes eligible to face the existing frozen shadow-test / promotion protocol.

Hostile tests assert the frozen behaviors, immutability of the contract and the invariant that the evaluator never activates a method itself.

## 12. Recursive interaction with Round-012 similarity theory

The concurrent Round-012 similarity lane added admissible mapping-capacity contracts, explicit query/probe families and immutable distinguishing-probe memory. This creates a genuine new residual for method assimilation:

> a method transition witness can itself be made vacuous if the allowed adapter/mapping family is expanded after seeing the desired external component.

RAKL does **not** modify the current v0.1 gate after observing that result. Instead it opens `META_N048_ASSIMILATION_TRANSITION_VERIFICATION`, whose future benchmark must freeze admissible method-map families and distinguishing probes before implementation.

This is recursive RAKL in action: one method fiber constrains another through an explicit transition, while benchmark chronology prevents post-hoc activation.

## 13. Novelty after deduplication

Not counted as novel:

- modular agent skills;
- typed skill contracts;
- scientific resource-to-skill mining;
- validated/self-evolving skill libraries;
- executable skill programs;
- dynamic tool retrieval;
- skill/tool co-evolution;
- anti-pattern memory;
- provenance/version pinning;
- small routed research modules;
- generic mapping-capacity warnings.

Retained RAKL-specific synthesis objects:

1. `METHOD_OPERATOR_AUTHORITY_ENVELOPE`
2. `ASSIMILATION_TRANSITION_WITNESS`
3. `PARALLEL_METHOD_ATLAS_VIEW`
4. `ASSIMILATION_NEGATIVE_HISTORY_VETO`

The paper claim is therefore narrowed to authority-preserving scientific-method assimilation under a contextual atlas and governed promotion boundary, not generic modularity or skill evolution.

## 14. Saturation verdict

```text
RAKL_METHOD = ACTIVE_NON_FLAT
method_assimilation_lane = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

Real external operators have not yet been compared under matched tasks/budgets, and transition witnesses are recorded but not semantically verified by the support module itself.

## 15. Next discriminators

1. `META_N047_REAL_COMPONENT_ASSIMILATION_BENCHMARK` — instantiate real retrieval, claim-evidence, falsification, verifier, memory and experiment-selection operators; compare uncontrolled aggregation, fixed curation and contextual RAKL assimilation.
2. `META_N048_ASSIMILATION_TRANSITION_VERIFICATION` — freeze adapter-map capacity, schema/assumption/authority preservation and distinguishing probes before implementing semantic transition verification.
3. Add paper ablations removing the authority envelope, equivalence deduplication and parallel-view preservation independently.
4. Continue adversarial prior-art review before promoting assimilation into a headline novelty claim.

The Constitution remains unchanged.
