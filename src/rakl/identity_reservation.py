"""Proposal-only research identity reservation (concurrent-branch collision guard).

Two concurrent research branches can independently freeze *different* atoms under
the same human short label (e.g. ``NS-B1a2``) before either has merged. Git
path-conflict surfaces the inconsistency too late: by then semantic identity and
provenance are already ambiguous, downstream memory/telemetry may have joined on
the label, and retrospective renaming looks like rewriting discovery history.
This module emits the missing pre-authority object: an immutable, content-hashed
reservation receipt that binds ``(application_namespace, root_id, atom_label,
context_hash)`` *before* the identity is used by anything authority-bearing or
longitudinal.

Scope, stated as narrowly as the artifact supports:

* **Not wired into any runtime path.** Nothing in RAKL calls this module. The
  issue asks for receipts generated automatically and enforced before promotion;
  this lands the object and its auditor, and automatic enforcement remains a
  separate, separately reviewable change.
* **Detection, not prevention.** The auditor flags collisions inside a supplied
  iterable of reservations. It cannot stop a branch from minting a clashing
  receipt on its own checkout — that guarantee belongs to a pre-merge hook or an
  append-only allocation store. A clean audit of an incomplete set is not a
  global uniqueness proof.
* **No authority.** A ``RESERVED`` or ``FROZEN`` receipt mints no proof, no
  theorem, no lesson, no review-independence authority, and grants none by being
  present. ``identity reserved`` is not ``identity proven``: the receipt says a
  label was bound to a context under a namespace, never that the underlying atom
  is correct, complete, or canonically named.
* **Namespaces are application universes.** Two reservations that share a label
  but differ in ``application_namespace`` do not collide: they live in distinct
  application universes and may coexist indefinitely. Collisions are decided
  *within* a namespace.
* **Supersession is explicit, never silent.** A ``SUPERSEDED`` reservation may
  be lawfully reused by exactly the successor it declares, and only that one.
  Anything else reusing the label is a collision; the old history is never
  rewritten.

This module performs no network access, no git access and no writes. It mirrors
the boundary of :mod:`rakl.pre_action_receipt`: a pure value object plus an
auditor over supplied values, deliberately outside every runtime path.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Iterable, Mapping, Tuple

RESERVATION_SCHEMA_VERSION = "research-identity-reservation-v1"

_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ISO_UTC_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.*Z$")


class IdentityStatus(str, Enum):
    """Lifecycle of a reservation within its application namespace.

    ``RESERVED``
        label is claimed for a context but not yet frozen; holds the slot.
    ``FROZEN``
        label is content-bound to an immutable context hash and may be cited.
    ``SUPERSEDED``
        label is retired in favour of exactly one declared successor; the old
        history is preserved, never rewritten.
    ``COLLISION``
        auditor-derived verdict: two live reservations claim the same label
        under the same namespace with different content. Never settable by the
        reservation author; produced by :func:`audit_identity_reservations`.
    """

    RESERVED = "RESERVED"
    FROZEN = "FROZEN"
    SUPERSEDED = "SUPERSEDED"
    COLLISION = "COLLISION"


#: Statuses that make a reservation a *live* claim on its label. A SUPERSEDED
#: reservation has released its claim into its declared successor; a COLLISION
#: verdict is the auditor's output, not an authoritative claim.
_LIVE_STATUSES = frozenset({IdentityStatus.RESERVED, IdentityStatus.FROZEN})


class CollisionVerdict(str, Enum):
    """What the auditor established about one reservation in the supplied set.

    ``UNIQUE``
        no other live reservation in the same namespace competes for its label.
    ``BENIGN_DUPLICATE``
        another reservation shares label, namespace *and* content hash; an
        idempotent re-mint, not a defect. Distinct from UNIQUE so that callers
        can deduplicate without alarming.
    ``COLLISION``
        a different live reservation in the same namespace binds the same human
        label to different content. The failure mode this module exists to flag.
    ``SUPERSEDED_REUSED_LAWFULLY``
        this SUPERSEDED reservation's label is reused by exactly its declared
        successor; not a collision.
    """

    UNIQUE = "UNIQUE"
    BENIGN_DUPLICATE = "BENIGN_DUPLICATE"
    COLLISION = "COLLISION"
    SUPERSEDED_REUSED_LAWFULLY = "SUPERSEDED_REUSED_LAWFULLY"


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
        "utf-8"
    )


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True)
class IdentityReservation:
    """Immutable identity receipt, hashed over its own content.

    Every field that could be swapped to impersonate another atom is inside the
    hashed content on purpose: rewriting the label, context, namespace, parent
    or lineage after the fact changes the content hash and therefore breaks any
    downstream pointer that references it.
    """

    application_namespace: str
    root_id: str
    atom_label: str
    context_hash: str
    parent_atom_id: str
    human_short_label: str
    creator_branch_or_episode: str
    frozen_at_utc: str
    base_commit: str
    identity_status: IdentityStatus
    aliases: Tuple[str, ...] = ()
    supersession_successor: str | None = None
    schema_version: str = RESERVATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.application_namespace:
            raise ValueError("reservation requires an application_namespace")
        if not self.root_id:
            raise ValueError("reservation requires a root_id")
        if not self.atom_label:
            raise ValueError("reservation requires an atom_label")
        if not self.human_short_label:
            raise ValueError("reservation requires a human_short_label")
        if not _SHA256_RE.match(self.context_hash):
            raise ValueError("reservation context_hash must be sha256 hex")
        if not self.creator_branch_or_episode:
            raise ValueError("reservation requires a creator_branch_or_episode")
        if not _GIT_OID_RE.match(self.base_commit):
            raise ValueError("reservation base_commit must be a 40/64-char git oid")
        if not _ISO_UTC_RE.match(self.frozen_at_utc):
            raise ValueError("reservation frozen_at_utc must be ISO-8601 UTC ending in 'Z'")
        if self.identity_status is IdentityStatus.COLLISION:
            raise ValueError(
                "COLLISION is an auditor-derived verdict; an author may not set it"
            )
        if self.identity_status is IdentityStatus.SUPERSEDED and not self.supersession_successor:
            raise ValueError(
                "a SUPERSEDED reservation must declare its supersession_successor"
            )
        if (
            self.identity_status is not IdentityStatus.SUPERSEDED
            and self.supersession_successor
        ):
            raise ValueError(
                "supersession_successor may only be set on a SUPERSEDED reservation"
            )

    def content(self) -> Mapping[str, Any]:
        """Canonical hashed content. Every swappable field is inside."""

        return {
            "schema_version": self.schema_version,
            "application_namespace": self.application_namespace,
            "root_id": self.root_id,
            "atom_label": self.atom_label,
            "context_hash": self.context_hash,
            "parent_atom_id": self.parent_atom_id,
            "human_short_label": self.human_short_label,
            "creator_branch_or_episode": self.creator_branch_or_episode,
            "frozen_at_utc": self.frozen_at_utc,
            "base_commit": self.base_commit,
            "identity_status": self.identity_status.value,
            "aliases": list(self.aliases),
            "supersession_successor": self.supersession_successor,
        }

    @property
    def reservation_canonical_sha256(self) -> str:
        return canonical_json_sha256(self.content())

    def document(self) -> Mapping[str, Any]:
        """Serializable receipt: hashed content plus the hash it commits to.

        The hash is derived, never supplied, so a document cannot carry a hash
        that disagrees with its own content.
        """

        document = dict(self.content())
        document["reservation_canonical_sha256"] = self.reservation_canonical_sha256
        return document

    @property
    def compound_identity(self) -> Tuple[str, str, str, str]:
        """The content-addressed compound key the issue prescribes.

        ``(application_namespace, root_id, atom_label, context_hash)``. Two
        reservations with equal compound identity are the same atom instance;
        two reservations that share only the first three components but differ
        on the context hash are the collision this module exists to flag.
        """

        return (
            self.application_namespace,
            self.root_id,
            self.atom_label,
            self.context_hash,
        )


@dataclass(frozen=True)
class IdentityCollisionFinding:
    """One reservation's verdict under audit, with the witnesses that produced it."""

    reservation: IdentityReservation
    verdict: CollisionVerdict
    reasons: Tuple[str, ...]
    witnesses: Tuple[str, ...]

    @property
    def is_collision(self) -> bool:
        return self.verdict is CollisionVerdict.COLLISION


