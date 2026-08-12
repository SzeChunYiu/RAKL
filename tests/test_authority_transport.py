from rakl.authority_ledger import AuthorityAxis, AuthorityCertificate
from rakl.authority_transport import (
    AuthorityTransportOperation,
    AuthorityTransportRequest,
    AuthorityTransportVerdict,
    PropagationAction,
    evaluate_authority_transport,
    plan_revocation_propagation,
)
from rakl.epistemic_noninterference import EvidenceRootKind
from rakl.v3_scientific_authority import ScientificEvidenceBinding


def _evidence(evidence_id, *, upstream=None, axis=AuthorityAxis.MECHANISM):
    return ScientificEvidenceBinding(
        evidence_id=evidence_id,
        kind=EvidenceRootKind.EXTERNAL_OBSERVATION if upstream is None else EvidenceRootKind.DERIVED_REPORT,
        content_sha256=(evidence_id.encode().hex() + "0" * 64)[:64],
        supports_axes=(axis,),
        upstream_evidence_id=upstream,
    )


def _cert(
    certificate_id,
    *,
    claim="claim-1",
    axis=AuthorityAxis.MECHANISM,
    scope="regime-A",
    evidence=("obs-1",),
):
    return AuthorityCertificate(
        certificate_id=certificate_id,
        claim_id=claim,
        axis=axis,
        proposition="mechanism proposition",
        scope_id=scope,
        evidence_ids=tuple(evidence),
    )


def _request(
    *,
    operation=AuthorityTransportOperation.CONSOLIDATION,
    claim="claim-1",
    axis=AuthorityAxis.MECHANISM,
    scope="regime-A",
    sources=("cert-1",),
    evidence=("obs-1",),
    frozen=True,
):
    return AuthorityTransportRequest(
        request_id="transport-1",
        operation=operation,
        successor_claim_id=claim,
        successor_axis=axis,
        successor_scope_id=scope,
        source_certificate_ids=tuple(sources),
        successor_evidence_ids=tuple(evidence),
        frozen_before_use=frozen,
    )


def test_exact_delegation_is_non_amplifying_but_grants_no_authority():
    evidence = {"obs-1": _evidence("obs-1")}
    cert = _cert("cert-1")
    result = evaluate_authority_transport(
        _request(operation=AuthorityTransportOperation.DELEGATION),
        {cert.certificate_id: cert},
        (cert.certificate_id,),
        evidence,
    )
    assert result.verdict is AuthorityTransportVerdict.NON_AMPLIFYING_TRANSPORT_CHALLENGER
    assert result.terminal_root_ids == ("obs-1",)
    assert result.independent_root_count == 1
    assert result.grants_scientific_authority is False


def test_trusted_tool_echo_cannot_escalate_representation_to_mechanism():
    evidence = {"obs-1": _evidence("obs-1", axis=AuthorityAxis.REPRESENTATION)}
    cert = _cert("cert-1", axis=AuthorityAxis.REPRESENTATION)
    result = evaluate_authority_transport(
        _request(operation=AuthorityTransportOperation.TOOL_ECHO, axis=AuthorityAxis.MECHANISM),
        {cert.certificate_id: cert},
        (cert.certificate_id,),
        evidence,
    )
    assert result.verdict is AuthorityTransportVerdict.INVALID
    assert any(reason.startswith("cross_axis_authority_amplification:") for reason in result.reasons)


def test_scope_change_needs_verified_transport_witness():
    evidence = {"obs-1": _evidence("obs-1")}
    cert = _cert("cert-1")
    result = evaluate_authority_transport(
        _request(scope="regime-B"),
        {cert.certificate_id: cert},
        (cert.certificate_id,),
        evidence,
    )
    assert result.verdict is AuthorityTransportVerdict.CANNOT_CHECK
    assert "scope_transport_requires_verified_scope_witness" in result.reasons


def test_cross_claim_derivation_needs_verified_semantic_transport():
    evidence = {"obs-1": _evidence("obs-1")}
    cert = _cert("cert-1")
    result = evaluate_authority_transport(
        _request(operation=AuthorityTransportOperation.DERIVATION, claim="claim-derived"),
        {cert.certificate_id: cert},
        (cert.certificate_id,),
        evidence,
    )
    assert result.verdict is AuthorityTransportVerdict.CANNOT_CHECK
    assert "semantic_derivation_requires_verified_claim_transport_witness" in result.reasons


