"""I/O helpers for content-bound mechanic research packet sets.

This module is intentionally shadow-only. Loading a valid packet set does not
change the existing promotion gate and grants no scientific or promotion
authority. It exists so preregistered packet artifacts can be checked by CI
without inventing outcome states.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Tuple

from .mechanic_research_packet import (
    ApplicabilityGateState,
    MechanicResearchCoverageReport,
    MechanicResearchPacket,
    MechanicResearchPacketVerdict,
    MechanismGateState,
    StrongestParentSpec,
    audit_mechanic_research_packet_coverage,
    validate_mechanic_research_packet,
)


PACKET_SET_SCHEMA_VERSION = "p5-p6-mechanic-research-packet-set-v1"


def strongest_parent_from_dict(document: Mapping[str, Any]) -> StrongestParentSpec:
    return StrongestParentSpec(
        parent_id=str(document["parent_id"]),
        implementation_refs=tuple(str(item) for item in document["implementation_refs"]),
        cost_model_id=str(document["cost_model_id"]),
        cost_equation=str(document["cost_equation"]),
        justification=str(document["justification"]),
        evidence_pointers=tuple(str(item) for item in document.get("evidence_pointers", ())),
    )


def packet_from_dict(document: Mapping[str, Any]) -> MechanicResearchPacket:
    """Reconstruct one frozen packet without recomputing or mutating its hash."""

    return MechanicResearchPacket(
        packet_id=str(document["packet_id"]),
        mechanic_id=str(document["mechanic_id"]),
        variant_id=str(document["variant_id"]),
        parent_method_sha=str(document["parent_method_sha"]),
        object_description=str(document["object_description"]),
        qoi=str(document["qoi"]),
        scope=tuple(str(item) for item in document["scope"]),
        assumptions=tuple(str(item) for item in document["assumptions"]),
        strongest_parents=tuple(
            strongest_parent_from_dict(item) for item in document["strongest_parents"]
        ),
        prior_art_equivalence_map=tuple(
            str(item) for item in document["prior_art_equivalence_map"]
        ),
        oracle_or_lower_bound=str(document["oracle_or_lower_bound"]),
        minimal_counterexamples=tuple(str(item) for item in document["minimal_counterexamples"]),
        development_benchmark_id=str(document["development_benchmark_id"]),
        development_case_ids=tuple(str(item) for item in document["development_case_ids"]),
        fresh_assurance_benchmark_id=str(document["fresh_assurance_benchmark_id"]),
        fresh_assurance_case_ids=tuple(str(item) for item in document["fresh_assurance_case_ids"]),
        selection_case_ids=tuple(str(item) for item in document["selection_case_ids"]),
        falsifier=str(document["falsifier"]),
        same_system_ablation=str(document["same_system_ablation"]),
        hard_gate_obligations=tuple(str(item) for item in document["hard_gate_obligations"]),
        required_telemetry_fields=tuple(str(item) for item in document["required_telemetry_fields"]),
        total_cost_equation=str(document["total_cost_equation"]),
        novelty_residual=str(document["novelty_residual"]),
        permitted_publication_claim=str(document["permitted_publication_claim"]),
        evidence_pointers=tuple(str(item) for item in document["evidence_pointers"]),
        mechanism_gate_state=MechanismGateState(str(document["mechanism_gate_state"])),
        applicability_gate_state=ApplicabilityGateState(str(document["applicability_gate_state"])),
        frozen_before_implementation=bool(document["frozen_before_implementation"]),
        frozen_before_outcome_access=bool(document["frozen_before_outcome_access"]),
        packet_content_sha256=str(document["packet_content_sha256"]),
        schema_version=str(document["schema_version"]),
    )


@dataclass(frozen=True)
class MechanicResearchPacketSet:
    schema_version: str
    scientific_parent_sha: str
    packet_contract_merge_sha: str
    campaign_issue: str
    campaign_freeze_comment_id: str
    required_variant_ids: Tuple[str, ...]
    packets: Tuple[MechanicResearchPacket, ...]
    notes: Tuple[str, ...]

    def __post_init__(self) -> None:
        if self.schema_version != PACKET_SET_SCHEMA_VERSION:
            raise ValueError("unsupported packet-set schema version")
        if len(self.required_variant_ids) != len(set(self.required_variant_ids)):
            raise ValueError("required variant ids must be unique")
        if not self.scientific_parent_sha or not self.packet_contract_merge_sha:
            raise ValueError("packet set requires frozen scientific and packet-contract subjects")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_promotion_authority(self) -> bool:
        return False

    def coverage_report(self) -> MechanicResearchCoverageReport:
        return audit_mechanic_research_packet_coverage(self.required_variant_ids, self.packets)


def packet_set_from_dict(document: Mapping[str, Any]) -> MechanicResearchPacketSet:
    for forbidden in (
        "grants_scientific_authority",
        "grants_promotion_authority",
        "enforces_promotion_gate",
    ):
        if document.get(forbidden) is not False:
            raise ValueError(f"packet set must explicitly declare {forbidden}=false")
    return MechanicResearchPacketSet(
        schema_version=str(document["schema_version"]),
        scientific_parent_sha=str(document["scientific_parent_sha"]),
        packet_contract_merge_sha=str(document["packet_contract_merge_sha"]),
        campaign_issue=str(document["campaign_issue"]),
        campaign_freeze_comment_id=str(document["campaign_freeze_comment_id"]),
        required_variant_ids=tuple(str(item) for item in document["required_variant_ids"]),
        packets=tuple(packet_from_dict(item) for item in document["packets"]),
        notes=tuple(str(item) for item in document.get("notes", ())),
    )


def load_packet_set(path: str | Path) -> MechanicResearchPacketSet:
    with Path(path).open("r", encoding="utf-8") as handle:
        document = json.load(handle)
    if not isinstance(document, dict):
        raise ValueError("packet-set root must be an object")
    return packet_set_from_dict(document)


def validate_packet_set(packet_set: MechanicResearchPacketSet) -> Tuple[str, ...]:
    """Return fail-closed reasons; empty means 100% shadow preregistration coverage."""

    reasons: list[str] = []
    if not packet_set.required_variant_ids:
        reasons.append("required_variant_universe_missing")
    if not packet_set.packets:
        reasons.append("packets_missing")
    packet_ids = [packet.packet_id for packet in packet_set.packets]
    if len(packet_ids) != len(set(packet_ids)):
        reasons.append("duplicate_packet_id")
    for packet in packet_set.packets:
        report = validate_mechanic_research_packet(packet)
        if report.verdict is not MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE:
            reasons.extend(f"{packet.variant_id}:{reason}" for reason in report.reasons)
    coverage = packet_set.coverage_report()
    if not coverage.complete:
        reasons.extend(coverage.reasons)
    return tuple(reasons)
