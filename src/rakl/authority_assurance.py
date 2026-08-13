"""Self-contained assurance bindings around scientific/derived authority objects."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DerivedAuthoritySemantics(str, Enum):
    PROVENANCE_REFERENCE_ONLY = "PROVENANCE_REFERENCE_ONLY"
    EXACT_SCOPE_PRESERVING_REVERIFIED = "EXACT_SCOPE_PRESERVING_REVERIFIED"


class TrustBackendClass(str, Enum):
    INTERNAL_RELEASE_FIXTURE = "INTERNAL_RELEASE_FIXTURE"
    EXTERNAL_PUBLIC_KEY = "EXTERNAL_PUBLIC_KEY"
    EXTERNAL_PUBLIC_KEY_WITH_TRANSPARENCY_LOG = "EXTERNAL_PUBLIC_KEY_WITH_TRANSPARENCY_LOG"


@dataclass(frozen=True)
class CertificateAssuranceBinding:
    binding_id: str
    certificate_id: str
    certificate_content_hash: str
    attestation_id: str
    attestation_subject_hash: str
    evaluator_artifact_hash: str
    evidence_content_hashes: tuple[str, ...]
    trust_backend_id: str
    trust_backend_class: TrustBackendClass

    def __post_init__(self) -> None:
        required = (
            self.binding_id, self.certificate_id, self.certificate_content_hash,
            self.attestation_id, self.attestation_subject_hash, self.evaluator_artifact_hash,
            self.trust_backend_id,
        )
        if any(not x for x in required) or not self.evidence_content_hashes:
            raise ValueError("certificate assurance must remain self-contained and evidence-bound")
        if len(self.evidence_content_hashes) != len(set(self.evidence_content_hashes)):
            raise ValueError("evidence content hashes must be unique")

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def production_grade_trust_root(self) -> bool:
        return self.trust_backend_class in {
            TrustBackendClass.EXTERNAL_PUBLIC_KEY,
            TrustBackendClass.EXTERNAL_PUBLIC_KEY_WITH_TRANSPARENCY_LOG,
        }


@dataclass(frozen=True)
class DerivedAuthorityBinding:
    derived_view_id: str
    derived_view_hash: str
    source_certificate_ids: tuple[str, ...]
    semantics: DerivedAuthoritySemantics
    revalidation_receipt_id: str | None = None

    def __post_init__(self) -> None:
        if not self.derived_view_id or not self.derived_view_hash or not self.source_certificate_ids:
            raise ValueError("derived authority binding requires view and source certificates")
        if self.semantics is DerivedAuthoritySemantics.EXACT_SCOPE_PRESERVING_REVERIFIED and not self.revalidation_receipt_id:
            raise ValueError("actual authority propagation requires separate exact-scope revalidation")
        if self.semantics is DerivedAuthoritySemantics.PROVENANCE_REFERENCE_ONLY and self.revalidation_receipt_id:
            raise ValueError("provenance-only binding must not masquerade as revalidated authority")

    @property
    def grants_derived_authority(self) -> bool:
        # A caller-named revalidation receipt is never itself an authority root.
        # The existing scientific-authority promotion path must resolve the
        # revalidation and mint any derived certificate.
        return False

    @property
    def declares_exact_scope_revalidation(self) -> bool:
        return (
            self.semantics is DerivedAuthoritySemantics.EXACT_SCOPE_PRESERVING_REVERIFIED
            and bool(self.revalidation_receipt_id)
        )


def derived_view_eligible_for_authority_gate(
    binding: DerivedAuthorityBinding,
    *,
    resolved_revalidation_receipt_ids: frozenset[str],
) -> bool:
    return (
        binding.declares_exact_scope_revalidation
        and binding.revalidation_receipt_id in resolved_revalidation_receipt_ids
    )
