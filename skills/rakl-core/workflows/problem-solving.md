# Workflow — Problem Solving v2: Instrumented Research Machine

Use for a new scientific, mathematical, engineering, or modelling problem.

This workflow treats RAKL as a **research machine**, not an LLM prompt chain. The LLM is one proposer/tool among retrieval, structured memory, symbolic/numerical computation, experiment design, verification, metrology and governed self-evolution.

## Research-machine invariant

For every consequential transition:

```text
state_before
-> process_surface
-> prediction / expected effect
-> action
-> observable result
-> state_after
-> cost / uncertainty
-> typed residual
-> next action
```

Emit canonical process telemetry using the existing RAKL metrology/evolution objects. Inventory counts are descriptive only. A step that cannot produce the required identity, evidence or metrology fails closed as `CANNOT_CHECK`.

## Phase 0 — Freeze target, instrument and bind the epoch

1. Define the object, downstream QoI/decision and positive-goal criteria when applicable.
2. Compile the problem signature: objects, relations, quantifiers, symmetries, domain, goal type and constraints.
3. Bind model/tool/harness/repository/evaluator identities and the registered cost policy for the observational epoch.
4. Draw the current solution chain as atomic transformations and register every unresolved step as an explicit obstruction.
5. Open a persistent knowledge fiber for every unresolved consequential step.

Do not interpret a model/tool/harness change as scientific learning without a new observational epoch or a matched same-time control.

## Phase 1 — Initial Apple knowledge acquisition

For a consequential research problem, do not jump directly from prompt to candidate. For every unresolved knowledge fiber, compose `literature-absorption` and perform bounded search/read/normalize rounds across the registered route families.

At minimum consider:

```text
foundational / exact theory
failure / impossibility / counterexample literature
newest primary research
adjacent scientific/mathematical domains
deliberately alien domains with matching structure
alternative terminology / notation / ontology
citation ancestry / influential descendants
relevant standards, repositories, datasets or grey literature when applicable
```

Each round must produce a `KnowledgeAcquisitionRound`-equivalent record containing source/query identity, relevant sources, retained semantic objects, Apple projection classes, cost and evidence pointers.

**Paper count is never a stopping rule.**

For each retained source projection record:

```text
object
facet
projection / observation operator
context
claim
assumptions
uncertainty/evidence level
what the projection cannot see
downstream QoI implication
```

## Phase 2 — Quantified bounded knowledge saturation

Evaluate the KNOWLEDGE axis using the existing saturation-vector semantics plus the registered route-family coverage.

Proceed from broad knowledge acquisition to object work only when:

```text
recent retained semantic novelty == 0
AND enough independent route families are flat
AND all required route families are covered or explicitly blocked
AND no native residual reopens KNOWLEDGE
AND freshness is acceptable for the problem's evidence horizon
```

A search-budget limit while semantic novelty continues to arrive is `NOT_SATURATED`, not evidence of completeness.

A bounded saturation certificate is local to the registered source/query/evidence universe. It never means “all relevant knowledge in existence is known.”

## Phase 3 — Reconstruct the object before model competition

Apply the Apple Principle:

```text
GLUE
-> align projections and contexts
-> classify complementary/equivalent/contextual/contradictory relations
-> connect mechanisms between facets
-> preserve unresolved contradictions

ABSTRACT
-> remove domain identity while recording an erasure ledger

JUMP
-> search distant realizations of preserved structure
-> create mapping witnesses
-> treat transferred ideas as hypotheses only

TEST
-> validate in the target domain
-> GLUE new evidence
```

Maintain an object portrait containing facet coverage, projection diversity, context coverage, mechanism connectivity, contradictions, blind spots and unresolved coordinates.

## Phase 4 — Construct and test object-level paths

6. For each unresolved step, enumerate alternative representations, mechanisms, assumptions, observations, scales, inference methods and falsifiers.
7. Collapse exact/equivalent representations and remove incompatible combinations.
8. Retrieve typed research operators whose preconditions match the current state and whose targets intersect active obstructions.
9. Construct candidate operator paths. Rank paths by explicit cost, verification debt, boundary risk and obstruction relief.
10. Treat operator composition as partial and non-commutative unless witnessed otherwise.
11. Identify observations/proof obligations that fail to distinguish survivors.
12. Choose discriminators, falsifiers or verifiers.
13. Validate on controlled/known-answer/hostile worlds before native evidence where applicable.
14. Preserve every failed path as negative history.
15. Synthesize a global object portrait and only derive a new formalism when surviving prior descriptions can be recovered as scoped projections/special cases.

The executable planning layer remains `src/rakl/problem_solving_algebra.py`; planning objects cannot mint terminal scientific authority.

## Phase 5 — Instrument every consequential process

Every material invocation of a canonical `method_specs.py` surface should emit the existing `ProcessTelemetry`/metric lineage with, at minimum:

