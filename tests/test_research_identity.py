"""Frozen fixture worlds for the issue-#142 identity-collision benchmark.

The six worlds are exactly the ones the issue enumerates as the cheapest benchmark.
Each asserts both the alarm case and, where applicable, the no-alarm control, because a
collision detector that fires on everything has perfect recall and no value.
"""

from __future__ import annotations

import dataclasses

import pytest

from rakl.research_identity import (
    CandidateIdentity,
    IdentityStatus,
    RegistrationVerdict,
    ResearchIdentity,
    ResearchIdentityRegistry,
    ResolutionVerdict,
    score_collision_detection,
)


NAMESPACE = "SzeChunYiu/RAKL_math"
ROOT = "navier_stokes"


def _atom(
    label: str,
    context_hash: str,
    *,
    branch: str = "research/branch-a",
    base_commit: str = "a" * 40,
    parent: str | None = None,
) -> ResearchIdentity:
    return ResearchIdentity(
        application_namespace=NAMESPACE,
        root_id=ROOT,
        atom_label=label,
        context_hash=context_hash,
        creator_branch=branch,
        base_commit=base_commit,
        created_at_utc="2026-08-11T09:00:00Z",
        parent_atom_uid=parent,
    )


@pytest.fixture()
def registry() -> ResearchIdentityRegistry:
    return ResearchIdentityRegistry()


# --- World 1: same label, same content/context -> deduplicable -------------------


def test_world1_same_label_same_context_deduplicates(registry) -> None:
    first = registry.register(_atom("NS-B1a2", "ctx-compactness"))
    second = registry.register(_atom("NS-B1a2", "ctx-compactness", branch="research/other"))

    assert first.verdict is RegistrationVerdict.REGISTERED
    assert second.verdict is RegistrationVerdict.DEDUPLICATED
    assert first.uid == second.uid
    # No-alarm control: an honest re-registration must not be logged as a collision.
    assert registry.collisions == []


# --- World 2: same label, different context -> collision MUST be detected --------


def test_world2_same_label_different_context_is_a_collision(registry) -> None:
    """Replays the exact #142 incident: two NS-B1a2 atoms, disjoint mathematics."""

    compactness = registry.register(
        _atom(
            "NS-B1a2",
            "ctx-compactness-time-drift",
            branch="research/ns-b1a2-selfsimilar-time-drift-20260811",
            base_commit="5c2583396e1c80569915cd960426b49ba5fae980",
        )
    )
    kinetic = registry.register(
        _atom(
            "NS-B1a2",
            "ctx-kinetic-energy-core-packing",
            branch="research/ns-b1a2-critical-blob-packing-20260811",
            base_commit="48d1153c3b5fa749b1a6fd84212befb9e39daabe",
        )
    )

    assert compactness.verdict is RegistrationVerdict.REGISTERED
    assert kinetic.verdict is RegistrationVerdict.LABEL_COLLISION
    assert "same_label_different_context_hash" in kinetic.reasons
    assert compactness.uid in kinetic.conflicting_uids
    assert compactness.uid != kinetic.uid

    # Both immutable histories survive under distinct uids; neither is rewritten.
    assert registry.identities[compactness.uid].status is IdentityStatus.RESERVED
    assert registry.identities[kinetic.uid].status is IdentityStatus.COLLISION
    assert (
        registry.identities[compactness.uid].creator_branch
        == "research/ns-b1a2-selfsimilar-time-drift-20260811"
    )

    # The conflict stays visible as process history.
    assert len(registry.collisions) == 1
    collision = registry.collisions[0]
    assert collision.incumbent_uid == compactness.uid
    assert collision.challenger_uid == kinetic.uid


def test_world2_ambiguous_label_fails_closed_for_downstream_queries(registry) -> None:
    """The central rule: once a label is ambiguous, it stops being a usable key."""

    registry.register(_atom("NS-B1a2", "ctx-compactness"))
    registry.register(_atom("NS-B1a2", "ctx-kinetic", branch="research/other"))

    ambiguous = registry.resolve_label(
        application_namespace=NAMESPACE, root_id=ROOT, atom_label="NS-B1a2"
    )
    assert ambiguous.verdict is ResolutionVerdict.AMBIGUOUS_LABEL
    assert "downstream_query_must_supply_exact_uid" in ambiguous.reasons
    assert len(ambiguous.uids) == 2

    # No-alarm control: an unambiguous label still resolves cleanly.
    registry.register(_atom("NS-B3c1", "ctx-other"))
    resolved = registry.resolve_label(
        application_namespace=NAMESPACE, root_id=ROOT, atom_label="NS-B3c1"
    )
    assert resolved.verdict is ResolutionVerdict.RESOLVED
    assert len(resolved.uids) == 1

    missing = registry.resolve_label(
        application_namespace=NAMESPACE, root_id=ROOT, atom_label="NS-NEVER"
    )
    assert missing.verdict is ResolutionVerdict.NOT_FOUND


