# Workflow — Mathematical Research

Use when the target includes a conjecture, theorem, proof, formalization, or a claim of new mathematics.

## Core separation

Keep nine questions independent:

1. **Discovery context** — was the active atom understood across equivalent formulations, solved/near-solved analogues and witnessed method-transfer assumptions before candidate generation?
2. **Accumulated experience** — were relevant success-derived tools and prior failure experiences queried, scoped and incorporated before choosing the next move?
3. **Semantic shortcut** — was the active relational obstruction fingerprinted and routed through direct reuse, witnessed far transfer, compatible composition, or bounded residual-guided invention in the correct order?
4. **Research trace** — is there an auditable chronological record of atomization, context, analogy scan, experience review, obstruction–transformation routing, method choice, expert objections, next action, falsification, residuals and later promotion events?
5. **Specification** — does the formal statement mean what the researcher intended?
6. **Truth** — is that exact formal statement proved from the registered assumptions?
7. **Verifier trust** — what checker, axioms, dependencies and artifact identities does the truth claim rely on?
8. **Novelty** — is an equivalent or stronger prior result already known in the registered literature world?
9. **Research value** — is the result interesting, general, explanatory, or useful enough to pursue or publish?

No score may average these gates together. Discovery-process compliance does not make a theorem true; theorem truth does not retroactively establish that strict RAKL discovery procedure was followed.

## Hard pre-candidate gates

After atomization and **before** the LLM may propose a proof idea, lemma, invariant, auxiliary construction or other mathematical candidate, four process gates must pass.

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

### Gate C — obstruction–transformation semantic shortcut

Freeze an `ObstructionTransformationReview` conforming to `schemas/obstruction-transformation-review.schema.json` and `src/rakl/semantic_shortcut.py`, bound to the active atom, context hash, dual-memory review hash, and exact obstruction–transformation episode-memory snapshot.

The central search question is:

> **Has this relational obstruction — and a transformation that breaks it — occurred anywhere in recorded knowledge?**

First construct an `ObstructionFingerprint` using structural coordinates rather than surface vocabulary:

```text
roles
relations
constraints
failure mechanisms
invariants to preserve
desired transition
forbidden losses
```

Then route in strict invention-last order:

1. **SEARCH** — retrieve a directly applicable recorded obstruction→transformation episode in the same or compatible context;
2. **JUMP** — if no direct route survives, retrieve a structurally analogous episode from any recorded domain and require a `StructuralMappingWitness` with source→target role mapping, shared relations/constraints, material disanalogies and target-validation obligations;
3. **GLUE** — if no single episode closes the obstruction, compose compatible partial transformations only with a `TransformationCompositionWitness` binding operation order, interfaces, incompatibility checks and target-validation obligations;
4. **LIFT** — only if SEARCH, JUMP and GLUE are each explicitly `NO_VIABLE_MATCH` inside a recorded bounded search and at least two distinct failed attempts share residual structure, produce a `MissingTransformationSpecification` describing what an invented representation/operator must preserve, break, expose, reduce and validate;
5. **CANNOT_CHECK** — when the evidence needed to justify the next route is incomplete.

The episode source may come from mathematics, science, engineering, algorithms, organizations, ordinary situations, journalism or other recorded knowledge. A source event can be valid while its transfer is invalid. The mapping witness, not lexical similarity or embedding proximity, carries the transport obligation.

`LIFT` is not permission for unconstrained creativity. A single failed proof, an unbounded retrieval miss, or a desire for novelty cannot establish the need for invention. LIFT outputs a constrained inverse-invention target, not theorem truth or a promoted research tool.

### Gate D — public research trace

Freeze and append an auditable trace conforming to `schemas/math-research-trace.schema.json`. Before candidate generation, the active atom must have these chronological events:

1. `ATOMIZED` — exact decomposition result and relation to parent/root;
2. `CONTEXT_FROZEN` — current context state and exact context-packet hash;
3. `ANALOGY_SCAN` — retained/refuted analogies or explicit no-safe-bridge result;
4. `METHOD_TRANSFER_REVIEW` — source methods, enabling assumptions, shared structure and disanalogies;
5. `EXPERT_CONTEXT_REVIEW` — role-separated objections, disagreements, unresolved uncertainty and recommendation;
6. `EXPERIENCE_MEMORY_REVIEW` — relevant success tools, failure experiences, applicability/reuse warnings and exact memory-review artifact;
7. `OBSTRUCTION_TRANSFORMATION_REVIEW` — relational obstruction fingerprint, episode-memory snapshot, SEARCH/JUMP/GLUE/LIFT results, witnesses, selected mode and exact shortcut-review artifact;
8. `NEXT_STEP_PROPOSED` — proposed action, alternatives considered, concise evidence-grounded selection rationale, uncertainty and expected discriminator.

