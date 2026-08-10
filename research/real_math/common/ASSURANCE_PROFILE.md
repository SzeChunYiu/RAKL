# Real-math strict assurance profile

This profile specializes `docs/MATHEMATICAL_RESEARCH_ASSURANCE.md` and the `mathematical-research` RAKL workflow for famous open problems.

## Non-compensatory gates

1. **Specification**. The exact mathematical claim must be frozen and round-trip checked.
2. **Truth**. Every proof-critical edge must be justified from registered premises.
3. **Verifier trust**. Proof checker, versions, dependencies, axioms, source hashes, and isolated recheck are explicit.
4. **Novelty**. Truth does not imply novelty. Prior-art equivalence and stronger-parent searches are separate.
5. **Research value**. Novelty does not imply importance.

No aggregate score can compensate for failure of one gate.

## Root-solution gate

A Millennium-scale root claim may advance to `CANDIDATE_ROOT_SOLUTION` only if all of the following are true.

- The root statement is exactly the intended problem, not a stronger/weaker neighboring statement accidentally substituted without disclosure.
- The proof DAG closes every dependency from axioms/registered parent theorems to the root.
- No `sorryAx`, placeholder, unregistered custom axiom, unchecked numerical leap, hidden oracle, or unstated regularity/complexity assumption occurs transitively.
- Every generated formal proof is rechecked in an isolated verifier context when the ecosystem permits it.
- Every non-formalized proof edge has an explicit conversion obligation. Until conversion, the root remains unproved.
- Barrier checks relevant to the problem are recorded. Passing a proof checker does not establish that the informal root was correctly encoded.
- Three independent or genuinely isolated mathematical review reports are frozen before synthesis.
- A bounded novelty search is complete enough to rule out obvious rediscovery or proof of a known neighboring result.

## Allowed intermediate authority

The program may retain useful states below root closure.

- `CONJECTURE`
- `COMPUTATIONALLY_SUPPORTED`
- `REFUTED`
- `FORMALIZED_UNPROVEN`
- `VERIFIED_LEMMA`
- `MACHINE_PROVEN_NOVELTY_UNRESOLVED`
- `VERIFIED_REDISCOVERY`
- `BOUNDED_NOVEL_RESULT`
- `NEW_MATHEMATICS_CANDIDATE`

Resource exhaustion is nonterminal. It does not count as evidence for or against the root conjecture.
