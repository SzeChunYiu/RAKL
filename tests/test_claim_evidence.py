from dataclasses import replace

from rakl.claim_evidence import (
    ClaimAtom,
    ClaimEvidenceLink,
    ClaimEvidenceVerdict,
    EvidenceJudgment,
    EvidenceRelation,
    EvidenceReviewVerdict,
    EvidenceSourceSnapshot,
    TextSpanSelector,
    freeze_source_snapshot,
    sha256_text,
    validate_claim_evidence_link,
)


def _packet(text: str = "Alpha evidence supports the frozen claim. Omega"):
    source = freeze_source_snapshot("src-1", "paper://one", text)
    exact = "evidence supports"
    start = text.index(exact)
    selector = TextSpanSelector(
        start=start,
        end=start + len(exact),
        exact=exact,
        prefix="Alpha ",
        suffix=" the frozen claim. Omega",
    )
    claim = ClaimAtom("claim-1", "The evidence supports the claim.", "qoi:one")
    link = ClaimEvidenceLink(
        link_id="link-1",
        claim_id=claim.claim_id,
        source_id=source.source_id,
        source_sha256=source.sha256,
        selector=selector,
        proposed_relation=EvidenceRelation.SUPPORTS,
        selector_frozen_before_review=True,
    )
    return claim, source, link


def _judgment(
    *,
    verdict: EvidenceReviewVerdict = EvidenceReviewVerdict.SUPPORTS,
    known_answer_validated=True,
    frozen_before_synthesis=True,
    link_id="link-1",
    claim_id="claim-1",
    scope="qoi:one",
):
    return EvidenceJudgment(
        judgment_id="judgment-1",
        link_id=link_id,
        claim_id=claim_id,
        scope=scope,
        verdict=verdict,
        known_answer_validated=known_answer_validated,
        frozen_before_synthesis=frozen_before_synthesis,
    )


def test_exact_locator_does_not_establish_semantic_support():
    claim, source, link = _packet()
    report = validate_claim_evidence_link(claim, source, link)
    assert report.verdict == ClaimEvidenceVerdict.LOCATOR_VERIFIED_SEMANTICS_UNREVIEWED
    assert report.locator_verified is True
    assert report.semantic_review_verified is False
    assert report.locator_fidelity_establishes_semantic_support is False
    assert report.grants_scientific_authority is False
    assert report.grants_target_authority is False


def test_stale_source_snapshot_fails_closed():
    claim, source, link = _packet()
    stale = replace(source, text=source.text + " changed")
    report = validate_claim_evidence_link(claim, stale, link)
    assert report.verdict == ClaimEvidenceVerdict.CANNOT_CHECK
    assert report.reasons == ("source_snapshot_hash_mismatch",)


def test_link_source_hash_mismatch_is_invalid():
    claim, source, link = _packet()
    report = validate_claim_evidence_link(
        claim, source, replace(link, source_sha256="0" * 64)
    )
    assert report.verdict == ClaimEvidenceVerdict.TRIAL_INVALID
    assert report.reasons == ("link_source_hash_mismatch",)


def test_selector_bounds_fail_closed():
    claim, source, link = _packet()
    bad = replace(link, selector=replace(link.selector, start=-1))
    report = validate_claim_evidence_link(claim, source, bad)
    assert report.verdict == ClaimEvidenceVerdict.TRIAL_INVALID
    assert report.reasons == ("selector_bounds_invalid",)


def test_exact_prefix_and_suffix_mismatches_are_distinguished():
    claim, source, link = _packet()
    exact_bad = replace(link, selector=replace(link.selector, exact="wrong"))
    assert validate_claim_evidence_link(claim, source, exact_bad).reasons == (
        "selector_exact_mismatch",
    )

    prefix_bad = replace(link, selector=replace(link.selector, prefix="wrong "))
    assert validate_claim_evidence_link(claim, source, prefix_bad).reasons == (
        "selector_prefix_mismatch",
    )

    suffix_bad = replace(link, selector=replace(link.selector, suffix=" wrong"))
    assert validate_claim_evidence_link(claim, source, suffix_bad).reasons == (
        "selector_suffix_mismatch",
    )


def test_repeated_quote_is_disambiguated_by_offsets():
    text = "A target B target C"
    source = freeze_source_snapshot("src-1", "paper://repeat", text)
    claim = ClaimAtom("claim-1", "Target occurs in the second location.", "qoi:one")
    start = text.rindex("target")
    link = ClaimEvidenceLink(
        "link-1",
        claim.claim_id,
        source.source_id,
        source.sha256,
        TextSpanSelector(start, start + 6, "target", prefix="B ", suffix=" C"),
        EvidenceRelation.SUPPORTS,
        True,
    )
    report = validate_claim_evidence_link(claim, source, link)
    assert report.verdict == ClaimEvidenceVerdict.LOCATOR_VERIFIED_SEMANTICS_UNREVIEWED


def test_unicode_offsets_use_python_unicode_code_points():
    text = "α🍎β evidence γ"
    source = freeze_source_snapshot("src-1", "paper://unicode", text)
    exact = "evidence"
    start = text.index(exact)
    claim = ClaimAtom("claim-1", "Unicode locator is exact.", "qoi:one")
    link = ClaimEvidenceLink(
        "link-1",
        claim.claim_id,
        source.source_id,
        source.sha256,
        TextSpanSelector(start, start + len(exact), exact, prefix="α🍎β ", suffix=" γ"),
        EvidenceRelation.SUPPORTS,
        True,
    )
    report = validate_claim_evidence_link(claim, source, link)
    assert report.locator_verified is True


