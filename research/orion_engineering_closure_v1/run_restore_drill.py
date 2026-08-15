"""E15 item 17: a REAL restore drill over the actual ORION stores.

The incumbent E15 evidence is ``take_backup``/``verify_restore`` proven on plain
files. That is a byte verifier, not the obligation. The obligation is:

    restore into a completely EMPTY environment and prove exact reconstruction
    of project snapshots, Atlas, evidence, metrics, saturation, episodes,
    decisions and workflow history.

So this drill populates the ACTUAL stores (no fixtures, no fakes), backs up the
store directory with the real backup primitives, restores into an empty
directory, and then proves reconstruction TWICE over:

    byte-wise      ``verify_restore`` against the content-addressed manifest
    semantically   re-open every store with its real class and compare plane
                   counts, record ids, revisions and the workflow event hash chain

Byte equality alone is not the proof asked for. A store whose bytes match but
reopens with a different logical state is a failure, and byte-level agreement is
not allowed to stand in for the semantic verdict — so both are recorded per
plane, separately.

CASES ARE FROZEN HERE BEFORE EXECUTION.

    D01 clean full restore              -> EXACT + every plane fingerprint EQUAL.
                                           This is the NO-ALARM CONTROL: if the
                                           legitimate restore is ever flagged,
                                           nothing else in this file means anything.
    D02 corrupted blob                  -> CORRUPTED_BLOB + dangling evidence payload
    D03 missing object-store data       -> MISSING_BLOB + dangling evidence payload
    D04 partial restore (atlas absent)  -> MISSING_BLOB byte-side, and the atlas
                                           plane must come back CANNOT_CHECK, never
                                           an empty-equals-empty pass
    D05 tampered manifest               -> MANIFEST_TAMPERED
    D06 restore to a FROZEN snapshot    -> head is the frozen snapshot, later
                                           records absent, workflow history verifies
                                           against the frozen sealed head and FAILS
                                           against the later one, so tail truncation
                                           is detectable rather than silently accepted
    D07 naive main-file-only copy       -> measured, not predicted: whether a copy
                                           that ignores WAL sidecars reconstructs
    D08 byte-clean, workflow tail cut    -> CHECKER VALIDATION. The manifest is
                                           re-derived from the mutated tree so byte
                                           verification is EXACT by construction; only
                                           the semantic re-open can catch it, and it
                                           must report exactly one DIVERGED plane
    D09 byte-clean, atlas row removed    -> CHECKER VALIDATION, as D08, on the atlas plane

WHAT THIS DRILL DOES NOT EXERCISE, stated exactly:
  * PostgreSQL WAL / point-in-time recovery. There is no PostgreSQL here. No PITR
    claim is made anywhere in this receipt.
  * Database failover, replica promotion, HA. Not exercised.
  * The incumbent RAKL MetricLedger and EpisodeStore as separate stores. In this
    engineering layer, metrics / saturation / hard gates / controller decisions /
    residual events are exercised as snapshot-bound ControlArtifactProjection
    records plus the heads carried in ProjectSnapshot. The incumbent stores
    themselves are not in this store directory.
  * Any production release artifact, object-store backend, or restore rehearsal
    on real infrastructure.
"""

from __future__ import annotations

import copy
import json
import shutil
import sqlite3
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, "src")

from rakl.engineering_atlas_store import (  # noqa: E402
    ATLAS_GENESIS_REVISION,
    AtlasChartRecord,
    AtlasObstructionRecord,
    AtlasPlaneBatch,
    AtlasTransitionRecord,
    SqliteAtlasPlaneStore,
)
from rakl.engineering_atomic import SqliteAtomicEngineeringCoordinator  # noqa: E402
from rakl.engineering_backup import (  # noqa: E402
    create_consistent_sqlite_copy,
    create_reference_backup,
    restore_reference_backup,
    verify_reference_backup,
)
from rakl.engineering_blob import LocalFilesystemBlobStore  # noqa: E402
from rakl.engineering_control_store import (  # noqa: E402
    ControlArtifactKind,
    ControlArtifactProjection,
    SqliteControlProjectionStore,
)
from rakl.engineering_evidence_store import EvidenceMutationBatch, EvidenceRecord  # noqa: E402
from rakl.engineering_ops import BackupManifest, RestoreVerdict, take_backup, verify_restore  # noqa: E402
from rakl.engineering_semantic_store import (  # noqa: E402
    RelationWitnessVersion,
    SemanticAtomVersion,
    SemanticFiber,
    SemanticMutationBatch,
    SqliteSemanticStateStore,
)
from rakl.engineering_state import (  # noqa: E402
    EpistemicAxisStatus,
    EpistemicStatus,
    NextActionClass,
    ProjectSnapshot,
    StateTransitionRequest,
)
from rakl.engineering_store import SqliteEngineeringStateStore  # noqa: E402
from rakl.engineering_workflow import ActivitySpec, SqliteReferenceWorkflowEngine  # noqa: E402

OUT = Path("research/orion_engineering_closure_v1/RESTORE_DRILL_V1.json")

PROJECT = "orion-restore-drill"
NOW = "2026-08-15T00:00:00+00:00"

ORION_DB = "orion.db"
ATLAS_DB = "atlas.db"
BLOB_DIR = "blobs"

CANNOT_CHECK = "CANNOT_CHECK"
RECONSTRUCTED = "RECONSTRUCTED"
EQUAL = "EQUAL"
DIVERGED = "DIVERGED"

PLANES = (
    "project_snapshots",
    "transition_decisions",
    "evidence",
    "semantic",
    "atlas",
    "control_metrics_saturation_gates_decisions_residuals",
    "epistemic_status",
    "workflow_history",
    "blobs",
)


@dataclass
class LiveState:
    """Identities the drill needs to interrogate a restored tree by name."""

    root: Path
    snapshot_ids: list[str] = field(default_factory=list)
    atlas_batch_ids: list[str] = field(default_factory=list)
    evidence_batch_ids: list[str] = field(default_factory=list)
    semantic_batch_ids: list[str] = field(default_factory=list)
    idempotency_keys: list[str] = field(default_factory=list)
    frozen_snapshot_id: str = ""
    frozen_wf1_head: str = ""
    current_wf1_head: str = ""
    current_wf2_head: str = ""


