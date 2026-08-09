# Hourly Self-RAKL R&D Protocol

This is the repository-resident operating contract for recurring autonomous RAKL research and improvement.

The scheduling system may live outside GitHub, but every run should obey this file.

## 1. Start from live reality

At the beginning of every run:

1. fetch current `main` SHA;
2. inspect commits since the last self-R&D receipt;
3. inspect `docs/CONSTITUTION.md`;
4. inspect `research/EXTERNAL_FRAMEWORK_ATLAS.json`;
5. inspect the newest `SELF_RAKL_RESEARCH_*` receipt;
6. inspect open meta-fibers/backlog;
7. inspect all available test/CI evidence;
8. record an evidence-cutoff SHA.

Never assume the framework has not changed since the previous hour.

## 2. Select one or more atomic meta-fibers

Use `research/META_FIBER_BACKLOG.json` plus residuals from recent runs.

Prioritize by:

```text
expected decision/research quality improvement
× uncertainty about the current method
× downstream centrality
× semantic novelty potential
÷ cost
```

while preserving the non-greedy research portfolio in `src/rakl/meta.py`.

## 3. Research recursively

For each selected meta-fiber run materially different knowledge routes until the current run's budget is exhausted:

```text
foundational theory
failure/counterexample literature
newest primary work
agent/research software implementations
adjacent disciplines
alien disciplines
alternative vocabulary
benchmarks/evaluation literature
```

Do not count new sources as new knowledge unless semantic deduplication retains something new.

Update the external framework atlas or a fiber-specific atlas with:

```text
source
facet/projection
context
retained semantic object
equivalence mapping
what it cannot see
adoption status
```

## 4. Apply the Apple/Knowledge-Atlas rule

External frameworks are local charts of the object `RAKL_METHOD`.

Do not ask which framework should replace RAKL globally.

Ask which method facet it describes better:

```text
routing
retrieval
perspective discovery
claim extraction
memory
experiment design
review
workflow optimization
benchmarking
provenance
saturation
etc.
```

Gluing is earned through compatibility and benchmark evidence.

## 5. Method residual first

A code or workflow change must respond to a named residual or retained new semantic object.

Examples:

```text
false novelty too high
missing facets discovered late
router loads irrelevant modules
greedy branch collapse
saturation false positive
reviewers correlated
memory resurrects refuted idea
benchmark contamination
```

Do not modify code merely because a new paper uses a fashionable technique.

## 5A. Capability-shaping check before adding workflow complexity

Treat every candidate research-method change as a capability-shaping hypothesis.

Before adding a prompt scaffold, extra agent, reviewer, tool, memory layer, verifier, decomposition stage, routing rule, abstraction level, or interface, record:

```text
atomic cognitive operation
model strength intentionally exploited
predictable weakness/failure mode targeted
amplification mechanism
compensator or externalizer
verification/oracle contract
typed handoff / memory contract
base-model identity and configuration
external resources available before/after
blocking validity invariants
non-blocking meta-QoIs
cost/latency accounting
falsifier
```

Use `docs/AI_CAPABILITY_SHAPING.md` as the theory contract and `src/rakl/capability.py` as the support evaluator.

Distinguish at least:

```text
MODEL_UTILIZATION_AMPLIFICATION
FAILURE_SUPPRESSION
EXTERNAL_CAPABILITY_SUBSTITUTION
SPECIALIST_COMPLEMENTATION
ROUTING_GAIN
DECOMPOSITION_GAIN
MEMORY_EXTERNALIZATION_GAIN
UNRESOLVED_MIXED_ATTRIBUTION
```

A system can become better because it receives an external solver, specialist model, additional corpus, interface, or tool. That is a valid system gain but is not evidence that the base model itself became intrinsically more capable.

### Smallest-compensator rule

Never assume more scaffolding is better. For each named weakness compare, when feasible:

```text
minimal baseline
smallest targeted compensator
richer scaffold only if justified
```

Use the same frozen task packet, model/configuration, answer contract, evaluator, hidden labels and resource set for a workflow-only attribution claim. Any resource delta must be explicit and changes the attribution class.

If the simpler baseline ties or beats the richer scaffold at lower cost, preserve the null/negative result and keep the richer method optional.

A blocking validity regression cannot be traded away for higher nominal task success.

Same-context self-critique remains same-context self-critique; do not relabel it as independent review.

## 6. Freeze challenger evaluation and its validator

For Class B workflow changes, before evaluating the implementation record:

```text
incumbent behavior
challenger behavior
benchmark tasks/meta-split
blocking RAKLBench axes
optimization meta-QoIs
acceptance/rejection rule
cost budget
validator/evaluator fingerprints
```

Do not change the benchmark after seeing the result.

A candidate must not be allowed to weaken the evaluator that judges the same candidate. Freeze the validation workflow, blocking criteria and pre-existing regression tests before the challenger is created. New tests may be added, but existing protected evaluator artifacts must remain byte-identical unless evaluator evolution is itself the declared research object. Evaluator-evolution work requires a parent/frozen validator or separate independent validation path and cannot self-certify merely because its new validator says it passes.

