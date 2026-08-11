# Real-math strict assurance profile

This profile specializes `docs/MATHEMATICAL_RESEARCH_ASSURANCE.md` and the `mathematical-research` RAKL workflow for famous open problems.

## Pre-candidate discovery gates

For every **new** mathematical candidate created under this profile, the active atomic obstruction must first pass both discovery-process gates.

### Gate A — context and transfer

Freeze a `MathContextFiber` satisfying `schemas/math-context-fiber.schema.json` and `audit_math_context_fiber`.

The context packet must precede candidate generation and contain the atom's structural coordinates, equivalent formulations, solved/near-solved analogous contexts, method-transfer assumptions, shared structure, explicit disanalogies, repair questions, source anchors, cross-domain/everyday analogy scan and content hash.

Every retained cross-domain analogy must have an explicit abstraction and role mapping, shared constraints, disanalogies and a falsifiable mathematical validation obligation. An attractive everyday story is proposal material only.

### Gate B — auditable research trace

Freeze/append a `MathResearchTrace` satisfying `schemas/math-research-trace.schema.json` and `audit_pre_candidate_trace`.

Before the first candidate for an atom, the trace must record `ATOMIZED`, `CONTEXT_FROZEN`, `ANALOGY_SCAN`, `METHOD_TRANSFER_REVIEW` and `NEXT_STEP_PROPOSED` in chronological order. The next-step entry must record alternatives considered, a concise evidence-grounded selection rationale, uncertainty and expected discriminator.

A paper list, generic literature summary, after-the-fact explanation or reconstructed narrative does not pass these gates. If `plan_math_research(..., context_fiber=..., research_trace=...)` reports `candidate_generation_allowed: false`, only `pre_candidate_actions` may be executed.

The public trace is a reproducible scientific decision ledger, not a raw private chain-of-thought transcript.

### No retroactive grandfathering

Candidates and negative checkpoints created before these gates existed remain valid historical research artifacts at their already recorded authority levels. They must **not** be relabeled as strict context-first discoveries by backfilling packets or trace events after the fact.

After these gates are merged, any materially new successor candidate must begin from a freshly frozen context fiber and trace. Existing residuals may be reused as the atomic obstruction, but the analogue/method-transfer/analogy analysis, decision record and chronology must be newly frozen before the successor candidate is generated.

## Non-compensatory gates

1. **Discovery-process compliance**. If the work is claimed as strict RAKL-mediated discovery, the pre-candidate context, analogy and trace chronology must pass. This gate does not substitute for mathematical truth.
2. **Specification**. The exact mathematical claim must be frozen and round-trip checked.
3. **Truth**. Every proof-critical edge must be justified from registered premises.
4. **Verifier trust**. Proof checker, versions, dependencies, axioms, source hashes, and isolated recheck are explicit.
5. **Novelty**. Truth does not imply novelty. Prior-art equivalence and stronger-parent searches are separate.
6. **Research value**. Novelty does not imply importance.

No aggregate score can compensate for failure of one gate.

## Root-solution gate

A Millennium-scale root claim may advance to `CANDIDATE_ROOT_SOLUTION` only if all of the following are true.

- If the root candidate is generated after adoption of these gates, its exact parent obstruction has a pre-candidate context packet and auditable trace with valid chronology.
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

- `CONTEXT_BLOCKED`
- `TRACE_BLOCKED`
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
