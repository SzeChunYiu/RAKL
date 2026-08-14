# Falsifiable experiment ladder — RAKL Neural Structural Bridge

**Status:** design/handoff. The development run already executed is explicitly marked below; every later stage requires a fresh freeze before outcome access.

## What “prove it works” means in this programme

Different claims require different evidence classes. Do not collapse them.

1. **Formal/software proof:** a contract follows from definitions or exact executable semantics.
2. **Known-world mechanism evidence:** a preregistered generated world has exact latent/verifier truth and the proposed mechanism beats named controls on fresh cases.
3. **Neural mechanism evidence:** an actually trained neural model shows the residual under matched data/compute and fresh OOD tests.
4. **LLM evidence:** an open/pretrained language model updated by the mechanism beats the strongest fair parent at full accounted cost.
5. **Shared-substrate evidence:** exact training structural identities add fresh inference-time transfer value.
6. **System-evolution evidence:** external RAKL failures compiled into bounded weight changes improve fresh end-to-end RAKL outcomes without authority leakage or hard regressions.

A stage does not imply any later stage.

---

# NB-0 — novelty and claim freeze

## Question

What exact residual is not already explained by conditional metric learning, relational/causal abstraction, adaptive data selection, shared structural inventories, modular adapters or self-improving agents?

## Required parents

At minimum:

- Conditional Similarity Networks;
- Abstractors / relational bottleneck;
- causal abstraction + IIT;
- structural-information/analogical-reasoning work;
- MATES / Group-MATES / STAT / Skill-It / MASS / STEPS;
- SciForma;
- Context Codec / formal slicing-abstraction controls for TCSQ;
- LatentSkill and at least one modular-adapter parent;
- DGM/Hyperagents and an external→weight compilation parent for cognitive compilation.

## Gate

`NOVELTY_RESIDUAL_EXECUTABLE` only if every proposed claim is written as a contrast against its strongest parent. Otherwise `ASSIMILATE_PARENT_AND_NARROW`.

Current branch decision: **pass only for the conjunction described in README; broad component claims are rejected.**

---

# NB-1 — exact task-conditioned quotient known world

## Objective

Test whether a validated QoI/context-conditioned quotient can preserve decision-relevant structure while ignoring irrelevant surface/domain variation and rejecting protected-coordinate/boundary near-misses.

## Generator

Create executable latent factors independently:

```text
P = principle / base relation
C = composition interface
B = boundary / regime
R = representation / notation
T = transfer-domain shell
V = surface / nuisance variation
Q = quantity of interest
K = context / assumptions
```

The gold quotient is derived from the executable target decision function, never from a perturbation name or an LLM judge.

For each `(Q,K)`, register:

- protected coordinates;
- erasable coordinates;
- forbidden-loss coordinates;
- source identity;
- reconstruction rule where representation change is lossy;
- original verifier.

## Required adversarial cases

1. **surface-far / structure-valid** pair;
2. **surface-near / structure-invalid** decoy;
3. same pair that is equivalent under `Q0` but not `Q1`;
4. boundary-only invalidation;
5. unseen composition of already seen factors;
6. fresh domain shell;
7. nuisance intervention that must not change the quotient;
8. protected-coordinate intervention that must change it;
9. missing-information case that must return `CANNOT_CHECK`;
10. reconstruction/original-verifier failure.

## Arms

A. raw surface embedding / direct model  
B. unconditioned structural representation  
C. Conditional-Similarity-style task-conditioned metric learner  
D. C + matched counterfactual nuisance/protected-coordinate augmentations  
E. relational-bottleneck / Abstractor-like parent  
F. IIT/causal-abstraction parent when a faithful causal model is available  
G. RAKL TCSQ neural representation with explicit protected/erased/boundary supervision  
H. oracle quotient upper bound

## Primary residual

```text
G - max(C,D,E,F)
```

on a frozen structural-OOD endpoint, not `G-A`.

Preferred primary endpoint: invalid-near-miss false accept under fresh `(Q,K)`-compatible structural OOD, with fresh-domain correct retrieval/decision as a co-primary only if preregistered.

## Hard constraints

- no worse protected-coordinate false merge than strongest parent by more than the preregistered harm margin;
- `CANNOT_CHECK` must not be coerced to accept/reject;
- no target-label leakage through generator IDs/templates;
- train/probe disjointness by content, not ID only;
- same parameter/data/step budget where scientifically feasible;
- full preprocessing/structural-label generation cost reported.

