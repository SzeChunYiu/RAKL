# Workflow — Failure Diagnosis

Use when a model, method, derivation, data pipeline, experiment, proof attempt, candidate or strategy fails.

## Principle

A failure is not an instruction to try a more complicated model. It is a measurement of where the current object description, method assumptions, transfer map or research vocabulary may be incomplete.

Diagnose at **two scales**:

1. **local** — why did this exact candidate fail in this exact frozen context?
2. **global** — does this failure share a mechanism with failures elsewhere in the project or another domain?

The global view is experience, not a blacklist. A method that failed before may be correct later under different scope conditions.

## Root-cause ladder

Inspect in order:

```text
R0 source/version/access
R1 schema/parser/units/transformation
R2 clocks/joins/availability/leakage
R3 target/denominator/population/inferential unit
R4 rules/protocol/accounting/settlement
R5 hidden state/censoring/missingness/observation
R6 confounding/identifiability/equivalence
R7 state reduction/projection/functional form
R8 scale/regime/transport/capacity/performativity
R9 numerical/software/simulation/optimization
R10 genuine formalism/mechanism/method-transfer mismatch
R11 ontology or method-basis gap
```

Do not invent new mechanics before R10 unless an impossibility theorem already proves the current object class inadequate. Do not declare R11 merely because several attempts were disappointing; repeated unclassified residuals must be preserved and routed through the metacognitive auditor.

## Residual signature

Record what failed using domain-appropriate coordinates, for example:

```text
mean / variance / tails
uncertainty growth
first passage / memory
scale / aggregation / regime
clock / session
proxy / observable
balance / invariants
intervention response
calibration
execution / value
numerical convergence
formal statement / quantifier / boundary
proof dependency / missing bridge
model-scope mismatch
reuse / composition / sharing
asymptotic scaling / threshold transport
analogy or method-transfer assumption
```

## Local failure packet

For every material failure, preserve an immutable `FailureExperience` in the global failure lattice. Bind it to the exact context packet and public research-trace event. Record:

```text
failure id
atom id
candidate id
context packet hash
research trace event id
method family
failure mode
residual signature
broken assumptions
scope conditions
competing diagnoses
selected bounded diagnosis + status
evidence pointers
falsifier/proof attempt
observed result
local repair attempts
timestamp
artifact hash
```

Observation and diagnosis are separate. `the candidate failed` does not prove `why it failed`.

## Global failure lattice

After local diagnosis, query `src/rakl/failure_lattice.py` for related experiences by method family, residual signature, broken assumptions and structural context. Add typed links only when supported:

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

Use the global portrait to answer:

- Which failure mechanisms recur?
- Under what conditions do they recur?
- Which assumptions repeatedly break during transfer?
- Which representations repeatedly erase load-bearing structure?
- Which repairs have worked?
- Which earlier warnings were contradicted by later success?
- Which residuals remain unclassified?
- Is the same epistemic cut appearing across otherwise different routes?

Do not infer causality from mere co-occurrence or shared vocabulary.

## Method reuse protocol

Before reusing a method that has relevant failure history, run `assess_method_reuse`.

- `NO_RELEVANT_FAILURE_FOUND` — no registered warning selected.
- `SAME_CONTEXT_RETRY` — the old failure may recur; require new evidence/derivation or explicitly label the action a retry and run the old failure test first.
- `DIFFERENCE_WITNESSED` — reuse is allowed because a load-bearing difference is explicit; run the targeted repeat-failure test first.
- `PRIOR_FAILURE_NOT_APPLICABLE` — retain the old experience but document why its scope does not match.
- `GLOBALLY_BLOCKED_BY_VERIFIED_IMPOSSIBILITY` — only when a verified impossibility result covers the same registered context.

A `DifferenceWitness` must state what structural coordinate changed, which failed assumption is restored/replaced, why the old falsifier may no longer apply, and the cheapest test that could show the claimed difference is illusory.

This design deliberately **does not ban reuse of failed methods**. It turns failure into a conditional prior and a better test plan.

## Recursive response

1. Preserve the exact local failure observation and research-trace event.
2. Generate competing diagnoses; do not commit immediately to one cause.
3. Run cheap discriminators for the diagnoses where possible.
4. Normalize only the bounded diagnosis supported by evidence.
5. Add/update the failure experience and typed lattice links.
6. Build/update the global failure portrait.
7. Map the residual to fiber dimensions capable of producing it.
8. Reopen the context fiber if a new structural coordinate, broken transfer assumption or equivalent formulation was exposed.
9. Search solved/near-solved and cross-domain contexts that handle the missing capability.
10. Before the next candidate, query the failure lattice and record the reuse assessment/difference witness.
11. Freeze a discriminator where the surviving explanations make different predictions.
12. Run known-answer/hostile worlds and then native/real evidence as appropriate.
13. Eliminate, bound, or preserve surviving mechanism classes.
14. Recurse on the new residual.

## Meta-learning trigger

If multiple failures remain outside the current taxonomy, do not hide them under `other`. Feed the count and evidence into `src/rakl/metacognition.py` using the `REPEATED_UNCLASSIFIED_RESIDUAL` trigger. A recurring unexplained pattern may become an ontology-gap or method-basis-gap candidate, which opens a new RAKL child problem about the framework itself.

## Prohibited rescue

Never rescue a failed object by:

```text
moving acceptance thresholds after seeing the result
changing population after seeing the result
dropping a falsifier
using a different target without versioning the claim
hiding failed configurations
inventing a causal diagnosis from one failure
blacklisting a method globally from a local failure
ignoring earlier failures when retrying the same structural method
converting missing evidence into LLM confidence
```
