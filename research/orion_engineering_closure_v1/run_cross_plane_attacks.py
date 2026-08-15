"""E18 item 23: cross-plane atomicity attacks.

The claim under attack, stated so it can fail:

    the evidence, semantic, Atlas and control heads cannot be changed by an
    action whose payload hash does not bind those effects.

CASES ARE FROZEN HERE BEFORE EXECUTION. Every outcome is preserved, including —
especially — the ones that BROKE.

    X01 legitimate evidence transition        NO-ALARM CONTROL: must COMMIT unflagged
    X02 legitimate semantic transition        NO-ALARM CONTROL: must COMMIT unflagged
    X03 legitimate atlas plane batch          NO-ALARM CONTROL: must COMMIT unflagged
    X04 payload binds semantic batch,         effect touches the EVIDENCE plane
        after-snapshot moves evidence_cutoff
    X05 payload binds evidence batch,         effect touches the SEMANTIC plane
        after-snapshot moves semantic rev
    X06 payload binds a DIFFERENT semantic batch than the one being committed
    X07 cross-plane payload-hash confusion:   an atlas payload hash offered to the
                                              evidence commit path
    X08 CONTROL-HEAD ADVANCE WITH NO PAYLOAD BINDING, through the reference
        service facade — the headline case
    X08b the same attack through the atomic coordinator (the contrast that makes
        X08 a defect rather than a layering choice)
    X09 injected fault mid-transaction: evidence rows written, snapshot write
        fails -> BOTH planes must roll back
    X10 atlas batch half-write (obstruction id collision) -> whole plane rolls back
    X11 atlas revision advanced under a STALE expected/base revision
    X12 atlas sequence rewind (a sequence already committed)
    X13 replayed cross-plane batch: same atlas batch id, different content
    X14 replayed semantic batch id with different content
    X15 replayed idempotency key with a different request
    X16 atlas batch naming a project snapshot that does not exist
    X17 control projection naming a project snapshot that does not exist

Outcomes: HELD / BROKE / CANNOT_CHECK / CONFIRMS_KNOWN_OPEN.
CONFIRMS_KNOWN_OPEN is reserved for behaviour already recorded as open in this
packet; it is not counted as a break and it is not counted as a pass.

NOT claimed: an independently executed pass on a production release; distributed
exactly-once across external effects; any PostgreSQL/serializable backend result.
"""

from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, "src")

from rakl.engineering_api import EngineeringServiceFacade  # noqa: E402
from rakl.engineering_atlas_store import (  # noqa: E402
    AtlasChartRecord,
    AtlasObstructionRecord,
    AtlasPlaneBatch,
    AtlasTransitionRecord,
    SqliteAtlasPlaneStore,
    atlas_action_payload_hash,
    atlas_revision_for,
)
from rakl.engineering_atomic import SqliteAtomicEngineeringCoordinator  # noqa: E402
from rakl.engineering_blob import LocalFilesystemBlobStore  # noqa: E402
from rakl.engineering_control_store import (  # noqa: E402
    ControlArtifactKind,
    ControlArtifactProjection,
    SqliteControlProjectionStore,
)
from rakl.engineering_evidence_store import EvidenceMutationBatch, EvidenceRecord  # noqa: E402
from rakl.engineering_semantic_store import (  # noqa: E402
    RelationWitnessVersion,
    SemanticAtomVersion,
    SemanticFiber,
    SemanticMutationBatch,
)
from rakl.engineering_state import (  # noqa: E402
    ProjectSnapshot,
    StateTransitionRequest,
    TransitionStatus,
    canonical_sha256,
)
from rakl.engineering_store import SqliteEngineeringStateStore  # noqa: E402

OUT = Path("research/orion_engineering_closure_v1/CROSS_PLANE_ATTACKS_V1.json")

PROJECT = "orion-cross-plane"
NOW = "2026-08-15T00:00:00+00:00"

HELD = "HELD"
BROKE = "BROKE"
CANNOT_CHECK = "CANNOT_CHECK"
KNOWN_OPEN = "CONFIRMS_KNOWN_OPEN"

RESULTS: list[dict[str, Any]] = []


