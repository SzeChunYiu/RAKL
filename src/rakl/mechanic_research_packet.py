"""Fail-closed preregistration contract for promotable mechanic variants.

This module implements the parent/oracle/counterexample research packet required
by RAKL issue #546.  It deliberately does *not* score outcomes and does not
replace ``scripts/promotion_gate.py``.  Its only job is to establish whether a
mechanic variant has a content-bound, chronologically valid research packet that
may be handed to the existing promotion/evaluation machinery.

A valid packet is proposal-only.  It grants neither scientific authority nor
method-promotion authority.  Outcome-dependent mechanism/applicability states
must remain UNASSESSED in the frozen preregistration packet; later evidence is
owned by the existing promotion gate and protected governance path.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Any, Mapping, Tuple


PACKET_SCHEMA_VERSION = "mechanic-research-packet-v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class MechanismGateState(str, Enum):
    """Outcome state referenced by the packet, never decided by this module."""

    UNASSESSED = "UNASSESSED"
    MECHANISM_SUPPORTED = "MECHANISM_SUPPORTED"
    MECHANISM_CONDITIONALLY_SUPPORTED = "MECHANISM_CONDITIONALLY_SUPPORTED"
    MECHANISM_NOT_SUPPORTED = "MECHANISM_NOT_SUPPORTED"
    CANNOT_CHECK = "CANNOT_CHECK"


class ApplicabilityGateState(str, Enum):
    """Outcome applicability state referenced by the packet."""

    UNASSESSED = "UNASSESSED"
    UNCONDITIONAL = "UNCONDITIONAL"
    CONDITIONAL = "CONDITIONAL"
    BASELINE_ONLY = "BASELINE_ONLY"
    CANNOT_CHECK = "CANNOT_CHECK"


class MechanicResearchPacketVerdict(str, Enum):
    READY_FOR_EXISTING_PROMOTION_GATE = "READY_FOR_EXISTING_PROMOTION_GATE"
    PROPOSAL_ONLY_INCOMPLETE = "PROPOSAL_ONLY_INCOMPLETE"
    INVALID_CHRONOLOGY = "INVALID_CHRONOLOGY"
    CANNOT_CHECK = "CANNOT_CHECK"


class MechanicResearchCoverageVerdict(str, Enum):
    COMPLETE_SHADOW_COVERAGE = "COMPLETE_SHADOW_COVERAGE"
    INCOMPLETE_SHADOW_COVERAGE = "INCOMPLETE_SHADOW_COVERAGE"
    CANNOT_CHECK = "CANNOT_CHECK"


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _packet_hash(document: Mapping[str, Any]) -> str:
    subject = dict(document)
    subject.pop("packet_content_sha256", None)
    return canonical_sha256(subject)


@dataclass(frozen=True)
class StrongestParentSpec:
    """One strongest known parent/control that the challenger must beat or match."""

    parent_id: str
    implementation_refs: Tuple[str, ...]
    cost_model_id: str
    cost_equation: str
    justification: str
    evidence_pointers: Tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent_id": self.parent_id,
            "implementation_refs": list(self.implementation_refs),
            "cost_model_id": self.cost_model_id,
            "cost_equation": self.cost_equation,
            "justification": self.justification,
            "evidence_pointers": list(self.evidence_pointers),
        }


@dataclass(frozen=True)
class MechanicResearchPacket:
    """Frozen, content-bound preregistration for one mechanic variant.

    ``selection_case_ids`` may overlap the development cases because development
    is where a challenger may be selected/refined.  It must be disjoint from the
    fresh assurance cases.  The fresh set is therefore not available for variant
    selection or repair.
    """

    packet_id: str
    mechanic_id: str
    variant_id: str
    parent_method_sha: str
    object_description: str
    qoi: str
    scope: Tuple[str, ...]
    assumptions: Tuple[str, ...]
    strongest_parents: Tuple[StrongestParentSpec, ...]
    prior_art_equivalence_map: Tuple[str, ...]
    oracle_or_lower_bound: str
    minimal_counterexamples: Tuple[str, ...]
    development_benchmark_id: str
    development_case_ids: Tuple[str, ...]
    fresh_assurance_benchmark_id: str
    fresh_assurance_case_ids: Tuple[str, ...]
    selection_case_ids: Tuple[str, ...]
    falsifier: str
    same_system_ablation: str
    hard_gate_obligations: Tuple[str, ...]
    required_telemetry_fields: Tuple[str, ...]
    total_cost_equation: str
    novelty_residual: str
    permitted_publication_claim: str
    evidence_pointers: Tuple[str, ...]
    mechanism_gate_state: MechanismGateState = MechanismGateState.UNASSESSED
    applicability_gate_state: ApplicabilityGateState = ApplicabilityGateState.UNASSESSED
    frozen_before_implementation: bool = True
    frozen_before_outcome_access: bool = True
    packet_content_sha256: str = ""
    schema_version: str = field(default=PACKET_SCHEMA_VERSION)

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packet_id": self.packet_id,
            "mechanic_id": self.mechanic_id,
            "variant_id": self.variant_id,
            "parent_method_sha": self.parent_method_sha,
            "object_description": self.object_description,
            "qoi": self.qoi,
            "scope": list(self.scope),
            "assumptions": list(self.assumptions),
            "strongest_parents": [parent.to_dict() for parent in self.strongest_parents],
            "prior_art_equivalence_map": list(self.prior_art_equivalence_map),
            "oracle_or_lower_bound": self.oracle_or_lower_bound,
            "minimal_counterexamples": list(self.minimal_counterexamples),
            "development_benchmark_id": self.development_benchmark_id,
            "development_case_ids": list(self.development_case_ids),
            "fresh_assurance_benchmark_id": self.fresh_assurance_benchmark_id,
            "fresh_assurance_case_ids": list(self.fresh_assurance_case_ids),
            "selection_case_ids": list(self.selection_case_ids),
            "falsifier": self.falsifier,
            "same_system_ablation": self.same_system_ablation,
            "hard_gate_obligations": list(self.hard_gate_obligations),
            "required_telemetry_fields": list(self.required_telemetry_fields),
            "total_cost_equation": self.total_cost_equation,
            "novelty_residual": self.novelty_residual,
            "permitted_publication_claim": self.permitted_publication_claim,
            "evidence_pointers": list(self.evidence_pointers),
            "mechanism_gate_state": self.mechanism_gate_state.value,
            "applicability_gate_state": self.applicability_gate_state.value,
            "frozen_before_implementation": self.frozen_before_implementation,
            "frozen_before_outcome_access": self.frozen_before_outcome_access,
            "packet_content_sha256": self.packet_content_sha256,
            "grants_scientific_authority": False,
            "grants_promotion_authority": False,
            "replaces_promotion_gate": False,
        }

    def with_content_hash(self) -> "MechanicResearchPacket":
        return replace(self, packet_content_sha256=_packet_hash(self.to_dict()))

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_promotion_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class MechanicResearchPacketReport:
    verdict: MechanicResearchPacketVerdict
    eligible_for_existing_promotion_gate: bool
    reasons: Tuple[str, ...]
    packet_id: str | None
    mechanic_id: str | None
    variant_id: str | None
    packet_content_sha256: str | None

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_promotion_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class MechanicResearchCoverageReport:
    verdict: MechanicResearchCoverageVerdict
    required_variant_ids: Tuple[str, ...]
    valid_variant_ids: Tuple[str, ...]
    invalid_variant_ids: Tuple[str, ...]
    missing_variant_ids: Tuple[str, ...]
    reasons: Tuple[str, ...]

    @property
    def complete(self) -> bool:
        return self.verdict is MechanicResearchCoverageVerdict.COMPLETE_SHADOW_COVERAGE

    @property
    def grants_promotion_authority(self) -> bool:
        return False


def _duplicates(values: Tuple[str, ...]) -> bool:
    return len(set(values)) != len(values)


def _missing_text(name: str, value: str, reasons: list[str]) -> None:
    if not (value or "").strip():
        reasons.append(f"{name}_missing")


def validate_mechanic_research_packet(
    packet: MechanicResearchPacket | None,
) -> MechanicResearchPacketReport:
    """Validate preregistration completeness and chronology, never the outcome.

    A READY report means only that the packet is structurally eligible to be
    consumed by the *existing* promotion/evaluation path.  It is not a positive
    evidence result.
    """

    if packet is None:
        return MechanicResearchPacketReport(
            MechanicResearchPacketVerdict.CANNOT_CHECK,
            False,
            ("mechanic_research_packet_missing",),
            None,
            None,
            None,
            None,
        )

    missing: list[str] = []
    chronology: list[str] = []
    integrity: list[str] = []

    if packet.schema_version != PACKET_SCHEMA_VERSION:
        integrity.append("schema_version_unsupported")

    for name in (
        "packet_id",
        "mechanic_id",
        "variant_id",
        "object_description",
        "qoi",
        "oracle_or_lower_bound",
        "development_benchmark_id",
        "fresh_assurance_benchmark_id",
        "falsifier",
        "same_system_ablation",
        "total_cost_equation",
        "novelty_residual",
        "permitted_publication_claim",
    ):
        _missing_text(name, str(getattr(packet, name)), missing)

    if not _GIT_SHA_RE.match(packet.parent_method_sha or ""):
        integrity.append("parent_method_sha_must_be_full_git_sha")

    for name, values in (
        ("scope", packet.scope),
        ("assumptions", packet.assumptions),
        ("prior_art_equivalence_map", packet.prior_art_equivalence_map),
        ("minimal_counterexamples", packet.minimal_counterexamples),
        ("development_case_ids", packet.development_case_ids),
        ("fresh_assurance_case_ids", packet.fresh_assurance_case_ids),
        ("selection_case_ids", packet.selection_case_ids),
        ("hard_gate_obligations", packet.hard_gate_obligations),
        ("required_telemetry_fields", packet.required_telemetry_fields),
        ("evidence_pointers", packet.evidence_pointers),
    ):
        if not values:
            missing.append(f"{name}_missing")
        elif _duplicates(values):
            integrity.append(f"{name}_contains_duplicates")

    if not packet.strongest_parents:
        missing.append("strongest_parents_missing")
    else:
        parent_ids: list[str] = []
        for index, parent in enumerate(packet.strongest_parents):
            prefix = f"strongest_parent_{index}"
            parent_ids.append(parent.parent_id)
            if not parent.parent_id.strip():
                missing.append(f"{prefix}_id_missing")
            if not parent.implementation_refs:
                missing.append(f"{prefix}_implementation_refs_missing")
            if not parent.cost_model_id.strip():
                missing.append(f"{prefix}_cost_model_missing")
            if not parent.cost_equation.strip():
                missing.append(f"{prefix}_cost_equation_missing")
            if not parent.justification.strip():
                missing.append(f"{prefix}_justification_missing")
        if len(set(parent_ids)) != len(parent_ids):
            integrity.append("strongest_parent_ids_not_unique")

    development = set(packet.development_case_ids)
    fresh = set(packet.fresh_assurance_case_ids)
    selection = set(packet.selection_case_ids)
    if development & fresh:
        chronology.append("development_and_fresh_assurance_cases_overlap")
    if selection & fresh:
        chronology.append("selection_and_fresh_assurance_cases_overlap")
    if selection and not selection.issubset(development):
        chronology.append("selection_cases_must_be_subset_of_development_cases")
    if not packet.frozen_before_implementation:
        chronology.append("packet_not_frozen_before_implementation")
    if not packet.frozen_before_outcome_access:
        chronology.append("packet_not_frozen_before_outcome_access")
    if packet.mechanism_gate_state is not MechanismGateState.UNASSESSED:
        chronology.append("preregistration_packet_cannot_contain_outcome_mechanism_state")
    if packet.applicability_gate_state is not ApplicabilityGateState.UNASSESSED:
        chronology.append("preregistration_packet_cannot_contain_outcome_applicability_state")

    if not packet.packet_content_sha256:
        missing.append("packet_content_sha256_missing")
    elif not _SHA256_RE.match(packet.packet_content_sha256):
        integrity.append("packet_content_sha256_malformed")
    elif _packet_hash(packet.to_dict()) != packet.packet_content_sha256:
        integrity.append("packet_content_sha256_mismatch")

    reasons = tuple(missing + chronology + integrity)
    if chronology:
        verdict = MechanicResearchPacketVerdict.INVALID_CHRONOLOGY
    elif integrity:
        verdict = MechanicResearchPacketVerdict.CANNOT_CHECK
    elif missing:
        verdict = MechanicResearchPacketVerdict.PROPOSAL_ONLY_INCOMPLETE
    else:
        verdict = MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE

    return MechanicResearchPacketReport(
        verdict=verdict,
        eligible_for_existing_promotion_gate=(
            verdict is MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE
        ),
        reasons=reasons,
        packet_id=packet.packet_id,
        mechanic_id=packet.mechanic_id,
        variant_id=packet.variant_id,
        packet_content_sha256=packet.packet_content_sha256 or None,
    )


def audit_mechanic_research_packet_coverage(
    required_variant_ids: Tuple[str, ...],
    packets: Tuple[MechanicResearchPacket, ...],
) -> MechanicResearchCoverageReport:
    """Shadow-only coverage audit for a declared promotable-variant universe."""

    if not required_variant_ids:
        return MechanicResearchCoverageReport(
            MechanicResearchCoverageVerdict.CANNOT_CHECK,
            (),
            (),
            (),
            (),
            ("required_variant_universe_missing",),
        )
    if _duplicates(required_variant_ids):
        return MechanicResearchCoverageReport(
            MechanicResearchCoverageVerdict.CANNOT_CHECK,
            required_variant_ids,
            (),
            (),
            (),
            ("required_variant_universe_contains_duplicates",),
        )

    by_variant: dict[str, MechanicResearchPacket] = {}
    duplicate_packets: set[str] = set()
    for packet in packets:
        if packet.variant_id in by_variant:
            duplicate_packets.add(packet.variant_id)
        else:
            by_variant[packet.variant_id] = packet

    valid: list[str] = []
    invalid: list[str] = []
    missing: list[str] = []
    reasons: list[str] = []
    required_set = set(required_variant_ids)

    for variant_id in required_variant_ids:
        packet = by_variant.get(variant_id)
        if packet is None:
            missing.append(variant_id)
            reasons.append(f"missing_packet:{variant_id}")
            continue
        if variant_id in duplicate_packets:
            invalid.append(variant_id)
            reasons.append(f"duplicate_packets:{variant_id}")
            continue
        report = validate_mechanic_research_packet(packet)
        if report.eligible_for_existing_promotion_gate:
            valid.append(variant_id)
        else:
            invalid.append(variant_id)
            reasons.extend(f"{variant_id}:{reason}" for reason in report.reasons)

    unregistered = sorted(set(by_variant) - required_set)
    reasons.extend(f"packet_outside_required_universe:{variant_id}" for variant_id in unregistered)

    if missing or invalid:
        verdict = MechanicResearchCoverageVerdict.INCOMPLETE_SHADOW_COVERAGE
    else:
        verdict = MechanicResearchCoverageVerdict.COMPLETE_SHADOW_COVERAGE

    return MechanicResearchCoverageReport(
        verdict=verdict,
        required_variant_ids=required_variant_ids,
        valid_variant_ids=tuple(valid),
        invalid_variant_ids=tuple(invalid),
        missing_variant_ids=tuple(missing),
        reasons=tuple(reasons),
    )
