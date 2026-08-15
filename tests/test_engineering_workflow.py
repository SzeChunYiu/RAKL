import sqlite3

import pytest

from rakl.engineering_workflow import (
    ActivitySpec,
    ActivityStatus,
    SqliteReferenceWorkflowEngine,
    WorkflowIntegrityError,
    WorkflowStatus,
)


def spec(activity_id="a", *, retry_safe=True, external_effect=True, max_attempts=3):
    return ActivitySpec(
        activity_id=activity_id,
        invocation_id=f"invoke:{activity_id}",
        input_digest=f"input:{activity_id}",
        retry_safe=retry_safe,
        external_effect=external_effect,
        max_attempts=max_attempts,
    )


def test_durable_history_survives_engine_reopen_and_completes(tmp_path):
    path = tmp_path / "workflow.sqlite3"
    engine = SqliteReferenceWorkflowEngine(path)
    engine.start_workflow(workflow_id="w1", project_id="p", project_snapshot_id="s0")
    engine.schedule_activity("w1", spec())
    engine.begin_activity("w1", "a")
    engine.complete_activity("w1", "a", result_digest="result:1")

    reopened = SqliteReferenceWorkflowEngine(path)
    assert reopened.verify_history("w1")
    assert reopened.activity("w1", "a").status is ActivityStatus.COMPLETED
    assert reopened.complete_workflow("w1").status is WorkflowStatus.COMPLETED


def test_ambiguous_non_retry_safe_external_effect_blocks_reexecution(tmp_path):
    engine = SqliteReferenceWorkflowEngine(tmp_path / "workflow.sqlite3")
    engine.start_workflow(workflow_id="w", project_id="p", project_snapshot_id="s")
    engine.schedule_activity("w", spec(retry_safe=False, external_effect=True))
    engine.begin_activity("w", "a")
    recovered = engine.recover_ambiguous_activity("w", "a")
    assert recovered.status is ActivityStatus.RECOVERY_REQUIRED
    assert engine.workflow("w").status is WorkflowStatus.RECOVERY_REQUIRED
    with pytest.raises(WorkflowIntegrityError):
        engine.begin_activity("w", "a")


def test_ambiguous_retry_safe_activity_can_be_retried_with_attempt_history(tmp_path):
    engine = SqliteReferenceWorkflowEngine(tmp_path / "workflow.sqlite3")
    engine.start_workflow(workflow_id="w", project_id="p", project_snapshot_id="s")
    engine.schedule_activity("w", spec(retry_safe=True, external_effect=True))
    first = engine.begin_activity("w", "a")
    assert first.attempt_count == 1
    assert engine.recover_ambiguous_activity("w", "a").status is ActivityStatus.SCHEDULED
    second = engine.begin_activity("w", "a")
    assert second.attempt_count == 2
    assert engine.verify_history("w")


def test_retryable_failure_requires_declared_retry_safety(tmp_path):
    engine = SqliteReferenceWorkflowEngine(tmp_path / "workflow.sqlite3")
    engine.start_workflow(workflow_id="w", project_id="p", project_snapshot_id="s")
    engine.schedule_activity("w", spec(retry_safe=False))
    engine.begin_activity("w", "a")
    failed = engine.fail_activity("w", "a", error="timeout", retryable=True)
    assert failed.status is ActivityStatus.FAILED


def test_workflow_refuses_to_treat_stale_snapshot_as_current(tmp_path):
    engine = SqliteReferenceWorkflowEngine(tmp_path / "workflow.sqlite3")
    engine.start_workflow(workflow_id="w", project_id="p", project_snapshot_id="s0")
    assert engine.check_snapshot_freshness("w", current_project_snapshot_id="s0") is WorkflowStatus.RUNNING
    assert engine.check_snapshot_freshness("w", current_project_snapshot_id="s1") is WorkflowStatus.CANNOT_CHECK


def test_history_tampering_is_detected(tmp_path):
    path = tmp_path / "workflow.sqlite3"
    engine = SqliteReferenceWorkflowEngine(path)
    engine.start_workflow(workflow_id="w", project_id="p", project_snapshot_id="s")
    engine.schedule_activity("w", spec())
    assert engine.verify_history("w")
    with sqlite3.connect(path) as db:
        db.execute(
            "UPDATE workflow_events SET payload_json=? WHERE workflow_id=? AND sequence=?",
            ('{"tampered":true}', "w", 1),
        )
    assert not engine.verify_history("w")


def test_expected_head_detects_valid_but_shortened_history(tmp_path):
    path = tmp_path / "workflow.sqlite3"
    engine = SqliteReferenceWorkflowEngine(path)
    engine.start_workflow(workflow_id="w", project_id="p", project_snapshot_id="s")
    engine.schedule_activity("w", spec())
    sealed_head = engine.workflow("w").head_event_hash
    engine.begin_activity("w", "a")
    later_head = engine.workflow("w").head_event_hash
    assert engine.verify_history("w", expected_head_hash=later_head)
    assert not engine.verify_history("w", expected_head_hash=sealed_head)


def test_integrated_workflow_rejects_unknown_or_cross_project_snapshot(tmp_path):
    from rakl.engineering_state import ProjectSnapshot
    from rakl.engineering_store import SqliteEngineeringStateStore
    path = tmp_path / "integrated.sqlite3"
    state = SqliteEngineeringStateStore(path)
    s = state.initialize_project(ProjectSnapshot(
        project_id="project:a", sequence=0, previous_snapshot_id=None,
        evidence_cutoff="e0", semantic_state_revision="s0", metric_ledger_head="m0",
        episode_store_head="ep0", saturation_basis_ids=("b",),
        authority_projection_revision="a0", controller_epoch_id="epoch",
        created_at_utc="2026-08-15T15:00:00+00:00",
    ))
    engine = SqliteReferenceWorkflowEngine(path)
    with pytest.raises(WorkflowIntegrityError, match="unknown project snapshot"):
        engine.start_workflow(
            workflow_id="wf:unknown", project_id="project:a",
            project_snapshot_id="snapshot:" + "f" * 64,
        )
    with pytest.raises(WorkflowIntegrityError, match="different project"):
        engine.start_workflow(
            workflow_id="wf:cross", project_id="project:b",
            project_snapshot_id=s.snapshot_id,
        )
