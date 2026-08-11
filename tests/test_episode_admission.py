"""Frozen hostile worlds for episode storage/admission separation (issue #182).

Worlds match the issue's cheapest prospective discriminator:

1. valid TaskEpisode + valid protected canonical admission receipt
2. valid TaskEpisode marked/stored proposal-shadow only
3. valid TaskEpisode marked shadow but referenced by a canonical/protected consumer
4. malformed/stale-hash variants of the above

Path/filename hints must never mint authority.
"""

from __future__ import annotations

from hashlib import sha256

import pytest

from rakl.episode_admission import (
    AdmissionVerdict,
    EpisodeAdmissionReceipt,
    EpisodeStorageStatus,
    ProtectedConsumer,
    audit_episode_admission,
    count_canonical_authority_episodes,
    retainable_for_search_and_failure_learning,
    satisfies_canonical_inventory,
)
from rakl.experience_substrate import EpisodeOutcome, TaskEpisode, episode_content_bytes


def _episode(**overrides: object) -> TaskEpisode:
    base = dict(
        episode_id="E-shadow-or-canonical-1",
        task_id="T-1",
        atom_id="A-1",
        context_hash="ctx-1",
        problem_signature=("storage-admission-separation",),
        fibre_snapshot_hash="fibre-1",
        operator_ids=("op.record_episode",),
        action_trace=("recorded episode",),
        observation_ids=("O-1",),
        verification_ids=(),
        outcome=EpisodeOutcome.FAILURE,
        residual_signature=("inventory_authority_conflation",),
        evidence_pointers=("artifact:observation-1",),
        artifact_hash="0" * 64,
        timestamp="2026-08-11T12:00:00+00:00",
        cost=0.0,
    )
    base.update(overrides)
    draft = TaskEpisode(**base)  # type: ignore[arg-type]
    if overrides.get("artifact_hash") == "0" * 64 or "artifact_hash" not in overrides:
        digest = sha256(episode_content_bytes(draft)).hexdigest()
        draft = TaskEpisode(**{**base, "artifact_hash": digest})  # type: ignore[arg-type]
    return draft


def _receipt(episode: TaskEpisode, **overrides: object) -> EpisodeAdmissionReceipt:
    base = dict(
        receipt_id="R-admit-1",
        episode_id=episode.episode_id,
        episode_artifact_hash=episode.artifact_hash,
        storage_status=EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED,
        inventory_registry_id="inventory:v3-canonical",
        registered_at_utc="2026-08-11T12:05:00Z",
        registration_evidence_pointers=("evidence:admission-attestation-1",),
        reverification_triggers=("episode_artifact_hash_change",),
    )
    base.update(overrides)
    return EpisodeAdmissionReceipt(**base)  # type: ignore[arg-type]


def test_world1_canonical_admission_passes_exhaustive_checks() -> None:
    episode = _episode()
    receipt = _receipt(episode)
    report = audit_episode_admission(episode, receipt)

    assert report.verdict is AdmissionVerdict.CANONICAL_ADMITTED
    assert report.satisfies_canonical_inventory is True
    assert report.retained_for_search_or_failure_learning is True
    assert satisfies_canonical_inventory(episode, receipt) is True
    assert report.path_or_name_heuristics_consulted is False


def test_world2_shadow_retained_but_excluded_from_canonical_counts() -> None:
    episode = _episode()
    receipt = _receipt(
        episode,
        storage_status=EpisodeStorageStatus.PROPOSAL_SHADOW_STORED,
        inventory_registry_id="shadow:proposal-sidecar",
    )
    report = audit_episode_admission(
        episode,
        receipt,
        claimed_path_or_name_hint="episodes/E-1.json.shadow",
    )

    assert report.verdict is AdmissionVerdict.SHADOW_RETAINED
    assert report.retained_for_search_or_failure_learning is True
    assert report.satisfies_canonical_inventory is False
    assert retainable_for_search_and_failure_learning(episode, receipt) is True
    assert satisfies_canonical_inventory(episode, receipt) is False
    assert report.path_or_name_heuristics_consulted is False
    assert "path_or_name_hint_ignored" in report.reasons


