from __future__ import annotations

from rakl.mini_archive_demo import run_mini_archive_demo


def test_pendulum_archive_demo_preserves_history_while_bounding_hot_footprint():
    receipt = run_mini_archive_demo()
    assert receipt.original_source_records == 8
    assert receipt.original_logical_raw_bytes == 826
    assert receipt.original_unique_blobs == 8
    assert receipt.original_stored_physical_bytes <= receipt.original_logical_raw_bytes
    assert receipt.records_after_byte_identical_refetch == 9
    assert receipt.unique_blobs_after_byte_identical_refetch == 8
    assert receipt.refetch_stored_bytes_delta == 0
    assert receipt.refetch_deduplicated
    assert receipt.stored_physical_bytes_after_byte_identical_refetch == receipt.original_stored_physical_bytes
    assert receipt.hot_unique_blobs_after_demotion == 3
    assert receipt.cold_unique_blobs_after_demotion == 5
    assert receipt.total_stored_bytes_after_demotion == receipt.original_stored_physical_bytes
    assert receipt.rehydration_verified
    assert receipt.canonical_records_deleted == 0
    assert receipt.proves_scientific_superiority is False