def _snapshot(seq: int, previous: str | None, **over: Any) -> ProjectSnapshot:
    base: dict[str, Any] = dict(
        project_id=PROJECT,
        sequence=seq,
        previous_snapshot_id=previous,
        evidence_cutoff="",
        semantic_state_revision="",
        metric_ledger_head="metric-ledger-head-0",
        episode_store_head="episode-store-head-0",
        saturation_basis_ids=("saturation-basis-0",),
        authority_projection_revision="authority-projection-0",
        controller_epoch_id="controller-epoch-0",
        created_at_utc=NOW,
    )
    base.update(over)
    return ProjectSnapshot(**base)


def _request(before: str, action: str, payload_hash: str, key: str) -> StateTransitionRequest:
    return StateTransitionRequest(
        project_id=PROJECT,
        before_snapshot_id=before,
        action=action,
        action_payload_hash=payload_hash,
        idempotency_key=key,
        process_identity="restore-drill",
        read_set=(),
        write_set=(),
        created_at_utc=NOW,
    )


# ---------------------------------------------------------------------------
# population — the ACTUAL stores, no fixtures.
# Split in two phases so the frozen backup is a genuine point-in-time image.
# ---------------------------------------------------------------------------


def populate_phase_one(root: Path) -> LiveState:
    """Everything up to the freeze point: s0..s2, atlas batch 1, wf-1 first activity."""

    root.mkdir(parents=True, exist_ok=True)
    orion = root / ORION_DB
    coordinator = SqliteAtomicEngineeringCoordinator(orion)
    blobs = LocalFilesystemBlobStore(root / BLOB_DIR)
    workflow = SqliteReferenceWorkflowEngine(orion)
    atlas = SqliteAtlasPlaneStore(root / ATLAS_DB)

    live = LiveState(root=root)

    s0 = _snapshot(
        0,
        None,
        evidence_cutoff=coordinator.evidence.evidence_revision(PROJECT, 0),
        semantic_state_revision=coordinator.semantic.semantic_revision(0),
    )
    coordinator.initialize_empty_project(s0)
    live.snapshot_ids.append(s0.snapshot_id)

    # s1 — evidence ingestion with real content-addressed blobs
    digests = [blobs.put_if_absent(f"drill evidence payload {i}".encode()) for i in range(3)]
    evidence_batch = EvidenceMutationBatch(
        project_id=PROJECT,
        sequence=1,
        base_evidence_revision=coordinator.evidence.evidence_revision(PROJECT, 0),
        records=tuple(
            EvidenceRecord(
                project_id=PROJECT,
                logical_record_id=f"ev-{i}",
                payload_sha256=digests[i],
                source_identity=f"source-{i}",
                source_version="v1",
                provenance_payload={"drill": True, "index": i},
                created_sequence=1,
            )
            for i in range(3)
        ),
    )
    s1 = _snapshot(
        1,
        s0.snapshot_id,
        evidence_cutoff=coordinator.evidence.preview_batch_revision(evidence_batch),
        semantic_state_revision=s0.semantic_state_revision,
    )
    coordinator.commit_evidence_transition(
        _request(
            s0.snapshot_id,
            "ingest_evidence",
            coordinator.evidence_action_payload_hash(evidence_batch),
            "drill-evidence-1",
        ),
        evidence_batch,
        s1,
        blob_store=blobs,
        created_at_utc=NOW,
    )
    live.snapshot_ids.append(s1.snapshot_id)
    live.evidence_batch_ids.append(evidence_batch.batch_id)
    live.idempotency_keys.append("drill-evidence-1")

    # s2 — semantic plane: fibers, atoms, a relation witness
    semantic_batch = SemanticMutationBatch(
        sequence=2,
        base_semantic_revision=coordinator.semantic.semantic_revision(1),
        new_fibers=(
            SemanticFiber("fiber-root", None, 2),
            SemanticFiber("fiber-child", "fiber-root", 2),
        ),
        atom_versions=tuple(
            SemanticAtomVersion(
                atom_id=f"atom-{i}",
                fiber_id="fiber-root" if i < 2 else "fiber-child",
                kind="MECHANISM",
                label=f"atom label {i}",
                evidence_ids=(f"ev-{i}",),
                payload={"drill": True, "index": i},
                valid_from_sequence=2,
            )
            for i in range(3)
        ),
        witness_versions=(
            RelationWitnessVersion(
                witness_id="witness-0",
                left_atom_id="atom-0",
                right_atom_id="atom-1",
                relation_type="SUPPORTS",
                reason="drill relation",
                condition=None,
                evidence_ids=("ev-0",),
                payload={"drill": True},
                valid_from_sequence=2,
            ),
        ),
    )
    s2 = _snapshot(
        2,
        s1.snapshot_id,
        evidence_cutoff=s1.evidence_cutoff,
        semantic_state_revision=coordinator.semantic.preview_batch_revision(semantic_batch),
    )
    coordinator.commit_semantic_transition(
        _request(
            s1.snapshot_id,
            "update_semantic_plane",
            coordinator.semantic_action_payload_hash(semantic_batch),
            "drill-semantic-2",
        ),
        semantic_batch,
        s2,
        created_at_utc=NOW,
    )
    live.snapshot_ids.append(s2.snapshot_id)
    live.semantic_batch_ids.append(semantic_batch.batch_id)
    live.idempotency_keys.append("drill-semantic-2")

    atlas_b1 = AtlasPlaneBatch(
        sequence=1,
        base_atlas_revision=ATLAS_GENESIS_REVISION,
        batch_id="atlas-batch-1",
        charts=(
            AtlasChartRecord("chart-a", "layer-0", ("x", "y")),
            AtlasChartRecord("chart-b", "layer-0", ("y", "z")),
        ),
        transitions=(AtlasTransitionRecord("transition-ab", "chart-a", "chart-b", "GLUED"),),
        obstructions=(AtlasObstructionRecord("obstruction-ab", "transition-ab", "COCYCLE"),),
    )
    atlas.commit_batch(atlas_b1, committed_snapshot_id=s2.snapshot_id, expected_atlas_revision="")
    live.atlas_batch_ids.append(atlas_b1.batch_id)

    # Control plane BEFORE the freeze, so the frozen-restore comparison is not a
    # vacuous empty-equals-empty pass on the control/epistemic planes.
    control = SqliteControlProjectionStore(orion)
    for kind, source in (
        (ControlArtifactKind.METRIC_RECEIPT, "metric-receipt-0"),
        (ControlArtifactKind.CONTROLLER_DECISION, "controller-decision-0"),
        (ControlArtifactKind.SATURATION_CERTIFICATE, "saturation-certificate-0"),
    ):
        control.record(
            ControlArtifactProjection(
                project_snapshot_id=s2.snapshot_id,
                kind=kind,
                source_object_id=source,
                canonical_payload={"drill": True, "source": source},
                source_receipt_ids=(f"receipt::{source}",),
            )
        )
    SqliteEngineeringStateStore(orion).record_epistemic_status(
        EpistemicStatus(
            project_snapshot_id=s2.snapshot_id,
            target_id="target-drill",
            fiber_id="fiber-drill",
            axis_statuses=(EpistemicAxisStatus("mechanism", False, 3, ("route-a",), ()),),
            required_routes=("route-a", "route-b"),
            covered_routes=("route-a",),
            missing_routes=("route-b",),
            active_residual_ids=(),
            freshness_stale=False,
            required_authority=1,
            available_support_paths=1,
            blocking_cut_ids=(),
            hard_gate_ids=("hard-gate-0",),
            next_action=NextActionClass.CONTINUE_SEARCH,
            reasons=("restore_drill_frozen_era_status",),
            metric_receipt_ids=("metric-receipt-0",),
            basis_fingerprints=("saturation-basis-0",),
        )
    )

    workflow.start_workflow(workflow_id="wf-1", project_id=PROJECT, project_snapshot_id=s2.snapshot_id)
    workflow.schedule_activity("wf-1", ActivitySpec("act-1", "inv-1", "digest-1", True, False))
    workflow.begin_activity("wf-1", "act-1")
    workflow.complete_activity("wf-1", "act-1", result_digest="result-1")

    live.frozen_snapshot_id = s2.snapshot_id
    live.frozen_wf1_head = workflow.workflow("wf-1").head_event_hash
    return live


