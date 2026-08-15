from pathlib import Path

from rakl.engineering_atomic import SqliteAtomicEngineeringCoordinator
from rakl.engineering_backup import create_consistent_sqlite_copy, create_reference_backup, restore_reference_backup
from rakl.engineering_blob import LocalFilesystemBlobStore
from rakl.engineering_control_store import ControlArtifactKind, ControlArtifactProjection, SqliteControlProjectionStore
from rakl.engineering_evidence_store import EvidenceMutationBatch, EvidenceRecord
from rakl.engineering_index import RebuildableSemanticIndex
from rakl.engineering_semantic_store import SemanticAtomVersion, SemanticFiber, SemanticMutationBatch
from rakl.engineering_state import (
    EpistemicAxisStatus, EpistemicStatus, NextActionClass, ProjectSnapshot,
    StateTransitionRequest, TransitionStatus,
)
from rakl.engineering_workflow import ActivitySpec, SqliteReferenceWorkflowEngine, WorkflowStatus

T0="2026-08-15T16:00:00+00:00"; T1="2026-08-15T16:01:00+00:00"; T2="2026-08-15T16:02:00+00:00"


def test_reference_clean_install_restart_restore_reconstruct(tmp_path):
    project = tmp_path / "project"; project.mkdir()
    db_path = project / "orion.sqlite3"
    blob_root = project / "blobs"
    blobs = LocalFilesystemBlobStore(blob_root)

    coordinator = SqliteAtomicEngineeringCoordinator(db_path)
    project_id="project:e2e"
    s0 = ProjectSnapshot(
        project_id=project_id, sequence=0, previous_snapshot_id=None,
        evidence_cutoff=coordinator.evidence.evidence_revision(project_id,0),
        semantic_state_revision=coordinator.semantic.semantic_revision(0),
        metric_ledger_head="metric:0", episode_store_head="episode:0",
        saturation_basis_ids=("basis:knowledge:v1",), authority_projection_revision="authority:0",
        controller_epoch_id="epoch:0", created_at_utc=T0,
    )
    coordinator.initialize_empty_project(s0)

    # EVIDENCE PLANE: exact bytes first, then metadata + project head atomically.
    evidence_digest = blobs.put_if_absent(b"source evidence bytes")
    evidence_record = EvidenceRecord(
        project_id, "source:demo", evidence_digest, "source:demo", "v1",
        {"kind":"SOURCE_PROJECTION"}, 1,
    )
    evidence_batch = EvidenceMutationBatch(
        project_id, 1, coordinator.evidence.evidence_revision(project_id,0), (evidence_record,)
    )
    evidence_revision = coordinator.evidence.preview_batch_revision(evidence_batch)
    s1 = ProjectSnapshot(
        project_id=project_id, sequence=1, previous_snapshot_id=s0.snapshot_id,
        evidence_cutoff=evidence_revision, semantic_state_revision=s0.semantic_state_revision,
        metric_ledger_head=s0.metric_ledger_head, episode_store_head=s0.episode_store_head,
        saturation_basis_ids=s0.saturation_basis_ids, authority_projection_revision=s0.authority_projection_revision,
        controller_epoch_id=s0.controller_epoch_id, created_at_utc=T1,
    )
    evidence_request = StateTransitionRequest(
        project_id=project_id, before_snapshot_id=s0.snapshot_id, action="INGEST_EVIDENCE",
        action_payload_hash=coordinator.evidence_action_payload_hash(evidence_batch),
        idempotency_key="e2e:evidence:1", process_identity="worker:reference",
        read_set=("evidence",), write_set=("evidence",), created_at_utc=T1,
    )
    evidence_transition=coordinator.commit_evidence_transition(
        evidence_request,evidence_batch,s1,blob_store=blobs,created_at_utc=T1
    )
    assert evidence_transition.transition_receipt.status is TransitionStatus.COMMITTED

    # SEMANTIC PLANE: structural extraction uses the exact evidence identity but may
    # change only the semantic head under this action payload.
    batch = SemanticMutationBatch(
        sequence=2,
        base_semantic_revision=coordinator.semantic.semantic_revision(1),
        new_fibers=(SemanticFiber("fiber:mechanism", created_from_sequence=2),),
        atom_versions=(SemanticAtomVersion(
            atom_id="atom:memory", fiber_id="fiber:mechanism", kind="MECHANISM_NODE",
            label="memory kernel", evidence_ids=(evidence_record.evidence_id,),
            payload={"source_sha256": evidence_digest}, valid_from_sequence=2,
        ),),
    )
    preview = coordinator.semantic.preview_batch_revision(batch)
    s2 = ProjectSnapshot(
        project_id=project_id, sequence=2, previous_snapshot_id=s1.snapshot_id,
        evidence_cutoff=s1.evidence_cutoff, semantic_state_revision=preview,
        metric_ledger_head=s1.metric_ledger_head, episode_store_head=s1.episode_store_head,
        saturation_basis_ids=s1.saturation_basis_ids, authority_projection_revision=s1.authority_projection_revision,
        controller_epoch_id=s1.controller_epoch_id, created_at_utc=T2,
    )
    request = StateTransitionRequest(
        project_id=project_id, before_snapshot_id=s1.snapshot_id,
        action="UPDATE_SEMANTIC_ATLAS",
        action_payload_hash=coordinator.semantic_action_payload_hash(batch),
        idempotency_key="e2e:semantic:2", process_identity="worker:reference",
        read_set=("semantic",), write_set=("semantic",), created_at_utc=T2,
    )
    transition = coordinator.commit_semantic_transition(request, batch, s2, created_at_utc=T2)
    assert transition.transition_receipt.status is TransitionStatus.COMMITTED

    status = EpistemicStatus(
        project_snapshot_id=s2.snapshot_id, target_id="target:demo", fiber_id="fiber:mechanism",
        axis_statuses=(EpistemicAxisStatus("KNOWLEDGE", True, 0, ("FOUNDATIONAL", "ALIEN")),),
        required_routes=("FOUNDATIONAL", "ALIEN"), covered_routes=("FOUNDATIONAL", "ALIEN"),
        missing_routes=(), active_residual_ids=(), freshness_stale=False,
        required_authority=0, available_support_paths=1, blocking_cut_ids=(),
        hard_gate_ids=("bounded_saturation_gate",), next_action=NextActionClass.COMPILE_SOLVER_VIEW,
        reasons=("reference_known_world_flat",), metric_receipt_ids=("metric:sat:1",),
        basis_fingerprints=("basis:fingerprint:1",),
    )
    coordinator.state.record_epistemic_status(status)
    controls = SqliteControlProjectionStore(db_path)
    controls.record(ControlArtifactProjection(
        project_snapshot_id=s2.snapshot_id, kind=ControlArtifactKind.SATURATION_CERTIFICATE,
        source_object_id="sat:1", canonical_payload=status.to_dict(), source_receipt_ids=("metric:sat:1",),
    ))

    index = RebuildableSemanticIndex(); index_snapshot = index.rebuild(coordinator.semantic, sequence=2)
    assert index.lexical("memory")[0].atom_id == "atom:memory"

    workflow = SqliteReferenceWorkflowEngine(db_path)
    workflow.start_workflow(workflow_id="wf:e2e", project_id=project_id, project_snapshot_id=s2.snapshot_id)
    workflow.schedule_activity("wf:e2e", ActivitySpec(
        activity_id="compile", invocation_id="invoke:compile", input_digest=status.status_id,
        retry_safe=True, external_effect=False,
    ))
    workflow.begin_activity("wf:e2e", "compile")
    workflow.complete_activity("wf:e2e", "compile", result_digest=index_snapshot.index_id)
    workflow.complete_workflow("wf:e2e")
    sealed_workflow_head = workflow.workflow("wf:e2e").head_event_hash
    assert workflow.verify_history("wf:e2e", expected_head_hash=sealed_workflow_head)

    backup_path = tmp_path / "e2e-backup.zip"
    stable_db = tmp_path / "orion-consistent.sqlite3"
    create_consistent_sqlite_copy(db_path, stable_db)
    manifest = create_reference_backup(
        backup_path, project_snapshot_id=s2.snapshot_id, created_at_utc=T2,
        inputs={"metadata/orion.sqlite3": stable_db, "blobs": blob_root},
    )
    restored_root = tmp_path / "restored"
    restored = restore_reference_backup(backup_path, restored_root)
    assert restored.backup_id == manifest.backup_id

    restored_db = restored_root / "metadata/orion.sqlite3"
    reopened = SqliteAtomicEngineeringCoordinator(restored_db)
    assert reopened.state.head(project_id) == s2
    assert reopened.evidence.evidence_revision(project_id,2) == s2.evidence_cutoff
    assert reopened.evidence.records_at(project_id,2) == (evidence_record,)
    assert reopened.semantic.semantic_revision(2) == s2.semantic_state_revision
    assert reopened.state.latest_epistemic_status(
        project_snapshot_id=s2.snapshot_id, target_id="target:demo", fiber_id="fiber:mechanism"
    ) == status
    restored_controls = SqliteControlProjectionStore(restored_db)
    assert restored_controls.records(s2.snapshot_id)[0].source_object_id == "sat:1"
    restored_workflow = SqliteReferenceWorkflowEngine(restored_db)
    assert restored_workflow.workflow("wf:e2e").status is WorkflowStatus.COMPLETED
    assert restored_workflow.verify_history("wf:e2e", expected_head_hash=sealed_workflow_head)
    restored_blobs = LocalFilesystemBlobStore(restored_root / "blobs")
    assert restored_blobs.get_verified(evidence_digest) == b"source evidence bytes"
