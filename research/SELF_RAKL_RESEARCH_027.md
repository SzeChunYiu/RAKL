# SELF-RAKL Research 027 — Promotion Ref-State Attestation and Round-026 Repair

Date: 2026-08-09  
Frozen benchmark: `research/SELF_RAKL_RESEARCH_027_FROZEN_BENCHMARK.json`

## Selected atomic residual

The active repository state falsified the authority claim in `SELF_RAKL_RESEARCH_026_VALIDATION.json`.

Observed before Round-027 repair:

- active `main`: `a63babbe08a8de11ff6b927ed81150391a1467e9`;
- its parent: `11c8ccbffa65c4ef2922d85e5dcfc966f17fe7de`;
- Round-026 PR #3: closed and not merged;
- surviving Round-026 candidate head: `b29030f5e0cceb60ff7a601334bdd66fdaf908df`;
- the prior validation's claimed promoted SHA `d63139040bbf22c54aa8009c3950d43eac6f368c` does not resolve in the repository;
- active `test.yml` still used `actions/checkout@v4` and `actions/setup-python@v5`.

Therefore candidate validation and active promotion had been conflated. The original validation file is preserved unchanged as negative history and is superseded for authority by `SELF_RAKL_RESEARCH_026_VALIDATION_ERRATUM_027.json`.

## Six-role review panel

1. **Research-integrity/provenance lead** — required immutable erratum rather than rewriting the false receipt; separated evidence existence from evidence authority.
2. **Git/version-control and CI security engineer** — verified PR state, branch/head identity, candidate CI history, protected workflow contents and fast-forward semantics.
3. **Formal-methods/state-machine expert** — decomposed promotion into four distinct states: gate decision, ref-update event, observed active ref, and post-promotion validation.
4. **Software test/reproducibility engineer** — converted the failure into frozen known-answer/hostile worlds before implementing support code.
5. **Knowledge-representation lead** — modeled a validation receipt as a claim about an explicit repository subject rather than as self-authorizing prose.
6. **Adversarial scientific-method reviewer** — attacked nonexistent claimed SHAs, closed-unmerged PRs, stale candidate CI, active-content mismatch, erased negative history, and ref drift during attestation.

All retained findings were reviewed by at least two roles. The main disagreement concerned whether exact main equality should be required forever. The Git and provenance roles rejected exact equality because a valid post-validation documentation commit may follow promotion. The adopted invariant is instead that active main must be the candidate or a descendant of it, with the required promoted content still matching.

## New executable contract

`src/rakl/promotion_attestation.py` adds a fail-closed post-promotion observer. It does not perform network access; repository facts must be supplied by an external observer.

The core separation is:

```text
promotion gate decision
!= ref update event
!= active ref identity
!= post-promotion evidence authority
```

A candidate CI success cannot prove that main moved. A validation document cannot override missing ancestry. A claimed promoted SHA that does not exist is a refuted claim, not a soft warning. A later main commit may legitimately descend from the candidate, but content/manifest identity and exact candidate/post-promotion validation must still be positive.

## Round-026 replay

The prior candidate CI on `b29030f5e0cceb60ff7a601334bdd66fdaf908df` is preserved as candidate evidence, not active-main evidence. Round 027 restores the previously frozen Round-026 pinning contract and replays only the exact intended full-SHA action substitutions into the new candidate lineage:

- checkout → `11d5960a326750d5838078e36cf38b85af677262`;
- setup-python → `a26af69be951a213d495a4c3e4e4022e16d87065`.

The parent evaluator is expected to reject those protected workflow byte changes, exactly as the original benchmark specifies. That rejection is evidence that the existing firewall remains intact; it is not relabeled as a passing parent review.

## External projection and novelty

GitHub artifact-attestation documentation and SLSA both reinforce subject-bound provenance: the object named by an attestation must be verified rather than inferred from the existence of a receipt. Git fast-forward semantics provide the repository transition primitive. These are prior art, not RAKL novelty.

The narrower RAKL-specific retained method object is the application of subject/ref attestation to recursive method promotion: validation authority is denied unless the claimed candidate is actually reachable from the observed active ref and the promoted content remains present.

## Capability-shaping attribution

- **Model strength amplified:** detecting semantic inconsistencies across evidence ledgers and repository state.
- **Weakness constrained:** prose-level self-confirmation and stale-success reuse.
- **Smallest compensator:** deterministic ancestry/existence/content/CI observations plus a pure fail-closed classifier.
- **Verification oracle:** GitHub repository refs/commits/workflow state and hostile unit tests.
- **External-resource gain:** GitHub provides actual ref/commit/CI state; this is not intrinsic model improvement.
- **Whole-system gain target:** false-positive promotion attestations 1→0 and active-ref truth coverage 0→1.

## Status and closure impact

This route is **NON_FLAT**. It retained a new native fiber, `META_N091_POST_PROMOTION_REF_STATE_ATTESTATION`, and exposed a blocking non-fabrication failure in a prior validation receipt. Same-context and independent-flat counters therefore reset to zero.

The framework cannot issue a saturation certificate while post-promotion truth is unresolved. After this candidate passes exact-SHA tests, the required next sequence is: re-observe main, perform only a non-forced fast-forward, verify active ancestry/content, obtain exact-active-main validation, and then issue a new Round-027 validation receipt. Runner/environment identity, release identity, durable execution, real model/tokenizer matrices, claim-evidence provenance, and real scientific RAKLBench remain independent open fibers.
