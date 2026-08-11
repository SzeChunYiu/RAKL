# Workflow — Mathematical Research

Use when the target includes a conjecture, theorem, proof, formalization, or a claim of new mathematics.

## Core separation

Keep seven questions independent:

1. **Discovery context** — was the active atom understood across equivalent formulations, solved/near-solved analogues and witnessed method-transfer assumptions before candidate generation?
2. **Research trace** — is there an auditable chronological record of atomization, context, analogy scan, method choice, next action, falsification, residuals and later promotion events?
3. **Specification** — does the formal statement mean what the researcher intended?
4. **Truth** — is that exact formal statement proved from the registered assumptions?
5. **Verifier trust** — what checker, axioms, dependencies and artifact identities does the truth claim rely on?
6. **Novelty** — is an equivalent or stronger prior result already known in the registered literature world?
7. **Research value** — is the result interesting, general, explanatory, or useful enough to pursue or publish?

No score may average these gates together. Discovery-process compliance does not make a theorem true; theorem truth does not retroactively establish that strict RAKL discovery procedure was followed.

## Hard pre-candidate gates

After atomization and **before** the LLM may propose a proof idea, lemma, invariant, auxiliary construction or other mathematical candidate, two process gates must pass.

### Gate A — mathematical context fiber

Freeze a `MathContextFiber` conforming to `schemas/math-context-fiber.schema.json`. It must contain:

1. the exact atomic obstruction and object context;
2. structural coordinates that matter for the obstruction;
3. equivalent formulations/representations;
4. at least one solved or near-solved analogue;
5. a method-transfer matrix;
6. for every transferred method, its required assumptions and source anchors;
7. the exact shared structure between analogue and target;
8. explicit disanalogies/broken assumptions;
9. the smallest repair question exposed by the mismatch;
10. a mandatory cross-domain analogy scan;
11. for every retained analogy, an explicit common abstraction, source-to-target mapping, shared constraints, disanalogies, candidate principle and falsifiable validation obligation;
12. a packet hash and chronology showing the packet was frozen before the first candidate.

The cross-domain scan may inspect other mathematics, physics, engineering, algorithms, biology, games, organizations and ordinary human situations. Its purpose is structural transfer, not storytelling. Surface resemblance is rejected. If no safe analogy survives, record `NO_SAFE_BRIDGE_FOUND` with the search boundary rather than forcing one.

A bibliography, paper list, generic survey or sentence such as "this resembles X" does not pass this gate.

### Gate B — public research trace

Freeze and append an auditable trace conforming to `schemas/math-research-trace.schema.json`. Before candidate generation, the active atom must have these chronological events:

1. `ATOMIZED` — exact decomposition result and relation to parent/root;
2. `CONTEXT_FROZEN` — current context state and exact context-packet hash;
3. `ANALOGY_SCAN` — retained/refuted analogies or explicit no-safe-bridge result;
4. `METHOD_TRANSFER_REVIEW` — source methods, enabling assumptions, shared structure and disanalogies;
5. `NEXT_STEP_PROPOSED` — proposed action, alternatives considered, concise evidence-grounded selection rationale, uncertainty and expected discriminator.

This is an inspectable scientific decision record, not a raw private chain-of-thought transcript. Record only reproducible state, bounded rationale, evidence, outputs, uncertainties, residuals and next actions.

Call `plan_math_research(..., context_fiber=..., research_trace=...)`. If `candidate_generation_allowed` is false, execute only `pre_candidate_actions`. Do not directly call lower-level candidate operators to bypass either gate. Do not write a candidate and backfill context or trace afterward.

## Procedure

