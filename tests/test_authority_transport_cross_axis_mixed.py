from rakl.authority_ledger import AuthorityAxis, AuthorityCertificate
from rakl.authority_transport import (
    AuthorityTransportOperation,
    AuthorityTransportRequest,
    AuthorityTransportVerdict,
    evaluate_authority_transport,
)
from rakl.epistemic_noninterference import EvidenceRootKind
from rakl.v3_scientific_authority import ScientificEvidenceBinding


def test_mixed_source_axes_cannot_amplify_to_absent_identification_axis():
    evidence = {
        "obs-r": ScientificEvidenceBinding(
            "obs-r",
            EvidenceRootKind.EXTERNAL_OBSERVATION,
            "a" * 64,
            (AuthorityAxis.REPRESENTATION,),
        ),
        "obs-m": ScientificEvidenceBinding(
            "obs-m",
            EvidenceRootKind.EXTERNAL_OBSERVATION,
            "b" * 64,
            (AuthorityAxis.MECHANISM,),
        ),
    }
    rep = AuthorityCertificate(
        "cert-r",
        "claim-1",
        AuthorityAxis.REPRESENTATION,
        "predictive relation",
        "scope-1",
        ("obs-r",),
    )
    mech = AuthorityCertificate(
        "cert-m",
        "claim-1",
        AuthorityAxis.MECHANISM,
        "mechanism relation",
        "scope-1",
        ("obs-m",),
    )
    request = AuthorityTransportRequest(
        request_id="mixed-to-identification",
        operation=AuthorityTransportOperation.CONSOLIDATION,
        successor_claim_id="claim-1",
        successor_axis=AuthorityAxis.IDENTIFICATION,
        successor_scope_id="scope-1",
        source_certificate_ids=("cert-r", "cert-m"),
        successor_evidence_ids=("obs-r", "obs-m"),
        frozen_before_use=True,
    )

    result = evaluate_authority_transport(
        request,
        {"cert-r": rep, "cert-m": mech},
        ("cert-r", "cert-m"),
        evidence,
    )

    assert result.verdict is AuthorityTransportVerdict.INVALID
    assert any(
        reason.startswith("cross_axis_authority_amplification:")
        and reason.endswith("->IDENTIFICATION")
        for reason in result.reasons
    )
