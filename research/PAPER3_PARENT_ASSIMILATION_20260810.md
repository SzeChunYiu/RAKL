# Paper 3 parent-method assimilation ledger

Date: 2026-08-10  
Status: active; new parent methods reopen this ledger.

## Purpose

The structural-amortization programme treats prior work as reusable parent mechanisms. The goal is not to avoid overlap. It is to reproduce the strongest parent result that matters, assimilate useful mechanisms, identify a residual and design a matched challenger.

## MASS — training-data skill graph

**Parent strength.** Mathematical skill graph used for pretraining data selection; reports comparable mathematical performance with substantially fewer training tokens and same-budget performance gains.

**Assimilate.** Skill dependency as a training-data value signal; strong data-selection baseline.

**Residual.** Skill nodes are domain/task labels learned in a mathematical setting. Paper 3 asks whether cross-domain role/relation structure adds transfer information when surface skill/domain labels differ, and whether the same structural object is reusable at inference.

**Challenge.** Controlled Q2 domain shift plus structural redundancy levels; compare tokens-to-structural-OOD capability.

## Skill-It — data-driven skill dependencies

**Parent strength.** Learns dependencies among skills and adapts sampling; demonstrates higher performance with less continual-pretraining data in several settings.

**Assimilate.** Evaluation-conditioned dependency sampling.

**Residual.** Does not by itself establish surface-disjoint structural equivalence or a shared training/inference object.

**Challenge.** Match the parent skill graph and add only structural witness information.

## SWIFT — workflow structural priors

**Parent strength.** Explicit amortized workflow design from structural priors; transfers to unseen tasks and sharply reduces marginal workflow-search cost. Operator-name randomization retains much of performance, supporting topological rather than purely semantic transfer. The paper also reports OOD cases where mismatched transferred strategies can mislead.

**Assimilate.** Contrastive structural-prior extraction and cross-task workflow transfer; negative-transfer cases.

**Residual.** Workflow topology is not yet a context/QoI-scoped scientific structural object shared with training selection. Paper 3 adds an explicit boundary/mismatch witness and tests semantic-decoy rejection.

**Challenge.** Same base model, same workflow/operator library, structural witness on/off; Q2/Q3 controlled cases.

## Reasoning Primitive Induction

**Parent strength.** Mines recurrent successful ReAct moves into typed pseudo-tools; strong held-out improvements and lower average inference cost.

**Assimilate.** Trace mining and typed reusable reasoning primitives.

**Residual.** Applicability is represented primarily through pseudo-tool descriptions rather than a scientific transfer witness with explicit non-preserved properties and boundary conditions.

**Challenge.** Use the same induced primitive library, compare semantic primitive retrieval to witnessed structural retrieval/adaptation.

## TraceCompiler

**Parent strength.** Mines noisy traces into mostly deterministic workflows using evidence-bearing dependencies and conservative refusal under underdetermined irreversible branches.

**Assimilate.** Evidence-bearing dependency edges, refusal semantics, deterministic compilation.

**Residual.** Runtime call reduction is not a demonstrated net-efficiency result because offline compilation cost is not measured. This directly motivates Paper 3's total-cost accounting.

**Challenge.** Report induction/compilation cost and break-even reuse count; do not claim net efficiency from runtime compression alone.

## ReX — reusable latent experience bank

**Parent strength.** A shared Experience Bank stores latent skill vectors and dynamically composes them into input-conditioned lightweight adapters across tasks without explicit task identifiers.

**Assimilate.** Persistent reusable experience and dynamic task-conditioned composition.

**Residual.** ReX does not by itself establish an externally inspectable scientific structural object, cross-domain training-data redundancy, directional transfer boundaries or semantic-decoy rejection.

**Challenge.** Compare shared latent experience against explicit witnessed structure on Q2/Q3 and on training-data selection.

## SkillGraph / SKILLGRAPH / GraSP / SkillDAG — dependency and execution graphs