def test_transport_cannot_inject_new_evidence_or_drop_source_provenance():
    evidence = {
        "obs-1": _evidence("obs-1"),
        "obs-2": _evidence("obs-2"),
    }
    cert = _cert("cert-1", evidence=("obs-1",))

    added = evaluate_authority_transport(
        _request(evidence=("obs-1", "obs-2")),
        {cert.certificate_id: cert},
        (cert.certificate_id,),
        evidence,
    )
    assert added.verdict is AuthorityTransportVerdict.INVALID
    assert "unbound_evidence_added_during_transport:obs-2" in added.reasons

    dropped_cert = _cert("cert-2", evidence=("obs-1", "obs-2"))
    dropped = evaluate_authority_transport(
        _request(sources=("cert-2",), evidence=("obs-1",)),
        {dropped_cert.certificate_id: dropped_cert},
        (dropped_cert.certificate_id,),
        evidence,
    )
    assert dropped.verdict is AuthorityTransportVerdict.INVALID
    assert "provenance_or_support_dropped_during_transport:obs-2" in dropped.reasons


def test_derivative_echoes_count_as_one_terminal_root():
    evidence = {
        "root": _evidence("root"),
        "paper-a": _evidence("paper-a", upstream="root"),
        "paper-b": _evidence("paper-b", upstream="root"),
    }
    cert = _cert("cert-1", evidence=("paper-a", "paper-b"))
    result = evaluate_authority_transport(
        _request(sources=("cert-1",), evidence=("paper-a", "paper-b")),
        {cert.certificate_id: cert},
        (cert.certificate_id,),
        evidence,
    )
    assert result.verdict is AuthorityTransportVerdict.NON_AMPLIFYING_TRANSPORT_CHALLENGER
    assert result.terminal_root_ids == ("root",)
    assert result.independent_root_count == 1


def test_multi_axis_consolidation_cannot_be_flattened_to_one_axis():
    evidence = {
        "obs-r": _evidence("obs-r", axis=AuthorityAxis.REPRESENTATION),
        "obs-m": _evidence("obs-m", axis=AuthorityAxis.MECHANISM),
    }
    rep = _cert("cert-r", axis=AuthorityAxis.REPRESENTATION, evidence=("obs-r",))
    mech = _cert("cert-m", axis=AuthorityAxis.MECHANISM, evidence=("obs-m",))
    result = evaluate_authority_transport(
        _request(
            sources=("cert-r", "cert-m"),
            evidence=("obs-r", "obs-m"),
            axis=AuthorityAxis.MECHANISM,
        ),
        {rep.certificate_id: rep, mech.certificate_id: mech},
        (rep.certificate_id, mech.certificate_id),
        evidence,
    )
    assert result.verdict is AuthorityTransportVerdict.CANNOT_CHECK
    assert "multi_axis_transport_requires_typed_projection" in result.reasons


def test_inactive_source_certificate_cannot_be_laundered_by_consolidation():
    evidence = {"obs-1": _evidence("obs-1")}
    cert = _cert("cert-1")
    result = evaluate_authority_transport(
        _request(),
        {cert.certificate_id: cert},
        (),
        evidence,
    )
    assert result.verdict is AuthorityTransportVerdict.INVALID
    assert "source_certificate_not_active:cert-1" in result.reasons


def test_posthoc_transport_is_invalid():
    evidence = {"obs-1": _evidence("obs-1")}
    cert = _cert("cert-1")
    result = evaluate_authority_transport(
        _request(frozen=False),
        {cert.certificate_id: cert},
        (cert.certificate_id,),
        evidence,
    )
    assert result.verdict is AuthorityTransportVerdict.INVALID
    assert "transport_defined_posthoc" in result.reasons


def test_revocation_plan_revokes_when_all_support_roots_are_revoked():
    evidence = {"root": _evidence("root")}
    cert = _cert("cert-1", evidence=("root",))
    plan = plan_revocation_propagation(
        ("root",),
        {cert.certificate_id: cert},
        (cert.certificate_id,),
        evidence,
    )
    assert plan.entries[0].action is PropagationAction.REVOKE_REQUIRED
    assert plan.entries[0].affected_root_ids == ("root",)
    assert plan.entries[0].mutates_authority is False


def test_revocation_plan_requires_reevaluation_when_independent_root_remains():
    evidence = {
        "root-a": _evidence("root-a"),
        "root-b": _evidence("root-b"),
    }
    cert = _cert("cert-1", evidence=("root-a", "root-b"))
    plan = plan_revocation_propagation(
        ("root-a",),
        {cert.certificate_id: cert},
        (cert.certificate_id,),
        evidence,
    )
    assert plan.entries[0].action is PropagationAction.REEVALUATE_REQUIRED
    assert plan.entries[0].affected_root_ids == ("root-a",)
    assert plan.entries[0].remaining_root_ids == ("root-b",)


def test_revocation_of_unrelated_root_leaves_independent_certificate_unaffected():
    evidence = {
        "root-a": _evidence("root-a"),
        "root-b": _evidence("root-b"),
    }
    cert = _cert("cert-1", evidence=("root-b",))
    plan = plan_revocation_propagation(
        ("root-a",),
        {cert.certificate_id: cert},
        (cert.certificate_id,),
        evidence,
    )
    assert plan.entries[0].action is PropagationAction.UNAFFECTED
