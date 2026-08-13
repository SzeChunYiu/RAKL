"""Single composition surface for the unified RAKL hardening handoff.

The component modules intentionally retain typed semantics rather than being
flattened into one mega-state.  This manifest binds the exact versions that are
allowed to participate in one experiment/integration epoch and checks the
cross-surface invariants the individual modules cannot see by themselves.

It grants no scientific, proof, transfer, model-promotion, or governance
authority.  ``READY_FOR_INTEGRATION_TEST`` means only that identities and
required external receipts are sufficiently bound to run the next experiment.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from .canonical_commitment import sha256_digest


class IntegrationReadiness(str, Enum):
    READY_FOR_INTEGRATION_TEST = "READY_FOR_INTEGRATION_TEST"
    CANNOT_CHECK = "CANNOT_CHECK"
    REJECT = "REJECT"


@dataclass(frozen=True)
class UnifiedMechanicsManifest:
    manifest_id: str
    base_commit_hash: str
    state_commitment_digest: str
    structural_identity_digest: str
    operational_subject_digest: str | None = None
    geometry_id: str | None = None
    geometry_learning_receipt_id: str | None = None
    quotient_validation_receipt_id: str | None = None
    structural_transfer_use_receipt_id: str | None = None
    training_assurance_id: str | None = None
    shared_identity_reuse_receipt_id: str | None = None
    compilation_proposal_id: str | None = None
    fresh_compilation_assurance_id: str | None = None
    exact_base_guard_receipt_id: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "manifest_id",
            "base_commit_hash",
            "state_commitment_digest",
            "structural_identity_digest",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        optional = (
            "operational_subject_digest",
            "geometry_id",
            "geometry_learning_receipt_id",
            "quotient_validation_receipt_id",
            "structural_transfer_use_receipt_id",
            "training_assurance_id",
            "shared_identity_reuse_receipt_id",
            "compilation_proposal_id",
            "fresh_compilation_assurance_id",
            "exact_base_guard_receipt_id",
        )
        for name in optional:
            value = getattr(self, name)
            if value is not None and not value.strip():
                raise ValueError(f"{name} must be omitted or nonempty")
        if (self.geometry_id is None) != (self.operational_subject_digest is None):
            raise ValueError("geometry use must be bound to an operational subject")
        if self.geometry_learning_receipt_id is not None and self.geometry_id is None:
            raise ValueError("geometry learning receipt requires a geometry identity")
        if self.fresh_compilation_assurance_id is not None and self.compilation_proposal_id is None:
            raise ValueError("fresh compilation assurance requires the proposal it assures")

    @property
    def digest(self) -> str:
        return sha256_digest(self, domain="rakl-unified-mechanics-manifest/v1")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_proof_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class UnifiedIntegrationReport:
    verdict: IntegrationReadiness
    reasons: tuple[str, ...]
    manifest_digest: str

    @property
    def grants_authority(self) -> bool:
        return False


def assess_unified_integration(
    manifest: UnifiedMechanicsManifest,
    *,
    expected_base_commit_hash: str,
    resolved_receipt_ids: Iterable[str],
    require_geometry: bool = False,
    require_training: bool = False,
    require_shared_identity_reuse: bool = False,
    require_cognitive_compilation: bool = False,
    require_quotient_assurance: bool = False,
    require_transfer_use_assurance: bool = False,
    require_exact_base_guards: bool = True,
) -> UnifiedIntegrationReport:
    """Check one integration epoch without coercing the component authority domains."""
    reasons: list[str] = []
    resolved = set(resolved_receipt_ids)
    if manifest.base_commit_hash != expected_base_commit_hash:
        reasons.append("base_commit_mismatch")

    def require_field(name: str, *, receipt: bool = False) -> None:
        value = getattr(manifest, name)
        if value is None:
            reasons.append(f"missing:{name}")
        elif receipt and value not in resolved:
            reasons.append(f"unresolved:{name}:{value}")

    if require_exact_base_guards:
        require_field("exact_base_guard_receipt_id", receipt=True)
    if require_geometry:
        require_field("geometry_id")
        require_field("operational_subject_digest")
        # A learned-geometry receipt is optional for exact/oracle-free constructions;
        # the geometry module itself owns constructibility-specific requirements.
        if manifest.geometry_learning_receipt_id is not None and manifest.geometry_learning_receipt_id not in resolved:
            reasons.append(f"unresolved:geometry_learning_receipt_id:{manifest.geometry_learning_receipt_id}")
    if require_training:
        require_field("training_assurance_id", receipt=True)
    if require_shared_identity_reuse:
        require_field("shared_identity_reuse_receipt_id", receipt=True)
    if require_cognitive_compilation:
        require_field("compilation_proposal_id")
        require_field("fresh_compilation_assurance_id", receipt=True)
    if require_quotient_assurance:
        require_field("quotient_validation_receipt_id", receipt=True)
    if require_transfer_use_assurance:
        require_field("structural_transfer_use_receipt_id", receipt=True)

    if reasons:
        verdict = IntegrationReadiness.REJECT if "base_commit_mismatch" in reasons else IntegrationReadiness.CANNOT_CHECK
    else:
        verdict = IntegrationReadiness.READY_FOR_INTEGRATION_TEST
    return UnifiedIntegrationReport(verdict, tuple(reasons), manifest.digest)


def build_unified_mechanics_manifest(
    *,
    manifest_id: str,
    base_commit_hash: str,
    state_commitment_digest: str,
    structural_identity_digest: str,
    operational_subject_digest: str | None = None,
    geometry_id: str | None = None,
    geometry_learning_receipt_id: str | None = None,
    quotient_validation_receipt_id: str | None = None,
    structural_transfer_use_receipt_id: str | None = None,
    training_assurance_id: str | None = None,
    shared_identity_reuse_receipt_id: str | None = None,
    compilation_proposal_id: str | None = None,
    fresh_compilation_assurance_id: str | None = None,
    exact_base_guard_receipt_id: str | None = None,
) -> UnifiedMechanicsManifest:
    """Assemble one integration-epoch manifest from its component identities/receipts.

    This is the composition surface for a single experiment/integration epoch:
    it binds the exact base commit, the canonical state commitment digest, the
    structural identity digest and every resolved component receipt that
    participates in the epoch.  It does NOT flatten the component authority
    domains; ``assess_unified_integration`` reports ``READY_FOR_INTEGRATION_TEST``
    only when identities/receipts are sufficiently bound to *run* the next
    experiment, never a capability or authority claim.
    """
    return UnifiedMechanicsManifest(
        manifest_id=manifest_id,
        base_commit_hash=base_commit_hash,
        state_commitment_digest=state_commitment_digest,
        structural_identity_digest=structural_identity_digest,
        operational_subject_digest=operational_subject_digest,
        geometry_id=geometry_id,
        geometry_learning_receipt_id=geometry_learning_receipt_id,
        quotient_validation_receipt_id=quotient_validation_receipt_id,
        structural_transfer_use_receipt_id=structural_transfer_use_receipt_id,
        training_assurance_id=training_assurance_id,
        shared_identity_reuse_receipt_id=shared_identity_reuse_receipt_id,
        compilation_proposal_id=compilation_proposal_id,
        fresh_compilation_assurance_id=fresh_compilation_assurance_id,
        exact_base_guard_receipt_id=exact_base_guard_receipt_id,
    )
