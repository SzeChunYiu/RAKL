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

## Public research trace

Every material mathematical-research step must also be appended to a machine-readable trace conforming to `schemas/math-research-trace.schema.json` and `src/rakl/research_trace.py`.

Before the first candidate for an atom, the trace must contain, in chronological order:

1. `ATOMIZED` — exact atomization result and parent/root relation;
2. `CONTEXT_FROZEN` — current context snapshot and context-packet hash;
3. `ANALOGY_SCAN` — retained/refuted cross-domain analogies or explicit no-safe-bridge result;
4. `METHOD_TRANSFER_REVIEW` — solved/near-solved contexts, transferable methods, enabling assumptions and disanalogies;
5. `NEXT_STEP_PROPOSED` — proposed next action, alternatives considered, concise evidence-grounded selection rationale, uncertainties and expected discriminator.

After candidate generation, keep recording `CANDIDATE_PROPOSED`, `FALSIFIER_RUN`, `RESULT_RECORDED`, `RESIDUAL_OPENED`, `FORMALIZED`, `PROOF_CHECKED`, `NOVELTY_CHECKED`, `REVIEWED` and `PROMOTED` events as applicable. Each event must bind evidence/artifact pointers and a content hash.

This trace is an **auditable scientific decision record**, not a raw private chain-of-thought transcript. Record reproducible state, alternatives, concise decision rationale, evidence, outputs, uncertainties, residuals and next actions. Do not claim that hidden model reasoning has been exposed.

Call `plan_math_research(..., context_fiber=..., research_trace=...)`. If `candidate_generation_allowed` is false, do **not** propose a proof, lemma, invariant, auxiliary construction, or mathematical candidate. Execute `pre_candidate_actions` instead. Do not bypass this by directly invoking lower-level search operators or by writing a candidate first and backfilling context/trace later.

A proof that arrives from outside this process may still be checked for truth by the assurance layer, but it must not be described as a strict RAKL context-first discovery unless the pre-candidate chronology and trace gates passed.

Use `python -m rakl` for project state, bounded task packets, exact receipts and reproducible execution where applicable.
