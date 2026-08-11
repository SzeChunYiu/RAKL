"""Framework-native corpus for issue #182: shadow storage vs canonical admission.

Four cases from the issue (no application evidence embedded):

1. valid TaskEpisode + valid protected admission receipt -> admitted
2. valid TaskEpisode proposal-shadow only -> retained, excluded from canonical counts
3. valid TaskEpisode marked shadow but referenced as canonical -> fails closed
4. malformed/stale-hash variants of (1)-(3) -> fail under current strict hash contracts
"""

from __future__ import annotations

from dataclasses import asdict, replace
from hashlib import sha256
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from rakl.experience_substrate import (
    EpisodeAdmissionReceipt,
    EpisodeOutcome,
    EpisodeStorageAdmission,
    ExperienceLedger,
    InventoryAdmissionVerdict,
    TaskEpisode,
    add_admission_receipt,
    add_episode,
    admission_receipt_content_bytes,
    canonical_inventory_episodes,
    episode_content_bytes,
    episode_portrait,
    proposal_shadow_episodes,
    require_canonical_inventory_admission,
    resolve_inventory_admission,
    validate_admission_receipt,
    validate_episode,
)


ROOT = Path(__file__).resolve().parents[1]


def _episode(
    episode_id: str,
    *,
    storage_admission: EpisodeStorageAdmission = EpisodeStorageAdmission.PROPOSAL_SHADOW_STORED,
) -> TaskEpisode:
    draft = TaskEpisode(
        episode_id=episode_id,
        task_id=f"task-{episode_id}",
        atom_id="A-ADMISSION",
        context_hash="sha256:" + "a" * 64,
        problem_signature=("episode admission", "shadow versus canonical"),
        fibre_snapshot_hash="sha256:" + "b" * 64,
        operator_ids=("OP-ADMISSION",),
        action_trace=("freeze episode", "resolve storage admission"),
        observation_ids=("OBS-ADMISSION",),
        verification_ids=("VERIFY-ADMISSION",),
        outcome=EpisodeOutcome.SUCCESS,
        residual_signature=(),
        evidence_pointers=(f"test:admission-corpus:{episode_id}",),
        artifact_hash="",
        timestamp="2026-08-11T19:00:00Z",
        cost=0.0,
        storage_admission=storage_admission,
    )
    return replace(draft, artifact_hash=sha256(episode_content_bytes(draft)).hexdigest())


def _receipt(episode: TaskEpisode, receipt_id: str = "AR-1") -> EpisodeAdmissionReceipt:
    draft = EpisodeAdmissionReceipt(
        receipt_id=receipt_id,
        episode_id=episode.episode_id,
        episode_artifact_hash=episode.artifact_hash,
        storage_admission=EpisodeStorageAdmission.CANONICAL_INVENTORY_ADMITTED,
        evidence_pointers=(f"test:admission-receipt:{receipt_id}",),
        artifact_hash="",
        timestamp="2026-08-11T19:05:00Z",
    )
    return replace(draft, artifact_hash=sha256(admission_receipt_content_bytes(draft)).hexdigest())


def _json_episode(episode: TaskEpisode) -> dict:
    payload = asdict(episode)
    payload["outcome"] = episode.outcome.value
    payload["storage_admission"] = episode.storage_admission.value
    for name in (
        "problem_signature",
        "operator_ids",
        "action_trace",
        "observation_ids",
        "verification_ids",
        "residual_signature",
        "evidence_pointers",
    ):
        payload[name] = list(payload[name])
    return payload


def _json_receipt(receipt: EpisodeAdmissionReceipt) -> dict:
    payload = asdict(receipt)
    payload["storage_admission"] = receipt.storage_admission.value
    payload["evidence_pointers"] = list(payload["evidence_pointers"])
    return payload


def test_case1_valid_episode_plus_valid_admission_receipt_is_admitted() -> None:
    episode = _episode("EP-CANONICAL-1", storage_admission=EpisodeStorageAdmission.CANONICAL_INVENTORY_ADMITTED)
    receipt = _receipt(episode)
    report = resolve_inventory_admission(episode, receipt, treat_as_canonical=True)

    assert report.verdict is InventoryAdmissionVerdict.CANONICAL_INVENTORY_ADMITTED
    assert report.counts_toward_canonical_inventory is True
    assert require_canonical_inventory_admission(episode, receipt).verdict is (
        InventoryAdmissionVerdict.CANONICAL_INVENTORY_ADMITTED
    )

    ledger = add_admission_receipt(add_episode(ExperienceLedger(), episode), receipt)
    assert canonical_inventory_episodes(ledger) == (episode,)
    assert proposal_shadow_episodes(ledger) == ()
    portrait = episode_portrait(ledger)
    assert portrait["canonical_inventory_episode_count"] == 1
    assert portrait["proposal_shadow_episode_count"] == 0
    assert portrait["admission_receipt_count"] == 1


def test_case2_proposal_shadow_retained_but_excluded_from_canonical_counts() -> None:
    episode = _episode("EP-SHADOW-1")
    report = resolve_inventory_admission(episode, treat_as_canonical=False)

    assert report.verdict is InventoryAdmissionVerdict.PROPOSAL_SHADOW_STORED
    assert report.retained_for_search is True
    assert report.counts_toward_canonical_inventory is False

    ledger = add_episode(ExperienceLedger(), episode)
    assert proposal_shadow_episodes(ledger) == (episode,)
    assert canonical_inventory_episodes(ledger) == ()
    portrait = episode_portrait(ledger)
    assert portrait["episode_count"] == 1
    assert portrait["canonical_inventory_episode_count"] == 0
    assert portrait["proposal_shadow_episode_count"] == 1


