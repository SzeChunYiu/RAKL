# RAKL × LLM Structural Bridge — research synthesis and handoff

**Date:** 2026-08-13  
**Branch:** `research/llm-structural-bridge-20260813`  
**Base:** `main` at the branch-creation point  
**Status:** research synthesis + development known-world evidence. No new LLM-training efficacy claim is granted by this directory.

## Mission

This lane asks a narrower question than “can structure improve an LLM?” and a broader question than “can RAKL prompt an LLM better?”

> Can RAKL's explicit, directional, QoI-/context-/boundary-scoped structural substrate become a shared computational object across external reasoning, neural representation learning, weight updates, and inference-time transfer, while preserving a hard separation between scientific authority and learner utility?

The work is reviewed through five internal lenses (not independent reviewers):

1. **Neural representation:** what must be encoded or erased in latent space?
2. **Training dynamics:** where can RAKL enter the gradient/update process?
3. **Transfer/formal structure:** what exactly transports, in which direction, and under which boundaries?
4. **Epistemic governance:** what may change model behavior without changing scientific authority?
5. **Adversarial prior art/evaluation:** which simpler parent already explains the proposed function?

## Executive decision

The broad ingredients are heavily occupied. The strongest surviving RAKL opportunity is therefore a **conjunction**, not any one ingredient:

```text
Task-/QoI-conditioned structural quotient
+ explicit protected/erased coordinate ledger and sufficiency validation
+ directional StructuralWitness with preserved AND non-preserved properties
+ applicability boundaries and hostile near-misses
+ exact identity reuse across external reasoning, learning, and inference
+ checkpoint-bound learner state / training projection
+ fresh-assurance promotion
+ scientific-authority noninterference
```

A result on only one row below does not establish the conjunction.

## Evidence ledger as of this branch