def populate_phase_two(root: Path, live: LiveState) -> LiveState:
    """After the freeze: s3, atlas batch 2, control plane, epistemic status, workflows."""

    orion = root / ORION_DB
    coordinator = SqliteAtomicEngineeringCoordinator(orion)
    control = SqliteControlProjectionStore(orion)
    workflow = SqliteReferenceWorkflowEngine(orion)
    atlas = SqliteAtlasPlaneStore(root / ATLAS_DB)
    state_store = SqliteEngineeringStateStore(orion)

    s2 = state_store.head(PROJECT)
    head_atom_0 = coordinator.semantic.latest_atom_version("atom-0")
    assert head_atom_0 is not None

    semantic_batch_2 = SemanticMutationBatch(
        sequence=3,
        base_semantic_revision=coordinator.semantic.semantic_revision(2),
        new_fibers=(),
        atom_versions=(
            SemanticAtomVersion(
                atom_id="atom-0",
                fiber_id="fiber-root",
                kind="MECHANISM",
                label="atom label 0 (revised)",
                evidence_ids=("ev-0", "ev-1"),
                payload={"drill": True, "index": 0, "revision": 2},
                valid_from_sequence=3,
                supersedes_version_id=head_atom_0.version_id,
            ),
            SemanticAtomVersion(
                atom_id="atom-3",
                fiber_id="fiber-child",
                kind="OBSERVATION",
                label="atom label 3",
                evidence_ids=("ev-2",),
                payload={"drill": True, "index": 3},
                valid_from_sequence=3,
            ),
        ),
        witness_versions=(
            RelationWitnessVersion(
                witness_id="witness-1",
                left_atom_id="atom-1",
                right_atom_id="atom-2",
                relation_type="CONSTRAINS",
                reason="drill relation 2",
                condition="regime-A",
                evidence_ids=("ev-1",),
                payload={"drill": True},
                valid_from_sequence=3,
            ),
        ),
    )
    s3 = _snapshot(
        3,
        s2.snapshot_id,
        evidence_cutoff=s2.evidence_cutoff,
        semantic_state_revision=coordinator.semantic.preview_batch_revision(semantic_batch_2),
    )
    coordinator.commit_semantic_transition(
        _request(
            s2.snapshot_id,
            "update_semantic_plane",
            coordinator.semantic_action_payload_hash(semantic_batch_2),
            "drill-semantic-3",
        ),
        semantic_batch_2,
        s3,
        created_at_utc=NOW,
    )
    live.snapshot_ids.append(s3.snapshot_id)
    live.semantic_batch_ids.append(semantic_batch_2.batch_id)
    live.idempotency_keys.append("drill-semantic-3")

    atlas_b2 = AtlasPlaneBatch(
        sequence=2,
        base_atlas_revision=atlas.current_atlas_revision(),
        batch_id="atlas-batch-2",
        charts=(
            AtlasChartRecord("chart-c", "layer-1", ("z", "w")),
            AtlasChartRecord("chart-d", "layer-1", ("w", "v")),
        ),
        transitions=(AtlasTransitionRecord("transition-cd", "chart-c", "chart-d", "OBSTRUCTED"),),
        obstructions=(AtlasObstructionRecord("obstruction-cd", "transition-cd", "MONODROMY"),),
    )
    atlas.commit_batch(atlas_b2, committed_snapshot_id=s3.snapshot_id, expected_atlas_revision="")
    live.atlas_batch_ids.append(atlas_b2.batch_id)

    for kind, source in (
        (ControlArtifactKind.METRIC_RECEIPT, "metric-receipt-1"),
        (ControlArtifactKind.SATURATION_CERTIFICATE, "saturation-certificate-1"),
        (ControlArtifactKind.HARD_GATE, "hard-gate-1"),
        (ControlArtifactKind.CONTROLLER_DECISION, "controller-decision-1"),
        (ControlArtifactKind.RESIDUAL_EVENT, "residual-event-1"),
        (ControlArtifactKind.AUTHORITY_PROJECTION, "authority-projection-1"),
    ):
        control.record(
            ControlArtifactProjection(
                project_snapshot_id=s3.snapshot_id,
                kind=kind,
                source_object_id=source,
                canonical_payload={"drill": True, "source": source},
                source_receipt_ids=(f"receipt::{source}",),
            )
        )

    state_store.record_epistemic_status(
        EpistemicStatus(
            project_snapshot_id=s3.snapshot_id,
            target_id="target-drill",
            fiber_id="fiber-drill",
            axis_statuses=(
                EpistemicAxisStatus("mechanism", True, 0, ("route-a", "route-b"), ()),
                EpistemicAxisStatus("measurement", False, 2, ("route-a",), ()),
            ),
            required_routes=("route-a", "route-b"),
            covered_routes=("route-a",),
            missing_routes=("route-b",),
            active_residual_ids=("residual-event-1",),
            freshness_stale=False,
            required_authority=2,
            available_support_paths=1,
            blocking_cut_ids=(),
            hard_gate_ids=("hard-gate-1",),
            next_action=NextActionClass.CONTINUE_SEARCH,
            reasons=("restore_drill_fixture_status",),
            metric_receipt_ids=("metric-receipt-1",),
            basis_fingerprints=("saturation-basis-0",),
        )
    )

    workflow.schedule_activity("wf-1", ActivitySpec("act-2", "inv-2", "digest-2", True, False))
    workflow.begin_activity("wf-1", "act-2")
    workflow.complete_activity("wf-1", "act-2", result_digest="result-2")
    workflow.complete_workflow("wf-1")

    workflow.start_workflow(workflow_id="wf-2", project_id=PROJECT, project_snapshot_id=s3.snapshot_id)
    workflow.schedule_activity("wf-2", ActivitySpec("act-3", "inv-3", "digest-3", False, True))
    workflow.begin_activity("wf-2", "act-3")
    workflow.recover_ambiguous_activity("wf-2", "act-3")

    live.current_wf1_head = workflow.workflow("wf-1").head_event_hash
    live.current_wf2_head = workflow.workflow("wf-2").head_event_hash
    return live


