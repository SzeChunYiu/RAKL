"""Resolution gate for Task-Conditioned Structural Quotient validation reports.

The existing ``semantic_quotient`` module correctly separates proposal and
validation *objects*, but a caller can still instantiate a passing validation
report.  That is acceptable as a data model, but production solver use should
bind the report to a resolved verifier/replay receipt rather than treating an
enum plus evidence IDs as self-authenticating.

This sidecar is additive: it does not change historical TCSQ hashes.  It provides
a stronger materialization entry point for new integrations.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Tuple


@dataclass(frozen=True)
class ResolvedQuotientValidationReceipt:
    receipt_id: str
    validation_report_hash: str
    proposal_hash: str
    source_hash: str
    verifier_id: str
    evidence_content_hashes: Tuple[str, ...]
    resolution_class: str = "VERIFIER_REPLAY"

    def __post_init__(self) -> None:
        for name in (
            "receipt_id",
            "validation_report_hash",
            "proposal_hash",
            "source_hash",
            "verifier_id",
            "resolution_class",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if not self.evidence_content_hashes:
            raise ValueError("resolved quotient validation requires content-bound evidence")
        if any(not item.strip() for item in self.evidence_content_hashes):
            raise ValueError("evidence content hashes cannot be blank")
        if len(set(self.evidence_content_hashes)) != len(self.evidence_content_hashes):
            raise ValueError("evidence content hashes must be unique")

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def validation_receipt_matches(
    *,
    proposal: Any,
    source: Any,
    report: Any,
    receipt: ResolvedQuotientValidationReceipt,
    resolved_receipt_ids: Iterable[str],
) -> bool:
    """Return true only for an externally resolved receipt bound to exact content."""
    if receipt.receipt_id not in set(resolved_receipt_ids):
        return False
    try:
        return (
            receipt.validation_report_hash == report.content_hash
            and receipt.proposal_hash == proposal.content_hash
            and receipt.source_hash == source.source_hash
            and report.proposal_hash == proposal.content_hash
            and report.source_hash == source.source_hash
            and report.quotient_id == proposal.quotient_id
        )
    except AttributeError:
        return False


def assured_materialize_validated_quotient(
    source: Any,
    proposal: Any,
    report: Any,
    *,
    validation_receipt: ResolvedQuotientValidationReceipt,
    resolved_receipt_ids: Iterable[str],
    desired_effects: tuple[str, ...] = (),
) -> Any:
    """Materialize only after exact validation receipt resolution.

    The underlying semantic-quotient contract remains authoritative for
    partition, sufficiency, approximation and evidence checks.  This wrapper
    adds the missing trust/resolution edge; it does not mint scientific authority.
    """
    if not validation_receipt_matches(
        proposal=proposal,
        source=source,
        report=report,
        receipt=validation_receipt,
        resolved_receipt_ids=resolved_receipt_ids,
    ):
        raise ValueError("quotient_validation_receipt_unresolved_or_content_mismatched")
    from .semantic_quotient import materialize_validated_quotient

    return materialize_validated_quotient(
        source,
        proposal,
        report,
        desired_effects=desired_effects,
    )
