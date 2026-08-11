"""Certificate-bound scientific authority for the RAKL v3 persistent runtime (refs #242).

This module composes the scientific :mod:`~rakl.authority_ledger` objects into
the v3 runtime *without* inventing a second authority ontology and without
routing scientific authority through the unified substrate's generic
``metadata["authority"]`` string.

Three properties are load-bearing.

**Value semantics.** :class:`~rakl.authority_ledger.AuthorityLedger` is a mutable
dataclass holding ``dict``/``set``/``list``. Embedding a live ledger in the frozen
:class:`~rakl.v3_runtime.RAKLV3State` would alias it across
``dataclasses.replace``, so ``pi_auth(before)`` and ``pi_auth(after)`` would
project the *same mutated object* and every authority movement would be
invisible to the noninterference checker. That failure mode was reproduced
before this module was written: a real mint under ``RECORD_EPISODE`` reported
``PASS``. :class:`ScientificAuthorityProjection` is therefore an immutable
snapshot of tuples, and every transition reconstructs a fresh ledger, mutates
it, and snapshots back. Aliasing is impossible by construction.

**Certificate binding, not declaration binding.** The historical v3 integration
audit found declaration-bound authority surfaces: a caller-supplied enum,
boolean or string standing in for verification. ``AuthorityLedger.commit_verified``
is itself declaration-bound — it accepts a caller's
:class:`~rakl.authority_ledger.VerificationOutcome`. This module never exposes
that path to the runtime. A scientific promotion resolves a
:class:`~rakl.v3_authority.ProtectedAttestation` whose ``subject_hash`` must equal
a digest computed here over the *actual* claim text, axis, scope and registered
evidence content digests. Changing any of those invalidates the attestation, so
an attestation cannot be reused for a different scientific assertion.

**Content-bound evidence.** Evidence is registered with a SHA-256 over its exact
bytes and a frozen provenance class. The provenance class is supplied by
registration, never inferred from text here.

This module mints no authority of its own and is wired into no promotion gate
outside the explicit functions below.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from typing import Iterable, Mapping, Tuple

from .authority_ledger import (
    AuthorityAxis,
    AuthorityCertificate,
    AuthorityEvent,
    AuthorityLedger,
    AuthorityProposal,
    VerificationOutcome,
)
from .claim_evidence import ClaimAtom, sha256_text
from .epistemic_noninterference import EvidenceRootKind
from .v3_authority import (
    AttestationPurpose,
    ProtectedAuthorityContext,
    canonical_sha256,
    resolve_protected_attestation,
)

__all__ = [
    "ScientificAuthorityProjection",
    "ScientificEvidenceBinding",
    "ScientificTransitionOutcome",
    "StateCoordinate",
    "TRANSITION_OWNERSHIP",
    "ledger_from_projection",
    "projection_from_ledger",
    "promotion_subject_hash",
    "revocation_subject_hash",
    "supersession_subject_hash",
]


# --------------------------------------------------------------------------
# Transition ownership registry (issue #242 §3)
# --------------------------------------------------------------------------


class StateCoordinate(str, Enum):
    """The three coordinates a registered runtime transition may change.

    Every public v3 transition is classified against this set. The classification
    is enforced by ``tests/test_v3_scientific_authority_noninterference.py``:
    adding a transition without registering it fails the suite, so ownership
    cannot be left implicit.
    """

    EXPERIENCE_ROUTING = "EXPERIENCE_ROUTING"
    CANONICAL_SCIENTIFIC_CONTENT = "CANONICAL_SCIENTIFIC_CONTENT"
    SCIENTIFIC_AUTHORITY = "SCIENTIFIC_AUTHORITY"


_EXPERIENCE_ONLY = frozenset({StateCoordinate.EXPERIENCE_ROUTING})

#: Which coordinates each registered v3 transition may move.
#:
#: Only the three ``*_scientific_authority`` entries carry
#: :data:`StateCoordinate.SCIENTIFIC_AUTHORITY`. Everything else is
#: authority-inert by contract, which is exactly what
#: ``EPISTEMIC_NONINTERFERENCE`` makes executable.
TRANSITION_OWNERSHIP: Mapping[str, frozenset[StateCoordinate]] = {
    # experience / routing side
    "record_task_episode": _EXPERIENCE_ONLY,
    "consolidate_lesson": _EXPERIENCE_ONLY,
    "record_saturation_round": _EXPERIENCE_ONLY,
    # read-only over the state; move nothing
    "compile_state_fibre": frozenset(),
    "materialize_state_substrate": frozenset(),
    "state_fingerprint": frozenset(),
    "state_fingerprint_v2": frozenset(),
    # canonical scientific content, authority-inert
    "register_scientific_claim": frozenset({StateCoordinate.CANONICAL_SCIENTIFIC_CONTENT}),
    "register_scientific_evidence": frozenset({StateCoordinate.CANONICAL_SCIENTIFIC_CONTENT}),
    # the only authority-bearing transitions
    "promote_scientific_authority": frozenset(
        {StateCoordinate.CANONICAL_SCIENTIFIC_CONTENT, StateCoordinate.SCIENTIFIC_AUTHORITY}
    ),
    "revoke_scientific_authority": frozenset({StateCoordinate.SCIENTIFIC_AUTHORITY}),
    "supersede_scientific_authority": frozenset(
        {StateCoordinate.CANONICAL_SCIENTIFIC_CONTENT, StateCoordinate.SCIENTIFIC_AUTHORITY}
    ),
}


# --------------------------------------------------------------------------
# Minimal canonical scientific state
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class ScientificEvidenceBinding:
    """One registered evidence root, bound by content digest.

    ``kind`` and ``supports_axes`` are frozen properties of the registration, not
    judgements made here; no semantic oracle is consulted. ``upstream_evidence_id``
    keeps derivative lineage explicit so many descendants of one experiment cannot
    be counted as independent support.
    """

    evidence_id: str
    kind: EvidenceRootKind
    content_sha256: str
    supports_axes: Tuple[AuthorityAxis, ...] = ()
    upstream_evidence_id: str | None = None

    def __post_init__(self) -> None:
        if not self.evidence_id.strip():
            raise ValueError("evidence binding requires a non-empty id")
        if len(self.content_sha256) != 64 or any(
            ch not in "0123456789abcdef" for ch in self.content_sha256
        ):
            raise ValueError("evidence binding requires a lowercase SHA-256 content digest")
        if self.upstream_evidence_id is not None and not self.upstream_evidence_id.strip():
            raise ValueError("upstream_evidence_id must be omitted or non-empty")
        if self.upstream_evidence_id == self.evidence_id:
            raise ValueError("evidence binding cannot be its own upstream root")
        if len(set(self.supports_axes)) != len(self.supports_axes):
            raise ValueError("supports_axes must not repeat an axis")
        # Normalise axis order. ``supports_axes`` is a set of axes semantically,
        # but a tuple structurally, so (R, M) and (M, R) would otherwise be
        # unequal values meaning the same thing — enough to make an idempotent
        # re-registration raise "already registered with different content"
        # while producing an identical subject hash.
        ordered = tuple(sorted(self.supports_axes, key=lambda axis: axis.value))
        if ordered != self.supports_axes:
            object.__setattr__(self, "supports_axes", ordered)


@dataclass(frozen=True)
class ScientificAuthorityProjection:
    """Immutable snapshot of scientific authority plus its minimal claim/evidence binding.

    The name deliberately carries ``Authority`` so
    :func:`~rakl.epistemic_noninterference.describe_integration_surface` sees a
    composed authority coordinate on the live dataclass.

    All fields are tuples of frozen dataclasses, so two states never share
    mutable authority structure. ``certificates`` and ``events`` retain full
    history; ``active_certificate_ids`` is the non-monotone active view that
    revocation and supersession shrink.
    """

    certificates: Tuple[AuthorityCertificate, ...] = ()
    active_certificate_ids: Tuple[str, ...] = ()
    events: Tuple[AuthorityEvent, ...] = ()
    claims: Tuple[ClaimAtom, ...] = ()
    evidence: Tuple[ScientificEvidenceBinding, ...] = ()

    def claim_by_id(self) -> Mapping[str, ClaimAtom]:
        return {claim.claim_id: claim for claim in self.claims}

    def evidence_by_id(self) -> Mapping[str, ScientificEvidenceBinding]:
        return {item.evidence_id: item for item in self.evidence}


def ledger_from_projection(projection: ScientificAuthorityProjection) -> AuthorityLedger:
    """Reconstruct a working (mutable) ledger from an immutable snapshot."""

    return AuthorityLedger(
        certificates={item.certificate_id: item for item in projection.certificates},
        active_ids=set(projection.active_certificate_ids),
        events=list(projection.events),
    )


def projection_from_ledger(
    ledger: AuthorityLedger,
    *,
    claims: Iterable[ClaimAtom] = (),
    evidence: Iterable[ScientificEvidenceBinding] = (),
) -> ScientificAuthorityProjection:
    """Snapshot a working ledger back into an immutable, order-stable projection."""

    return ScientificAuthorityProjection(
        certificates=tuple(
            sorted(ledger.certificates.values(), key=lambda item: item.certificate_id)
        ),
        active_certificate_ids=tuple(sorted(ledger.active_ids)),
        events=tuple(ledger.events),
        claims=tuple(sorted(claims, key=lambda item: item.claim_id)),
        evidence=tuple(sorted(evidence, key=lambda item: item.evidence_id)),
    )


# --------------------------------------------------------------------------
# Subject hashes: what an attestation must commit to
# --------------------------------------------------------------------------


def _evidence_digest_pairs(
    evidence_ids: Iterable[str], registered: Mapping[str, ScientificEvidenceBinding]
) -> list[list[str]]:
    return sorted(
        [evidence_id, registered[evidence_id].content_sha256]
        for evidence_id in evidence_ids
        if evidence_id in registered
    )


def promotion_subject_hash(
    *,
    claim: ClaimAtom,
    axis: AuthorityAxis,
    proposition: str,
    scope_id: str,
    evidence_ids: Iterable[str],
    registered_evidence: Mapping[str, ScientificEvidenceBinding],
) -> str:
    """Digest of the exact scientific assertion an attestation must be bound to.

    Includes the claim *text* digest, not just the claim id, so renaming content
    behind a stable id invalidates the attestation.
    """

    return canonical_sha256(
        {
            "kind": "SCIENTIFIC_AUTHORITY_PROMOTION",
            "claim_id": claim.claim_id,
            "claim_text_sha256": sha256_text(claim.text),
            "claim_scope": claim.scope,
            "axis": axis.value,
            "proposition_sha256": sha256_text(proposition),
            "scope_id": scope_id,
            "evidence": _evidence_digest_pairs(evidence_ids, registered_evidence),
        }
    )


def revocation_subject_hash(
    *,
    certificate: AuthorityCertificate,
    reason: str,
    refutation_evidence_ids: Iterable[str],
    registered_evidence: Mapping[str, ScientificEvidenceBinding],
) -> str:
    """Digest binding a revocation to the exact certificate and refuting evidence."""

    return canonical_sha256(
        {
            "kind": "SCIENTIFIC_AUTHORITY_REVOCATION",
            "certificate_id": certificate.certificate_id,
            "claim_id": certificate.claim_id,
            "axis": certificate.axis.value,
            "scope_id": certificate.scope_id,
            "reason_sha256": sha256_text(reason),
            "refutation_evidence": _evidence_digest_pairs(
                refutation_evidence_ids, registered_evidence
            ),
        }
    )


def supersession_subject_hash(
    *,
    old_certificate: AuthorityCertificate,
    new_proposal: AuthorityProposal,
    reason: str,
    registered_evidence: Mapping[str, ScientificEvidenceBinding],
) -> str:
    """Digest binding a supersession to both the retired and replacement assertions."""

    return canonical_sha256(
        {
            "kind": "SCIENTIFIC_AUTHORITY_SUPERSESSION",
            "old_certificate_id": old_certificate.certificate_id,
            "claim_id": old_certificate.claim_id,
            "new_axis": new_proposal.axis.value,
            "new_proposition_sha256": sha256_text(new_proposal.proposition),
            "new_scope_id": new_proposal.scope_id,
            "reason_sha256": sha256_text(reason),
            "evidence": _evidence_digest_pairs(
                new_proposal.evidence_ids, registered_evidence
            ),
        }
    )


# --------------------------------------------------------------------------
# The §5 promotion contract, enforced at the runtime boundary
# --------------------------------------------------------------------------


_SCIENTIFIC_KINDS = frozenset(
    {EvidenceRootKind.EXTERNAL_OBSERVATION, EvidenceRootKind.DERIVED_REPORT}
)
_EXPERIENCE_KINDS = frozenset(
    {
        EvidenceRootKind.TASK_EPISODE,
        EvidenceRootKind.LESSON,
        EvidenceRootKind.ROUTING_STATISTIC,
    }
)

#: ``MECHANISM`` may not be minted by representation-only support;
#: ``IDENTIFICATION`` may not be minted by mechanism-only support.
_STRICTLY_WEAKER: Mapping[AuthorityAxis, AuthorityAxis] = {
    AuthorityAxis.MECHANISM: AuthorityAxis.REPRESENTATION,
    AuthorityAxis.IDENTIFICATION: AuthorityAxis.MECHANISM,
}


def _terminal_evidence(
    evidence_id: str, registered: Mapping[str, ScientificEvidenceBinding]
) -> str:
    seen: set[str] = set()
    current = evidence_id
    while current in registered and current not in seen:
        seen.add(current)
        upstream = registered[current].upstream_evidence_id
        if upstream is None:
            return current
        current = upstream
    return current


def _check_evidence_contract(
    axis: AuthorityAxis,
    evidence_ids: Tuple[str, ...],
    registered: Mapping[str, ScientificEvidenceBinding],
) -> Tuple[str, ...]:
    """Return refusal reasons for the §5 evidence contract. Empty tuple means clean."""

    reasons: list[str] = []
    unknown = [item for item in evidence_ids if item not in registered]
    if unknown:
        reasons.append("scientific_evidence_unregistered:" + ",".join(sorted(unknown)))
        return tuple(reasons)

    resolved = [registered[item] for item in evidence_ids]
    scientific = [item for item in resolved if item.kind in _SCIENTIFIC_KINDS]
    experience = [item for item in resolved if item.kind in _EXPERIENCE_KINDS]

    if not scientific:
        reasons.append("scientific_authority_requires_non_experience_evidence")
    if experience:
        reasons.append(
            "experience_objects_claimed_as_scientific_evidence:"
            + ",".join(sorted(item.evidence_id for item in experience))
        )

    if len(evidence_ids) > 1:
        terminal = {_terminal_evidence(item, registered) for item in evidence_ids}
        if len(terminal) < len(evidence_ids):
            reasons.append(
                f"claimed_evidence_collapses_to_{len(terminal)}_independent_lineage_roots"
            )

    supported = {axis_ for item in scientific for axis_ in item.supports_axes}
    if axis not in supported:
        weaker = _STRICTLY_WEAKER.get(axis)
        if weaker is not None and weaker in supported:
            reasons.append(
                f"axis_escalation:{axis.name}_supported_only_up_to_{weaker.name}"
            )
        else:
            reasons.append(f"registered_evidence_does_not_support_axis:{axis.name}")
    return tuple(reasons)


@dataclass(frozen=True)
class ScientificTransitionOutcome:
    """Result of an authority-bearing transition.

    ``state`` is always returned. When ``committed`` is false the returned state
    is value-equal to the input on the authority coordinate: a refused promotion
    is inert, not partially applied.
    """

    state: "object"
    committed: bool
    reasons: Tuple[str, ...] = ()
    certificate_id: str | None = None

    @property
    def grants_authority(self) -> bool:
        """Authority was minted only when a protected attestation resolved."""

        return self.committed


def _resolve_or_refuse(
    context: ProtectedAuthorityContext | None,
    attestation_id: str | None,
    *,
    purpose: AttestationPurpose,
    subject_hash: str,
) -> Tuple[str, ...]:
    resolution = resolve_protected_attestation(
        context, attestation_id, purpose=purpose, subject_hash=subject_hash
    )
    return () if resolution.valid else tuple(resolution.reasons)


def promote_scientific_authority(
    state: "object",
    proposal: AuthorityProposal,
    *,
    certificate_id: str,
    outcome: VerificationOutcome,
    authority_context: ProtectedAuthorityContext | None = None,
    attestation_id: str | None = None,
) -> ScientificTransitionOutcome:
    """Mint scientific authority only under a subject-bound protected attestation.

    Refuses, without partial application, when the §5 evidence contract fails or
    when no attestation resolves against the digest of *this exact* assertion.
    The caller-supplied ``outcome`` alone can never mint authority; that is the
    declaration-bound surface this function exists to close.
    """

    projection: ScientificAuthorityProjection = state.scientific_authority  # type: ignore[attr-defined]
    registered = projection.evidence_by_id()
    claim = projection.claim_by_id().get(proposal.claim_id)

    reasons: list[str] = []
    if claim is None:
        reasons.append(f"canonical_claim_unregistered:{proposal.claim_id}")
    if outcome not in {VerificationOutcome.SUPPORTED, VerificationOutcome.PARTIAL}:
        reasons.append(f"verification_outcome_cannot_mint:{outcome.value}")
    reasons.extend(
        _check_evidence_contract(proposal.axis, proposal.evidence_ids, registered)
    )

    if claim is not None:
        subject = promotion_subject_hash(
            claim=claim,
            axis=proposal.axis,
            proposition=proposal.proposition,
            scope_id=proposal.scope_id,
            evidence_ids=proposal.evidence_ids,
            registered_evidence=registered,
        )
        reasons.extend(
            _resolve_or_refuse(
                authority_context,
                attestation_id,
                purpose=AttestationPurpose.SCIENTIFIC_AUTHORITY_PROMOTION,
                subject_hash=subject,
            )
        )
    else:
        reasons.append("resolved_protected_attestation_missing")

    if reasons:
        return ScientificTransitionOutcome(state, False, tuple(sorted(set(reasons))))

    ledger = ledger_from_projection(projection)
    certificate = ledger.commit_verified(
        proposal, certificate_id=certificate_id, outcome=outcome
    )
    if certificate is None:  # pragma: no cover - guarded by outcome check above
        return ScientificTransitionOutcome(state, False, ("verification_outcome_cannot_mint",))
    return ScientificTransitionOutcome(
        replace(
            state,  # type: ignore[type-var]
            scientific_authority=projection_from_ledger(
                ledger, claims=projection.claims, evidence=projection.evidence
            ),
        ),
        True,
        (),
        certificate.certificate_id,
    )


def revoke_scientific_authority(
    state: "object",
    certificate_id: str,
    *,
    reason: str,
    refutation_evidence_ids: Tuple[str, ...] = (),
    authority_context: ProtectedAuthorityContext | None = None,
    attestation_id: str | None = None,
) -> ScientificTransitionOutcome:
    """Retire an active certificate under refuting evidence and a bound attestation.

    Revocation moves ``pi_auth`` just as promotion does, so it carries the same
    binding obligation. A bare ``reason`` string is a declaration, not evidence.
    """

    projection: ScientificAuthorityProjection = state.scientific_authority  # type: ignore[attr-defined]
    registered = projection.evidence_by_id()
    by_id = {item.certificate_id: item for item in projection.certificates}
    certificate = by_id.get(certificate_id)

    reasons: list[str] = []
    if certificate is None:
        reasons.append(f"certificate_unknown:{certificate_id}")
    elif certificate_id not in projection.active_certificate_ids:
        reasons.append(f"certificate_not_active:{certificate_id}")
    if not reason.strip():
        reasons.append("revocation_reason_required")
    if not refutation_evidence_ids:
        reasons.append("revocation_requires_registered_refuting_evidence")
    else:
        unknown = [item for item in refutation_evidence_ids if item not in registered]
        if unknown:
            reasons.append("refutation_evidence_unregistered:" + ",".join(sorted(unknown)))
        elif not any(
            registered[item].kind in _SCIENTIFIC_KINDS for item in refutation_evidence_ids
        ):
            reasons.append("refutation_requires_non_experience_evidence")

    if certificate is not None:
        subject = revocation_subject_hash(
            certificate=certificate,
            reason=reason,
            refutation_evidence_ids=refutation_evidence_ids,
            registered_evidence=registered,
        )
        reasons.extend(
            _resolve_or_refuse(
                authority_context,
                attestation_id,
                purpose=AttestationPurpose.SCIENTIFIC_AUTHORITY_REVOCATION,
                subject_hash=subject,
            )
        )
    else:
        reasons.append("resolved_protected_attestation_missing")

    if reasons:
        return ScientificTransitionOutcome(state, False, tuple(sorted(set(reasons))))

    ledger = ledger_from_projection(projection)
    ledger.revoke(certificate_id, reason=reason)
    return ScientificTransitionOutcome(
        replace(
            state,  # type: ignore[type-var]
            scientific_authority=projection_from_ledger(
                ledger, claims=projection.claims, evidence=projection.evidence
            ),
        ),
        True,
        (),
        certificate_id,
    )


def supersede_scientific_authority(
    state: "object",
    old_certificate_id: str,
    new_proposal: AuthorityProposal,
    *,
    new_certificate_id: str,
    reason: str,
    outcome: VerificationOutcome = VerificationOutcome.SUPPORTED,
    authority_context: ProtectedAuthorityContext | None = None,
    attestation_id: str | None = None,
) -> ScientificTransitionOutcome:
    """Replace an active certificate while preserving the historical one.

    The retired certificate stays in ``certificates`` and its issue/supersede
    events stay in ``events``; only the active view shrinks. That is the
    non-monotone behaviour the invariant is stated over.
    """

    projection: ScientificAuthorityProjection = state.scientific_authority  # type: ignore[attr-defined]
    registered = projection.evidence_by_id()
    by_id = {item.certificate_id: item for item in projection.certificates}
    old_certificate = by_id.get(old_certificate_id)

    reasons: list[str] = []
    if old_certificate is None:
        reasons.append(f"certificate_unknown:{old_certificate_id}")
    elif old_certificate_id not in projection.active_certificate_ids:
        reasons.append(f"certificate_not_active:{old_certificate_id}")
    elif old_certificate.claim_id != new_proposal.claim_id:
        reasons.append("supersession_must_concern_the_same_claim")
    if not reason.strip():
        reasons.append("supersession_reason_required")
    if outcome not in {VerificationOutcome.SUPPORTED, VerificationOutcome.PARTIAL}:
        reasons.append(f"verification_outcome_cannot_mint:{outcome.value}")
    reasons.extend(
        _check_evidence_contract(new_proposal.axis, new_proposal.evidence_ids, registered)
    )

    if old_certificate is not None:
        subject = supersession_subject_hash(
            old_certificate=old_certificate,
            new_proposal=new_proposal,
            reason=reason,
            registered_evidence=registered,
        )
        reasons.extend(
            _resolve_or_refuse(
                authority_context,
                attestation_id,
                purpose=AttestationPurpose.SCIENTIFIC_AUTHORITY_SUPERSESSION,
                subject_hash=subject,
            )
        )
    else:
        reasons.append("resolved_protected_attestation_missing")

    if reasons:
        return ScientificTransitionOutcome(state, False, tuple(sorted(set(reasons))))

    ledger = ledger_from_projection(projection)
    replacement = AuthorityCertificate(
        certificate_id=new_certificate_id,
        claim_id=new_proposal.claim_id,
        axis=new_proposal.axis,
        proposition=new_proposal.proposition,
        scope_id=new_proposal.scope_id,
        evidence_ids=new_proposal.evidence_ids,
        partial=outcome is VerificationOutcome.PARTIAL,
    )
    ledger.supersede(old_certificate_id, replacement, reason=reason)
    return ScientificTransitionOutcome(
        replace(
            state,  # type: ignore[type-var]
            scientific_authority=projection_from_ledger(
                ledger, claims=projection.claims, evidence=projection.evidence
            ),
        ),
        True,
        (),
        new_certificate_id,
    )


# --------------------------------------------------------------------------
# Canonical scientific content registration (authority-inert)
# --------------------------------------------------------------------------


def register_scientific_claim(state: "object", claim: ClaimAtom) -> "object":
    """Add a canonical claim. Never moves ``pi_auth``."""

    if not claim.claim_id.strip() or not claim.text.strip() or not claim.scope.strip():
        raise ValueError("claim atom requires id, text and scope")
    projection: ScientificAuthorityProjection = state.scientific_authority  # type: ignore[attr-defined]
    existing = projection.claim_by_id().get(claim.claim_id)
    if existing is not None:
        if existing != claim:
            raise ValueError("claim identity already registered with different content")
        return state
    return replace(  # type: ignore[type-var]
        state,
        scientific_authority=replace(
            projection,
            claims=tuple(sorted(projection.claims + (claim,), key=lambda i: i.claim_id)),
        ),
    )


def register_scientific_evidence(
    state: "object", binding: ScientificEvidenceBinding
) -> "object":
    """Add a content-bound evidence root. Never moves ``pi_auth``."""

    projection: ScientificAuthorityProjection = state.scientific_authority  # type: ignore[attr-defined]
    existing = projection.evidence_by_id().get(binding.evidence_id)
    if existing is not None:
        if existing != binding:
            raise ValueError("evidence identity already registered with different content")
        return state
    return replace(  # type: ignore[type-var]
        state,
        scientific_authority=replace(
            projection,
            evidence=tuple(
                sorted(projection.evidence + (binding,), key=lambda i: i.evidence_id)
            ),
        ),
    )