**Parent strength.** These systems move beyond flat semantic skill retrieval. They encode prerequisites, enhancement/co-occurrence/conflict or precondition-effect edges, retrieve ordered subgraphs, compile executable DAGs, verify nodes, evolve structure from trajectories and in some cases couple the graph to reinforcement-learning policy improvement.

**Assimilate.** Typed dependency edges, structural retrieval, graph evolution, precondition/effect contracts, node-level verification and conservative repair.

**Residual.** A graph shared by policy learning and execution already exists, so Paper 3 cannot claim ``one graph across learning and inference.'' The remaining candidate is specifically cross-domain scientific structural redundancy used for **training-data selection** and inference transfer with QoI/context/evidence/boundary semantics.

**Challenge.** Use the strongest graph/skill parents as inference controls; test whether the RAKL scientific witness adds safe transfer and whether its same persistent object also improves training selection.

## SkillSight — calibrated semantic skill retrieval

**Parent strength.** Shows that shared descriptive boilerplate biases dense and lexical skill retrieval and removes much of that bias through semantic/lexical background calibration without extra training.

**Assimilate.** Strong semantic retrieval control that discounts shared background.

**Residual.** Paper 3 cannot use a weak embedding retriever as the semantic baseline. Structural gains must survive calibrated semantic retrieval.

**Challenge.** Q3 semantic decoys should remain a structural failure after SkillSight-style background calibration; otherwise the apparent structural gain was just semantic calibration.

## AgentGL — graph-conditioned learning and graph-native inference

**Parent strength.** Uses graph-native tools at inference and a graph-conditioned curriculum during reinforcement learning, demonstrating one structural substrate can influence both training and execution.

**Assimilate.** Graph-conditioned curriculum and graph-native inference as a cross-phase parent mechanism.

**Residual.** AgentGL is a graph-learning system rather than a general cross-domain scientific equivalence/redundancy representation. It substantially narrows, but does not automatically subsume, the Paper-3 training-data-selection plus safe cross-domain transfer claim.

**Challenge.** The RAKL shared-substrate claim must be phrased in terms of structural classes/witnesses that transfer across different surface domains and that directly alter data selection as well as inference.

## Asymmetric structural transfer between language and biology

**Parent strength.** Controlled results report stronger structural transfer from language models to biological sequence tasks than the reverse under several matched conditions.

**Assimilate.** Directionality as a first-class transfer property; reverse-direction perturbation in the benchmark.

**Residual.** Shared structure does not justify symmetric equivalence. RAKL's witness is therefore directional and retains direction-specific failure history.

## Structural information in LLMs (ACL 2026)

**Parent strength.** Controlled evidence that language models can learn abstract structural information and that structural learning is related to later compositional use, while test-time structural use remains a separate challenge.

**Assimilate.** Separate structure acquisition from structure utilization.

**Residual.** Paper 3 externalizes a witnessed structure and tests whether it predicts safe cross-domain transfer beyond the model's implicit structural representation.

## RLAD / AbstRaL

**Parent strength.** Explicit abstraction generation/reinforcement can improve reasoning robustness and OOD behavior.

**Assimilate.** Abstraction is a trainable reasoning object, not merely a prompt instruction.

**Residual.** The Paper-3 target is an external, evidence-bearing, boundary-aware structure that supports both training data selection and inference reuse.

## Current residual novelty candidate

After this assimilation pass the candidate contribution is deliberately narrow:

> A persistent, context/QoI-scoped and evidence-bearing structural object with directional mapping witnesses is used both to estimate **cross-domain training-data redundancy/selection value** and to license or reject inference-time transfer across surface-disjoint domains; its value is measured by total cost-to-capability including induction and verification.

The words ``shared substrate,'' ``skill graph,'' ``structural prior,'' ``amortization,'' ``experience bank,'' ``graph across learning and execution,'' and ``semantic retrieval is insufficient'' are all occupied parent territory and must not be presented as standalone novelty.

This candidate is false or uninteresting if a strong parent method supplies the same cross-domain transfer signal and training-selection/inference cost frontier without the extra scientific witness machinery.
