# Workflow — Mathematical Research

Use when the target includes a conjecture, theorem, proof, formalization, or a claim of new mathematics.

## Core separation

Keep six questions independent:

1. **Discovery context** — was the active atom understood across equivalent formulations, solved/near-solved analogues and witnessed method-transfer assumptions before candidate generation?
2. **Specification** — does the formal statement mean what the researcher intended?
3. **Truth** — is that exact formal statement proved from the registered assumptions?
4. **Verifier trust** — what checker, axioms, dependencies and artifact identities does the truth claim rely on?
5. **Novelty** — is an equivalent or stronger prior result already known in the registered literature world?
6. **Research value** — is the result interesting, general, explanatory, or useful enough to pursue or publish?

No score may average these gates together. Discovery-process compliance does not make a theorem true; theorem truth does not retroactively establish that strict RAKL discovery procedure was followed.

## Hard pre-candidate gate

After atomization and **before** the LLM may propose a proof idea, lemma, invariant, auxiliary construction or other mathematical candidate, freeze a `MathContextFiber` conforming to `schemas/math-context-fiber.schema.json`.

The packet must contain:

1. the exact atomic obstruction and object context;
2. structural coordinates that matter for the obstruction;
3. equivalent formulations/representations;
4. at least one solved or near-solved analogue;
5. a method-transfer matrix;
6. for every transferred method, its required assumptions and source anchors;
7. the exact shared structure between analogue and target;
8. explicit disanalogies/broken assumptions;
9. the smallest repair question exposed by the mismatch;
10. a packet hash and chronology showing the packet was frozen before the first candidate.

A bibliography, paper list, or generic survey does not pass this gate. "This problem resembles X" does not pass. A transfer is witnessed only when the method, its enabling assumptions, the shared structure, the disanalogy and the repair question are all explicit.

Call `plan_math_research(..., context_fiber=...)`. If `candidate_generation_allowed` is false, execute only `pre_candidate_actions`. Do not directly call lower-level candidate operators to bypass the gate. Do not write a candidate and backfill the context packet afterward.

## Procedure

1. Freeze the informal research target, assumptions, notation, scope, success criteria and failure conditions.
2. Compile a `ProblemSignature` and decompose the research program into a persistent DAG of conjectures, lemmas, definitions, counterexamples, computations, representations and unresolved proof obligations.
3. Select the smallest active atomic obstruction whose resolution would change the proof DAG or eliminate a material route.
4. Build the atom's context fiber. Map structural coordinates and equivalent formulations before proposing a solution.
5. Search multiple vocabularies/disciplines for solved and near-solved contexts with matching structure. Extract methods and enabling assumptions, not paper summaries.
6. Build the method-transfer matrix. For each analogue, record shared structure, broken assumptions/disanalogies and the minimum repair question needed for transfer.
7. Freeze/hash the context packet before candidate generation and pass `audit_math_context_fiber` / `plan_math_research`.
8. Only after the context gate passes, use LLMs as proposal generators for conjectures, proof ideas, lemmas, representations, auxiliary objects and search actions. Each candidate must point to the context-transfer row or residual that motivated it; ungrounded candidate invention is rejected as search drift.
9. Compile the current assurance state into explicit obstructions with `plan_math_research`; use obstruction-guided operator paths as candidate research routes, not as truth authority.
10. Run a **counterexample-first pass** before expensive proof search: exact finite enumeration where possible, randomized/property testing, CAS/SMT/SAT/model finding, boundary and degenerate cases. Failure to find a counterexample is evidence for search prioritization only; it is never proof.
11. If a candidate fails, preserve the failure and classify the residual. Update the context fiber when the failure reveals a new structural coordinate, disanalogy, method limitation or equivalent formulation. Do not blindly generate another proof from the same unchanged context packet.
12. Formalize the candidate statement. Bind the informal claim and formal statement with hashes and an explicit `FormalizationWitness`.
13. Check the formalization by round-trip paraphrase, positive/negative examples, boundary cases, assumptions, quantifier order, domains, and at least one independent review for a new-mathematics claim.
14. Search for a proof in a theorem prover or other proof-producing system. Treat every failed proof attempt as negative history rather than deleting it.
15. For any accepted theorem, record a `ProofReceipt` bound to the exact formal statement and source hash.
16. Audit all transitive proof dependencies. Finished strict-profile results must not depend on `sorryAx`; unregistered custom axioms are rejected, and compiler/native trust is rejected when independent kernel-level assurance is required.
17. Recheck generated proof artifacts in an isolated independent checker where the proof ecosystem supports it. Pin checker versions and dependency identities.
18. Only after truth assurance, open the novelty fiber. Build a notation-normalized and structure-aware theorem fingerprint; search multiple literature corpora, terminology variants, citation neighborhoods, translations, structural equivalents and known stronger parent theorems.
19. Record novelty only as a **bounded, cutoff-scoped certificate**. A later prior-art hit may demote novelty without demoting proof validity.
20. Evaluate research value separately: generality, compression, explanatory power, connection to open problems, nontriviality, downstream consequences, new representation/invariant/technique and expert interest.
21. Promote to `NEW_MATHEMATICS_CANDIDATE` only when specification alignment, proof assurance, verifier-trust audit, bounded novelty, and research-value review all pass. If claiming strict RAKL-mediated discovery, the pre-candidate context chronology must also be preserved.
22. Release the context fiber, theorem statement, proof artifact, dependency/axiom audit, checker identities, corpus cutoff, novelty search routes, structural fingerprint/equivalence policy and negative-history summary.

The executable reference surfaces are:

```text
src/rakl/math_context.py
src/rakl/problem_solving_algebra.py
src/rakl/math_research_runtime.py
src/rakl/math_research_assurance.py
schemas/math-context-fiber.schema.json
benchmarks/math_research_assurance/tasks_v0.json
docs/MATH_RESEARCH_QUICKSTART.md
```

## Long-horizon rule

Do not store mathematical research as one long natural-language transcript. Every verified lemma is a persistent checkpoint in the proof DAG. Every active atom has a versioned context fiber. Generator mistakes should increase search cost or create rejected branches; they must not accumulate as hidden logical debt inside an accepted theorem. Planning operators may modify candidate states, but only verified certificates/receipts can mint terminal or theorem authority.

When several candidates fail for the same structural reason, do not ask for another unconstrained proof. Promote that repeated residual into a new context atom and search solved sibling contexts for methods that specifically handle the missing structure.

## Required questions before every candidate

> What exact atomic obstruction is active?
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
> What is the minimum repair question created by that failure?
>
> Was this context packet frozen before the candidate was generated?

If these questions are not answered in a frozen packet, candidate generation is blocked.

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
- `candidate_generated_before_context_freeze` is a chronology failure. The candidate may be evaluated for truth, but it is not a strict context-first RAKL discovery artifact.
- `literature_list_present` is not equivalent to `method_transfer_mapped`.
- `analogy_found` is not equivalent to `method_transfer_valid`; assumptions and disanalogies must be explicit.
- repeated failure under an unchanged context packet triggers context reopening rather than unlimited same-basis candidate generation.
- `tested_many_cases` is never promoted to `proved`.
- `candidate_path_completed` is never promoted to `problem_closed` without a verified terminal certificate.
- `machine_proven` is never promoted to `novel` without a novelty certificate.
- `no_prior_art_found` is never represented as globally complete novelty.
- `interesting` cannot compensate for an unproved theorem.
- `proof_found` cannot compensate for a specification mismatch or failed verifier-trust audit.
- resource exhaustion is a nonterminal block, not evidence that a conjecture is false.
