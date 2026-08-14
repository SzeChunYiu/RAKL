"""Resolve current eligibility of immutable mechanic research packets.

A packet answers "what was frozen before this candidate was evaluated?".  This
registry answers a different, later question: "is that packet still the active
candidate basis after newer knowledge/supersession/dependency information?"
Neither object grants scientific or promotion authority.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Tuple

from .mechanic_research_packet import (
    MechanicResearchPacket,
    MechanicResearchPacketVerdict,
    validate_mechanic_research_packet,
)
from .mechanic_research_packet_io import load_packet_set, packet_from_dict


REGISTRY_SCHEMA_VERSION = "orion-active-mechanic-packet-registry-v1"


class PacketRegistryStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    BLOCKED_BASIS_EXPANDED = "BLOCKED_BASIS_EXPANDED"
    BLOCKED_DEPENDENCY = "BLOCKED_DEPENDENCY"
    CANNOT_CHECK = "CANNOT_CHECK"


class PacketSourceType(str, Enum):
    P2_PACKET_SET = "P2_PACKET_SET"
    INDIVIDUAL_JSON = "INDIVIDUAL_JSON"


@dataclass(frozen=True)
class PacketRegistryEntry:
    variant_id: str
    packet_id: str
    source_type: PacketSourceType
    source_path: str
    packet_content_sha256: str
    status: PacketRegistryStatus
    reason: str
    superseded_by: str | None = None
    replacement_family: str | None = None
    dependencies: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("variant_id", self.variant_id),
            ("packet_id", self.packet_id),
            ("source_path", self.source_path),
            ("packet_content_sha256", self.packet_content_sha256),
            ("reason", self.reason),
        ):
            if not value or not value.strip():
                raise ValueError(f"{name} is required")
        if len(self.packet_content_sha256) != 64:
            raise ValueError("packet_content_sha256 must be a sha256 hex digest")
        if self.status is PacketRegistryStatus.SUPERSEDED and not self.superseded_by:
            raise ValueError("SUPERSEDED entry requires superseded_by")
        if self.status is PacketRegistryStatus.BLOCKED_BASIS_EXPANDED and not self.replacement_family:
            raise ValueError("BLOCKED_BASIS_EXPANDED entry requires replacement_family")
        if self.status is PacketRegistryStatus.BLOCKED_DEPENDENCY and not self.dependencies:
            raise ValueError("BLOCKED_DEPENDENCY entry requires dependencies")


@dataclass(frozen=True)
class ActivePacketRegistry:
    subject_main_sha: str
    policy: str
    entries: Tuple[PacketRegistryEntry, ...]
    schema_version: str = REGISTRY_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != REGISTRY_SCHEMA_VERSION:
            raise ValueError("unsupported active packet registry schema")
        if not self.subject_main_sha.strip() or not self.policy.strip():
            raise ValueError("registry requires subject and policy")
        ids = [entry.variant_id for entry in self.entries]
        if len(ids) != len(set(ids)):
            raise ValueError("active packet registry variant ids must be unique")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_promotion_authority(self) -> bool:
        return False

    def entry_for(self, variant_id: str) -> PacketRegistryEntry | None:
        return next((entry for entry in self.entries if entry.variant_id == variant_id), None)


@dataclass(frozen=True)
class PacketEligibilityReport:
    variant_id: str
    status: PacketRegistryStatus
    eligible_for_existing_promotion_gate: bool
    reasons: Tuple[str, ...]
    packet_id: str | None = None
    packet_content_sha256: str | None = None
    superseded_by: str | None = None
    replacement_family: str | None = None
    dependencies: Tuple[str, ...] = ()

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_promotion_authority(self) -> bool:
        return False


def _entry_from_dict(document: Mapping[str, Any]) -> PacketRegistryEntry:
    return PacketRegistryEntry(
        variant_id=str(document["variant_id"]),
        packet_id=str(document["packet_id"]),
        source_type=PacketSourceType(str(document["source_type"])),
        source_path=str(document["source_path"]),
        packet_content_sha256=str(document["packet_content_sha256"]),
        status=PacketRegistryStatus(str(document["status"])),
        reason=str(document["reason"]),
        superseded_by=(None if document.get("superseded_by") is None else str(document["superseded_by"])),
        replacement_family=(None if document.get("replacement_family") is None else str(document["replacement_family"])),
        dependencies=tuple(str(item) for item in document.get("dependencies", ())),
    )


def load_active_packet_registry(path: str | Path) -> ActivePacketRegistry:
    document = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("active packet registry root must be an object")
    if document.get("grants_scientific_authority") is not False:
        raise ValueError("active packet registry must explicitly disclaim scientific authority")
    if document.get("grants_promotion_authority") is not False:
        raise ValueError("active packet registry must explicitly disclaim promotion authority")
    return ActivePacketRegistry(
        schema_version=str(document["schema_version"]),
        subject_main_sha=str(document["subject_main_sha"]),
        policy=str(document["policy"]),
        entries=tuple(_entry_from_dict(item) for item in document["entries"]),
    )


def _load_packet(entry: PacketRegistryEntry, repo_root: Path) -> MechanicResearchPacket:
    source = repo_root / entry.source_path
    if entry.source_type is PacketSourceType.P2_PACKET_SET:
        packet_set = load_packet_set(source)
        packet = next((item for item in packet_set.packets if item.variant_id == entry.variant_id), None)
        if packet is None:
            raise ValueError("registry packet variant not found in packet set")
        return packet
    document = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise ValueError("individual mechanic packet root must be an object")
    return packet_from_dict(document)


def validate_active_packet_registry(
    registry: ActivePacketRegistry,
    *,
    repo_root: str | Path,
) -> Tuple[str, ...]:
    root = Path(repo_root)
    reasons: list[str] = []
    known_ids = {entry.variant_id for entry in registry.entries}
    for entry in registry.entries:
        try:
            packet = _load_packet(entry, root)
        except Exception as exc:
            reasons.append(f"{entry.variant_id}:packet_load_failed:{type(exc).__name__}:{exc}")
            continue
        report = validate_mechanic_research_packet(packet)
        if report.verdict is not MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE:
            reasons.extend(f"{entry.variant_id}:{reason}" for reason in report.reasons)
        if packet.packet_id != entry.packet_id:
            reasons.append(f"{entry.variant_id}:packet_id_mismatch")
        if packet.packet_content_sha256 != entry.packet_content_sha256:
            reasons.append(f"{entry.variant_id}:packet_content_sha256_mismatch")
        if entry.superseded_by and entry.superseded_by not in known_ids:
            reasons.append(f"{entry.variant_id}:superseded_target_missing")
        for dependency in entry.dependencies:
            if dependency not in known_ids:
                reasons.append(f"{entry.variant_id}:dependency_missing:{dependency}")
    return tuple(reasons)


def resolve_packet_eligibility(
    variant_id: str,
    registry: ActivePacketRegistry,
    *,
    repo_root: str | Path,
) -> PacketEligibilityReport:
    entry = registry.entry_for(variant_id)
    if entry is None:
        return PacketEligibilityReport(
            variant_id=variant_id,
            status=PacketRegistryStatus.CANNOT_CHECK,
            eligible_for_existing_promotion_gate=False,
            reasons=("variant_not_registered",),
        )

    try:
        packet = _load_packet(entry, Path(repo_root))
        packet_report = validate_mechanic_research_packet(packet)
    except Exception as exc:
        return PacketEligibilityReport(
            variant_id=variant_id,
            status=PacketRegistryStatus.CANNOT_CHECK,
            eligible_for_existing_promotion_gate=False,
            reasons=(f"packet_load_failed:{type(exc).__name__}:{exc}",),
            packet_id=entry.packet_id,
            packet_content_sha256=entry.packet_content_sha256,
        )

    reasons: list[str] = []
    if packet_report.verdict is not MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE:
        reasons.extend(packet_report.reasons or (packet_report.verdict.value,))
    if packet.packet_id != entry.packet_id:
        reasons.append("packet_id_mismatch")
    if packet.packet_content_sha256 != entry.packet_content_sha256:
        reasons.append("packet_content_sha256_mismatch")

    if reasons:
        return PacketEligibilityReport(
            variant_id=variant_id,
            status=PacketRegistryStatus.CANNOT_CHECK,
            eligible_for_existing_promotion_gate=False,
            reasons=tuple(reasons),
            packet_id=entry.packet_id,
            packet_content_sha256=entry.packet_content_sha256,
            superseded_by=entry.superseded_by,
            replacement_family=entry.replacement_family,
            dependencies=entry.dependencies,
        )

    if entry.status is PacketRegistryStatus.ACTIVE:
        return PacketEligibilityReport(
            variant_id=variant_id,
            status=entry.status,
            eligible_for_existing_promotion_gate=True,
            reasons=("packet_structurally_valid", "registry_status_active"),
            packet_id=entry.packet_id,
            packet_content_sha256=entry.packet_content_sha256,
        )

    if entry.status is PacketRegistryStatus.SUPERSEDED:
        reasons = ("packet_superseded", entry.reason)
    elif entry.status is PacketRegistryStatus.BLOCKED_BASIS_EXPANDED:
        reasons = ("candidate_basis_expanded_before_execution", entry.reason)
    elif entry.status is PacketRegistryStatus.BLOCKED_DEPENDENCY:
        dependency_states = []
        for dependency in entry.dependencies:
            dep = registry.entry_for(dependency)
            dependency_states.append(f"{dependency}:{'MISSING' if dep is None else dep.status.value}")
        reasons = ("load_bearing_dependency_not_active", entry.reason, *dependency_states)
    else:
        reasons = (entry.reason,)

    return PacketEligibilityReport(
        variant_id=variant_id,
        status=entry.status,
        eligible_for_existing_promotion_gate=False,
        reasons=tuple(reasons),
        packet_id=entry.packet_id,
        packet_content_sha256=entry.packet_content_sha256,
        superseded_by=entry.superseded_by,
        replacement_family=entry.replacement_family,
        dependencies=entry.dependencies,
    )
