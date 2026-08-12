# Training-time RAKL extension — 2026 prior-art addendum

**Date:** 2026-08-12  
**Refs:** #455, #461, #462, #466  
**Status:** claim-boundary research only; no training-efficacy result.

This addendum extends `TRAINING_TIME_EXTENSION_CROSS_PAPER_SYNTHESIS_20260812.md` after an additional hostile search focused specifically on **learner-state dependence, cross-domain transfer, composition, coverage and continual/adaptive data selection**.

## 1. New strongest threats

### Transfer-Aware Curriculum (TAC), 2026

`Transferability for General Reasoning: An Automated Curriculum for Multi-Domain RLVR` (arXiv:2606.25178) is a major threat to any broad claim that RAKL is the first curriculum to allocate training based on cross-domain transfer. TAC combines local learnability with projected-gradient alignment to estimate whether updating on one domain benefits the others, then uses that signal in an online bandit-style curriculum. It reports low additional wall-clock overhead and improvements over learnability-only allocation.

**Claim consequence:** RAKL must not claim priority for:
- transfer-aware curriculum allocation;
- using learner progress plus cross-domain transfer as an online scheduling signal;
- adaptive multi-domain reasoning curriculum in general.

**Residual RAKL question:** does an *explicit directional relational structure*, with QoI, boundaries, preserved/non-preserved properties and exact source/target identities, expose a useful training signal beyond gradient/domain transferability?

### Adapt-Infinity, ICLR 2025

`Adapt-∞: Scalable Continual Multimodal Instruction Tuning via Dynamic Data Selection` explicitly selects data according to the current state of acquired knowledge, builds pseudo-skill clusters from gradient-based representations, changes selectors over a continual stream, prunes redundant data and measures forgetting/forward transfer.

**Claim consequence:** RAKL must not claim priority for:
- current-learner-state adaptive selection;
- continual dynamic example selection;
- combining adaptive selection with forgetting control or forward transfer;
- pseudo-skill-cluster-aware pruning in general.

**Residual RAKL question:** can the RAKL structural substrate give a *scientifically interpretable and boundary-aware* reason why one example is redundant while another composition/regime/transfer example is not, and does that residual improve fresh structural-OOD cost-to-capability?

### Online reweighting versus offline curation, 2026

Recent work explicitly argues that online reweighting generalizes better than offline curation when model/task state changes.

**Claim consequence:** adaptivity itself is firmly prior art. Static-vs-adaptive comparison is necessary to establish a RAKL mechanism but cannot be advertised as a new category of training method.

### Coverage over difficulty, 2026

Recent generative fine-tuning work reports that difficulty-based selection can underperform because it loses input-space coverage; a simple coverage-based selector can outperform difficulty heuristics.

**Design consequence:** RAKL training allocation needs non-compensatory coverage constraints. A high estimated marginal-utility score must not consume all budget from rare structural families, boundary cases or challenge/near-miss strata.

### PPL-Factory / perplexity-aware selection, 2026

Task-aware and budget-aware perplexity selection and perplexity-aware scaling-law work strengthen perplexity as a cheap model-state baseline.

**Design consequence:** Phase 0/1 must test whether vector structural mastery predicts future transfer gain beyond loss/perplexity. If it does not, the added RAKL structure is not empirically earned.

### Structure/component compositional development, 2026

Recent compositionality work finds that identical symbolic content can lead to different compositional development depending on structure, components and combinations.

**Design consequence:** the proposed vector mastery state is better justified as a testable factorization than as a scalar `skill mastered` flag. But composition-sensitive training itself remains occupied prior art.

### Emergence and test-time use of structural information, ACL 2026

Existing work directly studies how language models learn abstract structure and use structural information at test time.

**Claim consequence:** RAKL cannot broadly claim first shared structure between training and inference.

**Residual RAKL question:** can the *same explicit registered RAKL structural identity* — roles, relations, invariants, QoI and boundaries — be used both to drive training allocation and later to support fail-closed directional transfer, without switching to an unrelated latent representation?

## 2. Revised residual novelty boundary

After this addendum, the strongest defensible candidate is not:

```text
learner-conditioned data selection
+ saturation
+ transfer-aware curriculum
```

All three are substantially occupied.

The remaining candidate is the conjunction:

```text
explicit directional relational structure
+ QoI and boundary scope
+ preserved / non-preserved coordinates
+ learner-specific vector saturation of the exact structure
+ allocation toward unsaturated composition/boundary/representation/transfer coordinates
+ nonzero retention/repetition and coverage constraints
+ exact structural identity reused at inference
+ training/search/scientific-authority projections kept non-coercible
```

The claim is only earned if each load-bearing residual is empirically necessary.

## 3. Implication for Paper VI gate (#462)

The threshold for a sixth paper should be raised.

A standalone `Structural Learning Mechanics` paper should require more than Adaptive RAKL beating Static RAKL. It should additionally show at least one result that generic model-aware/transfer-aware parents do not already explain, such as:

1. coordinate-specific saturation over an explicit relational object predicts later structural-OOD gain beyond perplexity/influence/gradient-transfer baselines;
2. boundary/composition-aware allocation prevents a failure that a flat skill/domain curriculum systematically makes;
3. the exact same registered structure gives measurable value at both training and inference;
4. the effect generalizes across more than one synthetic family and more than one model/checkpoint regime;
5. full preprocessing/probing cost does not erase the gain.

Otherwise the correct publication action remains `ABSORB_INTO_PAPER_III` or `REJECT_NEW_PAPER`.

## 4. Framework implication

The architecture should support three views over shared identities without sharing scores:

```text
pi_epi   -> scientific authority / evidence
pi_search -> investigation priority
pi_train  -> gradient-allocation hypotheses
```

`pi_train` may consume structural identities, failure history and model probes. It must not consume scientific authority as a scalar quality score, and no training success may self-promote a scientific claim. Conversely, high scientific authority does not make an item mandatory training data if the learner-specific training projection finds it redundant.

The proposal-only `src/rakl/training_projection.py` implements this identity/type boundary. #461 owns whether the mastery object is measurable; #466 owns whether an adaptive policy built on it adds causal value.
