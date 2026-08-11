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
- a content hash and chronology proving the context packet was frozen before the first candidate.

Do not treat a list of papers or a literature summary as a context fiber. The required object is a **method-transfer matrix** explaining why a method works elsewhere and exactly what blocks its transfer here.

Call `plan_math_research(..., context_fiber=...)`. If `candidate_generation_allowed` is false, do **not** propose a proof, lemma, invariant, auxiliary construction, or mathematical candidate. Execute `pre_candidate_actions` instead. Do not bypass this by directly invoking lower-level search operators or by writing a candidate first and backfilling context later.

A proof that arrives from outside this process may still be checked for truth by the assurance layer, but it must not be described as a strict RAKL context-first discovery unless the pre-candidate chronology gate passed.

Use `python -m rakl` for project state, bounded task packets, exact receipts and reproducible execution where applicable.