## Development result already executed

`known_world_neural_bridge.py` in this directory is **development only**. It uses a simpler generated world and four arms: raw surface, unconditioned structural, strong QoI-conditioned metric, explicit RAKL structural supervision.

Five-seed headline:

| Arm | adversarial triplet | fresh-domain retrieval | QoI-flip | boundary decoy |
|---|---:|---:|---:|---:|
| Raw surface | 0.000 | 0.380 ± 0.036 | 0.000 | 0.008 ± 0.008 |
| Unconditioned structural | 0.632 ± 0.037 | 0.556 ± 0.079 | 0.000 | 1.000 |
| Conditional metric | 0.949 ± 0.016 | 0.837 ± 0.044 | 0.940 ± 0.076 | 0.998 ± 0.004 |
| Explicit RAKL | 1.000 | 0.999 ± 0.001 | 1.000 | 1.000 |

Terminal:

```text
FEASIBILITY_SUPPORTED_RAKL_SPECIFIC_RESIDUAL_NOT_ESTABLISHED
```

Reason: the strongest generic conditional metric parent explains most of the effect and the development world is too easy to license a RAKL-specific claim.

---

# NB-2 — witness-aligned directional transfer known world

## Objective

Test the feature that generic analogy/relational learning does not automatically provide: **partial one-way transfer with explicit non-preservation and target-boundary obligations**.

## World

Generate source/target relational systems whose roles and relations are exact. A `StructuralWitness` contains:

- one-to-one role mapping;
- preserved relation/invariant subset;
- non-preserved property subset;
- required target boundary values;
- direction `source -> target`;
- QoI/context scope.

Construct hostile cases where:

- semantic/surface similarity is high but one load-bearing boundary flips;
- an irrelevant property changes and transfer should remain valid;
- the same changed property becomes relevant under another QoI and transfer must fail;
- reverse transfer is invalid although forward transfer is valid;
- two individually valid mappings cannot be composed because an interface obligation fails;
- a missing target fact forces `CANNOT_CHECK`.

## Arms

A. direct scalar transfer classifier  
B. strongest conditional metric parent  
C. relational-bottleneck/Abstractor parent  
D. IIT/causal-abstraction parent where faithful  
E. RAKL witness-aligned model with obligation-level heads/loss and fail-closed conjunction  
F. E without non-preserved properties  
G. E without boundary obligations  
H. E with witness direction symmetrized (hostile ablation)

## Primary endpoint

Invalid-transfer false accept on held-out **direction/boundary/QoI interaction combinations**.

## Required residual

E must distinguishably beat the strongest of A-D and every load-bearing ablation F-H must lose the corresponding protected capability. If D matches E, assimilate causal-abstraction machinery and narrow the RAKL claim to governance/representation rather than neural superiority.

---

# NB-3 — small open-model Neural TCSQ / witness training

Execute only after NB-1 or NB-2 establishes a nontrivial residual in a fresh known world.

## Model selection rule

Do not pick a model after seeing which one favors RAKL. Freeze a capability screen first. Select the smallest open model/checkpoint that:

1. clears the base-task learnability positive control;
2. fits the authorized compute envelope;
3. supports the required adapter/intervention hooks.

If none clears the screen, terminal is `CAPABLE_MODEL_UNAVAILABLE`, not a null RAKL result.

## First implementation

Prefer LoRA/adapters over full pretraining. This tests whether the mechanism can enter weights without pretending to create a new foundation model.

## Matched arms

A. base SFT/LoRA  
B. base + generic conditional contrastive/metric objective  
C. base + relational/causal parent objective (faithful strongest feasible parent)  
D. base + TCSQ protected/erased/boundary objective  
E. base + TCSQ + directional witness objective  
Optional F. dual-stream explicit structural channel, only if D/E suggest representation bottleneck

All arms share base checkpoint, raw examples, optimizer family, token/FLOP ceiling, split identities and evaluation cadence where feasible. Charge structural extraction/probe overhead.

## Endpoints

- fresh structure-known/domain-new performance;
- hostile semantic-near false transfer;
- boundary/regime violation rate;
- novel composition;
- representation invariance;
- calibration/abstention;
- retention/forgetting;
- total cost: preprocessing + forward/backward FLOPs + GPU time + wall time + verification.

