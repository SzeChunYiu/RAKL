from __future__ import annotations

from dataclasses import asdict, dataclass
import json

from .content_addressed_archive import ContentAddressedArchive, HotArchivePolicy
from .mini_research_demo import _sources


@dataclass(frozen=True)
class MiniArchiveReceipt:
    demo_id: str
    original_source_records: int
    original_logical_raw_bytes: int
    original_unique_blobs: int
    original_stored_physical_bytes: int
    original_compression_saved_bytes: int
    records_after_byte_identical_refetch: int
    unique_blobs_after_byte_identical_refetch: int
    logical_raw_bytes_after_byte_identical_refetch: int
    stored_physical_bytes_after_byte_identical_refetch: int
    refetch_stored_bytes_delta: int
    refetch_deduplicated: bool
    hot_unique_blobs_after_demotion: int
    cold_unique_blobs_after_demotion: int
    hot_stored_bytes_after_demotion: int
    total_stored_bytes_after_demotion: int
    rehydration_verified: bool
    canonical_records_deleted: int
    proves_scientific_superiority: bool


def run_mini_archive_demo() -> MiniArchiveReceipt:
    archive = ContentAddressedArchive()
    sources = _sources()
    source_payloads = {
        f"raw:{source.source_id}": source.text.encode("utf-8") for source in sources
    }
    for record_id, payload in source_payloads.items():
        archive.put(record_id, payload)
    original = archive.metrics()

    first_record_id = f"raw:{sources[0].source_id}"
    refetch_payload = source_payloads[first_record_id]
    refetch = archive.put(f"{first_record_id}:refetch", refetch_payload)
    after_refetch = archive.metrics()

    protected_record_ids = ("raw:S1", "raw:S3", "raw:S7")
    protected_hashes = {
        archive.digest(source_payloads[record_id]) for record_id in protected_record_ids
    }
    protected_stored_bytes = sum(
        blob.stored_bytes for blob in archive.blobs if blob.payload_hash in protected_hashes
    )
    plan = archive.plan_cold_demotion(
        HotArchivePolicy(
            max_hot_stored_bytes=protected_stored_bytes,
            max_hot_unique_blobs=len(protected_hashes),
        ),
        protected_record_ids=protected_record_ids,
    )
    archive.apply_cold_demotion(plan)
    after_demotion = archive.metrics()

    rehydration_verified = all(
        archive.rehydrate(record_id) == payload
        for record_id, payload in source_payloads.items()
    ) and archive.rehydrate(f"{first_record_id}:refetch") == refetch_payload

    return MiniArchiveReceipt(
        demo_id="PENDULUM_CONTEXT_ATLAS_001_ARCHIVE_V1",
        original_source_records=original.logical_records,
        original_logical_raw_bytes=original.logical_raw_bytes,
        original_unique_blobs=original.unique_blobs,
        original_stored_physical_bytes=original.stored_physical_bytes,
        original_compression_saved_bytes=original.compression_saved_bytes,
        records_after_byte_identical_refetch=after_refetch.logical_records,
        unique_blobs_after_byte_identical_refetch=after_refetch.unique_blobs,
        logical_raw_bytes_after_byte_identical_refetch=after_refetch.logical_raw_bytes,
        stored_physical_bytes_after_byte_identical_refetch=after_refetch.stored_physical_bytes,
        refetch_stored_bytes_delta=refetch.stored_bytes_delta,
        refetch_deduplicated=not refetch.new_physical_blob,
        hot_unique_blobs_after_demotion=after_demotion.hot_unique_blobs,
        cold_unique_blobs_after_demotion=after_demotion.cold_unique_blobs,
        hot_stored_bytes_after_demotion=after_demotion.hot_stored_bytes,
        total_stored_bytes_after_demotion=after_demotion.stored_physical_bytes,
        rehydration_verified=rehydration_verified,
        canonical_records_deleted=0,
        proves_scientific_superiority=False,
    )


def receipt_json(*, indent: int = 2) -> str:
    return json.dumps(asdict(run_mini_archive_demo()), indent=indent, sort_keys=True) + "\n"


def main() -> int:
    print(receipt_json(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
