from dataclasses import replace

from rakl.authority_ledger import AuthorityAxis, AuthorityProposal
from rakl.claim_evidence import (
    ClaimAtom,
    ClaimEvidenceLink,
    EvidenceJudgment,
    EvidenceRelation,
    EvidenceReviewVerdict,
    TextSpanSelector,
    freeze_source_snapshot,
    validate_claim_evidence_link,
)
from rakl.epistemic_noninterference import EvidenceRootKind
from rakl.evidence_binding_certificate import (
    EvidenceBindingVerdict,
    ReviewedEvidenceBinding,
    evaluate_evidence_binding_for_promotion,
)
from rakl.v3_scientific_authority import ScientificEvidenceBinding


CLAIM = ClaimAtom("claim-1", "Thermal drift generates the residual.", "regime-A")


def _binding(
    evidence_id: str,
    *,
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS,
    reviewed: EvidenceReviewVerdict | None = EvidenceReviewVerdict.SUPPORTS,
    kind: EvidenceRootKind = EvidenceRootKind.EXTERNAL_OBSERVATION,
    supports_axes=(AuthorityAxis.MECHANISM,),
    upstream: str | None = None,
    link_id: str | None = None,
):
    text = f"Exact evidence payload for {evidence_id}."
    source = freeze_source_snapshot(evidence_id, f"paper://{evidence_id}", text)
    exact = "evidence payload"
    start = text.index(exact)
    link = ClaimEvidenceLink(
        link_id=link_id or f"link-{evidence_id}",
        claim_id=CLAIM.claim_id,
        source_id=source.source_id,
        source_sha256=source.sha256,
        selector=TextSpanSelector(start, start + len(exact), exact),
        proposed_relation=relation,
        selector_frozen_before_review=True,
    )
    judgment = None
    if reviewed is not None:
        judgment = EvidenceJudgment(
            judgment_id=f"judgment-{evidence_id}",
            link_id=link.link_id,
            claim_id=CLAIM.claim_id,
            scope=CLAIM.scope,
            verdict=reviewed,
            known_answer_validated=True,
            frozen_before_synthesis=True,
        )
    report = validate_claim_evidence_link(CLAIM, source, link, judgment)
    registration = ScientificEvidenceBinding(
        evidence_id,
        kind,
        source.sha256,
        tuple(supports_axes),
        upstream,
    )
    return ReviewedEvidenceBinding(evidence_id, link, report), registration


def _proposal(*evidence_ids: str, axis=AuthorityAxis.MECHANISM, scope="regime-A"):
    return AuthorityProposal(
        proposal_id="proposal-1",
        claim_id=CLAIM.claim_id,
        axis=axis,
        proposition="Thermal drift is the generating mechanism.",
        scope_id=scope,
        evidence_ids=tuple(evidence_ids),
    )


def _assess(proposal, bindings, registrations, **kwargs):
    return evaluate_evidence_binding_for_promotion(
        CLAIM,
        proposal,
        bindings,
        {item.evidence_id: item for item in registrations},
        certificate_id=kwargs.pop("certificate_id", "bind-cert-1"),
        frozen_before_promotion=kwargs.pop("frozen_before_promotion", True),
        **kwargs,
    )


def test_reviewed_exact_support_yields_proposal_only_certificate():
    binding, registration = _binding("obs-1")
    result = _assess(_proposal("obs-1"), (binding,), (registration,))

    assert result.verdict is EvidenceBindingVerdict.VALID_FOR_PROMOTION_CHALLENGER
    assert result.valid_for_promotion_challenger is True
    assert result.grants_scientific_authority is False
    assert result.certificate is not None
    assert result.certificate.support_evidence_ids == ("obs-1",)
    assert result.certificate.terminal_root_ids == ("obs-1",)
    assert result.certificate.grants_scientific_authority is False
    assert len(result.certificate.subject_hash) == 64


def test_correct_claim_with_wrong_evidence_ids_is_invalid():
    support, reg1 = _binding("obs-good")
    _, reg2 = _binding("obs-wrong")
    result = _assess(
        _proposal("obs-wrong"),
        (support,),
        (reg1, reg2),
    )

    assert result.verdict is EvidenceBindingVerdict.INVALID
    assert "promotion_evidence_ids_do_not_exactly_match_reviewed_support_bindings" in result.reasons


