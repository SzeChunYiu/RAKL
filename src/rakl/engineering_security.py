"""Infrastructure authorization contracts kept separate from RAKL authority."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class InfraCapability(str, Enum):
    OBSERVE = "OBSERVE"
    EVIDENCE_READ = "EVIDENCE_READ"
    EVIDENCE_WRITE = "EVIDENCE_WRITE"
    EXECUTE = "EXECUTE"
    CONTROL = "CONTROL"
    GOVERNANCE_PROPOSE = "GOVERNANCE_PROPOSE"
    GOVERNANCE_PROMOTE = "GOVERNANCE_PROMOTE"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class InfrastructurePrincipal:
    principal_id: str
    workload_identity: str
    capabilities: Tuple[InfraCapability, ...]

    def __post_init__(self) -> None:
        if not self.principal_id or not self.workload_identity:
            raise ValueError("principal and workload identity required")
        if len(self.capabilities) != len(set(self.capabilities)):
            raise ValueError("infrastructure capabilities must be unique")

    @property
    def grants_scientific_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class SecretReference:
    provider: str
    reference_id: str
    revision: str

    def __post_init__(self) -> None:
        if not self.provider or not self.reference_id or not self.revision:
            raise ValueError("secret reference requires provider/id/revision")


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def authorize_infrastructure(
    principal: InfrastructurePrincipal,
    capability: InfraCapability,
) -> AuthorizationDecision:
    if capability in principal.capabilities or InfraCapability.ADMIN in principal.capabilities:
        return AuthorizationDecision(True, f"infra_capability_present:{capability.value}")
    return AuthorizationDecision(False, f"infra_capability_missing:{capability.value}")
