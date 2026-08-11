# Workflow — Mathematical Research

Use when the target includes a conjecture, theorem, proof, formalization, or a claim of new mathematics.

## Core separation

Keep eight questions independent:

1. **Discovery context** — was the active atom understood across equivalent formulations, solved/near-solved analogues and witnessed method-transfer assumptions before candidate generation?
2. **Accumulated experience** — were relevant success-derived tools and prior failure experiences queried, scoped and incorporated before choosing the next move?
3. **Research trace** — is there an auditable chronological record of atomization, context, analogy scan, experience review, method choice, expert objections, next action, falsification, residuals and later promotion events?
4. **Specification** — does the formal statement mean what the researcher intended?
5. **Truth** — is that exact formal statement proved from the registered assumptions?
6. **Verifier trust** — what checker, axioms, dependencies and artifact identities does the truth claim rely on?
7. **Novelty** — is an equivalent or stronger prior result already known in the registered literature world?
8. **Research value** — is the result interesting, general, explanatory, or useful enough to pursue or publish?

No score may average these gates together. Discovery-process compliance does not make a theorem true; theorem truth does not retroactively establish that strict RAKL discovery procedure was followed.

## Hard pre-candidate gates

After atomization and **before** the LLM may propose a proof idea, lemma, invariant, auxiliary construction or other mathematical candidate, three process gates must pass.

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

### Gate B — dual research experience memory

Before selecting a candidate method, query both:

- the **scoped success-derived research tool inventory** (`src/rakl/research_tool_inventory.py`);
- the **global failure experience lattice** (`src/rakl/failure_lattice.py`).

Freeze a `ResearchMemoryReview` bound to the current atom/context and exact memory snapshot hashes. Record the candidate method families searched, relevant tool ids, relevant failure ids, tool applicability assessment, failure reuse/scope assessment, unresolved warnings and evidence pointers. Explicit `NO_RELEVANT_MATCH` is allowed; silently skipping the query is not.

Successful steps are promoted to reusable tools only when preconditions, structural signature, guaranteed effects, non-guarantees, validation obligations, provenance and known failure history are explicit. `worked_once` never means `universally_valid`.

Failures are reusable experience, not blacklists. Reusing a method with relevant prior failure history requires a scope/difference witness and targeted repeat-failure test. Only a verified impossibility result may globally block reuse, and only inside its registered scope.

### Gate C — public research trace

Freeze and append an auditable trace conforming to `schemas/math-research-trace.schema.json`. Before candidate generation, the active atom must have these chronological events:

1. `ATOMIZED` — exact decomposition result and relation to parent/root;
2. `CONTEXT_FROZEN` — current context state and exact context-packet hash;
3. `ANALOGY_SCAN` — retained/refuted analogies or explicit no-safe-bridge result;
4. `METHOD_TRANSFER_REVIEW` — source methods, enabling assumptions, shared structure and disanalogies;
5. `EXPERT_CONTEXT_REVIEW` — role-separated objections, disagreements, unresolved uncertainty and recommendation;
6. `EXPERIENCE_MEMORY_REVIEW` — relevant success tools, failure experiences, applicability/reuse warnings and exact memory-review artifact;
7. `NEXT_STEP_PROPOSED` — proposed action, alternatives considered, concise evidence-grounded selection rationale, uncertainty and expected discriminator.

The pre-candidate expert cell must cover at least: domain/theory, analogy/method transfer, adversarial falsification, formal methods/verifier trust, and novelty/research value. These are same-context role-separated passes and must never be labelled independent peer review.

Trace entries are hash-chained. Except for the first event, `previous_event_hash` must equal the previous event's `artifact_hash`. This makes the public chronology tamper-evident.

This is an inspectable scientific decision record, not a raw private chain-of-thought transcript. Record only reproducible state, bounded rationale, evidence, outputs, uncertainties, residuals and next actions.