# ---------------------------------------------------------------------------
# semantic fingerprint — re-open with the REAL classes
# ---------------------------------------------------------------------------


def _absent(reason: str) -> dict[str, Any]:
    """A plane that could not be checked. Deliberately NOT an empty success."""

    return {"status": CANNOT_CHECK, "reason": reason}


def logical_fingerprint(root: Path, live: LiveState) -> dict[str, Any]:
    """Re-open every store with its production class and project logical state.

    Every store constructor in this codebase creates its file and schema when
    absent, so instantiating a store on a missing database fabricates an EMPTY
    store whose fingerprint compares equal to any other empty one. Each plane is
    therefore gated on the file existing FIRST; a missing file yields
    CANNOT_CHECK and can never be reported as agreement.
    """

    orion = root / ORION_DB
    atlas_path = root / ATLAS_DB
    blob_root = root / BLOB_DIR
    fingerprint: dict[str, Any] = {}

    if not orion.is_file():
        reason = f"{ORION_DB} absent from restored tree"
        for plane in (
            "project_snapshots",
            "transition_decisions",
            "evidence",
            "semantic",
            "control_metrics_saturation_gates_decisions_residuals",
            "epistemic_status",
            "workflow_history",
        ):
            fingerprint[plane] = _absent(reason)
    else:
        state_store = SqliteEngineeringStateStore(orion)
        coordinator = SqliteAtomicEngineeringCoordinator(orion)
        control = SqliteControlProjectionStore(orion)
        workflow = SqliteReferenceWorkflowEngine(orion)
        semantic = SqliteSemanticStateStore(orion)

        head = state_store.head(PROJECT)
        snapshots = []
        for snapshot_id in live.snapshot_ids:
            try:
                snap = state_store.get_snapshot(snapshot_id)
            except KeyError:
                snapshots.append({"snapshot_id": snapshot_id, "present": False})
                continue
            snapshots.append(
                {
                    "snapshot_id": snap.snapshot_id,
                    "present": True,
                    "sequence": snap.sequence,
                    "previous_snapshot_id": snap.previous_snapshot_id,
                    "evidence_cutoff": snap.evidence_cutoff,
                    "semantic_state_revision": snap.semantic_state_revision,
                    "metric_ledger_head": snap.metric_ledger_head,
                    "episode_store_head": snap.episode_store_head,
                    "saturation_basis_ids": list(snap.saturation_basis_ids),
                    "authority_projection_revision": snap.authority_projection_revision,
                    "controller_epoch_id": snap.controller_epoch_id,
                }
            )
        fingerprint["project_snapshots"] = {
            "status": RECONSTRUCTED,
            "head_snapshot_id": head.snapshot_id,
            "head_sequence": head.sequence,
            "snapshots": snapshots,
        }

        receipts = []
        for key in live.idempotency_keys:
            receipt = state_store.transition_receipt(PROJECT, key)
            if receipt is None:
                receipts.append({"idempotency_key": key, "present": False})
            else:
                receipts.append(
                    {
                        "idempotency_key": key,
                        "present": True,
                        "transition_id": receipt.transition_id,
                        "status": receipt.status.value,
                        "action": receipt.action,
                        "action_payload_hash": receipt.action_payload_hash,
                        "after_snapshot_id": receipt.after_snapshot_id,
                        "produced_artifact_ids": list(receipt.produced_artifact_ids),
                    }
                )
        fingerprint["transition_decisions"] = {"status": RECONSTRUCTED, "receipts": receipts}

        evidence_records = coordinator.evidence.records_at(PROJECT, 99)
        evidence_commits = []
        for batch_id in live.evidence_batch_ids:
            commit = coordinator.evidence.batch_commit(batch_id)
            evidence_commits.append(
                {"batch_id": batch_id, "present": False}
                if commit is None
                else {
                    "batch_id": batch_id,
                    "present": True,
                    "committed_snapshot_id": commit.committed_snapshot_id,
                    "evidence_revision": commit.evidence_revision,
                }
            )
        fingerprint["evidence"] = {
            "status": RECONSTRUCTED,
            "count": len(evidence_records),
            "evidence_ids": [item.evidence_id for item in evidence_records],
            "payload_digests": [item.payload_sha256 for item in evidence_records],
            "evidence_revision": coordinator.evidence.evidence_revision(PROJECT, 99),
            "batch_commits": evidence_commits,
        }

        semantic_commits = []
        for batch_id in live.semantic_batch_ids:
            commit = coordinator.semantic.batch_commit(batch_id)
            semantic_commits.append(
                {"batch_id": batch_id, "present": False}
                if commit is None
                else {
                    "batch_id": batch_id,
                    "present": True,
                    "committed_snapshot_id": commit.committed_snapshot_id,
                    "semantic_revision": commit.semantic_revision,
                }
            )
        fingerprint["semantic"] = {
            "status": RECONSTRUCTED,
            "fibers": [item.to_dict() for item in semantic.fibers_at(99)],
            "atom_version_ids": [item.version_id for item in semantic.atom_versions_at(99)],
            "witness_version_ids": [item.version_id for item in semantic.witness_versions_at(99)],
            "semantic_revision": semantic.semantic_revision(99),
            "batch_commits": semantic_commits,
        }

        control_snapshot = live.snapshot_ids[-1]
        control_records = control.records(control_snapshot)
        fingerprint["control_metrics_saturation_gates_decisions_residuals"] = {
            "status": RECONSTRUCTED,
            "count": len(control_records),
            "record_ids": [item.record_id for item in control_records],
            "kinds": sorted(item.kind.value for item in control_records),
            "source_object_ids": sorted(item.source_object_id for item in control_records),
            "control_revision": control.control_revision(control_snapshot),
        }

        status = state_store.latest_epistemic_status(
            project_snapshot_id=control_snapshot,
            target_id="target-drill",
            fiber_id="fiber-drill",
        )
        fingerprint["epistemic_status"] = {
            "status": RECONSTRUCTED,
            "present": status is not None,
            "status_id": None if status is None else status.status_id,
            "next_action": None if status is None else status.next_action.value,
            "hard_gate_ids": None if status is None else list(status.hard_gate_ids),
        }

        history: dict[str, Any] = {"status": RECONSTRUCTED}
        for workflow_id, sealed in (
            ("wf-1", live.current_wf1_head),
            ("wf-2", live.current_wf2_head),
        ):
            try:
                record_ = workflow.workflow(workflow_id)
            except KeyError:
                history[workflow_id] = {"present": False}
                continue
            events = workflow.events(workflow_id)
            history[workflow_id] = {
                "present": True,
                "status": record_.status.value,
                "project_snapshot_id": record_.project_snapshot_id,
                "head_event_hash": record_.head_event_hash,
                "event_count": len(events),
                "event_kinds": [event.kind for event in events],
                "event_hashes": [event.event_hash for event in events],
                "chain_valid": workflow.verify_history(workflow_id),
                "chain_valid_vs_sealed_current_head": (
                    workflow.verify_history(workflow_id, expected_head_hash=sealed)
                    if sealed
                    else None
                ),
            }
        fingerprint["workflow_history"] = history

    if not atlas_path.is_file():
        fingerprint["atlas"] = _absent(f"{ATLAS_DB} absent from restored tree")
    else:
        atlas = SqliteAtlasPlaneStore(atlas_path)
        commits = []
        for batch_id in live.atlas_batch_ids:
            commit = atlas.batch_commit(batch_id)
            commits.append(
                {"batch_id": batch_id, "present": False}
                if commit is None
                else {
                    "batch_id": batch_id,
                    "present": True,
                    "atlas_revision": commit.atlas_revision,
                    "committed_snapshot_id": commit.committed_snapshot_id,
                    "chart_count": commit.chart_count,
                    "transition_count": commit.transition_count,
                    "obstruction_count": commit.obstruction_count,
                }
            )
        fingerprint["atlas"] = {
            "status": RECONSTRUCTED,
            "plane_counts": atlas.plane_counts(),
            "current_sequence": atlas.current_sequence(),
            "current_atlas_revision": atlas.current_atlas_revision(),
            "batch_commits": commits,
        }

    if not blob_root.is_dir():
        fingerprint["blobs"] = _absent(f"{BLOB_DIR}/ absent from restored tree")
    else:
        blobs = LocalFilesystemBlobStore(blob_root)
        stored = sorted(p.name for p in blob_root.rglob("*") if p.is_file())
        dangling: list[str] = []
        if orion.is_file():
            evidence_store = SqliteAtomicEngineeringCoordinator(orion).evidence
            for record_ in evidence_store.records_at(PROJECT, 99):
                if not blobs.exists_verified(record_.payload_sha256):
                    dangling.append(f"{record_.logical_record_id}->{record_.payload_sha256}")
        else:
            dangling = [CANNOT_CHECK]
        fingerprint["blobs"] = {
            "status": RECONSTRUCTED,
            "stored_digests": stored,
            "dangling_evidence_payloads": dangling,
        }

    return fingerprint


