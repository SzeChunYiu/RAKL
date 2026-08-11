"""Frozen hostile worlds for episode inventory admission (issue #182).

The four worlds are exactly the ones the issue enumerates:

1. valid TaskEpisode + valid protected admission receipt -> admitted
2. valid TaskEpisode marked/stored proposal-shadow only -> retained, excluded
   from canonical authority counts
3. valid TaskEpisode marked shadow but referenced by a canonical/protected
   consumer -> fails closed
4. malformed/stale-hash variants -> fail exactly as current strict hash contracts

No RAKL_math paths or Millennium identifiers appear here.
"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, FormatChecker  # type: ignore[import-untyped]

from rakl.episode_inventory_admission import (
    AdmissionVerdict,
    EpisodeInventoryAdmissionReceipt,
    EpisodeStorageStatus,
    ProtectedConsumerKind,
    audit_episode_inventory_admission,
)
from rakl.experience_substrate import EpisodeOutcome, TaskEpisode, episode_content_bytes

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "schemas" / "episode-inventory-admission-receipt-v1.schema.json"


def _episode(**overrides: object) -> TaskEpisode:
    base = dict(
        episode_id="E-shadow-or-canonical-1",
        task_id="T-1",
        atom_id="A-1",
        context_hash="ctx-1",
        problem_signature=("framework-process",),
        fibre_snapshot_hash="fibre-1",
        operator_ids=("op.record_episode",),
        action_trace=("recorded proposal episode",),
        observation_ids=("O-1",),
        verification_ids=(),
        outcome=EpisodeOutcome.FAILURE,
        residual_signature=("inventory_admission_unbound",),
        evidence_pointers=("artifact:observation-1",),
        artifact_hash="pending",
        timestamp="2026-08-11T12:00:00Z",
        cost=0.0,
    )
    base.update(overrides)
    episode = TaskEpisode(**base)  # type: ignore[arg-type]
    if episode.artifact_hash == "pending" or overrides.get("artifact_hash") is None:
        digest = sha256(episode_content_bytes(episode)).hexdigest()
        episode = TaskEpisode(**{**base, "artifact_hash": digest})  # type: ignore[arg-type]
    return episode


def _receipt(
    episode: TaskEpisode,
    *,
    storage_status: EpisodeStorageStatus = EpisodeStorageStatus.PROPOSAL_SHADOW_STORED,
    **overrides: object,
) -> EpisodeInventoryAdmissionReceipt:
    base = dict(
        receipt_id="ADM-1",
        episode_id=episode.episode_id,
        episode_artifact_hash=episode.artifact_hash,
        storage_status=storage_status,
        claim_boundary=(
            "PROPOSAL_ONLY / NO_FRAMEWORK_PROMOTION / "
            "storage-vs-admission separation only"
        ),
        admission_attestation_id=(
            "attestation:canonical-inventory-1"
            if storage_status is EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED
            else None
        ),
        evidence_pointers=("artifact:admission-evidence-1",),
        frozen_at_utc="2026-08-11T11:00:00Z",
    )
    base.update(overrides)
    return EpisodeInventoryAdmissionReceipt(**base)  # type: ignore[arg-type]


# --- world 1: valid episode + valid protected admission receipt ---------------


def test_world1_valid_episode_with_admission_receipt_is_admitted() -> None:
    episode = _episode()
    receipt = _receipt(
        episode, storage_status=EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED
    )
    report = audit_episode_inventory_admission(
        receipt,
        episode,
        consumer=ProtectedConsumerKind.CANONICAL_INVENTORY,
    )

    assert report.verdict is AdmissionVerdict.CANONICAL_ADMISSION_VERIFIED
    assert report.canonical_inventory_admissible
    assert report.counts_toward_canonical_inventory
    assert report.retained_for_search_or_failure_learning
    assert report.reasons == ()


@pytest.mark.parametrize(
    "consumer",
    [
        ProtectedConsumerKind.CANONICAL_INVENTORY,
        ProtectedConsumerKind.PROMOTION_GATE,
        ProtectedConsumerKind.LESSON_TOOL_PROOF_OR_ROOT_GATE,
    ],
)
def test_world1_admission_covers_all_protected_consumers(
    consumer: ProtectedConsumerKind,
) -> None:
    episode = _episode()
    receipt = _receipt(
        episode, storage_status=EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED
    )
    report = audit_episode_inventory_admission(receipt, episode, consumer=consumer)
    assert report.verdict is AdmissionVerdict.CANONICAL_ADMISSION_VERIFIED


# --- world 2: proposal-shadow only -------------------------------------------


def test_world2_shadow_episode_retained_but_excluded_from_canonical_counts() -> None:
    episode = _episode()
    receipt = _receipt(
        episode, storage_status=EpisodeStorageStatus.PROPOSAL_SHADOW_STORED
    )
    report = audit_episode_inventory_admission(
        receipt,
        episode,
        consumer=ProtectedConsumerKind.SEARCH_OR_FAILURE_LEARNING,
    )

    assert report.verdict is AdmissionVerdict.SHADOW_RETAINED_NONCANONICAL
    assert report.retained_for_search_or_failure_learning
    assert not report.counts_toward_canonical_inventory
    assert not report.canonical_inventory_admissible
    assert report.storage_status is EpisodeStorageStatus.PROPOSAL_SHADOW_STORED


# --- world 3: shadow referenced by a protected consumer ----------------------


@pytest.mark.parametrize(
    "consumer",
    [
        ProtectedConsumerKind.CANONICAL_INVENTORY,
        ProtectedConsumerKind.PROMOTION_GATE,
        ProtectedConsumerKind.LESSON_TOOL_PROOF_OR_ROOT_GATE,
    ],
)
def test_world3_shadow_referenced_by_protected_consumer_fails_closed(
    consumer: ProtectedConsumerKind,
) -> None:
    episode = _episode()
    receipt = _receipt(
        episode, storage_status=EpisodeStorageStatus.PROPOSAL_SHADOW_STORED
    )
    report = audit_episode_inventory_admission(receipt, episode, consumer=consumer)

    assert report.verdict is AdmissionVerdict.REJECTED_SHADOW_AS_CANONICAL
    assert not report.canonical_inventory_admissible
    assert not report.counts_toward_canonical_inventory
    assert "shadow_storage_cannot_satisfy_protected_consumer" in report.reasons


def test_path_or_extension_is_not_an_authority_mechanism() -> None:
    """A shadow receipt cannot escalate by narrative alone; attestation is required."""

    episode = _episode()
    # Declaring canonical without an admission attestation is structurally rejected.
    receipt = _receipt(
        episode,
        storage_status=EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED,
        admission_attestation_id=None,
    )
    report = audit_episode_inventory_admission(
        receipt,
        episode,
        consumer=ProtectedConsumerKind.CANONICAL_INVENTORY,
    )
    assert report.verdict is AdmissionVerdict.REJECTED_STATUS_MISMATCH
    assert "canonical_admission_attestation_missing" in report.reasons


# --- world 4: malformed / stale-hash variants --------------------------------


def test_world4_stale_episode_artifact_hash_fails_closed() -> None:
    episode = _episode()
    receipt = _receipt(
        episode,
        storage_status=EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED,
        episode_artifact_hash="a" * 64,
    )
    report = audit_episode_inventory_admission(
        receipt,
        episode,
        consumer=ProtectedConsumerKind.CANONICAL_INVENTORY,
    )
    assert report.verdict is AdmissionVerdict.CANNOT_CHECK
    assert "episode_artifact_hash_mismatch" in report.reasons


def test_world4_malformed_episode_hash_on_episode_fails_like_strict_contract() -> None:
    episode = _episode(artifact_hash="sha256:" + ("b" * 64))
    receipt = _receipt(
        episode,
        storage_status=EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED,
        episode_artifact_hash="b" * 64,
    )
    report = audit_episode_inventory_admission(
        receipt,
        episode,
        consumer=ProtectedConsumerKind.CANONICAL_INVENTORY,
    )
    assert report.verdict is AdmissionVerdict.CANNOT_CHECK
    assert any(reason.startswith("episode_invalid:") for reason in report.reasons)


def test_world4_episode_id_mismatch_fails_closed() -> None:
    episode = _episode()
    receipt = _receipt(
        episode,
        storage_status=EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED,
        episode_id="E-other",
    )
    report = audit_episode_inventory_admission(
        receipt,
        episode,
        consumer=ProtectedConsumerKind.CANONICAL_INVENTORY,
    )
    assert report.verdict is AdmissionVerdict.CANNOT_CHECK
    assert "episode_id_mismatch" in report.reasons


def test_world4_missing_receipt_for_protected_consumer_fails_closed() -> None:
    report = audit_episode_inventory_admission(
        None,
        _episode(),
        consumer=ProtectedConsumerKind.PROMOTION_GATE,
    )
    assert report.verdict is AdmissionVerdict.CANNOT_CHECK
    assert "no_admission_receipt_supplied_for_protected_consumer" in report.reasons


# --- authority / schema ------------------------------------------------------


def test_document_authority_flags_are_literal_false() -> None:
    episode = _episode()
    doc = _receipt(episode).document()
    assert doc["grants_proof_authority"] is False
    assert doc["grants_lesson_tool_authority"] is False
    assert doc["grants_framework_authority"] is False
    assert doc["path_or_extension_is_not_authority"] is True
    assert doc["receipt_canonical_sha256"] == _receipt(episode).receipt_canonical_sha256


def test_receipt_document_validates_against_frozen_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    episode = _episode()
    shadow = _receipt(
        episode, storage_status=EpisodeStorageStatus.PROPOSAL_SHADOW_STORED
    )
    canonical = _receipt(
        episode, storage_status=EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED
    )
    validator.validate(shadow.document())
    validator.validate(canonical.document())


def test_schema_rejects_receipt_that_claims_authority() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    episode = _episode()
    doc = dict(_receipt(episode).document())
    doc["grants_framework_authority"] = True
    with pytest.raises(Exception):
        validator.validate(doc)


def test_schema_rejects_canonical_without_attestation() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)
    episode = _episode()
    doc = dict(
        _receipt(
            episode, storage_status=EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED
        ).document()
    )
    doc["admission_attestation_id"] = None
    # Recompute hash would still be wrong for content; schema alone must reject.
    with pytest.raises(Exception):
        validator.validate(doc)


def test_canonical_episode_remains_usable_for_search_learning() -> None:
    episode = _episode()
    receipt = _receipt(
        episode, storage_status=EpisodeStorageStatus.CANONICAL_INVENTORY_ADMITTED
    )
    report = audit_episode_inventory_admission(
        receipt,
        episode,
        consumer=ProtectedConsumerKind.SEARCH_OR_FAILURE_LEARNING,
    )
    assert report.verdict is AdmissionVerdict.CANONICAL_ADMISSION_VERIFIED
    assert report.retained_for_search_or_failure_learning
