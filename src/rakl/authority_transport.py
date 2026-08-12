"""Proposal-only scientific-authority transport laws (refs #428).

The v3 runtime already enforces subject-bound scientific promotion and explicit
lineage for evidence roots. This module asks a different question: after an
already-authorized scientific object is summarized, consolidated, delegated,
derived, corroborated, or passed through Self-RAKL, what authority may the
successor *inherit without new evidence*?

Version 1 is intentionally conservative and typed rather than scalar. It never
orders G/R/M/I/D as one confidence ladder. Without a separately verified
semantic/scope transport witness, inherited authority must preserve the exact
claim, authority axis, scope, and evidence set. Cross-claim or cross-scope
transport therefore returns ``CANNOT_CHECK``; cross-axis or injected-evidence
amplification is ``INVALID``.

The module also provides a read-only revocation propagation planner over evidence
roots. It does not mutate :class:`~rakl.authority_ledger.AuthorityLedger` and it
never grants scientific authority. Canonical runtime wiring requires fresh
assurance and a separately governed integration change.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence, Tuple

from .authority_ledger import AuthorityAxis, AuthorityCertificate
from .v3_scientific_authority import ScientificEvidenceBinding

__all__ = [
    "AuthorityTransportAssessment",
    "AuthorityTransportOperation",
    "AuthorityTransportRequest",
    "AuthorityTransportVerdict",
    "PropagationAction",
    "PropagationEntry",
    "RevocationPropagationPlan",
    "evaluate_authority_transport",
    "plan_revocation_propagation",
]


class AuthorityTransportOperation(str, Enum):
    DERIVATION = "DERIVATION"
    CONSOLIDATION = "CONSOLIDATION"
    DELEGATION = "DELEGATION"
    CORROBORATION = "CORROBORATION"
    TOOL_ECHO = "TOOL_ECHO"
    SELF_EVOLUTION = "SELF_EVOLUTION"


class AuthorityTransportVerdict(str, Enum):
    NON_AMPLIFYING_TRANSPORT_CHALLENGER = "NON_AMPLIFYING_TRANSPORT_CHALLENGER"
    CANNOT_CHECK = "CANNOT_CHECK"
    INVALID = "INVALID"


@dataclass(frozen=True)
class AuthorityTransportRequest:
    request_id: str
    operation: AuthorityTransportOperation
    successor_claim_id: str
    successor_axis: AuthorityAxis
    successor_scope_id: str
    source_certificate_ids: Tuple[str, ...]
    successor_evidence_ids: Tuple[str, ...]
    frozen_before_use: bool | None


@dataclass(frozen=True)
class AuthorityTransportAssessment:
    verdict: AuthorityTransportVerdict
    reasons: Tuple[str, ...] = ()
    terminal_root_ids: Tuple[str, ...] = ()
    independent_root_count: int = 0

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_target_authority(self) -> bool:
        return False


class PropagationAction(str, Enum):
    UNAFFECTED = "UNAFFECTED"
    REVOKE_REQUIRED = "REVOKE_REQUIRED"
    REEVALUATE_REQUIRED = "REEVALUATE_REQUIRED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class PropagationEntry:
    certificate_id: str
    action: PropagationAction
    affected_root_ids: Tuple[str, ...] = ()
    remaining_root_ids: Tuple[str, ...] = ()
    reasons: Tuple[str, ...] = ()

    @property
    def mutates_authority(self) -> bool:
        return False


@dataclass(frozen=True)
class RevocationPropagationPlan:
    revoked_root_ids: Tuple[str, ...]
    entries: Tuple[PropagationEntry, ...]

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def _terminal_root(
    evidence_id: str,
    registered: Mapping[str, ScientificEvidenceBinding],
) -> tuple[str | None, str | None]:
    """Return terminal root plus an optional fail-closed reason."""

    if evidence_id not in registered:
        return None, f"evidence_unregistered:{evidence_id}"
    current = evidence_id
    seen: set[str] = set()
    while True:
        if current in seen:
            return None, f"evidence_lineage_cycle:{evidence_id}"
        seen.add(current)
        item = registered.get(current)
        if item is None:
            return None, f"upstream_evidence_unregistered:{current}"
        upstream = item.upstream_evidence_id
        if upstream is None:
            return current, None
        current = upstream


def _roots_for(
    evidence_ids: Sequence[str],
    registered: Mapping[str, ScientificEvidenceBinding],
) -> tuple[Tuple[str, ...], Tuple[str, ...]]:
    roots: list[str] = []
    reasons: list[str] = []
    for evidence_id in evidence_ids:
        root, reason = _terminal_root(evidence_id, registered)
        if reason is not None:
            reasons.append(reason)
        elif root is not None:
            roots.append(root)
    return tuple(sorted(set(roots))), tuple(sorted(set(reasons)))


def evaluate_authority_transport(
    request: AuthorityTransportRequest,
    certificates: Mapping[str, AuthorityCertificate],
    active_certificate_ids: Sequence[str],
    registered_evidence: Mapping[str, ScientificEvidenceBinding],
) -> AuthorityTransportAssessment:
    """Evaluate whether a successor can inherit authority without amplification.

    This is a *transport* checker only; success means the requested transformation
    did not introduce a stronger authority assertion than its sources. It never
    issues a successor certificate.
    """

    invalid: list[str] = []
    cannot_check: list[str] = []

    if not request.request_id.strip():
        invalid.append("transport_request_id_required")
    if not request.successor_claim_id.strip() or not request.successor_scope_id.strip():
        invalid.append("successor_claim_and_scope_required")
    if request.frozen_before_use is None:
        cannot_check.append("transport_freeze_chronology_unknown")
    elif request.frozen_before_use is False:
        invalid.append("transport_defined_posthoc")

    if not request.source_certificate_ids:
        cannot_check.append("transport_requires_source_certificate")
    if len(set(request.source_certificate_ids)) != len(request.source_certificate_ids):
        invalid.append("duplicate_source_certificate_id")
    if not request.successor_evidence_ids:
        cannot_check.append("transport_requires_preserved_evidence_binding")
    if len(set(request.successor_evidence_ids)) != len(request.successor_evidence_ids):
        invalid.append("duplicate_successor_evidence_id")

    active = set(active_certificate_ids)
    source_certificates: list[AuthorityCertificate] = []
    for certificate_id in request.source_certificate_ids:
        certificate = certificates.get(certificate_id)
        if certificate is None:
            invalid.append(f"source_certificate_unknown:{certificate_id}")
            continue
        source_certificates.append(certificate)
        if certificate_id not in active:
            invalid.append(f"source_certificate_not_active:{certificate_id}")

    if source_certificates:
        claim_ids = {item.claim_id for item in source_certificates}
        scopes = {item.scope_id for item in source_certificates}
        axes = {item.axis for item in source_certificates}

        if len(claim_ids) != 1 or request.successor_claim_id not in claim_ids:
            cannot_check.append("semantic_derivation_requires_verified_claim_transport_witness")
        if len(scopes) != 1 or request.successor_scope_id not in scopes:
            cannot_check.append("scope_transport_requires_verified_scope_witness")

        # A requested axis absent from *all* source certificates is authority
        # amplification regardless of whether the source set itself spans one
        # or multiple typed axes. Mixed-source projection remains CANNOT_CHECK
        # only when the requested axis is actually among the source axes.
        if request.successor_axis not in axes:
            invalid.append(
                "cross_axis_authority_amplification:"
                + ",".join(sorted(axis.name for axis in axes))
                + "->"
                + request.successor_axis.name
            )
        if len(axes) != 1:
            cannot_check.append("multi_axis_transport_requires_typed_projection")

        source_evidence = tuple(
            sorted({evidence_id for item in source_certificates for evidence_id in item.evidence_ids})
        )
        successor_evidence = tuple(sorted(request.successor_evidence_ids))
        if successor_evidence != source_evidence:
            added = sorted(set(successor_evidence) - set(source_evidence))
            dropped = sorted(set(source_evidence) - set(successor_evidence))
            if added:
                invalid.append("unbound_evidence_added_during_transport:" + ",".join(added))
            if dropped:
                invalid.append("provenance_or_support_dropped_during_transport:" + ",".join(dropped))

    roots, root_reasons = _roots_for(request.successor_evidence_ids, registered_evidence)
    cannot_check.extend(root_reasons)

    if invalid:
        return AuthorityTransportAssessment(
            AuthorityTransportVerdict.INVALID,
            tuple(sorted(set(invalid + cannot_check))),
            roots,
            len(roots),
        )
    if cannot_check:
        return AuthorityTransportAssessment(
            AuthorityTransportVerdict.CANNOT_CHECK,
            tuple(sorted(set(cannot_check))),
            roots,
            len(roots),
        )
    return AuthorityTransportAssessment(
        AuthorityTransportVerdict.NON_AMPLIFYING_TRANSPORT_CHALLENGER,
        (),
        roots,
        len(roots),
    )


def plan_revocation_propagation(
    revoked_root_ids: Sequence[str],
    certificates: Mapping[str, AuthorityCertificate],
    active_certificate_ids: Sequence[str],
    registered_evidence: Mapping[str, ScientificEvidenceBinding],
) -> RevocationPropagationPlan:
    """Plan fail-closed descendant handling after evidence-root revocation.

    ``REVOKE_REQUIRED`` means all evidence roots supporting the active certificate
    are revoked. ``REEVALUATE_REQUIRED`` means at least one revoked and at least
    one independent root remains; this function does not assume the remaining
    root is sufficient for the authority coordinate. Independent certificates
    whose roots do not intersect the revoked set are left ``UNAFFECTED``.
    """

    revoked = tuple(sorted(set(revoked_root_ids)))
    revoked_set = set(revoked)
    entries: list[PropagationEntry] = []
    active = set(active_certificate_ids)

    for certificate_id in sorted(active):
        certificate = certificates.get(certificate_id)
        if certificate is None:
            entries.append(
                PropagationEntry(
                    certificate_id,
                    PropagationAction.CANNOT_CHECK,
                    reasons=("active_certificate_record_missing",),
                )
            )
            continue
        roots, reasons = _roots_for(certificate.evidence_ids, registered_evidence)
        if reasons or not roots:
            entries.append(
                PropagationEntry(
                    certificate_id,
                    PropagationAction.CANNOT_CHECK,
                    reasons=reasons or ("certificate_has_no_resolvable_evidence_root",),
                )
            )
            continue
        affected = tuple(sorted(set(roots) & revoked_set))
        remaining = tuple(sorted(set(roots) - revoked_set))
        if not affected:
            action = PropagationAction.UNAFFECTED
        elif not remaining:
            action = PropagationAction.REVOKE_REQUIRED
        else:
            action = PropagationAction.REEVALUATE_REQUIRED
        entries.append(
            PropagationEntry(
                certificate_id=certificate_id,
                action=action,
                affected_root_ids=affected,
                remaining_root_ids=remaining,
            )
        )

    return RevocationPropagationPlan(revoked, tuple(entries))
