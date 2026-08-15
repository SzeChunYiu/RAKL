# Paper V — current scientific question and status (2026-08-15)

Status: **binding editorial/claim addendum for this research branch**. It records what is currently implemented/testable and what remains external. It grants no theorem, novelty, scientific, value or publication authority.

## Headline question

Paper V is not fundamentally a claim that an LLM can search for proofs. Its durable question is:

> **What must be true before a machine-generated mathematical result may be promoted into the research record as the intended result?**

The load-bearing coordinates remain noncompensatory:

1. specification alignment — the formal theorem is the intended claim;
2. theorem truth — the exact formal statement has a trusted proof path;
3. novelty — no equivalent/stronger prior result is found within a declared, cutoff-scoped literature world;
4. research value — the result passes a separately declared value/importance review;
5. verifier trust — the checker/proof-source/dependency path is the one actually audited.

Proof search, LLM generation, symbolic enumeration and other proposal mechanisms are executors beneath this promotion contract.

## Existing executable assurance inherited by this branch

The repository already contains a strict mathematical-research state machine and hostile benchmark. The existing ten-case benchmark checks, among other cases:

- finite computation is not proof;
- round-trip formalization failure blocks promotion;
- a proof for a neighboring statement hash is rejected;
- `sorryAx` and unregistered custom axioms are rejected;
- missing isolated independent recheck is rejected;
- a verified proof does not mint novelty;
- an identified prior equivalent becomes `VERIFIED_REDISCOVERY`;
- bounded novelty is not automatically a new-mathematics candidate;
- the positive control reaches `NEW_MATHEMATICS_CANDIDATE` only when all incumbent gates pass.

The finite Boolean authority-product test additionally exhausts all 32 states of specification/truth/novelty/value/verifier-trust. A strict product gate has zero missing-spec/truth/trust false promotions; a naive 4-of-5 gate has three.

## New formal assurance nucleus

`formal/PaperVAssurance.lean` mechanizes the minimum executor-independent assurance claims under the repository's exact Lean toolchain:

- generator-error containment under a sound checker and promotion-requires-check rule;
- noncompensatory promotion coordinates;
- theorem truth can remain fixed while novelty decreases under literature expansion;
- transitive proof-dependency closure;
- proposal/search mutation cannot by itself change mathematical authority.

The dedicated `paper5-formal-assurance` workflow is load-bearing: it rejects unfinished proof placeholders, typechecks the development, requires Lean to reject a deliberately false/type-invalid control, and audits all five theorem dependencies with `#print axioms`. These claims become mechanized only when that exact-head workflow is green.

## New self-certification hardening

The incumbent assurance objects represented some independent review by counts/booleans. That is insufficient for a paper whose central claim is non-sovereign promotion. The v2 wrapper now binds:

- formalization review to exact formal-statement hash, review procedure, reviewer identity and proposer identity;
- novelty review to exact theorem fingerprint, literature manifest, search routes/cutoff and independent reviewer identity;
- value review to the exact formal statement and a frozen criteria/procedure identity;
- verifier trust to the exact proof-source hash and checker identity manifest.

A reviewer count or boolean cannot substitute for those receipts. Self-review, subject swaps, novelty-world swaps and verifier-source/checker swaps fail closed. The wrapper is conservative: it may remove a v1 promotion path, never add one that v1 rejected.

## New ProofDAG dependency hardening

The incumbent DAG validates endpoints, relation orientation, cycles, exact statement binding and strict proof receipts. The v2 checkpoint additionally requires a dependency-manifest receipt extracted for the exact proof source. The transitive dependency **statement-hash set** in the DAG must match the proof-source manifest exactly; omitted, extra or source-swapped dependencies are rejected before checkpoint promotion.

## Executor independence

The publication claim should concern invariant promotion semantics across proposer classes, not equal proposal quality. An LLM proposer, symbolic enumerator, tactic searcher or human may discover different candidates. None may bypass the same exact-subject specification/proof/novelty/value/verifier-trust product.

## What remains external

Local architecture/conformance can be closed by the CI and hostile tests above. A stronger field-facing empirical paper still requires:

1. an independently frozen public/open mathematical task epoch (known-answer and open-discovery roles kept separate);
2. at least one substantially different or LLM-free proposer lane;
3. measured valid-promotion recall alongside false-promotion rate, so reject-all is not a success;
4. fully costed strongest proof-search parents for any verified-transformation/search-performance claim;
5. bounded novelty evidence whose literature world is actually searched for the concrete output;
6. independent mathematical/value review for any concrete claimed new result.

Until those exist, Paper V may claim an implemented/mechanized assurance architecture at the scopes actually green in CI; it may not claim autonomous new mathematical discovery or global novelty.
