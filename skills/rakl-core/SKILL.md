---
name: rakl-core
description: >-
  Recursive Atomic Knowledge Lattice research operating system. Use to solve hard scientific,
  mathematical, engineering, modelling, strategy, or method-design problems by recursively
  decomposing atomic steps, expanding multi-perspective knowledge fibers, mapping equivalent
  representations, deriving mechanisms, selecting discriminating experiments, and recursively
  improving the research method itself.
---

# RAKL Core — Router

This file is intentionally a small dynamic router.

Do not try to execute the entire RAKL method from memory. Load `manifest.yaml`, the always-loaded core modules, and only the workflow fragments required for the current problem.

## 1. Load manifest and core

Read `manifest.yaml`.

Always load:

- `static/core/principles.md`
- `static/core/workflow.md`

## 2. Detect workflow

A task may activate one or more workflows:

```text
problem-solving
literature-absorption
failure-diagnosis
self-rakl
strategy-synthesis
```

### `problem-solving`

Use when solving a new scientific, mathematical, engineering, or modelling problem.

### `literature-absorption`

Use when expanding the lattice from papers, repositories, books, standards, or other knowledge sources.

### `failure-diagnosis`

Use when an existing model/method/derivation/experiment failed or produced a residual.

### `self-rakl`

Use when evaluating or improving RAKL's own decomposition, routing, search, synthesis, review, logging, or stopping procedures.

### `strategy-synthesis`

Use when converting surviving knowledge/mechanisms into a decision/control/strategy space with explicit economics or utility.

State the detected workflows briefly before processing when this is user-facing and useful.

## 3. Load only matching fragments

Load the workflow files declared by the manifest.

Do not load every workflow by default.

A workflow may recursively open a child workflow if its residual creates a new atomic problem.

## 4. Execute in invariant order

Regardless of workflow, preserve this authority order:

```text
source/evidence reality
→ object + decision/QoI
→ atomic decomposition
→ knowledge fibers
→ projection/equivalence/compatibility analysis
→ derivation or identified set
→ frozen discriminator
→ known-answer/hostile validation
→ native/real evidence
→ residual recursion
→ synthesis
→ review
→ promotion or continued uncertainty
```

## 5. LLM governance

The LLM may propose:

- new facets;
- search vocabularies;
- equivalence mappings;
- mechanisms;
- experiments;
- synthesized formalism;
- improvements to RAKL itself.

LLM proposals do not become canonical because they are fluent or plausible.

Promotion requires the evidence and governance rules in the loaded workflow/core modules.

## 6. Apple Principle

Treat source statements as contextual projections of an object.

Do not force every paper into winner/loser competition. First determine whether two statements are:

```text
complementary facets
equivalent representations
context-dependent differences
genuine contradictions
```

Synthesize the global picture only after this classification.

## 7. Self-recursion

If the current RAKL workflow itself causes a repeated failure, open a `self-rakl` child fiber for the failing atomic method step.

Do not silently patch the method inside another study.

## 8. Output minimum

Every substantive invocation should make explicit:

```text
object/problem
QoI/decision
active atomic steps
new knowledge fibers opened
new semantic objects retained
representation/equivalence map
remaining mechanism/model set
frozen next discriminator(s)
residuals/blockers
synthesis status
next recursion target
```

For persistent implementations, use machine-readable schemas under `schemas/`.