@pytest.mark.parametrize(
    "consumer",
    [
        ProtectedConsumer.CANONICAL_INVENTORY,
        ProtectedConsumer.PROMOTION,
        ProtectedConsumer.LESSON_OR_TOOL,
        ProtectedConsumer.PROOF,
        ProtectedConsumer.ROOT_GATE,
    ],
)
def test_world3_shadow_referenced_by_protected_consumer_fails_closed(
    consumer: ProtectedConsumer,
) -> None:
    episode = _episode()
    receipt = _receipt(
        episode,
        storage_status=EpisodeStorageStatus.PROPOSAL_SHADOW_STORED,
        inventory_registry_id="shadow:proposal-sidecar",
    )
    report = audit_episode_admission(
        episode,
        receipt,
        protected_consumer=consumer,
        claimed_path_or_name_hint="canonical/episodes/E-1.json",
    )

    assert report.verdict is AdmissionVerdict.PROTECTED_CONSUMER_REJECTED
    assert report.fail_closed is True
    assert report.satisfies_canonical_inventory is False
    assert report.retained_for_search_or_failure_learning is True
    assert report.path_or_name_heuristics_consulted is False


def test_world4_stale_hash_receipt_is_unverifiable() -> None:
    episode = _episode()
    receipt = _receipt(episode, episode_artifact_hash="b" * 64)
    report = audit_episode_admission(episode, receipt)

    assert report.verdict is AdmissionVerdict.RECEIPT_UNVERIFIABLE
    assert "receipt_episode_artifact_hash_mismatch" in report.reasons
    assert report.satisfies_canonical_inventory is False
    assert report.retained_for_search_or_failure_learning is False


def test_world4_malformed_episode_fails_exactly_as_hash_contract() -> None:
    episode = _episode(artifact_hash="not-a-hash")
    receipt = _receipt(
        episode,
        episode_artifact_hash="c" * 64,
    )
    report = audit_episode_admission(episode, receipt)

    assert report.verdict is AdmissionVerdict.EPISODE_INVALID
    assert any(reason.startswith("episode:artifact_hash") for reason in report.reasons)


def test_missing_receipt_cannot_satisfy_protected_consumer() -> None:
    episode = _episode()
    report = audit_episode_admission(
        episode,
        None,
        protected_consumer=ProtectedConsumer.CANONICAL_INVENTORY,
    )

    assert report.verdict is AdmissionVerdict.PROTECTED_CONSUMER_REJECTED
    assert report.fail_closed is True


def test_path_extension_never_mints_canonical_authority() -> None:
    """Renaming to a non-.shadow path must not admit a shadow receipt."""

    episode = _episode()
    shadow = _receipt(
        episode,
        storage_status=EpisodeStorageStatus.PROPOSAL_SHADOW_STORED,
        inventory_registry_id="shadow:proposal-sidecar",
    )
    report = audit_episode_admission(
        episode,
        shadow,
        protected_consumer=ProtectedConsumer.CANONICAL_INVENTORY,
        claimed_path_or_name_hint="/canonical/inventory/E-1.json",
    )
    assert report.verdict is AdmissionVerdict.PROTECTED_CONSUMER_REJECTED
    assert satisfies_canonical_inventory(episode, shadow) is False


def test_canonical_authority_count_ignores_shadow_only_storage() -> None:
    canonical_episode = _episode(episode_id="E-canonical")
    shadow_episode = _episode(episode_id="E-shadow")
    pairs = (
        (canonical_episode, _receipt(canonical_episode)),
        (
            shadow_episode,
            _receipt(
                shadow_episode,
                storage_status=EpisodeStorageStatus.PROPOSAL_SHADOW_STORED,
                inventory_registry_id="shadow:proposal-sidecar",
            ),
        ),
        (shadow_episode, None),
    )
    assert count_canonical_authority_episodes(pairs) == 1


def test_document_hash_is_derived_not_supplied() -> None:
    episode = _episode()
    receipt = _receipt(episode)
    document = receipt.document()
    assert document["receipt_canonical_sha256"] == receipt.receipt_canonical_sha256
    assert len(document["receipt_canonical_sha256"]) == 64


def test_canonical_status_rejects_shadow_registry_prefix() -> None:
    episode = _episode()
    with pytest.raises(ValueError, match="shadow:"):
        _receipt(
            episode,
            storage_status=EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED,
            inventory_registry_id="shadow:sneaky",
        )