Call `plan_math_research(..., context_fiber=..., memory_review=..., research_trace=...)`. If `candidate_generation_allowed` is false, execute only `pre_candidate_actions`. Do not directly call lower-level candidate operators to bypass any gate. Do not write a candidate and backfill context, memory review or trace afterward.

## Procedure

1. Freeze the informal research target, assumptions, notation, scope, success criteria and failure conditions. Record `PROBLEM_FROZEN` when a trace is opened.
2. Compile a `ProblemSignature` and decompose the research program into a persistent DAG of conjectures, lemmas, definitions, counterexamples, computations, representations and unresolved proof obligations.
3. Select the smallest active atomic obstruction whose resolution would change the proof DAG or eliminate a material route. Record `ATOMIZED` with the exact atomization output.
4. Build the atom's context fiber. Map structural coordinates and equivalent formulations before proposing a solution.
5. Search multiple vocabularies/disciplines for solved and near-solved contexts with matching structure. Extract methods and enabling assumptions, not paper summaries.
6. Run a cross-domain analogy scan. Abstract away domain nouns and compare roles, constraints, resources, transformations, bottlenecks, information flow, reuse, symmetry, conservation and failure modes. Retain an analogy only when its mapping and disanalogies are explicit.
7. Build the method-transfer matrix. For each analogue, record shared structure, broken assumptions/disanalogies and the minimum repair question needed for transfer.
8. Freeze/hash the context packet and record `CONTEXT_FROZEN`, `ANALOGY_SCAN` and `METHOD_TRANSFER_REVIEW` before candidate generation.
9. Convene the same-context expert cell. Preserve disagreement and record `EXPERT_CONTEXT_REVIEW`.
10. Query the success-derived tool inventory for structurally applicable methods and review each tool's preconditions, guarantees, non-guarantees, validation obligations and known failures.
11. Query the failure lattice for relevant method families, broken assumptions and residual signatures. If reusing a warned method, record a `DifferenceWitness` and cheapest repeat-failure test. If repeated residuals remain unclassified, route them to metacognition rather than guessing again.
12. Freeze the `ResearchMemoryReview` and record `EXPERIENCE_MEMORY_REVIEW`.
13. Propose the next action and alternatives. Record `NEXT_STEP_PROPOSED` with a concise evidence-grounded rationale and expected discriminator, including how accumulated experience affected the choice.
14. Pass `audit_math_context_fiber`, `audit_research_memory_review`, `audit_pre_candidate_trace` and `plan_math_research`.
15. Only after all three gates pass, use LLMs as proposal generators for conjectures, proof ideas, lemmas, representations, auxiliary objects and search actions. Each candidate must point to the context-transfer row, witnessed analogy, reusable tool, failure repair/difference witness or residual that motivated it. Record `CANDIDATE_PROPOSED`.
16. Run a **counterexample-first pass** before expensive proof search. Record `FALSIFIER_RUN` and `RESULT_RECORDED`.
17. If a candidate fails, preserve the exact failure and record `RESIDUAL_OPENED`. Generate competing diagnoses, test them where possible, create/update a `FailureExperience`, link it into the global failure lattice, and update the global failure portrait. Reopen context if the failure reveals a new structural coordinate or transfer mismatch.
18. If a candidate succeeds, update the knowledge/proof DAG at the exact authority achieved. If a method step is genuinely reusable, distill a scoped `ResearchTool`; do not automatically universalize the success.
19. Formalize the candidate statement. Bind the informal claim and formal statement with hashes and an explicit `FormalizationWitness`. Record `FORMALIZED`.
20. Check the formalization by round-trip paraphrase, positive/negative examples, boundary cases, assumptions, quantifier order, domains, and at least one independent review for a new-mathematics claim.
21. Search for a proof in a theorem prover or other proof-producing system. Treat every failed proof attempt as negative history and failure experience when material.
22. For any accepted theorem, record a `ProofReceipt` bound to the exact formal statement and source hash. Record `PROOF_CHECKED` only at the actual authority achieved.
23. Audit all transitive proof dependencies and recheck generated proof artifacts in an isolated independent checker where supported.
24. Only after truth assurance, open the novelty fiber. Build a notation-normalized and structure-aware theorem fingerprint; search multiple literature corpora and structural equivalents. Record `NOVELTY_CHECKED`.
25. Record novelty only as a bounded, cutoff-scoped certificate.
26. Evaluate research value separately.
27. Run same-context consistency review, then genuinely isolated reviewers where independence is required. Record `REVIEWED` with exact review authority.
28. Promote to `NEW_MATHEMATICS_CANDIDATE` only when specification alignment, proof assurance, verifier-trust audit, bounded novelty, and research-value review all pass. If claiming strict RAKL-mediated discovery, context, dual-memory and trace chronology must also pass. Record `PROMOTED` only after those gates.
29. Release the context fiber, memory review, research trace, relevant tool/failure records, theorem statement, proof artifact, dependency/axiom audit, checker identities, novelty search world and negative-history summary.

