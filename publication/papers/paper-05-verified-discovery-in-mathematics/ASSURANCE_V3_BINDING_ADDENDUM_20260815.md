# Paper V — assurance v3 transitive binding addendum (2026-08-15)

This addendum supersedes the identity-binding description in `CURRENT_QUESTION_AND_STATUS_20260815.md` where the later hostile review is stricter. It grants no authority by itself.

The final local assurance successor is `src/rakl/math_research_assurance_v3.py`.

In addition to the v2 exact-subject controls, v3 requires:

- **current-proposer binding**: an independent-review receipt records the proposer it was issued against and must match the current proposer; a receipt cannot be reused by a different proposer;
- **formalization-pair binding**: specification review binds a digest of both the informal-claim hash and the formal-statement hash, so changing the intended informal claim while retaining the same Lean statement requires a new review;
- **complete novelty-dossier binding**: novelty review binds cutoff, corpus/search routes, theorem fingerprint, literature manifest, equivalence result, candidate matches and coverage notes; a post-review `equivalent_found`/candidate-match flip invalidates the receipt;
- **independent verifier attestation**: verifier trust is bound to the current proposer, exact proof source, checker identity/manifest and a separate attestor identity; proposer self-attestation and cross-proposer receipt reuse fail closed;
- **ProofDAG manifest binding** remains separate and load-bearing for checkpointed proofs: the exact proof-source transitive dependency statement-hash set must equal the DAG closure.

The frozen symbolic-vs-LLM executor-invariance cases are re-run through v3. The same exact artifact/evidence chain must receive the same authority stage regardless of proposer class, while self-review still blocks.

This is a **promotion-contract** result. It does not claim that different executors discover equally good mathematics, that any concrete theorem is globally novel, or that a new-mathematics candidate has publication authority.