# --- World 3: different labels, same content -> alias candidate, NOT equivalence --


def test_world3_same_content_different_label_is_only_an_alias_candidate(registry) -> None:
    first = registry.register(_atom("NS-B1a2", "ctx-shared"))
    second = registry.register(_atom("NS-B1a2-alt", "ctx-shared"))

    assert first.verdict is RegistrationVerdict.REGISTERED
    assert second.verdict is RegistrationVerdict.ALIAS_CANDIDATE
    assert "alias_candidate_requires_explicit_equivalence_decision" in second.reasons
    assert first.uid in second.conflicting_uids
    # Crucially NOT deduplicated, and NOT a collision: equal bytes are not equal meaning.
    assert second.verdict is not RegistrationVerdict.DEDUPLICATED
    assert registry.collisions == []


# --- World 4: parent renamed/superseded while a child branch is active ------------


def test_world4_child_of_superseded_parent_fails_closed(registry) -> None:
    parent = registry.register(_atom("NS-B1", "ctx-parent-v1"))
    successor = registry.register(_atom("NS-B1-v2", "ctx-parent-v2"))
    registry.supersede(retired_uid=parent.uid, successor_uid=successor.uid)

    stale_child = registry.register(
        _atom("NS-B1a2", "ctx-child", parent=parent.uid)
    )
    assert stale_child.verdict is RegistrationVerdict.CANNOT_CHECK
    assert "parent_atom_superseded_resolve_lineage_explicitly" in stale_child.reasons

    # No-alarm control: a child of the live successor registers normally.
    fresh_child = registry.register(
        _atom("NS-B1a3", "ctx-child-fresh", parent=successor.uid)
    )
    assert fresh_child.verdict is RegistrationVerdict.REGISTERED

    # Supersession preserved both parties rather than deleting the retired one.
    assert registry.identities[parent.uid].status is IdentityStatus.SUPERSEDED
    assert parent.uid in registry.identities[successor.uid].supersedes


def test_world4_unknown_parent_fails_closed(registry) -> None:
    orphan = registry.register(_atom("NS-B1a2", "ctx-child", parent="deadbeef" * 8))
    assert orphan.verdict is RegistrationVerdict.CANNOT_CHECK
    assert "parent_atom_uid_not_registered" in orphan.reasons


# --- World 5: two candidate ids C001 under distinct exact atoms -------------------


def test_world5_same_candidate_label_under_distinct_atoms_is_not_a_collision(
    registry,
) -> None:
    compactness = registry.register(_atom("NS-B1a2", "ctx-compactness"))
    kinetic = registry.register(_atom("NS-B1a2-kinetic", "ctx-kinetic"))

    first = registry.register_candidate(
        CandidateIdentity(
            parent_atom_uid=compactness.uid,
            candidate_label="C001",
            content_hash="candidate-compactness",
        )
    )
    second = registry.register_candidate(
        CandidateIdentity(
            parent_atom_uid=kinetic.uid,
            candidate_label="C001",
            content_hash="candidate-kinetic",
        )
    )

    # No-alarm case: identical readable label, different exact atoms -> both fine.
    assert first.verdict is RegistrationVerdict.REGISTERED
    assert second.verdict is RegistrationVerdict.REGISTERED
    assert first.uid != second.uid


def test_world5_same_candidate_label_under_one_atom_with_new_content_collides(
    registry,
) -> None:
    atom = registry.register(_atom("NS-B1a2", "ctx-compactness"))
    registry.register_candidate(
        CandidateIdentity(atom.uid, "C001", content_hash="first-content")
    )
    clash = registry.register_candidate(
        CandidateIdentity(atom.uid, "C001", content_hash="different-content")
    )
    assert clash.verdict is RegistrationVerdict.LABEL_COLLISION

    repeat = registry.register_candidate(
        CandidateIdentity(atom.uid, "C001", content_hash="first-content")
    )
    assert repeat.verdict is RegistrationVerdict.DEDUPLICATED


def test_world5_candidate_without_registered_atom_fails_closed(registry) -> None:
    report = registry.register_candidate(
        CandidateIdentity("f" * 64, "C001", content_hash="x")
    )
    assert report.verdict is RegistrationVerdict.CANNOT_CHECK


# --- World 6: stale branch created before the label was consumed on main ----------


def test_world6_stale_base_commit_collision_records_why(registry) -> None:
    registry.register(
        _atom("NS-B1a2", "ctx-on-main", base_commit="1" * 40, branch="main")
    )
    stale = registry.register(
        _atom(
            "NS-B1a2",
            "ctx-stale-branch",
            base_commit="0" * 40,
            branch="research/created-before-main-consumed-label",
        )
    )
    assert stale.verdict is RegistrationVerdict.LABEL_COLLISION
    assert "challenger_base_commit_differs_from_incumbent" in stale.reasons


