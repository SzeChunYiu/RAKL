# RAKL coding-agent instructions

RAKL is an evidence-governed research method, not a prompt to improvise scientific conclusions.

## Load-on-demand entrypoint

For a RAKL task, read `skills/rakl-core/SKILL.md`, then its manifest, core files, and only the workflow fragments relevant to the active problem.

Do not preload all `research/` or `docs/`. Treat those directories as an external archive and read exact artifacts only when the active fiber requires them.

## Non-negotiable rules

1. Define object/QoI/context before comparing candidates.
2. Projection/context before competition/contradiction.
3. Representation/prediction is not mechanism; mechanism is not identification.
4. LLM output is proposal-only.
5. Preserve nulls, refutations, failures and supersession lineage.
6. Freeze benchmark/evaluator/candidate chronology before evaluated result access.
7. Missing evidence fails closed.
8. Same-session reflection is not independent review.
9. Do not weaken protected evaluators, Constitution invariants, or frozen falsifiers to obtain a pass.
10. Self-RAKL improvements require fresh assurance for a strong evolution claim.

## Mathematical research pre-candidate gate

For any theorem, conjecture, proof search, open problem, or request to "solve" mathematics, candidate generation is **forbidden** immediately after atomization.

After freezing the exact active atomic obstruction, first create and freeze a mathematical context fiber satisfying `schemas/math-context-fiber.schema.json` and `src/rakl/math_context.py`. It must record:

- the exact atomic object/obstruction;
- structural coordinates such as symmetry, locality, algebra, rank, spectrum, composition/reuse law, monotonicity, dimensionality or other load-bearing structure;
- equivalent formulations/representations;
- solved and/or near-solved analogous contexts;
- methods that work in those contexts;
- the assumptions that make each method work;
- shared structure between source and target;
- explicit disanalogies or broken assumptions;
- the smallest repair/transfer question exposed by each mismatch;
- primary/authoritative source anchors;
- a mandatory cross-domain analogy scan, including mathematics, science, engineering, games and ordinary human situations when structurally relevant;
- for every retained analogy, the common abstraction, explicit source-to-target mapping, shared constraints, disanalogies, proposed transferable principle and a falsifiable validation obligation;
- a content hash and chronology proving the context packet was frozen before the first candidate.

An analogy may generate a proposal but never supplies theorem authority. Surface resemblance is insufficient. If no cross-domain or everyday analogy survives the mapping/disanalogy gate, record `NO_SAFE_BRIDGE_FOUND` with the search boundary rather than inventing one.

Do not treat a list of papers or a literature summary as a context fiber. The required object is a **method-transfer matrix** explaining why a method works elsewhere and exactly what blocks its transfer here.

## Scoped success-derived research tool inventory

Successful research steps may become reusable tools, but promotion is not automatic. Use `src/rakl/research_tool_inventory.py` / `schemas/research-tool-inventory.schema.json`.

A reusable `ResearchTool` must record:

- exact source atom/candidate/result/context;
- abstraction and operation;
- preconditions and structural signature;
- guaranteed effects and explicit non-guarantees;
- target-specific validation obligations;
- evidence/proof backing;
- known failure ids and successful reuse ids;
- authority level and artifact hash.

`worked_once` is not `universally_valid`. Before reusing a tool, create a `ToolApplicabilityWitness` checking target preconditions/structure and all known failure warnings. Changed structural coordinates normally require target-specific validation.

## Global failure experience lattice

A failed candidate is both local negative history and a reusable global experience record. After every material failure/refutation, update `src/rakl/failure_lattice.py` / `schemas/failure-experience-lattice.schema.json` with:

- exact atom, candidate, context-packet hash and public research-trace event id;
- method family and falsifier/proof attempt;
- observed result and residual signature;
- competing diagnoses, selected bounded diagnosis and diagnosis status;
- broken assumptions and exact scope conditions;
- evidence pointers, local repair attempts, timestamp and artifact hash.

Then connect the failure to structurally related prior failures using typed relations. Do not equate correlation with cause. Maintain the global portrait of recurring failure modes, broken assumptions, unresolved diagnoses and verified impossibilities.

A prior failure is a warning, **not a blacklist**. Reusing the same method is allowed when the new context differs materially or new evidence/derivation exists. For a close prior failure, supply a `DifferenceWitness` stating what changed, which failed assumption is restored/replaced, why the old falsifier may no longer apply, and the cheapest test that could show the claimed difference is illusory. Only a verified impossibility result may block reuse, and only inside its registered scope.

Repeated unclassified failures are not an invitation to keep guessing. Route them to the existing metacognitive auditor as an ontology/method-basis gap candidate and reopen perspective/context search.

## Dual experience memory review

Before proposing the next candidate, query **both** the success-derived tool inventory and the global failure lattice. Freeze a `ResearchMemoryReview` from `src/rakl/research_memory.py`, bound to the current atom/context and exact memory snapshot hashes.

The review must record candidate method families searched, relevant tool ids or explicit `NO_RELEVANT_MATCH`, relevant failure ids or explicit `NO_RELEVANT_MATCH`, tool applicability notes, failure reuse/scope notes, unresolved warnings, evidence pointers and artifact hash.