1. Freeze the informal research target, assumptions, notation, scope, success criteria and failure conditions. Record `PROBLEM_FROZEN` when a trace is opened.
2. Compile a `ProblemSignature` and decompose the research program into a persistent DAG of conjectures, lemmas, definitions, counterexamples, computations, representations and unresolved proof obligations.
3. Select the smallest active atomic obstruction whose resolution would change the proof DAG or eliminate a material route. Record `ATOMIZED` with the exact atomization output.
4. Build the atom's context fiber. Map structural coordinates and equivalent formulations before proposing a solution.
5. Search multiple vocabularies/disciplines for solved and near-solved contexts with matching structure. Extract methods and enabling assumptions, not paper summaries.
6. Run a cross-domain analogy scan. Abstract away domain nouns and compare roles, constraints, resources, transformations, bottlenecks, information flow, reuse, symmetry, conservation and failure modes. Retain an analogy only when its mapping and disanalogies are explicit.
7. Build the method-transfer matrix. For each analogue, record shared structure, broken assumptions/disanalogies and the minimum repair question needed for transfer.
8. Freeze/hash the context packet and record `CONTEXT_FROZEN`, `ANALOGY_SCAN` and `METHOD_TRANSFER_REVIEW` before candidate generation.
9. Propose the next action and alternatives. Record `NEXT_STEP_PROPOSED` with a concise evidence-grounded rationale and expected discriminator.
10. Pass `audit_math_context_fiber`, `audit_pre_candidate_trace` and `plan_math_research`.
11. Only after both gates pass, use LLMs as proposal generators for conjectures, proof ideas, lemmas, representations, auxiliary objects and search actions. Each candidate must point to the context-transfer row, witnessed analogy or residual that motivated it. Record `CANDIDATE_PROPOSED`.
12. Compile the assurance state into explicit obstructions with `plan_math_research`; use obstruction-guided operator paths as candidate research routes, not truth authority.
13. Run a **counterexample-first pass** before expensive proof search: exact finite enumeration where possible, randomized/property testing, CAS/SMT/SAT/model finding, boundary and degenerate cases. Record `FALSIFIER_RUN` and `RESULT_RECORDED`.
14. If a candidate fails, preserve the failure, record `RESIDUAL_OPENED`, and classify the residual. Update the context fiber when the failure reveals a new structural coordinate, disanalogy, method limitation or equivalent formulation. Do not blindly generate another proof from the same unchanged context packet.
15. Formalize the candidate statement. Bind the informal claim and formal statement with hashes and an explicit `FormalizationWitness`. Record `FORMALIZED`.
16. Check the formalization by round-trip paraphrase, positive/negative examples, boundary cases, assumptions, quantifier order, domains, and at least one independent review for a new-mathematics claim.
17. Search for a proof in a theorem prover or other proof-producing system. Treat every failed proof attempt as negative history rather than deleting it.
18. For any accepted theorem, record a `ProofReceipt` bound to the exact formal statement and source hash. Record `PROOF_CHECKED` only at the actual authority achieved.
19. Audit all transitive proof dependencies. Finished strict-profile results must not depend on `sorryAx`; unregistered custom axioms are rejected, and compiler/native trust is rejected when independent kernel-level assurance is required.
20. Recheck generated proof artifacts in an isolated independent checker where the proof ecosystem supports it. Pin checker versions and dependency identities.
21. Only after truth assurance, open the novelty fiber. Build a notation-normalized and structure-aware theorem fingerprint; search multiple literature corpora, terminology variants, citation neighborhoods, translations, structural equivalents and known stronger parent theorems. Record `NOVELTY_CHECKED`.
22. Record novelty only as a **bounded, cutoff-scoped certificate**. A later prior-art hit may demote novelty without demoting proof validity.
23. Evaluate research value separately: generality, compression, explanatory power, connection to open problems, nontriviality, downstream consequences, new representation/invariant/technique and expert interest.
24. Run same-context consistency review, then genuinely isolated reviewers where independence is required. Record `REVIEWED` with the exact review authority.
25. Promote to `NEW_MATHEMATICS_CANDIDATE` only when specification alignment, proof assurance, verifier-trust audit, bounded novelty, and research-value review all pass. If claiming strict RAKL-mediated discovery, context chronology and research trace must also pass. Record `PROMOTED` only after those gates.
26. Release the context fiber, research trace, theorem statement, proof artifact, dependency/axiom audit, checker identities, corpus cutoff, novelty search routes, structural fingerprint/equivalence policy and negative-history summary.

