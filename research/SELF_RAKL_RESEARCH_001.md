# SELF_RAKL_RESEARCH_001 — External Research Framework Atlas

Date: 2026-08-09

Object: `RAKL_METHOD`

Status: `NON_FLAT`

This is the first explicit use of RAKL to improve RAKL after initialization.

The core philosophy in `docs/CONSTITUTION.md` was frozen before adopting workflow changes. External systems are treated as **local charts/projections** of the research-method object, not as wholesale replacement candidates.

## Research routes

This round sampled multiple distinct traditions:

```text
scientific autonomous agents
deep research / knowledge curation
scientific RAG
automated workflow optimization
self-improving LM programs
agent tree search
long-horizon autonomous experimentation
Bayesian experimental design
scientific-agent benchmarks
Bayesian model workflow / criticism
multiverse/specification analysis
local-to-global consistency / sheaf methods
unseen-species / discovery saturation estimation
```

The objective was semantic gain, not repository count.

## Retained external projections

### 1. `Yuan1z0825/nature-skills`

Strong facets:

- manifest-driven routing;
- static reusable modules + dynamic workflow selection;
- source routing/fallback;
- structured experiment logging;
- terminology ledger / consistency sweep;
- mutually blind reviewer contexts frozen before synthesis;
- raw archive separated from promoted knowledge.

RAKL adoption:

Already integrated in v0.1. The new contribution of this round is to treat each of these as a replaceable meta-fiber rather than permanent implementation.

### 2. STORM / Co-STORM

Strong facets:

- perspective-guided question asking;
- simulated expert conversations to generate follow-up questions;
- a dynamic mind map for a shared conceptual space;
- human/agent collaborative discourse.

RAKL adaptation:

**Retain.** Add `PERSPECTIVE_DISCOVERY` before deep search. RAKL should explicitly ask which facets/perspectives are missing before generating queries.

The mind map becomes a typed **Knowledge Atlas**, not an untyped outline.

### 3. PaperQA2

Strong facets:

- metadata-aware scientific retrieval;
- LLM re-ranking and contextual summarization;
- agentic iterative query refinement;
- redundant metadata acquisition from multiple providers;
- explicit evaluation splits and contradiction-detection emphasis.

RAKL adaptation:

**Retain.** Separate `source discovery`, `evidence gathering`, and `claim synthesis`. Use redundant metadata/source identity resolution. Evidence chunks should be scored for the active facet/query rather than globally.

### 4. ResearchAgent

Strong facets:

- iterative research-problem generation grounded in a paper/knowledge store;
- multi-metric reviewer feedback;
- refinement focused on weak dimensions.

RAKL adaptation:

**Retain with modification.** Reviewer feedback becomes a residual routed to specific knowledge fibers. Multiple reviewers should be isolated/frozen when independence is claimed.

### 5. AI Scientist v2

Strong facets:

- progressive agentic tree search;
- experiment-manager control over research branches;
- open-ended exploration rather than one fixed template.

RAKL adaptation:

**Retain.** Replace purely linear recursion with a branchable `RESEARCH_TREE`. Each node is a fiber state and each branch is a versioned hypothesis/method path.

Tree search may rank branches by expected information gain, decision impact and cost, but cannot alter scientific acceptance thresholds.

### 6. InternAgent / long-horizon research systems

Strong facets:

- persistent experiment memory across sessions;
- full-cycle research task decomposition;
- deep research separated from experiment execution;
- solution evolution inside bounded hypothesis spaces.

RAKL adaptation:

**Retain.** Add persistent semantic and failure memory. Memory entries are immutable observations/results plus supersession edges, not prose that silently rewrites history.

### 7. Karpathy `autoresearch`

Strong facets:

- simple autonomous modify → run → evaluate → keep/discard loop;
- cheap fixed-duration experiments;
- `program.md` as research-organization code.

RAKL adaptation:

**Retain as one inner-loop mode, not the global philosophy.** It is excellent when the objective is stable and quantitative.

Risk: a binary keep/discard loop induces greedy hill climbing and can create a saturation wall.

RAKL therefore adds research-portfolio branches rather than using greedy replacement globally.

### 8. DSPy

Strong facets:

- declarative modular LM programs;
- optimize prompts/weights/program behavior against explicit metrics;
- reflection-based optimizers such as GEPA/SIMBA;
- composition of optimizers.

RAKL adaptation:

**Retain.** Each LLM-dependent atomic method step should eventually be representable as a module with typed input/output contract and benchmark metric.

Risk: optimizing a metric can overfit or corrupt philosophy. Blocking constitutional meta-QoIs remain lexicographic gates.

### 9. AutoFlow / AFlow

Strong facets:

- workflow generation/optimization as a search problem;
- code/natural-language workflows as candidate programs;
- tree/MCTS search over workflow structure.

RAKL adaptation:

**Retain for Class B workflow modules.** RAKL may automatically search alternative workflow topology, but only against frozen benchmark tasks and constitutional gates.

### 10. BED-LLM / Bayesian Experimental Design

Strong facet:

- select queries/actions that maximize expected information gain about the task.

RAKL adaptation:

**Retain.** Replace the current simple separation-per-cost heuristic with a hierarchy:

```text
expected decision-relevant information gain
expected mechanism discrimination
expected identified-set shrinkage
cost / latency / authority risk
```

Exact Bayesian EIG is optional; approximations must expose assumptions and calibration.

