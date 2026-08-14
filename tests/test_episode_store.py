"""Durable episode-store tests (ORION capability 1: persistent episode memory).

Proves: the checker does not cry wolf (untampered store verifies VALID - the
no-alarm control comes first), the JSONL hash chain detects a bit-flipped
middle record at the right index, truncation and torn tail writes are TRUNCATED
not VALID, a missing file is CANNOT_CHECK (never "checked and fine"), the
in-memory substrate objects round-trip exactly, queries return copies, storing
an episode never upgrades its admission, and the runtime-resumption episode-
store reference is add-only (old-format serialized states restore unchanged).
"""
from __future__ import annotations

import dataclasses
import json
from dataclasses import replace
from hashlib import sha256
from types import SimpleNamespace

import pytest

from rakl.episode_store import (
    ChainVerdict,
    EpisodeStore,
    EpisodeStoreIntegrityError,
    _record_hash,
    load_experience_ledger,
    verify_episode_store,
)
from rakl.evolution_trace import MetricLedger
from rakl.experience_substrate import (
    EpisodeAdmissionReceipt,
    EpisodeOutcome,
    EpisodeStorageAdmission,
    ExperienceLedger,
    InventoryAdmissionVerdict,
    Lesson,
    LessonAuthority,
    LessonKind,
    TaskEpisode,
    add_admission_receipt,
    add_episode,
    add_lesson,
    admission_receipt_content_bytes,
    episode_content_bytes,
    lesson_content_bytes,
    resolve_inventory_admission,
)
from rakl.observability_adapters import (
    build_evaluation_epoch,
    process_telemetry_to_receipts,
    rakl_canonical_metrics,
)
from rakl.runtime_resumption import (
    ResumableStateEnvelope,
    restore_resumable_state,
    serialize_resumable_state,
)
from rakl.v3_authority import canonical_json_bytes


def _episode(
    episode_id: str,
    outcome: EpisodeOutcome,
    *,
    timestamp: str = "2026-08-11T08:30:00+00:00",
    storage_admission: EpisodeStorageAdmission = EpisodeStorageAdmission.PROPOSAL_SHADOW_STORED,
) -> TaskEpisode:
    residual = () if outcome is EpisodeOutcome.SUCCESS else ("bridge",)
    draft = TaskEpisode(
        episode_id=episode_id,
        task_id=f"task-{episode_id}",
        atom_id="A1",
        context_hash="ctx-1",
        problem_signature=("bridge", "graph"),
        fibre_snapshot_hash=f"fibre-{episode_id}",
        operator_ids=("bridge-op",),
        action_trace=("compile fibre", "apply operator", "verify outcome"),
        observation_ids=(f"obs-{episode_id}",),
        verification_ids=(f"verify-{episode_id}",),
        outcome=outcome,
        residual_signature=residual,
        evidence_pointers=(f"artifact:{episode_id}",),
        artifact_hash="",
        timestamp=timestamp,
        cost=1.0,
        storage_admission=storage_admission,
    )
    return replace(draft, artifact_hash=sha256(episode_content_bytes(draft)).hexdigest())


def _lesson(lesson_id: str = "L1", supporting: tuple[str, ...] = ("E1",)) -> Lesson:
    draft = Lesson(
        lesson_id=lesson_id,
        kind=LessonKind.OPERATOR,
        trigger_signature=("bridge", "graph"),
        context_scope=("finite graph", "typed interface"),
        action="introduce a typed bridge object before global composition",
        expected_effects=("connect", "reduce_missing_bridge"),
        boundaries=("does not prove bridge correctness",),
        supporting_episode_ids=supporting,
        contradicting_episode_ids=(),
        falsifier="old no-bridge counterexample still passes unchanged",
        authority=LessonAuthority.CANDIDATE,
        validation_obligations=("validate bridge mapping",),
        evidence_pointers=("artifact:E1",),
        artifact_hash="",
    )
    return replace(draft, artifact_hash=sha256(lesson_content_bytes(draft)).hexdigest())


def _admission_receipt(episode: TaskEpisode) -> EpisodeAdmissionReceipt:
    draft = EpisodeAdmissionReceipt(
        receipt_id=f"R-{episode.episode_id}",
        episode_id=episode.episode_id,
        episode_artifact_hash=episode.artifact_hash,
        storage_admission=EpisodeStorageAdmission.CANONICAL_INVENTORY_ADMITTED,
        evidence_pointers=(f"registry:{episode.episode_id}",),
        artifact_hash="",
        timestamp="2026-08-11T09:00:00+00:00",
    )
    return replace(
        draft, artifact_hash=sha256(admission_receipt_content_bytes(draft)).hexdigest()
    )