def case(case_id: str, name: str, fn: Callable[[], tuple[str, str]], **extra: Any) -> None:
    try:
        outcome, detail = fn()
    except Exception as exc:  # noqa: BLE001 — an attack that crashed the harness did not check
        outcome, detail = CANNOT_CHECK, f"harness raised {type(exc).__name__}: {exc}"
    RESULTS.append({"case": case_id, "name": name, "outcome": outcome, "detail": detail, **extra})
    print(f"  {outcome:<20} {case_id:<5} {name:<50} {detail}")


# ---------------------------------------------------------------------------
# fixture: a real project with a real evidence blob available
# ---------------------------------------------------------------------------


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
        process_identity="cross-plane-attacker",
        read_set=(),
        write_set=(),
        created_at_utc=NOW,
    )


class Fixture:
    """A freshly initialised project on real stores."""

    def __init__(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        self.root = root
        self.db = root / "orion.db"
        self.coordinator = SqliteAtomicEngineeringCoordinator(self.db)
        self.blobs = LocalFilesystemBlobStore(root / "blobs")
        self.s0 = _snapshot(
            0,
            None,
            evidence_cutoff=self.coordinator.evidence.evidence_revision(PROJECT, 0),
            semantic_state_revision=self.coordinator.semantic.semantic_revision(0),
        )
        self.coordinator.initialize_empty_project(self.s0)
        self.digest = self.blobs.put_if_absent(b"cross plane payload")

    def evidence_batch(self, sequence: int = 1, logical: str = "ev-0") -> EvidenceMutationBatch:
        return EvidenceMutationBatch(
            project_id=PROJECT,
            sequence=sequence,
            base_evidence_revision=self.coordinator.evidence.evidence_revision(PROJECT, sequence - 1),
            records=(
                EvidenceRecord(
                    project_id=PROJECT,
                    logical_record_id=logical,
                    payload_sha256=self.digest,
                    source_identity="source-0",
                    source_version="v1",
                    provenance_payload={"attack": True},
                    created_sequence=sequence,
                ),
            ),
        )

    def semantic_batch(self, sequence: int, label: str = "atom label") -> SemanticMutationBatch:
        return SemanticMutationBatch(
            sequence=sequence,
            base_semantic_revision=self.coordinator.semantic.semantic_revision(sequence - 1),
            new_fibers=(SemanticFiber("fiber-root", None, sequence),),
            atom_versions=(
                SemanticAtomVersion(
                    atom_id="atom-0",
                    fiber_id="fiber-root",
                    kind="MECHANISM",
                    label=label,
                    evidence_ids=("ev-0",),
                    payload={"attack": True},
                    valid_from_sequence=sequence,
                ),
                SemanticAtomVersion(
                    atom_id="atom-1",
                    fiber_id="fiber-root",
                    kind="MECHANISM",
                    label=label + " b",
                    evidence_ids=("ev-1",),
                    payload={"attack": True},
                    valid_from_sequence=sequence,
                ),
            ),
            witness_versions=(
                RelationWitnessVersion(
                    witness_id="witness-0",
                    left_atom_id="atom-0",
                    right_atom_id="atom-1",
                    relation_type="SUPPORTS",
                    reason="attack fixture",
                    condition=None,
                    evidence_ids=("ev-0",),
                    payload={"attack": True},
                    valid_from_sequence=sequence,
                ),
            ),
        )

    def counts(self) -> dict[str, int]:
        db = sqlite3.connect(self.db)
        try:
            return {
                table: db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                for table in (
                    "snapshots",
                    "transitions",
                    "engineering_evidence_records",
                    "engineering_evidence_batch_commits",
                    "semantic_fibers",
                    "semantic_atoms",
                    "semantic_atom_versions",
                    "semantic_batch_commits",
                )
            }
        finally:
            db.close()


def fixture(stack: list[Any], name: str) -> Fixture:
    tmp = tempfile.TemporaryDirectory(prefix=f"cross-plane-{name}-")
    stack.append(tmp)
    return Fixture(Path(tmp.name) / "stores")


STACK: list[Any] = []


# ---------------------------------------------------------------------------
# X01-X03 — NO-ALARM CONTROLS
# ---------------------------------------------------------------------------


def x01() -> tuple[str, str]:
    f = fixture(STACK, "x01")
    batch = f.evidence_batch()
    after = _snapshot(
        1,
        f.s0.snapshot_id,
        evidence_cutoff=f.coordinator.evidence.preview_batch_revision(batch),
        semantic_state_revision=f.s0.semantic_state_revision,
    )
    result = f.coordinator.commit_evidence_transition(
        _request(f.s0.snapshot_id, "ingest_evidence", f.coordinator.evidence_action_payload_hash(batch), "k1"),
        batch,
        after,
        blob_store=f.blobs,
        created_at_utc=NOW,
    )
    ok = (
        result.transition_receipt.status is TransitionStatus.COMMITTED
        and result.evidence_commit is not None
        and f.coordinator.state.head(PROJECT).snapshot_id == after.snapshot_id
        and f.counts()["engineering_evidence_records"] == 1
    )
    return (HELD if ok else BROKE), f"legitimate evidence transition {result.transition_receipt.status.value}"


def x02() -> tuple[str, str]:
    f = fixture(STACK, "x02")
    batch = f.semantic_batch(1)
    after = _snapshot(
        1,
        f.s0.snapshot_id,
        evidence_cutoff=f.s0.evidence_cutoff,
        semantic_state_revision=f.coordinator.semantic.preview_batch_revision(batch),
    )
    result = f.coordinator.commit_semantic_transition(
        _request(f.s0.snapshot_id, "update_semantic", f.coordinator.semantic_action_payload_hash(batch), "k1"),
        batch,
        after,
        created_at_utc=NOW,
    )
    ok = (
        result.transition_receipt.status is TransitionStatus.COMMITTED
        and result.semantic_commit is not None
        and f.coordinator.state.head(PROJECT).snapshot_id == after.snapshot_id
        and f.counts()["semantic_atom_versions"] == 2
    )
    return (HELD if ok else BROKE), f"legitimate semantic transition {result.transition_receipt.status.value}"


def x03() -> tuple[str, str]:
    f = fixture(STACK, "x03")
    atlas = SqliteAtlasPlaneStore(f.root / "atlas.db")
    batch = AtlasPlaneBatch(
        1,
        "atlas-base-empty",
        "atlas-batch-1",
        charts=(AtlasChartRecord("chart-a", "L"), AtlasChartRecord("chart-b", "L")),
        transitions=(AtlasTransitionRecord("t-ab", "chart-a", "chart-b", "GLUED"),),
        obstructions=(AtlasObstructionRecord("o-ab", "t-ab", "COCYCLE"),),
    )
    commit = atlas.commit_batch(batch, committed_snapshot_id=f.s0.snapshot_id, expected_atlas_revision="")
    counts = atlas.plane_counts()
    ok = commit.atlas_revision == atlas_revision_for(1, batch) and counts == {
        "atlas_plane_commits": 1,
        "atlas_charts": 2,
        "atlas_transitions": 1,
        "atlas_obstructions": 1,
    }
    return (HELD if ok else BROKE), f"legitimate atlas batch committed, counts={counts}"


# ---------------------------------------------------------------------------
# X04-X07 — payload binds plane A, effect touches plane B
# ---------------------------------------------------------------------------


def x04() -> tuple[str, str]:
    f = fixture(STACK, "x04")
    batch = f.semantic_batch(1)
    before = f.counts()
    after = _snapshot(
        1,
        f.s0.snapshot_id,
        evidence_cutoff="evidence-revision:SMUGGLED",
        semantic_state_revision=f.coordinator.semantic.preview_batch_revision(batch),
    )
    try:
        f.coordinator.commit_semantic_transition(
            _request(f.s0.snapshot_id, "update_semantic", f.coordinator.semantic_action_payload_hash(batch), "k1"),
            batch,
            after,
            created_at_utc=NOW,
        )
        return BROKE, f"evidence head moved by a semantic payload; counts={f.counts()}"
    except Exception as exc:  # noqa: BLE001
        unchanged = f.counts() == before and f.coordinator.state.head(PROJECT).snapshot_id == f.s0.snapshot_id
        return (HELD if unchanged else BROKE), f"{type(exc).__name__}: {exc}"


def x05() -> tuple[str, str]:
    f = fixture(STACK, "x05")
    batch = f.evidence_batch()
    before = f.counts()
    after = _snapshot(
        1,
        f.s0.snapshot_id,
        evidence_cutoff=f.coordinator.evidence.preview_batch_revision(batch),
        semantic_state_revision="semantic-revision:SMUGGLED",
    )
    try:
        f.coordinator.commit_evidence_transition(
            _request(f.s0.snapshot_id, "ingest_evidence", f.coordinator.evidence_action_payload_hash(batch), "k1"),
            batch,
            after,
            blob_store=f.blobs,
            created_at_utc=NOW,
        )
        return BROKE, f"semantic head moved by an evidence payload; counts={f.counts()}"
    except Exception as exc:  # noqa: BLE001
        unchanged = f.counts() == before and f.coordinator.state.head(PROJECT).snapshot_id == f.s0.snapshot_id
        return (HELD if unchanged else BROKE), f"{type(exc).__name__}: {exc}"


def x06() -> tuple[str, str]:
    f = fixture(STACK, "x06")
    committed = f.semantic_batch(1, label="the batch actually committed")
    decoy = f.semantic_batch(1, label="the batch the payload hash binds")
    before = f.counts()
    after = _snapshot(
        1,
        f.s0.snapshot_id,
        evidence_cutoff=f.s0.evidence_cutoff,
        semantic_state_revision=f.coordinator.semantic.preview_batch_revision(committed),
    )
    try:
        f.coordinator.commit_semantic_transition(
            _request(f.s0.snapshot_id, "update_semantic", f.coordinator.semantic_action_payload_hash(decoy), "k1"),
            committed,
            after,
            created_at_utc=NOW,
        )
        return BROKE, f"payload bound batch {decoy.batch_id[:24]} but batch {committed.batch_id[:24]} committed"
    except Exception as exc:  # noqa: BLE001
        unchanged = f.counts() == before
        return (HELD if unchanged else BROKE), f"{type(exc).__name__}: {exc}"


def x07() -> tuple[str, str]:
    f = fixture(STACK, "x07")
    batch = f.evidence_batch()
    atlas_batch = AtlasPlaneBatch(1, "r0", "atlas-batch-1", charts=(AtlasChartRecord("chart-a", "L"),))
    before = f.counts()
    after = _snapshot(
        1,
        f.s0.snapshot_id,
        evidence_cutoff=f.coordinator.evidence.preview_batch_revision(batch),
        semantic_state_revision=f.s0.semantic_state_revision,
    )
    try:
        f.coordinator.commit_evidence_transition(
            _request(f.s0.snapshot_id, "ingest_evidence", atlas_action_payload_hash(atlas_batch), "k1"),
            batch,
            after,
            blob_store=f.blobs,
            created_at_utc=NOW,
        )
        return BROKE, "an atlas payload hash was accepted as binding an evidence batch"
    except Exception as exc:  # noqa: BLE001
        unchanged = f.counts() == before
        return (
            (HELD if unchanged else BROKE),
            f"domain-separated hashes ({{atlas_batch_id}} vs {{evidence_batch_id}}); {type(exc).__name__}",
        )


# ---------------------------------------------------------------------------
# X08 — control-head advance with no payload binding (headline)
# ---------------------------------------------------------------------------


def x08() -> tuple[str, str]:
    f = fixture(STACK, "x08")
    facade = EngineeringServiceFacade(SqliteEngineeringStateStore(f.db))
    after = _snapshot(
        1,
        f.s0.snapshot_id,
        evidence_cutoff="evidence-revision:ATTACKER",
        semantic_state_revision="semantic-revision:ATTACKER",
        metric_ledger_head="metric-ledger-ATTACKER",
        episode_store_head="episode-store-ATTACKER",
        saturation_basis_ids=("saturation-basis-ATTACKER",),
        authority_projection_revision="authority-projection-ATTACKER",
        controller_epoch_id="controller-epoch-ATTACKER",
    )
    receipt = facade.commit_metadata_transition(
        request=_request(
            f.s0.snapshot_id,
            "unrelated_noop",
            canonical_sha256({"binds": "nothing at all"}),
            "k1",
        ),
        after_snapshot=after,
        created_at_utc=NOW,
    )
    head = facade.state.head(PROJECT)
    moved = [
        name
        for name in (
            "evidence_cutoff",
            "semantic_state_revision",
            "metric_ledger_head",
            "episode_store_head",
            "authority_projection_revision",
            "controller_epoch_id",
        )
        if getattr(head, name) != getattr(f.s0, name)
    ]
    if receipt.status is TransitionStatus.COMMITTED and moved:
        return (
            BROKE,
            "SqliteEngineeringStateStore.commit_transition, reachable via "
            "EngineeringServiceFacade.commit_metadata_transition, COMMITTED a transition whose "
            f"action_payload_hash binds nothing and moved {len(moved)} heads: {moved}",
        )
    return HELD, f"status={receipt.status.value} moved={moved}"


def x08b() -> tuple[str, str]:
    """The contrast: the same control-head advance through the atomic coordinator."""

    f = fixture(STACK, "x08b")
    batch = f.semantic_batch(1)
    before = f.counts()
    after = _snapshot(
        1,
        f.s0.snapshot_id,
        evidence_cutoff=f.s0.evidence_cutoff,
        semantic_state_revision=f.coordinator.semantic.preview_batch_revision(batch),
        authority_projection_revision="authority-projection-ATTACKER",
        controller_epoch_id="controller-epoch-ATTACKER",
    )
    try:
        f.coordinator.commit_semantic_transition(
            _request(f.s0.snapshot_id, "update_semantic", f.coordinator.semantic_action_payload_hash(batch), "k1"),
            batch,
            after,
            created_at_utc=NOW,
        )
        return BROKE, f"coordinator moved control heads under a semantic payload; counts={f.counts()}"
    except Exception as exc:  # noqa: BLE001
        unchanged = f.counts() == before and f.coordinator.state.head(PROJECT).snapshot_id == f.s0.snapshot_id
        return (HELD if unchanged else BROKE), f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------
# X09-X10 — half-writes must roll back every plane they touched
# ---------------------------------------------------------------------------


def x09() -> tuple[str, str]:
    """Injected fault AFTER the evidence rows are written, BEFORE the snapshot write.

    ``commit_evidence_transition`` writes the evidence batch first and the project
    snapshot second inside one transaction. A trigger that aborts the snapshot
    INSERT therefore lands exactly in the window where two planes are half-written.
    """

    f = fixture(STACK, "x09")
    batch = f.evidence_batch()
    before = f.counts()
    after = _snapshot(
        1,
        f.s0.snapshot_id,
        evidence_cutoff=f.coordinator.evidence.preview_batch_revision(batch),
        semantic_state_revision=f.s0.semantic_state_revision,
    )
    db = sqlite3.connect(f.db)
    try:
        db.execute(
            "CREATE TRIGGER injected_snapshot_fault BEFORE INSERT ON snapshots "
            "BEGIN SELECT RAISE(ABORT,'injected snapshot write fault'); END"
        )
        db.commit()
    finally:
        db.close()
    request = _request(
        f.s0.snapshot_id, "ingest_evidence", f.coordinator.evidence_action_payload_hash(batch), "k1"
    )
    try:
        f.coordinator.commit_evidence_transition(
            request, batch, after, blob_store=f.blobs, created_at_utc=NOW
        )
        faulted = False
    except Exception:  # noqa: BLE001 — the injected fault is the point
        faulted = True
    mid = f.counts()
    rolled_back = faulted and mid == before

    # Remove the injected fault and confirm the very same transition now commits:
    # a rollback that leaves the store unable to make progress is not a rollback.
    db = sqlite3.connect(f.db)
    try:
        db.execute("DROP TRIGGER injected_snapshot_fault")
        db.commit()
    finally:
        db.close()
    result = f.coordinator.commit_evidence_transition(
        request, batch, after, blob_store=f.blobs, created_at_utc=NOW
    )
    recovered = result.transition_receipt.status is TransitionStatus.COMMITTED
    return (
        (HELD if rolled_back and recovered else BROKE),
        f"fault_raised={faulted} both_planes_rolled_back={mid == before} "
        f"replay_after_fault_removed={result.transition_receipt.status.value}",
    )


def x10() -> tuple[str, str]:
    f = fixture(STACK, "x10")
    atlas = SqliteAtlasPlaneStore(f.root / "atlas.db")
    good = AtlasPlaneBatch(
        1,
        "atlas-base-empty",
        "atlas-batch-1",
        charts=(AtlasChartRecord("chart-a", "L"), AtlasChartRecord("chart-b", "L")),
        transitions=(AtlasTransitionRecord("t-ab", "chart-a", "chart-b"),),
        obstructions=(AtlasObstructionRecord("o-1", "t-ab"),),
    )
    atlas.commit_batch(good, committed_snapshot_id=f.s0.snapshot_id, expected_atlas_revision="")
    before = atlas.plane_counts()
    colliding = AtlasPlaneBatch(
        2,
        "atlas-base-after-1",
        "atlas-batch-2",
        charts=(AtlasChartRecord("chart-c", "L"), AtlasChartRecord("chart-d", "L")),
        transitions=(AtlasTransitionRecord("t-cd", "chart-c", "chart-d"),),
        obstructions=(AtlasObstructionRecord("o-1", "t-cd"),),  # obstruction id collides
    )
    try:
        atlas.commit_batch(colliding, committed_snapshot_id=f.s0.snapshot_id, expected_atlas_revision="")
        return BROKE, f"collision accepted; counts={atlas.plane_counts()}"
    except Exception as exc:  # noqa: BLE001
        after = atlas.plane_counts()
        return (
            (HELD if after == before else BROKE),
            f"{type(exc).__name__}; charts/transitions rolled back with the obstruction, counts={after}",
        )


# ---------------------------------------------------------------------------
# X11-X12 — atlas revision advance under a stale base
# ---------------------------------------------------------------------------


def x11() -> tuple[str, str]:
    f = fixture(STACK, "x11")
    atlas = SqliteAtlasPlaneStore(f.root / "atlas.db")
    b1 = AtlasPlaneBatch(
        1,
        "atlas-base-empty",
        "atlas-batch-1",
        charts=(AtlasChartRecord("chart-a", "L"), AtlasChartRecord("chart-b", "L")),
        transitions=(AtlasTransitionRecord("t-ab", "chart-a", "chart-b"),),
        obstructions=(AtlasObstructionRecord("o-ab", "t-ab"),),
    )
    c1 = atlas.commit_batch(b1, committed_snapshot_id=f.s0.snapshot_id, expected_atlas_revision="")
    # b2 declares the SAME pre-b1 base revision: it plans against a plane state that
    # no longer exists. The semantic store raises "base revision is stale" here.
    b2 = AtlasPlaneBatch(
        2,
        "atlas-base-empty",
        "atlas-batch-2",
        charts=(AtlasChartRecord("chart-c", "L"),),
    )
    try:
        c2 = atlas.commit_batch(b2, committed_snapshot_id=f.s0.snapshot_id, expected_atlas_revision="")
    except Exception as exc:  # noqa: BLE001
        return HELD, f"stale base revision rejected: {type(exc).__name__}: {exc}"
    # Also show that expected_atlas_revision cannot detect this: it is recomputed
    # from the same batch, so it agrees with any base the batch cares to declare.
    self_consistent = c2.atlas_revision == atlas_revision_for(2, b2)
    return (
        BROKE,
        "SqliteAtlasPlaneStore.commit_batch never compares base_atlas_revision against the "
        f"stored revision (current was {c1.atlas_revision[:16]}..., batch declared "
        "'atlas-base-empty') and expected_atlas_revision is recomputed from the same batch "
        f"(self_consistent={self_consistent}), so no compare-and-swap against stored plane "
        "state exists; the batch committed",
    )


def x12() -> tuple[str, str]:
    """Rewind FROM a legitimately established position, so this is not a restatement of X11.

    Sequences 1 and 2 are committed in order first. Only then is sequence 1 offered
    again, under a fresh batch id with disjoint record ids, so the only thing that
    could reject it is a monotonic check against the stored plane position.
    """

    f = fixture(STACK, "x12")
    atlas = SqliteAtlasPlaneStore(f.root / "atlas.db")
    b1 = AtlasPlaneBatch(
        1,
        "atlas-base-empty",
        "atlas-batch-1",
        charts=(AtlasChartRecord("chart-a", "L"), AtlasChartRecord("chart-b", "L")),
        transitions=(AtlasTransitionRecord("t-ab", "chart-a", "chart-b"),),
        obstructions=(AtlasObstructionRecord("o-ab", "t-ab"),),
    )
    c1 = atlas.commit_batch(b1, committed_snapshot_id=f.s0.snapshot_id, expected_atlas_revision="")
    b2 = AtlasPlaneBatch(
        2,
        c1.atlas_revision,
        "atlas-batch-2",
        charts=(AtlasChartRecord("chart-c", "L"), AtlasChartRecord("chart-d", "L")),
        transitions=(AtlasTransitionRecord("t-cd", "chart-c", "chart-d"),),
    )
    c2 = atlas.commit_batch(b2, committed_snapshot_id=f.s0.snapshot_id, expected_atlas_revision="")
    before = atlas.plane_counts()

    rewind = AtlasPlaneBatch(
        1,  # a position the plane already passed
        c2.atlas_revision,  # honest base: only the SEQUENCE is a rewind
        "atlas-batch-3",
        charts=(AtlasChartRecord("chart-e", "L"),),
    )
    try:
        atlas.commit_batch(rewind, committed_snapshot_id=f.s0.snapshot_id, expected_atlas_revision="")
    except Exception as exc:  # noqa: BLE001
        return HELD, f"sequence rewind rejected: {type(exc).__name__}: {exc}"
    return (
        BROKE,
        "after sequences 1 and 2 committed in order, a batch declaring sequence 1 with an "
        "otherwise honest base revision committed as well; the atlas plane has no monotonic "
        f"sequence check against stored plane position (counts {before} -> {atlas.plane_counts()})",
    )


# ---------------------------------------------------------------------------
# X13-X15 — replay with different content
# ---------------------------------------------------------------------------


def x13() -> tuple[str, str]:
    f = fixture(STACK, "x13")
    atlas = SqliteAtlasPlaneStore(f.root / "atlas.db")
    b1 = AtlasPlaneBatch(1, "base", "shared-batch-id", charts=(AtlasChartRecord("chart-a", "L"),))
    atlas.commit_batch(b1, committed_snapshot_id=f.s0.snapshot_id, expected_atlas_revision="")
    before = atlas.plane_counts()
    b2 = AtlasPlaneBatch(1, "base", "shared-batch-id", charts=(AtlasChartRecord("chart-z", "L"),))
    try:
        atlas.commit_batch(b2, committed_snapshot_id=f.s0.snapshot_id, expected_atlas_revision="")
        return BROKE, f"same batch id rebound to different content; counts={atlas.plane_counts()}"
    except Exception as exc:  # noqa: BLE001
        after = atlas.plane_counts()
        return (HELD if after == before else BROKE), f"{type(exc).__name__}: {exc}"


def x14() -> tuple[str, str]:
    f = fixture(STACK, "x14")
    honest = f.semantic_batch(1)
    try:
        SemanticMutationBatch(
            sequence=1,
            base_semantic_revision=honest.base_semantic_revision,
            new_fibers=honest.new_fibers,
            atom_versions=honest.atom_versions[:1],  # different content...
            witness_versions=(),
            batch_id=honest.batch_id,  # ...under the original id
        )
        return BROKE, "a semantic batch id was accepted for content it does not hash to"
    except ValueError as exc:
        return HELD, f"semantic batch ids are content-derived; forging one raises ValueError: {exc}"


def x15() -> tuple[str, str]:
    f = fixture(STACK, "x15")
    batch = f.evidence_batch()
    after = _snapshot(
        1,
        f.s0.snapshot_id,
        evidence_cutoff=f.coordinator.evidence.preview_batch_revision(batch),
        semantic_state_revision=f.s0.semantic_state_revision,
    )
    f.coordinator.commit_evidence_transition(
        _request(f.s0.snapshot_id, "ingest_evidence", f.coordinator.evidence_action_payload_hash(batch), "k1"),
        batch,
        after,
        blob_store=f.blobs,
        created_at_utc=NOW,
    )
    before = f.counts()
    other = f.evidence_batch(sequence=1, logical="ev-different")
    try:
        f.coordinator.commit_evidence_transition(
            _request(
                f.s0.snapshot_id,
                "ingest_evidence",
                f.coordinator.evidence_action_payload_hash(other),
                "k1",  # same idempotency key, different request
            ),
            other,
            after,
            blob_store=f.blobs,
            created_at_utc=NOW,
        )
        return BROKE, f"idempotency key rebound to a different request; counts={f.counts()}"
    except Exception as exc:  # noqa: BLE001
        return (HELD if f.counts() == before else BROKE), f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------
# X16-X17 — plane writes naming a snapshot that does not exist
# ---------------------------------------------------------------------------


def x16() -> tuple[str, str]:
    """The atlas plane lives outside the atomic metadata transaction.

    ``V2_IMPLEMENTATION_STATUS.md`` records "full Atlas chart/transition/obstruction
    persistence in the atomic metadata transaction" as an OPEN production residual,
    so this is confirmation of a documented gap, not a newly discovered defect.
    """

    f = fixture(STACK, "x16")
    atlas = SqliteAtlasPlaneStore(f.db)  # same database file as the snapshots table
    batch = AtlasPlaneBatch(1, "base", "atlas-batch-1", charts=(AtlasChartRecord("chart-a", "L"),))
    try:
        commit = atlas.commit_batch(
            batch, committed_snapshot_id="snapshot:this-snapshot-does-not-exist", expected_atlas_revision=""
        )
    except Exception as exc:  # noqa: BLE001
        return HELD, f"unknown snapshot rejected: {type(exc).__name__}: {exc}"
    return (
        KNOWN_OPEN,
        "atlas batch committed against snapshot id "
        f"{commit.committed_snapshot_id!r} which is absent from the snapshots table in the "
        "SAME database; the store has no snapshot-binding check (documented open item, "
        "V2_IMPLEMENTATION_STATUS.md: Atlas persistence in the atomic metadata transaction)",
    )


def x17() -> tuple[str, str]:
    f = fixture(STACK, "x17")
    control = SqliteControlProjectionStore(f.db)
    projection = ControlArtifactProjection(
        project_snapshot_id="snapshot:this-snapshot-does-not-exist",
        kind=ControlArtifactKind.CONTROLLER_DECISION,
        source_object_id="controller-decision-attack",
        canonical_payload={"attack": True},
    )
    try:
        control.record(projection)
        return BROKE, "control projection accepted an unknown project snapshot"
    except Exception as exc:  # noqa: BLE001
        return HELD, f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------------------

print("=" * 110)
print("CROSS-PLANE ATOMICITY ATTACKS V1 — E18 item 23")
print("=" * 110)
case("X01", "legitimate evidence transition (no-alarm control)", x01)
case("X02", "legitimate semantic transition (no-alarm control)", x02)
case("X03", "legitimate atlas plane batch (no-alarm control)", x03)
case("X04", "semantic payload, effect on the evidence plane", x04)
case("X05", "evidence payload, effect on the semantic plane", x05)
case("X06", "payload binds a different semantic batch", x06)
case("X07", "atlas payload hash offered to the evidence path", x07)
case("X08", "control-head advance with no payload binding", x08)
case("X08b", "same attack through the atomic coordinator", x08b)
case("X09", "injected fault mid-transaction, two planes", x09)
case("X10", "atlas batch half-write (id collision)", x10)
case("X11", "atlas advanced under a stale base revision", x11)
case("X12", "atlas sequence rewind", x12)
case("X13", "replayed atlas batch id, different content", x13)
case("X14", "replayed semantic batch id, different content", x14)
case("X15", "replayed idempotency key, different request", x15)
case("X16", "atlas batch naming an unknown snapshot", x16)
case("X17", "control projection naming an unknown snapshot", x17)

for tmp in STACK:
    tmp.cleanup()

held = sum(1 for r in RESULTS if r["outcome"] == HELD)
broke = sum(1 for r in RESULTS if r["outcome"] == BROKE)
known_open = sum(1 for r in RESULTS if r["outcome"] == KNOWN_OPEN)
cannot = sum(1 for r in RESULTS if r["outcome"] == CANNOT_CHECK)
print("=" * 110)
print(f"held {held}/{len(RESULTS)}   BROKE {broke}   confirms-known-open {known_open}   cannot-check {cannot}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(
    json.dumps(
        {
            "schema_version": "orion-cross-plane-attacks-v1",
            "fiber_id": "E18",
            "claim_under_attack": (
                "evidence / semantic / Atlas / control heads cannot be changed by an action "
                "whose payload hash does not bind those effects"
            ),
            "status": "FROZEN_CASES_EXECUTED__ALL_OUTCOMES_PRESERVED",
            "grants_scientific_authority": False,
            "cases_frozen_before_execution": True,
            "held": held,
            "broke": broke,
            "confirms_known_open": known_open,
            "cannot_check": cannot,
            "total": len(RESULTS),
            "no_alarm_controls": ["X01", "X02", "X03"],
            "breaks": [r for r in RESULTS if r["outcome"] == BROKE],
            "results": RESULTS,
            "not_claimed": [
                "an independently executed pass on an exact production release",
                "distributed exactly-once across external effects",
                "any result on a PostgreSQL or otherwise serializable production backend",
            ],
        },
        indent=2,
        sort_keys=True,
    )
    + "\n",
    encoding="utf-8",
)
print(f"wrote {OUT}")