| Lane | Current evidence | Honest status |
|---|---|---|
| Full structural applicability contract | Preregistered objective known-world, 4 exact-verifier families, `n=576`; full contract matched all 576 decisions; mechanism-only control had 25% invalid false-accepts; paired Brier residual 0.120, bootstrap 95% CI [0.0938, 0.1481] | **SUPPORTED in registered exact-verifier scope**; not raw-prose extraction or broad natural-domain transfer |
| External LLM applicability gate | Frozen GLM-5.2 comparator, fresh exact-verifier `n≈504`: invalid false-accept Direct 0.527 [0.460,0.589], Free-CoT 0.536 [0.473,0.603], RAKL gate 0.339 [0.277,0.402]; 3-way accuracy 0.637 → 0.708 | **SUPPORTED system/scaffold effect for one model/seed/family set**; hardest semantic near-misses remain weak |
| TCSQ SQ-1 | 720-case, four-family oracle quotient; exact verifier agreement 1.0; public primitive count reduced ~25.3% | **SUPPORTED oracle decision-sufficiency upper bound**; not learned quotient discovery or total-cost gain |
| TCSQ SQ-2 | 144-case finite intervention audit; exact dependency recovery in all 4 families; precision/recall/specificity 1.0 | **SUPPORTED finite registered dependency-recovery mechanism**; human candidate schema/interventions supply prior structure |
| Neural task-conditioned structural geometry | New five-seed CPU known-world in this directory: explicit RAKL arm reaches 1.000 triplet, 0.999±0.001 fresh-domain retrieval and 1.000 QoI-flip; strongest generic conditional-metric parent already reaches 0.949±0.016, 0.837±0.044 and 0.940±0.076 | **FEASIBILITY SUPPORTED; RAKL-SPECIFIC RESIDUAL NOT ESTABLISHED** |
| Learner-conditioned structural saturation/allocation | Historical Phase-0/1 v1 Qwen run is **retracted as an instrument artifact**; corrected v2 instrument exists and passes held-out learnability validation, but the full frozen v2 ladder rerun is pending | **UNRESOLVED**; do not cite old v1 terminals as evidence about the mechanism |
| Exact train→inference structural identity reuse | Protocol exists (#467) | **UNTESTED / gated** |
| Epistemically governed cognitive compilation (external RAKL → bounded weight update → fresh assurance → promote/reject) | Architectural synthesis only | **UNTESTED as a weight-learning mechanism** |

## Critical chronology correction: Phase-1 v1 is retracted

Older result files under `research/paper4_phase1_results/` contain terminals such as `NO_STATE_DEPENDENT_RESIDUAL`, `MODEL_FLOOR`, and `REPETITION_REMAINS_VALUABLE`. **Do not interpret those terminals scientifically.** The current Structural Learning Mechanics manuscript records two independent v1 defects:

1. the generator exposed only two unique inputs per family, so it did not test rule generalization;
2. byte-pair tokenization merged the answer-token space such that the gold VALID/INVALID token was masked and no decision gradient was delivered.

Either defect voids the inference. The corrected `experiments/training_ladder/phase1_v2.py` uses a varied generator, token-id concatenation that trains the answer, prompt-level train/probe disjointness, and a learnability positive-control gate. Full v2 exposure-ladder evidence remains pending.

## High-novelty candidates after adversarial prior-art pressure

### H1 — Evidence-governed Task-Conditioned Structural Quotients (TCSQ)

The high-novelty object is **not** context compression or task-conditioned similarity. It is a derived QoI/context-conditioned problem view whose erasure is governed by explicit sufficiency/protected-coordinate obligations, whose source remains immutable, and whose solution must reconstruct to and verify against the original problem before scientific promotion.

Existing SQ-1/SQ-2 results make this the most mature novel lane. The next load-bearing test is SQ-3: matched *net* solver benefit after quotient construction, validation, reconstruction and original verification overhead, against strong compression/slicing/abstraction controls.

### H2 — Neural TCSQ / task-conditioned quotient geometry

Candidate object:

```text
x ~_(q,c) y
```

only when the distinctions erased between `x` and `y` are irrelevant to the registered QoI/context and all protected/boundary coordinates remain compatible.

This is **not novel by itself**: Conditional Similarity Networks already learn condition-specific similarity subspaces. The RAKL residual must therefore require the TCSQ sufficiency/erasure contract, boundary traps, reconstruction/original verification where applicable, and comparison with the strongest matched conditional-metric parent.

The development experiment in this directory establishes feasibility only.

### H3 — Witness-aligned directional neural transfer

Train or intervene on a neural representation using the exact directional `StructuralWitness` object:

```text
source roles/relations/invariants
  --[one-way witness; target boundaries]-->
target roles/relations/invariants
```

with explicit `non_preserved_properties` and hostile semantic-near/structure-wrong decoys. The strong claim is not “the model learns analogy”; relational bottlenecks, Abstractors, causal-abstraction/IIT, and 2026 mechanistic analogical-reasoning work already occupy that space. The residual must show measurable value from **partial, QoI-scoped, fail-closed directional transfer obligations** beyond those parents.

### H4 — Exact shared external↔training↔inference structural substrate

Use the *same frozen structural identity family* (`structure_id`, role/relation/invariant/boundary schema and witness obligations) for:

1. external RAKL reasoning/retrieval;
2. learner-state/mastery probes and/or training losses;
3. training allocation;
4. inference-time structural retrieval/transfer.

Broad “same structural inventory at training and inference” is no longer safe novelty language: SciForma (2026) already uses one structural inventory for multi-dimensional training and inference-time editing. RAKL must show a residual from its directional applicability semantics, exact identity reuse, shared train/inference transfer, and authority/provenance contract.

### H5 — Epistemically governed cognitive compilation

Potential loop:

```text
external RAKL failure / residual
-> typed diagnosis
-> frozen structural training hypothesis
-> bounded challenger weight update
-> fresh disjoint assurance
-> promote / reject / narrow
-> challenger returns to external RAKL
```

Generic self-improvement is occupied by DGM/Hyperagents; external skills compiled into weights is occupied by LatentSkill and related work; instruction-space reflection followed by distillation is also prior art. The RAKL residual must therefore be the **evidence-governed typed transition law** and authority firewall, plus demonstrated benefit from structural failure diagnoses rather than generic reflection.

### H6 — Learner-conditioned structural gradient allocation

This remains the #455/#461/#466 programme. Novelty is only the residual over static RAKL and the strongest model-/skill-aware parent. The critical estimand remains:

```text
ADAPTIVE_RAKL_STRUCTURAL - STATIC_RAKL_STRUCTURAL
```

The lane is blocked until the corrected v2 Phase-1 instrument produces valid learner-state evidence.

## Anti-claims

Do **not** claim any of the following from this directory:

- first conditional similarity/metric representation;
- first relational or causal neural bottleneck;
- first model-aware/adaptive curriculum;
- first learner-specific missing-skill profile;
- first structure-aware training;
- first reuse of a structural inventory at training and inference;
- first self-improving agent;
- first external-skill-to-weight compilation;
- that the CPU known-world proves an LLM benefit;
- that TCSQ SQ-1/SQ-2 prove solver cost reduction or autonomous quotient discovery;
- that training utility, mastery or neural salience grants scientific authority.

## Immediate decision sequence

1. Preserve this branch as a **development / handoff** epoch.
2. Freeze a fresh Neural-Bridge v2 known-world protocol before new outcomes, with strongest controls explicitly named.
3. Require a residual over conditional similarity/metric learning, relational/causal abstraction parents, and a matched-information counterfactual-augmentation parent.
4. If that residual survives, move to a small open-model LoRA/adapter experiment with identical examples/compute and fresh structural-OOD tests.
5. In parallel, finish TCSQ SQ-3 because SQ-1/SQ-2 already justify a real next empirical gate.
6. Rerun the corrected Phase-1 v2 structural-learning ladder before any adaptive scheduler.
7. Only after a learner-side mechanism survives, run exact train→inference identity reuse on fresh tasks.
8. Treat cognitive compilation as a final integration experiment, not as evidence inferred from architecture diagrams.

## Primary internal references

- `src/rakl/structural_types.py`
- `src/rakl/training_projection.py`
- `ARCHITECTURE.md`
- `research/tcsq_v0/`
- `publication/papers/paper-02-structural-mechanics/sections/03c_objective_confirmatory_result.tex`
- `research/llm_comparator_confirmatory_v1/`
- `publication/papers/paper-04-structural-learning-mechanics/main.tex`
- `experiments/training_ladder/phase1_v2.py`
- issues #455, #461, #466, #467, #468, #497, #507

The detailed prior-art matrix, neural development script/result and next-session execution contract live beside this file.