### 11. SAGA / goal-evolving agents

Strong facet:

- outer loop can revise objectives/scoring functions when the current objective is a poor proxy for scientific progress.

RAKL adaptation:

**Partial retain.** RAKL may recursively improve **non-constitutional meta-objectives** and benchmark metrics.

It may not autonomously optimize away blocking evidence invariants. Constitutional changes remain Class C amendments.

### 12. ScienceAgentBench / AstaBench / ResearchGym / MLE-bench

Strong facets:

- evaluate atomic scientific/engineering skills separately;
- reproducible execution environments;
- explicit cost accounting;
- objective or rubric-based evaluation;
- long-horizon/open-ended research benchmarks.

RAKL adaptation:

**Retain strongly.** Build `RAKLBench` with atomic tests before claiming end-to-end self-improvement.

Required benchmark categories:

```text
problem decomposition
facet discovery
false-split/false-merge detection
context-before-contradiction
representation equivalence
mechanism vs representation separation
residual routing
experiment/query selection
saturation detection
review independence
source/provenance correctness
end-to-end synthesis
```

### 13. Bayesian Workflow

Strong facets:

- iterative model building, predictive checking, validation and computational troubleshooting are one tangled workflow;
- many models are fit during understanding even if few survive conclusions.

RAKL adaptation:

**Retain.** Model criticism becomes a first-class loop rather than a final validation step. A model can be useful diagnostically even if it is not selected.

### 14. Multiverse / specification analysis

Strong facet:

- expose sensitivity to reasonable analytic choices instead of hiding researcher degrees of freedom.

RAKL adaptation:

**Retain with constrained-product rule.** RAKL does not brute-force every combination. It enumerates structurally compatible decision forks and estimates which atomic choices drive outcome sensitivity.

Failed combinations are retained as evidence.

### 15. Local-to-global / sheaf consistency

Strong facet:

- heterogeneous local views can sometimes be glued into a global object by checking compatibility on overlaps;
- inconsistency on overlaps diagnoses where global synthesis fails.

RAKL adaptation:

**Retain as the formal generalization of the Apple Principle.** See `docs/KNOWLEDGE_ATLAS_PRINCIPLE.md`.

A full sheaf implementation is optional and must be earned by a use case.

### 16. Unseen-species / species-accumulation methods

Strong facet:

- use frequency of rare discoveries and discovery curves to estimate remaining unseen diversity.

RAKL adaptation:

**Retain as diagnostic only.** Semantic objects are not iid species and RAKL search is adaptive, so Good–Turing/Chao/capture-recapture style estimates cannot certify saturation. They can estimate novelty risk and identify underexplored routes.

See `docs/KNOWLEDGE_SATURATION.md`.

## New RAKL meta-fibers opened

This research round adds the following retained semantic objects:

```text
META_N001 perspective-guided facet/question discovery
META_N002 typed dynamic Knowledge Atlas / chart transition map
META_N003 research-tree search instead of single-path recursion
META_N004 research-portfolio scheduler with exploit/diversify/moonshot/meta budgets
META_N005 modular LM-method optimization under constitutional gates
META_N006 decision-relevant expected-information-gain query/experiment selection
META_N007 atomic-capability benchmark before end-to-end self-improvement claims
META_N008 persistent immutable semantic/failure memory
META_N009 constrained multiverse sensitivity analysis
META_N010 objective-evolution limited to non-constitutional meta-QoIs
META_N011 semantic unseen-mass saturation diagnostic
META_N012 knowledge-saturation versus problem-closure state separation
```

The round is therefore `NON_FLAT`.

## Research portfolio scheduler

A long-running self-improving research method should not allocate all compute to the current best path.

Default conceptual budget:

```text
EXPLOIT     55%  improve/test the strongest current path
DIVERSIFY   25%  test alternative representations/mechanisms/workflows
MOONSHOT    10%  structurally alien or high-risk hypotheses
META_RAKL   10%  improve the research process itself
```

These are defaults, not scientific constants. The scheduler is itself a self-RAKL fiber.

Rules:

- failed moonshots remain in the trial ledger;
- exploit cannot consume 100% solely because it has short-term metric advantage;
- diversification should target epistemically distinct branches, not trivial prompt variants;
- a saturation wall increases diversify/moonshot/meta allocation;
- a high-value native residual can temporarily concentrate budget on one implicated fiber.

## Next implementation targets

1. `SaturationTracker` with route coverage, semantic novelty and reversible states.
2. `ConstitutionGuard` for Class A/B/C method changes.
3. `ResearchPortfolioScheduler`.
4. `RAKLBench` minimal known-answer suite.
5. perspective-discovery workflow before literature queries.
6. tree-search data structure for parallel hypothesis/fiber branches.
7. immutable run/semantic-memory schema.

## What was NOT adopted

- unrestricted self-modification of constitutional principles;
- one scalar “research quality” objective;
- automatic promotion because a generated paper/report looks persuasive;
- pure greedy keep/discard as the global search policy;
- same-context multi-agent personas as independent review;
- paper-count based saturation;
- brute-force unconstrained Cartesian multiverse search.

## Saturation state

`RAKL_METHOD` is **not saturated**.

This first pass added 12 retained meta-objects. Future rounds should recurse into each atomic meta-fiber and search alternative implementations until route-specific and independent semantic novelty becomes flat.
