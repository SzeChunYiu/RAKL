# Workflow — Mathematical Research

Use when the target includes a conjecture, theorem, proof, formalization, or a claim of new mathematics.

## Core separation

Keep these nine questions independent:

1. **Discovery context** — was the active atom understood across equivalent formulations, solved/near-solved analogues and witnessed method-transfer assumptions before candidate generation?
2. **Accumulated experience** — were relevant success-derived tools and prior failure experiences queried and scoped before choosing the next move?
3. **Semantic shortcut** — was the active relational obstruction searched against a content-bound obstruction–transformation memory in invention-last order?
4. **Research trace** — is there an auditable chronology of context, experience, shortcut routing, candidate selection, falsification and residuals?
5. **Specification** — does the formal statement mean what was intended?
6. **Truth** — is that exact statement proved from the registered assumptions?
7. **Verifier trust** — which checker, axioms, dependencies and artifact identities support the proof?
8. **Novelty** — is an equivalent or stronger prior result already known in the registered search world?
9. **Research value** — is the result interesting, general, explanatory or useful enough to pursue?

No scalar score may average these gates together. Discovery compliance does not make a theorem true, and theorem truth does not retroactively establish that strict RAKL discovery procedure was followed.

## Hard pre-candidate gates

After atomization and **before** the LLM may propose a proof idea, lemma, invariant, auxiliary construction or other mathematical candidate, four discovery gates must pass.

### Gate A — mathematical context fiber

Freeze a `MathContextFiber` conforming to `schemas/math-context-fiber.schema.json`. It must bind the exact atomic obstruction and record:

```text
load-bearing structural coordinates
equivalent formulations / representations
solved and near-solved analogues
methods that work in those source contexts
source-method enabling assumptions
shared structure
explicit disanalogies / broken assumptions
minimum repair questions
primary source anchors
cross-domain and everyday analogy scan
packet hash and pre-candidate chronology
```

For every retained analogy, record the common abstraction, source→target role mapping, shared constraints, disanalogies, candidate principle and a falsifiable target validation obligation. Surface resemblance is rejected. If no bridge survives, record `NO_SAFE_BRIDGE_FOUND` with the search boundary rather than forcing one.

A bibliography, paper list or generic survey is not a context fiber or method-transfer matrix.

### Gate B — dual research experience memory

Query both:

- the scoped success-derived `ResearchToolInventory`;
- the global `FailureExperienceLattice`.

Freeze a `ResearchMemoryReview` bound to the current atom/context and exact memory snapshot hashes. Record candidate method families searched, relevant tool/failure ids or explicit no-match status, tool applicability, failure reuse/scope warnings, unresolved warnings and evidence pointers.

`worked_once` never means `universally_valid`. A local failure is a warning, not a universal blacklist. Reusing a method with relevant failure history requires a scope/difference witness and a cheapest repeat-failure test. Only a verified impossibility may block reuse, and only inside its registered scope.

### Gate C — obstruction–transformation semantic shortcut

Compile or load a content-bound `ObstructionTransformationMemory` conforming to `schemas/obstruction-transformation-memory.schema.json`. Its reusable object is a scoped episode:

```text
relational obstruction O
  -- transformation T with explicit preconditions -->
changed relation/state O'
```

The memory binds its declared source universe, episode contents, evidence pointers and snapshot hash. An asserted episode id that is absent from that snapshot is not a match. Proposal-only or superseded source episodes may guide exploration but cannot become strict viable routes.

Then freeze an `ObstructionTransformationReview` conforming to `schemas/obstruction-transformation-review.schema.json`, bound to the active atom, context hash, dual-memory review hash and exact transformation-memory snapshot.

The central question is:

> **Has this relational obstruction — and a transformation that breaks it — occurred anywhere in recorded knowledge?**

Construct an `ObstructionFingerprint` using domain-light coordinates:

```text
roles
relations
constraints
failure mechanisms
invariants to preserve
desired transition
forbidden losses
```

Rank source episodes using obstruction morphology and the transformation's **recorded effects**, not topic vocabulary or the source problem's intended goal. Then route in strict invention-last order:

1. **SEARCH** — use a same-domain episode only if its source event has sufficient authority, every enabling source precondition is mapped or repaired, forbidden target invariants are preserved, disanalogies are explicit and target-validation obligations are frozen.
2. **JUMP** — if no direct route survives, use a cross-domain episode only with a `StructuralMappingWitness` covering roles, shared relations/constraints, complete source-precondition accounting, material disanalogies and target validation.
3. **GLUE** — if no single episode closes the obstruction, compose partial transformations only when their recorded effects jointly cover the target transition and a `TransformationCompositionWitness` binds operation order, interfaces, incompatibility checks and target validation.
4. **LIFT** — only if SEARCH, JUMP and GLUE are each `NO_VIABLE_MATCH` inside a recorded bounded search, all retrieved candidates are explicitly accounted for, a cross-problem coverage receipt binds the no-match claim, and at least two distinct failed attempts share residual structure. LIFT emits a `MissingTransformationSpecification` stating what a new representation/operator must preserve, break, expose, reduce and validate.
5. **CANNOT_CHECK** — when memory identity, mapping, coverage, composition or residual evidence is insufficient.

A source event can be valid while its transfer is invalid. Source authority never becomes target authority automatically. A single failed proof, a local retrieval miss, embedding similarity or a desire for novelty never establishes the need for LIFT.

`MissingTransformationSpecification` is an inverse-invention target, not a theorem, tool or method-promotion certificate.

### Gate D — public research trace

Freeze and append a trace conforming to `schemas/math-research-trace.schema.json`. Before candidate generation, the active atom must contain, in order:

1. `ATOMIZED`
2. `CONTEXT_FROZEN`
3. `ANALOGY_SCAN`
4. `METHOD_TRANSFER_REVIEW`
5. `EXPERT_CONTEXT_REVIEW`
6. `EXPERIENCE_MEMORY_REVIEW`
7. `OBSTRUCTION_TRANSFORMATION_REVIEW`
8. `NEXT_STEP_PROPOSED`

`OBSTRUCTION_TRANSFORMATION_REVIEW` must bind the obstruction fingerprint, exact transformation-memory snapshot, SEARCH/JUMP/GLUE/LIFT statuses, mapping/composition/exhaustion witnesses, selected route, validation obligations and shortcut-review artifact hash.

The expert cell must cover at least domain/theory, analogy/method transfer, adversarial falsification, formal methods/verifier trust, and novelty/research value. These are same-context role-separated passes, not independent peer review.

Trace entries are hash-chained: except for the first event, `previous_event_hash` equals the preceding event's `artifact_hash`. The trace is a reproducible public scientific decision record, not a raw private chain-of-thought transcript.

For strict mathematical discovery call:

```text
plan_math_research(...,
    context_fiber=...,
    memory_review=...,
    transformation_memory=...,
    shortcut_review=...,
    research_trace=...,
    preservation_receipt=...,
    expected_preservation_sha256=...)
```

If `candidate_generation_allowed` is false, execute only `pre_candidate_actions`. Do not bypass a gate by calling lower-level candidate operators or by generating a candidate first and backfilling context, memory, transformation memory, shortcut review or trace later.

## Procedure

