# Self-RAKL P4-P6 question saturation v2 — READ ME FIRST

Date: 2026-08-15 (Europe/Stockholm)  
Base: `main@e17eaa5498701ed25aa765f4952baaa46f177524`  
Branch: `research/self-rakl-p4-p6-question-saturation-20260815`

Authority: same-context research only. No scientific, promotion, evaluator, publication or production authority.

## Object of this round

This round does **not** begin by asking how to make the existing Paper-IV, V and VI mechanisms score better. It asks the upstream questions:

1. Are the papers decomposing the right scientific objects?
2. Are headline questions confounding information, policy, assurance or executor capability?
3. Which atomic mechanics are already occupied by strongest prior work?
4. Which exact residuals remain distinctive to RAKL?
5. Can Self-RAKL route a repair without corrupting the evaluator that authorizes the repair?

## Expert cell

1. Formal methods / product-authority semantics.
2. Learning theory / adaptive data allocation.
3. Automated reasoning / research-level mathematics.
4. Scientific-agent systems / recursive self-improvement.
5. Adversarial metrology / evaluator and benchmark integrity.

These are same-context roles and are not independent reviewers.

## Saturation routes

The round uses multiple route families so self-vocabulary cannot create false saturation:

- exact RAKL terminology;
- function search without RAKL terms;
- strongest-parent search;
- failure-mode search;
- benchmark/evaluator search;
- adjacent-domain mechanism search;
- current-main negative-history and incident search.

## Main conclusions at freeze

### Paper IV

The current residual bundles three questions that can return different answers:

```text
INFORMATION: does typed structural learner state predict future transfer gain/harm beyond strong parents?
DECISION: can a policy convert that incremental information into better allocation under matched total cost and hard harms?
IDENTITY: does the exact structural identity used during training remain useful at inference-time transfer?
```

A negative Adaptive-vs-Static result does not logically refute the information or identity questions. A positive allocation result does not establish exact identity reuse.

### Paper V

Research-level proof/search ability is now occupied by strong systems and benchmarks. The durable RAKL residual is not "can an LLM do mathematics?" but:

> What exact, executor-independent promotion contract must a machine-generated mathematical result satisfy before it may enter a research record as the intended theorem, with truth, novelty, value and verifier trust kept separate?

Proof-search efficiency remains a secondary cost/benefit question.

### Paper VI

Persistent memory, skill evolution and Pareto selection are occupied functions. The stronger capstone object is:

> Can an evidence-governed research engine recursively improve its own methods — including evaluator policy — while preventing the improvement process from changing, contaminating or gaming the measurement that authorizes the change?

The existing layer-by-layer contribution/cost table remains necessary, but becomes the measurement instrument for this self-evolution claim rather than the headline itself.

## New framework gap exposed

`src/rakl/meta_evolution.py` already permits evaluator/meta-policy/mutation-language evolution, but its controller loses information at five boundaries:

1. it consumes causes but not the diagnosis verdict, so `DISCRIMINATOR_REQUIRED` can be bypassed;
2. higher-order governance accepts a boolean `outer_assurance_frozen`, losing evaluator identity and chronology;
3. mutation-operator credit is global rather than context/layer scoped;
4. escalation uses raw failed-generation count rather than distinct failed mutation families/evidence epochs;
5. Pareto selection itself has no blocking-validity gate.

`META_EVOLUTION_V2_FROZEN_BENCHMARK.json` was committed **before** `src/rakl/meta_evolution_v2.py` and freezes counterexamples for all five.

## Non-negotiable rule

No current paper is strengthened simply because a better question was found. Question improvement changes what evidence should be collected; it does not manufacture the evidence.