def _ledger() -> ExperienceLedger:
    ledger = ExperienceLedger()
    ledger = add_episode(ledger, _episode("E1", EpisodeOutcome.SUCCESS))
    ledger = add_episode(
        ledger,
        _episode("E2", EpisodeOutcome.FAILURE, timestamp="2026-08-12T10:00:00+00:00"),
    )
    canonical = _episode(
        "E3",
        EpisodeOutcome.SUCCESS,
        timestamp="2026-08-13T11:00:00+00:00",
        storage_admission=EpisodeStorageAdmission.CANONICAL_INVENTORY_ADMITTED,
    )
    ledger = add_episode(ledger, canonical)
    ledger = add_admission_receipt(ledger, _admission_receipt(canonical))
    return add_lesson(ledger, _lesson())


def _populated_store(tmp_path):
    path = tmp_path / "episodes.jsonl"
    store = EpisodeStore(path)
    store.append_experience_ledger(_ledger())
    return path, store


# --- no-alarm control (validate the checker before trusting its alarms) -------
def test_untampered_store_verifies_valid_no_false_alarm(tmp_path):
    path, store = _populated_store(tmp_path)
    report = verify_episode_store(path)
    assert report.verdict is ChainVerdict.VALID
    assert report.valid
    assert report.first_bad_index is None
    assert report.reasons == ()
    assert report.head_hash == store.head_hash
    # With the expected head supplied it is still VALID, not TRUNCATED.
    assert verify_episode_store(path, expected_head_hash=store.head_hash).valid
    # Reopening (which replays and re-verifies) also raises no alarm.
    assert EpisodeStore(path).head_hash == store.head_hash


