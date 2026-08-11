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

The reference implementation uses HMAC-SHA256 with key material supplied by the protected evaluator environment. Candidate code must not possess that key. A production deployment still needs external key custody, runner isolation, rotation, audit logging, and independent review of the exact PR head.