def test_case3_shadow_referenced_by_canonical_consumer_fails_closed() -> None:
    episode = _episode("EP-SHADOW-2")
    forged_receipt = _receipt(episode)

    report = resolve_inventory_admission(episode, forged_receipt, treat_as_canonical=True)
    assert report.verdict is InventoryAdmissionVerdict.SHADOW_REFERENCED_AS_CANONICAL
    assert report.counts_toward_canonical_inventory is False

    with pytest.raises(ValueError, match="shadow_episode_referenced_as_canonical"):
        require_canonical_inventory_admission(episode, forged_receipt)

    ledger = add_episode(ExperienceLedger(), episode)
    with pytest.raises(ValueError, match="shadow_episode_referenced_as_canonical"):
        add_admission_receipt(ledger, forged_receipt)
    assert canonical_inventory_episodes(ledger) == ()


def test_case4_malformed_and_stale_hashes_fail_closed() -> None:
    canonical = _episode(
        "EP-CANONICAL-BAD",
        storage_admission=EpisodeStorageAdmission.CANONICAL_INVENTORY_ADMITTED,
    )
    receipt = _receipt(canonical)
    shadow = _episode("EP-SHADOW-BAD")

    for malformed in (
        "sha256:" + canonical.artifact_hash,
        canonical.artifact_hash[:-1],
        canonical.artifact_hash + "0",
        "g" * 64,
        "not-a-digest",
    ):
        assert "episode:artifact_hash_invalid" in validate_episode(
            replace(canonical, artifact_hash=malformed)
        )
        assert "episode:artifact_hash_invalid" in validate_episode(
            replace(shadow, artifact_hash=malformed)
        )
        assert "admission_receipt:artifact_hash_invalid" in validate_admission_receipt(
            replace(receipt, artifact_hash=malformed)
        )
        assert "admission_receipt:episode_artifact_hash_invalid" in validate_admission_receipt(
            replace(receipt, episode_artifact_hash=malformed)
        )

    stale_episode = replace(canonical, artifact_hash="0" * 64)
    assert validate_episode(stale_episode) == ("episode:artifact_hash_mismatch",)
    stale_report = resolve_inventory_admission(stale_episode, receipt, treat_as_canonical=True)
    assert stale_report.verdict is InventoryAdmissionVerdict.EPISODE_INVALID

    stale_receipt = replace(receipt, artifact_hash="0" * 64)
    assert validate_admission_receipt(stale_receipt) == ("admission_receipt:artifact_hash_mismatch",)
    stale_binding = resolve_inventory_admission(canonical, stale_receipt, treat_as_canonical=True)
    assert stale_binding.verdict is InventoryAdmissionVerdict.ADMISSION_RECEIPT_INVALID
    assert stale_binding.reasons == ("admission_receipt:artifact_hash_mismatch",)

    # Binding mismatch with an otherwise valid receipt hash still fails closed.
    rebound = EpisodeAdmissionReceipt(
        receipt_id=receipt.receipt_id,
        episode_id=receipt.episode_id,
        episode_artifact_hash="1" * 64,
        storage_admission=receipt.storage_admission,
        evidence_pointers=receipt.evidence_pointers,
        artifact_hash="",
        timestamp=receipt.timestamp,
    )
    rebound = replace(
        rebound,
        artifact_hash=sha256(admission_receipt_content_bytes(rebound)).hexdigest(),
    )
    rebound_report = resolve_inventory_admission(canonical, rebound, treat_as_canonical=True)
    assert rebound_report.verdict is InventoryAdmissionVerdict.ADMISSION_RECEIPT_INVALID
    assert rebound_report.reasons == ("admission:receipt_episode_artifact_hash_mismatch",)


def test_canonical_declaration_without_receipt_is_not_inventory_authority() -> None:
    episode = _episode(
        "EP-DECLARED-ONLY",
        storage_admission=EpisodeStorageAdmission.CANONICAL_INVENTORY_ADMITTED,
    )
    report = resolve_inventory_admission(episode, treat_as_canonical=True)
    assert report.verdict is InventoryAdmissionVerdict.ADMISSION_RECEIPT_INVALID
    assert report.counts_toward_canonical_inventory is False
    with pytest.raises(ValueError, match="canonical_requires_admission_receipt"):
        require_canonical_inventory_admission(episode, None)


def test_schemas_accept_corpus_and_reject_malformed_hashes() -> None:
    episode_schema = json.loads((ROOT / "schemas/task-episode.schema.json").read_text())
    receipt_schema = json.loads(
        (ROOT / "schemas/episode-admission-receipt.schema.json").read_text()
    )
    episode_validator = Draft202012Validator(episode_schema)
    receipt_validator = Draft202012Validator(receipt_schema)

    canonical = _episode(
        "EP-SCHEMA-CANONICAL",
        storage_admission=EpisodeStorageAdmission.CANONICAL_INVENTORY_ADMITTED,
    )
    shadow = _episode("EP-SCHEMA-SHADOW")
    receipt = _receipt(canonical, receipt_id="AR-SCHEMA")

    assert list(episode_validator.iter_errors(_json_episode(canonical))) == []
    assert list(episode_validator.iter_errors(_json_episode(shadow))) == []
    assert list(receipt_validator.iter_errors(_json_receipt(receipt))) == []

    hostile_episode = dict(_json_episode(shadow), artifact_hash="sha256:" + shadow.artifact_hash)
    assert list(episode_validator.iter_errors(hostile_episode))
    hostile_receipt = dict(_json_receipt(receipt), artifact_hash="0" * 63)
    assert list(receipt_validator.iter_errors(hostile_receipt))
    shadow_receipt = dict(
        _json_receipt(receipt),
        storage_admission=EpisodeStorageAdmission.PROPOSAL_SHADOW_STORED.value,
    )
    assert list(receipt_validator.iter_errors(shadow_receipt))
