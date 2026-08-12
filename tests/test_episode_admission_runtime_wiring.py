"""Runtime wiring of episode-admission receipts into protected inventory (#395).

Framework-native discriminators (no Millennium data):

1. valid TaskEpisode + PROPOSAL_SHADOW_STORED -> retained, not counted canonically
2. same shadow routed into ProtectedConsumer.CANONICAL_INVENTORY -> hard fail
3. valid TaskEpisode + matching CANONICAL_INVENTORY_ADMITTED -> accepted once
4. canonical receipt with mismatched episode hash -> hard fail
5. adversarial filenames/extensions/top-level ids -> identical verdicts
"""

from __future__ import annotations

from hashlib import sha256

import pytest

from rakl.episode_admission import (
    AdmissionVerdict,
    EpisodeAdmissionReceipt,
    EpisodeStorageStatus,
    ProtectedConsumer,
    count_canonical_authority_episodes,
    filter_canonical_inventory_episodes,
    require_protected_consumer_admission,
)
from rakl.experience_substrate import EpisodeOutcome, TaskEpisode, episode_content_bytes
from rakl.v3_runtime import (
    RAKLV3State,
    protected_canonical_inventory,
    record_task_episode,
    require_protected_inventory_admission,
)


def _episode(episode_id: str = "E-wire-1") -> TaskEpisode:
    base = dict(
        episode_id=episode_id,
        task_id=f"task-{episode_id}",
        atom_id="A-WIRE",
        context_hash="ctx-wire",
        problem_signature=("episode-admission-runtime-wiring",),
        fibre_snapshot_hash="fibre-wire",
        operator_ids=("op.record_episode",),
        action_trace=("recorded episode",),
        observation_ids=("O-wire",),
        verification_ids=(),
        outcome=EpisodeOutcome.SUCCESS,
        residual_signature=(),
        evidence_pointers=(f"artifact:{episode_id}",),
        artifact_hash="0" * 64,
        timestamp="2026-08-12T05:00:00+00:00",
        cost=0.0,
    )
    draft = TaskEpisode(**base)  # type: ignore[arg-type]
    digest = sha256(episode_content_bytes(draft)).hexdigest()
    return TaskEpisode(**{**base, "artifact_hash": digest})  # type: ignore[arg-type]


def _receipt(
    episode: TaskEpisode,
    *,
    storage_status: EpisodeStorageStatus = EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED,
    receipt_id: str = "R-wire-1",
    episode_artifact_hash: str | None = None,
) -> EpisodeAdmissionReceipt:
    return EpisodeAdmissionReceipt(
        receipt_id=receipt_id,
        episode_id=episode.episode_id,
        episode_artifact_hash=episode_artifact_hash or episode.artifact_hash,
        storage_status=storage_status,
        inventory_registry_id=(
            "inventory:v3-canonical"
            if storage_status is EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED
            else "shadow:proposal-sidecar"
        ),
        registered_at_utc="2026-08-12T05:05:00Z",
        registration_evidence_pointers=(f"evidence:{receipt_id}",),
        reverification_triggers=("episode_artifact_hash_change",),
    )


def test_shadow_retained_not_counted_canonically() -> None:
    episode = _episode()
    receipt = _receipt(episode, storage_status=EpisodeStorageStatus.PROPOSAL_SHADOW_STORED)
    state = record_task_episode(
        RAKLV3State(),
        episode,
        proposal_admission_receipt=receipt,
    )
    assert len(state.experience.episodes) == 1
    assert count_canonical_authority_episodes([(episode, receipt)]) == 0
    assert filter_canonical_inventory_episodes([(episode, receipt)]) == ()


def test_shadow_into_protected_canonical_inventory_hard_fails() -> None:
    episode = _episode()
    receipt = _receipt(episode, storage_status=EpisodeStorageStatus.PROPOSAL_SHADOW_STORED)
    with pytest.raises(ValueError, match="protected consumer rejected"):
        require_protected_consumer_admission(
            episode,
            receipt,
            protected_consumer=ProtectedConsumer.CANONICAL_INVENTORY,
            claimed_path_or_name_hint="episodes/E-wire-1.json",
        )
    with pytest.raises(ValueError, match="protected consumer rejected"):
        record_task_episode(
            RAKLV3State(),
            episode,
            proposal_admission_receipt=receipt,
            protected_consumer=ProtectedConsumer.CANONICAL_INVENTORY,
            claimed_path_or_name_hint="canonical/episodes/E-wire-1.json",
        )


def test_matching_canonical_receipt_accepted_exactly_once() -> None:
    episode = _episode()
    receipt = _receipt(episode)
    report = require_protected_inventory_admission(
        episode,
        receipt,
        protected_consumer=ProtectedConsumer.CANONICAL_INVENTORY,
    )
    assert report.verdict is AdmissionVerdict.CANONICAL_ADMITTED
    assert protected_canonical_inventory([(episode, receipt)]) == (episode,)
    assert count_canonical_authority_episodes([(episode, receipt)]) == 1
    state = record_task_episode(
        RAKLV3State(),
        episode,
        proposal_admission_receipt=receipt,
        protected_consumer=ProtectedConsumer.CANONICAL_INVENTORY,
    )
    assert len(state.experience.episodes) == 1


def test_stale_hash_canonical_receipt_hard_fails() -> None:
    episode = _episode()
    receipt = _receipt(episode, episode_artifact_hash="d" * 64)
    with pytest.raises(ValueError, match="protected consumer rejected"):
        require_protected_consumer_admission(episode, receipt)
    assert count_canonical_authority_episodes([(episode, receipt)]) == 0


@pytest.mark.parametrize(
    "hint",
    [
        "episodes/E-wire-1.json",
        "episodes/E-wire-1.json.shadow",
        "canonical/inventory/E-wire-1.taskepisode",
        ".taskepisode/E-wire-1.json",
        None,
    ],
)
def test_adversarial_filenames_do_not_change_verdicts(hint: str | None) -> None:
    episode = _episode("E-adv")
    shadow = _receipt(
        episode,
        storage_status=EpisodeStorageStatus.PROPOSAL_SHADOW_STORED,
        receipt_id="R-shadow",
    )
    canonical = _receipt(episode, receipt_id="R-canonical")

    assert filter_canonical_inventory_episodes(
        [(episode, shadow)],
        claimed_path_or_name_hint=hint,
    ) == ()
    assert filter_canonical_inventory_episodes(
        [(episode, canonical)],
        claimed_path_or_name_hint=hint,
    ) == (episode,)
    with pytest.raises(ValueError, match="protected consumer rejected"):
        require_protected_consumer_admission(
            episode,
            shadow,
            protected_consumer=ProtectedConsumer.CANONICAL_INVENTORY,
            claimed_path_or_name_hint=hint,
        )
    assert (
        require_protected_consumer_admission(
            episode,
            canonical,
            protected_consumer=ProtectedConsumer.CANONICAL_INVENTORY,
            claimed_path_or_name_hint=hint,
        ).verdict
        is AdmissionVerdict.CANONICAL_ADMITTED
    )
