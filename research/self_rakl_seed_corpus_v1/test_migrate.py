"""Research-local tests for the SELF_RAKL_RESEARCH_* seed-corpus migration.

Covers: real-receipt round-trip (source hash binding), CANNOT_PARSE as a
first-class skip outcome, NO_RECOVERABLE_DATE as a typed skip, proposal-only
admission, and byte-level determinism of the produced store.

Run only this file:  python3 -m pytest research/self_rakl_seed_corpus_v1/test_migrate.py
"""

from __future__ import annotations

import sys
from hashlib import sha256
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

import migrate  # noqa: E402
from migrate import (  # noqa: E402
    REASON_CANNOT_PARSE,
    REASON_NO_RECOVERABLE_DATE,
    SkipEntry,
    episode_from_receipt,
    parse_receipt_file,
    run_migration,
)
from rakl.episode_store import EpisodeStore, verify_episode_store  # noqa: E402
from rakl.experience_substrate import (  # noqa: E402
    EpisodeOutcome,
    EpisodeStorageAdmission,
    TaskEpisode,
    validate_episode,
)

RESEARCH_DIR = _HERE.parent


def _episode_for(name: str) -> TaskEpisode:
    parsed = parse_receipt_file(RESEARCH_DIR / name, RESEARCH_DIR)
    assert not isinstance(parsed, SkipEntry), parsed
    episode = episode_from_receipt(parsed)
    assert isinstance(episode, TaskEpisode), episode
    return episode


@pytest.mark.parametrize(
    "name",
    [
        "SELF_RAKL_RESEARCH_001.md",
        "SELF_RAKL_RESEARCH_002_RECEIPT.json",
        "SELF_RAKL_RESEARCH_006_VALIDATION.json",
    ],
)
def test_round_trip_source_hash_binds_real_receipt(name: str) -> None:
    """The mapped episode's sha256 evidence pointer matches the raw file bytes."""

    episode = _episode_for(name)
    raw_digest = sha256((RESEARCH_DIR / name).read_bytes()).hexdigest()
    assert f"research/{name}" in episode.evidence_pointers
    assert f"sha256:{raw_digest}" in episode.evidence_pointers
    assert validate_episode(episode) == ()
    assert episode.storage_admission is EpisodeStorageAdmission.PROPOSAL_SHADOW_STORED


def test_real_receipt_field_recovery_is_content_derived() -> None:
    md = _episode_for("SELF_RAKL_RESEARCH_001.md")
    assert md.task_id == "SELF_RAKL_RESEARCH_001"
    assert md.atom_id == "MAIN"
    assert md.timestamp == "2026-08-09T00:00:00Z"
    assert md.outcome is EpisodeOutcome.UNKNOWN
    assert "object:RAKL_METHOD" in md.problem_signature

    receipt = _episode_for("SELF_RAKL_RESEARCH_002_RECEIPT.json")
    assert receipt.atom_id == "RECEIPT"
    # Negative history preserved: the receipt's native process residual survives.
    assert (
        "native_process_residual:META_N016_PREPROMOTION_STAGING"
        in receipt.residual_signature
    )

    validation = _episode_for("SELF_RAKL_RESEARCH_006_VALIDATION.json")
    # Explicit PROMOTED marker only; no prose interpretation.
    assert validation.outcome is EpisodeOutcome.SUCCESS
    assert "ci_run:31293064693" in validation.verification_ids


def test_no_recoverable_date_is_typed_skip_not_fabrication() -> None:
    parsed = parse_receipt_file(RESEARCH_DIR / "SELF_RAKL_RESEARCH_042.md", RESEARCH_DIR)
    assert not isinstance(parsed, SkipEntry)
    result = episode_from_receipt(parsed)
    assert isinstance(result, SkipEntry)
    assert result.reason == REASON_NO_RECOVERABLE_DATE


def test_cannot_parse_is_first_class_and_counts_sum(tmp_path: Path) -> None:
    corpus = tmp_path / "research"
    corpus.mkdir()
    good = RESEARCH_DIR / "SELF_RAKL_RESEARCH_002_RECEIPT.json"
    (corpus / good.name).write_bytes(good.read_bytes())
    (corpus / "SELF_RAKL_RESEARCH_998_RECEIPT.json").write_text(
        "{not valid json", encoding="utf-8"
    )
    (corpus / "SELF_RAKL_RESEARCH_999_RECEIPT.json").write_bytes(b"\xff\xfe\x00broken")

    result = run_migration(corpus, tmp_path / "out")
    assert result.inventory_count == 3
    assert result.ingested_count == 1
    reasons = {entry.file: entry.reason for entry in result.skipped}
    assert reasons["research/SELF_RAKL_RESEARCH_998_RECEIPT.json"] == REASON_CANNOT_PARSE
    assert reasons["research/SELF_RAKL_RESEARCH_999_RECEIPT.json"] == REASON_CANNOT_PARSE
    assert result.ingested_count + len(result.skipped) == result.inventory_count
    assert result.verification.verdict.value == "VALID"


def test_full_migration_deterministic_and_proposal_only(tmp_path: Path) -> None:
    first = run_migration(RESEARCH_DIR, tmp_path / "run1")
    second = run_migration(RESEARCH_DIR, tmp_path / "run2")

    # Same input -> same store bytes (and identical sidecars).
    for name in (
        migrate.STORE_FILENAME,
        migrate.SKIP_LIST_FILENAME,
        migrate.ADMISSION_RECEIPTS_FILENAME,
    ):
        assert (tmp_path / "run1" / name).read_bytes() == (
            tmp_path / "run2" / name
        ).read_bytes()
    assert first.head_hash == second.head_hash

    # Counts sum to the inventory; typed verify is VALID.
    assert first.ingested_count + len(first.skipped) == first.inventory_count
    report = verify_episode_store(
        first.store_path, expected_head_hash=first.head_hash
    )
    assert report.verdict.value == "VALID"
    assert report.record_count == first.ingested_count

    # Proposal-only: nothing canonical anywhere; admission was SHADOW_RETAINED.
    store = EpisodeStore(first.store_path)
    for episode in store.episodes():
        assert episode.storage_admission is EpisodeStorageAdmission.PROPOSAL_SHADOW_STORED
    assert set(first.admission_verdicts.values()) == {"SHADOW_RETAINED"}
    assert len(first.admission_verdicts) == first.ingested_count
    # The store contains no admission-receipt records (canonical-only kind).
    assert store.admission_receipts() == ()


def test_refuses_to_overwrite_existing_store(tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    (out / migrate.STORE_FILENAME).write_text("", encoding="utf-8")
    with pytest.raises(FileExistsError):
        run_migration(RESEARCH_DIR, out)