Accumulated experience guides search; it never mints theorem truth.

## Role-separated pre-candidate review

Before selecting the next mathematical action, run a same-context expert cell with at least these lenses:

- **domain/theory lead** — exact definitions, known theorems, barriers and model scope;
- **analogy/method-transfer lead** — structural equivalence, enabling assumptions and transfer repair questions;
- **adversarial falsification lead** — cheapest counterexamples, degenerate cases and obstruction-renaming risks;
- **formal-methods lead** — statement binding, proof obligations, checker/trust boundary and formalizability;
- **novelty/research-value lead** — likely prior art, rediscovery risk, explanatory value and next-search information gain.

These are role-separated same-context passes, not independent peer review. Preserve disagreements, strongest objection, unresolved uncertainty and the resulting next-action recommendation in `EXPERT_CONTEXT_REVIEW`.

## Public research trace

Every material mathematical-research step must also be appended to a machine-readable trace conforming to `schemas/math-research-trace.schema.json` and `src/rakl/research_trace.py`.

Before the first candidate for an atom, the trace must contain, in chronological order:

1. `ATOMIZED` — exact atomization result and parent/root relation;
2. `CONTEXT_FROZEN` — current context snapshot and context-packet hash;
3. `ANALOGY_SCAN` — retained/refuted cross-domain analogies or explicit no-safe-bridge result;
4. `METHOD_TRANSFER_REVIEW` — solved/near-solved contexts, transferable methods, enabling assumptions and disanalogies;
5. `EXPERT_CONTEXT_REVIEW` — role-separated objections, disagreements, uncertainties and recommendation;
6. `EXPERIENCE_MEMORY_REVIEW` — exact success-tool/failure-lattice queries, applicability/reuse warnings, selected reusable tools if any, and memory-review artifact;
7. `NEXT_STEP_PROPOSED` — proposed next action, alternatives considered, concise evidence-grounded selection rationale, uncertainties and expected discriminator, including how relevant prior success/failure experience affected the choice.

After candidate generation, keep recording `CANDIDATE_PROPOSED`, `FALSIFIER_RUN`, `RESULT_RECORDED`, `RESIDUAL_OPENED`, `FORMALIZED`, `PROOF_CHECKED`, `NOVELTY_CHECKED`, `REVIEWED` and `PROMOTED` events as applicable. Each event must bind evidence/artifact pointers and a content hash. Every material failed result must also emit/update a failure-experience record; every genuinely reusable successful step may emit a scoped research-tool candidate.

Trace entries are hash-chained: except for the first event, `previous_event_hash` must equal the prior event's `artifact_hash`. This makes chronology tamper-evident and prevents silent insertion or rewriting from looking like an original discovery path.

This trace is an **auditable scientific decision record**, not a raw private chain-of-thought transcript. Record reproducible state, alternatives, concise decision rationale, evidence, outputs, uncertainties, residuals and next actions. Do not claim that hidden model reasoning has been exposed.

Call `plan_math_research(..., context_fiber=..., memory_review=..., research_trace=..., preservation_receipt=...)`. If `candidate_generation_allowed` is false, do **not** propose a proof, lemma, invariant, auxiliary construction, or mathematical candidate. Execute `pre_candidate_actions` instead. Do not bypass this by directly invoking lower-level search operators or by writing a candidate first and backfilling context/memory/trace later.

A proof that arrives from outside this process may still be checked for truth by the assurance layer, but it must not be described as a strict RAKL context-first discovery unless the pre-candidate context, experience-memory and trace gates passed.

Use `python -m rakl` for project state, bounded task packets, exact receipts and reproducible execution where applicable.

## Self-RAKL and framework-upgrade entrypoint

For any task that may change RAKL framework behavior, research workflow, authority semantics, protected evaluators, self-evolution machinery, or method version:

1. read `RAKL_VERSION.json` if present;
2. read `docs/RAKL_UPGRADE_PROTOCOL.md`;
3. inspect the affected contract in `src/rakl/method_specs.py` and the relevant protected gates;
4. classify the change as Class A implementation, Class B workflow/method, or Class C constitution **before editing**;
5. for Class B/C changes, freeze the upgrade hypothesis, predicted meta-QoIs, evaluator/benchmark identity, negative controls and rollback plan before evaluated outcomes;
6. implement on a challenger branch/PR and preserve the exact parent/candidate identity;
7. never interpret deployment, a green badge from another SHA, a caller-supplied authority Boolean, same-session review, or the candidate's own evaluation narrative as promotion evidence;
8. never change a protected evaluator/threshold/assurance packet in the same challenger that it judges unless a separately governed evaluator migration has been frozen;
9. require fresh assurance for a strong method-evolution claim and keep exposed assurance packets out of later strong claims;
10. after any promotion, separately attest that active `main` contains the approved content and passes exact-active-main validation.

A direct operator instruction may override this process operationally. Record such an event as an explicit operator/process override. It may move code, but it does not create Self-RAKL evolution evidence by itself.