The pre-candidate expert cell must cover at least: domain/theory, analogy/method transfer, adversarial falsification, formal methods/verifier trust, and novelty/research value. These are same-context role-separated passes and must never be labelled independent peer review.

Trace entries are hash-chained. Except for the first event, `previous_event_hash` must equal the previous event's `artifact_hash`. This makes the public chronology tamper-evident.

This is an inspectable scientific decision record, not a raw private chain-of-thought transcript. Record only reproducible state, bounded rationale, evidence, outputs, uncertainties, residuals and next actions.

Call `plan_math_research(..., context_fiber=..., memory_review=..., shortcut_review=..., research_trace=...)`. If `candidate_generation_allowed` is false, execute only `pre_candidate_actions`. Do not directly call lower-level candidate operators to bypass any gate. Do not write a candidate and backfill context, memory review, shortcut review or trace afterward.

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
13. Build the active `ObstructionFingerprint`. Treat domain nouns as labels and preserve only load-bearing roles, relations, constraints, failure mechanisms, invariants, desired transition and forbidden losses.
14. Query recorded obstruction→transformation episodes. Prefer direct applicability first, then structural far transfer. Rankers may propose matches but cannot certify transport.
15. If direct reuse is viable, select `SEARCH`. If not, test JUMP candidates using explicit `StructuralMappingWitness` objects. Reject a JUMP whose enabling relation, constraint, invariant or target-validation obligation is missing.
16. If no single JUMP survives, search compatible partial transformations and use `GLUE` only with an explicit composition witness and interface obligations.
17. Enter `LIFT` only when SEARCH/JUMP/GLUE are each explicitly exhausted or blocked inside the recorded boundary and repeated residual structure exists across at least two distinct failed attempts. Convert those residuals into a frozen `MissingTransformationSpecification`; do not invent the candidate operator yet.
18. Freeze the `ObstructionTransformationReview` and record `OBSTRUCTION_TRANSFORMATION_REVIEW` with its exact artifact hash and unresolved warnings.
19. Propose the next action and alternatives. Record `NEXT_STEP_PROPOSED` with a concise evidence-grounded rationale and expected discriminator, including how accumulated experience and the shortcut route affected the choice.
20. Pass `audit_math_context_fiber`, `audit_research_memory_review`, `audit_obstruction_transformation_review`, `audit_pre_candidate_trace` and `plan_math_research`.
21. Only after all four gates pass, use LLMs as proposal generators for conjectures, proof ideas, lemmas, representations, auxiliary objects and search actions. Each candidate must point to the context-transfer row, witnessed analogy, reusable tool, obstruction–transformation episode/witness, failure repair/difference witness, LIFT specification or residual that motivated it. Record `CANDIDATE_PROPOSED`.
22. Run a **counterexample-first pass** before expensive proof search. Record `FALSIFIER_RUN` and `RESULT_RECORDED`.
23. If a candidate fails, preserve the exact failure and record `RESIDUAL_OPENED`. Generate competing diagnoses, test them where possible, create/update a `FailureExperience`, link it into the global failure lattice, and update the global failure portrait. Reopen context and the obstruction–transformation review if the failure reveals a new structural coordinate, transfer mismatch or repeated residual feature.
24. If a candidate succeeds, update the knowledge/proof DAG at the exact authority achieved. If a method step is genuinely reusable, distill a scoped `ResearchTool`; do not automatically universalize the success. A validated obstruction→transformation episode may also be added to structural episode memory with exact source/target lineage.
25. Formalize the candidate statement. Bind the informal claim and formal statement with hashes and an explicit `FormalizationWitness`. Record `FORMALIZED`.
26. Check the formalization by round-trip paraphrase, positive/negative examples, boundary cases, assumptions, quantifier order, domains, and at least one independent review for a new-mathematics claim.
27. Search for a proof in a theorem prover or other proof-producing system. Treat every failed proof attempt as negative history and failure experience when material.
28. For any accepted theorem, record a `ProofReceipt` bound to the exact formal statement and source hash. Record `PROOF_CHECKED` only at the actual authority achieved.
29. Audit all transitive proof dependencies and recheck generated proof artifacts in an isolated independent checker where supported.
30. Only after truth assurance, open the novelty fiber. Build a notation-normalized and structure-aware theorem fingerprint; search multiple literature corpora and structural equivalents. Record `NOVELTY_CHECKED`.
31. Record novelty only as a bounded, cutoff-scoped certificate.
32. Evaluate research value separately.
33. Run same-context consistency review, then genuinely isolated reviewers where independence is required. Record `REVIEWED` with exact review authority.
34. Promote to `NEW_MATHEMATICS_CANDIDATE` only when specification alignment, proof assurance, verifier-trust audit, bounded novelty, and research-value review all pass. If claiming strict RAKL-mediated discovery, context, dual-memory, obstruction–transformation and trace chronology must also pass. Record `PROMOTED` only after those gates.
35. Release the context fiber, memory review, obstruction–transformation review, research trace, relevant tool/failure/episode records, theorem statement, proof artifact, dependency/axiom audit, checker identities, novelty search world and negative-history summary.

