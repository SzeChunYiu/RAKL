# Paper 1 external-review solicitation packet

## Status and authority boundary

This directory is an **external-review solicitation packet, not a completed review**. It records zero external responses and does not establish independent review, journal peer review, acceptance, or publication. A returned response is reviewer evidence to be provenance-audited and answered; it is **not peer-review acceptance** or a journal decision.

The packet preserves the open parent concern `P1-R50-INDEPENDENCE`. Its purpose is to solicit three distinct assessments of the same exact artifact:

1. formal methods and internal validity;
2. nearest-work novelty and prior art;
3. editorial significance, clarity, and scope.

The authors' sequential Nature-skills-style passes remain same-context internal review. They are not represented here as independent evidence.

## Exact artifact

| Item | Identifier |
|---|---|
| Frozen Git subject | `118b74c17606637a916fc0e1fea8db6508adb847` |
| Modular source | `paper/epistemic_mechanics_round050/main.tex` |
| Modular source SHA-256 | `76c20f20e642939c10d6582a1a87233f172cbf7ee6a45f2dbdcdc4db35bee871` |
| Deterministic builder | `paper/build_epistemic_mechanics.py` |
| Builder SHA-256 | `d52c1715b4e1519443a7cef6e26ff2d03f5a8e000bc6a2ae2db0f03ed13b981b` |
| Builder parameters | `subject_sha=118b74c17606637a916fc0e1fea8db6508adb847`, `software_tests=840` |
| Staged source SHA-256 | `aa00a64d801ac802d310c818fe7699454db1346ccb2adf5e4d7de28019c20eb1` |
| PDF SHA-256 | `b6a07517699a52151260c6c321f239af61b1e07089c079a1eac9f7c0ac1352af` |
| PDF pages | `44` |

Verify the hashes in `PACKET_MANIFEST.json` before reading. If any artifact differs, stop and report a coordinator-allocated `P1-EXT-ARTIFACT-CODE-RNN-NNN` concern rather than reviewing an unbound version.

## Reviewer procedure

1. Choose exactly one lens form. Separate people should normally cover separate lenses.
2. Before substantive reading, verify the exact artifact hashes and record `artifact_accessed_at_utc`.
3. Read the independence and conflict-of-interest conditions. Disclose authorship, project involvement, collaboration, supervision, financial interests, close personal relationships, competitive stakes, and any other relevant conflict. `reviewer_asserts_independence_eligibility` is only a reviewer assertion; a separate coordinator identity, COI, and chronology audit must qualify any independent evidence.
4. Do not access an author response or another reviewer's response before freezing. Later access is allowed but must be recorded after `response_frozen_at_utc`.
5. Obtain a coordinator-assigned four-character concern code and round. Copy `RESPONSE_TEMPLATE.json`, replace every example value, and use IDs such as `P1-EXT-FORMAL-X001-R01-001`; reserve `P1-EXT-ARTIFACT-X001-R01-NNN` for binding/reproducibility.
6. Freeze the response, set `response_status` to `frozen-external-reviewer-response`, replace the zero manifest hash, and run `python validate_response.py RESPONSE.json`. The script applies bundled `SCHEMA.json`; binds the exact manifest, artifact hashes/pages, lens/role, and reviewer code; and checks chronology plus concern-set relations.
7. Transmit the response only through the secure return channel supplied by the soliciting coordinator. No channel or external reviewer has yet been designated in this repository packet; do not improvise one or expose private identity data publicly.
8. The coordinator must retain exact response bytes, record a SHA-256 receipt, privately verify identity/COI/chronology, and issue a separate qualification receipt. Schema and relational validity alone are insufficient.

## Files

- `FORMAL_METHODS_REVIEW.md` — formal definitions, claims, proofs/arguments, falsifiers, and executable correspondence.
- `NOVELTY_PRIOR_ART_REVIEW.md` — nearest work, distinction accuracy, priority, and novelty scope.
- `EDITORIAL_SIGNIFICANCE_REVIEW.md` — significance, audience, clarity, proportionality, and submission fitness.
- `RESPONSE_TEMPLATE.json` — schema-valid example only; it is explicitly not a submitted review.
- `SCHEMA.json` and `validate_response.py` — standalone structural and relational validation inside this directory.
- `BUILD_RECEIPT.json` — exact immutable-render build command, measured hashes, pages, and warning boundary.
- `BRANCH_OBSERVATION.json` — fetch/branch observation made before packet construction.
- `artifacts/main.tex` and `artifacts/main.pdf` — exact staged artifact under solicitation.
- `PACKET_MANIFEST.json` — subject identity, governance state, and content-bound inventory.

## Stable concern IDs

- `P1-EXT-FORMAL-X001-R01-001`, `P1-EXT-FORMAL-X001-R01-002`, ...
- `P1-EXT-NOVELTY-X002-R01-001`, `P1-EXT-NOVELTY-X002-R01-002`, ...
- `P1-EXT-EDITORIAL-X003-R01-001`, `P1-EXT-EDITORIAL-X003-R01-002`, ...
- `P1-EXT-ARTIFACT-X001-R01-001`, `P1-EXT-ARTIFACT-X001-R01-002`, ...

IDs never get reused. If a concern is withdrawn or closed by evidence available during review, retain the record and change its status; do not delete or renumber it.