1. Freeze the informal target, assumptions, notation, scope, success criteria and failure conditions. Open `PROBLEM_FROZEN` when applicable.
2. Compile a `ProblemSignature` and decompose the program into a persistent DAG of conjectures, lemmas, definitions, computations, representations and unresolved obligations.
3. Select the smallest active atomic obstruction whose resolution changes the proof DAG. Record `ATOMIZED`.
4. Build and freeze the atom's context fiber.
5. Search multiple vocabularies/disciplines for solved and near-solved structural contexts. Extract methods and enabling assumptions, not paper summaries.
6. Run the cross-domain/everyday analogy scan and reject surface-only matches.
7. Build the method-transfer matrix and minimum repair questions.
8. Record `CONTEXT_FROZEN`, `ANALOGY_SCAN` and `METHOD_TRANSFER_REVIEW` before any candidate.
9. Run the same-context expert cell and record `EXPERT_CONTEXT_REVIEW`.
10. Query the success-tool inventory and check actual applicability.
11. Query the failure lattice; when reusing a warned method, record a `DifferenceWitness` and regression test.
12. Freeze `ResearchMemoryReview` and record `EXPERIENCE_MEMORY_REVIEW`.
13. Build the active `ObstructionFingerprint`.
14. Compile/load the content-bound `ObstructionTransformationMemory` for the registered source universe; bind its snapshot hash.
15. Query same-domain episodes by obstruction morphology and recorded transformation effects. Reject episodes with insufficient source authority, forbidden losses or unrepaired preconditions.
16. If a viable direct episode survives, select `SEARCH` and freeze its target mapping/validation witness.
17. Otherwise test cross-domain candidates and select `JUMP` only with complete `StructuralMappingWitness` objects.
18. If no single JUMP survives, test effect-covering partial compositions and select `GLUE` only with mapped components plus an explicit composition/interface witness.
19. Enter `LIFT` only after SEARCH/JUMP/GLUE are boundedly exhausted. Bind the cross-problem coverage receipt, account for every retrieved candidate, require repeated residual structure across at least two distinct failures, and freeze the `MissingTransformationSpecification` before downstream invention.
20. Freeze `ObstructionTransformationReview` and record `OBSTRUCTION_TRANSFORMATION_REVIEW`.
21. Record `NEXT_STEP_PROPOSED` with alternatives, bounded rationale, warnings and expected discriminator.
22. Pass `audit_math_context_fiber`, `audit_research_memory_review`, `audit_obstruction_transformation_review`, `audit_pre_candidate_trace` and `plan_math_research`.
23. Only after all gates pass, use LLMs or other generators to propose proof ideas, lemmas, representations, auxiliary objects and actions. Every candidate points to the structural/evidence object that motivated it. Record `CANDIDATE_PROPOSED`.
24. Run a counterexample-first/falsifier pass before expensive proof search. Record `FALSIFIER_RUN` and `RESULT_RECORDED`.
25. On failure, preserve the exact failure, record `RESIDUAL_OPENED`, update the failure lattice, and reopen context/shortcut search if a new structural coordinate, transfer mismatch or repeated residual appears.
26. On success, update the proof DAG at the exact authority achieved. A genuinely reusable operation may become a scoped `ResearchTool`; a validated structural transition may separately become an `ObstructionTransformationEpisode`. Neither promotion is automatic.
27. Formalize the candidate and bind informal/formal statement hashes with a `FormalizationWitness`. Record `FORMALIZED`.
28. Check specification alignment, boundary cases, assumptions, quantifier order and domains.
29. Search for a proof in a proof-producing system. Material failed proof attempts remain negative history.
30. Bind every accepted proof to the exact statement and checker in a `ProofReceipt`; record `PROOF_CHECKED` only at achieved authority.
31. Audit transitive proof dependencies and isolated recheck where supported.
32. Only after truth assurance, search notation-normalized and structural prior art; record bounded `NOVELTY_CHECKED` evidence.
33. Evaluate research value separately, then run same-context consistency and genuinely isolated review where required.
34. Promote to `NEW_MATHEMATICS_CANDIDATE` only when specification, truth/verifier, bounded novelty and research-value gates all pass. Strict RAKL-mediated discovery additionally requires all four pre-candidate process gates and chronology.
35. Release context, dual-memory review, transformation-memory snapshot, shortcut review, research trace, relevant tool/failure/episode records, proof artifact, dependency audit, checker identities, novelty world and negative-history summary.

## LIFT and mechanism invention

If a valid shortcut review selects `LIFT`, the downstream mechanism/formalism-invention workflow receives the frozen `MissingTransformationSpecification` as its construction contract. Candidate representations/operators must address its:

```text
must_preserve
must_break
must_expose
must_reduce
allowed representation changes
forbidden shortcuts
validation obligations
falsifiers
```

