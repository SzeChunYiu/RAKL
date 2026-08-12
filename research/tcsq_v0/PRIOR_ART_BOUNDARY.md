# TCSQ v0 prior-art boundary

## Functions that are prior art

TCSQ does **not** claim novelty for the following functions in isolation:

1. **Task-relevant compression / sufficient representations.** The information-bottleneck literature formalizes compression while retaining information relevant to a target variable.
2. **Decision/action/value sufficient state abstraction.** Reinforcement-learning and control literature studies state abstractions that retain decision-relevant information and bound value loss.
3. **Decision-sufficient data representations.** Recent optimization work studies compressed representations sufficient to recover optimal decisions.
4. **Program/model abstraction and refinement.** Abstract interpretation, program slicing/cone-of-influence reduction and CEGAR remove irrelevant state while using correctness obligations or counterexamples to refine abstractions.
5. **Prompt/context compression.** LLMLingua-family methods and related systems delete or compress context while optimizing downstream LLM faithfulness/performance.
6. **Verifiable context compression.** Context Codec (2026) already uses source-grounded semantic atoms, protected commitments, verification metrics, round-trip recoverability and conservative fallback for low-confidence/safety-critical content. TCSQ therefore cannot claim novelty merely for an auditable compression ledger, protected information, verification or fallback.
7. **Learned program slicing.** SLICEFORMER (ACL 2026) learns static program slices with dataflow-aware representations and constrained decoding. Removing irrelevant program state with a learned model is not a TCSQ novelty.
8. **State-aware reasoning compression.** STACK (ACL Findings 2026) compresses reasoning by using state/knowledge signals to remove redundant computation. Fewer explicit reasoning tokens or state-aware compression is not a TCSQ novelty.
9. **Latent/internal reasoning.** Hidden-state or latent-reasoning systems may reduce explicit tokenized reasoning without exposing a symbolic quotient.
10. **Generic structural abstraction.** Graph abstractions, equivalence classes, bisimulation and mechanism/relational representations predate RAKL.

## Candidate residual

The research residual worth testing is narrower than generic verifiable compression:

> A scientific-problem/QoI/context-conditioned **structural quotient** inside an evidence-governed research-agent substrate, with an explicit equivalence/erasure contract, complete preserved/erased/conditional ledger, protected coordinates and forbidden losses, content-bound solver-sufficiency obligations and falsifiers, immutable canonical-source lineage, fail-closed `CANNOT_CHECK`, direct integration with problem-fibre retrieval and directional transfer witnesses, explicit reconstruction bindings, mandatory verification on the exact original problem, and representation-level scientific-authority non-escalation.

The load-bearing distinctions from a general context codec are therefore:
- the object being reduced is a problem representation for a registered scientific QoI/context, not arbitrary dialogue/memory context;
- quotient validity means solver-side decision/solution sufficiency under a declared equivalence/erasure contract, not only preservation of textual commitments;
- the validated quotient feeds RAKL's structural retrieval and directional `JUMP`/`GLUE` transfer machinery;
- quotient-side success is insufficient until bindings are reconstructed and the untouched original-problem verifier passes;
- computational erasure cannot mint, revoke or upgrade scientific authority.

No listed parent is treated as absent merely because it uses different terminology. The empirical programme must compare functions, not names.

## Strongest comparator classes required at SQ-3+

- raw/full problem representation;
- structured representation with no erasure;
- generic prompt/context compression under matched context budget;
- Context-Codec-style verifiable/commitment-preserving compression where a faithful implementation is feasible;
- task-sufficient/state-abstraction baseline where the domain supports one;
- exact/program-slicing or cone-of-influence baseline where available;
- state-aware reasoning-compression baseline when the endpoint is a reasoning trace rather than a static problem object;
- mechanism/relational abstraction without the TCSQ governance ledger;
- incumbent RAKL structural routing without quotienting;
- full TCSQ;
- oracle quotient upper bound.

A top-tier experiment cannot claim a structural-quotient residual merely by beating lexical/semantic compression.

## Novelty kill criteria

Narrow or remove the TCSQ novelty claim if any of the following is established:

- Context Codec or another closest parent already has the same problem-QoI structural equivalence + solver-sufficiency + original-verification + directional-transfer + authority contract;
- a formal slice/state abstraction makes the same decisions at equal or lower total cost, leaving the additional governance fields semantically inert;
- the only gain is fewer prompt tokens under an unmatched resource budget;
- generic/verifiable compression, structure-only, or mechanism-alignment controls match full TCSQ after cost matching;
- quotient success depends on information manually supplied from hidden outcomes in a way unavailable to comparators;
- original-problem verification adds no residual because the comparator already enforces the same source-bound end-to-end certificate.

## Primary sources already added to Paper II

- Tishby, Pereira & Bialek — information bottleneck.
- Huang et al. — action-sufficient state representation learning.
- Abel et al. — value-preserving state-action abstractions.
- Ye, Amin & Ozdaglar — decision-sufficient representations for linear optimization.
- Jiang et al. — LongLLMLingua prompt compression.
- Pan et al. — LLMLingua-2 faithful task-agnostic prompt compression.
- Clarke et al. — counterexample-guided abstraction refinement.
- Trukhina & Vashkelis — Context Codec / verifiable LLM context compression.
- He et al. — SLICEFORMER / learned static program slicing.
- Sui et al. — STACK / state-aware reasoning compression.
