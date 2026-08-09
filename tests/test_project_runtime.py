import json

import pytest

from rakl.project_runtime import (
    PayloadIntegrityError,
    ProjectRuntimeError,
    RAKLProject,
    TaskPacketVerdict,
)


def test_canonical_store_deduplicates_equal_bytes(tmp_path):
    project = RAKLProject.create(tmp_path, project_id="p")
    first = project.store.put_bytes(b"same")
    second = project.store.put_bytes(b"same")
    assert first.sha256 == second.sha256
    assert project.store.object_count() == 1


def test_different_bytes_have_different_identity(tmp_path):
    project = RAKLProject.create(tmp_path, project_id="p")
    first = project.store.put_bytes(b"a")
    second = project.store.put_bytes(b"b")
    assert first.sha256 != second.sha256
    assert project.store.object_count() == 2


def test_tampered_payload_is_detected(tmp_path):
    project = RAKLProject.create(tmp_path, project_id="p")
    stored = project.store.put_bytes(b"canonical")
    project.store.path_for(stored.sha256).write_bytes(b"tampered")
    with pytest.raises(PayloadIntegrityError):
        project.store.read_bytes(stored.sha256)


def test_record_id_with_separators_never_controls_filesystem_path(tmp_path):
    root = tmp_path / "project"
    project = RAKLProject.create(root, project_id="p")
    project.ingest_bytes(
        record_id="nested/record/name",
        payload=b"evidence",
        token_cost=5,
        coverage_atoms=("fact",),
    )
    record_files = list((root / ".rakl" / "records").glob("*.json"))
    assert len(record_files) == 1
    assert record_files[0].parent == root / ".rakl" / "records"
    assert not (root / ".rakl" / "records" / "nested").exists()


def test_existing_incompatible_project_is_not_reinitialized(tmp_path):
    first = RAKLProject.create(tmp_path, project_id="one", reference_profile="ordinary-8k")
    original = first.manifest_path.read_bytes()
    with pytest.raises(ProjectRuntimeError):
        RAKLProject.create(tmp_path, project_id="two", reference_profile="ordinary-8k")
    assert first.manifest_path.read_bytes() == original


def test_exact_ingest_replay_is_idempotent_but_record_identity_is_immutable(tmp_path):
    project = RAKLProject.create(tmp_path, project_id="p")
    first = project.ingest_bytes(
        record_id="r1",
        payload=b"one",
        token_cost=4,
        coverage_atoms=("a",),
    )
    replay = project.ingest_bytes(
        record_id="r1",
        payload=b"one",
        token_cost=4,
        coverage_atoms=("a",),
    )
    assert replay == first
    with pytest.raises(ProjectRuntimeError):
        project.ingest_bytes(
            record_id="r1",
            payload=b"different",
            token_cost=4,
            coverage_atoms=("a",),
        )


def test_mandatory_negative_history_survives_packet_compilation(tmp_path):
    project = RAKLProject.create(tmp_path, project_id="p")
    project.ingest_bytes(
        record_id="old-refutation",
        payload=b"mechanism A was refuted by intervention X",
        token_cost=3,
        kind="FAILURE",
        coverage_atoms=("negative_history",),
        mandatory=True,
    )
    for index in range(20):
        project.ingest_bytes(
            record_id=f"optional-{index:02d}",
            payload=f"optional {index}".encode(),
            token_cost=2,
            fiber_ids=("other",),
            coverage_atoms=(f"optional_{index}",),
        )
    report = project.compile_task_packet(
        operation="mechanism_review",
        question="Is mechanism A still viable?",
        budget_tokens=5,
        target_fibers=("target",),
        required_coverage_atoms=("negative_history",),
    )
    assert report.verdict == TaskPacketVerdict.READY
    assert report.packet is not None
    ids = [record["record_id"] for record in report.packet["selected_records"]]
    assert ids == ["old-refutation"]
    assert report.packet["authority_boundary"]["llm_output_authority"] == "PROPOSAL_ONLY"


def test_mandatory_over_budget_fails_closed(tmp_path):
    project = RAKLProject.create(tmp_path, project_id="p")
    project.ingest_bytes(
        record_id="mandatory",
        payload=b"critical evidence",
        token_cost=10,
        coverage_atoms=("critical",),
        mandatory=True,
    )
    report = project.compile_task_packet(
        operation="review",
        question="q",
        budget_tokens=5,
        required_coverage_atoms=("critical",),
    )
    assert report.verdict == TaskPacketVerdict.CANNOT_COMPILE
    assert report.packet is None
    assert "mandatory_over_budget" in report.issues


def test_task_packet_replay_is_deterministic(tmp_path):
    project = RAKLProject.create(tmp_path, project_id="p")
    project.ingest_bytes(
        record_id="source",
        payload=b"source text",
        token_cost=3,
        fiber_ids=("f",),
        coverage_atoms=("claim",),
    )
    kwargs = dict(
        operation="synthesis",
        question="What follows?",
        budget_tokens=10,
        target_fibers=("f",),
        required_coverage_atoms=("claim",),
    )
    first = project.compile_task_packet(**kwargs)
    second = project.compile_task_packet(**kwargs)
    assert first.verdict == TaskPacketVerdict.READY
    assert second.verdict == TaskPacketVerdict.READY
    assert project.canonical_packet_json(first.packet) == project.canonical_packet_json(second.packet)


def test_doctor_detects_missing_payload(tmp_path):
    project = RAKLProject.create(tmp_path, project_id="p")
    record = project.ingest_bytes(
        record_id="r",
        payload=b"source",
        token_cost=2,
        coverage_atoms=("x",),
    )
    project.store.path_for(record.payload_sha256).unlink()
    report = project.doctor()
    assert not report.healthy
    assert any(issue.startswith("missing_payload:r:") for issue in report.issues)


def test_doctor_accepts_clean_project(tmp_path):
    project = RAKLProject.create(tmp_path, project_id="p")
    project.ingest_bytes(
        record_id="r",
        payload=b"source",
        token_cost=2,
        coverage_atoms=("x",),
    )
    report = project.doctor()
    assert report.healthy
    assert report.record_count == 1
    assert report.payload_count == 1


def test_non_utf8_payload_cannot_be_materialized_for_llm(tmp_path):
    project = RAKLProject.create(tmp_path, project_id="p")
    project.ingest_bytes(
        record_id="binary",
        payload=bytes([255, 254, 0]),
        token_cost=2,
        coverage_atoms=("binary",),
        mandatory=True,
    )
    report = project.compile_task_packet(
        operation="review",
        question="inspect",
        budget_tokens=10,
        required_coverage_atoms=("binary",),
    )
    assert report.verdict == TaskPacketVerdict.CANNOT_MATERIALIZE
    assert report.packet is None
    assert "non_utf8_payload:binary" in report.issues


def test_packet_source_digest_matches_exact_payload(tmp_path):
    project = RAKLProject.create(tmp_path, project_id="p")
    record = project.ingest_bytes(
        record_id="r",
        payload=b"abc",
        token_cost=2,
        coverage_atoms=("x",),
        mandatory=True,
    )
    report = project.compile_task_packet(
        operation="extract",
        question="q",
        budget_tokens=10,
        required_coverage_atoms=("x",),
    )
    assert report.packet["source_digests"] == [record.payload_sha256]
    json.dumps(report.packet)
