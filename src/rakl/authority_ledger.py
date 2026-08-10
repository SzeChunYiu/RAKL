from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class AuthorityAxis(str, Enum):
    """Canonical scientific-authority coordinates used by the Paper-1 formalism."""

    GROUNDING = "G"
    REPRESENTATION = "R"
    MECHANISM = "M"
    IDENTIFICATION = "I"
    DECISION = "D"


class VerificationOutcome(str, Enum):
    SUPPORTED = "SUPPORTED"
    PARTIAL = "PARTIAL"
    REFUTED = "REFUTED"
    CANNOT_CHECK = "CANNOT_CHECK"


class AuthorityEventKind(str, Enum):
    ISSUE = "ISSUE"
    REVOKE = "REVOKE"
    SUPERSEDE = "SUPERSEDE"


@dataclass(frozen=True)
class AuthorityProposal:
    """A proposal has no canonical authority until a verifier commits it."""

    proposal_id: str
    claim_id: str
    axis: AuthorityAxis
    proposition: str
    scope_id: str
    evidence_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        for value, name in (
            (self.proposal_id, "proposal_id"),
            (self.claim_id, "claim_id"),
            (self.proposition, "proposition"),
            (self.scope_id, "scope_id"),
        ):
            if not value.strip():
                raise ValueError(f"{name} is required")
        if not self.evidence_ids or any(not item.strip() for item in self.evidence_ids):
            raise ValueError("authority proposal requires non-empty evidence ids")


@dataclass(frozen=True)
class AuthorityCertificate:
    certificate_id: str
    claim_id: str
    axis: AuthorityAxis
    proposition: str
    scope_id: str
    evidence_ids: tuple[str, ...]
    partial: bool = False


@dataclass(frozen=True)
class AuthorityEvent:
    sequence: int
    kind: AuthorityEventKind
    certificate_id: str
    reason: str
    replacement_certificate_id: str | None = None


@dataclass
class AuthorityLedger:
    """Append-only certificate history with a non-monotone active-authority view.

    The ledger implements the distinction used in the long-form Epistemic Mechanics
    paper: historical evidence/certificate events remain addressable, while the set of
    currently valid authority certificates may shrink after refutation or supersession.
    A proposal is deliberately inert until ``commit_verified`` is called with a
    verifier outcome that can mint scoped authority.
    """

    certificates: dict[str, AuthorityCertificate] = field(default_factory=dict)
    active_ids: set[str] = field(default_factory=set)
    events: list[AuthorityEvent] = field(default_factory=list)

    def commit_verified(
        self,
        proposal: AuthorityProposal,
        *,
        certificate_id: str,
        outcome: VerificationOutcome,
    ) -> AuthorityCertificate | None:
        if outcome not in {VerificationOutcome.SUPPORTED, VerificationOutcome.PARTIAL}:
            return None
        if not certificate_id.strip():
            raise ValueError("certificate_id is required")
        if certificate_id in self.certificates:
            raise ValueError(f"duplicate certificate id: {certificate_id}")

        certificate = AuthorityCertificate(
            certificate_id=certificate_id,
            claim_id=proposal.claim_id,
            axis=proposal.axis,
            proposition=proposal.proposition,
            scope_id=proposal.scope_id,
            evidence_ids=proposal.evidence_ids,
            partial=outcome is VerificationOutcome.PARTIAL,
        )
        self.certificates[certificate_id] = certificate
        self.active_ids.add(certificate_id)
        self.events.append(
            AuthorityEvent(
                sequence=len(self.events) + 1,
                kind=AuthorityEventKind.ISSUE,
                certificate_id=certificate_id,
                reason=f"verified:{outcome.value}",
            )
        )
        return certificate

    def revoke(self, certificate_id: str, *, reason: str) -> None:
        if certificate_id not in self.certificates:
            raise KeyError(certificate_id)
        if certificate_id not in self.active_ids:
            raise ValueError("certificate is not active")
        if not reason.strip():
            raise ValueError("revocation reason required")

        self.active_ids.remove(certificate_id)
        self.events.append(
            AuthorityEvent(
                sequence=len(self.events) + 1,
                kind=AuthorityEventKind.REVOKE,
                certificate_id=certificate_id,
                reason=reason.strip(),
            )
        )

    def supersede(
        self,
        old_certificate_id: str,
        new_certificate: AuthorityCertificate,
        *,
        reason: str,
    ) -> None:
        if old_certificate_id not in self.active_ids:
            raise ValueError("old certificate must be active")
        if new_certificate.certificate_id in self.certificates:
            raise ValueError("replacement certificate id already exists")
        if new_certificate.claim_id != self.certificates[old_certificate_id].claim_id:
            raise ValueError("replacement must concern the same claim")
        if not reason.strip():
            raise ValueError("supersession reason required")

        self.active_ids.remove(old_certificate_id)
        self.certificates[new_certificate.certificate_id] = new_certificate
        self.active_ids.add(new_certificate.certificate_id)
        self.events.append(
            AuthorityEvent(
                sequence=len(self.events) + 1,
                kind=AuthorityEventKind.SUPERSEDE,
                certificate_id=old_certificate_id,
                reason=reason.strip(),
                replacement_certificate_id=new_certificate.certificate_id,
            )
        )

    def active_for(
        self, claim_id: str, axis: AuthorityAxis | None = None
    ) -> tuple[AuthorityCertificate, ...]:
        items = [
            self.certificates[certificate_id]
            for certificate_id in self.active_ids
            if self.certificates[certificate_id].claim_id == claim_id
            and (axis is None or self.certificates[certificate_id].axis is axis)
        ]
        return tuple(sorted(items, key=lambda item: item.certificate_id))

    def history_for(self, certificate_id: str) -> tuple[AuthorityEvent, ...]:
        return tuple(
            event
            for event in self.events
            if event.certificate_id == certificate_id
            or event.replacement_certificate_id == certificate_id
        )
