from dataclasses import dataclass

from rakl.semantic_quotient_assurance import (
    ResolvedQuotientValidationReceipt,
    validation_receipt_matches,
)


@dataclass(frozen=True)
class Obj:
    content_hash: str = "hash"
    source_hash: str = "source"
    proposal_hash: str = "hash"
    quotient_id: str = "q"


def test_validation_receipt_must_resolve_and_bind_every_identity() -> None:
    source = Obj(content_hash="source-content", source_hash="source")
    proposal = Obj(content_hash="proposal", source_hash="source", quotient_id="q")
    report = Obj(
        content_hash="report",
        source_hash="source",
        proposal_hash="proposal",
        quotient_id="q",
    )
    receipt = ResolvedQuotientValidationReceipt(
        receipt_id="receipt",
        validation_report_hash="report",
        proposal_hash="proposal",
        source_hash="source",
        verifier_id="kernel-replay",
        evidence_content_hashes=("sha256:evidence",),
    )
    assert not validation_receipt_matches(
        proposal=proposal,
        source=source,
        report=report,
        receipt=receipt,
        resolved_receipt_ids=(),
    )
    assert validation_receipt_matches(
        proposal=proposal,
        source=source,
        report=report,
        receipt=receipt,
        resolved_receipt_ids=("receipt",),
    )


def test_validation_receipt_content_mismatch_fails_closed() -> None:
    source = Obj(content_hash="source-content", source_hash="source")
    proposal = Obj(content_hash="proposal", source_hash="source", quotient_id="q")
    report = Obj(content_hash="report", source_hash="source", proposal_hash="proposal", quotient_id="q")
    bad = ResolvedQuotientValidationReceipt(
        receipt_id="receipt",
        validation_report_hash="wrong",
        proposal_hash="proposal",
        source_hash="source",
        verifier_id="kernel-replay",
        evidence_content_hashes=("sha256:evidence",),
    )
    assert not validation_receipt_matches(
        proposal=proposal,
        source=source,
        report=report,
        receipt=bad,
        resolved_receipt_ids=("receipt",),
    )
