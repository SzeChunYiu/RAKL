# Formal-methods external-review solicitation

**This form is a solicitation, not a completed review.** Completing it creates an external reviewer response; it does not by itself establish qualifying independence, completed peer review, acceptance, or publication.

## Artifact binding

Review only the 44-page `artifacts/main.pdf` with SHA-256 `b6a07517699a52151260c6c321f239af61b1e07089c079a1eac9f7c0ac1352af`, staged source SHA-256 `aa00a64d801ac802d310c818fe7699454db1346ccb2adf5e4d7de28019c20eb1`, and Git subject `118b74c17606637a916fc0e1fea8db6508adb847`. Report any mismatch under `P1-EXT-ARTIFACT-CODE-RNN-NNN` and stop.

## Independence, conflict of interest, and chronology

Before reviewing, disclose your relationship to the authors and RAKL, prior collaboration or supervision, financial or competitive interests, and other relevant conflict of interest. You may self-attest eligibility, but only a separate coordinator provenance audit can qualify the response as independent evidence. Record access, freeze, signature, and any post-freeze author/other-review access timestamps.

## Review questions

1. Are the object, quantities of interest, context, authority boundaries, and evidence states defined without category errors?
2. Are projection, equivalence, compatibility, mechanism, identification, validation, and promotion distinguished rigorously?
3. Do equations and operators have well-defined domains, codomains, assumptions, and failure states?
4. Are stated propositions actually supported by proofs, derivations, executable checks, or explicitly limited arguments?
5. Do known-answer PASS, planted FAIL, and structural `CANNOT_CHECK` worlds adequately test the validators?
6. Are frozen chronology and anti-leakage requirements sufficient to prevent post-result rescue?
7. Does the executable reference implementation match the manuscript's normative claims, and are any mismatches disclosed?
8. Which counterexample, edge regime, or adversarial construction most seriously threatens each load-bearing claim?
9. Are negative results and non-identification preserved rather than reframed as success?
10. What exact correction or additional evidence is required before formal-methods submission?

## Concern record

Obtain a four-character coordinator-assigned reviewer code and review round before starting. For code `X001`, round 1, assign `P1-EXT-FORMAL-X001-R01-001`, then increment without reuse. Use `P1-EXT-ARTIFACT-X001-R01-001` only for artifact binding or reproducibility. For every concern record:

- stable concern ID;
- severity and status;
- structured exact location (page, section, locator type, locator, and quoted anchor);
- finding;
- requested evidence or correction;
- falsifier or counterexample, where applicable;
- prior-art references, where applicable.

## Overall recommendation

Choose one schema recommendation and justify it: `reject`, `major_revision`, `minor_revision`, `invite_resubmission`, `suitable_for_external_submission`, or `cannot_assess`. Name the strongest contribution, most serious limitation, and every blocking concern ID.

Return a validated JSON response based on `RESPONSE_TEMPLATE.json` with `review_lens=formal_methods` and `role=formal_methods_reviewer`. The response is not peer-review acceptance or a journal decision.

Also populate `review_evidence.claims_checked`, `counterexample_search_summary`, and `executable_correspondence_checked`. Run `python validate_response.py RESPONSE.json`; schema validity and this relational check still do not confer independence authority.
