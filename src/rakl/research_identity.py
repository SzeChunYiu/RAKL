"""Proposal-only research atom/candidate identity reservation and collision detection.

Two concurrent research branches can independently freeze *different* mathematics under
the same human label (issue #142: two `NS-B1a2` atoms, both using `NS-B1a2-C001`). Git
path conflicts surface that late and only if the two branches happen to touch the same
files; they do not solve semantic identity. Memory, failure reuse, telemetry and
case-study attribution all join on identity, so a duplicated human label silently
corrupts every downstream join.

The rule this module encodes:

    A human label such as ``NS-B1a2`` must never be the sole global key.

Identity is the compound
``(application_namespace, root_id, atom_label, context_hash)``, content-addressed into a
stable ``uid``. The readable label is preserved as an alias, not as a primary key.

This module performs no network, git or filesystem access: every observation is supplied
by the caller. It is **proposal-only telemetry**. It mints no mathematical, tool, method,
review-independence or framework authority, and registering an identity says nothing about
whether the research under it is correct.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Dict, Iterable, List, Mapping, Tuple


class IdentityStatus(str, Enum):
    """Lifecycle of one allocated identity.

    ``COLLISION`` is a terminal observation about a *pair*; it never rewrites either
    party's own history. Both immutable histories survive under distinct uids.
    """

    RESERVED = "RESERVED"
    FROZEN = "FROZEN"
    SUPERSEDED = "SUPERSEDED"
    COLLISION = "COLLISION"


class RegistrationVerdict(str, Enum):
    """Outcome of offering one identity to the registry.

    ``ALIAS_CANDIDATE`` is deliberately not ``DEDUPLICATED``: equal content under
    different labels is a *candidate* for aliasing that a human or a separate
    equivalence procedure must confirm. Equal bytes are not proved equal meaning.
    """

    REGISTERED = "REGISTERED"
    DEDUPLICATED = "DEDUPLICATED"
    LABEL_COLLISION = "LABEL_COLLISION"
    ALIAS_CANDIDATE = "ALIAS_CANDIDATE"
    REJECTED = "REJECTED"
    CANNOT_CHECK = "CANNOT_CHECK"


class ResolutionVerdict(str, Enum):
    """Outcome of asking the registry to turn a human label into an identity."""

    RESOLVED = "RESOLVED"
    AMBIGUOUS_LABEL = "AMBIGUOUS_LABEL"
    NOT_FOUND = "NOT_FOUND"


REQUIRED_IDENTITY_FIELDS: Tuple[str, ...] = (
    "application_namespace",
    "root_id",
    "atom_label",
    "context_hash",
    "creator_branch",
    "base_commit",
    "created_at_utc",
)


def _canonical_uid(
    *, application_namespace: str, root_id: str, atom_label: str, context_hash: str
) -> str:
    """Content-address the compound identity.

    The label participates so that two genuinely different atoms that happen to share a
    context hash stay distinguishable, and the context hash participates so that the same
    label over different frozen content cannot collapse.
    """

    payload = json.dumps(
        {
            "application_namespace": application_namespace,
            "root_id": root_id,
            "atom_label": atom_label,
            "context_hash": context_hash,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ResearchIdentity:
    """One allocated research atom identity.

    ``uid`` is derived, never supplied: a caller cannot assert an identity that its own
    coordinates do not produce.
    """

    application_namespace: str
    root_id: str
    atom_label: str
    context_hash: str
    creator_branch: str
    base_commit: str
    created_at_utc: str
    status: IdentityStatus = IdentityStatus.RESERVED
    parent_atom_uid: str | None = None
    creator_episode_id: str | None = None
    aliases: Tuple[str, ...] = ()
    supersedes: Tuple[str, ...] = ()
    evidence_pointers: Tuple[str, ...] = ()

    @property
    def uid(self) -> str:
        return _canonical_uid(
            application_namespace=self.application_namespace,
            root_id=self.root_id,
            atom_label=self.atom_label,
            context_hash=self.context_hash,
        )

    @property
    def label_key(self) -> Tuple[str, str, str]:
        """The *narrative* key that must not be used as a global primary key."""

        return (self.application_namespace, self.root_id, self.atom_label)


@dataclass(frozen=True)
class CandidateIdentity:
    """A candidate id (`C001`) scoped by its exact parent atom uid.

    Two branches may both use ``C001`` without colliding, provided they hang off
    different atom uids. That is the normal case and must not be reported as a defect.
    """

    parent_atom_uid: str
    candidate_label: str
    content_hash: str

    @property
    def uid(self) -> str:
        payload = json.dumps(
            {
                "parent_atom_uid": self.parent_atom_uid,
                "candidate_label": self.candidate_label,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class IdentityCollision:
    """An immutable record that two identities claimed one human label.

    Neither party is rewritten. The collision is itself negative/process history.
    """

    label_key: Tuple[str, str, str]
    incumbent_uid: str
    challenger_uid: str
    incumbent_context_hash: str
    challenger_context_hash: str
    incumbent_branch: str
    challenger_branch: str
    reasons: Tuple[str, ...]


@dataclass(frozen=True)
class RegistrationReport:
    verdict: RegistrationVerdict
    reasons: Tuple[str, ...]
    uid: str | None = None
    conflicting_uids: Tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolutionReport:
    verdict: ResolutionVerdict
    reasons: Tuple[str, ...]
    uids: Tuple[str, ...] = ()


def _structural_failures(identity: ResearchIdentity) -> List[str]:
    failures: List[str] = []
    for name in REQUIRED_IDENTITY_FIELDS:
        if not str(getattr(identity, name, "") or "").strip():
            failures.append(f"identity_field_missing:{name}")
    return failures


@dataclass
class ResearchIdentityRegistry:
    """Append-only registry of research identities.

    Registration never mutates or deletes an existing entry. Supersession is recorded as
    a new explicit edge; a collision is recorded as a new immutable observation.
    """

    identities: Dict[str, ResearchIdentity] = field(default_factory=dict)
    collisions: List[IdentityCollision] = field(default_factory=list)
    candidates: Dict[str, CandidateIdentity] = field(default_factory=dict)

    # -- registration ----------------------------------------------------------

    def register(self, identity: ResearchIdentity) -> RegistrationReport:
        failures = _structural_failures(identity)
        if failures:
            return RegistrationReport(
                RegistrationVerdict.REJECTED, tuple(failures)
            )

        uid = identity.uid
        if identity.parent_atom_uid is not None:
            parent = self.identities.get(identity.parent_atom_uid)
            if parent is None:
                return RegistrationReport(
                    RegistrationVerdict.CANNOT_CHECK,
                    ("parent_atom_uid_not_registered",),
                    uid=uid,
                )
            if parent.status is IdentityStatus.SUPERSEDED:
                # Case 4: the parent moved under an active child branch. This is not a
                # collision, but the child must not silently inherit a retired parent.
                return RegistrationReport(
                    RegistrationVerdict.CANNOT_CHECK,
                    ("parent_atom_superseded_resolve_lineage_explicitly",),
                    uid=uid,
                    conflicting_uids=(parent.uid,),
                )

        existing = self.identities.get(uid)
        if existing is not None:
            # Case 1: identical compound key. Same label, same frozen content/context.
            return RegistrationReport(
                RegistrationVerdict.DEDUPLICATED,
                ("identical_compound_identity_already_registered",),
                uid=uid,
            )

        label_siblings = [
            other
            for other in self.identities.values()
            if other.label_key == identity.label_key
        ]
        if label_siblings:
            # Case 2 / case 6: same human label, different frozen content.
            reasons = ["same_label_different_context_hash"]
            for sibling in label_siblings:
                if sibling.base_commit != identity.base_commit:
                    reasons.append("challenger_base_commit_differs_from_incumbent")
                    break
            for sibling in label_siblings:
                self.collisions.append(
                    IdentityCollision(
                        label_key=identity.label_key,
                        incumbent_uid=sibling.uid,
                        challenger_uid=uid,
                        incumbent_context_hash=sibling.context_hash,
                        challenger_context_hash=identity.context_hash,
                        incumbent_branch=sibling.creator_branch,
                        challenger_branch=identity.creator_branch,
                        reasons=tuple(dict.fromkeys(reasons)),
                    )
                )
            # Both histories survive: the challenger is still stored, under its own uid,
            # flagged COLLISION. Nothing about the incumbent is rewritten.
            self.identities[uid] = replace(identity, status=IdentityStatus.COLLISION)
            return RegistrationReport(
                RegistrationVerdict.LABEL_COLLISION,
                tuple(dict.fromkeys(reasons)),
                uid=uid,
                conflicting_uids=tuple(sibling.uid for sibling in label_siblings),
            )

        content_twins = [
            other
            for other in self.identities.values()
            if other.context_hash == identity.context_hash
            and other.root_id == identity.root_id
            and other.application_namespace == identity.application_namespace
        ]
        self.identities[uid] = identity
        if content_twins:
            # Case 3: different labels, same content. A candidate for aliasing only.
            return RegistrationReport(
                RegistrationVerdict.ALIAS_CANDIDATE,
                (
                    "same_context_hash_under_different_label",
                    "alias_candidate_requires_explicit_equivalence_decision",
                ),
                uid=uid,
                conflicting_uids=tuple(twin.uid for twin in content_twins),
            )
        return RegistrationReport(
            RegistrationVerdict.REGISTERED, ("identity_registered",), uid=uid
        )

    def register_candidate(self, candidate: CandidateIdentity) -> RegistrationReport:
        """Register a candidate id scoped to an exact atom uid.

        Case 5: the same ``C001`` label under two *different* atom uids is normal and
        must not be reported as a collision.
        """

        if candidate.parent_atom_uid not in self.identities:
            return RegistrationReport(
                RegistrationVerdict.CANNOT_CHECK,
                ("candidate_parent_atom_uid_not_registered",),
            )
        uid = candidate.uid
        existing = self.candidates.get(uid)
        if existing is not None:
            if existing.content_hash == candidate.content_hash:
                return RegistrationReport(
                    RegistrationVerdict.DEDUPLICATED,
                    ("identical_candidate_already_registered",),
                    uid=uid,
                )
            return RegistrationReport(
                RegistrationVerdict.LABEL_COLLISION,
                ("same_candidate_label_under_one_atom_with_different_content",),
                uid=uid,
                conflicting_uids=(uid,),
            )
        self.candidates[uid] = candidate
        return RegistrationReport(
            RegistrationVerdict.REGISTERED, ("candidate_registered",), uid=uid
        )

    # -- supersession ----------------------------------------------------------

    def supersede(self, *, retired_uid: str, successor_uid: str) -> RegistrationReport:
        """Record an explicit supersession edge without deleting either party."""

        if retired_uid not in self.identities or successor_uid not in self.identities:
            return RegistrationReport(
                RegistrationVerdict.CANNOT_CHECK,
                ("supersession_endpoint_not_registered",),
            )
        retired = self.identities[retired_uid]
        successor = self.identities[successor_uid]
        self.identities[retired_uid] = replace(
            retired, status=IdentityStatus.SUPERSEDED
        )
        self.identities[successor_uid] = replace(
            successor, supersedes=tuple(dict.fromkeys(successor.supersedes + (retired_uid,)))
        )
        return RegistrationReport(
            RegistrationVerdict.REGISTERED,
            ("supersession_recorded",),
            uid=successor_uid,
        )

    # -- resolution ------------------------------------------------------------

    def resolve_label(
        self, *, application_namespace: str, root_id: str, atom_label: str
    ) -> ResolutionReport:
        """Turn a human label into an identity, failing closed when it is ambiguous.

        This is the enforcement point for the module's central rule: once a label maps to
        more than one frozen identity, every downstream memory/telemetry/metrics query
        must choose an exact uid instead of the readable label.
        """

        key = (application_namespace, root_id, atom_label)
        matches = tuple(
            sorted(other.uid for other in self.identities.values() if other.label_key == key)
        )
        if not matches:
            return ResolutionReport(ResolutionVerdict.NOT_FOUND, ("label_not_registered",))
        if len(matches) > 1:
            return ResolutionReport(
                ResolutionVerdict.AMBIGUOUS_LABEL,
                (
                    "label_maps_to_multiple_frozen_identities",
                    "downstream_query_must_supply_exact_uid",
                ),
                uids=matches,
            )
        return ResolutionReport(
            ResolutionVerdict.RESOLVED, ("label_uniquely_resolved",), uids=matches
        )


@dataclass(frozen=True)
class CollisionDetectionScore:
    """Benchmark score over a labelled fixture set.

    Recall alone is not a sufficient target: a detector that reports every registration
    as a collision has perfect recall and is useless, so the false-positive rate is
    scored alongside it and neither is compensatory.
    """

    total: int
    expected_collisions: int
    detected_collisions: int
    false_collisions: int

    @property
    def recall(self) -> float:
        if self.expected_collisions == 0:
            return 1.0
        return self.detected_collisions / self.expected_collisions

    @property
    def false_collision_rate(self) -> float:
        benign = self.total - self.expected_collisions
        if benign == 0:
            return 0.0
        return self.false_collisions / benign


def score_collision_detection(
    outcomes: Iterable[Tuple[RegistrationVerdict, bool]]
) -> CollisionDetectionScore:
    """Score (observed_verdict, is_expected_collision) pairs."""

    total = 0
    expected = 0
    detected = 0
    false_positive = 0
    for verdict, is_collision in outcomes:
        total += 1
        flagged = verdict is RegistrationVerdict.LABEL_COLLISION
        if is_collision:
            expected += 1
            if flagged:
                detected += 1
        elif flagged:
            false_positive += 1
    return CollisionDetectionScore(
        total=total,
        expected_collisions=expected,
        detected_collisions=detected,
        false_collisions=false_positive,
    )


def registry_from_records(records: Iterable[Mapping[str, object]]) -> ResearchIdentityRegistry:
    """Build a registry from plain mappings, preserving registration order."""

    registry = ResearchIdentityRegistry()
    for record in records:
        registry.register(
            ResearchIdentity(
                application_namespace=str(record["application_namespace"]),
                root_id=str(record["root_id"]),
                atom_label=str(record["atom_label"]),
                context_hash=str(record["context_hash"]),
                creator_branch=str(record["creator_branch"]),
                base_commit=str(record["base_commit"]),
                created_at_utc=str(record["created_at_utc"]),
            )
        )
    return registry
