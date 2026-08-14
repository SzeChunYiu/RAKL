"""Fail-closed strongest-formal-parent arbitration for Paper II.

This module does *not* implement causal transportability.  It encodes the
claim/routing boundary discovered by the Paper-II nearest-work audit: when a
registered formal parent already decides a transfer problem inside its own
scope, ORION may not override or rename that result as an ORION contribution.

The intended first parent is the Bareinboim/Pearl sID transportability family.
A future adapter can bind an actual formal-parent implementation to this
interface.  Until then, this module is a conformance/novelty boundary only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class TransferVerdict(str, Enum):
    LICENSED = "LICENSED"
    REJECTED = "REJECTED"
    CANNOT_CHECK = "CANNOT_CHECK"


class FormalParentDisposition(str, Enum):
    LICENSED = "LICENSED"
    REJECTED = "REJECTED"
    CANNOT_CHECK = "CANNOT_CHECK"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


def _is_sha256(value: object) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(ch in "0123456789abcdef" for ch in value)
    )


@dataclass(frozen=True)
class FormalParentResult:
    method_id: str
    method_version: str
    subject_sha256: str
    disposition: FormalParentDisposition
    derivation_sha256: str | None = None


@dataclass(frozen=True)
class TransferArbitration:
    verdict: TransferVerdict
    authority_source: str
    parent_disposition: FormalParentDisposition
    orion_verdict: TransferVerdict
    reasons: Tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def orion_residual_eligible(self) -> bool:
        """True only when the registered formal parent is explicitly out of scope."""
        return self.authority_source == "ORION_OUTSIDE_FORMAL_PARENT_SCOPE"


DEFAULT_PARENT_ID = "bareinboim-pearl-sid-family"
DEFAULT_PARENT_VERSION = "transportability-parent-boundary-v1"


def arbitrate_transfer(
    parent: FormalParentResult,
    orion_verdict: TransferVerdict,
    *,
    expected_subject_sha256: str,
    expected_parent_id: str = DEFAULT_PARENT_ID,
    expected_parent_version: str = DEFAULT_PARENT_VERSION,
) -> TransferArbitration:
    """Arbitrate a formal-parent result against an ORION transfer verdict.

    Decisive formal results dominate inside the exact bound subject.  A formal
    ``CANNOT_CHECK`` remains an abstention.  ORION is consulted only when the
    formal parent explicitly says the object is outside its registered scope.

    This is intentionally asymmetric: disagreement is diagnostic evidence, not
    a voting scheme.  A weaker or broader heuristic may not overturn a complete
    formal parent on the parent's own object class.
    """

    reasons: list[str] = []
    if parent.method_id != expected_parent_id:
        reasons.append("formal_parent_method_id_mismatch")
    if parent.method_version != expected_parent_version:
        reasons.append("formal_parent_method_version_mismatch")
    if not _is_sha256(expected_subject_sha256):
        reasons.append("expected_subject_sha256_invalid")
    if not _is_sha256(parent.subject_sha256):
        reasons.append("formal_parent_subject_sha256_invalid")
    elif _is_sha256(expected_subject_sha256) and parent.subject_sha256 != expected_subject_sha256:
        reasons.append("formal_parent_subject_mismatch")

    decisive = parent.disposition in {
        FormalParentDisposition.LICENSED,
        FormalParentDisposition.REJECTED,
    }
    if decisive and not _is_sha256(parent.derivation_sha256):
        reasons.append("formal_parent_decisive_result_missing_derivation_digest")
    if parent.disposition in {
        FormalParentDisposition.CANNOT_CHECK,
        FormalParentDisposition.OUT_OF_SCOPE,
    } and parent.derivation_sha256 is not None and not _is_sha256(parent.derivation_sha256):
        reasons.append("formal_parent_derivation_digest_invalid")

    if reasons:
        return TransferArbitration(
            verdict=TransferVerdict.CANNOT_CHECK,
            authority_source="BOUNDARY_VALIDATION_FAILURE",
            parent_disposition=parent.disposition,
            orion_verdict=orion_verdict,
            reasons=tuple(sorted(set(reasons))),
        )

    if parent.disposition is FormalParentDisposition.LICENSED:
        return TransferArbitration(
            verdict=TransferVerdict.LICENSED,
            authority_source="FORMAL_PARENT",
            parent_disposition=parent.disposition,
            orion_verdict=orion_verdict,
            reasons=(
                "formal_parent_decisive_inside_registered_scope",
                "orion_disagreement_is_diagnostic_only" if orion_verdict is not TransferVerdict.LICENSED else "orion_agrees",
            ),
        )

    if parent.disposition is FormalParentDisposition.REJECTED:
        return TransferArbitration(
            verdict=TransferVerdict.REJECTED,
            authority_source="FORMAL_PARENT",
            parent_disposition=parent.disposition,
            orion_verdict=orion_verdict,
            reasons=(
                "formal_parent_decisive_inside_registered_scope",
                "orion_disagreement_is_diagnostic_only" if orion_verdict is not TransferVerdict.REJECTED else "orion_agrees",
            ),
        )

    if parent.disposition is FormalParentDisposition.CANNOT_CHECK:
        return TransferArbitration(
            verdict=TransferVerdict.CANNOT_CHECK,
            authority_source="FORMAL_PARENT",
            parent_disposition=parent.disposition,
            orion_verdict=orion_verdict,
            reasons=("formal_parent_cannot_check_fails_closed",),
        )

    return TransferArbitration(
        verdict=orion_verdict,
        authority_source="ORION_OUTSIDE_FORMAL_PARENT_SCOPE",
        parent_disposition=parent.disposition,
        orion_verdict=orion_verdict,
        reasons=("formal_parent_explicitly_out_of_scope",),
    )