## Long-horizon memory rule

Do not store research as one long transcript or a folder of disconnected attempts. Maintain four complementary planes:

```text
knowledge/proof DAG       -> what is known / open
scoped tool inventory     -> what has worked, under what conditions
failure experience lattice-> what has failed, why/scope/repairs
public research trace     -> how the state changed over time
```

`src/rakl/metacognition.py` sits above these planes. Repeated unclassified failures may expose an ontology or method-basis gap and become a new RAKL child problem.

When several candidates fail for the same structural reason, do not ask for another unconstrained proof. Promote that repeated residual into a new context/meta atom and search for methods that specifically handle the missing structure.

## Analogy discipline

An everyday or cross-domain analogy is useful only as a **proposal compressor**. Convert both source and target into an abstract relational description first. Examples of transferable structure include shared-resource reuse, queueing, caching, bottlenecks, conservation, matching, routing, error correction, adversarial games, local-to-global assembly, redundancy and compression.

If an analogy cannot produce an explicit target-domain candidate principle and falsifiable test, discard it.

## Required questions before every candidate

> What exact atomic obstruction is active, and what did atomization produce?
>
> What is the current context snapshot and structural coordinates?
>
> Which solved/near-solved contexts and cross-domain analogies share the structure?
>
> Why do their methods work, and which assumptions break here?
>
> What successful RAKL tools are relevant, and do their preconditions actually match?
>
> What prior failures are structurally relevant, and what did we learn from them?
>
> If we reuse a previously failed method, what changed and what is the cheapest old-failure regression test?
>
> What did each expert lens object to?
>
> What alternatives were considered and why is this the next action?
>
> What result would discriminate or falsify it?
>
> Were context, memory review and hash-chained trace frozen before candidate generation?

If these are not answered in frozen artifacts, candidate generation is blocked.

## Failure rules

- missing/incomplete context, memory review or research trace blocks candidate generation;
- a literature list is not a method-transfer matrix;
- an analogy is not a transfer without structural mapping, disanalogy and falsifier;
- a successful local step does not become a universal tool without scope/applicability evidence;
- a failed local step does not become a universal blacklist;
- repeated same-context retry without new derivation/evidence or a difference witness is rejected as search drift;
- repeated unclassified failures trigger metacognitive gap analysis;
- finite tests are never promoted to proof;
- planning completion is never promoted to problem closure;
- machine proof never implies novelty;
- resource exhaustion is nonterminal.

The executable reference surfaces are:

```text
src/rakl/math_context.py
src/rakl/research_tool_inventory.py
src/rakl/failure_lattice.py
src/rakl/research_memory.py
src/rakl/research_trace.py
src/rakl/metacognition.py
src/rakl/math_research_runtime.py
src/rakl/math_research_assurance.py
schemas/math-context-fiber.schema.json
schemas/research-tool-inventory.schema.json
schemas/failure-experience-lattice.schema.json
schemas/research-memory-review.schema.json
schemas/math-research-trace.schema.json
docs/RESEARCH_MEMORY_ARCHITECTURE.md
