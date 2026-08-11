# RAKL Invariant Workflow

## A. Freeze the problem boundary and goal contract

Record:

```text
object
question/subclaim
decision or QoI
population
scale/horizon
observation boundary
units
allowed evidence
current authority/evidence cutoff
positive-goal criteria when the task is goal-seeking
```

When a positive scientific outcome is required, freeze the success vector before evaluated results. Candidate failure is nonterminal, but the goal contract cannot be weakened after seeing failures.

## B. Atomize

Decompose the solution chain until each step has one clear semantic job. Include data and mathematical transformations, not only named models.

Record the atomization result as a first-class artifact. A later researcher must be able to see what the parent problem became, which atom is active, and which dependencies remain outside that atom.

## C. Freeze the active context fiber

For every unresolved atomic step, identify the exact local object and record its load-bearing context before candidate generation.

At minimum capture:

```text
structural coordinates
equivalent formulations / representations
assumptions and boundaries
known solved siblings
near-solved siblings
relevant negative/barrier results
source anchors
```

For mathematical discovery, the context fiber must conform to `schemas/math-context-fiber.schema.json` and be frozen before the first candidate timestamp.

## D. Build the analogue / method-transfer matrix

Search through multiple vocabularies and disciplines for contexts sharing the atom's structure. Extract methods, not paper summaries.

For every proposed transfer record:

```text
source context
method
why the method works there
required assumptions
shared structure with the target
disanalogies / broken assumptions
minimum repair question
source anchors
```

A similarity label is not a witnessed transfer. If the enabling assumptions are unknown, candidate generation fails closed.

## E. Run cross-domain and everyday analogy discovery

Abstract away domain-specific nouns and compare structural roles. Search mathematics, science, engineering, algorithms, games, organizations and ordinary human situations for the same relational pattern.

Potential shared abstractions include:

```text
reuse versus recomputation
queueing and congestion
shared resources / caching
matching and assignment
routing and bottlenecks
conservation / budgets
redundancy and error correction
compression and description length
local-to-global assembly
adversarial games
feedback and control
symmetry breaking
```

Retain an analogy only when all of these are explicit:

```text
source situation
common abstraction
source-to-target role mapping
shared constraints
material disanalogies
proposed transferable principle
falsifiable target-domain validation obligation
provenance / observation note
```

An analogy can expand the proposal basis but never supplies truth authority. Surface resemblance is rejected. A completed scan may legitimately conclude `NO_SAFE_BRIDGE_FOUND`.

## F. Open and expand knowledge fibers

For every unresolved atomic step record alternatives across the standard RAKL dimensions. Search broadly enough to expose missing perspectives, terminology and equivalent representations.

## G. Normalize

Build terminology/ontology mappings and representation-equivalence relationships.

## H. Record the public decision trace

Every material research transition must leave an auditable record containing:

```text
current public state / context
atom id and parent relation
action taken
alternatives considered
concise evidence-grounded selection rationale
evidence / artifact pointers
output / result
uncertainties
residuals
proposed next action
content hash and timestamp
```

For strict mathematical research, the trace must conform to `schemas/math-research-trace.schema.json`. Before candidate generation the active atom must contain, in order, `ATOMIZED`, `CONTEXT_FROZEN`, `ANALOGY_SCAN`, `METHOD_TRANSFER_REVIEW`, `EXPERT_CONTEXT_REVIEW`, and `NEXT_STEP_PROPOSED`.

`EXPERT_CONTEXT_REVIEW` records role-separated same-context passes over domain knowledge, analogy transfer, adversarial falsification, formal methods/verifier trust, and novelty/research value. Preserve disagreement and unresolved uncertainty; do not represent these roles as independent peer review.

Trace entries are tamper-evident: except for the first event, `previous_event_hash` must equal the preceding event's `artifact_hash`.

This is a reproducible scientific decision ledger, not a raw private chain-of-thought transcript.

## I. Pre-candidate gate

