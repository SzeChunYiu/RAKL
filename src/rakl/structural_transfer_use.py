"""Use-site hardening for ``StructuralWitness.non_preserved_properties``.

The base structural-transfer gate correctly checks relations/invariants/boundaries,
but a witness's explicit ``non_preserved_properties`` is otherwise descriptive.
This sidecar makes non-preservation load-bearing at the consumer: every known loss
must be acknowledged as irrelevant to the registered use, and every additionally
required property must carry a separate preservation receipt that has been resolved
by the caller's protected/replay assurance layer. A caller-named receipt ID alone is
not enough.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .structural_transfer import assess_transfer
from .structural_types import StructuralObject, StructuralWitness, TransferDecision


class TransferUseVerdict(str, Enum):
    LICENSED_FOR_USE = "LICENSED_FOR_USE"
    REJECTED = "REJECTED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class StructuralTransferUseContract:
    use_id: str
    qoi: str
    required_properties: frozenset[str]
    accepted_non_preserved_properties: frozenset[str]
    property_preservation_receipts: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        if not self.use_id or not self.qoi:
            raise ValueError("transfer use identity/QoI required")
        if any(not p for p in self.required_properties | self.accepted_non_preserved_properties):
            raise ValueError("property names cannot be empty")
        if self.required_properties & self.accepted_non_preserved_properties:
            raise ValueError("a property cannot be required and accepted as non-preserved")
        keys = [p for p, receipt in self.property_preservation_receipts]
        if len(keys) != len(set(keys)) or any(not p or not receipt for p, receipt in self.property_preservation_receipts):
            raise ValueError("property preservation receipts must be unique and nonempty")

    @property
    def receipt_map(self) -> dict[str, str]:
        return dict(self.property_preservation_receipts)


@dataclass(frozen=True)
class TransferUseAssessment:
    verdict: TransferUseVerdict
    reasons: tuple[str, ...]
    base_decision: TransferDecision

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def assess_transfer_for_use(
    source: StructuralObject,
    target: StructuralObject,
    witness: StructuralWitness,
    use: StructuralTransferUseContract,
    *,
    resolved_witness_evidence_ids: frozenset[str] = frozenset(),
    resolved_preservation_receipt_ids: frozenset[str] = frozenset(),
) -> TransferUseAssessment:
    base = assess_transfer(source, target, witness)
    if base.decision is TransferDecision.CANNOT_CHECK:
        return TransferUseAssessment(TransferUseVerdict.CANNOT_CHECK, base.reasons, base.decision)
    if base.decision is not TransferDecision.LICENSED:
        return TransferUseAssessment(TransferUseVerdict.REJECTED, base.reasons, base.decision)

    reasons: list[str] = []
    cannot: list[str] = []
    unresolved_witness = set(witness.evidence_ids) - set(resolved_witness_evidence_ids)
    cannot.extend(f"witness_evidence_unresolved:{item}" for item in sorted(unresolved_witness))
    if use.qoi != source.qoi or use.qoi != target.qoi:
        reasons.append("use_qoi_mismatch")
    forbidden = use.required_properties & witness.non_preserved_properties
    reasons.extend(f"required_property_explicitly_non_preserved:{p}" for p in sorted(forbidden))

    unreviewed_losses = witness.non_preserved_properties - use.accepted_non_preserved_properties
    cannot.extend(f"non_preserved_property_not_acknowledged:{p}" for p in sorted(unreviewed_losses))

    receipt_map = use.receipt_map
    missing_receipts = use.required_properties - set(receipt_map)
    cannot.extend(f"required_property_preservation_unregistered:{p}" for p in sorted(missing_receipts))
    unresolved = {
        p for p in use.required_properties & set(receipt_map)
        if receipt_map[p] not in resolved_preservation_receipt_ids
    }
    cannot.extend(f"required_property_preservation_receipt_unresolved:{p}" for p in sorted(unresolved))

    if reasons:
        return TransferUseAssessment(TransferUseVerdict.REJECTED, tuple(reasons), base.decision)
    if cannot:
        return TransferUseAssessment(TransferUseVerdict.CANNOT_CHECK, tuple(cannot), base.decision)
    return TransferUseAssessment(TransferUseVerdict.LICENSED_FOR_USE, (), base.decision)
