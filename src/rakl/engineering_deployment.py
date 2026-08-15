"""Support-first deployment admissibility for ORION production backends.

This is an engineering precondition, not a scientific verdict.  It makes the
population/topology that an implementation must support explicit before calling a
backend production-ready, following RAKL's support-before-effort discipline.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class DeploymentMode(str, Enum):
    SINGLE_PROCESS = "SINGLE_PROCESS"
    MULTI_PROCESS_SINGLE_HOST = "MULTI_PROCESS_SINGLE_HOST"
    MULTI_HOST = "MULTI_HOST"


class SupportVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    UNSUPPORTED = "UNSUPPORTED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class EngineeringSupportProfile:
    profile_id: str
    mode: DeploymentMode
    max_concurrent_workers: int
    requires_shared_blob_store: bool
    requires_serializable_metadata: bool
    requires_durable_workflow_history: bool
    requires_point_in_time_recovery: bool
    requires_authz: bool
    requires_build_attestation: bool
    external_effect_classes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.profile_id.strip():
            raise ValueError("profile_id is required")
        if self.max_concurrent_workers < 1:
            raise ValueError("max_concurrent_workers must be positive")
        if len(self.external_effect_classes) != len(set(self.external_effect_classes)):
            raise ValueError("external effect classes must be unique")
        if self.mode is DeploymentMode.SINGLE_PROCESS and self.max_concurrent_workers != 1:
            raise ValueError("SINGLE_PROCESS profile requires exactly one worker")
        if self.external_effect_classes and not self.requires_durable_workflow_history:
            raise ValueError("external effects require durable workflow history")

    def to_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "mode": self.mode.value,
            "max_concurrent_workers": self.max_concurrent_workers,
            "requires_shared_blob_store": self.requires_shared_blob_store,
            "requires_serializable_metadata": self.requires_serializable_metadata,
            "requires_durable_workflow_history": self.requires_durable_workflow_history,
            "requires_point_in_time_recovery": self.requires_point_in_time_recovery,
            "requires_authz": self.requires_authz,
            "requires_build_attestation": self.requires_build_attestation,
            "external_effect_classes": list(self.external_effect_classes),
        }


@dataclass(frozen=True)
class BackendCapabilities:
    backend_id: str
    multi_process_safe: bool | None
    multi_host_safe: bool | None
    shared_blob_store: bool | None
    serializable_metadata: bool | None
    durable_workflow_history: bool | None
    point_in_time_recovery: bool | None
    authz: bool | None
    build_attestation: bool | None

    def __post_init__(self) -> None:
        if not self.backend_id.strip():
            raise ValueError("backend_id is required")


@dataclass(frozen=True)
class SupportAssessment:
    verdict: SupportVerdict
    missing: Tuple[str, ...]
    unknown: Tuple[str, ...]
    reasons: Tuple[str, ...]


def assess_engineering_support(
    profile: EngineeringSupportProfile,
    capabilities: BackendCapabilities,
) -> SupportAssessment:
    required: list[tuple[str, bool | None]] = []
    if profile.mode is not DeploymentMode.SINGLE_PROCESS or profile.max_concurrent_workers > 1:
        required.append(("multi_process_safe", capabilities.multi_process_safe))
    if profile.mode is DeploymentMode.MULTI_HOST:
        required.append(("multi_host_safe", capabilities.multi_host_safe))
    if profile.requires_shared_blob_store:
        required.append(("shared_blob_store", capabilities.shared_blob_store))
    if profile.requires_serializable_metadata:
        required.append(("serializable_metadata", capabilities.serializable_metadata))
    if profile.requires_durable_workflow_history:
        required.append(("durable_workflow_history", capabilities.durable_workflow_history))
    if profile.requires_point_in_time_recovery:
        required.append(("point_in_time_recovery", capabilities.point_in_time_recovery))
    if profile.requires_authz:
        required.append(("authz", capabilities.authz))
    if profile.requires_build_attestation:
        required.append(("build_attestation", capabilities.build_attestation))

    missing = tuple(name for name, value in required if value is False)
    unknown = tuple(name for name, value in required if value is None)
    if missing:
        return SupportAssessment(
            SupportVerdict.UNSUPPORTED,
            missing,
            unknown,
            tuple(f"required_capability_missing:{name}" for name in missing),
        )
    if unknown:
        return SupportAssessment(
            SupportVerdict.CANNOT_CHECK,
            (),
            unknown,
            tuple(f"required_capability_unmeasured:{name}" for name in unknown),
        )
    return SupportAssessment(
        SupportVerdict.SUPPORTED,
        (),
        (),
        ("all_registered_engineering_support_requirements_satisfied",),
    )
