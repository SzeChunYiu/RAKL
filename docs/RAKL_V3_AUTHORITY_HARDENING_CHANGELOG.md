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

The branch was merged with then-current `origin/main` `decd1a4eae2b10cfdbb98e76b5023e2a756fa7a8` at merge commit `c1a2a98183feb9da1731f70fd4979078ac176e5a`. The only overlapping edit was the independently introduced robust float assertion in the v3 benchmark test; the merged file retains `pytest.approx` without duplication. Post-integration verification is 40 focused v3 tests passed, 1314 full tests passed, and `git diff --check` passed.

## Recursive same-context review repair

A same-context review (not independent review) found that the first benchmark chronology implementation compared timestamp strings and did not fully bind protocol/output freeze order. The successor parses timezone-aware instants and requires: protocol artifacts frozen no later than the packet, freeze-attestation subject time equal to packet freeze time, runs after the freeze attestation, output artifact freeze time equal to the registered run time, and matched-result subject/issuance after all runs.

## Blocking-review repair round

A blocking review reproduced seven authority/replay defects. The receipt verdict was narrowed to `INTERNAL_CONFORMANCE_PASS_BLOCK_MERGE_PENDING_FRESH_REVIEW`. The successor removes runtime caller policy keys from the authority decision by requiring exact release-manifest membership; binds local certificates to the exact section, atom, and decomposition; rejects lesson-report replay across candidate content; binds governance to the complete archive/variant/edge state; uses timezone-aware benchmark chronology; requires exact development benchmark, assurance benchmark, candidate method, and result receipt artifacts for Self-RAKL assurance; and introspects every exported v3 facade symbol for a canonical method owner. These are same-context corrective claims pending fresh exact-head re-review.

## Second blocking-review repair round

Fresh hostile review reproduced three remaining replays. The successor binds each consolidation report to the exact evidence/context packet and requires the report support to equal the packet's full positive evidence set. A promoted lesson must preserve every reviewed semantic field from its exact parent, retain the evidence-packet hash, and expose exactly the episode lineage bound by the authority attestation. Research-tool projection now has an independent canonical content hash and a purpose-specific `TOOL_PROJECTION` attestation resolving the exact tool bytes, exact recorded promoted-lesson hash, lesson parent, and complete supporting-episode lineage; changing tool id, name, kind, operation, lesson content, or support subset invalidates the projection. Merge remains blocked pending fresh exact-head review.
