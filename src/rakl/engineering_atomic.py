"""Atomic semantic-state + ProjectSnapshot transition for the SQLite reference backend.

This is the reference proof that semantic revision, project head and transition receipt
can commit as one metadata transaction.  The production analogue should provide the
same observable semantics with a serializable transactional store or an equivalently
strong demonstrated protocol.

Blob writes may precede this transaction because content-addressed orphan blobs are
safe to retain/collect. External side effects are never folded into this transaction;
the workflow/recovery layer owns their ambiguity.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import json
from pathlib import Path
import sqlite3
from typing import Iterator, Tuple

from .engineering_evidence_store import (
    EvidenceBatchCommit,
    EvidenceMutationBatch,
    SqliteEvidenceMetadataStore,
)
from .engineering_semantic_store import (
    SemanticBatchCommit,
    SemanticMutationBatch,
    SqliteSemanticStateStore,
)
from .engineering_state import (
    ProjectSnapshot,
    StateTransitionReceipt,
    StateTransitionRequest,
    TransitionStatus,
    canonical_sha256,
)
from .engineering_store import (
    BlobStore,
    EngineeringIntegrityError,
    IdempotencyConflict,
    ProjectNotInitialized,
    SqliteEngineeringStateStore,
)


@dataclass(frozen=True)
class AtomicSemanticTransitionResult:
    transition_receipt: StateTransitionReceipt
    semantic_commit: SemanticBatchCommit | None


@dataclass(frozen=True)
class AtomicEvidenceTransitionResult:
    transition_receipt: StateTransitionReceipt
    evidence_commit: EvidenceBatchCommit | None


class SqliteAtomicEngineeringCoordinator:
    """Single-file/single-transaction reference coordinator."""

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        # Both schemas live in the SAME SQLite database file.
        self.state = SqliteEngineeringStateStore(path)
        self.semantic = SqliteSemanticStateStore(path)
        self.evidence = SqliteEvidenceMetadataStore(path)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10.0, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=10000")
        return db

    @contextmanager
    def _tx(self) -> Iterator[sqlite3.Connection]:
        db = self._connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.execute("COMMIT")
        except Exception:
            try:
                db.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            db.close()

    def initialize_empty_project(self, snapshot: ProjectSnapshot) -> ProjectSnapshot:
        """Initialize a project only when snapshot semantic head matches empty store."""
        if snapshot.sequence != 0:
            raise ValueError("initial reference project must start at sequence 0")
        expected = self.semantic.semantic_revision(0)
        if snapshot.semantic_state_revision != expected:
            raise EngineeringIntegrityError(
                "initial snapshot semantic revision does not match empty semantic store"
            )
        expected_evidence = self.evidence.evidence_revision(snapshot.project_id, 0)
        if snapshot.evidence_cutoff != expected_evidence:
            raise EngineeringIntegrityError(
                "initial snapshot evidence cutoff does not match empty evidence store"
            )
        return self.state.initialize_project(snapshot)

    @staticmethod
    def semantic_action_payload_hash(batch: SemanticMutationBatch) -> str:
        return canonical_sha256({"semantic_batch_id": batch.batch_id})

    @staticmethod
    def evidence_action_payload_hash(batch: EvidenceMutationBatch) -> str:
        return canonical_sha256({"evidence_batch_id": batch.batch_id})

    def commit_evidence_transition(
        self,
        request: StateTransitionRequest,
        batch: EvidenceMutationBatch,
        after_snapshot: ProjectSnapshot,
        *,
        blob_store: BlobStore,
        produced_artifact_ids: Tuple[str, ...] = (),
        created_at_utc: str,
    ) -> AtomicEvidenceTransitionResult:
        if request.project_id != batch.project_id or request.project_id != after_snapshot.project_id:
            raise ValueError("request, evidence batch and after snapshot project differ")
        if batch.sequence != after_snapshot.sequence:
            raise ValueError("evidence batch sequence must equal after snapshot sequence")
        if request.action_payload_hash != self.evidence_action_payload_hash(batch):
            raise EngineeringIntegrityError(
                "transition action payload hash does not bind evidence mutation batch"
            )
        # Content-addressed bytes are placed/verified before the metadata transaction.
        # An orphan blob after a crash is harmless; committed metadata pointing at a
        # missing/unverified blob is forbidden.
        for record in batch.records:
            if not blob_store.exists_verified(record.payload_sha256):
                raise EngineeringIntegrityError(
                    f"evidence payload unavailable or corrupt:{record.payload_sha256}"
                )

        with self._tx() as db:
            replay = db.execute(
                "SELECT request_hash,payload_json FROM transitions WHERE project_id=? AND idempotency_key=?",
                (request.project_id, request.idempotency_key),
            ).fetchone()
            if replay is not None:
                if replay["request_hash"] != request.request_hash:
                    raise IdempotencyConflict(
                        "idempotency key already bound to a different transition request"
                    )
                receipt = StateTransitionReceipt.from_dict(json.loads(replay["payload_json"]))
                evidence_commit = None
                if receipt.status is TransitionStatus.COMMITTED:
                    row = db.execute(
                        """SELECT committed_snapshot_id,evidence_revision
                           FROM engineering_evidence_batch_commits WHERE batch_id=?""",
                        (batch.batch_id,),
                    ).fetchone()
                    if row is None or row["committed_snapshot_id"] != receipt.after_snapshot_id:
                        raise EngineeringIntegrityError(
                            "committed transition missing matching evidence batch commit"
                        )
                    evidence_commit = EvidenceBatchCommit(
                        batch.batch_id, row["committed_snapshot_id"], row["evidence_revision"]
                    )
                return AtomicEvidenceTransitionResult(receipt, evidence_commit)

            before_row = db.execute(
                "SELECT project_id,payload_json FROM snapshots WHERE snapshot_id=?",
                (request.before_snapshot_id,),
            ).fetchone()
            if before_row is None:
                raise KeyError(request.before_snapshot_id)
            if before_row["project_id"] != request.project_id:
                raise EngineeringIntegrityError("transition snapshot belongs to a different project")
            before_snapshot = ProjectSnapshot.from_dict(json.loads(before_row["payload_json"]))
            head = db.execute(
                "SELECT snapshot_id,sequence FROM project_heads WHERE project_id=?",
                (request.project_id,),
            ).fetchone()
            if head is None:
                raise ProjectNotInitialized(request.project_id)
            if head["snapshot_id"] != request.before_snapshot_id:
                receipt = StateTransitionReceipt(
                    project_id=request.project_id, before_snapshot_id=request.before_snapshot_id,
                    after_snapshot_id=None, action=request.action,
                    action_payload_hash=request.action_payload_hash, idempotency_key=request.idempotency_key,
                    request_hash=request.request_hash, process_identity=request.process_identity,
                    read_set=request.read_set, write_set=request.write_set, produced_artifact_ids=(),
                    metric_receipt_ids=(), residual_ids=(), status=TransitionStatus.RETRY_REQUIRED,
                    reasons=("stale_before_snapshot_replan_on_current_head",),
                    created_at_utc=created_at_utc,
                )
                db.execute(
                    "INSERT INTO transitions VALUES(?,?,?,?,?,?,?,?)",
                    (receipt.transition_id, receipt.project_id, receipt.idempotency_key,
                     receipt.request_hash, receipt.before_snapshot_id, None, receipt.status.value,
                     self.state._dump(receipt.to_dict())),
                )
                return AtomicEvidenceTransitionResult(receipt, None)

            if after_snapshot.previous_snapshot_id != request.before_snapshot_id:
                raise ValueError("after snapshot must point to request before snapshot")
            if after_snapshot.sequence != int(head["sequence"]) + 1:
                raise ValueError("after snapshot sequence must advance exactly once")
            # A raw evidence ingestion transition changes only the evidence head.
            invariant_fields = (
                "semantic_state_revision", "metric_ledger_head", "episode_store_head",
                "saturation_basis_ids", "authority_projection_revision", "controller_epoch_id",
            )
            for field in invariant_fields:
                if getattr(after_snapshot, field) != getattr(before_snapshot, field):
                    raise EngineeringIntegrityError(
                        f"pure evidence ingest unexpectedly changes {field}"
                    )
            preview = self.evidence._preview_batch_revision_db(db, batch)
            if after_snapshot.evidence_cutoff != preview:
                raise EngineeringIntegrityError(
                    "after snapshot evidence cutoff does not equal batch preview"
                )
            evidence_commit = self.evidence._commit_batch_db(
                db, batch, committed_snapshot_id=after_snapshot.snapshot_id,
                expected_evidence_revision=preview,
            )
            db.execute(
                "INSERT INTO snapshots(snapshot_id,project_id,sequence,previous_snapshot_id,payload_json) VALUES(?,?,?,?,?)",
                (after_snapshot.snapshot_id, after_snapshot.project_id, after_snapshot.sequence,
                 after_snapshot.previous_snapshot_id, self.state._dump(after_snapshot.to_dict())),
            )
            db.execute(
                "UPDATE project_heads SET snapshot_id=?,sequence=? WHERE project_id=?",
                (after_snapshot.snapshot_id, after_snapshot.sequence, after_snapshot.project_id),
            )
            receipt = StateTransitionReceipt(
                project_id=request.project_id, before_snapshot_id=request.before_snapshot_id,
                after_snapshot_id=after_snapshot.snapshot_id, action=request.action,
                action_payload_hash=request.action_payload_hash, idempotency_key=request.idempotency_key,
                request_hash=request.request_hash, process_identity=request.process_identity,
                read_set=request.read_set, write_set=request.write_set,
                produced_artifact_ids=produced_artifact_ids + tuple(r.evidence_id for r in batch.records),
                metric_receipt_ids=(), residual_ids=(), status=TransitionStatus.COMMITTED,
                reasons=("evidence_metadata_and_project_snapshot_committed_atomically",),
                created_at_utc=created_at_utc,
            )
            db.execute(
                "INSERT INTO transitions VALUES(?,?,?,?,?,?,?,?)",
                (receipt.transition_id, receipt.project_id, receipt.idempotency_key,
                 receipt.request_hash, receipt.before_snapshot_id, receipt.after_snapshot_id,
                 receipt.status.value, self.state._dump(receipt.to_dict())),
            )
            return AtomicEvidenceTransitionResult(receipt, evidence_commit)

    def commit_semantic_transition(
        self,
        request: StateTransitionRequest,
        batch: SemanticMutationBatch,
        after_snapshot: ProjectSnapshot,
        *,
        produced_artifact_ids: Tuple[str, ...] = (),
        metric_receipt_ids: Tuple[str, ...] = (),
        residual_ids: Tuple[str, ...] = (),
        created_at_utc: str,
    ) -> AtomicSemanticTransitionResult:
        if request.project_id != after_snapshot.project_id:
            raise ValueError("request and after snapshot project differ")
        if batch.sequence != after_snapshot.sequence:
            raise ValueError("semantic batch sequence must equal after snapshot sequence")
        expected_action_hash = self.semantic_action_payload_hash(batch)
        if request.action_payload_hash != expected_action_hash:
            raise EngineeringIntegrityError(
                "transition action payload hash does not bind the semantic mutation batch"
            )

        with self._tx() as db:
            replay = db.execute(
                "SELECT request_hash,payload_json FROM transitions WHERE project_id=? AND idempotency_key=?",
                (request.project_id, request.idempotency_key),
            ).fetchone()
            if replay is not None:
                if replay["request_hash"] != request.request_hash:
                    raise IdempotencyConflict(
                        "idempotency key already bound to a different transition request"
                    )
                receipt = StateTransitionReceipt.from_dict(json.loads(replay["payload_json"]))
                semantic_commit = None
                if receipt.status is TransitionStatus.COMMITTED:
                    row = db.execute(
                        "SELECT committed_snapshot_id,semantic_revision FROM semantic_batch_commits WHERE batch_id=?",
                        (batch.batch_id,),
                    ).fetchone()
                    if row is None:
                        raise EngineeringIntegrityError(
                            "committed transition exists without semantic batch commit"
                        )
                    if row["committed_snapshot_id"] != receipt.after_snapshot_id:
                        raise EngineeringIntegrityError(
                            "semantic batch commit snapshot disagrees with transition receipt"
                        )
                    semantic_commit = SemanticBatchCommit(
                        batch.batch_id,
                        row["committed_snapshot_id"],
                        row["semantic_revision"],
                    )
                return AtomicSemanticTransitionResult(receipt, semantic_commit)

            before = db.execute(
                "SELECT project_id,payload_json FROM snapshots WHERE snapshot_id=?",
                (request.before_snapshot_id,),
            ).fetchone()
            if before is None:
                raise KeyError(request.before_snapshot_id)
            if before["project_id"] != request.project_id:
                raise EngineeringIntegrityError(
                    "transition snapshot belongs to a different project"
                )
            before_snapshot = ProjectSnapshot.from_dict(json.loads(before["payload_json"]))
            head = db.execute(
                "SELECT snapshot_id,sequence FROM project_heads WHERE project_id=?",
                (request.project_id,),
            ).fetchone()
            if head is None:
                raise ProjectNotInitialized(request.project_id)

            if head["snapshot_id"] != request.before_snapshot_id:
                receipt = StateTransitionReceipt(
                    project_id=request.project_id,
                    before_snapshot_id=request.before_snapshot_id,
                    after_snapshot_id=None,
                    action=request.action,
                    action_payload_hash=request.action_payload_hash,
                    idempotency_key=request.idempotency_key,
                    request_hash=request.request_hash,
                    process_identity=request.process_identity,
                    read_set=request.read_set,
                    write_set=request.write_set,
                    produced_artifact_ids=(),
                    metric_receipt_ids=(),
                    residual_ids=(),
                    status=TransitionStatus.RETRY_REQUIRED,
                    reasons=("stale_before_snapshot_replan_on_current_head",),
                    created_at_utc=created_at_utc,
                )
                db.execute(
                    "INSERT INTO transitions VALUES(?,?,?,?,?,?,?,?)",
                    (
                        receipt.transition_id,
                        receipt.project_id,
                        receipt.idempotency_key,
                        receipt.request_hash,
                        receipt.before_snapshot_id,
                        None,
                        receipt.status.value,
                        self.state._dump(receipt.to_dict()),
                    ),
                )
                return AtomicSemanticTransitionResult(receipt, None)

            if after_snapshot.previous_snapshot_id != request.before_snapshot_id:
                raise ValueError("after snapshot must point to request before snapshot")
            if after_snapshot.sequence != int(head["sequence"]) + 1:
                raise ValueError("after snapshot sequence must advance exactly once")
            # The semantic action payload binds only the semantic mutation batch. It
            # must not smuggle unrelated head changes through the same idempotency
            # identity. Composite multi-plane transitions need their own payload.
            invariant_fields = (
                "evidence_cutoff", "metric_ledger_head", "episode_store_head",
                "saturation_basis_ids", "authority_projection_revision", "controller_epoch_id",
            )
            for field in invariant_fields:
                if getattr(after_snapshot, field) != getattr(before_snapshot, field):
                    raise EngineeringIntegrityError(
                        f"pure semantic update unexpectedly changes {field}"
                    )

            preview = self.semantic._preview_batch_revision_db(db, batch)
            if after_snapshot.semantic_state_revision != preview:
                raise EngineeringIntegrityError(
                    "after snapshot semantic revision does not equal batch preview"
                )

            semantic_commit = self.semantic._commit_batch_db(
                db,
                batch,
                committed_snapshot_id=after_snapshot.snapshot_id,
                expected_semantic_revision=preview,
            )
            db.execute(
                "INSERT INTO snapshots(snapshot_id,project_id,sequence,previous_snapshot_id,payload_json) VALUES(?,?,?,?,?)",
                (
                    after_snapshot.snapshot_id,
                    after_snapshot.project_id,
                    after_snapshot.sequence,
                    after_snapshot.previous_snapshot_id,
                    self.state._dump(after_snapshot.to_dict()),
                ),
            )
            db.execute(
                "UPDATE project_heads SET snapshot_id=?,sequence=? WHERE project_id=?",
                (after_snapshot.snapshot_id, after_snapshot.sequence, after_snapshot.project_id),
            )
            receipt = StateTransitionReceipt(
                project_id=request.project_id,
                before_snapshot_id=request.before_snapshot_id,
                after_snapshot_id=after_snapshot.snapshot_id,
                action=request.action,
                action_payload_hash=request.action_payload_hash,
                idempotency_key=request.idempotency_key,
                request_hash=request.request_hash,
                process_identity=request.process_identity,
                read_set=request.read_set,
                write_set=request.write_set,
                produced_artifact_ids=produced_artifact_ids,
                metric_receipt_ids=metric_receipt_ids,
                residual_ids=residual_ids,
                status=TransitionStatus.COMMITTED,
                reasons=("semantic_batch_and_project_snapshot_committed_atomically",),
                created_at_utc=created_at_utc,
            )
            db.execute(
                "INSERT INTO transitions VALUES(?,?,?,?,?,?,?,?)",
                (
                    receipt.transition_id,
                    receipt.project_id,
                    receipt.idempotency_key,
                    receipt.request_hash,
                    receipt.before_snapshot_id,
                    receipt.after_snapshot_id,
                    receipt.status.value,
                    self.state._dump(receipt.to_dict()),
                ),
            )
            return AtomicSemanticTransitionResult(receipt, semantic_commit)
