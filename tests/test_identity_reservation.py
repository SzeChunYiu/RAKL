"""Hostile-world tests for :mod:`rakl.identity_reservation`.

Mirrors the discipline of ``pre_action_receipt``'s tests: every auditor verdict
is asserted both ways (collision when it must alarm, no-alarm on the benign
controls), and the content hash is shown to cover every swappable field. The
"hostile worlds" are the six concurrent-branch scenarios in issue #142's
benchmark, parametrized so a regression on any one fails loudly.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Callable

import pytest

from rakl.identity_reservation import (
    CollisionVerdict,
    IdentityReservation,
    IdentityStatus,
    audit_identity_reservations,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_NS = "SzeChunYiu/RAKL_math"
_ROOT = "NS"
_PARENT = "NS-B1"
_BASE = "a" * 40
_TS_A = "2026-08-11T09:00:00Z"
_TS_B = "2026-08-11T09:05:00Z"
_HASH_COMPACTNESS = "c1" * 32  # compactness/time-drift route content
_HASH_KINETIC = "0b" * 32  # kinetic-energy/core-packing route content
_HASH_SAME = "5a" * 32  # identical content re-minted on a second branch


def _make(
    *,
    application_namespace: str = _NS,
    root_id: str = _ROOT,
    atom_label: str = "NS-B1a2",
    context_hash: str = _HASH_COMPACTNESS,
    parent_atom_id: str = _PARENT,
    human_short_label: str = "NavierStokes-B1a2",
    creator_branch_or_episode: str = "research/ns-b1a2-selfsimilar-time-drift-20260811",
    frozen_at_utc: str = _TS_A,
    base_commit: str = _BASE,
    identity_status: IdentityStatus = IdentityStatus.FROZEN,
    aliases: tuple[str, ...] = (),
    supersession_successor: str | None = None,
) -> IdentityReservation:
    return IdentityReservation(
        application_namespace=application_namespace,
        root_id=root_id,
        atom_label=atom_label,
        context_hash=context_hash,
        parent_atom_id=parent_atom_id,
        human_short_label=human_short_label,
        creator_branch_or_episode=creator_branch_or_episode,
        frozen_at_utc=frozen_at_utc,
        base_commit=base_commit,
        identity_status=identity_status,
        aliases=aliases,
        supersession_successor=supersession_successor,
    )


# ---------------------------------------------------------------------------
# (a) same label, different context hash, same namespace -> COLLISION
# ---------------------------------------------------------------------------


def test_same_label_different_context_same_namespace_is_collision():
    branch_a = _make(
        creator_branch_or_episode="research/ns-b1a2-selfsimilar-time-drift-20260811",
        context_hash=_HASH_COMPACTNESS,
        frozen_at_utc=_TS_A,
    )
    branch_b = _make(
        creator_branch_or_episode="research/ns-b1a2-critical-blob-packing-20260811",
        context_hash=_HASH_KINETIC,
        frozen_at_utc=_TS_B,
        base_commit="b" * 40,
    )
    report = audit_identity_reservations([branch_a, branch_b])

    assert report.any_collision is True
    assert report.collision_count == 2
    assert report.all_unique is False
    verdicts = [finding.verdict for finding in report.findings]
    assert verdicts == [CollisionVerdict.COLLISION, CollisionVerdict.COLLISION]
    # Both branches are flagged, and each names the other as a witness.
    reasons_all = " ".join(reason for f in report.findings for reason in f.reasons)
    assert "same_namespace_label_different_context_hash" in reasons_all
    assert "critical-blob-packing" in reasons_all
    assert "selfsimilar-time-drift" in reasons_all


# ---------------------------------------------------------------------------
# (b) same label + same context hash, same namespace -> benign duplicate
# ---------------------------------------------------------------------------


def test_same_label_same_context_same_namespace_is_benign_duplicate():
    branch_a = _make(
        creator_branch_or_episode="research/branch-a",
        context_hash=_HASH_SAME,
    )
    branch_b = _make(
        creator_branch_or_episode="research/branch-b",
        context_hash=_HASH_SAME,
        frozen_at_utc=_TS_B,
    )
    report = audit_identity_reservations([branch_a, branch_b])

    assert report.any_collision is False
    assert report.collision_count == 0
    # all_unique is deliberately False here: a benign duplicate is collision-free
    # but not UNIQUE. This is the distinction #142's false-collision benchmark
    # requires.
    assert report.all_unique is False
    verdicts = sorted(finding.verdict for finding in report.findings)
    assert verdicts == [
        CollisionVerdict.BENIGN_DUPLICATE,
        CollisionVerdict.BENIGN_DUPLICATE,
    ]


# ---------------------------------------------------------------------------
# (c) same label, different namespaces -> no collision
# ---------------------------------------------------------------------------


def test_same_label_different_namespaces_do_not_collide():
    math_ns = _make(
        application_namespace="SzeChunYiu/RAKL_math",
        context_hash=_HASH_COMPACTNESS,
    )
    physics_ns = _make(
        application_namespace="SzeChunYiu/RAKL_physics",
        context_hash=_HASH_KINETIC,
        frozen_at_utc=_TS_B,
    )
    report = audit_identity_reservations([math_ns, physics_ns])

    assert report.any_collision is False
    assert report.all_unique is True
    assert [finding.verdict for finding in report.findings] == [
        CollisionVerdict.UNIQUE,
        CollisionVerdict.UNIQUE,
    ]


# ---------------------------------------------------------------------------
# (d) SUPERSEDED label lawfully reused by its declared successor -> no collision
# ---------------------------------------------------------------------------


def test_superseded_label_reused_by_declared_successor_is_not_collision():
    retired = _make(
        atom_label="NS-B1a2",
        context_hash=_HASH_COMPACTNESS,
        creator_branch_or_episode="research/ns-b1a2-legacy",
        identity_status=IdentityStatus.SUPERSEDED,
        supersession_successor="NS-B1a2-v2",
    )
    successor = _make(
        atom_label="NS-B1a2-v2",
        context_hash=_HASH_KINETIC,
        creator_branch_or_episode="research/ns-b1a2-rewrite",
        frozen_at_utc=_TS_B,
    )
    report = audit_identity_reservations([retired, successor])

    assert report.any_collision is False
    assert report.all_unique is False  # successor is UNIQUE, retired is lawful-reuse
    by_label = {f.reservation.atom_label: f.verdict for f in report.findings}
    assert by_label["NS-B1a2"] is CollisionVerdict.SUPERSEDED_REUSED_LAWFULLY
    assert by_label["NS-B1a2-v2"] is CollisionVerdict.UNIQUE


def test_superseded_label_reused_by_undeclared_label_is_collision_for_the_live_one():
    """A SUPERSEDED reservation releases its label only to its *declared*
    successor. A different live label reusing the slot still collides with any
    other live holder of that label."""
    retired = _make(
        atom_label="NS-B1a2",
        context_hash=_HASH_COMPACTNESS,
        identity_status=IdentityStatus.SUPERSEDED,
        supersession_successor="NS-B1a2-v2",
    )
    # An unrelated branch re-mints the superseded label as a fresh FROZEN atom
    # with different content; this is the collision supersession is meant to
    # prevent when no legitimate successor exists.
    interloper_a = _make(
        atom_label="NS-B1a2",
        context_hash=_HASH_KINETIC,
        creator_branch_or_episode="research/ns-b1a2-interloper-a",
        frozen_at_utc=_TS_B,
    )
    interloper_b = _make(
        atom_label="NS-B1a2",
        context_hash="9e" * 32,
        creator_branch_or_episode="research/ns-b1a2-interloper-b",
        frozen_at_utc="2026-08-11T09:06:00Z",
    )
    report = audit_identity_reservations([retired, interloper_a, interloper_b])

    assert report.any_collision is True
    # The retired reservation itself is still lawfully reusable by its declared
    # successor label (which happens not to be in this set as a peer of the
    # retired atom), so it does not collide; the two interlopers collide.
    retired_finding = next(
        f for f in report.findings if f.reservation is retired
    )
    assert retired_finding.verdict is not CollisionVerdict.COLLISION


# ---------------------------------------------------------------------------
# (e) clean all-unique set -> no alarm
# ---------------------------------------------------------------------------


def test_clean_all_unique_set_raises_no_alarm():
    a = _make(atom_label="NS-B1a2", context_hash=_HASH_COMPACTNESS)
    b = _make(
        atom_label="NS-B1a3",
        context_hash=_HASH_KINETIC,
        frozen_at_utc=_TS_B,
    )
    c = _make(
        atom_label="NS-B1a4",
        context_hash="9e" * 32,
        frozen_at_utc="2026-08-11T09:06:00Z",
    )
    report = audit_identity_reservations([a, b, c])

    assert report.any_collision is False
    assert report.all_unique is True
    assert report.collision_count == 0


def test_empty_set_is_clean_no_alarm():
    report = audit_identity_reservations([])
    assert report.any_collision is False
    assert report.collision_count == 0
    # all_unique is False for an empty set: there is nothing to certify.
    assert report.all_unique is False


# ---------------------------------------------------------------------------
# (f) content hash covers every swappable field
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "mutation",
    [
        lambda r: replace(r, application_namespace="SzeChunYiu/RAKL_other"),
        lambda r: replace(r, root_id="OTHER-ROOT"),
        lambda r: replace(r, atom_label="NS-B1a2-OTHER"),
        lambda r: replace(r, context_hash="0" * 64),
        lambda r: replace(r, parent_atom_id="NS-B9"),
        lambda r: replace(r, human_short_label="DifferentLabel"),
        lambda r: replace(r, creator_branch_or_episode="research/different-branch"),
        lambda r: replace(r, frozen_at_utc="2026-08-11T12:00:00Z"),
        lambda r: replace(r, base_commit="d" * 40),
        lambda r: replace(r, identity_status=IdentityStatus.RESERVED),
        lambda r: replace(r, aliases=("alias-1",)),
        # SUPERSEDED status changes the successor invariant; build a peer instead
        # of mutating in place to keep the mutation field-isolated.
    ],
)
def test_mutating_any_swappable_field_changes_the_content_hash(
    mutation: Callable[[IdentityReservation], IdentityReservation],
):
    base = _make()
    mutated = mutation(base)
    assert base.reservation_canonical_sha256 != mutated.reservation_canonical_sha256, (
        "mutating a swappable field must change the content hash"
    )


def test_supersession_successor_field_is_in_the_hash():
    retired_a = _make(
        identity_status=IdentityStatus.SUPERSEDED,
        supersession_successor="NS-B1a2-v2",
    )
    retired_b = _make(
        identity_status=IdentityStatus.SUPERSEDED,
        supersession_successor="NS-B1a2-v3",
    )
    assert (
        retired_a.reservation_canonical_sha256
        != retired_b.reservation_canonical_sha256
    )


def test_schema_version_is_in_the_hash():
    from rakl.identity_reservation import RESERVATION_SCHEMA_VERSION

    base = _make()
    other = replace(base, schema_version="research-identity-reservation-v0")
    assert base.reservation_canonical_sha256 != other.reservation_canonical_sha256
    assert RESERVATION_SCHEMA_VERSION == "research-identity-reservation-v1"


def test_two_structurally_equal_reservations_have_equal_hashes():
    a = _make()
    b = _make()
    assert a.reservation_canonical_sha256 == b.reservation_canonical_sha256


# ---------------------------------------------------------------------------
# Self-validation: author cannot mint a COLLISION verdict; structural guards
# ---------------------------------------------------------------------------


def test_author_cannot_set_collision_status():
    with pytest.raises(ValueError, match="COLLISION is an auditor-derived verdict"):
        _make(identity_status=IdentityStatus.COLLISION)


def test_superseded_without_successor_is_rejected():
    with pytest.raises(ValueError, match="supersession_successor"):
        _make(identity_status=IdentityStatus.SUPERSEDED, supersession_successor=None)


def test_non_superseded_with_successor_is_rejected():
    with pytest.raises(ValueError, match="supersession_successor may only be set"):
        _make(identity_status=IdentityStatus.FROZEN, supersession_successor="NS-B1a2-v2")


def test_bad_context_hash_rejected():
    with pytest.raises(ValueError, match="context_hash must be sha256 hex"):
        _make(context_hash="not-a-hash")


def test_bad_base_commit_rejected():
    with pytest.raises(ValueError, match="base_commit must be a 40/64-char git oid"):
        _make(base_commit="short")


def test_bad_timestamp_rejected():
    with pytest.raises(ValueError, match="frozen_at_utc"):
        _make(frozen_at_utc="2026-08-11 09:00:00")


def test_empty_namespace_rejected():
    with pytest.raises(ValueError, match="application_namespace"):
        _make(application_namespace="")


def test_document_hash_matches_content_hash():
    reservation = _make()
    document = reservation.document()
    assert document["reservation_canonical_sha256"] == reservation.reservation_canonical_sha256
    # The hash field is not present in content(); it is added by document().
    assert "reservation_canonical_sha256" not in dict(reservation.content())


def test_compound_identity_partitions_by_namespace():
    math_ns = _make(application_namespace="SzeChunYiu/RAKL_math")
    physics_ns = _make(application_namespace="SzeChunYiu/RAKL_physics")
    assert math_ns.compound_identity != physics_ns.compound_identity
    assert math_ns.compound_identity[0] != physics_ns.compound_identity[0]


def test_audit_rejects_non_reservation_input():
    with pytest.raises(TypeError):
        audit_identity_reservations([_make(), {"not": "a reservation"}])  # type: ignore[list-item]
