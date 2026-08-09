from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PublicationGateVerdict(str, Enum):
    NOT_SUBMISSION_READY = "NOT_SUBMISSION_READY"
    REJECT = "REJECT"
    SCOPED_SUBMISSION_READY = "SCOPED_SUBMISSION_READY"


@dataclass(frozen=True)
class PublicationGatePacket:
    manuscript_text: str
    required_result_ids: tuple[str, ...]
    receipted_result_ids: tuple[str, ...]
    quant_real_result_receipted: bool
    self_evolution_fresh_assurance_receipted: bool
    matched_workflow_receipted: bool
    independent_method_review: bool
    independent_quant_review: bool
    independent_artifact_reproduction: bool
    figures_tables_from_receipts: bool
    release_manifest_verified: bool
    code_data_availability_ready: bool
    ai_use_disclosure_ready: bool
    hand_entered_headline_numbers_detected: bool = False
    blocking_failures: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.manuscript_text:
            raise ValueError("manuscript_text cannot be empty")
        if len(set(self.required_result_ids)) != len(self.required_result_ids):
            raise ValueError("required_result_ids must be unique")
        if len(set(self.receipted_result_ids)) != len(self.receipted_result_ids):
            raise ValueError("receipted_result_ids must be unique")


@dataclass(frozen=True)
class PublicationGateReport:
    verdict: PublicationGateVerdict
    reasons: tuple[str, ...]
    unresolved_result_ids: tuple[str, ...]
    unresolved_manuscript_slots: tuple[str, ...]
    scientific_truth_authority: bool = False

    @property
    def submission_ready(self) -> bool:
        return self.verdict == PublicationGateVerdict.SCOPED_SUBMISSION_READY


def _result_slots(text: str) -> tuple[str, ...]:
    marker = "[[RESULT:"
    slots: list[str] = []
    start = 0
    while True:
        i = text.find(marker, start)
        if i < 0:
            break
        j = text.find("]]", i + len(marker))
        if j < 0:
            slots.append("MALFORMED_RESULT_SLOT")
            break
        ident = text[i + len(marker) : j].strip()
        slots.append(ident or "EMPTY_RESULT_SLOT")
        start = j + 2
    return tuple(slots)


def evaluate_publication_gate(packet: PublicationGatePacket) -> PublicationGateReport:
    slots = _result_slots(packet.manuscript_text)
    required = set(packet.required_result_ids)
    receipted = set(packet.receipted_result_ids)
    unresolved_ids = tuple(sorted(required - receipted))
    unresolved_slots = tuple(sorted(set(slots)))

    rejection_reasons: list[str] = []
    if packet.hand_entered_headline_numbers_detected:
        rejection_reasons.append("hand-entered headline result detected")
    rejection_reasons.extend(
        f"blocking validity failure: {failure}" for failure in packet.blocking_failures
    )
    if rejection_reasons:
        return PublicationGateReport(
            verdict=PublicationGateVerdict.REJECT,
            reasons=tuple(rejection_reasons),
            unresolved_result_ids=unresolved_ids,
            unresolved_manuscript_slots=unresolved_slots,
        )

    reasons: list[str] = []
    if unresolved_ids:
        reasons.append("required result receipts are missing")
    if unresolved_slots:
        reasons.append("blocking manuscript result slots remain")
    if not packet.quant_real_result_receipted:
        reasons.append("real quant-science result is not receipted")
    if not packet.self_evolution_fresh_assurance_receipted:
        reasons.append("fresh-assurance self-evolution result is not receipted")
    if not packet.matched_workflow_receipted:
        reasons.append("matched research-workflow comparison is not receipted")
    if not packet.independent_method_review:
        reasons.append("independent method/novelty review missing")
    if not packet.independent_quant_review:
        reasons.append("independent quant/statistics review missing")
    if not packet.independent_artifact_reproduction:
        reasons.append("independent artifact reproduction missing")
    if not packet.figures_tables_from_receipts:
        reasons.append("figures/tables are not fully generated from receipts")
    if not packet.release_manifest_verified:
        reasons.append("final release manifest is not verified")
    if not packet.code_data_availability_ready:
        reasons.append("code/data availability package incomplete")
    if not packet.ai_use_disclosure_ready:
        reasons.append("AI-use disclosure incomplete")

    if reasons:
        return PublicationGateReport(
            verdict=PublicationGateVerdict.NOT_SUBMISSION_READY,
            reasons=tuple(reasons),
            unresolved_result_ids=unresolved_ids,
            unresolved_manuscript_slots=unresolved_slots,
        )

    return PublicationGateReport(
        verdict=PublicationGateVerdict.SCOPED_SUBMISSION_READY,
        reasons=("all registered result, fresh-assurance, independent-review and artifact gates are represented as satisfied",),
        unresolved_result_ids=(),
        unresolved_manuscript_slots=(),
    )
