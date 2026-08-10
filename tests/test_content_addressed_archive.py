from __future__ import annotations

import pytest

from rakl.content_addressed_archive import (
    ArchiveCodec,
    ArchiveTier,
    ColdDemotionVerdict,
    ContentAddressedArchive,
    HotArchivePolicy,
)


def test_identical_payloads_deduplicate_physical_blob_but_keep_logical_records():
    archive = ContentAddressedArchive()
    payload = (b"same scientific source payload\n" * 40)
    first = archive.put("raw:S1", payload)
    second = archive.put("raw:S1-copy", payload)
    metrics = archive.metrics()

    assert first.new_logical_record and first.new_physical_blob
    assert second.new_logical_record and not second.new_physical_blob
    assert metrics.logical_records == 2
    assert metrics.unique_blobs == 1
    assert metrics.deduplicated_raw_bytes == len(payload)
    assert archive.rehydrate("raw:S1") == payload
    assert archive.rehydrate("raw:S1-copy") == payload


def test_compression_is_lossless_and_only_changes_physical_representation():
    archive = ContentAddressedArchive()
    payload = b"finite amplitude correction; " * 200
    result = archive.put("raw:S3", payload)
    metrics = archive.metrics()

    assert result.codec is ArchiveCodec.ZLIB
    assert result.payload_hash == archive.digest(payload)
    assert metrics.stored_physical_bytes < metrics.unique_raw_bytes
    assert metrics.compression_saved_bytes > 0
    assert archive.rehydrate("raw:S3") == payload


def test_same_canonical_record_id_cannot_be_rebound_to_new_content():
    archive = ContentAddressedArchive()
    archive.put("raw:S1", b"version one")
    with pytest.raises(ValueError, match="cannot be rebound"):
        archive.put("raw:S1", b"different content")


def test_idempotent_same_record_same_payload_has_zero_storage_delta():
    archive = ContentAddressedArchive()
    payload = b"stable bytes"
    archive.put("raw:S1", payload)
    again = archive.put("raw:S1", payload)
    assert not again.new_logical_record
    assert not again.new_physical_blob
    assert again.raw_bytes_delta == 0
    assert again.stored_bytes_delta == 0


def test_cold_demotion_reduces_hot_footprint_without_deleting_or_corrupting_records():
    archive = ContentAddressedArchive()
    payloads = {
        "raw:mandatory": b"mandatory evidence " * 50,
        "raw:old-a": b"old evidence A " * 80,
        "raw:old-b": b"old evidence B " * 100,
    }
    for record_id, payload in payloads.items():
        archive.put(record_id, payload)

    before = archive.metrics()
    protected_blob = next(
        blob for blob in archive.blobs
        if blob.payload_hash == archive.digest(payloads["raw:mandatory"])
    )
    policy = HotArchivePolicy(
        max_hot_stored_bytes=protected_blob.stored_bytes,
        max_hot_unique_blobs=1,
    )
    plan = archive.plan_cold_demotion(policy, protected_record_ids=("raw:mandatory",))
    assert plan.verdict is ColdDemotionVerdict.DEMOTION_PLAN_AVAILABLE
    assert protected_blob.payload_hash not in plan.demote_payload_hashes

    archive.apply_cold_demotion(plan)
    after = archive.metrics()
    assert after.hot_unique_blobs == 1
    assert after.hot_stored_bytes <= policy.max_hot_stored_bytes
    assert after.cold_unique_blobs == 2
    assert after.stored_physical_bytes == before.stored_physical_bytes
    assert all(archive.rehydrate(record_id) == payload for record_id, payload in payloads.items())
    assert any(blob.tier is ArchiveTier.COLD for blob in archive.blobs)


def test_protected_set_can_make_hot_capacity_unsatisfiable_without_deletion():
    archive = ContentAddressedArchive()
    archive.put("raw:must-a", b"A" * 1000)
    archive.put("raw:must-b", b"B" * 1000)
    policy = HotArchivePolicy(max_hot_stored_bytes=0, max_hot_unique_blobs=0)
    plan = archive.plan_cold_demotion(
        policy,
        protected_record_ids=("raw:must-a", "raw:must-b"),
    )
    assert plan.verdict is ColdDemotionVerdict.CANNOT_SATISFY_WITH_PROTECTED_SET
    assert plan.demote_payload_hashes == ()
    with pytest.raises(ValueError, match="unsatisfied"):
        archive.apply_cold_demotion(plan)
    assert archive.rehydrate("raw:must-a") == b"A" * 1000
    assert archive.rehydrate("raw:must-b") == b"B" * 1000