def compare_planes(reference: dict[str, Any], restored: dict[str, Any]) -> dict[str, str]:
    """Per-plane verdict. CANNOT_CHECK on either side never becomes EQUAL."""

    verdicts: dict[str, str] = {}
    for plane in PLANES:
        left = reference.get(plane)
        right = restored.get(plane)
        if left is None or right is None:
            verdicts[plane] = CANNOT_CHECK
        elif left.get("status") == CANNOT_CHECK or right.get("status") == CANNOT_CHECK:
            verdicts[plane] = CANNOT_CHECK
        elif left == right:
            verdicts[plane] = EQUAL
        else:
            verdicts[plane] = DIVERGED
    return verdicts


# ---------------------------------------------------------------------------
# backup / restore mechanics using the real primitives
# ---------------------------------------------------------------------------


def stage_consistent_copy(live_root: Path, staging: Path) -> None:
    """Stage a transactionally consistent copy of every store.

    ``create_consistent_sqlite_copy`` is the reference primitive precisely because
    copying a live WAL-mode database file byte-wise can omit committed pages.
    """

    staging.mkdir(parents=True, exist_ok=True)
    create_consistent_sqlite_copy(live_root / ORION_DB, staging / ORION_DB)
    create_consistent_sqlite_copy(live_root / ATLAS_DB, staging / ATLAS_DB)
    shutil.copytree(live_root / BLOB_DIR, staging / BLOB_DIR)


