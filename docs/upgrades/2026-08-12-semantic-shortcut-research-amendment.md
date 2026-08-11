# Semantic Shortcut Challenger — Pre-Evaluation Research Amendment

**Change class:** Class B workflow/method challenger.  
**Parent branch point:** `fc1ef58df028bc50646f10515cb73bf222a26b86`.  
**Operator instruction:** implement, open a PR, and merge operationally to `main`.  
**Evolution-evidence status:** none created by this amendment or by deployment.

## Why this amendment exists

The original preregistration froze the SEARCH/JUMP/GLUE/LIFT hypothesis before evaluated outcomes. A subsequent in-depth design-research pass was completed **before challenger CI/evaluated repository outcomes were inspected**. That research did not change the target goal; it exposed implementation-level ways the original mechanism could be satisfied narratively without actually proving that a structural shortcut had been found.

This amendment freezes those corrections before evaluation.

## Research lenses

The same-context design cell covered:

1. formal theorem proving and premise/lemma retrieval;
2. cognitive analogical structure mapping;
3. structured case-based retrieval and memory;
4. program synthesis / learned abstraction / vocabulary expansion;
5. scientific discovery, counterexample-guided refinement and RAKL governance.

These passes are design inputs, not independent assurance.

## Frozen architectural refinements

### 1. Content-bound transformation memory

A shortcut review may no longer cite arbitrary episode ids. It must bind a content-addressed `ObstructionTransformationMemory` containing explicit `O -> T -> O'` episodes and provenance.

### 2. Transformation effects, not stated goals

Structural ranking uses the source episode's recorded transformation effects (`resulting_relations`, preserved invariants) rather than assuming that the source problem's desired transition was achieved.

### 3. Complete source-precondition accounting

SEARCH/JUMP mappings must account for every enabling source precondition. An unrepaired source precondition blocks strict transport.

### 4. Source authority separation

`PROPOSAL_ONLY` and `SUPERSEDED` episodes cannot become strict viable shortcut routes. A verified source episode still creates no target authority.

### 5. Stronger GLUE

A candidate composition must be supported by components whose combined recorded effects cover the target transition, and must still provide operation-order, interface, incompatibility and target-validation obligations.

### 6. Coverage-bound LIFT

A LIFT exhaustion witness must bind a cross-problem coverage receipt. A local empty result cannot support a claim that recorded knowledge lacks a relevant transformation.

### 7. Exhaustion candidate accounting

Every direct, cross-domain or compositional candidate produced by the frozen transformation-memory query must be explicitly retained or rejected before LIFT can pass.

### 8. LIFT remains inverse specification

Repeated residuals constrain a `MissingTransformationSpecification`; they do not directly instantiate or promote a new operator.

## Additional frozen hostile controls

The challenger is expected to reject at least these cases:

- fake/unbound episode id;
- stale/tampered transformation-memory snapshot;
- proposal-only episode treated as reusable authority;
- transformation that breaks a target-forbidden invariant;
- source precondition silently omitted;
- JUMP used despite a viable same-domain SEARCH route;
- GLUE whose components do not cover the required effect;
- GLUE without interface/incompatibility obligations;
- LIFT after only one failed attempt;
- LIFT without cross-problem coverage binding;
- LIFT that fails to account for a retrieved candidate;
- LIFT specification unsupported by repeated residual structure;
- candidate generation before the obstruction-transformation trace event.

## Meta-QoIs unchanged

The previously frozen Class-B questions remain unchanged: shortcut/reuse quality, invalid-transfer rate, false invention activation, residual contraction, cost, and regression against protected authority/chronology invariants.

These tests demonstrate implementation conformance only. They do not establish fresh-transfer improvement.

## Rollback unchanged

If the challenger introduces blocking invariant regressions or cannot coexist with the current `main`, roll back the operational merge to the pre-merge main subject and preserve the challenger branch/PR as negative or partial evidence.
