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

## 6. Freeze challenger evaluation

For Class B workflow changes, before evaluating the implementation record:

```text
incumbent behavior
challenger behavior
benchmark tasks/meta-split
blocking RAKLBench axes
optimization meta-QoIs
acceptance/rejection rule
cost budget
```

Do not change the benchmark after seeing the result.

## 7. Implement the smallest improvement

Prefer one atomic method improvement per causal residual.

Add:

- code or versioned workflow fragment;
- known-answer test;
- hostile/negative test;
- missing-evidence/cannot-check case when applicable;
- self-R&D receipt.

## 8. Direct-to-main gate

### Class A implementation

May commit directly to main when:

```text
tests actually executed and pass
receipt exists
history/provenance preserved
no blocking constitutional invariant violated
```

### Class B workflow

In addition:

```text
benchmark frozen before result
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
LLM inspection says code looks right
synthetic examples exist
```

If execution is unavailable:

```text
verification = CANNOT_CHECK
```

Research/docs/fixtures may still be committed if they do not activate unverified behavior. Active behavior changes should wait for valid execution evidence.

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
code/workflow changes
benchmarks/tests actually run
CANNOT_CHECK items
saturation states
positive/null/refuted/partial-ID/blocked/transport branches
next highest-value fibers
```

## 12. Long-run objective

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
and knowing when its own research method needs to change
```

The objective is not frequent commits. The objective is cumulative epistemic improvement.