def test_unreviewed_semantics_are_cannot_check_not_wrong_evidence():
    binding, registration = _binding("obs-1", reviewed=None)
    result = _assess(_proposal("obs-1"), (binding,), (registration,))

    assert result.verdict is EvidenceBindingVerdict.CANNOT_CHECK
    assert "semantic_relation_unreviewed:obs-1" in result.reasons
    assert "promotion_evidence_ids_do_not_exactly_match_reviewed_support_bindings" not in result.reasons


def test_bound_refutation_blocks_promotion_until_conflict_resolution():
    support, reg1 = _binding("obs-support")
    refute, reg2 = _binding(
        "obs-refute",
        relation=EvidenceRelation.REFUTES,
        reviewed=EvidenceReviewVerdict.REFUTES,
    )
    result = _assess(
        _proposal("obs-support"),
        (support, refute),
        (reg1, reg2),
    )

    assert result.verdict is EvidenceBindingVerdict.CONFLICT_REQUIRES_RESOLUTION
    assert "promotion_has_bound_refuting_evidence:obs-refute" in result.reasons


def test_two_derivative_supports_do_not_become_two_independent_roots():
    first, reg1 = _binding("paper-a", upstream="root-exp")
    second, reg2 = _binding("paper-b", upstream="root-exp")
    result = _assess(
        _proposal("paper-a", "paper-b"),
        (first, second),
        (reg1, reg2),
    )

    assert result.verdict is EvidenceBindingVerdict.INVALID
    assert "reviewed_support_collapses_to_1_independent_lineage_roots" in result.reasons


def test_task_experience_cannot_be_bound_as_scientific_support():
    binding, registration = _binding(
        "episode-1",
        kind=EvidenceRootKind.TASK_EPISODE,
    )
    result = _assess(_proposal("episode-1"), (binding,), (registration,))

    assert result.verdict is EvidenceBindingVerdict.INVALID
    assert "experience_objects_bound_as_scientific_support:episode-1" in result.reasons


def test_representation_support_cannot_license_mechanism_axis():
    binding, registration = _binding(
        "obs-representation",
        supports_axes=(AuthorityAxis.REPRESENTATION,),
    )
    result = _assess(
        _proposal("obs-representation", axis=AuthorityAxis.MECHANISM),
        (binding,),
        (registration,),
    )

    assert result.verdict is EvidenceBindingVerdict.INVALID
    assert "reviewed_support_does_not_license_requested_axis:MECHANISM" in result.reasons


def test_scope_transport_requires_a_separate_verified_contract():
    binding, registration = _binding("obs-1")
    result = _assess(
        _proposal("obs-1", scope="regime-B"),
        (binding,),
        (registration,),
    )

    assert result.verdict is EvidenceBindingVerdict.INVALID
    assert "proposal_scope_not_exactly_claim_scope" in result.reasons


def test_unresolved_obligation_fails_closed():
    binding, registration = _binding("obs-1")
    result = _assess(
        _proposal("obs-1"),
        (binding,),
        (registration,),
        missing_obligations=("independent replication",),
    )

    assert result.verdict is EvidenceBindingVerdict.CANNOT_CHECK
    assert any(reason.startswith("unresolved_evidence_obligations:") for reason in result.reasons)


def test_certificate_subject_hash_is_deterministic_and_relation_bound():
    first, reg1 = _binding("obs-1", link_id="link-a")
    a = _assess(_proposal("obs-1"), (first,), (reg1,))
    b = _assess(_proposal("obs-1"), (first,), (reg1,))
    assert a.certificate is not None and b.certificate is not None
    assert a.certificate.subject_hash == b.certificate.subject_hash

    second, reg2 = _binding("obs-1", link_id="link-b")
    c = _assess(_proposal("obs-1"), (second,), (reg2,))
    assert c.certificate is not None
    assert c.certificate.subject_hash != a.certificate.subject_hash


def test_posthoc_binding_definition_is_invalid():
    binding, registration = _binding("obs-1")
    result = _assess(
        _proposal("obs-1"),
        (binding,),
        (registration,),
        frozen_before_promotion=False,
    )
    assert result.verdict is EvidenceBindingVerdict.INVALID
    assert "binding_defined_posthoc_after_promotion" in result.reasons
