import json
from pathlib import Path

import jsonschema

from rakl.engineering_state import (
    EpistemicAxisStatus,
    EpistemicStatus,
    NextActionClass,
    ProjectSnapshot,
    StateTransitionReceipt,
    StateTransitionRequest,
    TransitionStatus,
)


ROOT = Path(__file__).resolve().parents[1]
T0 = "2026-08-15T14:00:00+00:00"


def load_schema(name):
    return json.loads((ROOT / "schemas" / name).read_text("utf-8"))


def make_snapshot():
    return ProjectSnapshot(
        project_id="project:demo",
        sequence=0,
        previous_snapshot_id=None,
        evidence_cutoff="evidence:0",
        semantic_state_revision="semantic:0",
        metric_ledger_head="metric:0",
        episode_store_head="episode:0",
        saturation_basis_ids=("basis:0",),
        authority_projection_revision="authority:0",
        controller_epoch_id="epoch:0",
        created_at_utc=T0,
    )


def test_snapshot_schema_accepts_reference_contract():
    jsonschema.Draft202012Validator(load_schema("project_snapshot.schema.json")).validate(make_snapshot().to_dict())


def test_epistemic_status_schema_accepts_reference_contract():
    s = make_snapshot()
    status = EpistemicStatus(
        project_snapshot_id=s.snapshot_id,
        target_id="target:qoi",
        fiber_id="fiber:knowledge",
        axis_statuses=(EpistemicAxisStatus("KNOWLEDGE", True, 0, ("R1", "R2")),),
        required_routes=("R1", "R2"),
        covered_routes=("R1", "R2"),
        missing_routes=(),
        active_residual_ids=(),
        freshness_stale=False,
        required_authority=1,
        available_support_paths=1,
        blocking_cut_ids=(),
        hard_gate_ids=("bounded_saturation_gate",),
        next_action=NextActionClass.PROCEED_OBJECT_WORK,
        reasons=("bounded_knowledge_saturation_established",),
        metric_receipt_ids=("metric:1",),
        basis_fingerprints=("basis:fingerprint",),
    )
    jsonschema.Draft202012Validator(load_schema("epistemic_status.schema.json")).validate(status.to_dict())


def test_transition_schema_enforces_committed_after_snapshot():
    s = make_snapshot()
    req = StateTransitionRequest(
        project_id="project:demo",
        before_snapshot_id=s.snapshot_id,
        action="UPDATE_ATLAS",
        action_payload_hash="b" * 64,
        idempotency_key="idem:1",
        process_identity="worker:1",
        read_set=("semantic",),
        write_set=("semantic",),
        created_at_utc=T0,
    )
    receipt = StateTransitionReceipt(
        project_id=req.project_id,
        before_snapshot_id=req.before_snapshot_id,
        after_snapshot_id="snapshot:" + "a" * 64,
        action=req.action,
        action_payload_hash="b" * 64,
        idempotency_key=req.idempotency_key,
        request_hash=req.request_hash,
        process_identity=req.process_identity,
        read_set=req.read_set,
        write_set=req.write_set,
        produced_artifact_ids=(),
        metric_receipt_ids=(),
        residual_ids=(),
        status=TransitionStatus.COMMITTED,
        reasons=("committed",),
        created_at_utc=T0,
    )
    jsonschema.Draft202012Validator(load_schema("state_transition_receipt.schema.json")).validate(receipt.to_dict())


def test_extended_engineering_contract_schemas_accept_reference_objects(tmp_path):
    from hashlib import sha256
    from rakl.engineering_backup import create_reference_backup
    from rakl.engineering_deployment import DeploymentMode, EngineeringSupportProfile
    from rakl.engineering_integration import SnapshotBoundSolverView
    from rakl.engineering_migration import compare_migration_parity, build_import_receipt
    from rakl.engineering_release import RuntimeArtifactIdentity

    snapshot = make_snapshot()
    solver_view = SnapshotBoundSolverView(
        project_snapshot_id=snapshot.snapshot_id,
        problem_id="problem:1", target_id="target:1", support_structure_id="support:1",
        compiler_identity="compiler:v1", required_authority=1, atom_ids=("a", "b"),
    )
    jsonschema.Draft202012Validator(load_schema("solver_view.schema.json")).validate(solver_view.to_dict())

    parity = compare_migration_parity({"a": 1}, {"a": 1})
    receipt = build_import_receipt(
        import_id="import:1", project_id="project:demo", source_store_kind="JSONL",
        source_store_identity="file:episodes.jsonl", source_head_hash="head:1",
        target_backend_identity="postgres:test", imported_object_ids=("episode:1",),
        parity_report=parity, created_at_utc=T0,
    )
    jsonschema.Draft202012Validator(load_schema("import_receipt.schema.json")).validate(receipt.to_dict())

    profile = EngineeringSupportProfile(
        profile_id="profile:prod", mode=DeploymentMode.MULTI_HOST, max_concurrent_workers=4,
        requires_shared_blob_store=True, requires_serializable_metadata=True,
        requires_durable_workflow_history=True, requires_point_in_time_recovery=True,
        requires_authz=True, requires_build_attestation=True,
        external_effect_classes=("MODEL_PROVIDER",),
    )
    jsonschema.Draft202012Validator(load_schema("engineering_support_profile.schema.json")).validate(profile.to_dict())

    payload = b"artifact"
    identity = RuntimeArtifactIdentity(
        artifact_name="orion-worker", artifact_sha256=sha256(payload).hexdigest(),
        source_revision="git:abc", builder_id="builder:ci", build_type="python-wheel",
        provenance_id="slsa:1", image_digest="sha256:" + "b" * 64,
    )
    jsonschema.Draft202012Validator(load_schema("runtime_artifact_identity.schema.json")).validate(identity.to_dict())

    source = tmp_path / "state.bin"; source.write_bytes(b"state")
    backup = create_reference_backup(
        tmp_path / "backup.zip", project_snapshot_id=snapshot.snapshot_id,
        created_at_utc=T0, inputs={"state.bin": source},
    )
    jsonschema.Draft202012Validator(load_schema("backup_manifest.schema.json")).validate(backup.to_dict())
