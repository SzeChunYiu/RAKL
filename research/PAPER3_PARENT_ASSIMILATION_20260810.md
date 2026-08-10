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

## Structural information in LLMs (ACL 2026)

**Parent strength.** Controlled evidence that language models can learn abstract structural information and that structural learning is related to later compositional use, while test-time structural use remains a separate challenge.

**Assimilate.** Separate structure acquisition from structure utilization.

**Residual.** Paper 3 externalizes a witnessed structure and tests whether it predicts safe cross-domain transfer beyond the model's implicit structural representation.

## RLAD / AbstRaL

**Parent strength.** Explicit abstraction generation/reinforcement can improve reasoning robustness and OOD behavior.

**Assimilate.** Abstraction is a trainable reasoning object, not merely a prompt instruction.

**Residual.** The Paper-3 target is an external, evidence-bearing, boundary-aware structure that supports both training data selection and inference reuse.

## Current residual novelty candidate

The candidate contribution after parent assimilation is:

> A shared, context/QoI-scoped and evidence-bearing structural object with directional mapping witnesses is used both to estimate cross-domain training redundancy and to license/reject test-time transfer; its economic value is measured by total cost-to-capability including induction and verification.

This candidate is false or uninteresting if a strong parent method supplies the same transfer signal/cost frontier without the extra structural machinery.
