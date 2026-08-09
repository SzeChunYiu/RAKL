# RAKL Engineering Closure and Release Conformance

Status: release program v0.1. This document defines how engineering concerns become scientifically testable RAKL fibers.

## 1. Engineering defects are research objects

RAKL applies the same discipline to engineering as to scientific claims.

Every material engineering concern is represented as a fiber with:

```text
object / subsystem
registered user or scientific QoI
failure/residual signature
scope and environment
incumbent behavior
candidate mechanism/design
known-answer worlds
hostile worlds
resource budget
blocking invariants
measured optimization QoIs
rollback/recovery rule
closure/reopening rule
```

Examples include memory growth, context overflow, retrieval latency, retry safety, evaluator drift, schema migration, cache invalidation, dependency identity, tool failure and installation reproducibility.

## 2. No global "proven working" claim without scope

RAKL distinguishes:

```text
software tests passed
component contract validated
end-to-end workflow validated
scientific task benefit demonstrated
scoped engineering closure certified
global framework saturation
```

These are different authority levels.

A component can pass all software tests while its real scientific utility remains unmeasured. A workflow can be reliable on a reference environment while untested on another operating system or model provider.

The strongest permitted engineering statement is therefore scoped:

> "RAKL release X is closed against benchmark/profile Y under environment and resource envelope Z, with the listed unresolved exclusions."

## 3. Closure certificate for an engineering fiber

An engineering fiber may be marked `CLOSED_SCOPED` only when all applicable conditions are satisfied:

1. scope, environment and resource envelope frozen;
2. failure mode and meta-QoIs registered before challenger results;
3. known-answer positive, negative and cannot-check worlds executed;
4. hostile/adversarial cases executed;
5. blocking invariants pass;
6. at least one registered benefit improves for a Class-B workflow change;
7. cost, latency, storage/context and variance reported when relevant;
8. restart/retry/replay behavior tested for stateful or side-effectful components;
9. rollback path demonstrated when behavior is promotable;
10. negative failures and supersession history remain available;
11. evaluator/subject/dependency identity is sufficient for the claim;
12. machine-readable closure receipt committed.

Any new in-scope residual reopens the fiber.

## 4. Release planes

### Epistemic plane

Atlas, relation algebra, authority, assumptions, contradiction semantics, negative history and saturation.

### Storage plane

Canonical evidence/payload storage, content identity, indexes, summaries, provenance, migrations and garbage-free historical reconstruction.

### Context/execution plane

Routing, context compilation, model/tool invocation, bounded budgets, retry/replay and durable side effects.

### Evaluation/governance plane

Frozen benchmarks, parent evaluator, subject identity, dependency identity, information firewalls and promotion transactions.

### Product/package plane

CLI/API, configuration, examples, installation, diagnostics, observability and reference environment profiles.

### Scientific-validation plane

Matched baselines, ablations, real literature/science tasks, historical cutoffs, case studies and paper claims.

A release candidate is not ready until each plane has a closure status and explicit blockers.

## 5. Normal-LLM design constraint

The reference workflow must not require a frontier model to remember RAKL itself.

A normal model should receive a compiled task packet containing only:

```text
compact kernel
current operation contract
object/context/QoI
active fiber/residual
bounded evidence working set
negative-history guards
available tools
output schema
```

State persistence, search, history and long-term memory belong to the external package.

Model capability is then a measurable dependency rather than hidden architecture.

## 6. Reference profiles

Future releases should define tested profiles such as:

```text
MINIMAL_LOCAL
STANDARD_API
LONG_CONTEXT_OPTIONAL
OFFLINE_RESEARCH
CI_EVALUATOR
```

Each profile freezes:

- minimum Python/runtime version;
- model context budget rather than one vendor/model name;
- required tool capabilities;
- storage backend;
- network expectations;
- benchmark/task packet;
- latency/cost/storage envelope.

Profile claims must be validated separately.

## 7. Required end-to-end release tests

A ready-to-use package eventually needs prospective clean-install tests that execute:

```text
install package
initialize project
register object/QoI/context
create fiber
load/search source packet
compile bounded context
run proposal step
attach evidence
update atlas/memory
preserve negative result
run benchmark/review gate
produce synthesis and receipt
restart process
reconstruct state
```

Hostile variants must include unavailable tools, corrupted cache/index, context overflow, repeated side effects, stale evaluator dependencies, missing evidence and a deliberately refuted hypothesis.

## 8. Observability

Every operation should emit structured telemetry sufficient to diagnose:

```text
token input/output
compiled-context size
records considered/selected/rehydrated
search/retrieval cost
cache hit/miss
LLM/tool latency
retry count
failure class
authority changes
fiber openings/reopenings
benchmark trial identity
```

Observability is evidence for engineering claims, not merely operational convenience.

## 9. Storage growth policy

RAKL should not delete scientifically relevant history to control size.

Use:

- content-addressed deduplication;
- physical compression of immutable payloads;
- indexes that can be rebuilt;
- supersession edges rather than copies;
- compact materialized views;
- cold archival tiers;
- retention policies only for reproducible caches/transient transport artifacts.

Scientific evidence and negative-history records remain addressable.

## 10. Engineering portfolio

Engineering work uses the same non-greedy portfolio as research:

```text
exploit: fix measured bottlenecks in the active workflow
diversify: test alternative architectures/backends
moonshot: investigate large structural changes
meta-RAKL: improve the engineering/evaluation process itself
```

Expected decision-relevant failure reduction per implementation/review cost guides prioritization, subject to blocking invariants.

## 11. Current closure status

The latest framework inventory before this program reported 24 registered high-impact method steps and 24 open or unbenchmarked steps. Consequently, RAKL is not currently authorized to claim global scientific or engineering closure.

Round 020 begins by closing one prerequisite: bounded epistemic context compilation support. Subsequent release work must update the derived inventory rather than declaring the package finished by narrative judgment.
