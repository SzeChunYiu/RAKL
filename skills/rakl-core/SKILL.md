---
name: rakl-core
description: >-
  Recursive Atomic Knowledge Lattice research operating system. Use to solve hard scientific,
  mathematical, engineering, modelling, strategy, or method-design problems by recursively
  decomposing atomic steps, expanding multi-perspective knowledge fibers, mapping equivalent
  representations, inventing and deriving typed mechanisms/formalisms, selecting discriminating
  experiments, and recursively improving the research method itself.
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
perspective-discovery
literature-absorption
failure-diagnosis
mechanism-invention
self-rakl
strategy-synthesis
```

### `problem-solving`

Use when solving a new scientific, mathematical, engineering, or modelling problem.

### `perspective-discovery`

Use when the current vocabulary, ontology or decomposition may be missing relevant facets or alien-domain structure.

### `literature-absorption`

Use when expanding the lattice from papers, repositories, books, standards, or other knowledge sources.

### `failure-diagnosis`

Use when an existing model/method/derivation/experiment failed or produced a residual.

### `mechanism-invention`

Use when the task requires discovering or constructing a working mechanism, new mathematics, or a formalism; when existing representations fail to close a residual; or when a positive-goal lane must continue beyond failure of the current candidate set.

This workflow must materialize proposals as typed formalism/mechanism deltas with residual targets, parent lineage and falsifiers. Text-only equations are not sufficient for a certifying invention lane.

### `self-rakl`

Use when evaluating or improving RAKL's own decomposition, routing, search, synthesis, invention operator basis, review, logging, or stopping procedures.

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
→ object + decision/QoI + frozen goal contract
→ atomic decomposition
→ knowledge fibers
→ projection/equivalence/compatibility analysis
→ mechanism/formalism construction when required
→ identification / identified set
→ frozen discriminator
→ formal/known-answer/hostile validation
→ native/real evidence
→ typed residual
→ constructive mutation/recombination or ordinary recursion
→ synthesis / candidate tournament
→ positive-goal evaluation
→ review
→ narrow promotion or continued search
```

A failed candidate is evidence, not successful project closure. If the registered positive goal is not achieved, preserve the failure and continue through residual-driven invention unless an integrity/resource/data block prevents execution. A block is `CANNOT_CHECK`, not a fabricated positive.

## 5. LLM governance

The LLM may propose:

- new facets;
- search vocabularies;
- equivalence mappings;
- mechanisms;
- experiments;
- new mathematical expressions and typed formalisms;
- constructive invention moves;
- improvements to RAKL itself.

LLM proposals do not become canonical because they are fluent or plausible.

For mechanism/formalism invention, the proposal must be externalized into the typed IR and bound to a candidate id before evaluation. Promotion requires the evidence and governance rules in the loaded workflow/core modules.

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

If an identified epistemic cut cannot be crossed by the current constructive operator basis, open a method-basis gap and benchmark a challenger operator before promotion.

Do not silently patch the method inside another study.

## 8. Output minimum

Every substantive invocation should make explicit:

```text
object/problem
QoI/decision and positive-goal state when registered
active atomic steps
new knowledge fibers opened
new semantic objects retained
representation/equivalence map
remaining mechanism/model set
typed candidate formalisms and invention lineage when applicable
frozen next discriminator(s)
residuals/blockers
candidate frontier / synthesis status
next recursion or invention target
```

For persistent implementations, use machine-readable schemas under `schemas/`.