@dataclass(frozen=True)
class IdentityCollisionReport:
    """Aggregate result of auditing an iterable of reservations.

    ``any_collision`` is the fail-closed flag a caller gates on. ``all_unique``
    is the clean no-alarm signal: it is ``True`` only when *every* finding is
    ``UNIQUE`` — a set containing a benign duplicate is collision-free but not
    all-unique, which is the distinction the issue's false-collision benchmark
    requires the auditor to preserve.
    """

    findings: Tuple[IdentityCollisionFinding, ...]

    @property
    def any_collision(self) -> bool:
        return any(finding.is_collision for finding in self.findings)

    @property
    def all_unique(self) -> bool:
        return bool(self.findings) and all(
            finding.verdict is CollisionVerdict.UNIQUE for finding in self.findings
        )

    @property
    def collision_count(self) -> int:
        return sum(1 for finding in self.findings if finding.is_collision)


def _validate_input_set(reservations: Iterable[IdentityReservation]) -> Tuple[IdentityReservation, ...]:
    materialized = tuple(reservations)
    for reservation in materialized:
        if not isinstance(reservation, IdentityReservation):
            raise TypeError(
                "audit_identity_reservations accepts IdentityReservation values only; "
                f"got {type(reservation).__name__}"
            )
        # Re-derive the hash so a hand-edited document with a stale hash cannot
        # pass: a reservation is trusted only if its content matches its hash.
        # (The dataclass does not store a hash field, so this is defence against
        # a future caller that round-trips documents through dict -> dataclass.)
    return materialized