def test_empty_store_is_valid_with_empty_head(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("")
    report = verify_episode_store(path)
    assert report.verdict is ChainVerdict.VALID
    assert report.record_count == 0
    assert report.head_hash == ""


# --- exact round-trip ---------------------------------------------------------
def test_ledger_round_trips_exactly(tmp_path):
    path, _ = _populated_store(tmp_path)
    ledger = _ledger()
    restored = load_experience_ledger(path)
    assert restored == ledger
    # enums rebuild as members, tuples as tuples - not bare strings/lists
    assert restored.episodes[0].outcome is EpisodeOutcome.SUCCESS
    assert restored.episodes[0].storage_admission is EpisodeStorageAdmission.PROPOSAL_SHADOW_STORED
    assert isinstance(restored.episodes[0].problem_signature, tuple)
    assert restored.lessons[0].authority is LessonAuthority.CANDIDATE
    assert isinstance(restored.nodes[0].metadata, tuple)
    assert isinstance(restored.nodes[0].metadata[0], tuple)


def test_ledger_snapshot_requires_empty_store(tmp_path):
    _, store = _populated_store(tmp_path)
    with pytest.raises(ValueError, match="empty episode store"):
        store.append_experience_ledger(_ledger())


def test_append_refuses_invalid_and_duplicate_content(tmp_path):
    store = EpisodeStore(tmp_path / "episodes.jsonl")
    episode = _episode("E1", EpisodeOutcome.SUCCESS)
    store.append_episode(episode)
    with pytest.raises(ValueError, match="duplicate episode identity"):
        store.append_episode(episode)
    bad = replace(episode, episode_id="E-bad")  # artifact hash no longer matches
    with pytest.raises(ValueError, match="invalid episode"):
        store.append_episode(bad)


# --- hash-chain tamper detection ---------------------------------------------
def test_bit_flipped_middle_record_is_tampered_at_right_index(tmp_path):
    path, _ = _populated_store(tmp_path)
    lines = path.read_text().splitlines()
    middle = 2  # the E3 episode record - strictly interior (0 < 2 < len - 1)
    assert 0 < middle < len(lines) - 1
    flipped = lines[middle].replace('"atom_id":"A1"', '"atom_id":"Z1"', 1)
    assert flipped != lines[middle], "tamper fixture found nothing to flip"
    lines[middle] = flipped
    path.write_text("\n".join(lines) + "\n")
    report = verify_episode_store(path)
    assert report.verdict is ChainVerdict.TAMPERED
    assert report.first_bad_index == middle
    # Fail-closed: neither open nor load trusts a tampered chain.
    with pytest.raises(EpisodeStoreIntegrityError):
        EpisodeStore(path)
    with pytest.raises(EpisodeStoreIntegrityError):
        load_experience_ledger(path)


def test_rehashed_middle_record_breaks_the_chain_at_the_next_link(tmp_path):
    path, _ = _populated_store(tmp_path)
    lines = path.read_text().splitlines()
    middle = 2  # the E3 episode record - strictly interior
    record = json.loads(lines[middle])
    record["payload"]["atom_id"] = "Z1"
    # Hostile: the tamperer also recomputes the record's own seals ...
    record["payload_hash"] = sha256(canonical_json_bytes(record["payload"])).hexdigest()
    record["record_hash"] = _record_hash(record)
    lines[middle] = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n")
    report = verify_episode_store(path)
    # ... but the next record still embeds the original hash: chain breaks there.
    assert report.verdict is ChainVerdict.TAMPERED
    assert report.first_bad_index == middle + 1
    assert "previous_record_hash_mismatch" in report.reasons[0]


def test_deleted_interior_record_is_tampered(tmp_path):
    path, _ = _populated_store(tmp_path)
    lines = path.read_text().splitlines()
    middle = len(lines) // 2
    del lines[middle]
    path.write_text("\n".join(lines) + "\n")
    report = verify_episode_store(path)
    assert report.verdict is ChainVerdict.TAMPERED
    assert report.first_bad_index == middle


# --- truncation detection -----------------------------------------------------
def test_dropped_tail_records_are_truncated_against_expected_head(tmp_path):
    path, store = _populated_store(tmp_path)
    head = store.head_hash
    lines = path.read_text().splitlines()
    path.write_text("\n".join(lines[:-2]) + "\n")
    report = verify_episode_store(path, expected_head_hash=head)
    assert report.verdict is ChainVerdict.TRUNCATED
    assert report.reasons == ("head_hash_mismatch_on_internally_valid_chain",)
    # Without the expected head the shorter chain is internally valid -
    # exactly why resumption states carry the head hash.
    assert verify_episode_store(path).valid


def test_torn_tail_write_is_truncated_not_valid(tmp_path):
    path, _ = _populated_store(tmp_path)
    content = path.read_text()
    lines = content.splitlines()
    torn = "\n".join(lines[:-1]) + "\n" + lines[-1][: len(lines[-1]) // 2]
    path.write_text(torn)
    report = verify_episode_store(path)
    assert report.verdict is ChainVerdict.TRUNCATED
    assert report.first_bad_index == len(lines) - 1
    with pytest.raises(EpisodeStoreIntegrityError):
        EpisodeStore(path)


# --- CANNOT_CHECK is not "checked and fine" ----------------------------------
def test_missing_file_is_cannot_check_not_valid(tmp_path):
    report = verify_episode_store(tmp_path / "never-written.jsonl")
    assert report.verdict is ChainVerdict.CANNOT_CHECK
    assert not report.valid
    assert report.reasons == ("store_file_missing",)
    assert report.head_hash is None


def test_unsupported_record_schema_is_cannot_check(tmp_path):
    path, _ = _populated_store(tmp_path)
    lines = path.read_text().splitlines()
    record = json.loads(lines[0])
    record["schema_version"] = "rakl-episode-store-v999"
    record["record_hash"] = _record_hash(record)
    lines[0] = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    path.write_text("\n".join(lines) + "\n")
    assert verify_episode_store(path).verdict is ChainVerdict.CANNOT_CHECK


# --- query surface ------------------------------------------------------------
def test_queries_by_id_hash_outcome_and_time_range(tmp_path):
    _, store = _populated_store(tmp_path)
    episode = _episode("E1", EpisodeOutcome.SUCCESS)
    assert store.get_episode("E1") == episode
    assert store.get_episode("absent") is None
    assert store.find_by_artifact_hash(episode.artifact_hash) == (episode,)
    lesson = _lesson()
    assert store.find_by_artifact_hash(lesson.artifact_hash) == (lesson,)
    assert store.find_by_artifact_hash("0" * 64) == ()
    failures = store.episodes_by_outcome(EpisodeOutcome.FAILURE)
    assert tuple(item.episode_id for item in failures) == ("E2",)
    window = store.episodes_in_time_range(
        "2026-08-12T00:00:00+00:00", "2026-08-13T11:00:00+00:00"
    )
    assert tuple(item.episode_id for item in window) == ("E2", "E3")
    with pytest.raises(ValueError, match="timezone-aware"):
        store.episodes_in_time_range("not-a-time", "2026-08-13T11:00:00+00:00")
    with pytest.raises(ValueError, match="end precedes start"):
        store.episodes_in_time_range(
            "2026-08-13T11:00:00+00:00", "2026-08-12T00:00:00+00:00"
        )


def test_queries_return_copies_not_shared_references(tmp_path):
    _, store = _populated_store(tmp_path)
    first = store.get_episode("E1")
    second = store.get_episode("E1")
    assert first == second
    assert first is not second
    assert store.episodes() is not store.episodes()
    assert store.lessons()[0] is not store.lessons()[0]


# --- authority posture: the store mints nothing -------------------------------
def test_storing_a_shadow_episode_never_upgrades_it(tmp_path):
    store = EpisodeStore(tmp_path / "episodes.jsonl")
    shadow = _episode("E-shadow", EpisodeOutcome.SUCCESS)
    store.append_episode(shadow)
    loaded = store.get_episode("E-shadow")
    assert loaded.storage_admission is EpisodeStorageAdmission.PROPOSAL_SHADOW_STORED
    report = resolve_inventory_admission(loaded, None, treat_as_canonical=True)
    assert report.verdict is InventoryAdmissionVerdict.SHADOW_REFERENCED_AS_CANONICAL
    assert not report.counts_toward_canonical_inventory


# --- runtime-resumption integration (add-only) --------------------------------
def _epoch_and_ledger():
    epoch = build_evaluation_epoch(
        rakl_canonical_metrics,
        benchmark_protocol_hash="bench", evaluator_hash="eval",
        model_tool_harness_hash="mth", decision_policy_hash="dp",
        observatory_instrumentation_hash="oi",
    )
    telemetry = SimpleNamespace(
        invocation_id="inv1", process_surface="search", task_id="t1",
        output_state_hash="o1", outcome=SimpleNamespace(value="SUCCESS"),
        cost=2500.0, cost_policy_id="cp1",
        residual_before=("r1", "r2", "r3"), residual_after=("r1",),
        retained_novelty=(), raw_residual_contraction=2,
    )
    cost_r, contraction, out = process_telemetry_to_receipts(
        telemetry, epoch, rakl_canonical_metrics, sequence_base=0)
    return epoch, MetricLedger((cost_r, contraction, out))


def test_old_format_serialized_state_restores_unchanged():
    epoch, ledger = _epoch_and_ledger()
    envelope = serialize_resumable_state(epoch=epoch, ledger=ledger)
    # Simulate a state persisted before the episode-store fields existed:
    # its dict has only the original v1 keys.
    old_dict = {
        key: value
        for key, value in dataclasses.asdict(envelope).items()
        if key not in ("episode_store_path", "episode_store_head_hash")
    }
    old_envelope = ResumableStateEnvelope(**old_dict)
    restored = restore_resumable_state(old_envelope)
    assert restored.epoch == epoch
    assert restored.ledger == ledger
    assert restored.episode_store_path is None
    assert restored.episode_store_head_hash is None


def test_envelope_episode_store_reference_round_trips_and_is_checkable(tmp_path):
    path, store = _populated_store(tmp_path)
    epoch, ledger = _epoch_and_ledger()
    envelope = serialize_resumable_state(
        epoch=epoch,
        ledger=ledger,
        episode_store_path=str(path),
        episode_store_head_hash=store.head_hash,
    )
    restored = restore_resumable_state(envelope)
    assert restored.episode_store_path == str(path)
    assert restored.episode_store_head_hash == store.head_hash
    # The reference is a pointer, not authority: the store's own verifier is
    # what checks it, and it catches a store truncated after the state was saved.
    assert verify_episode_store(
        restored.episode_store_path,
        expected_head_hash=restored.episode_store_head_hash,
    ).valid
    lines = path.read_text().splitlines()
    path.write_text("\n".join(lines[:-1]) + "\n")
    late = verify_episode_store(
        restored.episode_store_path,
        expected_head_hash=restored.episode_store_head_hash,
    )
    assert late.verdict is ChainVerdict.TRUNCATED


def test_default_serialization_omits_episode_store_reference():
    epoch, ledger = _epoch_and_ledger()
    envelope = serialize_resumable_state(epoch=epoch, ledger=ledger)
    assert envelope.episode_store_path is None
    assert envelope.episode_store_head_hash is None
    restored = restore_resumable_state(envelope)
    assert restored.episode_store_path is None
    assert restored.episode_store_head_hash is None