The executable reference surfaces are:

```text
src/rakl/math_context.py
src/rakl/research_trace.py
src/rakl/problem_solving_algebra.py
src/rakl/math_research_runtime.py
src/rakl/math_research_assurance.py
schemas/math-context-fiber.schema.json
schemas/math-research-trace.schema.json
benchmarks/math_research_assurance/tasks_v0.json
docs/MATH_RESEARCH_QUICKSTART.md
```

## Long-horizon rule

Do not store mathematical research as one long natural-language transcript. Every verified lemma is a persistent checkpoint in the proof DAG. Every active atom has a versioned context fiber and an append-only public research trace. Generator mistakes should increase search cost or create rejected branches; they must not accumulate as hidden logical debt inside an accepted theorem.

When several candidates fail for the same structural reason, do not ask for another unconstrained proof. Promote that repeated residual into a new context atom and search solved sibling contexts and cross-domain analogues for methods that specifically handle the missing structure.

## Analogy discipline

An everyday or cross-domain analogy is useful only as a **proposal compressor**. Convert both source and target into an abstract relational description first. Examples of transferable structure include shared-resource reuse, queueing, caching, bottlenecks, conservation, matching, routing, error correction, adversarial games, local-to-global assembly, redundancy and compression.

For every retained analogy ask:

> What are the objects/roles on each side?
>
> What relation or constraint is truly shared?
>
> What transformation in the source corresponds to a legal transformation in the target?
>
> Which source assumptions have no target analogue?
>
> What candidate principle does the analogy suggest?
>
> What exact mathematical test would refute the transfer?

If the last two questions cannot be answered, discard the analogy.

## Required questions before every candidate

> What exact atomic obstruction is active?
>
> What did atomization produce?
>
> What is the current context snapshot?
>
> What structural coordinates make this atom difficult?
>
> What equivalent formulations expose different available methods?
>
> Which solved or near-solved contexts share those coordinates?
>
> Why does each candidate method work in the source context?
>
> Which assumption fails in the target context?
>
> Did any cross-domain/everyday situation share the same abstract structure, and if so what is the witnessed mapping and disanalogy?
>
> What alternatives were considered for the next step and why was this action selected?
>
> What result would discriminate or falsify this next step?
>
> Were the context packet and trace frozen before the candidate was generated?

If these questions are not answered in frozen artifacts, candidate generation is blocked.

## Required questions at every proof edge

> What exact proposition is being claimed here?
>
> What premises and axioms does it depend on?
>
> Can this edge be refuted cheaply before we spend proof-search budget?
>
> If the formal checker accepts it, have we also checked that the formal statement matches the intended mathematics?
>
> Which checker/trust boundary would have to fail for this accepted edge to be false?

## Failure rules

- `context_missing` or `context_incomplete` blocks candidate generation in strict RAKL mathematical discovery.
- `research_trace_missing` or `research_trace_incomplete` blocks candidate generation.
- `candidate_generated_before_context_freeze` or before required trace events is a chronology failure. The candidate may be evaluated for truth, but it is not a strict context-first RAKL discovery artifact.
- `literature_list_present` is not equivalent to `method_transfer_mapped`.
- `analogy_found` is not equivalent to `analogy_transfer_valid`; abstract mapping, disanalogies and falsifier must be explicit.
- `everyday_story_sounds_similar` has no authority and is discarded unless it survives the witnessed analogy gate.
- repeated failure under an unchanged context packet triggers context reopening rather than unlimited same-basis candidate generation.
- `tested_many_cases` is never promoted to `proved`.
- `candidate_path_completed` is never promoted to `problem_closed` without a verified terminal certificate.
- `machine_proven` is never promoted to `novel` without a novelty certificate.
- `no_prior_art_found` is never represented as globally complete novelty.
- `interesting` cannot compensate for an unproved theorem.
- `proof_found` cannot compensate for a specification mismatch or failed verifier-trust audit.
- resource exhaustion is a nonterminal block, not evidence that a conjecture is false.
