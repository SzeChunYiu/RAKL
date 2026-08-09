# SELF-RAKL Research Round 012 — Evidence-Governed Method Assimilation

Date: 2026-08-09

Starting `main`: `e39a7d2a6fe9b3c76f2ea68e1b32cdce9cfa8812`

Entering status: `ACTIVE_NON_FLAT`.

## 1. Baseline audit

The run began by checking current `main`, recent commits, open issues and pull requests, the Constitution, Self-RAKL documents, Knowledge Atlas/saturation doctrine, Round-011 research/receipt/validation, test workflow and current source/test structure.

Observed baseline:

```text
main = e39a7d2a6fe9b3c76f2ea68e1b32cdce9cfa8812
open issues = 0
open pull requests = 0
current-head push test workflow = completed success
current-head trusted-parent workflow = skipped, not counted as a pass
Constitution = unchanged
saturation = ACTIVE_NON_FLAT
```

The user requested that RAKL learn from the mechanisms behind many external research methods and recursively improve itself, while avoiding cultural names in the formal framework. This creates an explicit self-RAKL object:

> How can RAKL assimilate useful external method operators without importing unsupported epistemic authority or forcing incompatible methods into one global workflow?

## 2. Frozen expert panel

Six role-separated passes were fixed before synthesis.

1. **Scientific workflow / component architect** — modular interfaces, orchestration, lifecycle and dependency boundaries.
2. **Formal methods / contract researcher** — assume-guarantee contracts, fail-closed validation and composition obligations.
3. **Agent skill-ecosystem maintainer** — skill discovery, versioning, validation, technical debt and retirement.
4. **Scientific epistemologist** — claim scope, provenance, representation-versus-mechanism and authority leakage.
5. **Adversarial benchmark reviewer** — hostile imports, self-report, negative-history replay, false equivalence and forced fusion.
6. **Methods-paper reviewer** — novelty boundary and which claims belong in a publishable scientific-method contribution.

These passes shared one orchestration context. They increase coverage but are **not** independent or mutually blind review.

## 3. External projections from materially different routes

### 3.1 SkillOps — library-time maintenance is its own problem

SkillOps (arXiv:2605.13716) models skills as typed contracts and maintains a skill ecosystem graph over utility, compatibility, risk and validation. This is close prior art to any broad claim that RAKL invents typed method-module contracts.

**RAKL consequence:** method-library maintenance becomes a distinct meta-fiber; contract modularity itself is not counted as novelty.

### 3.2 SkillFoundry — scientific artifacts can be compiled into validated skills

SkillFoundry (arXiv:2604.03964) converts heterogeneous scientific resources into skills containing scope, I/O, execution steps, environment assumptions, provenance and tests, then expands, repairs, merges or prunes the library.

**RAKL consequence:** scientific skill mining and closed-loop validated skill evolution are prior art. RAKL must add value at the epistemic transition/authority layer rather than claim resource-to-skill compilation.

### 3.3 HASP — skills can be executable interventions

HASP (arXiv:2605.17734) turns skills into executable program functions that can intervene in failure-prone states and evolve under validation.

**RAKL consequence:** a skill's ability to intervene in an agent loop is a mechanism/execution capability, not scientific authority. Executability and epistemic authority remain separate axes.

### 3.4 SkillSmith — co-evolution and anti-pattern memory

SkillSmith (arXiv:2606.01314) co-evolves skills and tools, models complementarity/conflict and records failure anti-patterns with causal attributions and remedies.

**RAKL consequence:** anti-pattern memory is an external corroboration of RAKL's immutable negative-history principle. Rediscovered failed methods should be detected semantically rather than reintroduced under a new label.

### 3.5 S1-NexusAgent — dynamic scientific tool retrieval and trajectory distillation

S1-NexusAgent (arXiv:2602.01550) dynamically retrieves large heterogeneous scientific tool sets and distills successful trajectories into reusable scientific skills.

**RAKL consequence:** dynamic tool/skill routing is a replaceable method operator. It should compete under matched budgets and cannot by itself modify canonical authority.

### 3.6 Scientific Agent Skills and nature-skills — portable packages need lifecycle and boundary discipline

The current K-Dense scientific-agent-skills repository exposes provenance metadata, version pinning and a security warning that skills can execute code. The current nature-skills repository separates small routed skills, uses multi-source fallback/deduplication, maintains read-only raw literature boundaries and requires frozen reviewer outputs before synthesis.

**RAKL consequence:** source version, dependencies, archive boundaries and review isolation belong in the assimilation contract. Fixed scoring weights or workflow defaults are local implementation choices, not universal epistemic law.

## 4. Central refinement: external method reputation is not an assimilation certificate

The panel rejected the naive rule:

```text
external framework performs well
-> copy component
-> add to active RAKL pipeline
```

Instead, RAKL now represents one atomic external method operator with a typed contract:

\[
C_m=(I_m,O_m,\gamma_m,A_m,P_m,F_m,\alpha_m^+,\alpha_m^-,T_m,B_m),
\]

where:

