import pytest

from rakl.engineering_atomic import SqliteAtomicEngineeringCoordinator
from rakl.engineering_blob import LocalFilesystemBlobStore
from rakl.engineering_evidence_store import EvidenceMutationBatch, EvidenceRecord, SqliteEvidenceMetadataStore
from rakl.engineering_state import ProjectSnapshot, StateTransitionRequest, TransitionStatus
from rakl.engineering_store import EngineeringIntegrityError

T0="2026-08-15T17:20:00+00:00"; T1="2026-08-15T17:21:00+00:00"


def initial(c):
    return ProjectSnapshot(
        project_id="p", sequence=0, previous_snapshot_id=None,
        evidence_cutoff=c.evidence.evidence_revision("p",0),
        semantic_state_revision=c.semantic.semantic_revision(0), metric_ledger_head="m0",
        episode_store_head="ep0", saturation_basis_ids=("b",), authority_projection_revision="a0",
        controller_epoch_id="epoch", created_at_utc=T0,
    )


def test_evidence_metadata_and_snapshot_commit_after_verified_blob(tmp_path):
    c=SqliteAtomicEngineeringCoordinator(tmp_path/"state.sqlite3")
    blobs=LocalFilesystemBlobStore(tmp_path/"blobs")
    s0=c.initialize_empty_project(initial(c)); digest=blobs.put_if_absent(b"paper bytes")
    record=EvidenceRecord("p","source:1",digest,"doi:1","v1",{"route":"FOUNDATIONAL"},1)
    batch=EvidenceMutationBatch("p",1,c.evidence.evidence_revision("p",0),(record,))
    preview=c.evidence.preview_batch_revision(batch)
    s1=ProjectSnapshot(
        project_id="p",sequence=1,previous_snapshot_id=s0.snapshot_id,evidence_cutoff=preview,
        semantic_state_revision=s0.semantic_state_revision,metric_ledger_head=s0.metric_ledger_head,
        episode_store_head=s0.episode_store_head,saturation_basis_ids=s0.saturation_basis_ids,
        authority_projection_revision=s0.authority_projection_revision,
        controller_epoch_id=s0.controller_epoch_id,created_at_utc=T1,
    )
    req=StateTransitionRequest(
        project_id="p",before_snapshot_id=s0.snapshot_id,action="INGEST_EVIDENCE",
        action_payload_hash=c.evidence_action_payload_hash(batch),idempotency_key="ingest:1",
        process_identity="worker",read_set=("evidence",),write_set=("evidence",),created_at_utc=T1,
    )
    result=c.commit_evidence_transition(req,batch,s1,blob_store=blobs,created_at_utc=T1)
    assert result.transition_receipt.status is TransitionStatus.COMMITTED
    assert c.state.head("p") == s1
    assert c.evidence.evidence_revision("p",1) == preview
    assert c.evidence.records_at("p",1) == (record,)
    assert c.commit_evidence_transition(req,batch,s1,blob_store=blobs,created_at_utc=T1) == result


def test_evidence_metadata_never_commits_if_blob_missing_or_corrupt(tmp_path):
    path=tmp_path/"state.sqlite3"; c=SqliteAtomicEngineeringCoordinator(path)
    blobs=LocalFilesystemBlobStore(tmp_path/"blobs"); s0=c.initialize_empty_project(initial(c))
    record=EvidenceRecord("p","source:1","f"*64,"doi:1",None,{},1)
    batch=EvidenceMutationBatch("p",1,c.evidence.evidence_revision("p",0),(record,))
    preview=c.evidence.preview_batch_revision(batch)
    s1=ProjectSnapshot(
        project_id="p",sequence=1,previous_snapshot_id=s0.snapshot_id,evidence_cutoff=preview,
        semantic_state_revision=s0.semantic_state_revision,metric_ledger_head=s0.metric_ledger_head,
        episode_store_head=s0.episode_store_head,saturation_basis_ids=s0.saturation_basis_ids,
        authority_projection_revision=s0.authority_projection_revision,controller_epoch_id=s0.controller_epoch_id,
        created_at_utc=T1,
    )
    req=StateTransitionRequest(
        project_id="p",before_snapshot_id=s0.snapshot_id,action="INGEST_EVIDENCE",
        action_payload_hash=c.evidence_action_payload_hash(batch),idempotency_key="ingest:missing",
        process_identity="worker",read_set=("evidence",),write_set=("evidence",),created_at_utc=T1,
    )
    with pytest.raises(EngineeringIntegrityError,match="unavailable or corrupt"):
        c.commit_evidence_transition(req,batch,s1,blob_store=blobs,created_at_utc=T1)
    assert c.state.head("p") == s0
    assert c.evidence.records_at("p",1) == ()


def test_orphan_content_blob_is_safe_when_metadata_transition_never_commits(tmp_path):
    c=SqliteAtomicEngineeringCoordinator(tmp_path/"state.sqlite3"); blobs=LocalFilesystemBlobStore(tmp_path/"blobs")
    s0=c.initialize_empty_project(initial(c)); digest=blobs.put_if_absent(b"orphan-safe")
    assert blobs.exists_verified(digest)
    assert c.evidence.records_at("p",0) == ()
    assert c.state.head("p") == s0


def test_logical_record_id_rebinding_fails_preview(tmp_path):
    store=SqliteEvidenceMetadataStore(tmp_path/"evidence.sqlite3")
    base=store.evidence_revision("p",0)
    r1=EvidenceRecord("p","logical", "a"*64,"source:a",None,{},1)
    b1=EvidenceMutationBatch("p",1,base,(r1,)); rev=store.preview_batch_revision(b1)
    with store._tx() as db:
        store._commit_batch_db(db,b1,committed_snapshot_id="snapshot:"+"a"*64,expected_evidence_revision=rev)
    r2=EvidenceRecord("p","logical", "b"*64,"source:b",None,{},2)
    b2=EvidenceMutationBatch("p",2,rev,(r2,))
    with pytest.raises(EngineeringIntegrityError,match="cannot be rebound"):
        store.preview_batch_revision(b2)
