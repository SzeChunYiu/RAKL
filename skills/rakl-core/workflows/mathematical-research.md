# Workflow — Mathematical Research

Use when the target includes a conjecture, theorem, proof, formalization, or a claim of new mathematics.

## Core separation

Keep four questions independent:

1. **Truth** — is the formal statement proved?
2. **Specification** — does the formal statement mean what the researcher intended?
3. **Novelty** — is an equivalent result already known in the registered literature world?
4. **Research value** — is the result interesting, general, explanatory, or useful enough to pursue or publish?

No score may average these gates together.

## Procedure

1. Freeze the informal research target, assumptions, notation, scope, and failure conditions.
2. Decompose the research program into a persistent DAG of conjectures, lemmas, definitions, counterexamples, computations, and unresolved proof obligations.
3. Use LLMs only as proposal generators for conjectures, proof ideas, lemmas, representations, and search actions.
4. Run a **counterexample-first pass** before expensive proof search: exact finite enumeration where possible, randomized/property testing, CAS/SMT/SAT/model finding, boundary and degenerate cases. Failure to find a counterexample is evidence for search prioritization only; it is never proof.
5. Formalize the candidate statement. Bind the informal claim and formal statement with hashes and an explicit `FormalizationWitness`.
6. Check the formalization by round-trip paraphrase, positive/negative examples, boundary cases, assumptions, quantifier order, domains, and at least one independent review for a new-mathematics claim.
7. Search for a proof in a theorem prover or other proof-producing system. Treat every failed proof attempt as negative history rather than deleting it.
8. For any accepted theorem, record a `ProofReceipt` bound to the exact formal statement and source hash.
9. Audit all transitive proof dependencies. Finished results must not depend on `sorryAx`; the strict profile also rejects unregistered custom axioms and compiler/native trust when independent kernel-level checking is required.
10. Recheck generated proof artifacts in an isolated independent checker where the proof ecosystem supports it. Pin checker versions and dependency identities.
11. Only after truth assurance, open the novelty fiber. Build a notation-normalized and structure-aware theorem fingerprint; search multiple literature corpora, terminology variants, citation neighborhoods, translations, and known stronger parent theorems.
12. Record novelty only as a **bounded, cutoff-scoped certificate**. A later prior-art hit may demote novelty without demoting proof validity.
13. Evaluate research value separately: generality, compression, explanatory power, connection to open problems, nontriviality, downstream consequences, and expert interest.
14. Promote to `NEW_MATHEMATICS_CANDIDATE` only when specification alignment, proof assurance, bounded novelty, and research-value review all pass.
15. Release the theorem statement, proof artifact, dependency/axiom audit, checker identities, corpus cutoff, novelty search routes, and negative-history summary.

## Long-horizon rule

Do not store mathematical research as one long natural-language transcript. Every verified lemma is a persistent checkpoint in the proof DAG. Generator mistakes should increase search cost or create rejected branches; they must not accumulate as hidden logical debt inside an accepted theorem.

## Required questions at every proof edge

> What exact proposition is being claimed here?
>
> What premises and axioms does it depend on?
>
> Can this edge be refuted cheaply before we spend proof-search budget?
>
> If the formal checker accepts it, have we also checked that the formal statement matches the intended mathematics?

## Failure rules

- `tested_many_cases` is never promoted to `proved`.
- `machine_proven` is never promoted to `novel` without a novelty certificate.
- `no_prior_art_found` is never represented as globally complete novelty.
- `interesting` cannot compensate for an unproved theorem.
- `proof_found` cannot compensate for a specification mismatch.
- resource exhaustion is a nonterminal block, not evidence that a conjecture is false.
