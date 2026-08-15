"""E18: execute HOSTILE_TEST_MATRIX.md, all 30 rows, against the real code.

The 30 rows below are FROZEN before execution: this list is the registration.
Every case is written to attack the row's stated invariant, not to confirm it.

Terminals (per row):

    HELD          the invariant survived the attack
    BROKE         the attack landed; the code path is named
    CANNOT_CHECK  the row's mechanism cannot be reproduced locally (needs a
                  PostgreSQL primary, an object-store endpoint, a container
                  registry, an OTLP collector); the reason is stated

Every HELD also carries a scope:

    FULL                  the row's mechanism itself was reproduced
    LOCAL_REFERENCE_ONLY  the row's INVARIANT was attacked with a local stand-in
                          for a production mechanism; what is NOT reproduced is
                          named in `not_exercised`

There are no by-choice omissions. Rows the earlier A01..A12 campaign
(run_hostile_assurance_v3.py) already attacked are re-executed here rather than
cited, unless the citation is stated in `cross_ref` with why it suffices.

Two rows carry a deliberately weakened variant that must BROKE (harness
self-validation, both directions). They are labelled `WEAKENED_*` and are
excluded from the row count.

    H01  kill during canonical blob write
    H02  blob committed, metadata transition killed before commit
    H03  metadata references unavailable blob
    H04  mutate stored blob bytes
    H05  torn episode JSONL tail
    H06  delete interior episode record
    H07  concurrent identical idempotency key, identical request
    H08  same idempotency key, different request
    H09  two writers plan on same project snapshot
    H10  stale controller decision replayed after semantic mutation
    H11  saturation certificate basis fingerprint changes
    H12  new native residual after bounded saturation
    H13  delete full-text/vector/graph index
    H14  corrupt derived index to return nonexistent atom
    H15  worker finishes external effect, crashes before completion record
    H16  duplicate activity delivery
    H17  DB failover mid-transition
    H18  object store temporary outage
    H19  restore backup into empty environment
    H20  point-in-time replay to older snapshot
    H21  partial schema migration
    H22  rollback after failed migration
    H23  secret rotation during worker lifetime
    H24  infrastructure admin submits unverified scientific promotion
    H25  malicious fabricated hard-gate ID in status
    H26  clock skew on worker
    H27  execution artifact rebuilt from different source but same label
    H28  audit/log exporter unavailable
    H29  high transaction contention
    H30  huge knowledge lattice + context request

Run from repository root:  PYTHONPATH=src python research/orion_engineering_closure_v1/run_hostile_matrix.py
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Callable

sys.path.insert(0, "src")

from rakl.engineering_atomic import SqliteAtomicEngineeringCoordinator  # noqa: E402
from rakl.engineering_backup import create_reference_backup, restore_reference_backup, verify_reference_backup  # noqa: E402
from rakl.engineering_blob import LocalFilesystemBlobStore  # noqa: E402
from rakl.engineering_capacity import (  # noqa: E402
    CapacityVerdict, EngineeringCapacityObservation, EngineeringCapacityPolicy, assess_engineering_capacity,
)
from rakl.engineering_control_store import ControlArtifactKind, ControlArtifactProjection, SqliteControlProjectionStore  # noqa: E402
from rakl.engineering_evidence_store import EvidenceMutationBatch, EvidenceRecord  # noqa: E402
from rakl.engineering_http import (  # noqa: E402
    Actor, Capability, EngineeringHttpService, IdentityProvider, SecretStore, SpanExporter, Telemetry, content_hash,
)
from rakl.engineering_index import IndexedAtom, RebuildableSemanticIndex, SemanticIndexSnapshot  # noqa: E402
from rakl.engineering_integration import SnapshotBoundSolverView, SolverViewFreshness, solver_view_freshness  # noqa: E402
from rakl.engineering_migration import ParityVerdict, build_import_receipt, compare_migration_parity  # noqa: E402
from rakl.engineering_ops import BuildProvenance, ProvenanceVerdict, measure_slo  # noqa: E402
from rakl.engineering_release import RuntimeArtifactIdentity  # noqa: E402
from rakl.engineering_security import InfraCapability, InfrastructurePrincipal, authorize_infrastructure  # noqa: E402
from rakl.engineering_semantic_store import SemanticAtomVersion, SemanticFiber, SemanticMutationBatch, SqliteSemanticStateStore  # noqa: E402
from rakl.engineering_service import EngineeringReadService  # noqa: E402
from rakl.engineering_state import (  # noqa: E402
    EpistemicAxisStatus, EpistemicStatus, NextActionClass, ProjectSnapshot, StateTransitionRequest, TransitionStatus,
)
from rakl.engineering_store import (  # noqa: E402
    EngineeringIntegrityError, IdempotencyConflict, SqliteEngineeringStateStore, metadata_transition_payload_hash,
)
from rakl.engineering_workflow import ActivitySpec, ActivityStatus, SqliteReferenceWorkflowEngine, WorkflowIntegrityError, WorkflowStatus  # noqa: E402
from rakl.engineering_workflow_workers import ClaimVerdict, SqliteWorkerWorkflowEngine  # noqa: E402
from rakl.episode_store import ChainVerdict, EpisodeStore, EpisodeStoreIntegrityError, verify_episode_store  # noqa: E402
from rakl.epistemic_saturation import (  # noqa: E402
    EpistemicGrowthVector, OperatorOrderAudit, SaturationBasis, SaturationRound, SaturationStatus,
    audit_bounded_epistemic_saturation,
)
from rakl.experience_substrate import SubstrateKind, SubstrateNode  # noqa: E402
from rakl.hard_gates import HardGateContract, HardGateObservation, HardGateRequirement, HardGateState, evaluate_hard_gates  # noqa: E402
from rakl.research_machine_workflow import (  # noqa: E402
    KnowledgeAcquisitionRound, KnowledgeDecision, KnowledgeSaturationPolicy, KnowledgeSearchMode,
    assess_knowledge_saturation,
)

OUT = Path("research/orion_engineering_closure_v1/HOSTILE_MATRIX_EXECUTION_V1.json")
T0 = "2026-08-15T15:00:00+00:00"
T1 = "2026-08-15T15:01:00+00:00"
T2 = "2026-08-15T15:02:00+00:00"

RESULTS: list[dict] = []
CONTROLS: list[dict] = []


class Outcome:
    def __init__(self, verdict: str, detail: str, *, scope: str = "FULL",
                 not_exercised: str = "", cross_ref: str = "", code_path: str = "") -> None:
        self.verdict, self.detail, self.scope = verdict, detail, scope
        self.not_exercised, self.cross_ref, self.code_path = not_exercised, cross_ref, code_path


def held(detail: str, **kw) -> Outcome:
    return Outcome("HELD", detail, **kw)


def broke(detail: str, *, code_path: str, **kw) -> Outcome:
    return Outcome("BROKE", detail, code_path=code_path, **kw)


def cannot_check(detail: str, **kw) -> Outcome:
    return Outcome("CANNOT_CHECK", detail, scope="NONE", **kw)


def case(row: str, name: str, fn: Callable[[], Outcome], *, control: bool = False, expect: str = "") -> None:
    try:
        o = fn()
    except Exception as exc:  # noqa: BLE001 -- an attack that blew up is not HELD
        o = Outcome("BROKE", f"harness exception {type(exc).__name__}: {exc}",
                    code_path="(the harness itself raised; treat as unverified)")
    rec = {"row": row, "name": name, "verdict": o.verdict, "scope": o.scope, "detail": o.detail}
    if o.not_exercised:
        rec["not_exercised"] = o.not_exercised
    if o.cross_ref:
        rec["cross_ref"] = o.cross_ref
    if o.code_path:
        rec["code_path"] = o.code_path
    if control:
        rec["expected"] = expect
        rec["ok"] = (o.verdict == expect)
        CONTROLS.append(rec)
        tag = "CTRL-OK " if rec["ok"] else "CTRL-BAD"
        print(f"  {tag} {row:<10} {name:<52} {o.verdict}")
        return
    RESULTS.append(rec)
    mark = {"HELD": "HELD ", "BROKE": "BROKE", "CANNOT_CHECK": "CANNT"}[o.verdict]
    print(f"  {mark} {row} {name:<52} [{o.scope}] {o.detail[:70]}")


# --- shared fixtures ---------------------------------------------------------


def initial_snapshot(coord: SqliteAtomicEngineeringCoordinator, project: str = "p") -> ProjectSnapshot:
    return ProjectSnapshot(
        project_id=project, sequence=0, previous_snapshot_id=None,
        evidence_cutoff=coord.evidence.evidence_revision(project, 0),
        semantic_state_revision=coord.semantic.semantic_revision(0),
        metric_ledger_head="m0", episode_store_head="ep0", saturation_basis_ids=("b0",),
        authority_projection_revision="a0", controller_epoch_id="epoch0", created_at_utc=T0,
    )


def plain_initial(project: str = "p") -> ProjectSnapshot:
    return ProjectSnapshot(
        project_id=project, sequence=0, previous_snapshot_id=None, evidence_cutoff="e0",
        semantic_state_revision="s0", metric_ledger_head="m0", episode_store_head="ep0",
        saturation_basis_ids=("b0",), authority_projection_revision="a0",
        controller_epoch_id="epoch0", created_at_utc=T0,
    )


def next_snapshot(prev: ProjectSnapshot, *, created_at: str = T1, **overrides) -> ProjectSnapshot:
    fields = dict(
        project_id=prev.project_id, sequence=prev.sequence + 1, previous_snapshot_id=prev.snapshot_id,
        evidence_cutoff=prev.evidence_cutoff, semantic_state_revision=prev.semantic_state_revision,
        metric_ledger_head=prev.metric_ledger_head, episode_store_head=prev.episode_store_head,
        saturation_basis_ids=prev.saturation_basis_ids,
        authority_projection_revision=prev.authority_projection_revision,
        controller_epoch_id=prev.controller_epoch_id, created_at_utc=created_at,
    )
    fields.update(overrides)
    return ProjectSnapshot(**fields)


def request(before: ProjectSnapshot, after: ProjectSnapshot, *, key: str,
            action: str = "ACT", process: str = "w1", created_at: str = T1) -> StateTransitionRequest:
    """A bare metadata transition; the store requires the payload hash to bind the after snapshot (X08 guard)."""
    return StateTransitionRequest(
        project_id=before.project_id, before_snapshot_id=before.snapshot_id, action=action,
        action_payload_hash=metadata_transition_payload_hash(after), idempotency_key=key, process_identity=process,
        read_set=("x",), write_set=("x",), created_at_utc=created_at,
    )


def status_for(snapshot: ProjectSnapshot, *, gates=("gate:real",), fingerprints=("fp:A",),
               reasons=("r",)) -> EpistemicStatus:
    return EpistemicStatus(
        project_snapshot_id=snapshot.snapshot_id, target_id="t", fiber_id="f",
        axis_statuses=(EpistemicAxisStatus("mech", True, 0),),
        required_routes=("R1",), covered_routes=("R1",), missing_routes=(),
        active_residual_ids=(), freshness_stale=False, required_authority=1,
        available_support_paths=1, blocking_cut_ids=(), hard_gate_ids=tuple(gates),
        next_action=NextActionClass.PROCEED_OBJECT_WORK, reasons=tuple(reasons),
        metric_receipt_ids=(), basis_fingerprints=tuple(fingerprints),
    )


def semantic_batch(coord: SqliteAtomicEngineeringCoordinator, name: str = "a") -> SemanticMutationBatch:
    return SemanticMutationBatch(
        sequence=1, base_semantic_revision=coord.semantic.semantic_revision(0),
        new_fibers=(SemanticFiber(f"fiber:{name}", created_from_sequence=1),),
        atom_versions=(SemanticAtomVersion(
            atom_id=f"atom:{name}", fiber_id=f"fiber:{name}", kind="MECHANISM_NODE", label=name,
            evidence_ids=(f"e:{name}",), payload={}, valid_from_sequence=1),),
    )


def evidence_batch(coord: SqliteAtomicEngineeringCoordinator, digest: str) -> EvidenceMutationBatch:
    rec = EvidenceRecord("p", "logical:1", digest, "doi:1", "v1", {"route": "FOUNDATIONAL"}, 1)
    return EvidenceMutationBatch("p", 1, coord.evidence.evidence_revision("p", 0), (rec,))


def node(i: int) -> SubstrateNode:
    return SubstrateNode(node_id=f"n{i}", kind=SubstrateKind.EVIDENCE, label=f"node {i}", payload_hash="h" * 8)


def kround(rid: str, route: str, novelty: int = 0, *, residual_ids=()) -> KnowledgeAcquisitionRound:
    sem = tuple(f"{rid}-s{i}" for i in range(novelty))
    return KnowledgeAcquisitionRound(
        round_id=rid, route_family=route, mode=KnowledgeSearchMode.INITIAL_BROAD, independent_route=True,
        query_ids=(f"q-{rid}",), source_ids=tuple(f"{rid}-p{i}" for i in range(10)),
        relevant_source_ids=tuple(f"{rid}-p{i}" for i in range(5)), retained_semantic_ids=sem,
        new_facet_ids=sem[:1], new_mechanism_ids=sem[1:2], cost_policy_id="cost-v1", cost=1.0,
        evidence_pointers=(f"ev-{rid}",), residual_ids=tuple(residual_ids),
    )


KPOLICY = KnowledgeSaturationPolicy(required_route_families=("foundational", "counterexample", "adjacent"),
                                    min_independent_flat_routes=3, window=3)


def api(telemetry=None):
    """The rewritten service (real stores). Creates project 'p' and returns (svc, headers, secrets, head_id)."""
    idp, sec = IdentityProvider(), SecretStore()
    svc = EngineeringHttpService(idp=idp, secrets=sec, telemetry=telemetry)
    tok = idp.issue(Actor("w", frozenset({"p"}), frozenset(Capability)))
    hdr = {"Authorization": f"Bearer {tok}"}
    st, body, _h = svc.handle("POST", "/v1/projects", hdr, json.dumps({"project_id": "p"}).encode())
    head = body["snapshot"]["snapshot_id"] if int(st) in (200, 201) else None
    return svc, hdr, sec, head


def head_of(svc, hdr):
    st, body, _h = svc.handle("GET", "/v1/projects/p/head", hdr, b"")
    return body.get("snapshot_id")


def post(svc, hdr, payload, key="k", expected=None):
    if expected is None:
        expected = head_of(svc, hdr)
    body = json.dumps({"idempotency_key": key, "expected_snapshot_id": expected, "payload": payload,
                       "payload_hash": content_hash(payload)}).encode()
    return svc.handle("POST", "/v1/projects/p/evidence", hdr, body)


# =============================================================================
# H01 -- kill during canonical blob write
# =============================================================================


def h01() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        store = LocalFilesystemBlobStore(Path(td))
        payload = b"canonical bytes " * 64
        digest = hashlib.sha256(payload).hexdigest()

        # kill point: after the temp file is fsynced, before os.replace installs it
        real_replace = os.replace

        def killed(src, dst):
            raise OSError("simulated kill before install")

        os.replace = killed
        try:
            try:
                store.put_if_absent(payload)
                return broke("put_if_absent survived a replace() failure",
                             code_path="rakl.engineering_blob.LocalFilesystemBlobStore.put_if_absent")
            except OSError:
                pass
        finally:
            os.replace = real_replace
        shard = Path(td) / digest[:2]
        leftovers = list(shard.glob(".orion-blob-*")) if shard.exists() else []
        if leftovers:
            return broke(f"torn temp object left behind: {leftovers}",
                         code_path="rakl.engineering_blob.LocalFilesystemBlobStore.put_if_absent finally-block")
        if store.exists_verified(digest):
            return broke("digest reported present after killed write",
                         code_path="rakl.engineering_blob.LocalFilesystemBlobStore.exists_verified")
        try:
            store.get_verified(digest)
            return broke("get_verified returned bytes for a never-installed digest",
                         code_path="rakl.engineering_blob.LocalFilesystemBlobStore.get_verified")
        except KeyError:
            pass
        # retry installs the correct object
        assert store.put_if_absent(payload) == digest and store.get_verified(digest) == payload

        # second kill window: a torn object already sitting at the target path
        target = store._path(digest)
        target.write_bytes(payload[:10])
        try:
            store.get_verified(digest)
            return broke("torn object at target path served as verified", code_path="get_verified")
        except EngineeringIntegrityError:
            pass
        try:
            store.put_if_absent(payload)
            return broke("put_if_absent silently overwrote a torn object", code_path="put_if_absent")
        except EngineeringIntegrityError:
            pass
        return held("killed write leaves no temp, no target, digest absent; retry installs; "
                    "torn target -> integrity error on read and on re-put")


# =============================================================================
# H02 -- blob committed, metadata transition killed before commit
# =============================================================================


def _evidence_setup(td: str):
    coord = SqliteAtomicEngineeringCoordinator(Path(td) / "u.db")
    blobs = LocalFilesystemBlobStore(Path(td) / "blobs")
    s0 = coord.initialize_empty_project(initial_snapshot(coord))
    payload = b"evidence bytes"
    digest = blobs.put_if_absent(payload)
    batch = evidence_batch(coord, digest)
    s1 = next_snapshot(s0, evidence_cutoff=coord.evidence.preview_batch_revision(batch))
    req = StateTransitionRequest(
        project_id="p", before_snapshot_id=s0.snapshot_id, action="INGEST_EVIDENCE",
        action_payload_hash=coord.evidence_action_payload_hash(batch), idempotency_key="k1",
        process_identity="w1", read_set=("evidence",), write_set=("evidence",), created_at_utc=T1)
    return coord, blobs, s0, s1, batch, req, digest


def h02() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        coord, blobs, s0, s1, batch, req, digest = _evidence_setup(td)
        real = coord.evidence._commit_batch_db

        def commit_then_die(db, *a, **k):
            real(db, *a, **k)            # evidence rows written inside the open tx
            raise RuntimeError("worker killed after evidence rows, before head/receipt")

        coord.evidence._commit_batch_db = commit_then_die
        try:
            coord.commit_evidence_transition(req, batch, s1, blob_store=blobs, created_at_utc=T1)
            return broke("transition committed despite kill", code_path="commit_evidence_transition")
        except RuntimeError:
            pass
        finally:
            coord.evidence._commit_batch_db = real
        head = coord.state.head("p")
        with sqlite3.connect(Path(td) / "u.db") as db:
            n_tr = db.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
            n_ev = db.execute("SELECT COUNT(*) FROM engineering_evidence_records").fetchone()[0]
            n_bc = db.execute("SELECT COUNT(*) FROM engineering_evidence_batch_commits").fetchone()[0]
        if head != s0 or n_tr or n_ev or n_bc:
            return broke(f"partial state survived: head_moved={head != s0} transitions={n_tr} evidence={n_ev} batch_commits={n_bc}",
                         code_path="rakl.engineering_atomic.SqliteAtomicEngineeringCoordinator.commit_evidence_transition")
        if not blobs.exists_verified(digest):
            return broke("orphan blob was lost", code_path="engineering_blob")
        # retry with the identical request must now commit cleanly
        res = coord.commit_evidence_transition(req, batch, s1, blob_store=blobs, created_at_utc=T1)
        if res.transition_receipt.status is not TransitionStatus.COMMITTED or coord.state.head("p") != s1:
            return broke("retry after kill did not commit", code_path="commit_evidence_transition")
        return held("head unchanged, 0 transitions/evidence rows/batch commits after kill; orphan blob intact; retry commits")


# =============================================================================
# H03 -- metadata references unavailable blob
# =============================================================================


def h03() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        coord, blobs, s0, s1, batch, req, digest = _evidence_setup(td)
        # remove the object the metadata will reference
        blobs._path(digest).unlink()
        try:
            coord.commit_evidence_transition(req, batch, s1, blob_store=blobs, created_at_utc=T1)
            return broke("metadata committed pointing at a missing blob",
                         code_path="rakl.engineering_atomic.SqliteAtomicEngineeringCoordinator.commit_evidence_transition")
        except EngineeringIntegrityError as exc:
            msg = str(exc)
        if coord.state.head("p") != s0:
            return broke("head moved on refused evidence ingest", code_path="commit_evidence_transition")
        # a read of the missing digest fails closed, not empty
        try:
            blobs.stat(digest)
            return broke("stat() returned for a missing digest", code_path="engineering_blob.stat")
        except KeyError:
            pass
        return held(f"ingest refused ({msg[:50]}...); head unchanged; stat() raises KeyError")


# =============================================================================
# H04 -- mutate stored blob bytes
# =============================================================================


def h04() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        store = LocalFilesystemBlobStore(Path(td))
        payload = b"immutable evidence"
        digest = store.put_if_absent(payload)
        store._path(digest).write_bytes(b"immutable evidenc3")  # same length, one byte flipped
        try:
            store.get_verified(digest)
            return broke("mutated blob served as verified", code_path="rakl.engineering_blob.LocalFilesystemBlobStore.get_verified")
        except EngineeringIntegrityError:
            pass
        if store.exists_verified(digest):
            return broke("exists_verified True on mutated blob", code_path="exists_verified")
        try:
            store.put_if_absent(payload)
            return broke("re-put silently repaired the mutated object (identity ambiguity)", code_path="put_if_absent")
        except EngineeringIntegrityError:
            pass
        return held("digest mismatch on read; exists_verified False; re-put refuses rather than overwrite")


# =============================================================================
# H05 / H06 -- episode store tail truncation / interior deletion
# =============================================================================


def h05() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "ep.jsonl"
        st = EpisodeStore(p)
        for i in range(3):
            st.append_substrate_node(node(i))
        good_head = st.head_hash
        with p.open("a", encoding="utf-8") as h:
            h.write('{"schema_version":"x","sequence_index":3,"kind":"SUBSTRATE_N')  # torn tail, no newline
        rep = verify_episode_store(p)
        if rep.verdict is not ChainVerdict.TRUNCATED:
            return broke(f"torn tail reported {rep.verdict.value}", code_path="rakl.episode_store.verify_episode_store")
        if rep.record_count != 3 or rep.first_bad_index != 3 or rep.head_hash != good_head:
            return broke(f"prefix not preserved: count={rep.record_count} first_bad={rep.first_bad_index}",
                         code_path="verify_episode_store")
        try:
            EpisodeStore(p)
            return broke("store opened over a torn tail (append would extend a broken chain)",
                         code_path="rakl.episode_store.EpisodeStore.__init__")
        except EpisodeStoreIntegrityError:
            pass
        return held("TRUNCATED at index 3, 3-record prefix and head preserved; store refuses to open")


def h06() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "ep.jsonl"
        st = EpisodeStore(p)
        for i in range(4):
            st.append_substrate_node(node(i))
        lines = p.read_text().splitlines()
        del lines[1]
        p.write_text("\n".join(lines) + "\n")
        rep = verify_episode_store(p)
        if rep.verdict is not ChainVerdict.TAMPERED or rep.first_bad_index != 1:
            return broke(f"interior deletion -> {rep.verdict.value} first_bad={rep.first_bad_index}",
                         code_path="rakl.episode_store.verify_episode_store")
        # also: a rewritten shorter internally-valid chain is caught by the expected head
        st2 = EpisodeStore(Path(td) / "ep2.jsonl")
        for i in range(3):
            st2.append_substrate_node(node(i))
        head3 = st2.head_hash
        l2 = st2.path.read_text().splitlines()
        st2.path.write_text("\n".join(l2[:2]) + "\n")
        rep2 = verify_episode_store(st2.path, expected_head_hash=head3)
        if rep2.verdict is not ChainVerdict.TRUNCATED:
            return broke("tail rewrite passed against expected head", code_path="verify_episode_store")
        return held("TAMPERED with first_bad_index=1; tail-rewrite vs expected head -> TRUNCATED")


# =============================================================================
# H07 / H08 / H09 -- idempotency + snapshot CAS at the store layer
# =============================================================================


def h07() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "s.db"
        SqliteEngineeringStateStore(path).initialize_project(plain_initial())
        s0 = plain_initial()
        s1 = next_snapshot(s0)
        req = request(s0, s1, key="same")

        def worker(_):
            return SqliteEngineeringStateStore(path).commit_transition(req, s1, created_at_utc=T1)

        with ThreadPoolExecutor(8) as ex:
            receipts = list(ex.map(worker, range(8)))
        ids = {r.transition_id for r in receipts}
        statuses = {r.status for r in receipts}
        head = SqliteEngineeringStateStore(path).head("p")
        if len(ids) != 1 or statuses != {TransitionStatus.COMMITTED} or head != s1:
            return broke(f"{len(ids)} distinct receipts, statuses={statuses}, head_seq={head.sequence}",
                         code_path="rakl.engineering_store.SqliteEngineeringStateStore.commit_transition")
        return held("8 concurrent identical requests -> 1 transition_id, all COMMITTED replays, head seq 1",
                    cross_ref="A03 covers the HTTP layer serially; this re-executes concurrently at the store")


def h08() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        st = SqliteEngineeringStateStore(Path(td) / "s.db")
        s0 = st.initialize_project(plain_initial())
        s1 = next_snapshot(s0)
        st.commit_transition(request(s0, s1, key="k"), s1, created_at_utc=T1)
        s1_other = next_snapshot(s0, controller_epoch_id="other-epoch")     # a different request under the same key
        try:
            st.commit_transition(request(s0, s1_other, key="k"), s1_other, created_at_utc=T1)
            return broke("same key, different request accepted", code_path="commit_transition")
        except IdempotencyConflict:
            pass
        try:
            st.commit_transition(request(s0, s1, key="k", process="w2"), s1, created_at_utc=T1)   # same after, different requester
            return broke("same key, different process_identity accepted", code_path="commit_transition")
        except IdempotencyConflict:
            pass
        # also on the non-committed path
        try:
            st.record_noncommitted_transition(request(s0, s1_other, key="k"),
                                              status=TransitionStatus.ABORTED, reasons=("x",), created_at_utc=T1)
            return broke("record_noncommitted_transition rebinds a key", code_path="record_noncommitted_transition")
        except IdempotencyConflict:
            pass
        return held("IdempotencyConflict on both commit and non-committed paths",
                    cross_ref="A04 covers the HTTP layer; re-executed at the store")


def h09() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "s.db"
        SqliteEngineeringStateStore(path).initialize_project(plain_initial())
        s0 = plain_initial()

        def writer(i):
            st = SqliteEngineeringStateStore(path)
            s1 = next_snapshot(s0, controller_epoch_id=f"epoch-{i}")
            return st.commit_transition(request(s0, s1, key=f"k{i}", process=f"w{i}"), s1, created_at_utc=T1)

        with ThreadPoolExecutor(6) as ex:
            receipts = list(ex.map(writer, range(6)))
        committed = [r for r in receipts if r.status is TransitionStatus.COMMITTED]
        retry = [r for r in receipts if r.status is TransitionStatus.RETRY_REQUIRED]
        head = SqliteEngineeringStateStore(path).head("p")
        if len(committed) != 1 or len(retry) != 5 or head.sequence != 1:
            return broke(f"committed={len(committed)} retry={len(retry)} head_seq={head.sequence}",
                         code_path="rakl.engineering_store.SqliteEngineeringStateStore.commit_transition")
        return held("6 writers on one snapshot -> 1 COMMITTED, 5 RETRY_REQUIRED receipts, head seq 1",
                    cross_ref="A01 covers the HTTP layer serially; re-executed concurrently at the store")


# =============================================================================
# H10 -- stale controller decision replayed after semantic mutation
# =============================================================================


def h10() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        coord = SqliteAtomicEngineeringCoordinator(Path(td) / "u.db")
        s0 = coord.initialize_empty_project(initial_snapshot(coord))
        # a decision/view/workflow all planned on s0
        view = SnapshotBoundSolverView(project_snapshot_id=s0.snapshot_id, problem_id="pr", target_id="t",
                                       support_structure_id="ss", compiler_identity="c1",
                                       required_authority=1, atom_ids=("atom:a",))
        wf = SqliteReferenceWorkflowEngine(Path(td) / "wf.db")
        wf.start_workflow(workflow_id="w", project_id="p", project_snapshot_id=s0.snapshot_id)
        stale_after = next_snapshot(s0, controller_epoch_id="e1")
        decision_req = request(s0, stale_after, key="decision-on-s0", action="APPLY_CONTROLLER_DECISION")
        # semantic mutation moves the head
        b = semantic_batch(coord)
        s1 = next_snapshot(s0, semantic_state_revision=coord.semantic.preview_batch_revision(b))
        sreq = StateTransitionRequest(project_id="p", before_snapshot_id=s0.snapshot_id, action="UPDATE_SEMANTIC_ATLAS",
                                      action_payload_hash=coord.semantic_action_payload_hash(b), idempotency_key="sem",
                                      process_identity="w1", read_set=("semantic",), write_set=("semantic",), created_at_utc=T1)
        coord.commit_semantic_transition(sreq, b, s1, created_at_utc=T1)
        # replay the stale decision
        rc = coord.state.commit_transition(decision_req, stale_after, created_at_utc=T2)
        fresh = solver_view_freshness(view, coord.state.head("p"))
        wfs = wf.check_snapshot_freshness("w", current_project_snapshot_id=coord.state.head("p").snapshot_id)
        if rc.status is not TransitionStatus.RETRY_REQUIRED or coord.state.head("p") != s1:
            return broke(f"stale decision -> {rc.status.value}, head={coord.state.head('p').sequence}",
                         code_path="rakl.engineering_store.SqliteEngineeringStateStore.commit_transition")
        if fresh is not SolverViewFreshness.STALE or wfs is not WorkflowStatus.CANNOT_CHECK:
            return broke(f"view={fresh.value} workflow={wfs.value}", code_path="engineering_integration/engineering_workflow")
        return held("stale decision -> RETRY_REQUIRED, head still s1; solver view STALE; workflow CANNOT_CHECK")


# =============================================================================
# H11 -- saturation certificate basis fingerprint changes
# =============================================================================


def _sround(rid: str, fp: str) -> SaturationRound:
    audit = OperatorOrderAudit("oa", "d1", "d2", EpistemicGrowthVector(), ("ev",))
    return SaturationRound(rid, fp, EpistemicGrowthVector(), True, True, True, True, audit, "2026-08-01")


def h11() -> Outcome:
    basis_a = SaturationBasis("b", "scope", "id-v1", "routes-v1", "nov-v1", "ev-v1")
    basis_b = SaturationBasis("b", "scope", "id-v2", "routes-v1", "nov-v1", "ev-v1")  # identity policy changed
    rounds = (_sround("r1", basis_a.fingerprint), _sround("r2", basis_a.fingerprint))
    ok = audit_bounded_epistemic_saturation(rounds, basis=basis_a)
    if ok.status is not SaturationStatus.BOUNDED_SATURATED:
        return cannot_check(f"could not build a saturated certificate to invalidate: {ok.reasons}")
    bad = audit_bounded_epistemic_saturation(rounds, basis=basis_b)
    if bad.status is not SaturationStatus.INVALID_BASIS:
        return broke(f"certificate under a changed basis -> {bad.status.value}",
                     code_path="rakl.epistemic_saturation.audit_bounded_epistemic_saturation")
    # and at the status plane: same coordinates, different basis fingerprint -> refused, not silently replaced
    with tempfile.TemporaryDirectory() as td:
        st = SqliteEngineeringStateStore(Path(td) / "s.db")
        s0 = st.initialize_project(plain_initial())
        st.record_epistemic_status(status_for(s0, fingerprints=("fp:A",)))
        try:
            st.record_epistemic_status(status_for(s0, fingerprints=("fp:B",)))
            return broke("status with a different basis fingerprint replaced/coexisted at the same snapshot coords",
                         code_path="rakl.engineering_store.SqliteEngineeringStateStore.record_epistemic_status")
        except EngineeringIntegrityError:
            pass
    return held("INVALID_BASIS on fingerprint change; status plane refuses a second fingerprint at same coordinates")


# =============================================================================
# H12 -- new native residual after bounded saturation
# =============================================================================


def h12() -> Outcome:
    rounds = (kround("r1", "foundational"), kround("r2", "counterexample"), kround("r3", "adjacent"))
    sat = assess_knowledge_saturation(rounds, policy=KPOLICY)
    if sat.decision is not KnowledgeDecision.PROCEED_OBJECT_WORK:
        return cannot_check(f"could not reach bounded saturation to reopen: {sat.reasons}")
    reopened = assess_knowledge_saturation(rounds, policy=KPOLICY, active_knowledge_residual_ids=("res:native",))
    if reopened.decision is not KnowledgeDecision.TARGETED_REFRESH_REQUIRED:
        return broke(f"residual after saturation -> {reopened.decision.value}",
                     code_path="rakl.research_machine_workflow.assess_knowledge_saturation")
    # only the implicated axis reopens: an axis with a reopen residual cannot claim bounded_flat
    try:
        EpistemicAxisStatus("mech", True, 0, reopen_residual_ids=("res:native",))
        return broke("axis reopened by a residual still claims bounded_flat", code_path="rakl.engineering_state.EpistemicAxisStatus")
    except ValueError:
        pass
    st = EpistemicStatus(
        project_snapshot_id="snapshot:x", target_id="t", fiber_id="f",
        axis_statuses=(EpistemicAxisStatus("mech", False, 0, reopen_residual_ids=("res:native",)),
                       EpistemicAxisStatus("deriv", True, 0)),
        required_routes=(), covered_routes=(), missing_routes=(), active_residual_ids=("res:native",),
        freshness_stale=False, required_authority=0, available_support_paths=0, blocking_cut_ids=(),
        hard_gate_ids=(), next_action=NextActionClass.TARGETED_REFRESH_REQUIRED, reasons=("r",),
        metric_receipt_ids=(), basis_fingerprints=())
    if st.bounded_saturated or not st.axis_statuses[1].bounded_flat:
        return broke("untouched axis lost flatness or status still saturated", code_path="engineering_state.EpistemicStatus")
    return held("PROCEED -> TARGETED_REFRESH_REQUIRED on new residual; only the implicated axis is non-flat")


# =============================================================================
# H13 / H14 -- index deletion / index corruption
# =============================================================================


def _semantic_with_atom(td: str):
    store = SqliteSemanticStateStore(Path(td) / "sem.db")
    b = SemanticMutationBatch(
        sequence=1, base_semantic_revision=store.semantic_revision(0),
        new_fibers=(SemanticFiber("fiber:a", created_from_sequence=1),),
        atom_versions=(SemanticAtomVersion(atom_id="atom:a", fiber_id="fiber:a", kind="MECHANISM_NODE",
                                           label="alpha", evidence_ids=("e:a",), payload={}, valid_from_sequence=1),))
    store.commit_batch(b, committed_snapshot_id="snapshot:" + "1" * 64,
                       expected_semantic_revision=store.preview_batch_revision(b))
    return store


def h13() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        store = _semantic_with_atom(td)
        idx = RebuildableSemanticIndex()
        first = idx.rebuild(store, sequence=1)
        idx.clear()   # the deletion
        if idx.snapshot is not None or idx.exact_filter(fiber_ids=("fiber:a",)) != ():
            return broke("cleared index still serves", code_path="rakl.engineering_index.RebuildableSemanticIndex")
        if store.latest_atom_version("atom:a") is None:
            return broke("canonical atom lost with the index", code_path="engineering_semantic_store")
        again = idx.rebuild(store, sequence=1)
        if again.index_id != first.index_id or len(again.indexed_atoms) != 1:
            return broke("rebuild is not identity-stable", code_path="RebuildableSemanticIndex.rebuild")
        return held("cleared index returns () (degraded); canonical atom intact; rebuild reproduces identical index_id")


def h14() -> Outcome:
    from rakl.engineering_index import IndexIntegrityError, IndexVerdict
    with tempfile.TemporaryDirectory() as td:
        store = _semantic_with_atom(td)
        idx = RebuildableSemanticIndex()
        real = idx.rebuild(store, sequence=1)
        fake = IndexedAtom("atom:ghost", "ver:ghost", "fiber:a", "MECHANISM_NODE", "alpha ghost")
        # attack 1: forge a snapshot carrying a ghost under the REAL index_id
        try:
            SemanticIndexSnapshot(real.semantic_revision, real.indexed_atoms + (fake,), real.index_id)
            return broke("a snapshot with a fabricated atom was accepted under the real index_id",
                         code_path="rakl.engineering_index.SemanticIndexSnapshot.__post_init__")
        except ValueError:
            pass
        # attack 2: a self-consistent ghost snapshot (its own honest id) swapped in behind the verifier
        ghost_snap = SemanticIndexSnapshot(real.semantic_revision, real.indexed_atoms + (fake,))
        idx._snapshot = ghost_snap
        try:
            served = idx.exact_filter(fiber_ids=("fiber:a",))
            return broke(f"swapped-in ghost projection served {[a.atom_id for a in served]} without verification",
                         code_path="rakl.engineering_index.RebuildableSemanticIndex._served")
        except IndexIntegrityError:
            pass
        v = idx.verify(store)
        if v.verdict is not IndexVerdict.GHOST_ATOMS or v.ghost_atom_ids != ("atom:ghost",):
            return broke(f"verify() did not name the ghost: {v}", code_path="RebuildableSemanticIndex.verify")
        for call in (lambda: idx.exact_filter(fiber_ids=("fiber:a",)), lambda: idx.lexical("ghost")):
            try:
                call()
                return broke("ghost projection served after a failed verify()", code_path="RebuildableSemanticIndex._served")
            except IndexIntegrityError:
                pass
        # attack 3: mutate atoms behind a verified id (frozen dataclass -> object.__setattr__)
        idx.rebuild(store, sequence=1)
        object.__setattr__(idx._snapshot, "indexed_atoms", idx._snapshot.indexed_atoms + (fake,))
        try:
            idx.lexical("ghost")
            return broke("atoms mutated behind a verified index_id were served", code_path="RebuildableSemanticIndex._served")
        except IndexIntegrityError:
            pass
        # no-alarm: rebuild serves; verify() on the rebuilt index is VERIFIED
        again = idx.rebuild(store, sequence=1)
        ok = idx.verify(store)
        if not ok.ok or [a.atom_id for a in idx.exact_filter(fiber_ids=("fiber:a",))] != ["atom:a"]:
            return broke(f"honest index refused after rebuild: {ok}", code_path="RebuildableSemanticIndex")
        return held("forged id refused at construction; swapped-in ghost snapshot refused (unverified); verify() names "
                    "atom:ghost -> GHOST_ATOMS and exact_filter/lexical raise IndexIntegrityError; mutated-behind-id "
                    "caught; rebuilt index VERIFIED and served",
                    cross_ref="first execution BROKE here; fixed in engineering_index.py (SemanticIndexSnapshot.__post_init__, "
                              "RebuildableSemanticIndex.verify/_served)")


# =============================================================================
# H15 / H16 -- worker crash after effect / duplicate delivery
# =============================================================================


def h15() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        eng = SqliteWorkerWorkflowEngine(Path(td) / "w.db")
        eng.schedule("w", ActivitySpec("send", "inv-1", "d", retry_safe=False, external_effect=True), idempotency_key="k")
        a = eng.claim("w", "send", worker_id="A", now=0, ttl=10)
        eng.mark_effect_started(a.lease)          # effect goes out...
        # ...worker A dies here: no complete(). Lease lapses. Worker B arrives.
        b = eng.claim("w", "send", worker_id="B", now=100, ttl=10)
        act = eng.activity("w", "send")
        late = eng.complete(a.lease, result_digest="late")
        if b.verdict is not ClaimVerdict.RECOVERY_REQUIRED or act.status is not ActivityStatus.RECOVERY_REQUIRED:
            return broke(f"B claim -> {b.verdict.value}; activity {act.status.value} (effect may replay)",
                         code_path="rakl.engineering_workflow_workers.SqliteWorkerWorkflowEngine.claim")
        if late is not False:
            return broke("dead worker's stale lease could still write a receipt", code_path="SqliteWorkerWorkflowEngine.complete")
        # reference engine: same window
        ref = SqliteReferenceWorkflowEngine(Path(td) / "r.db")
        ref.start_workflow(workflow_id="w", project_id="p", project_snapshot_id="snapshot:" + "0" * 64)
        ref.schedule_activity("w", ActivitySpec("send", "inv-1", "d", retry_safe=False, external_effect=True))
        ref.begin_activity("w", "send")
        rec = ref.recover_ambiguous_activity("w", "send")
        try:
            ref.begin_activity("w", "send")
            return broke("reference engine restarted a RECOVERY_REQUIRED activity", code_path="SqliteReferenceWorkflowEngine.begin_activity")
        except WorkflowIntegrityError:
            pass
        if rec.status is not ActivityStatus.RECOVERY_REQUIRED or ref.workflow("w").status is not WorkflowStatus.RECOVERY_REQUIRED:
            return broke("reference engine did not escalate to RECOVERY_REQUIRED", code_path="recover_ambiguous_activity")
        return held("worker engine: RECOVERY_REQUIRED on reclaim after effect_started; stale lease cannot complete; "
                    "reference engine: RECOVERY_REQUIRED and re-begin refused",
                    cross_ref="A06 only tested lease expiry; this executes the effect-then-crash window the row names")


def h16() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        eng = SqliteWorkerWorkflowEngine(Path(td) / "w.db")
        eng.schedule("w", ActivitySpec("a", "inv-1", "d", retry_safe=True, external_effect=False), idempotency_key="k")
        a = eng.claim("w", "a", worker_id="A", now=0, ttl=30)
        dup_live = eng.claim("w", "a", worker_id="B", now=1, ttl=30)          # duplicate delivery while live
        eng.complete(a.lease, result_digest="d1")
        dup_done = eng.claim("w", "a", worker_id="C", now=2, ttl=30)          # duplicate delivery after completion
        act = eng.activity("w", "a")
        if dup_live.verdict is not ClaimVerdict.HELD_BY_LIVE_WORKER:
            return broke(f"second delivery while live -> {dup_live.verdict.value}", code_path="SqliteWorkerWorkflowEngine.claim")
        if dup_done.verdict is not ClaimVerdict.ALREADY_COMPLETED or act.attempt_count != 1 or act.result_digest != "d1":
            return broke(f"post-completion delivery -> {dup_done.verdict.value}, attempts={act.attempt_count}",
                         code_path="SqliteWorkerWorkflowEngine.claim")
        # reference engine: a second complete with a different digest cannot rebind
        ref = SqliteReferenceWorkflowEngine(Path(td) / "r.db")
        ref.start_workflow(workflow_id="w", project_id="p", project_snapshot_id="snapshot:" + "0" * 64)
        ref.schedule_activity("w", ActivitySpec("a", "inv-1", "d", retry_safe=True, external_effect=False))
        ref.begin_activity("w", "a")
        ref.complete_activity("w", "a", result_digest="d1")
        same = ref.complete_activity("w", "a", result_digest="d1")
        try:
            ref.complete_activity("w", "a", result_digest="d2")
            return broke("completed activity rebound to a second result", code_path="SqliteReferenceWorkflowEngine.complete_activity")
        except WorkflowIntegrityError:
            pass
        if same.result_digest != "d1":
            return broke("idempotent re-complete changed the result", code_path="complete_activity")
        return held("live duplicate HELD_BY_LIVE_WORKER; post-completion duplicate ALREADY_COMPLETED; attempts=1; "
                    "reference engine refuses to rebind a completed result",
                    cross_ref="A02 covered only the live-holder half")


# =============================================================================
# H17 -- DB failover mid-transition
# =============================================================================


def h17() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        coord = SqliteAtomicEngineeringCoordinator(Path(td) / "u.db")
        s0 = coord.initialize_empty_project(initial_snapshot(coord))
        b = semantic_batch(coord)
        s1 = next_snapshot(s0, semantic_state_revision=coord.semantic.preview_batch_revision(b))
        req = StateTransitionRequest(project_id="p", before_snapshot_id=s0.snapshot_id, action="UPDATE_SEMANTIC_ATLAS",
                                     action_payload_hash=coord.semantic_action_payload_hash(b), idempotency_key="k",
                                     process_identity="w1", read_set=("semantic",), write_set=("semantic",), created_at_utc=T1)
        real = coord.semantic._commit_batch_db

        def lose_connection(db, *a, **k):
            real(db, *a, **k)
            raise sqlite3.OperationalError("simulated connection loss to primary")

        coord.semantic._commit_batch_db = lose_connection
        try:
            coord.commit_semantic_transition(req, b, s1, created_at_utc=T1)
            return broke("commit reported success across the failure", code_path="commit_semantic_transition")
        except sqlite3.OperationalError:
            pass
        finally:
            coord.semantic._commit_batch_db = real
        head = coord.state.head("p")
        atoms = coord.semantic.atom_versions_at(1)
        with sqlite3.connect(Path(td) / "u.db") as db:
            n = db.execute("SELECT COUNT(*) FROM semantic_batch_commits").fetchone()[0] + \
                db.execute("SELECT COUNT(*) FROM transitions").fetchone()[0]
        if head != s0 or atoms or n:
            return broke(f"partial project state after mid-transition failure: head_moved={head != s0} atoms={len(atoms)} rows={n}",
                         code_path="rakl.engineering_atomic.SqliteAtomicEngineeringCoordinator._tx")
        res = coord.commit_semantic_transition(req, b, s1, created_at_utc=T1)
        if res.transition_receipt.status is not TransitionStatus.COMMITTED:
            return broke("retry did not commit", code_path="commit_semantic_transition")
        return held("mid-transaction connection loss -> full rollback (head, atoms, commits, receipts all unchanged); retry commits",
                    scope="LOCAL_REFERENCE_ONLY",
                    not_exercised="a real primary failover (connection drop + promoted replica) needs a PostgreSQL cluster; "
                                  "the invariant is shown under an in-process SQLite transaction abort only")


# =============================================================================
# H18 -- object store temporary outage
# =============================================================================


class _OutageBlobStore:
    """A BlobStore whose backend is unreachable. Every read raises OSError."""

    def put_if_absent(self, payload):  # noqa: D401
        raise OSError("object store unreachable")

    def get_verified(self, digest):
        raise OSError("object store unreachable")

    def exists_verified(self, digest):
        raise OSError("object store unreachable")

    def stat(self, digest):
        raise OSError("object store unreachable")


def h18() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        coord, blobs, s0, s1, batch, req, digest = _evidence_setup(td)
        try:
            coord.commit_evidence_transition(req, batch, s1, blob_store=_OutageBlobStore(), created_at_utc=T1)
            return broke("ingest committed while the object store was unreachable", code_path="commit_evidence_transition")
        except EngineeringIntegrityError as exc:
            # this is the fabricated conclusion the row forbids: "missing/corrupt" while merely unreachable
            return broke(f"outage was reported as evidence integrity failure: {exc}",
                         code_path="rakl.engineering_atomic.SqliteAtomicEngineeringCoordinator.commit_evidence_transition")
        except OSError:
            pass
        if coord.state.head("p") != s0:
            return broke("head moved during outage", code_path="commit_evidence_transition")
        # a real local outage: the shard directory becomes unreadable
        shard = blobs._path(digest).parent
        if os.geteuid() == 0:
            perm_note = "; chmod-based unreadable-shard variant skipped (running as root)"
        else:
            shard.chmod(0)
            try:
                try:
                    blobs.exists_verified(digest)
                    perm_note = "; BUT unreadable shard returned a boolean from exists_verified (permission error swallowed?)"
                    shard.chmod(0o755)
                    return broke("unreadable object store shard yielded a definite exists/missing answer" + perm_note,
                                 code_path="rakl.engineering_blob.LocalFilesystemBlobStore.exists_verified")
                except PermissionError:
                    perm_note = "; unreadable shard -> PermissionError propagates (no false 'missing')"
            finally:
                shard.chmod(0o755)
        return held("unreachable store -> OSError propagates, no integrity verdict fabricated, head unchanged" + perm_note,
                    scope="LOCAL_REFERENCE_ONLY",
                    not_exercised="a network object-store endpoint outage/timeout; the terminal is an unhandled OSError, "
                                  "not a typed CANNOT_CHECK receipt -- that shaping is a production-adapter obligation")


# =============================================================================
# H19 / H20 -- restore into empty env / point-in-time replay
# =============================================================================


def h19() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        coord, blobs, s0, s1, batch, req, digest = _evidence_setup(td)
        coord.commit_evidence_transition(req, batch, s1, blob_store=blobs, created_at_utc=T1)
        frozen_head = coord.state.head("p").snapshot_id
        zip_path = Path(td) / "backup.zip"
        manifest = create_reference_backup(zip_path, project_snapshot_id=frozen_head, created_at_utc=T2,
                                           inputs={"db/u.db": Path(td) / "u.db", "blobs": Path(td) / "blobs"})
        v = verify_reference_backup(zip_path)
        if not v.valid:
            return broke(f"fresh backup did not verify: {v.verdict.value}", code_path="engineering_backup.verify_reference_backup")
        empty = Path(td) / "restored"
        restore_reference_backup(zip_path, empty)
        rs = SqliteEngineeringStateStore(empty / "db" / "u.db")
        rb = LocalFilesystemBlobStore(empty / "blobs")
        if rs.head("p").snapshot_id != frozen_head or rs.head("p") != s1:
            return broke("restored head differs from frozen head", code_path="engineering_backup.restore_reference_backup")
        if rb.get_verified(digest) != b"evidence bytes":
            return broke("restored blob differs", code_path="restore_reference_backup")
        try:
            restore_reference_backup(zip_path, empty)   # not empty any more
            return broke("restore into a non-empty environment was allowed", code_path="restore_reference_backup")
        except ValueError:
            pass
        return held(f"restore into empty dir reproduces head {frozen_head[:24]}.. and blob bytes; non-empty destination refused",
                    cross_ref="A05 executed only the CORRUPTED_BLOB branch of a different (engineering_ops) verifier")


def h20() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        coord = SqliteAtomicEngineeringCoordinator(Path(td) / "u.db")
        ctrl = SqliteControlProjectionStore(Path(td) / "u.db")
        s0 = coord.initialize_empty_project(initial_snapshot(coord))
        st0 = coord.state.record_epistemic_status(status_for(s0, gates=("gate:g0",)))
        ctrl.record(ControlArtifactProjection(s0.snapshot_id, ControlArtifactKind.HARD_GATE, "gate:g0", {"state": "PASS"}))
        b = semantic_batch(coord)
        s1 = next_snapshot(s0, semantic_state_revision=coord.semantic.preview_batch_revision(b))
        coord.commit_semantic_transition(
            StateTransitionRequest(project_id="p", before_snapshot_id=s0.snapshot_id, action="UPDATE_SEMANTIC_ATLAS",
                                   action_payload_hash=coord.semantic_action_payload_hash(b), idempotency_key="k",
                                   process_identity="w1", read_set=("semantic",), write_set=("semantic",), created_at_utc=T1),
            b, s1, created_at_utc=T1)
        coord.state.record_epistemic_status(status_for(s1, gates=("gate:g1",)))
        # replay to s0
        old = coord.state.get_snapshot(s0.snapshot_id)
        old_status = coord.state.latest_epistemic_status(project_snapshot_id=s0.snapshot_id, target_id="t", fiber_id="f")
        old_gates = ctrl.records(s0.snapshot_id, kind=ControlArtifactKind.HARD_GATE)
        atoms_then, atoms_now = coord.semantic.atom_versions_at(0), coord.semantic.atom_versions_at(1)
        if old != s0 or old_status != st0 or old_status.status_id != st0.status_id:
            return broke("historical snapshot/status not reproduced exactly", code_path="engineering_store")
        if len(old_gates) != 1 or old_gates[0].source_object_id != "gate:g0" or atoms_then != () or len(atoms_now) != 1:
            return broke("historical control/semantic state not reproduced", code_path="engineering_control_store/semantic_store")
        return held("snapshot s0, its EpistemicStatus (same status_id), HARD_GATE projection and semantic state at seq 0 all reconstruct while head is s1")


# =============================================================================
# H21 / H22 -- partial schema migration / rollback after failed migration
# =============================================================================


def h21() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "s.db"
        st = SqliteEngineeringStateStore(path)
        s0 = st.initialize_project(plain_initial())
        s1 = next_snapshot(s0)
        st.commit_transition(request(s0, s1, key="k"), s1, created_at_utc=T1)
        # variant A: a payload from a future schema version lands in the table
        with sqlite3.connect(path) as db:
            row = json.loads(db.execute("SELECT payload_json FROM snapshots WHERE snapshot_id=?", (s1.snapshot_id,)).fetchone()[0])
            row["schema_version"] = "orion-engineering-state-v99"
            db.execute("UPDATE snapshots SET payload_json=? WHERE snapshot_id=?", (json.dumps(row), s1.snapshot_id))
        try:
            SqliteEngineeringStateStore(path).head("p")
            var_a = "BROKE: future-schema snapshot served"
        except ValueError:
            var_a = "future-schema payload refused"
        # restore payload
        with sqlite3.connect(path) as db:
            row["schema_version"] = "orion-engineering-state-v2"
            db.execute("UPDATE snapshots SET payload_json=? WHERE snapshot_id=?", (json.dumps(row), s1.snapshot_id))
        if var_a.startswith("BROKE"):
            return broke(var_a, code_path="rakl.engineering_state.ProjectSnapshot.from_dict")
        # variant B: half-applied migration -- a ledger table is missing
        from rakl.engineering_schema_guard import SchemaIntegrityError
        with sqlite3.connect(path) as db:
            db.execute("DROP TABLE transitions")
        try:
            reopened = SqliteEngineeringStateStore(path)
            head = reopened.head("p")
            return broke(f"{var_a}; BUT after a half-applied migration (transitions dropped) the store reopened and served "
                         f"head seq {head.sequence}", code_path="rakl.engineering_store.SqliteEngineeringStateStore._initialize_schema")
        except SchemaIntegrityError as exc:
            if "transitions" not in exc.missing_tables:
                return broke(f"typed error did not name the missing table: {exc}", code_path="engineering_schema_guard")
        with sqlite3.connect(path) as db:
            recreated = db.execute("SELECT 1 FROM sqlite_master WHERE name='transitions'").fetchone() is not None
        if recreated:
            return broke("the guard raised but the table was recreated anyway", code_path="engineering_schema_guard")
        # variant C: the same guard on the stores that share the idiom
        from rakl.engineering_semantic_store import SqliteSemanticStateStore as _Sem
        from rakl.engineering_workflow import SqliteReferenceWorkflowEngine as _Wf
        for cls, table in ((_Sem, "semantic_atom_versions"), (_Wf, "workflow_events")):
            p2 = Path(td) / f"{table}.db"
            cls(p2)
            with sqlite3.connect(p2) as db:
                db.execute(f"DROP TABLE {table}")
            try:
                cls(p2)
                return broke(f"{cls.__name__} reopened over a dropped {table}", code_path=f"{cls.__module__}._init_schema")
            except SchemaIntegrityError:
                pass
        # no-alarm: a fresh db and a normal reopen both work
        fresh = Path(td) / "fresh.db"
        SqliteEngineeringStateStore(fresh).initialize_project(plain_initial())
        if SqliteEngineeringStateStore(fresh).head("p") != s0:
            return broke("normal reopen failed", code_path="engineering_schema_guard")
        return held(f"{var_a}; dropped `transitions` -> SchemaIntegrityError naming it, table NOT recreated, head not served; "
                    f"same for semantic + workflow stores; fresh open and normal reopen fine",
                    cross_ref="first execution BROKE here; fixed via engineering_schema_guard in six stores")


def h22() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "s.db"
        st = SqliteEngineeringStateStore(path)
        s0 = st.initialize_project(plain_initial())
        s1 = next_snapshot(s0)
        st.commit_transition(request(s0, s1, key="k"), s1, created_at_utc=T1)

        def dump():
            with sqlite3.connect(path) as db:
                return {t: [tuple(r) for r in db.execute(f"SELECT * FROM {t} ORDER BY 1")]
                        for t in ("snapshots", "project_heads", "transitions", "epistemic_statuses")}

        before = dump()
        # a migration that fails half-way, run inside one transaction, then rolled back
        con = sqlite3.connect(path)
        try:
            con.execute("BEGIN")
            con.execute("ALTER TABLE transitions ADD COLUMN migrated INTEGER DEFAULT 0")
            con.execute("UPDATE transitions SET migrated=1")
            raise RuntimeError("migration step 3 failed")
        except RuntimeError:
            con.execute("ROLLBACK")
        finally:
            con.close()
        after = dump()
        parity = compare_migration_parity(before, after)
        if parity.verdict is not ParityVerdict.MATCH:
            return broke(f"post-rollback state differs from pre-migration: {parity.differences}",
                         code_path="sqlite ROLLBACK / engineering_migration.compare_migration_parity")
        # and a MISMATCH cannot be receipted
        bad = compare_migration_parity(before, {**after, "transitions": []})
        try:
            build_import_receipt(import_id="i", project_id="p", source_store_kind="sqlite", source_store_identity="a",
                                 source_head_hash="h", target_backend_identity="b", imported_object_ids=("x",),
                                 parity_report=bad, created_at_utc=T2)
            return broke("import receipt minted on MISMATCH parity", code_path="rakl.engineering_migration.build_import_receipt")
        except ValueError:
            pass
        ok = build_import_receipt(import_id="i", project_id="p", source_store_kind="sqlite", source_store_identity="a",
                                  source_head_hash="h", target_backend_identity="b", imported_object_ids=("x",),
                                  parity_report=parity, created_at_utc=T2)
        return held(f"canonical dumps MATCH after rollback (digest {parity.source_digest[:12]}..); MISMATCH cannot be receipted; "
                    f"receipt {ok.receipt_id[:28]}..")


# =============================================================================
# H23 / H24 / H25 -- secrets, infra-vs-scientific authority, fabricated gate id
# =============================================================================


def h23() -> Outcome:
    svc, hdr, sec, head = api()
    if head is None:
        return cannot_check("could not create project through the API")
    sec.put("api_key", "value-v1")
    r1 = sec.reference("api_key")
    s1, b1, _h = post(svc, hdr, {"content_utf8": "one", "secret_names": ["api_key"]}, key="k1")
    sec.put("api_key", "value-v2")             # rotation during the worker's lifetime
    r2 = sec.reference("api_key")
    s2, b2, _h = post(svc, hdr, {"content_utf8": "two", "secret_names": ["api_key"]}, key="k2")
    if int(s1) not in (200, 201) or int(s2) not in (200, 201):
        return cannot_check(f"evidence posts did not commit: {s1} {b1.get('error')} / {s2} {b2.get('error')}")
    _s, prov, _h = svc.handle("GET", "/v1/projects/p/provenance", hdr, b"")
    text = json.dumps(prov)
    if "value-v1" in text or "value-v2" in text:
        return broke("secret value entered provenance", code_path="rakl.engineering_http.EngineeringHttpService.handle")
    if r1 == r2 or r1 not in text or r2 not in text:
        return broke(f"rotation not reflected as a declared revision change: {r1} / {r2}", code_path="SecretStore.reference")
    if sec.resolve("api_key") != "value-v2":
        return broke("resolve did not follow rotation", code_path="SecretStore.resolve")
    return held(f"only {r1} and {r2} appear in receipts; resolve() follows rotation; no value leaked",
                cross_ref="A12 covered value-not-in-provenance; rotation added here")


def h24() -> Outcome:
    admin = InfrastructurePrincipal("root", "spiffe://cluster/admin", (InfraCapability.ADMIN,))
    dec = authorize_infrastructure(admin, InfraCapability.GOVERNANCE_PROMOTE)
    if not dec.allowed:
        return cannot_check("infra admin was not even authorized for the infra op; the scientific gate was never reached")
    if admin.grants_scientific_authority or dec.grants_scientific_authority:
        return broke("infrastructure ADMIN mints scientific authority", code_path="rakl.engineering_security")
    # the scientific gate itself: an unverified promotion (no gate observations, no evidence) -> not passable by anyone
    contract = HardGateContract("c", (HardGateRequirement("FORMAL_VERIFICATION", "x"),), frozen_before_candidate_results=True)
    rep = evaluate_hard_gates(contract, (), candidate_id="cand")
    if rep.state is not HardGateState.CANNOT_CHECK:
        return broke(f"promotion with no gate evidence -> {rep.state.value}", code_path="rakl.hard_gates.evaluate_hard_gates")
    # the API surface: full-capability actor tries to write scientific authority
    svc, hdr, _sec, head = api()
    if head is None:
        return cannot_check("could not create project through the API")
    st, body, _h = post(svc, hdr, {"scientific_authority": "PROMOTED"}, key="k")
    if st != 403 or body.get("error") != "AUTHORITY_PROJECTION_IMMUTABLE":
        return broke(f"API accepted a scientific_authority write from a full-capability actor: {st} {body}",
                     code_path="rakl.engineering_http.EngineeringHttpService._validate_mutation")
    return held("ADMIN authorized for the infra op but grants no scientific authority; unverified promotion -> hard gates CANNOT_CHECK; "
                "API refuses scientific_authority write with 403",
                cross_ref="A09 covered authority_projection_revision; scientific_authority key + hard-gate path added")


def h25() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        coord = SqliteAtomicEngineeringCoordinator(Path(td) / "u.db")
        ctrl = SqliteControlProjectionStore(Path(td) / "u.db")
        s0 = coord.initialize_empty_project(initial_snapshot(coord))
        ctrl.record(ControlArtifactProjection(s0.snapshot_id, ControlArtifactKind.HARD_GATE, "gate:real", {"state": "PASS"}))
        fabricated = status_for(s0, gates=("gate:FABRICATED",))
        coord.state.record_epistemic_status(fabricated)
        served = EngineeringReadService(coord.state).shared_status(project_id="p", target_id="t", fiber_id="f")
        # receipt lookup for the fabricated id
        backed = {r.source_object_id for r in ctrl.records(s0.snapshot_id, kind=ControlArtifactKind.HARD_GATE)}
        lookup_fails = "gate:FABRICATED" not in backed
        # authority binding: a fabricated PASS observation against a frozen contract
        contract = HardGateContract("c", (HardGateRequirement("gate:real", "x"),), frozen_before_candidate_results=True)
        obs = (HardGateObservation("gate:FABRICATED", "cand", HardGateState.PASS, evidence_ids=("ev",)),)
        rep = evaluate_hard_gates(contract, obs, candidate_id="cand")
        binding_fails = rep.state is HardGateState.CANNOT_CHECK and "gate:real" in rep.reasons[0]
        if not lookup_fails or not binding_fails:
            return broke(f"lookup_fails={lookup_fails} binding_fails={binding_fails} ({rep.state.value})",
                         code_path="engineering_control_store.records / hard_gates.evaluate_hard_gates")
        if served.status.grants_scientific_authority:
            return broke("status carrying a fabricated gate id grants authority", code_path="engineering_state.EpistemicStatus")
        return held("fabricated gate id has no HARD_GATE projection (lookup empty); fabricated PASS observation leaves the "
                    "contract's real gate unresolved -> CANNOT_CHECK; status grants no authority. CAVEAT preserved: "
                    "EngineeringReadService.shared_status served the status without cross-checking hard_gate_ids against "
                    "the control store -- the fail-closed depends on the consumer performing the lookup; no service does it for them.")


# =============================================================================
# H26 / H27 -- clock skew / rebuilt artifact
# =============================================================================


def h26() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        st = SqliteEngineeringStateStore(Path(td) / "s.db")
        s0 = st.initialize_project(plain_initial())
        skewed_earlier = "2026-08-15T14:00:00+00:00"   # worker clock an hour behind s0's created_at
        s1 = next_snapshot(s0, created_at=skewed_earlier)
        rc = st.commit_transition(request(s0, s1, key="k", created_at=skewed_earlier), s1, created_at_utc=skewed_earlier)
        if rc.status is not TransitionStatus.COMMITTED or st.head("p").sequence != 1:
            return broke("ordering depended on wall clock: skewed writer refused/mis-ordered", code_path="commit_transition")
        # a skewed writer still cannot jump the sequence
        try:
            jump = next_snapshot(s1, **{"sequence": 5})
            st.commit_transition(request(s1, jump, key="k2"), jump, created_at_utc=T2)
            return broke("sequence skipped", code_path="commit_transition")
        except ValueError:
            pass
        # workflow history: ordering is by sequence + hash chain
        wf = SqliteReferenceWorkflowEngine(Path(td) / "w.db")
        wf.start_workflow(workflow_id="w", project_id="p", project_snapshot_id=s0.snapshot_id)
        wf.schedule_activity("w", ActivitySpec("a", "i", "d", True, False))
        wf.begin_activity("w", "a")
        ev = wf.events("w")
        seqs = [e.sequence for e in ev]
        chained = all(ev[i].previous_event_hash == ev[i - 1].event_hash for i in range(1, len(ev)))
        if seqs != list(range(len(ev))) or not chained or not wf.verify_history("w"):
            return broke("workflow order not sequence/hash-bound", code_path="engineering_workflow")
        # worker leases: cite A07 (heartbeat in the past does not extend)
        return held("skewed-earlier writer commits at seq 1 (order by sequence, not clock); sequence jump refused; "
                    "workflow events sequence+hash chained; heartbeat-in-the-past covered by A07",
                    cross_ref="A07 clock skew: heartbeat in the past -> lease not extended")


def h27() -> Outcome:
    src_a, src_b = b"build-from-commit-A", b"build-from-commit-B"
    label = "registry/orion:release-1.0@sha256:" + hashlib.sha256(src_a).hexdigest()
    prov_a = BuildProvenance("commitA", "lockA", "procA", label, hashlib.sha256(src_a).hexdigest(), "cfg", "rm")
    v_same = prov_a.verify(src_a)
    v_rebuilt = prov_a.verify(src_b)          # same label, different source/bytes
    same_image = "sha256:" + hashlib.sha256(b"image").hexdigest()      # same image label/digest, different source
    id_a = RuntimeArtifactIdentity("orion", hashlib.sha256(src_a).hexdigest(), "commitA", "ci", "release", "prov-a", same_image, "env-a")
    id_b = RuntimeArtifactIdentity("orion", hashlib.sha256(src_b).hexdigest(), "commitB", "ci", "release", "prov-b", same_image, "env-a")
    if v_same is not ProvenanceVerdict.VERIFIED:
        return cannot_check("genuine artifact did not verify; cannot test the rebuilt case")
    if v_rebuilt is not ProvenanceVerdict.ARTIFACT_MISMATCH or id_a.identity_id == id_b.identity_id:
        return broke(f"rebuilt artifact under the same label -> {v_rebuilt.value}; ids equal={id_a.identity_id == id_b.identity_id}",
                     code_path="rakl.engineering_ops.BuildProvenance.verify / engineering_release.RuntimeArtifactIdentity")
    return held("same label, different source -> ARTIFACT_MISMATCH; RuntimeArtifactIdentity ids differ",
                cross_ref="A11 covered the mutable-tag refusal only")


# =============================================================================
# H28 -- audit/log exporter unavailable
# =============================================================================


class _DeadExporter(SpanExporter):
    def export(self, span):
        raise ConnectionError("OTLP collector unreachable")


def h28() -> Outcome:
    # project created while the exporter is healthy; then the collector goes away
    svc, hdr, _sec, head = api()
    if head is None:
        return cannot_check("could not create project through the API")
    svc.tel = Telemetry(_DeadExporter())
    seq_before = svc.state.head("p").sequence
    # a read
    try:
        st, body, _h = svc.handle("GET", "/v1/projects/p/head", hdr, b"")
        read = f"read ok {int(st)}"
    except Exception as exc:  # noqa: BLE001
        read = f"read RAISED {type(exc).__name__}"
    # a mutation
    try:
        st, body, _h = post(svc, hdr, {"content_utf8": "x"}, key="k1", expected=head)
        write = f"write ok {int(st)} status={body.get('status')}"
        raised = False
    except Exception as exc:  # noqa: BLE001
        write = f"write RAISED {type(exc).__name__}"
        raised = True
    seq_after = svc.state.head("p").sequence
    if raised or read.startswith("read RAISED"):
        return broke(
            f"{read}; {write}; project.sequence {seq_before}->{seq_after}. With the exporter down, EVERY request raises out "
            f"of handle(): reads are unavailable and the mutation's state change ({seq_before}->{seq_after}) was applied "
            f"but no response/receipt reached the caller. That is not 'degraded observability + explicit health'; it is "
            f"an outage of the scientific API caused by the telemetry sink, and a committed mutation with a lost receipt.",
            code_path="rakl.engineering_http._SpanCtx.__exit__ (exporter.export raises through the context manager) -> "
                      "EngineeringHttpService.handle (try/except ApiError sits INSIDE the span; the return value is discarded)")
    return held(f"{read}; {write}; transition semantics unchanged with exporter down")


# =============================================================================
# H29 / H30 -- contention / capacity
# =============================================================================


def h29() -> Outcome:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "s.db"
        SqliteEngineeringStateStore(path).initialize_project(plain_initial())
        N, retries, lat = 12, [0] * 12, []

        def writer(i):
            st = SqliteEngineeringStateStore(path)
            t0 = time.perf_counter()
            for attempt in range(200):
                head = st.head("p")
                s_next = next_snapshot(head, controller_epoch_id=f"e{i}-{attempt}")
                rc = st.commit_transition(request(head, s_next, key=f"w{i}-a{attempt}", process=f"w{i}"), s_next, created_at_utc=T1)
                if rc.status is TransitionStatus.COMMITTED:
                    lat.append((time.perf_counter() - t0) * 1000)
                    return attempt
                retries[i] += 1
            return -1

        with ThreadPoolExecutor(N) as ex:
            attempts = list(ex.map(writer, range(N)))
        head = SqliteEngineeringStateStore(path).head("p")
        with sqlite3.connect(path) as db:
            n_committed = db.execute("SELECT COUNT(*) FROM transitions WHERE status='COMMITTED'").fetchone()[0]
            n_retry = db.execute("SELECT COUNT(*) FROM transitions WHERE status='RETRY_REQUIRED'").fetchone()[0]
        lat.sort()
        p95 = lat[min(len(lat) - 1, int(len(lat) * 0.95))] if lat else -1
        if -1 in attempts or head.sequence != N or n_committed != N:
            return broke(f"contention: {attempts.count(-1)} writers starved; head={head.sequence} committed={n_committed}",
                         code_path="rakl.engineering_store.SqliteEngineeringStateStore.commit_transition")
        return held(f"{N} contending writers all committed (head seq {N}); {n_retry} RETRY_REQUIRED receipts preserved; "
                    f"max retries/writer={max(retries)}; p95 time-to-commit {p95:.1f} ms",
                    scope="LOCAL_REFERENCE_ONLY",
                    not_exercised="a production latency/resource envelope; these are single-host SQLite numbers on the "
                                  "test machine, not a registered SLO. PERFORMANCE_ENVELOPE_EXCEEDED cannot be judged here.")


def h30() -> Outcome:
    policy = EngineeringCapacityPolicy("cap-v1", 10_000, 10_000, 5, 2, 8_000)
    huge_context = assess_engineering_capacity(EngineeringCapacityObservation("snapshot:x", 100, 100, 1, 0, 2_000_000), policy)
    huge_index_lag = assess_engineering_capacity(EngineeringCapacityObservation("snapshot:x", 100, 100, 1, 50, 100), policy)
    unknown = assess_engineering_capacity(EngineeringCapacityObservation("snapshot:x", 100, None, 1, 0, 100), policy)
    if huge_context.verdict is not CapacityVerdict.BLOCK_NEW_WORK:
        return broke(f"context overflow -> {huge_context.verdict.value}", code_path="rakl.engineering_capacity.assess_engineering_capacity")
    if huge_index_lag.verdict is not CapacityVerdict.COMPACT_REBUILDABLE_VIEWS or not huge_index_lag.preserve_canonical_history:
        return broke(f"index lag -> {huge_index_lag.verdict.value}", code_path="assess_engineering_capacity")
    if unknown.verdict is not CapacityVerdict.CANNOT_CHECK:
        return broke(f"missing observation -> {unknown.verdict.value} (should fail closed)", code_path="assess_engineering_capacity")
    # the runtime compile path: a tiny budget must CANNOT_COMPILE, not silently truncate
    from rakl.project_runtime import RAKLProject, TaskPacketVerdict
    with tempfile.TemporaryDirectory() as td:
        proj = RAKLProject.create(Path(td) / "proj", project_id="p")
        for i in range(30):
            proj.ingest_bytes(record_id=f"r{i}", payload=(f"record {i} " * 200).encode(), token_cost=400,
                              fiber_ids=("f",), coverage_atoms=(f"a{i}",))
        rep = proj.compile_task_packet(operation="SOLVE", question="q", budget_tokens=5, target_fibers=("f",))
        cr = rep.compile_report
        # the same budget with MANDATORY records: does the guard exist at all?
        proj2 = RAKLProject.create(Path(td) / "proj2", project_id="p2")
        for i in range(5):
            proj2.ingest_bytes(record_id=f"m{i}", payload=(f"must {i} " * 200).encode(), token_cost=400,
                               fiber_ids=("f",), coverage_atoms=(f"a{i}",), mandatory=True)
        rep2 = proj2.compile_task_packet(operation="SOLVE", question="q", budget_tokens=5, target_fibers=("f",))
        if rep.verdict is not TaskPacketVerdict.READY:
            if "context_over_budget" not in tuple(rep.issues):
                return broke(f"not READY but the reason does not name the budget: {rep.issues}",
                             code_path="rakl.context_compiler.compile_epistemic_context")
            # no-alarm: records that fit are READY; nothing-relevant stays READY-empty (not over budget)
            proj3 = RAKLProject.create(Path(td) / "proj3", project_id="p3")
            for i in range(3):
                proj3.ingest_bytes(record_id=f"ok{i}", payload=b"small", token_cost=10, fiber_ids=("f",), coverage_atoms=(f"a{i}",))
            fit = proj3.compile_task_packet(operation="SOLVE", question="q", budget_tokens=100, target_fibers=("f",))
            if fit.verdict is not TaskPacketVerdict.READY or len(fit.compile_report.selected_record_ids) != 3:
                return broke(f"records that fit were not READY: {fit.verdict} {fit.issues}", code_path="context_compiler")
        if rep.verdict is TaskPacketVerdict.READY:
            return broke(
                f"30 non-mandatory records under a 5-token budget -> TaskPacketVerdict.READY with "
                f"{len(cr.selected_record_ids)}/30 records selected, {len(cr.omitted_record_ids)} omitted, "
                f"compile reasons={tuple(cr.reasons)!r}, issues={tuple(rep.issues)!r}: a SOLVE packet with zero context is "
                f"handed out as READY and nothing in verdict/issues/reasons says why. The guard exists only for "
                f"mandatory records (5 mandatory records -> {rep2.verdict.value}, {tuple(rep2.issues)!r}). Omissions are "
                f"recorded in omitted_record_ids, so this is not invisible -- but it is not the fail-closed "
                f"compact/demote/CANNOT_COMPILE the row requires; it is READY-with-nothing.",
                code_path="rakl.project_runtime.RAKLProject.compile_task_packet -> context_compiler (non-mandatory "
                          "records dropped to fit budget without a verdict downgrade or a reason)")
    return held(f"context overflow -> BLOCK_NEW_WORK; index lag -> COMPACT (history preserved); missing obs -> CANNOT_CHECK; "
                f"30 records / 5-token budget -> {rep.verdict.value} {tuple(rep.issues)}; mandatory -> {rep2.verdict.value}; "
                f"records that fit -> READY",
                cross_ref="first execution BROKE here; fixed in context_compiler.compile_epistemic_context (context_over_budget)")


# =============================================================================
# Harness self-validation: two rows with a deliberately WEAKENED variant that must BROKE
# =============================================================================


def weakened_h04() -> Outcome:
    """A blob store that does NOT verify on read. The H04 attack must catch it."""

    class Unverified(LocalFilesystemBlobStore):
        def get_verified(self, digest):
            return self._path(digest).read_bytes()

        def exists_verified(self, digest):
            return self._path(digest).exists()

    with tempfile.TemporaryDirectory() as td:
        store = Unverified(Path(td))
        digest = store.put_if_absent(b"immutable evidence")
        store._path(digest).write_bytes(b"immutable evidenc3")
        try:
            store.get_verified(digest)
            return broke("mutated blob served as verified", code_path="weakened get_verified (control)")
        except EngineeringIntegrityError:
            return held("weakened store still caught it -- the control is broken")


def weakened_h06() -> Outcome:
    """A verifier that ignores the previous_record_hash link. Interior deletion must slip through -> BROKE."""
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "ep.jsonl"
        st = EpisodeStore(p)
        for i in range(4):
            st.append_substrate_node(node(i))
        lines = p.read_text().splitlines()
        del lines[1]
        # rewrite sequence_index and record_hash so ONLY the chain link betrays the deletion
        from rakl.episode_store import _record_hash
        fixed = []
        for i, line in enumerate(lines):
            rec = json.loads(line)
            rec["sequence_index"] = i
            rec.pop("record_hash")
            rec["record_hash"] = _record_hash(rec)
            fixed.append(json.dumps(rec, sort_keys=True, separators=(",", ":")))
        p.write_text("\n".join(fixed) + "\n")

        # weakened verifier: per-record hashes only, no link check
        def weak_verify(path):
            for i, line in enumerate(Path(path).read_text().splitlines()):
                rec = json.loads(line)
                if _record_hash(rec) != rec["record_hash"] or rec["sequence_index"] != i:
                    return "TAMPERED", i
            return "VALID", None

        weak = weak_verify(p)
        real = verify_episode_store(p)
        if weak[0] == "VALID" and real.verdict is ChainVerdict.TAMPERED and real.first_bad_index == 1:
            return broke(f"weakened verifier says VALID; real verifier TAMPERED@{real.first_bad_index}", code_path="weakened verifier (control)")
        return held(f"control failed: weak={weak} real={real.verdict.value}")


# =============================================================================


print("=" * 90)
print("HOSTILE TEST MATRIX EXECUTION V1 -- all 30 rows, frozen above, against the real code")
print("=" * 90)
case("H01", "kill during canonical blob write", h01)
case("H02", "blob committed, metadata transition killed before commit", h02)
case("H03", "metadata references unavailable blob", h03)
case("H04", "mutate stored blob bytes", h04)
case("H05", "torn episode JSONL tail", h05)
case("H06", "delete interior episode record", h06)
case("H07", "concurrent identical idempotency key, identical request", h07)
case("H08", "same idempotency key, different request", h08)
case("H09", "two writers plan on same project snapshot", h09)
case("H10", "stale controller decision replayed after semantic mutation", h10)
case("H11", "saturation certificate basis fingerprint changes", h11)
case("H12", "new native residual after bounded saturation", h12)
case("H13", "delete full-text/vector/graph index", h13)
case("H14", "corrupt derived index to return nonexistent atom", h14)
case("H15", "worker finishes external effect, crashes before completion record", h15)
case("H16", "duplicate activity delivery", h16)
case("H17", "DB failover mid-transition", h17)
case("H18", "object store temporary outage", h18)
case("H19", "restore backup into empty environment", h19)
case("H20", "point-in-time replay to older snapshot", h20)
case("H21", "partial schema migration", h21)
case("H22", "rollback after failed migration", h22)
case("H23", "secret rotation during worker lifetime", h23)
case("H24", "infrastructure admin submits unverified scientific promotion", h24)
case("H25", "malicious fabricated hard-gate ID in status", h25)
case("H26", "clock skew on worker", h26)
case("H27", "execution artifact rebuilt from different source but same label", h27)
case("H28", "audit/log exporter unavailable", h28)
case("H29", "high transaction contention", h29)
case("H30", "huge knowledge lattice + context request", h30)
print("-" * 90)
case("WEAKENED_H04", "unverified blob store must BROKE", weakened_h04, control=True, expect="BROKE")
case("WEAKENED_H06", "link-blind chain verifier must BROKE", weakened_h06, control=True, expect="BROKE")

counts = {"HELD": 0, "BROKE": 0, "CANNOT_CHECK": 0}
scopes = {"FULL": 0, "LOCAL_REFERENCE_ONLY": 0}
for r in RESULTS:
    counts[r["verdict"]] += 1
    if r["verdict"] == "HELD":
        scopes[r["scope"]] += 1
print("=" * 90)
print(f"rows: {len(RESULTS)}   HELD={counts['HELD']} (full={scopes['FULL']}, local-reference-only={scopes['LOCAL_REFERENCE_ONLY']})"
      f"   BROKE={counts['BROKE']}   CANNOT_CHECK={counts['CANNOT_CHECK']}")
print(f"controls: {sum(1 for c in CONTROLS if c['ok'])}/{len(CONTROLS)} weakened variants BROKE as required")
for r in RESULTS:
    if r["verdict"] == "BROKE":
        print(f"  BROKE {r['row']}: {r['code_path']}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "schema_version": "orion-hostile-matrix-execution-v1",
    "matrix": "HOSTILE_TEST_MATRIX.md",
    "status": "FROZEN_ROWS_EXECUTED__ALL_OUTCOMES_PRESERVED",
    "grants_scientific_authority": False,
    "rows_specified": 30,
    "rows_executed": len(RESULTS),
    "counts": counts,
    "held_scope": scopes,
    "harness_self_validation": {"controls": CONTROLS, "all_broke_as_required": all(c["ok"] for c in CONTROLS)},
    "results": RESULTS,
    "cross_reference_policy": (
        "Rows previously touched by the A01..A12 campaign (run_hostile_assurance_v3.py) are RE-EXECUTED here against "
        "the row's own mechanism; where the A-case is cited it is as context, never as the evidence for this row."),
    "not_claimed": [
        "an independently executed pass on an exact production release",
        "distributed exactly-once across external effects",
        "any production latency/resource envelope (H29 numbers are local SQLite)",
        "a real PostgreSQL failover (H17), object-store network outage (H18) -- local stand-ins only",
    ],
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(f"wrote {OUT}")