def _inputs_for(staging: Path) -> dict[str, Path]:
    return {
        path.relative_to(staging).as_posix(): path
        for path in sorted(staging.rglob("*"))
        if path.is_file()
    }


def make_backup(
    live_root: Path, work: Path, name: str, snapshot_id: str
) -> tuple[Path, BackupManifest]:
    staging = work / f"staging-{name}"
    stage_consistent_copy(live_root, staging)
    ops_manifest = take_backup(staging, backup_id=f"backup-{name}", created_at=NOW)
    archive = work / f"{name}.zip"
    create_reference_backup(
        archive,
        project_snapshot_id=snapshot_id,
        created_at_utc=NOW,
        inputs=_inputs_for(staging),
    )
    return archive, ops_manifest


def fresh_restore(archive: Path, work: Path, name: str) -> Path:
    """Restore into a genuinely EMPTY directory (the primitive refuses otherwise)."""

    destination = work / f"restored-{name}"
    if destination.exists():
        shutil.rmtree(destination)
    restore_reference_backup(archive, destination)
    return destination


# ---------------------------------------------------------------------------
# execution
# ---------------------------------------------------------------------------


def run_drill(work: Path) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    def record(case_id: str, name: str, outcome: str, detail: str, **extra: Any) -> None:
        cases.append({"case": case_id, "name": name, "outcome": outcome, "detail": detail, **extra})
        print(f"  {outcome:<14} {case_id} {name:<44} {detail}")

    live_root = work / "live"
    live = populate_phase_one(live_root)
    frozen_archive, _frozen_ops = make_backup(live_root, work, "frozen", live.frozen_snapshot_id)
    # The frozen reference and the frozen restore must be interrogated with the SAME
    # identity set, otherwise the comparison is asking two different questions.
    frozen_live = copy.deepcopy(live)
    frozen_live.current_wf1_head = live.frozen_wf1_head
    frozen_reference = logical_fingerprint(live_root, frozen_live)

    populate_phase_two(live_root, live)
    current_archive, current_ops = make_backup(live_root, work, "current", live.snapshot_ids[-1])
    current_reference = logical_fingerprint(live_root, live)

    # --- D01 clean full restore (NO-ALARM CONTROL) --------------------------
    restored = fresh_restore(current_archive, work, "d01")
    byte_verdict, offenders = verify_restore(restored, current_ops)
    archive_check = verify_reference_backup(current_archive)
    restored_fingerprint = logical_fingerprint(restored, live)
    d01_planes = compare_planes(current_reference, restored_fingerprint)
    clean_ok = (
        byte_verdict is RestoreVerdict.EXACT
        and archive_check.valid
        and all(v == EQUAL for v in d01_planes.values())
    )
    record(
        "D01",
        "clean full restore into empty env",
        "HELD" if clean_ok else "BROKE",
        f"byte={byte_verdict.value} archive={archive_check.verdict.value} "
        f"planes_equal={sum(1 for v in d01_planes.values() if v == EQUAL)}/{len(d01_planes)}",
        plane_verdicts=d01_planes,
        byte_verdict=byte_verdict.value,
        byte_offenders=list(offenders),
    )

    # --- D02 corrupted blob --------------------------------------------------
    restored = fresh_restore(current_archive, work, "d02")
    blob_files = sorted(p for p in (restored / BLOB_DIR).rglob("*") if p.is_file())
    blob_files[0].write_bytes(b"corrupted-by-drill")
    byte_verdict, offenders = verify_restore(restored, current_ops)
    fingerprint = logical_fingerprint(restored, live)
    dangling = fingerprint["blobs"]["dangling_evidence_payloads"]
    held = byte_verdict is RestoreVerdict.CORRUPTED_BLOB and len(dangling) == 1
    record(
        "D02",
        "corrupted blob in restored tree",
        "HELD" if held else "BROKE",
        f"byte={byte_verdict.value} offenders={list(offenders)} dangling={dangling}",
        byte_verdict=byte_verdict.value,
        dangling_evidence_payloads=dangling,
    )

    # --- D03 missing object-store data ---------------------------------------
    restored = fresh_restore(current_archive, work, "d03")
    blob_files = sorted(p for p in (restored / BLOB_DIR).rglob("*") if p.is_file())
    blob_files[0].unlink()
    byte_verdict, offenders = verify_restore(restored, current_ops)
    fingerprint = logical_fingerprint(restored, live)
    dangling = fingerprint["blobs"]["dangling_evidence_payloads"]
    held = byte_verdict is RestoreVerdict.MISSING_BLOB and len(dangling) == 1
    record(
        "D03",
        "missing object-store payload",
        "HELD" if held else "BROKE",
        f"byte={byte_verdict.value} offenders={list(offenders)} dangling={dangling}",
        byte_verdict=byte_verdict.value,
        dangling_evidence_payloads=dangling,
    )

    # --- D04 partial restore -------------------------------------------------
    restored = fresh_restore(current_archive, work, "d04")
    (restored / ATLAS_DB).unlink()
    byte_verdict, offenders = verify_restore(restored, current_ops)
    fingerprint = logical_fingerprint(restored, live)
    d04_planes = compare_planes(current_reference, fingerprint)
    held = (
        byte_verdict is RestoreVerdict.MISSING_BLOB
        and fingerprint["atlas"]["status"] == CANNOT_CHECK
        and d04_planes["atlas"] == CANNOT_CHECK
        and d04_planes["semantic"] == EQUAL
        and d04_planes["evidence"] == EQUAL
        and d04_planes["workflow_history"] == EQUAL
        and d04_planes["project_snapshots"] == EQUAL
        and not (restored / ATLAS_DB).exists()
    )
    record(
        "D04",
        "partial restore, atlas plane absent",
        "HELD" if held else "BROKE",
        f"byte={byte_verdict.value} atlas={d04_planes['atlas']} "
        f"atlas_db_recreated_by_probe={(restored / ATLAS_DB).exists()} planes={d04_planes}",
        plane_verdicts=d04_planes,
        byte_verdict=byte_verdict.value,
    )

    # --- D05 tampered manifest -----------------------------------------------
    restored = fresh_restore(current_archive, work, "d05")
    tampered = copy.copy(current_ops)
    entries = dict(current_ops.entries)
    entries[sorted(entries)[0]] = "0" * 64
    object.__setattr__(tampered, "entries", entries)
    byte_verdict, _ = verify_restore(restored, tampered)
    record(
        "D05",
        "manifest tampered after signing",
        "HELD" if byte_verdict is RestoreVerdict.MANIFEST_TAMPERED else "BROKE",
        f"byte={byte_verdict.value}",
        byte_verdict=byte_verdict.value,
    )

    # --- D06 restore to a FROZEN snapshot -------------------------------------
    restored = fresh_restore(frozen_archive, work, "d06")
    fingerprint = logical_fingerprint(restored, frozen_live)
    frozen_planes = compare_planes(frozen_reference, fingerprint)
    state_store = SqliteEngineeringStateStore(restored / ORION_DB)
    head = state_store.head(PROJECT)
    later_control = SqliteControlProjectionStore(restored / ORION_DB).records(live.snapshot_ids[-1])
    try:
        state_store.get_snapshot(live.snapshot_ids[-1])
        later_snapshot_present = True
    except KeyError:
        later_snapshot_present = False
    later_atlas_present = (
        SqliteAtlasPlaneStore(restored / ATLAS_DB).batch_commit("atlas-batch-2") is not None
    )
    engine = SqliteReferenceWorkflowEngine(restored / ORION_DB)
    verifies_vs_frozen = engine.verify_history("wf-1", expected_head_hash=live.frozen_wf1_head)
    verifies_vs_later = engine.verify_history("wf-1", expected_head_hash=live.current_wf1_head)
    try:
        engine.workflow("wf-2")
        wf2_present = True
    except KeyError:
        wf2_present = False
    held = (
        head.snapshot_id == live.frozen_snapshot_id
        and not later_snapshot_present
        and not later_atlas_present
        and not later_control
        and not wf2_present
        and verifies_vs_frozen
        and not verifies_vs_later
        and all(v == EQUAL for v in frozen_planes.values())
    )
    record(
        "D06",
        "restore to frozen snapshot",
        "HELD" if held else "BROKE",
        (
            f"head_is_frozen={head.snapshot_id == live.frozen_snapshot_id} "
            f"later_snapshot_present={later_snapshot_present} "
            f"later_atlas_present={later_atlas_present} "
            f"later_control_records={len(later_control)} wf2_present={wf2_present} "
            f"chain_vs_frozen_sealed_head={verifies_vs_frozen} "
            f"chain_vs_later_sealed_head={verifies_vs_later} planes={frozen_planes}"
        ),
        plane_verdicts=frozen_planes,
    )

    # --- D07 naive main-file-only copy (measured, not predicted) --------------
    wal_sidecars = sorted(p.name for p in live_root.glob("*-wal")) + sorted(
        p.name for p in live_root.glob("*-shm")
    )
    naive = work / "naive"
    naive.mkdir()
    shutil.copy2(live_root / ORION_DB, naive / ORION_DB)
    shutil.copy2(live_root / ATLAS_DB, naive / ATLAS_DB)
    shutil.copytree(live_root / BLOB_DIR, naive / BLOB_DIR)
    if not wal_sidecars:
        record(
            "D07",
            "main-file-only copy ignoring WAL sidecars",
            "NOT_EXERCISED",
            "no -wal/-shm sidecar existed at copy time, so this copy could not have "
            "lost committed pages and the case proves nothing either way. The reason is "
            "a property of these stores, not an omission: every store closes its "
            "connection at the end of each transaction, so SQLite checkpoints the WAL "
            "back into the main database and removes the sidecars. A backend that holds "
            "connections open would leave a live WAL and this case would then bite",
            wal_sidecars=wal_sidecars,
        )
        naive_planes: dict[str, str] = {}
    else:
        naive_fingerprint = logical_fingerprint(naive, live)
        naive_planes = compare_planes(current_reference, naive_fingerprint)
        lossy = any(v != EQUAL for v in naive_planes.values())
        record(
            "D07",
            "main-file-only copy ignoring WAL sidecars",
            "HELD" if lossy else "BROKE",
            f"wal_sidecars={wal_sidecars} planes={naive_planes} — "
            + (
                "naive copy demonstrably lossy; the consistent-copy primitive is required"
                if lossy
                else "naive copy reproduced logical state even with live WAL sidecars present"
            ),
            wal_sidecars=wal_sidecars,
            plane_verdicts=naive_planes,
        )

    # --- D08/D09 CHECKER VALIDATION -----------------------------------------
    # A comparison that can only ever emit EQUAL proves nothing. These two cases
    # mutate a restored tree's LOGICAL state and then re-derive the byte manifest
    # from the mutated tree, so byte verification is EXACT by construction. Only
    # the semantic re-open can catch them. If either came back EQUAL, the whole
    # semantic half of this drill would be decorative.
    restored = fresh_restore(current_archive, work, "d08")
    db = sqlite3.connect(restored / ORION_DB)
    try:
        db.execute(
            "DELETE FROM workflow_events WHERE workflow_id='wf-1' AND sequence="
            "(SELECT MAX(sequence) FROM workflow_events WHERE workflow_id='wf-1')"
        )
        db.commit()
    finally:
        db.close()
    self_manifest = take_backup(restored, backup_id="backup-d08-self", created_at=NOW)
    byte_verdict, _ = verify_restore(restored, self_manifest)
    fingerprint = logical_fingerprint(restored, live)
    d08_planes = compare_planes(current_reference, fingerprint)
    held = (
        byte_verdict is RestoreVerdict.EXACT
        and d08_planes["workflow_history"] == DIVERGED
        and fingerprint["workflow_history"]["wf-1"]["chain_valid_vs_sealed_current_head"] is False
        and all(v == EQUAL for k, v in d08_planes.items() if k != "workflow_history")
    )
    record(
        "D08",
        "byte-clean tree, workflow tail truncated",
        "HELD" if held else "BROKE",
        f"byte={byte_verdict.value} (self-derived manifest) planes={d08_planes} "
        f"chain_valid={fingerprint['workflow_history']['wf-1']['chain_valid']}",
        plane_verdicts=d08_planes,
        byte_verdict=byte_verdict.value,
    )

    restored = fresh_restore(current_archive, work, "d09")
    db = sqlite3.connect(restored / ATLAS_DB)
    try:
        db.execute("DELETE FROM atlas_charts WHERE chart_id='chart-d'")
        db.commit()
    finally:
        db.close()
    self_manifest = take_backup(restored, backup_id="backup-d09-self", created_at=NOW)
    byte_verdict, _ = verify_restore(restored, self_manifest)
    fingerprint = logical_fingerprint(restored, live)
    d09_planes = compare_planes(current_reference, fingerprint)
    held = (
        byte_verdict is RestoreVerdict.EXACT
        and d09_planes["atlas"] == DIVERGED
        and all(v == EQUAL for k, v in d09_planes.items() if k != "atlas")
    )
    record(
        "D09",
        "byte-clean tree, atlas chart row removed",
        "HELD" if held else "BROKE",
        f"byte={byte_verdict.value} (self-derived manifest) planes={d09_planes} "
        f"plane_counts={fingerprint['atlas']['plane_counts']}",
        plane_verdicts=d09_planes,
        byte_verdict=byte_verdict.value,
    )

    return {
        "cases": cases,
        "clean_restore_plane_verdicts": d01_planes,
        "frozen_restore_plane_verdicts": frozen_planes,
        "partial_restore_plane_verdicts": d04_planes,
        "live_identities": {
            "project_id": PROJECT,
            "snapshot_ids": live.snapshot_ids,
            "frozen_snapshot_id": live.frozen_snapshot_id,
            "atlas_batch_ids": live.atlas_batch_ids,
            "evidence_batch_ids": live.evidence_batch_ids,
            "semantic_batch_ids": live.semantic_batch_ids,
            "sealed_workflow_heads": {
                "wf-1@frozen": live.frozen_wf1_head,
                "wf-1@current": live.current_wf1_head,
                "wf-2@current": live.current_wf2_head,
            },
        },
    }