## 7. Implement the smallest improvement

Prefer one atomic method improvement per causal residual.

Add:

- code or versioned workflow fragment;
- known-answer test;
- hostile/negative test;
- missing-evidence/cannot-check case when applicable;
- self-R&D receipt.

For invariants that apply to broad input families, add property-based or metamorphic tests where useful. Generated cases should attempt to refute the invariant and preserve a minimal counterexample when a failure is found.

## 8. Transactional pre-promotion gate

Active `main` must not move first and ask CI whether that move was safe afterward.

For every Class A/B behavior change:

1. freeze the benchmark, meta-QoIs, protected evaluator fingerprints and incumbent `main` SHA;
2. create a candidate branch/ref from that frozen incumbent;
3. implement the challenger only on the candidate;
4. run the required checks on the **exact candidate SHA**;
5. verify the checks came from the expected/trusted validation source;
6. verify all required checks concluded successfully, not merely that a workflow exists;
7. verify the protected validator/evaluator artifacts are unchanged;
8. verify active `main` still equals the frozen incumbent;
9. verify history/receipt/blocking invariants and the Class B positive meta-QoI rule;
10. only then fast-forward `main` to the already-tested candidate SHA with a non-forced ref update.

If the candidate fails, remains pending, has no observable check, changes its protected evaluator, or cannot be tied to the exact tested SHA:

```text
main remains on incumbent
candidate result = FAIL or CANNOT_CHECK
challenger history is preserved
relevant fiber is reopened/refined
```

A green check on some other revision is not evidence for the candidate. A green check generated by a candidate-weakened validator is not independent evidence for the candidate.

### Class A implementation

May promote from the candidate ref when:

```text
exact candidate checks actually executed and pass
receipt exists
history/provenance preserved
protected evaluator unchanged
no blocking constitutional invariant violated
```

### Class B workflow

In addition:

```text
benchmark frozen before candidate creation
at least one registered meta-QoI improves
blocking RAKLBench axes pass
regressions/cost recorded
```

### Class C constitution

Do not silently activate.

Commit only an amendment proposal/research artifact unless the required amendment/review process is satisfied.

## 9. Test honesty

Do not treat any of the following as a successful test:

```text
CI configuration file exists
unit tests were written but not executed
previous commit's CI passed
another candidate revision passed
LLM inspection says code looks right
synthetic examples exist
candidate rewrote its validator and the rewritten validator passed
```

If execution is unavailable or required checks are pending/unobservable:

```text
verification = CANNOT_CHECK
```

Research/docs/fixtures may still be committed if they do not activate unverified behavior. Active behavior changes stay on the candidate ref until valid execution evidence exists.

## 10. Saturation update

For every researched fiber update:

```text
required routes covered
new retained semantic objects
corroboration-only items
same-context trailing flat rounds
independent flat rounds
unseen-mass diagnostic (diagnostic only)
state
```

A new material residual sets the fiber to `REOPENED_BY_RESIDUAL`.

Do not manufacture hourly commits when no semantic, evidential, or implementation state changed.

## 11. End-of-run receipt

Each material run should create a versioned receipt containing:

```text
start/end SHA
evidence cutoff
selected fibers
source/search routes
semantic additions
rejected false novelty
candidate branch and SHA
frozen evaluator fingerprints
exact candidate checks actually run
promotion verdict
CANNOT_CHECK items
saturation states
positive/null/refuted/partial-ID/blocked/transport branches
next highest-value fibers
```

For capability-shaping trials also record:

```text
claimed capability attribution
actual resource delta
improved metrics
worsened metrics
unchanged metrics
whether blocking validity regressed
whether the result establishes only system capability or a same-resource model-utilization effect
```

## 12. Retry and side-effect discipline

Long-running research automation should separate replayable planning/evaluation state from irreversible or externally visible side effects.

- Re-reading sources, rebuilding a deterministic plan and recomputing a promotion verdict should be replay-safe.
- Commits, branch moves, external experiments and other side effects need explicit identity/idempotency handling.
- A transient retry must not silently duplicate an experiment or produce a second semantic record under the same identity.
- Append-only receipts should make it possible to reconstruct why a side effect was authorized.

This borrows the durable-execution lesson that replayable workflow logic and side-effectful activities have different correctness requirements; RAKL keeps the idea but applies its own evidence authority and scientific semantics.

## 13. Long-run objective

The hourly loop is successful if RAKL becomes increasingly better at:

```text
choosing how to decompose a problem
choosing which perspective is missing
finding semantically new knowledge
recognizing equivalent descriptions
identifying what cannot be known
selecting discriminating experiments
preserving research history
synthesizing local views without false unification
knowing when knowledge is saturated
knowing when its own research method needs to change
and shaping the research environment so model strengths are amplified while predictable weaknesses are constrained, externalized, substituted or exposed
```

The objective is not frequent commits. The objective is cumulative epistemic improvement.