The invention workflow may use composition/recombination, auxiliary/latent objects, coordinate or representation changes, regime splitting, coarse/fine graining, invariants, symmetry changes, nonlinearization, feedback/coupling changes and other typed moves—but it may not silently weaken the LIFT specification after seeing outcomes.

## Long-horizon memory

Maintain five complementary planes:

```text
knowledge/proof DAG                 -> what is known / open
scoped tool inventory               -> what has worked, under what conditions
failure experience lattice          -> what failed, why, scope and repairs
obstruction-transformation memory   -> where structural obstructions changed and by what operations
public research trace               -> how state changed over time
```

The transformation memory is a structural retrieval projection, not a truth-authority store. Its source episode and authority remain explicit, and every target transport requires a target witness and validation.

The cumulative loop is:

```text
SEARCH / JUMP / GLUE
        |
        v
candidate + target validation
   |                 |
 failure           success
   |                 |
 failure lattice    scoped tool + episode candidates
   |                 |
   +-------> future obstruction search <------+
                     |
               persistent residuals
                     |
                    LIFT
                     |
       missing-transform specification
                     |
           typed invention + validation
```

`src/rakl/metacognition.py` remains above these memories. Repeated residuals can motivate a missing-transformation specification, but only supported failure attribution may establish a true ontology/method-basis gap.

## Required questions before every candidate

> What exact atomic obstruction is active?
>
> What structural context and equivalent formulations are frozen?
>
> Which solved/near-solved contexts and analogies share the structure, and which enabling assumptions differ?
>
> What success tools and prior failures are relevant, and are their scopes applicable?
>
> **Has this relational obstruction — and a transformation that breaks it — occurred anywhere in recorded knowledge?**
>
> Which transformation-memory snapshot was actually searched?
>
> Which route is justified: SEARCH, JUMP, GLUE, LIFT or CANNOT_CHECK?
>
> For SEARCH/JUMP, are all source preconditions accounted for and what disanalogy can kill the transfer?
>
> For GLUE, do recorded effects cover the target and what interface/order obligations make composition valid?
>
> For LIFT, what bounded coverage shows prior routes were exhausted, which retrieved candidates were rejected and why, which residual feature repeats, and what exactly must the missing transformation preserve/break/expose/reduce?
>
> What did each expert lens object to?
>
> What result would falsify or discriminate the selected next action?
>
> Were context, dual memory, transformation memory, shortcut review and hash-chained trace frozen before candidate generation?

If these are not answered in frozen artifacts, strict candidate generation is blocked.

## Failure rules

- missing/incomplete context, dual-memory review, transformation memory, shortcut review or research trace blocks candidate generation;
- an asserted episode id is not a memory match;
- lexical/embedding similarity is not a structural mapping witness;
- source validity does not imply target applicability;
- an unrepaired source precondition blocks strict SEARCH/JUMP transport;
- a transformation that sacrifices a target-forbidden invariant is not viable;
- JUMP may not bypass a viable SEARCH route;
- GLUE without effect coverage plus ordering/interface obligations is invalid;
- one failed candidate never establishes the need for LIFT;
- a local empty search cannot support a recorded-knowledge no-match claim;
- LIFT must bind cross-problem coverage and account for retrieved candidates it rejects;
- repeated failures without a repeated residual feature do not define a coherent missing-transformation specification;
- a LIFT specification is proposal-only and cannot mint proof or method authority;
- a successful local operation is not a universal tool;
- a failed local operation is not a universal blacklist;
- finite tests never become proof;
- planning completion never becomes problem closure;
- machine proof never implies novelty;
- resource exhaustion is nonterminal.

## Executable reference surfaces

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
src/rakl/memory_coverage.py
schemas/math-context-fiber.schema.json
schemas/research-tool-inventory.schema.json
schemas/failure-experience-lattice.schema.json
schemas/research-memory-review.schema.json
schemas/obstruction-transformation-memory.schema.json
schemas/obstruction-transformation-review.schema.json
schemas/math-research-trace.schema.json
docs/RESEARCH_MEMORY_ARCHITECTURE.md
docs/SEMANTIC_SHORTCUT_ROUTER.md
```
