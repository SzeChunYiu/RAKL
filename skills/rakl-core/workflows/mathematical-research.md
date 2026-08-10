# Workflow — Mathematical Research

Use when the target includes a conjecture, theorem, proof, formalization, or a claim of new mathematics.

## Core separation

Keep five questions independent:

1. **Specification** — does the formal statement mean what the researcher intended?
2. **Truth** — is that exact formal statement proved from the registered assumptions?
3. **Verifier trust** — what checker, axioms, dependencies and artifact identities does the truth claim rely on?
4. **Novelty** — is an equivalent or stronger prior result already known in the registered literature world?
5. **Research value** — is the result interesting, general, explanatory, or useful enough to pursue or publish?

No score may average these gates together.

## Procedure

1. Freeze the informal research target, assumptions, notation, scope, and failure conditions.
2. Compile a `ProblemSignature` and decompose the research program into a persistent DAG of conjectures, lemmas, definitions, counterexamples, computations, representations and unresolved proof obligations.
3. Use LLMs only as proposal generators for conjectures, proof ideas, lemmas, representations, auxiliary objects and search actions.
4. Compile the current assurance state into explicit obstructions with `plan_math_research`; use obstruction-guided operator paths as candidate research routes, not as truth authority.
5. Run a **counterexample-first pass** before expensive proof search: exact finite enumeration where possible, randomized/property testing, CAS/SMT/SAT/model finding, boundary and degenerate cases. Failure to find a counterexample is evidence for search prioritization only; it is never proof.
6. Formalize the candidate statement. Bind the informal claim and formal statement with hashes and an explicit `FormalizationWitness`.
7. Check the formalization by round-trip paraphrase, positive/negative examples, boundary cases, assumptions, quantifier order, domains, and at least one independent review for a new-mathematics claim.
8. Search for a proof in a theorem prover or other proof-producing system. Treat every failed proof attempt as negative history rather than deleting it.
9. For any accepted theorem, record a `ProofReceipt` bound to the exact formal statement and source hash.
10. Audit all transitive proof dependencies. Finished strict-profile results must not depend on `sorryAx`; unregistered custom axioms are rejected, and compiler/native trust is rejected when independent kernel-level assurance is required.
11. Recheck generated proof artifacts in an isolated independent checker where the proof ecosystem supports it. Pin checker versions and dependency identities.
12. Only after truth assurance, open the novelty fiber. Build a notation-normalized and structure-aware theorem fingerprint; search multiple literature corpora, terminology variants, citation neighborhoods, translations, structural equivalents and known stronger parent theorems.
13. Record novelty only as a **bounded, cutoff-scoped certificate**. A later prior-art hit may demote novelty without demoting proof validity.
14. Evaluate research value separately: generality, compression, explanatory power, connection to open problems, nontriviality, downstream consequences, new representation/invariant/technique and expert interest.
15. Promote to `NEW_MATHEMATICS_CANDIDATE` only when specification alignment, proof assurance, verifier-trust audit, bounded novelty, and research-value review all pass.
16. Release the theorem statement, proof artifact, dependency/axiom audit, checker identities, corpus cutoff, novelty search routes, structural fingerprint/equivalence policy and negative-history summary.

The executable reference surfaces are:

```text
src/rakl/problem_solving_algebra.py
src/rakl/math_research_runtime.py
src/rakl/math_research_assurance.py
benchmarks/math_research_assurance/tasks_v0.json
docs/MATH_RESEARCH_QUICKSTART.md
```

## Long-horizon rule

Do not store mathematical research as one long natural-language transcript. Every verified lemma is a persistent checkpoint in the proof DAG. Generator mistakes should increase search cost or create rejected branches; they must not accumulate as hidden logical debt inside an accepted theorem. Planning operators may modify candidate states, but only verified certificates/receipts can mint terminal or theorem authority.

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

- `tested_many_cases` is never promoted to `proved`.
- `candidate_path_completed` is never promoted to `problem_closed` without a verified terminal certificate.
- `machine_proven` is never promoted to `novel` without a novelty certificate.
- `no_prior_art_found` is never represented as globally complete novelty.
- `interesting` cannot compensate for an unproved theorem.
- `proof_found` cannot compensate for a specification mismatch or failed verifier-trust audit.
- resource exhaustion is a nonterminal block, not evidence that a conjecture is false.