```text
process + invocation identity
task / episode identity
input and output state hashes
registered cost policy + resource use
predicted useful-progress / expected effect when available
outcome
residual-before / residual-after
seven-axis retained novelty
retrieved / selected / rejected ids
verification / evidence pointers
uncertainty / calibration information when available
timestamp
```

Process-specific indicators should be used rather than a single RAKL score. Examples:

```text
search/query generation:
  relevant-hit rate
  semantic novelty/query
  cost/new semantic object
  missed-key-source diagnostics

reading/extraction:
  new facets/mechanisms/contexts/contradictions/blind-spots
  semantic yield/source
  source-scope mismatch

GLUE:
  facet/projection coverage gain
  context-resolved disagreement
  false semantic merge
  unresolved interface rate

JUMP:
  structural-mapping yield
  false-transfer rate
  target-domain transfer success

routing:
  route success/calibration
  regret when estimable
  saturated-route retry rate
  route-switch latency

experiment/discriminator selection:
  separation/information gain per cost
  decisive-discriminator rate

verification:
  planted-fail detection
  structural CANNOT_CHECK honesty
  false-positive/false-negative rate

stopping:
  semantic novelty slope
  independent flat routes
  false saturation
  wasted post-saturation search
```

Hard-protected integrity metrics remain non-compensatory and cannot be traded for performance gains.

## Phase 6 — Residual-conditioned recursion

Use residuals to choose which fiber to reopen. Do **not** restart every process after every failure.

```text
MISSING_EVIDENCE_OR_MEASUREMENT -> targeted evidence acquisition
KNOWLEDGE_GAP                 -> targeted literature resaturation
RETRIEVAL_OR_MEMORY_GAP       -> memory/retrieval policy
REPRESENTATION_GAP            -> representation search/restructuring
METHOD_OPERATOR_GAP           -> operator invention / Self-RAKL bridge
EXPERIMENT_SELECTION_GAP      -> discriminator/experimental-design search
VERIFIER_GAP                  -> verifier/assurance repair
IMPLEMENTATION_DEFECT         -> code/tool repair
MODEL_TOOL_FLOOR              -> tool/model capability escalation or CANNOT_CHECK
UNKNOWN                       -> cheapest discriminating challenge
```

A previously saturated knowledge fiber remains valid across ordinary local iterations. Reopen it only when a native residual, contradiction, ontology/representation change, source-freshness event or explicit coverage defect invalidates the prior certificate.

## Phase 7 — Persistent incremental reading, not repeated full rereads

After initial bounded saturation:

```text
ordinary local iteration
-> retrieve from the persistent Knowledge Atlas
-> do not rerun global literature saturation

new knowledge residual
-> targeted search/read/normalize around the new residual
-> re-establish local flatness

freshness event / fast-moving field
-> incremental search from the prior cutoff
-> do not erase previous normalized knowledge
```

This turns literature acquisition into a persistent cache with explicit invalidation rather than a full rebuild every iteration.

## Phase 8 — Self-RAKL trigger

The observatory should periodically ask which RAKL method surface is the bottleneck.

Open `self-rakl` when evidence supports a framework/process problem, for example:

```text
repeated same-surface residuals across non-equivalent object attempts
poor process calibration
high cost with low residual closure
persistent false saturation or retrieval misses
repeated GLUE/JUMP failure
operator-basis exhaustion
a method surface materially underperforms a frozen challenger
```

One project failure never automatically implies framework evolution.

## Mathematical-research handoff

If any target is a conjecture, theorem, proof, formalization or claim of new mathematics, compose this workflow with `mathematical-research.md`. Generated derivations, numerical examples, CAS output or absence of counterexamples remain proposals/evidence until mathematical assurance classifies them.

## Required questions at every step

> What aspect of the object does this step preserve, and what does it throw away?

> Which explicit obstruction is this operation intended to relieve, what new obligation does it introduce, and under what conditions is the next operation composable?

> What quantitative evidence says this is the best next use of research resources rather than another search/read/experiment/verification action?

For proof edges also ask:

> What exact proposition is claimed, which assumptions does it depend on, and what independent checker or refuter can attack it?

## Failure / stopping rules

- If all models fail, reopen source, observation, target, identifiability, decomposition, representation, operator basis and scale fibers before merely increasing model complexity.
- Resource exhaustion is nonterminal.
- Knowledge saturation is not problem closure.
- A bounded knowledge-saturation state may persist through local iterations.
- A new native residual can reopen the affected fiber.
- Terminal closure requires the appropriate verified certificate.
- No aggregate efficiency/quality score can average away a hard integrity failure.

## Output minimum

Every substantive cycle should expose:

```text
object / QoI / positive-goal status
active atom(s)
research-machine/evaluation epoch
knowledge fiber identity
knowledge saturation state + route coverage
reading/search semantic-gain indicators
Apple object portrait state
process telemetry for consequential steps
candidate paths / experiments / proofs
residual changes
cost/resource vector
self-model prediction vs observation when available
next action and why
Self-RAKL trigger state
```