# --- Structural fail-closed and derived-uid guarantees ---------------------------


def test_missing_required_fields_are_rejected(registry) -> None:
    report = registry.register(
        ResearchIdentity(
            application_namespace=NAMESPACE,
            root_id=ROOT,
            atom_label="   ",
            context_hash="ctx",
            creator_branch="",
            base_commit="b" * 40,
            created_at_utc="2026-08-11T09:00:00Z",
        )
    )
    assert report.verdict is RegistrationVerdict.REJECTED
    assert "identity_field_missing:atom_label" in report.reasons
    assert "identity_field_missing:creator_branch" in report.reasons


def test_uid_is_derived_not_asserted() -> None:
    """A caller cannot claim a uid its own coordinates do not produce."""

    left = _atom("NS-B1a2", "ctx-one")
    right = _atom("NS-B1a2", "ctx-one", branch="different", base_commit="c" * 40)
    assert left.uid == right.uid  # branch/commit are provenance, not identity
    assert _atom("NS-B1a2", "ctx-two").uid != left.uid

    # `uid` is a derived property, not a constructor field, so a caller cannot assert
    # an identity that its own coordinates do not produce.
    assert "uid" not in {f.name for f in dataclasses.fields(ResearchIdentity)}
    with pytest.raises(TypeError):
        ResearchIdentity(  # type: ignore[call-arg]
            application_namespace=NAMESPACE,
            root_id=ROOT,
            atom_label="NS-B1a2",
            context_hash="ctx-one",
            creator_branch="b",
            base_commit="d" * 40,
            created_at_utc="2026-08-11T09:00:00Z",
            uid="forged",
        )


# --- The scorer itself must be validated -----------------------------------------


def test_scorer_rewards_recall_and_punishes_a_degenerate_always_flag_detector() -> None:
    truth = [False, True, False, True, False]

    perfect = score_collision_detection(
        [
            (
                RegistrationVerdict.LABEL_COLLISION
                if is_collision
                else RegistrationVerdict.REGISTERED,
                is_collision,
            )
            for is_collision in truth
        ]
    )
    assert perfect.recall == 1.0
    assert perfect.false_collision_rate == 0.0

    # A detector that flags everything: perfect recall, useless precision. The score
    # must expose that rather than reporting success.
    degenerate = score_collision_detection(
        [(RegistrationVerdict.LABEL_COLLISION, is_collision) for is_collision in truth]
    )
    assert degenerate.recall == 1.0
    assert degenerate.false_collision_rate == 1.0

    blind = score_collision_detection(
        [(RegistrationVerdict.REGISTERED, is_collision) for is_collision in truth]
    )
    assert blind.recall == 0.0
    assert blind.false_collision_rate == 0.0


def test_six_world_benchmark_scores_cleanly() -> None:
    """End-to-end: the six enumerated worlds, scored as one fixture set."""

    outcomes = []

    registry = ResearchIdentityRegistry()
    registry.register(_atom("A", "ctx-a"))
    outcomes.append((registry.register(_atom("A", "ctx-a")).verdict, False))  # world 1

    registry = ResearchIdentityRegistry()
    registry.register(_atom("A", "ctx-a"))
    outcomes.append((registry.register(_atom("A", "ctx-b")).verdict, True))  # world 2

    registry = ResearchIdentityRegistry()
    registry.register(_atom("A", "ctx-a"))
    outcomes.append((registry.register(_atom("B", "ctx-a")).verdict, False))  # world 3

    registry = ResearchIdentityRegistry()
    parent = registry.register(_atom("P", "ctx-p"))
    successor = registry.register(_atom("P2", "ctx-p2"))
    registry.supersede(retired_uid=parent.uid, successor_uid=successor.uid)
    outcomes.append(
        (registry.register(_atom("C", "ctx-c", parent=parent.uid)).verdict, False)
    )  # world 4

    registry = ResearchIdentityRegistry()
    left = registry.register(_atom("A", "ctx-a"))
    right = registry.register(_atom("B", "ctx-b"))
    registry.register_candidate(CandidateIdentity(left.uid, "C001", "x"))
    outcomes.append(
        (registry.register_candidate(CandidateIdentity(right.uid, "C001", "y")).verdict, False)
    )  # world 5

    registry = ResearchIdentityRegistry()
    registry.register(_atom("A", "ctx-a", base_commit="1" * 40))
    outcomes.append(
        (registry.register(_atom("A", "ctx-stale", base_commit="0" * 40)).verdict, True)
    )  # world 6

    score = score_collision_detection(outcomes)
    assert score.total == 6
    assert score.expected_collisions == 2
    assert score.recall == 1.0
    assert score.false_collision_rate == 0.0