- `I/O` are input/output schemas;
- `gamma` is context scope;
- `A` assumptions;
- `P` provenance/dependencies;
- `F` known failure modes;
- `alpha+` authority the operator may mint;
- `alpha-` authority the operator must not mint;
- `T` an explicit transition map into the target RAKL fiber;
- `B` the frozen benchmark identity.

This opens the retained object `METHOD_OPERATOR_AUTHORITY_ENVELOPE`.

## 5. Authority decontamination before comparison

A method operator is reduced to the authority actually justified by its evidence before it can be compared or composed.

Invalid upgrades include:

```text
retrieval -> claim support
prediction -> mechanism
formal proof -> empirical truth of premises
agent consensus -> independent evidence
memory entry -> canonical truth
citation multiplicity -> evidence independence
```

Requested authority outside the verified `may_mint` envelope, or inside `must_not_mint`, is rejected before shadow testing.

## 6. Assimilation requires a transition witness

Interface resemblance is insufficient. RAKL requires an evidence-bearing map

\[
T_{m\rightarrow f}: O_m \rightarrow I_f.
\]

This map states how representation, assumptions, scope, provenance and authority are preserved or transformed.

Missing transition evidence yields `CANNOT_CHECK`; refuted transition evidence yields `BLOCK`.

This opens `ASSIMILATION_TRANSITION_WITNESS` and a child fiber for executable semantic verification.

## 7. External methods form an atlas too

The Knowledge Atlas principle applies recursively to RAKL's method library.

Three non-active synthesis outcomes are legitimate:

```text
EQUIVALENT_TO_INCUMBENT
PARALLEL_LOCAL_VIEW
ELIGIBLE_FOR_SHADOW
```

An equivalent method is deduplicated. A locally valid method whose assumptions do not glue to the incumbent remains a parallel local method view. It is not forced into one universal pipeline and is not rejected merely because it serves a different context.

This opens `PARALLEL_METHOD_ATLAS_VIEW`.

## 8. Negative method history is a veto signal

If a proposed operator matches a preserved failed anti-pattern, the default outcome is rejection rather than rediscovery credit. A later re-entry requires explicit supersession evidence in a future fiber.

This is a recursive consequence of existing negative-history preservation, not a new constitutional axiom.

## 9. Frozen benchmark before implementation

`SELF_RAKL_RESEARCH_012_FROZEN_BENCHMARK.json` was committed at `87dfe4e2fdd77f0610a164532e38ce383ed82e56` before `src/rakl/assimilation.py` existed.

The 15 worlds cover:

- clean shadow eligibility;
- self-contradictory authority contract;
- requested authority outside envelope;
- missing provenance;
- candidate self-report;
- absent and refuted transition maps;
- unfrozen benchmark;
- unknown authority scope;
- incomplete assumptions/context;
- semantic equivalence deduplication;
- incompatible but locally valid parallel view;
- known negative-history repeat;
- unknown comparison status.

Registered meta-QoIs are authority-leakage rejection, `CANNOT_CHECK` honesty, parallel-view preservation, semantic deduplication, negative-history replay rejection and clean shadow-eligibility precision.

## 10. Supporting implementation

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

It intentionally has **no `ACTIVE` outcome**. Even a clean operator only becomes eligible for the existing frozen shadow-test/promotion process.

Hostile tests cover the frozen behaviors and check that the support object is immutable and never activates a method by itself.

## 11. Novelty after deduplication

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
- small routed research modules.

Retained RAKL-specific synthesis objects:

1. `METHOD_OPERATOR_AUTHORITY_ENVELOPE`
2. `ASSIMILATION_TRANSITION_WITNESS`
3. `PARALLEL_METHOD_ATLAS_VIEW`
4. `ASSIMILATION_NEGATIVE_HISTORY_VETO`

The paper claim is therefore narrowed to authority-preserving scientific method assimilation under a contextual atlas and governed promotion boundary, not generic modularity or skill evolution.

## 12. Saturation verdict

```text
RAKL_METHOD = ACTIVE_NON_FLAT
method_assimilation_lane = ACTIVE_NON_FLAT
same_context_flat_rounds = 0
independent_flat_rounds = 0
```

The lane remains open because real external operators have not yet been compared under matched tasks/budgets and transition witnesses are recorded but not semantically verified by the support module itself.

## 13. Next discriminators

1. `META_N043_REAL_COMPONENT_ASSIMILATION_BENCHMARK` — instantiate real retrieval, claim-evidence, falsification, verifier, memory and experiment-selection operators and compare uncontrolled aggregation, fixed curation and RAKL contextual assimilation.
2. `META_N044_ASSIMILATION_TRANSITION_VERIFICATION` — verify schema/assumption/authority preservation rather than accepting a boolean external statement.
3. Reuse the Round-011 witness algebra only where a method-transition relation truly has the same structure; do not collapse method equivalence into scientific analogy.
4. Add a paper ablation of authority envelopes and parallel-view preservation.
5. Continue adversarial prior-art search before elevating the assimilation layer into a novelty claim.

The Constitution is unchanged.