def main() -> int:
    work = Path(tempfile.mkdtemp(prefix="orion-restore-drill-"))
    try:
        print("=" * 90)
        print("RESTORE DRILL V1 — real ORION stores, empty-environment restore")
        print("=" * 90)
        result = run_drill(work)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    cases = result["cases"]
    held = sum(1 for c in cases if c["outcome"] == "HELD")
    broke = sum(1 for c in cases if c["outcome"] == "BROKE")
    other = len(cases) - held - broke
    print("=" * 90)
    print(f"held {held}/{len(cases)}   broke {broke}   non-terminal {other}")

    plane_coverage = {
        "project_snapshots": "EXERCISED_reconstructed_and_compared",
        "transition_decisions": "EXERCISED_reconstructed_and_compared",
        "evidence": "EXERCISED_reconstructed_and_compared",
        "semantic": "EXERCISED_reconstructed_and_compared",
        "atlas": "EXERCISED_reconstructed_and_compared",
        "control_metrics_saturation_gates_decisions_residuals": (
            "EXERCISED_as_snapshot_bound_ControlArtifactProjection_records_only"
        ),
        "epistemic_status": "EXERCISED_reconstructed_and_compared",
        "workflow_history": "EXERCISED_hash_chain_and_sealed_head_verified",
        "blobs": "EXERCISED_content_addressed_bytes_and_dangling_pointer_check",
        "incumbent_MetricLedger_store": "NOT_EXERCISED_not_present_in_this_store_directory",
        "incumbent_EpisodeStore_store": "NOT_EXERCISED_not_present_in_this_store_directory",
        "postgresql_wal_pitr": "NOT_EXERCISED_no_postgresql_present",
        "database_failover_ha": "NOT_EXERCISED_no_replicated_database_present",
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "schema_version": "orion-restore-drill-v1",
                "fiber_id": "E15",
                "obligation": (
                    "restore into a completely empty environment and prove exact "
                    "reconstruction of project snapshots, Atlas, evidence, metrics, "
                    "saturation, episodes, decisions and workflow history"
                ),
                "status": "FROZEN_CASES_EXECUTED__ALL_OUTCOMES_PRESERVED",
                "grants_scientific_authority": False,
                "cases_frozen_before_execution": True,
                "proof_mode": "byte_manifest_AND_independent_semantic_reopen",
                "held": held,
                "broke": broke,
                "non_terminal": other,
                "total": len(cases),
                "plane_coverage": plane_coverage,
                "clean_restore_plane_verdicts": result["clean_restore_plane_verdicts"],
                "frozen_restore_plane_verdicts": result["frozen_restore_plane_verdicts"],
                "partial_restore_plane_verdicts": result["partial_restore_plane_verdicts"],
                "live_identities": result["live_identities"],
                "cases": cases,
                "not_claimed": [
                    "PostgreSQL WAL or point-in-time recovery of any kind",
                    "database failover, replica promotion or HA behaviour",
                    "a restore rehearsal on production infrastructure or a real object store",
                    "reconstruction of the incumbent RAKL MetricLedger or EpisodeStore, "
                    "which are separate stores not present in this store directory",
                    "that byte equality alone establishes logical reconstruction, or the converse",
                ],
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(f"wrote {OUT}")
    return 0 if broke == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