## Long-horizon memory rule

Do not store research as one long transcript or a folder of disconnected attempts. Maintain five complementary planes:

```text
knowledge/proof DAG                 -> what is known / open
scoped tool inventory               -> what has worked, under what conditions
failure experience lattice          -> what has failed, why/scope/repairs
obstruction-transformation episodes -> where a structural obstruction changed and by what operation
public research trace               -> how the state changed over time
```

The obstruction–transformation episode memory is a structural retrieval projection over accumulated experience, not a new truth-authority store. Its source episode and authority must remain explicit. Target transport always requires a target witness and validation.

`src/rakl/metacognition.py` sits above these planes. Repeated unclassified failures may expose an ontology or method-basis gap and become a new RAKL child problem.

When several candidates fail for the same structural reason, do not ask for another unconstrained proof. Promote the repeated residual into a new context/meta atom, rerun SEARCH/JUMP/GLUE over that obstruction, and only then let a valid LIFT specification constrain invention.

## Analogy discipline

An everyday or cross-domain analogy is useful only as a **proposal compressor**. Convert both source and target into an abstract relational description first. Examples of transferable structure include shared-resource reuse, queueing, caching, bottlenecks, conservation, matching, routing, error correction, adversarial games, local-to-global assembly, redundancy and compression.

If an analogy cannot produce an explicit target-domain candidate principle and falsifiable test, discard it. If it is retained as a JUMP, bind it to a `StructuralMappingWitness`; a prose analogy alone does not satisfy the semantic-shortcut gate.

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
> **Has this relational obstruction — and a transformation that breaks it — occurred anywhere in recorded knowledge?**
>
> Which route is justified: SEARCH, JUMP, GLUE, LIFT or CANNOT_CHECK?
>
> If JUMP, where is the explicit source→target structural witness and what disanalogy can kill the transfer?
>
> If GLUE, what interface and ordering obligations make the composition valid?
>
> If LIFT, what bounded evidence shows SEARCH/JUMP/GLUE were exhausted, which residual feature repeats across distinct failures, and what exactly must the missing transformation preserve/break/expose/reduce?
>
> If we reuse a previously failed method, what changed and what is the cheapest old-failure regression test?
>
> What did each expert lens object to?
>
> What alternatives were considered and why is this the next action?
>
> What result would discriminate or falsify it?
>
> Were context, memory review, shortcut review and hash-chained trace frozen before candidate generation?

If these are not answered in frozen artifacts, candidate generation is blocked.

## Failure rules

- missing/incomplete context, memory review, obstruction–transformation review or research trace blocks candidate generation;
- a literature list is not a method-transfer matrix;
- an analogy is not a transfer without structural mapping, disanalogy and falsifier;
- embedding/lexical similarity is not a structural mapping witness;
- a direct applicable transformation blocks premature LIFT;
- one failed candidate never establishes the need for a new tool;
- multiple failures without a repeated residual feature do not justify a coherent missing-transformation specification;
- GLUE without ordering/interface obligations is invalid;
- a LIFT specification is proposal-only and cannot mint proof or method authority;
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
src/rakl/semantic_shortcut.py
src/rakl/research_trace.py
src/rakl/metacognition.py
src/rakl/math_research_runtime.py
src/rakl/math_research_assurance.py
schemas/math-context-fiber.schema.json
schemas/research-tool-inventory.schema.json
schemas/failure-experience-lattice.schema.json
schemas/research-memory-review.schema.json
schemas/obstruction-transformation-review.schema.json
schemas/math-research-trace.schema.json
docs/RESEARCH_MEMORY_ARCHITECTURE.md
docs/SEMANTIC_SHORTCUT_ROUTER.md
```