def test_posthoc_or_unknown_selector_chronology_is_not_accepted():
    claim, source, link = _packet()
    posthoc = validate_claim_evidence_link(
        claim, source, replace(link, selector_frozen_before_review=False)
    )
    assert posthoc.verdict == ClaimEvidenceVerdict.TRIAL_INVALID
    assert posthoc.reasons == ("posthoc_selector_definition",)

    unknown = validate_claim_evidence_link(
        claim, source, replace(link, selector_frozen_before_review=None)
    )
    assert unknown.verdict == ClaimEvidenceVerdict.CANNOT_CHECK
    assert unknown.reasons == ("selector_freeze_chronology_unknown",)


def test_semantic_review_requires_known_answer_validation():
    claim, source, link = _packet()
    report = validate_claim_evidence_link(
        claim, source, link, _judgment(known_answer_validated=None)
    )
    assert report.verdict == ClaimEvidenceVerdict.CANNOT_CHECK
    assert report.reasons == ("semantic_review_known_answer_validation_unknown",)


def test_semantic_review_must_precede_synthesis():
    claim, source, link = _packet()
    report = validate_claim_evidence_link(
        claim, source, link, _judgment(frozen_before_synthesis=False)
    )
    assert report.verdict == ClaimEvidenceVerdict.TRIAL_INVALID
    assert report.reasons == ("posthoc_semantic_review",)


def test_semantic_judgment_identity_and_scope_must_match():
    claim, source, link = _packet()
    wrong_id = validate_claim_evidence_link(
        claim, source, link, _judgment(link_id="other-link")
    )
    assert wrong_id.verdict == ClaimEvidenceVerdict.TRIAL_INVALID
    assert wrong_id.reasons == ("semantic_judgment_identity_mismatch",)

    wrong_scope = validate_claim_evidence_link(
        claim, source, link, _judgment(scope="qoi:other")
    )
    assert wrong_scope.verdict == ClaimEvidenceVerdict.TRIAL_INVALID
    assert wrong_scope.reasons == ("semantic_judgment_scope_mismatch",)


def test_refuting_review_preserves_contradiction_to_support_proposal():
    claim, source, link = _packet()
    report = validate_claim_evidence_link(
        claim, source, link, _judgment(verdict=EvidenceReviewVerdict.REFUTES)
    )
    assert report.verdict == ClaimEvidenceVerdict.REVIEW_CONTRADICTION
    assert report.reviewed_relation == EvidenceReviewVerdict.REFUTES
    assert "proposed:SUPPORTS" in report.reasons
    assert "reviewed:REFUTES" in report.reasons
    assert report.grants_scientific_authority is False


def test_insufficient_review_never_becomes_support():
    claim, source, link = _packet()
    report = validate_claim_evidence_link(
        claim, source, link, _judgment(verdict=EvidenceReviewVerdict.INSUFFICIENT)
    )
    assert report.verdict == ClaimEvidenceVerdict.REVIEWED_INSUFFICIENT_EVIDENCE
    assert report.semantic_review_verified is True
    assert report.grants_target_authority is False


def test_reviewed_support_is_proposal_only():
    claim, source, link = _packet()
    report = validate_claim_evidence_link(claim, source, link, _judgment())
    assert report.verdict == ClaimEvidenceVerdict.REVIEWED_SUPPORT_PROPOSAL_ONLY
    assert report.locator_verified is True
    assert report.semantic_review_verified is True
    assert report.grants_scientific_authority is False
    assert report.activates_canonical_knowledge is False


def test_reviewed_refutation_is_proposal_only():
    claim, source, link = _packet()
    refuting_link = replace(link, proposed_relation=EvidenceRelation.REFUTES)
    report = validate_claim_evidence_link(
        claim,
        source,
        refuting_link,
        _judgment(verdict=EvidenceReviewVerdict.REFUTES),
    )
    assert report.verdict == ClaimEvidenceVerdict.REVIEWED_REFUTATION_PROPOSAL_ONLY
    assert report.grants_scientific_authority is False


def test_context_review_can_only_qualify_a_qualification_link():
    claim, source, link = _packet()
    qualifying = replace(link, proposed_relation=EvidenceRelation.QUALIFIES)
    report = validate_claim_evidence_link(
        claim,
        source,
        qualifying,
        _judgment(verdict=EvidenceReviewVerdict.CONTEXT_ONLY),
    )
    assert report.verdict == ClaimEvidenceVerdict.REVIEWED_CONTEXT_PROPOSAL_ONLY


def test_source_hash_prevents_silent_relocation_between_versions():
    claim, source, link = _packet()
    copied_text = source.text.replace("Omega", "Version two")
    different_snapshot = EvidenceSourceSnapshot(
        source_id=source.source_id,
        source_locator=source.source_locator,
        text=copied_text,
        sha256=source.sha256,
    )
    report = validate_claim_evidence_link(claim, different_snapshot, link)
    assert report.verdict == ClaimEvidenceVerdict.CANNOT_CHECK
    assert report.reasons == ("source_snapshot_hash_mismatch",)


def test_freeze_snapshot_hash_is_exact_utf8_and_deterministic():
    text = "Exact α evidence 🍎"
    first = freeze_source_snapshot("src", "paper://x", text)
    second = freeze_source_snapshot("src", "paper://x", text)
    assert first == second
    assert first.sha256 == sha256_text(text)
    assert first.sha256 != sha256_text(text + " ")


def test_reports_are_deterministic_for_stable_inputs():
    claim, source, link = _packet()
    judgment = _judgment()
    assert validate_claim_evidence_link(
        claim, source, link, judgment
    ) == validate_claim_evidence_link(claim, source, link, judgment)