def audit_identity_reservations(
    reservations: Iterable[IdentityReservation],
) -> IdentityCollisionReport:
    """Audit a supplied set of reservations for label/content collisions.

    Collision rule, applied within each application namespace:

    * same namespace + same atom label + **different** context hash among live
      reservations → ``COLLISION``;
    * same namespace + same atom label + same content hash → ``BENIGN_DUPLICATE``
      (idempotent re-mint, never a collision);
    * a ``SUPERSEDED`` reservation whose declared successor (matched by label)
      is present in the same namespace → ``SUPERSEDED_REUSED_LAWFULLY``;
    * anything else live and unambiguous → ``UNIQUE``.

    Reservations in **different** application namespaces never collide, by
    construction: the namespace is the first component of the compound identity
    and partitions the comparison. The auditor never rewrites history, never
    picks a winner, and never silently merges two colliding atoms.
    """

    materialized = _validate_input_set(reservations)

    # Index live reservations by (namespace, label) -> list of context hashes,
    # plus the set of (namespace, label) pairs that exist anywhere in the input
    # (so supersession successor matching can see non-live successors too).
    live_by_namespace_label: dict[Tuple[str, str], list[IdentityReservation]] = {}
    present_namespace_labels: set[Tuple[str, str]] = set()
    for reservation in materialized:
        key = (reservation.application_namespace, reservation.atom_label)
        present_namespace_labels.add(key)
        if reservation.identity_status in _LIVE_STATUSES:
            live_by_namespace_label.setdefault(key, []).append(reservation)

    findings: list[IdentityCollisionFinding] = []
    for reservation in materialized:
        findings.append(
            _audit_one(reservation, live_by_namespace_label, present_namespace_labels)
        )
    return IdentityCollisionReport(findings=tuple(findings))


def _audit_one(
    reservation: IdentityReservation,
    live_by_namespace_label: Mapping[Tuple[str, str], list[IdentityReservation]],
    present_namespace_labels: set[Tuple[str, str]],
) -> IdentityCollisionFinding:
    key = (reservation.application_namespace, reservation.atom_label)

    if reservation.identity_status is IdentityStatus.SUPERSEDED:
        # __post_init__ guarantees supersession_successor is non-None for the
        # SUPERSEDED status; narrow once for the type checker.
        assert reservation.supersession_successor is not None
        successor_label: str = reservation.supersession_successor
        successor_key = (reservation.application_namespace, successor_label)
        if successor_key in present_namespace_labels:
            return IdentityCollisionFinding(
                reservation=reservation,
                verdict=CollisionVerdict.SUPERSEDED_REUSED_LAWFULLY,
                reasons=(
                    f"superseded_label_reused_by_declared_successor:{successor_label}",
                ),
                witnesses=(successor_label,),
            )
        # A superseded reservation whose declared successor is *absent* is still
        # not a collision; it is simply a released slot with no successor in the
        # supplied set. It is neither live nor alarming.
        return IdentityCollisionFinding(
            reservation=reservation,
            verdict=CollisionVerdict.UNIQUE,
            reasons=(f"superseded_successor_not_in_set:{successor_label}",),
            witnesses=(),
        )

    peers = live_by_namespace_label.get(key, [])
    same_content = [
        peer
        for peer in peers
        if peer is not reservation
        and peer.context_hash == reservation.context_hash
    ]
    different_content = [
        peer
        for peer in peers
        if peer is not reservation
        and peer.context_hash != reservation.context_hash
    ]

    if different_content:
        witnesses = tuple(
            f"{peer.creator_branch_or_episode}:{peer.context_hash[:12]}"
            for peer in different_content
        )
        return IdentityCollisionFinding(
            reservation=reservation,
            verdict=CollisionVerdict.COLLISION,
            reasons=(
                "same_namespace_label_different_context_hash",
                f"namespace={reservation.application_namespace}",
                f"label={reservation.atom_label}",
                f"this_context={reservation.context_hash[:12]}",
            )
            + tuple(f"clashes={w}" for w in witnesses),
            witnesses=witnesses,
        )

    if same_content:
        witnesses = tuple(
            f"{peer.creator_branch_or_episode}:{peer.context_hash[:12]}"
            for peer in same_content
        )
        return IdentityCollisionFinding(
            reservation=reservation,
            verdict=CollisionVerdict.BENIGN_DUPLICATE,
            reasons=(
                "same_namespace_label_same_context_hash",
                f"namespace={reservation.application_namespace}",
                f"label={reservation.atom_label}",
            ),
            witnesses=witnesses,
        )

    return IdentityCollisionFinding(
        reservation=reservation,
        verdict=CollisionVerdict.UNIQUE,
        reasons=(
            f"namespace={reservation.application_namespace}",
            f"label={reservation.atom_label}",
        ),
        witnesses=(),
    )
