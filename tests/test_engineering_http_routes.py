"""E10 — the twelve routes API_AND_OBSERVATORY.md names, each over the live socket.

For every route: it exists (never 404 NOT_FOUND), it is auth-gated (401 without a
token, 403 for an actor on the wrong project), and its response has the documented
shape. Every mutation returns a `StateTransitionReceipt` — asserted on COMMITTED,
RETRY_REQUIRED, ABORTED, RECOVERY_REQUIRED and CANNOT_CHECK, and round-tripped
through `StateTransitionReceipt.from_dict`. The 16-thread same-key race that
produced 16 commits against the old in-memory service is pinned to exactly one.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import urllib.error
import urllib.request

import pytest

from rakl.engineering_atomic import SqliteAtomicEngineeringCoordinator
from rakl.engineering_blob import LocalFilesystemBlobStore
from rakl.engineering_http import (
    Actor,
    Capability,
    EngineeringHttpService,
    IdentityProvider,
    SecretStore,
    SpanExporter,
    Telemetry,
    content_hash,
    serve,
)
from rakl.engineering_state import (
    EpistemicAxisStatus,
    EpistemicStatus,
    NextActionClass,
    StateTransitionReceipt,
    TransitionStatus,
)

ROUTES = [
    ("POST", "/v1/projects"),
    ("GET", "/v1/projects/p1/head"),
    ("GET", "/v1/projects/p1/snapshots/{snapshot}"),
    ("POST", "/v1/projects/p1/evidence"),
    ("POST", "/v1/projects/p1/research-rounds"),
    ("GET", "/v1/projects/p1/epistemic-status?snapshot={snapshot}&target=t&fiber=f"),
    ("POST", "/v1/projects/p1/actions:plan"),
    ("POST", "/v1/projects/p1/actions:execute"),
    ("GET", "/v1/projects/p1/transitions/{transition}"),
    ("GET", "/v1/projects/p1/decisions/{decision}"),
    ("GET", "/v1/projects/p1/runs/{invocation}"),
    ("GET", "/v1/projects/p1/provenance/{evidence_id}"),
]


def call(base, method, path, *, token=None, body=None, trace=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + path, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if trace:
        req.add_header("X-Trace-Id", trace)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read()), dict(r.headers)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read()), dict(e.headers)


def mutation(payload, *, key, expected):
    return {"idempotency_key": key, "expected_snapshot_id": expected, "payload": payload,
            "payload_hash": content_hash(payload)}


def as_receipt(body: dict) -> StateTransitionReceipt:
    """A response is a receipt iff the canonical dataclass round-trips it and re-derives the same id."""

    receipt = StateTransitionReceipt.from_dict(body)
    assert receipt.transition_id == body["transition_id"]
    assert body["status"] in {s.value for s in TransitionStatus}
    assert "error" not in body
    return receipt


@pytest.fixture()
def world(tmp_path):
    idp, secrets, exporter = IdentityProvider(), SecretStore(), SpanExporter()
    coordinator = SqliteAtomicEngineeringCoordinator(tmp_path / "orion.sqlite3")
    blobs = LocalFilesystemBlobStore(tmp_path / "blobs")
    service = EngineeringHttpService(idp=idp, secrets=secrets, telemetry=Telemetry(exporter),
                                     coordinator=coordinator, blob_store=blobs)
    server = serve(service)
    base = f"http://127.0.0.1:{server.server_address[1]}"
    admin = idp.issue(Actor("root", frozenset({"p1"}), frozenset(Capability)))
    reader = idp.issue(Actor("bob", frozenset({"p1"}), frozenset({Capability.READ_EVIDENCE})))
    other = idp.issue(Actor("carol", frozenset({"p2"}), frozenset(Capability)))
    status, created, _ = call(base, "POST", "/v1/projects", token=admin, body={"project_id": "p1"})
    assert status == 201 and created["created"] is True
    w = {"base": base, "svc": service, "exporter": exporter, "admin": admin, "reader": reader, "other": other,
         "genesis": created["snapshot"]["snapshot_id"], "coordinator": coordinator}
    try:
        yield w
    finally:
        server.shutdown()


def head(w):
    _, snap, _ = call(w["base"], "GET", "/v1/projects/p1/head", token=w["admin"])
    return snap


def record_status(w, *, target="t", fiber="f"):
    snapshot_id = head(w)["snapshot_id"]
    status = EpistemicStatus(
        project_snapshot_id=snapshot_id, target_id=target, fiber_id=fiber,
        axis_statuses=(EpistemicAxisStatus("KNOWLEDGE", True, 0, ("FOUNDATIONAL",)),),
        required_routes=("FOUNDATIONAL",), covered_routes=("FOUNDATIONAL",), missing_routes=(),
        active_residual_ids=(), freshness_stale=False, required_authority=0, available_support_paths=1,
        blocking_cut_ids=(), hard_gate_ids=("bounded_saturation_gate",),
        next_action=NextActionClass.COMPILE_SOLVER_VIEW, reasons=("route_test_known_world",),
        metric_receipt_ids=("metric:route:1",), basis_fingerprints=("basis:route:1",),
    )
    w["coordinator"].state.record_epistemic_status(status)
    return status


def ingest(w, payload, *, key, expected=None):
    return call(w["base"], "POST", "/v1/projects/p1/evidence", token=w["admin"],
                body=mutation(payload, key=key, expected=expected or head(w)["snapshot_id"]))


def research_round(w, *, key, expected=None, atoms=None):
    payload = {
        "new_fibers": [{"fiber_id": "fiber:route"}],
        "atom_versions": atoms if atoms is not None else [
            {"atom_id": "atom:a", "fiber_id": "fiber:route", "kind": "MECHANISM_NODE", "label": "atom a",
             "evidence_ids": ["e:1"], "payload": {"v": 1}},
        ],
    }
    return call(w["base"], "POST", "/v1/projects/p1/research-rounds", token=w["admin"],
                body=mutation(payload, key=key, expected=expected or head(w)["snapshot_id"]))


def plan(w, *, target="t", fiber="f"):
    return call(w["base"], "POST", "/v1/projects/p1/actions:plan", token=w["admin"],
                body={"target": target, "fiber": fiber})


def execute(w, decision_id, *, key, expected=None, **spec):
    payload = {"decision_id": decision_id, "invocation_id": f"invocation:{key}", **spec}
    return call(w["base"], "POST", "/v1/projects/p1/actions:execute", token=w["admin"],
                body=mutation(payload, key=key, expected=expected or head(w)["snapshot_id"]))


def full_world(w):
    """Drive every mutation once so every read route has something real to return."""

    s, ev, _ = ingest(w, {"records": [{"logical_record_id": "src:1", "content": {"k": 1}, "source_identity": "src"}]},
                      key="ev-1")
    assert s == 200, ev
    s, rr, _ = research_round(w, key="rr-1")
    assert s == 200, rr
    record_status(w)
    s, pl, _ = plan(w)
    assert s == 200, pl
    s, ex, _ = execute(w, pl["decision_id"], key="ex-1")
    assert s == 200, ex
    return {"evidence": ev, "round": rr, "plan": pl, "execute": ex,
            "evidence_id": ev["produced_artifact_ids"][0], "snapshot": rr["after_snapshot_id"],
            "transition": rr["transition_id"], "decision": pl["decision_id"], "invocation": "invocation:ex-1"}


def bind(path: str, ids: dict) -> str:
    for k, v in ids.items():
        if isinstance(v, str):
            path = path.replace("{" + k + "}", v)
    return path


# --- the twelve routes: exist, auth-gated ---------------------------------------


@pytest.mark.parametrize("method,template", ROUTES)
def test_route_exists_and_is_auth_gated(world, method, template) -> None:
    ids = full_world(world)
    path = bind(template, ids)
    body = {"project_id": "p1"} if path == "/v1/projects" else (mutation({}, key="x", expected=ids["snapshot"]) if method == "POST" else None)
    # no token: 401 before anything else
    s0, b0, _ = call(world["base"], method, path, body=body)
    assert s0 == 401 and b0["error"] == "UNAUTHENTICATED", (method, path, s0, b0)
    # wrong project, every capability: 403
    s1, b1, _ = call(world["base"], method, path, token=world["other"], body=body)
    assert s1 == 403 and b1["error"] == "FORBIDDEN", (method, path, s1, b1)
    # right actor: whatever it returns, it is NOT an unknown route
    s2, b2, h2 = call(world["base"], method, path, token=world["admin"], body=body)
    assert not (s2 == 404 and b2.get("error") == "NOT_FOUND"), (method, path, s2, b2)
    assert h2["X-Api-Version"] == "v1" and h2["X-Trace-Id"]


@pytest.mark.parametrize("path", ["/v1/projects/p1/evidence", "/v1/projects/p1/research-rounds",
                                  "/v1/projects/p1/actions:execute", "/v1/projects/p1/actions:plan"])
def test_reader_cannot_reach_any_mutating_or_governing_route(world, path) -> None:
    s, b, _ = call(world["base"], "POST", path, token=world["reader"],
                   body=mutation({}, key="x", expected=world["genesis"]))
    assert s == 403 and b["error"] == "FORBIDDEN"


# --- shapes, route by route -----------------------------------------------------------


def test_create_project_is_genesis_and_idempotent(world) -> None:
    s, again, _ = call(world["base"], "POST", "/v1/projects", token=world["admin"], body={"project_id": "p1"})
    assert s == 200 and again["created"] is False
    assert again["snapshot"]["snapshot_id"] == world["genesis"]
    assert again["snapshot"]["sequence"] == 0 and again["snapshot"]["previous_snapshot_id"] is None
    s2, conflict, _ = call(world["base"], "POST", "/v1/projects", token=world["admin"],
                           body={"project_id": "p1", "metric_ledger_head": "metric:other"})
    assert s2 == 409 and conflict["error"] == "PROJECT_ALREADY_INITIALIZED"
    s3, missing, _ = call(world["base"], "POST", "/v1/projects", token=world["admin"], body={})
    assert s3 == 400 and missing["error"] == "INVALID_REQUEST"


def test_head_and_snapshots_read_the_real_store(world) -> None:
    ids = full_world(world)
    h = head(world)
    assert h["sequence"] == 3 and h["snapshot_id"].startswith("snapshot:")
    assert h["snapshot_id"] == world["coordinator"].state.head("p1").snapshot_id
    s, snap, _ = call(world["base"], "GET", f"/v1/projects/p1/snapshots/{ids['snapshot']}", token=world["admin"])
    assert s == 200 and snap["snapshot_id"] == ids["snapshot"] and snap["sequence"] == 2
    s, nope, _ = call(world["base"], "GET", "/v1/projects/p1/snapshots/snapshot:nope", token=world["admin"])
    assert s == 404 and nope["error"] == "UNKNOWN_SNAPSHOT"
    s, unknown, _ = call(world["base"], "GET", "/v1/projects/p9/head", token=world["other"])
    assert s == 403  # carol is on p2, not p9
    s, uninit, _ = call(world["base"], "GET", "/v1/projects/p2/head", token=world["other"])
    assert s == 404 and uninit["error"] == "PROJECT_NOT_INITIALIZED"


def test_evidence_mutation_returns_committed_receipt_and_stores_bytes(world) -> None:
    s, body, _ = ingest(world, {"records": [{"logical_record_id": "src:1", "content_utf8": "raw source text",
                                              "source_identity": "src", "provenance": {"kind": "SOURCE"}}]}, key="ev")
    assert s == 200
    receipt = as_receipt(body)
    assert receipt.status is TransitionStatus.COMMITTED and receipt.action == "INGEST_EVIDENCE"
    assert receipt.after_snapshot_id == head(world)["snapshot_id"]
    assert body["replayed"] is False and body["persisted"] is True
    assert body["client_payload_hash"] != body["action_payload_hash"]  # API binding vs store binding
    evidence_id = receipt.produced_artifact_ids[0]
    s, prov, _ = call(world["base"], "GET", f"/v1/projects/p1/provenance/{evidence_id}", token=world["admin"])
    assert s == 200 and prov["kind"] == "EVIDENCE_RECORD"
    assert prov["record"]["logical_record_id"] == "src:1"
    assert prov["blob"]["verified"] is True and prov["blob"]["raw_bytes"] == len(b"raw source text")
    assert prov["committed_snapshot_id"] == receipt.after_snapshot_id
    # the same record by logical id
    s, prov2, _ = call(world["base"], "GET", "/v1/projects/p1/provenance/src:1", token=world["admin"])
    assert s == 200 and prov2["record"]["evidence_id"] == evidence_id


def test_research_round_commits_semantic_batch_atomically_with_the_head(world) -> None:
    before = head(world)
    s, body, _ = research_round(world, key="rr")
    assert s == 200
    receipt = as_receipt(body)
    assert receipt.status is TransitionStatus.COMMITTED and receipt.action == "UPDATE_SEMANTIC_ATLAS"
    after = head(world)
    assert after["semantic_state_revision"] != before["semantic_state_revision"]
    assert after["evidence_cutoff"] == before["evidence_cutoff"]
    assert world["coordinator"].semantic.semantic_revision(after["sequence"]) == after["semantic_state_revision"]
    assert receipt.produced_artifact_ids and receipt.produced_artifact_ids[0].startswith("atom-version:")


def test_research_round_that_the_store_refuses_is_an_aborted_receipt(world) -> None:
    """An atom on a fiber the batch does not carry: EngineeringIntegrityError -> ABORTED receipt, persisted."""

    s, body, _ = research_round(world, key="rr-bad", atoms=[
        {"atom_id": "atom:x", "fiber_id": "fiber:missing", "kind": "K", "label": "x"}])
    assert s == 422
    receipt = as_receipt(body)
    assert receipt.status is TransitionStatus.ABORTED and receipt.after_snapshot_id is None
    assert any(r.startswith("store_refused:") for r in receipt.reasons)
    assert body["persisted"] is True
    assert head(world)["sequence"] == 0  # nothing moved
    s2, again, _ = call(world["base"], "GET", f"/v1/projects/p1/transitions/{receipt.transition_id}", token=world["admin"])
    assert s2 == 200 and again["status"] == "ABORTED"


def test_empty_research_round_is_a_typed_400(world) -> None:
    s, body, _ = call(world["base"], "POST", "/v1/projects/p1/research-rounds", token=world["admin"],
                      body=mutation({}, key="rr-empty", expected=world["genesis"]))
    assert s == 400 and body["error"] == "INVALID_REQUEST"


def test_epistemic_status_parses_the_query_string_and_returns_the_canonical_object(world) -> None:
    status = record_status(world)
    snap = head(world)["snapshot_id"]
    s, body, _ = call(world["base"], "GET", f"/v1/projects/p1/epistemic-status?snapshot={snap}&target=t&fiber=f",
                      token=world["admin"])
    assert s == 200
    assert body["status_id"] == status.status_id
    assert EpistemicStatus.from_dict(body).status_id == status.status_id
    assert body["axis_statuses"][0]["axis"] == "KNOWLEDGE"
    assert not any(k in body for k in ("saturation_percent", "saturation_score", "score"))
    # head form (no snapshot) resolves the same object
    s2, body2, _ = call(world["base"], "GET", "/v1/projects/p1/epistemic-status?target=t&fiber=f", token=world["admin"])
    assert s2 == 200 and body2["status_id"] == status.status_id
    # missing coordinates / unknown coordinates are typed
    s3, b3, _ = call(world["base"], "GET", "/v1/projects/p1/epistemic-status?target=t", token=world["admin"])
    assert s3 == 400 and b3["error"] == "INVALID_REQUEST"
    s4, b4, _ = call(world["base"], "GET", "/v1/projects/p1/epistemic-status?target=t&fiber=other", token=world["admin"])
    assert s4 == 404 and b4["error"] == "NOT_FOUND"


def test_plan_records_a_decision_bound_to_the_head_and_is_readable(world) -> None:
    s0, b0, _ = plan(world)
    assert s0 == 409 and b0["error"] == "CANNOT_CHECK"  # no status yet: refuses, does not invent
    status = record_status(world)
    s, body, _ = plan(world)
    assert s == 200 and body["decision_id"].startswith("decision:")
    assert body["plan"]["status_id"] == status.status_id
    assert body["plan"]["next_action"] == "COMPILE_SOLVER_VIEW"
    assert body["grants_scientific_authority"] is False
    s2, again, _ = plan(world)
    assert s2 == 200 and again["decision_id"] == body["decision_id"]  # deterministic
    s3, dec, _ = call(world["base"], "GET", f"/v1/projects/p1/decisions/{body['decision_id']}", token=world["admin"])
    assert s3 == 200 and dec["kind"] == "CONTROLLER_DECISION"
    assert dec["canonical_payload"] == body["plan"] and dec["project_snapshot_id"] == status.project_snapshot_id
    assert dec["source_receipt_ids"] == ["metric:route:1"]
    s4, nope, _ = call(world["base"], "GET", "/v1/projects/p1/decisions/decision:nope", token=world["admin"])
    assert s4 == 404 and nope["error"] == "NOT_FOUND"


def test_execute_commits_a_metadata_transition_and_schedules_a_durable_run(world) -> None:
    record_status(world)
    _, pl, _ = plan(world)
    before = head(world)
    s, body, _ = execute(world, pl["decision_id"], key="ex", retry_safe=True)
    assert s == 200
    receipt = as_receipt(body)
    assert receipt.status is TransitionStatus.COMMITTED and receipt.action == "EXECUTE_CONTROLLER_DECISION"
    after = head(world)
    assert after["sequence"] == before["sequence"] + 1
    assert after["controller_epoch_id"] != before["controller_epoch_id"]
    assert after["semantic_state_revision"] == before["semantic_state_revision"]
    assert body["run_scheduled"] is True and body["invocation_id"] == "invocation:ex"
    s2, run, _ = call(world["base"], "GET", "/v1/projects/p1/runs/invocation:ex", token=world["admin"])
    assert s2 == 200
    assert run["workflow"]["project_snapshot_id"] == receipt.after_snapshot_id
    assert run["activity"]["status"] == "SCHEDULED" and run["activity"]["spec"]["retry_safe"] is True
    assert run["history_intact"] is True and [e["kind"] for e in run["events"]] == ["WORKFLOW_STARTED", "ACTIVITY_SCHEDULED"]
    # replay: same receipt, no second run
    s3, again, _ = execute(world, pl["decision_id"], key="ex", expected=before["snapshot_id"], retry_safe=True)
    assert s3 == 200 and again["replayed"] is True and again["transition_id"] == receipt.transition_id
    assert head(world)["sequence"] == after["sequence"]
    # same key, different activity spec: conflict, not a silent second run
    s4, conflict, _ = execute(world, pl["decision_id"], key="ex", expected=before["snapshot_id"], retry_safe=False)
    assert s4 == 409 and conflict["error"] == "IDEMPOTENCY_CONFLICT"
    s5, nope, _ = call(world["base"], "GET", "/v1/projects/p1/runs/invocation:nope", token=world["admin"])
    assert s5 == 404 and nope["error"] == "NOT_FOUND"


def test_execute_of_a_decision_not_bound_to_the_expected_snapshot_is_aborted(world) -> None:
    s, body, _ = execute(world, "decision:unbound", key="ex-bad")
    assert s == 422
    receipt = as_receipt(body)
    assert receipt.status is TransitionStatus.ABORTED
    assert receipt.reasons == ("decision_not_bound_to_expected_snapshot:decision:unbound",)
    assert head(world)["sequence"] == 0
    assert "run_scheduled" not in body


def test_transitions_route_reads_by_id_and_by_idempotency_key(world) -> None:
    ids = full_world(world)
    s, by_id, _ = call(world["base"], "GET", f"/v1/projects/p1/transitions/{ids['transition']}", token=world["admin"])
    s2, by_key, _ = call(world["base"], "GET", "/v1/projects/p1/transitions/rr-1", token=world["admin"])
    assert s == s2 == 200 and by_id["transition_id"] == by_key["transition_id"] == ids["transition"]
    assert as_receipt(by_id).status is TransitionStatus.COMMITTED
    s3, nope, _ = call(world["base"], "GET", "/v1/projects/p1/transitions/transition:nope", token=world["admin"])
    assert s3 == 404 and nope["error"] == "NOT_FOUND"


def test_provenance_resolves_evidence_transitions_and_decisions(world) -> None:
    ids = full_world(world)
    for entity, kind in ((ids["evidence_id"], "EVIDENCE_RECORD"), (ids["transition"], "TRANSITION_RECEIPT"),
                         (ids["decision"], "CONTROLLER_DECISION")):
        s, body, _ = call(world["base"], "GET", f"/v1/projects/p1/provenance/{entity}", token=world["admin"])
        assert s == 200 and body["kind"] == kind, (entity, body)
    s, listing, _ = call(world["base"], "GET", "/v1/projects/p1/provenance", token=world["admin"])
    assert s == 200 and [r["logical_record_id"] for r in listing["evidence"]] == ["src:1"]
    s, nope, _ = call(world["base"], "GET", "/v1/projects/p1/provenance/nothing", token=world["admin"])
    assert s == 404 and nope["error"] == "NOT_FOUND"


# --- receipts on the non-COMMITTED terminals ------------------------------------------


def test_stale_snapshot_is_a_retry_required_receipt_on_every_mutation_route(world) -> None:
    genesis = world["genesis"]
    s, first, _ = ingest(world, {"a": 1}, key="first", expected=genesis)
    assert s == 200
    record_status(world)
    _, pl, _ = plan(world)
    stale = [
        ingest(world, {"b": 2}, key="stale-ev", expected=genesis),
        research_round(world, key="stale-rr", expected=genesis),
        execute(world, pl["decision_id"], key="stale-ex", expected=genesis),
    ]
    for status_code, body, _ in stale:
        assert status_code == 409, body
        receipt = as_receipt(body)
        assert receipt.status is TransitionStatus.RETRY_REQUIRED
        assert receipt.before_snapshot_id == genesis and receipt.after_snapshot_id is None
        assert receipt.reasons == ("stale_before_snapshot_replan_on_current_head",)
        assert body["head_snapshot_id"] == first["after_snapshot_id"]
    assert head(world)["sequence"] == 1


def test_store_error_after_dispatch_is_a_persisted_recovery_required_receipt(world, monkeypatch) -> None:
    """The store threw mid-commit: the effect is ambiguous, so RECOVERY_REQUIRED, and it is durable."""

    def boom(*a, **k):
        raise sqlite3.OperationalError("database is locked")

    monkeypatch.setattr(world["svc"].coordinator, "commit_evidence_transition", boom)
    s, body, _ = ingest(world, {"a": 1}, key="rec")
    assert s == 503
    receipt = as_receipt(body)
    assert receipt.status is TransitionStatus.RECOVERY_REQUIRED and body["persisted"] is True
    assert receipt.reasons == ("store_error_after_dispatch:OperationalError",)
    monkeypatch.undo()
    s2, again, _ = call(world["base"], "GET", f"/v1/projects/p1/transitions/{receipt.transition_id}", token=world["admin"])
    assert s2 == 200 and again["status"] == "RECOVERY_REQUIRED"


def test_unreachable_store_is_a_cannot_check_receipt_flagged_unpersisted(world, monkeypatch) -> None:
    def boom(*a, **k):
        raise sqlite3.OperationalError("disk I/O error")

    monkeypatch.setattr(world["svc"].coordinator, "commit_evidence_transition", boom)
    monkeypatch.setattr(world["svc"].facade, "record_recovery_required", boom)
    s, body, _ = ingest(world, {"a": 1}, key="cc")
    assert s == 503
    receipt = as_receipt(body)
    assert receipt.status is TransitionStatus.CANNOT_CHECK
    assert body["persisted"] is False
    assert any(r.startswith("store_unreachable:") for r in receipt.reasons)
    assert any(r.startswith("receipt_not_persisted:") for r in receipt.reasons)


# --- the race that produced 16 commits against the old service ------------------------


def _hammer(w, bodies):
    results: list[tuple[int, dict]] = []
    lock = threading.Lock()

    def one(body):
        s, b, _ = call(w["base"], "POST", "/v1/projects/p1/evidence", token=w["admin"], body=body)
        with lock:
            results.append((s, b))

    threads = [threading.Thread(target=one, args=(b,)) for b in bodies]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    return results


def test_sixteen_threads_one_key_one_expected_snapshot_commit_exactly_once(world) -> None:
    body = mutation({"same": "payload"}, key="one-key", expected=world["genesis"])
    results = _hammer(world, [body] * 16)
    assert len(results) == 16
    assert all(s == 200 for s, _ in results), [(s, b.get("error"), b.get("status")) for s, b in results]
    committed = [b for _, b in results if b["status"] == "COMMITTED"]
    assert len(committed) == 16 and all("error" not in b for b in committed)
    assert len({b["after_snapshot_id"] for b in committed}) == 1
    assert len({b["transition_id"] for b in committed}) == 1
    fresh = [b for b in committed if b["replayed"] is False]
    assert len(fresh) == 1 and sum(1 for b in committed if b["replayed"]) == 15
    h = head(world)
    assert h["sequence"] == 1 and h["snapshot_id"] == committed[0]["after_snapshot_id"]
    with sqlite3.connect(world["coordinator"].path) as db:
        assert db.execute("SELECT COUNT(*) FROM transitions WHERE project_id='p1'").fetchone()[0] == 1


def test_sixteen_threads_distinct_keys_same_expected_snapshot_commit_once_and_retry_fifteen(world) -> None:
    bodies = [mutation({"n": i}, key=f"key-{i}", expected=world["genesis"]) for i in range(16)]
    results = _hammer(world, bodies)
    statuses = sorted(b["status"] for _, b in results)
    assert statuses.count("COMMITTED") == 1 and statuses.count("RETRY_REQUIRED") == 15, statuses
    for s, b in results:
        as_receipt(b)
        assert s == (200 if b["status"] == "COMMITTED" else 409)
    assert head(world)["sequence"] == 1


# --- no in-memory state -----------------------------------------------------------------


def test_service_holds_no_project_state_of_its_own(world) -> None:
    svc = world["svc"]
    assert not hasattr(svc, "projects") and not hasattr(svc, "_advance")
    ingest(world, {"a": 1}, key="k")
    # a second service over the SAME stores sees the same head: the store is the state
    twin = EngineeringHttpService(idp=svc.idp, secrets=svc.secrets, coordinator=svc.coordinator, blob_store=svc.blobs)
    assert twin.state.head("p1").snapshot_id == head(world)["snapshot_id"]