Do not invent or propose a candidate while the active context/method-transfer/analogy packet, expert context review, or public trace is missing, incomplete, unfrozen, hash-chain-invalid, or chronologically later than the candidate.

When a runtime gate exists, obey it. For mathematical research, call:

```text
plan_math_research(..., context_fiber=..., research_trace=...)
```

If `candidate_generation_allowed` is false, execute only `pre_candidate_actions`.

Backfilling context or trace after candidate generation does not repair discovery chronology. Such a candidate may still be checked for truth, but it is not a strict context-first RAKL discovery artifact.

## J. Build constrained global paths

Compose only compatible local choices.

## K. Mechanize

Where mechanism matters, derive the effective representation from lower-level building blocks or state explicitly that the model is phenomenological/teacher-only.

For a certifying mechanism lane, materialize the candidate as a typed formalism containing symbols, equation ASTs, mechanism graph, observation maps, assumptions, regimes, invariants/limits, falsifiers and provenance.

## L. Construct / invent when required

Only after the pre-candidate gate passes, if existing representations do not close the registered residual, invoke the mechanism-invention workflow rather than expanding a fixed model menu blindly.

Use residual-guided operators such as composition/recombination, latent-state addition, regime splitting, clock changes, coarse/fine graining, stochasticization, feedback/coupling changes, nonlinearization, symmetry/invariant operations, observation-map changes and witnessed analogical transfer.

Every invention must be an explicit typed delta with parent lineage, targeted residual ids and a pointer to the method-transfer row, witnessed analogy or residual that motivated it.

## M. Identify

Ask whether observations distinguish the proposed mechanisms. If not, keep an identified/model set or bounds and generate discriminators or new observation mappings.

## N. Discriminate

Choose the lowest-cost experiment with the highest expected separation or identified-set shrinkage. Freeze predictions and result branches before native execution.

## O. Validate the validator and the formalism

Require clean PASS, planted FAIL, and structural CANNOT_CHECK worlds.

For invented formalisms, bind oracle receipts to the exact candidate identity and check, when applicable:

```text
type/symbol integrity
dimensional consistency
limit cases
invariants
stability
identifiability
simulation sanity
clock/availability/leakage
falsifier execution
```

## P. Run real/native evidence

Use the same registered population, filtration, target, units, and split across competing candidates.

## Q. Read the residual

Do not immediately fit another arbitrary model. Classify the residual and reopen only plausible generating fibers.

A failed candidate emits a residual signature that becomes direct input to the constructive invention algebra. If repeated candidates fail for the same structural reason, reopen the context fiber, method-transfer matrix and analogy scan before generating another candidate.

## R. Tournament and synthesize

Maintain a candidate population and Pareto frontier across:

```text
descriptive coverage
residual closure
predictive value
identification
falsifiability
robustness
novelty
complexity
```

Produce a global object portrait containing established/uncertain facets, representation classes, candidate mechanism ancestry, unresolved residuals and any new derived formalism.

## S. Evaluate the positive-goal contract

If all frozen success gates and required verification checks pass, the exact candidate may advance to independent review and narrow promotion.

Otherwise:

```text
candidate rejected
-> retain negative receipt
-> residual diagnosis
-> reopen context/fibers
-> update analogue/method-transfer/analogy matrix when needed
-> record next-step decision
-> generate/mutate/recombine
-> freeze candidate
-> verify
-> retest
```

Negative candidate evidence is never reclassified as positive closure. Persistent search never licenses fabricated evidence, target leakage, selective deletion, forced analogies, or post-result threshold rescue.

## T. Review

Run same-context consistency/reflection, then isolated reviewers when independence is required. Freeze reports before synthesis.

## U. Promote narrowly

Promote only claims/method steps supported by their evidence scope.

## V. Recurse

Any new contradiction, failure, missing facet, unexplained residual, or method weakness becomes a new RAKL child problem. If the incumbent invention-operator basis cannot cross an identified epistemic cut, open a method-basis gap and evolve RAKL itself.