## Promotion rule

Do not promote because E beats A. The load-bearing contrast is E versus the strongest faithful B/C parent, with hard harm constraints.

---

# NB-4 — learner-conditioned structural exposure / allocation

This is the existing #455/#461/#466 programme and must remain separate from NB-1/NB-2 representation learning.

## Current chronology

The Phase-0/1 v1 Qwen run is retracted as an instrument artifact. The corrected v2 runner is `experiments/training_ladder/phase1_v2.py`.

## Required order

1. run corrected v2 exposure ladder;
2. require learnability positive-control pass;
3. establish a learner-state-dependent structural residual;
4. only then freeze a minimal allocator;
5. run matched arms with primary estimand:

```text
ADAPTIVE_RAKL_STRUCTURAL - STATIC_RAKL_STRUCTURAL
```

6. compare with strongest model-/skill-aware parent;
7. preserve repetition/retention floor.

If adaptive = static with adequate power, the learner-conditioned extension is unsupported even if static RAKL beats random.

---

# NB-5 — exact shared train→inference substrate

Execute only after a learner-side RAKL mechanism has positive evidence.

## Freeze before inference outcomes

- exact trained checkpoint;
- exact structural-catalog content hash;
- exact structural schema/version;
- exact `structure_id`, role/relation/invariant/boundary identities used during training;
- exact witness schema;
- fresh inference-task generator/corpus;
- strongest semantic/content retrieval baseline;
- strongest latent/skill/causal parent;
- hostile false-transfer and boundary harm ceilings.

## Arms

A. no retrieval  
B. semantic/content retrieval  
C. strongest skill/latent/causal parent  
D. RAKL exact training-structure reuse  
E. RAKL ID-only ablation  
F. separately learned post-hoc structural representation

## Interpretation

- D > B/C with no hard harm: `SHARED_SUBSTRATE_SUPPORTED`.
- training helps but D adds no inference value: `TRAINING_ONLY_MECHANISM`.
- F required for gain: `TWO_MECHANISMS_NOT_SHARED_SUBSTRATE`.
- ID-only E matches D: explicit relations/invariants/boundaries did not carry the residual.

---

# NB-6 — epistemically governed cognitive compilation

## Objective

Test whether verified *external* RAKL failure structure can be converted into a bounded model update that improves future end-to-end RAKL operation better than generic reflection/distillation.

## Frozen loop

```text
external failure receipt
-> typed diagnosis
-> allowed training intervention family
-> frozen challenger proposal
-> weight update
-> fresh assurance corpus inaccessible during proposal
-> compare challenger vs incumbent
-> promote / reject / narrow
```

## Required controls

A. frozen incumbent  
B. generic reflection + distillation  
C. textual-skill→LoRA/LatentSkill-like parent  
D. generic failure-example fine-tuning  
E. RAKL diagnosis-bound structural compilation

## End-to-end endpoints

- fresh research/problem-solving success;
- invalid-transfer false accept;
- contradiction/boundary detection;
- calibration/abstention;
- regression suite;
- total cost;
- frequency of unjustified authority transitions (must remain zero by construction).

## Noninterference invariant

A successful training challenger may change model parameters and training projection. It may **not** alter evidence roots, source identities or scientific-authority state merely because training metrics improve.

---

# Terminal vocabulary

Use typed terminals rather than narrative spin:

- `MECHANISM_SUPPORTED_IN_REGISTERED_SCOPE`
- `FEASIBILITY_SUPPORTED_PARENT_RESIDUAL_NOT_ESTABLISHED`
- `PARENT_MATCHES_OR_BEATS`
- `STATIC_EQUALS_ADAPTIVE`
- `HARD_BOUNDARY_OR_RETENTION_HARM`
- `TRAINING_ONLY_MECHANISM`
- `TWO_MECHANISMS_NOT_SHARED_SUBSTRATE`
- `CAPABLE_MODEL_UNAVAILABLE`
- `UNDERPOWERED`
- `INSTRUMENT_DEFECT`
- `INVALID_CONTAMINATED`
- `CANNOT_CHECK`

Never turn `UNDERPOWERED`, `CANNOT_CHECK`, `CAPABLE_MODEL_UNAVAILABLE` or `INSTRUMENT_DEFECT` into a positive or null scientific result.