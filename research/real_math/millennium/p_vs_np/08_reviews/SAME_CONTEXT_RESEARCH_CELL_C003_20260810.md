# C003 research-cell review

**Independence status:** SAME_CONTEXT_RESEARCH_CELL. This is multidisciplinary adversarial review inside one research run. It does **not** satisfy the isolated-review promotion gate.

## Frozen object

Candidate `C003_single_copy_wrapper_no_amplification.md` and its source-dependent MCSP corollary.

## Cell roles

### Cell A — complexity theorist

Background: Boolean circuit complexity, reductions, nonuniform complexity, hardness magnification.

- **Finding:** The structural lemma is valid under its explicit additive-overhead assumptions. If `CC(f_n)=2^(mu n+o(n))` with `mu>0`, additive `2^(o(n))` wrapper cost cannot alter the leading circuit-complexity exponent in the original `n` scale.
- **Strongest objection:** A useful MCSP transport need not be single-copy or restriction-recoverable, so C003 is route pruning, not a barrier to threshold transport in general.
- **Vote:** ACCEPT_AS_NEGATIVE_CHECKPOINT.

### Cell B — meta-complexity / MCSP specialist

Background: MCSP parameterization, truth-table input models, hardness magnification, oracle/locality barriers.

- **Finding:** The STACS 2021 source explicitly separates the small-threshold magnification theorem from a near-maximal-threshold lower bound and identifies the threshold parameter as the missing bridge. The streamable-wrapper corollary is aligned with that source when the simulation assumption is stated.
- **Strongest objection:** Streamability is transformation-specific. It must not be inferred from circuit-size preservation alone.
- **Resolution:** C003 states streamability as an additional hypothesis rather than part of the structural lemma.
- **Vote:** ACCEPT_WITH_SCOPE_GUARD.

### Cell C — adversarial proof reviewer

Background: counterexamples, quantifier audits, asymptotic edge cases, reduction-direction errors.

- **Finding:** The proof requires `mu>0`; at zero/subexponential circuit scale the dominance argument over `h(n)=2^(o(n))` can fail. The text correctly freezes `mu>0`.
- **Finding:** If restriction recovery adds more than constant/subexponential reconstruction cost, the lower squeeze must be changed. The current definition uses `O(1)` recovery.
- **Strongest objection:** The phrase "cannot create amplification" would be false without the single-copy and subexponential-overhead hypotheses.
- **Resolution:** Candidate title and body retain those hypotheses explicitly.
- **Vote:** ACCEPT_AS_SCOPED.

### Cell D — formal-methods lead

Background: theorem specification, proof assistants, dependency receipts, model/formal statement alignment.

- **Finding:** C003-L1 is an appropriate next formalization target because its proof is a short asymptotic squeeze with explicit premises.
- **Blocking gap:** No theorem-prover artifact exists yet. The `2^(mu n+o(n))` notation will require a precise sequence/asymptotic encoding before a strict proof receipt can be minted.
- **Vote:** BLOCK_PROMOTION_ABOVE_PROOF_DRAFT.

### Cell E — novelty and research-value lead

Background: literature normalization, stronger-parent search, route triage.

- **Finding:** The theorem may be folklore. No novelty claim should be made. Its present value is operational because it removes a broad class of wrappers from the search queue and forces the next route to confront multi-copy sharing/direct-sum behavior.
- **Primary-source context:** STACS 2021 supplies the threshold mismatch and oracle/locality motivation. Separate self-reducibility and hardness-amplification literature shows that amplification is highly model- and structure-dependent, so no generic stronger inference is licensed.
- **Vote:** RETAIN_AS_RESEARCH_CHECKPOINT / NOVELTY_UNRESOLVED.

## Synthesis

The cell agrees on one promotion-safe conclusion.

> Single-copy restriction-recoverable wrappers with subexponential additive circuit overhead cannot provide the required exponential circuit-threshold amplification merely by expanding the variable count; under a separate streamability condition, they inherit the same exponent-cancellation problem as dummy padding when compared with the STACS 2021 high-threshold lower-bound envelope.

The cell rejects any stronger conclusion that threshold transport itself is impossible.

## Next atomic obligation

`C003-R1`: multi-copy composition. The first discriminator is whether a proposed direct-sum/direct-product construction has a **proved lower bound against circuit sharing**, rather than only the trivial upper bound obtained by evaluating copies independently.

Any proposal whose amplification theorem is just an unproved direct-sum assertion must be tagged `OBSTRUCTION_RENAMED`, not progress toward the root.
