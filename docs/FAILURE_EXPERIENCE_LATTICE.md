# Failure Experience Lattice

RAKL treats failure as reusable evidence, not just local negative history.

## Purpose

A failed candidate should update two views simultaneously:

1. the **local proof/research DAG**, which records what happened to the active atom;
2. a **global failure experience lattice**, which records normalized structural failure modes across atoms, routes and domains.

The global lattice is an experience system, not a blacklist. A method that failed in one context remains usable later. Reuse requires a **difference witness** explaining which load-bearing condition has changed and why the earlier failure need not recur. Only a separately verified impossibility theorem may justify a global prohibition.

## Four levels

### F0 — observed failure

Exact immutable event:

```text
atom
candidate
context-packet hash
research-trace event
method / transfer / analogy used
falsifier or proof attempt
observed result
evidence pointers
```

### F1 — diagnosed failure mode

Normalize the local event into a structural statement such as:

```text
wrong target / specification drift
assumption mismatch
analogy mismatch
representation loses load-bearing information
method requires tree-like recomputation but target permits reuse
local invariant collapses under composition
finite evidence does not scale asymptotically
threshold transport loses exponent
source/target model mismatch
quantifier or boundary failure
proof dependency missing
candidate is true but too weak for parent atom
```

The diagnosis must state confidence and competing diagnoses. A failure observation does not automatically prove its cause.

### F2 — recurring failure family

Link multiple F1 nodes when they share a normalized mechanism, broken assumption, residual signature or transformation failure. Keep context differences visible.

Examples:

```text
reuse defeats recomputation-charging measures
padding preserves the wrong complexity scale
low-dimensional quotient collapses apparent complexity
local coordinate witnesses multiplex across products
restricted-model lower bound does not transfer to unrestricted DAG reuse
```

### F3 — meta failure / method-basis gap

When many distinct methods fail because the current research vocabulary lacks the same structural capability, open a meta-atom. This may trigger perspective discovery, literature search, cross-domain analogy search, or RAKL self-improvement.

## Typed relations

Use explicit typed edges rather than narrative similarity:

```text
INSTANCE_OF
SHARES_RESIDUAL_WITH
SHARES_BROKEN_ASSUMPTION_WITH
SAME_METHOD_FAMILY_AS
CONTEXT_SPECIALIZATION_OF
SUPERSEDES_DIAGNOSIS
CONTRADICTED_BY_SUCCESS
RESOLVED_BY
TRANSFER_WARNING_FOR
MOTIVATES_META_ATOM
```

Do not use a causal edge unless causal attribution is actually supported.

## Reuse protocol

Before proposing a materially new candidate, query the failure lattice by:

```text
method family
structural coordinates
required assumptions
analogy abstraction
operator sequence
residual signature
parent obstruction
```

For every close prior failure, classify the proposed reuse as one of:

- `SAME_CONTEXT_RETRY` — no material difference; reject unless new evidence/derivation exists;
- `DIFFERENCE_WITNESSED` — one or more load-bearing differences are explicit; allow with targeted falsifier;
- `PRIOR_FAILURE_NOT_APPLICABLE` — structural mismatch is demonstrated;
- `GLOBALLY_BLOCKED_BY_VERIFIED_IMPOSSIBILITY` — only when a verified theorem/authority certificate actually covers the new context.

A difference witness should answer:

```text
which earlier failure is relevant?
which context coordinate changed?
which failed assumption is now restored/replaced?
why should the old counterexample/falsifier no longer apply?
what cheapest test could show that this claimed difference is illusory?
```

### Realization domain (obligation-strength typing)

When a `DifferenceWitness` feeds **strict-reduction / obligation-strength**
routing, it must also declare a realization domain:

- `AMBIENT_REPRESENTATION` — distinction in an ambient encoding/statistic space;
  may prune identities/representations, **must not** certify target-domain
  obligation weakening (`REPRESENTATION_ONLY`).
- `TARGET_DOMAIN` — hostile pair realized inside the fixed target theory.
- `TRANSFERRED_WITH_WITNESS` — transported distinction; requires bound
  source→target mapping, shared constraints, disanalogies, and assumptions.

Missing domain typing fails closed as `CANNOT_CHECK`. Ordinary method-reuse
assessment remains separate and does not mint obligation-strength authority.
Same-context review still carries zero independent-review authority; promotion
gates are unchanged.

## Learning loop

```text
candidate fails
-> preserve exact failure observation
-> generate competing diagnoses
-> test/score diagnoses
-> normalize accepted bounded diagnosis
-> link into failure lattice
-> update global failure portrait
-> reopen current context if needed
-> query solved analogues / cross-domain analogies for the missing capability
-> propose next action with difference witness
-> targeted falsifier first
```

## Global failure portrait

At any point the repository should be able to summarize:

- dominant failure families;
- which methods repeatedly fail and under what conditions;
- which assumptions are most often broken during transfer;
- which representations repeatedly collapse complexity;
- which failure families have known repairs;
- which previous warnings were later contradicted by success in a changed context;
- unresolved meta-atoms suggesting the invention basis itself is incomplete.

This portrait is a compact form of research experience. It should reduce repeated mistakes without suppressing legitimate reuse of old methods in new contexts.
