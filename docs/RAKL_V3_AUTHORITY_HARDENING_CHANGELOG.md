# RAKL v3 authority hardening — 2026-08-11

## Boundary

This is an urgent corrective framework round following the merge of PR #118. It is internal framework assurance, not independent peer review. No paper, publication, publishing, or paper-review artifact is changed.

## Failure diagnosis

The merged v3 interfaces correctly described evidence governance, but several executable transitions still trusted caller-controlled representations of authority: strings standing for verification or proof, booleans standing for independence/freeze/matching, `LocalSection.verified`, `governance_approved`, and bare authority enums. The root cause was **declaration-bound authority without protected content resolution**.

## Corrective invariant

An authority-sensitive v3 transition now requires a protected attestation that resolves all of:

1. exact canonical subject SHA-256;
2. exact evidence bytes and SHA-256 bindings;
3. exact evaluator bytes and SHA-256 binding;
4. protected signer identity under an externally supplied trust policy;
5. proposer/evaluator separation encoded by distinct identities, not a caller boolean;
6. artifact-freeze, subject-freeze, and attestation chronology;
7. a purpose-specific PASS verdict.

IDs, labels, enums, and booleans remain usable as proposal or display data only. Missing or forged authority evidence fails closed.

## Hardened surfaces

- immutable episode and lesson content identities;
- lesson verification, transfer, proof, promotion, and research-tool projection;
- local-section gluing and solution authority;
- Self-RAKL assurance and incumbent governance promotion;
- matched continual-learning benchmark packet/evaluator/task/output binding and chronology;
- public v3 authority facade;
- canonical `METHOD_CONTRACTS` ownership mapping for v3 modules and authority surfaces.

## Hostile worlds retained

The test suite preserves malformed content, caller ID/boolean substitution, forged signatures, empty local evidence, unprotected Self-RAKL assurance/governance, unprotected benchmark labels, corrupt output bytes, and post-hoc freeze chronology.

## Verification

Machine-readable evidence: `research/receipts/RAKL_V3_AUTHORITY_HARDENING_20260811.json`.

At implementation commit `35da974c57dece0c451cbb88cd7712478e211c95`:

- focused v3 suite: 39 passed;
- exact full framework suite: 1312 passed;
- `git diff --check`: PASS;
- pre-existing failures on this exact base: none;
- paper files touched: none.

## Residual trust boundary

The corrected reference implementation accepts authority only for exact attestation payload digests pinned by a governed framework-release manifest. Runtime caller keys and policies are proposal inputs and cannot extend that manifest. A production deployment still needs external evaluator isolation, governed manifest updates, audit logging, and independent review of the exact PR head.

## Latest-main integration

The branch was first merged with `origin/main` `decd1a4eae2b10cfdbb98e76b5023e2a756fa7a8` at merge commit `c1a2a98183feb9da1731f70fd4979078ac176e5a`; the only overlapping edit was the independently introduced robust float assertion in the v3 benchmark test. Before final review, the branch was fresh-fetched and history-merged with exact latest `origin/main` `a521d577724dfedb3123e22cdbac457bce4e22f7` at merge commit `a816932a4fb80a17616db192679d413a96b03bc7`. The intervening main changes were publication/workflow/script-only and produced no overlap with the authority-hardening source, tests, receipt, or changelog. Post-second-repair verification is 41 focused v3 tests passed, 1315 full tests passed, and `git diff --check` passed.

## Recursive same-context review repair

A same-context review (not independent review) found that the first benchmark chronology implementation compared timestamp strings and did not fully bind protocol/output freeze order. The successor parses timezone-aware instants and requires: protocol artifacts frozen no later than the packet, freeze-attestation subject time equal to packet freeze time, runs after the freeze attestation, output artifact freeze time equal to the registered run time, and matched-result subject/issuance after all runs.

## Blocking-review repair round

A blocking review reproduced seven authority/replay defects. The receipt verdict was narrowed to `INTERNAL_CONFORMANCE_PASS_BLOCK_MERGE_PENDING_FRESH_REVIEW`. The successor removes runtime caller policy keys from the authority decision by requiring exact release-manifest membership; binds local certificates to the exact section, atom, and decomposition; rejects lesson-report replay across candidate content; binds governance to the complete archive/variant/edge state; uses timezone-aware benchmark chronology; requires exact development benchmark, assurance benchmark, candidate method, and result receipt artifacts for Self-RAKL assurance; and introspects every exported v3 facade symbol for a canonical method owner. These are same-context corrective claims pending fresh exact-head re-review.

## Second blocking-review repair round

Fresh hostile review reproduced three remaining replays. The successor binds each consolidation report to the exact evidence/context packet and requires the report support to equal the packet's full positive evidence set. A promoted lesson must preserve every reviewed semantic field from its exact parent, retain the evidence-packet hash, and expose exactly the episode lineage bound by the authority attestation. Research-tool projection now has an independent canonical content hash and a purpose-specific `TOOL_PROJECTION` attestation resolving the exact tool bytes, exact recorded promoted-lesson hash, lesson parent, and complete supporting-episode lineage; changing tool id, name, kind, operation, lesson content, or support subset invalidates the projection. Merge remains blocked pending fresh exact-head review.

## Third blocking-review repair round

Fresh hostile review then reproduced two deeper trust-boundary failures. First, a caller could reconstruct a known manifest id and unsigned payload with arbitrary key material because the former signature was an unkeyed SHA-256 and resolution did not authenticate the runtime policy key. Attestations now use HMAC-SHA-256, and resolution requires both the exact release-manifest payload digest and a release-governed signer-key fingerprint; a runtime policy supplies verification material but cannot authorize a new key. The planted known-id replay uses the exact `section-check` payload with caller-controlled key material and fails closed.

Second, a caller could mutate a promoted lesson's contradiction lineage, evidence pointers, or packet hash and recompute its self-hash. Promotion now freezes a canonical consolidation-packet artifact and requires a separate purpose-specific `LESSON_PROMOTION` attestation whose subject is the exact final promoted-lesson content hash and whose evidence binds the exact parent, packet artifact, and complete episode lineage. Mutating any reviewed final field invalidates this protected final-content attestation. These remain internal hostile conformance repairs, not independent review, and merge remains blocked pending a fresh review of the successor head.

## Final exact-head hostile review and current-main refresh

A fresh same-context internal technical review, not independent peer review, checked exact head `4adcb8e79acb1a070db971e622d6e4ef79e4660d` against base `a521d577724dfedb3123e22cdbac457bce4e22f7`. It rejected the known-manifest arbitrary/mismatched-key mint, cross-problem local-section replay, report and final-lesson content mutations, promotion-attestation/packet corruption, arbitrary or unrecorded tool projections, support-subset projection replay, governance replay, chronology/binding bypasses, and incomplete method ownership. The exact control passed. Verification was 41 focused v3 tests and 1315 full tests, with receipt/source hashes valid and no paper or publication path in the PR diff.

After that review, the branch was history-merged with fresh `origin/main` `337807625a60ba821e123f39d05f085fd9b0a5fa` at merge commit `815249dff0f8f38b9af5ce12b4b03038a9f66990`. The intervening main changes were publication-only and did not overlap the authority source, tests, receipt, or changelog; there were no conflicts and this round resolved or edited no paper file. Merge authority remains conditional on required GitHub checks completing successfully. This is scoped internal conformance only and grants none of independent peer review, universal security, mathematical truth, empirical RAKL superiority, or automatic framework promotion.
