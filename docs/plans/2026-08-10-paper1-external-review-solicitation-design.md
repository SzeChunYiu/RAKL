# Paper 1 External-Review Solicitation Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Produce a content-bound Paper 1 solicitation packet that enables genuinely external formal, novelty, and editorial responses without representing the packet or any same-session critique as completed peer review.

**Architecture:** Keep the frozen Paper 1 manuscript at merged `main` subject `118b74c17606637a916fc0e1fea8db6508adb847` unchanged. Add an auditable packet containing the exact staged source and PDF, a machine-readable manifest, three lens-specific forms, and one strict response schema/template. Treat every future response as evidence requiring separate provenance and authority evaluation; the packet itself closes no external gate.

**Tech Stack:** Markdown, JSON Schema Draft 2020-12, JSON, Python/pytest, the existing deterministic Paper 1 source builder, Tectonic 0.15.0 for the content-addressed distributed render, `latexmk` for exact GitHub compile CI, and `pdfinfo`.

---

## Frozen boundary

- **Object:** Paper 1, *Epistemic Mechanics*, as built from merged subject `118b74c17606637a916fc0e1fea8db6508adb847`.
- **QoI:** whether the exact artifact is ready to solicit genuinely external formal-methods, nearest-work novelty, and editorial/significance assessments.
- **Authority boundary:** this iteration constructs a solicitation only. It receives no external response and provides no independent-review, peer-review, acceptance, or publication evidence.
- **Preserved concern:** `P1-R50-INDEPENDENCE` remains open until qualifying external responses are received and separately audited.
- **Failure behavior:** missing hashes, role/COI attestations, chronology, exact locations, or response declarations fail closed at response ingestion. A disclosed conflict may be recorded, but the response cannot silently count as independent evidence.

## Alternatives considered

1. **One unstructured review document.** Rejected because it cannot enforce artifact binding, chronology, stable concern identities, or role-specific questions.
2. **Three unrelated schemas.** Rejected because duplicated contracts would drift and make cross-lens aggregation harder.
3. **Recommended: three human-readable forms plus one strict shared response schema.** This keeps each review lens distinct while preserving one machine-readable evidence contract and stable concern namespaces.

## Task 1: Add fail-closed packet tests

**Files:**
- Create: `tests/test_paper1_external_review_solicitation.py`

1. Assert that the manifest names the artifact a solicitation and records zero completed external reviews.
2. Assert the frozen subject, source, builder, staged-source, and PDF hashes against real files.
3. Assert the three forms are separate, use distinct stable concern namespaces, and never claim completed review.
4. Validate the response template with Draft 2020-12 and prove missing binding, independence/COI, chronology, or concern-location fields are rejected.
5. Assert chronology timestamps are ordered and that the template declares no pre-freeze author-response access.
6. Run `rtk pytest -q tests/test_paper1_external_review_solicitation.py` and confirm RED because packet artifacts do not exist.

## Task 2: Build the exact frozen manuscript

**Files:**
- Create: `review/paper1/external_solicitation/artifacts/main.tex`
- Create: `review/paper1/external_solicitation/artifacts/main.pdf`

1. Run the deterministic builder with subject `118b74c17606637a916fc0e1fea8db6508adb847` and `software_tests=840`.
2. Compile the immutable distributed render with the exact Tectonic command in `BUILD_RECEIPT.json`; do not promise byte-identical PDF regeneration because creation metadata varies.
3. Reject overfull boxes, oversized floats, undefined references/citations, or partial rendering.
4. Record SHA-256 digests and page count from the generated artifacts.

## Task 3: Implement the solicitation contract

**Files:**
- Create: `review/paper1/external_solicitation/README.md`
- Create: `review/paper1/external_solicitation/PACKET_MANIFEST.json`
- Create: `review/paper1/external_solicitation/FORMAL_METHODS_REVIEW.md`
- Create: `review/paper1/external_solicitation/NOVELTY_PRIOR_ART_REVIEW.md`
- Create: `review/paper1/external_solicitation/EDITORIAL_SIGNIFICANCE_REVIEW.md`
- Create: `review/paper1/external_solicitation/RESPONSE_TEMPLATE.json`
- Create: `schemas/paper1-external-review-response.schema.json`

1. Write the three lens-specific forms with namespaces `P1-EXT-FORMAL-*`, `P1-EXT-NOVELTY-*`, and `P1-EXT-EDITORIAL-*`; reserve `P1-EXT-ARTIFACT-*` for binding/reproducibility concerns.
2. Require pseudonymous reviewer identity, role/lens, independence and COI disclosures, access/freeze/signature times, no author-response access before freeze, exact artifact hashes, exact concern locations, severity/status, findings, requested evidence/correction, and falsifier/counterexample/prior-art references when applicable.
3. State throughout that the packet is a solicitation, not a review, and that a response is not journal peer-review acceptance.
4. Fill the manifest only from measured artifact hashes and counts.
5. Run the targeted test and confirm GREEN.

## Task 4: Verify, review, and publish the PR without merging

1. Run the full pytest suite.
2. Re-run the Paper 1 targeted workflow equivalent with the new supplemental test included.
3. Rebuild the exact PDF, compare hashes, run warning preflight, render every page, and inspect the render montage.
4. Run `rtk git diff --check` and the trusted-parent evaluator without modifying protected evaluators.
5. Request a hostile same-session read-only review and label it internal, non-independent critique.
6. Resolve blocking findings and repeat verification.
7. Commit, push, and open a PR to `main`; monitor exact-head CI.
8. Do **not** merge. Leave `P1-R50-INDEPENDENCE` and all three external gates open pending qualifying external evidence.
