"""E10 (API contract), E12 (telemetry correlation), E13 (auth/secrets) — over a live HTTP server.

Every test hits the real ThreadingHTTPServer over a socket, not the handler
in-process, so the contract is tested at the boundary a client actually sees.

The service is wired to REAL stores (an atomic coordinator over SQLite plus a
filesystem blob store), so snapshot ids are content hashes and mutations
return `StateTransitionReceipt`s. Route-by-route contract tests for the twelve
documented routes live in tests/test_engineering_http_routes.py.
"""

from __future__ import annotations

import json
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
from rakl.engineering_state import StateTransitionReceipt


@pytest.fixture()
def world(tmp_path):
    idp = IdentityProvider()
    secrets = SecretStore()
    exporter = SpanExporter()
    coordinator = SqliteAtomicEngineeringCoordinator(tmp_path / "orion.sqlite3")
    blobs = LocalFilesystemBlobStore(tmp_path / "blobs")
    service = EngineeringHttpService(idp=idp, secrets=secrets, telemetry=Telemetry(exporter),
                                     coordinator=coordinator, blob_store=blobs)
    server = serve(service)
    base = f"http://127.0.0.1:{server.server_address[1]}"

    writer = idp.issue(Actor("alice", frozenset({"p1"}), frozenset({Capability.READ_EVIDENCE, Capability.WRITE_EVIDENCE})))
    reader = idp.issue(Actor("bob", frozenset({"p1"}), frozenset({Capability.READ_EVIDENCE})))
    other = idp.issue(Actor("carol", frozenset({"p2"}), frozenset(Capability)))  # all caps, wrong project
    admin = idp.issue(Actor("root", frozenset({"p1"}), frozenset(Capability)))
    status, created, _ = call(base, "POST", "/v1/projects", token=admin, body={"project_id": "p1"})
    assert status == 201, created
    try:
        yield {"base": base, "svc": service, "exporter": exporter, "secrets": secrets,
               "writer": writer, "reader": reader, "other": other, "admin": admin,
               "head": created["snapshot"]["snapshot_id"]}
    finally:
        server.shutdown()


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


def mutation(payload, *, key="k1", expected="snapshot:never-existed", hash_override=None):
    """The default ``expected`` names no snapshot; successful paths must pass the real head."""

    return {"idempotency_key": key, "expected_snapshot_id": expected, "payload": payload,
            "payload_hash": hash_override or content_hash(payload)}


def head_of(world):
    _, snap, _ = call(world["base"], "GET", "/v1/projects/p1/head", token=world["admin"])
    return snap["snapshot_id"]


# --- E13: authentication and authorization ---------------------------------


def test_no_token_is_unauthenticated(world) -> None:
    status, body, _ = call(world["base"], "GET", "/v1/projects/p1/snapshot")
    assert status == 401 and body["error"] == "UNAUTHENTICATED"


def test_reader_cannot_write(world) -> None:
    status, body, _ = call(world["base"], "POST", "/v1/projects/p1/evidence",
                           token=world["reader"], body=mutation({"x": 1}))
    assert status == 403 and body["error"] == "FORBIDDEN"


def test_tenant_isolation_all_caps_on_wrong_project_is_forbidden(world) -> None:
    status, body, _ = call(world["base"], "GET", "/v1/projects/p1/snapshot", token=world["other"])
    assert status == 403


def test_even_admin_cannot_write_the_authority_projection(world) -> None:
    _, before, _ = call(world["base"], "GET", "/v1/projects/p1/snapshot", token=world["admin"])
    status, body, _ = call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["admin"],
                           body=mutation({"authority_projection_revision": "auth-99"}, expected=world["head"]))
    assert status == 403 and body["error"] == "AUTHORITY_PROJECTION_IMMUTABLE"
    s2, snap, _ = call(world["base"], "GET", "/v1/projects/p1/snapshot", token=world["admin"])
    assert snap["authority_projection_revision"] == before["authority_projection_revision"]
    assert snap["snapshot_id"] == before["snapshot_id"]  # nothing moved
    # nor at genesis
    s3, body3, _ = call(world["base"], "POST", "/v1/projects", token=world["admin"],
                        body={"project_id": "p1", "authority_projection_revision": "auth-99"})
    assert s3 == 403 and body3["error"] == "AUTHORITY_PROJECTION_IMMUTABLE"


def test_secrets_enter_receipts_by_reference_only(world) -> None:
    world["secrets"].put("db_password", "hunter2")
    status, body, _ = call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"],
                           body=mutation({"secret_names": ["db_password"], "note": "uses the db"}, expected=world["head"]))
    assert status == 200 and body["status"] == "COMMITTED"
    assert "hunter2" not in json.dumps(body)
    _, prov, _ = call(world["base"], "GET", "/v1/projects/p1/provenance", token=world["writer"])
    text = json.dumps(prov)
    assert "hunter2" not in text
    assert "secret://db_password@v1" in text
    # rotation bumps the reference; the old value never appears
    world["secrets"].put("db_password", "hunter3")
    assert world["secrets"].reference("db_password") == "secret://db_password@v2"


# --- E10: the mutation contract --------------------------------------------


def test_mutation_without_idempotency_key_is_typed_400(world) -> None:
    body = mutation({"x": 1}); del body["idempotency_key"]
    status, resp, _ = call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"], body=body)
    assert status == 400 and resp["error"] == "MISSING_IDEMPOTENCY_KEY"


def test_mutation_without_expected_snapshot_is_typed_400(world) -> None:
    body = mutation({"x": 1}); del body["expected_snapshot_id"]
    status, resp, _ = call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"], body=body)
    assert status == 400 and resp["error"] == "MISSING_EXPECTED_SNAPSHOT"


def test_payload_hash_must_bind_the_payload(world) -> None:
    status, resp, _ = call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"],
                           body=mutation({"x": 1}, hash_override="deadbeef"))
    assert status == 400 and resp["error"] == "PAYLOAD_HASH_MISMATCH"


def test_stale_snapshot_is_409_and_names_the_head(world) -> None:
    """Staleness is a RETRY_REQUIRED *receipt* from the store, not an error dict."""

    genesis = world["head"]
    s1, r1, _ = call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"],
                     body=mutation({"a": 1}, key="k1", expected=genesis))
    assert s1 == 200
    status, resp, _ = call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"],
                           body=mutation({"b": 2}, key="k2", expected=genesis))
    assert status == 409
    assert "error" not in resp
    assert resp["status"] == "RETRY_REQUIRED"
    assert resp["before_snapshot_id"] == genesis and resp["after_snapshot_id"] is None
    assert resp["head_snapshot_id"] == r1["after_snapshot_id"] == head_of(world)
    receipt = StateTransitionReceipt.from_dict(resp)   # round-trips as a real receipt
    assert receipt.transition_id == resp["transition_id"]
    assert resp["persisted"] is True
    # and it is durable: readable back by id
    s3, again, _ = call(world["base"], "GET", f"/v1/projects/p1/transitions/{resp['transition_id']}", token=world["writer"])
    assert s3 == 200 and again["status"] == "RETRY_REQUIRED"


def test_expected_snapshot_that_never_existed_is_a_typed_4xx_not_a_receipt(world) -> None:
    status, resp, _ = call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"],
                           body=mutation({"a": 1}))
    assert status == 404 and resp["error"] == "UNKNOWN_SNAPSHOT"


def test_idempotent_replay_returns_the_same_result_and_does_not_advance(world) -> None:
    s1, r1, _ = call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"],
                     body=mutation({"a": 1}, expected=world["head"]))
    s2, r2, _ = call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"],
                     body=mutation({"a": 1}, expected=world["head"]))
    assert s1 == s2 == 200
    assert r1["status"] == r2["status"] == "COMMITTED"
    assert r1["after_snapshot_id"] == r2["after_snapshot_id"]
    assert r1["transition_id"] == r2["transition_id"]
    assert r1.get("replayed") is False and r2.get("replayed") is True
    _, snap, _ = call(world["base"], "GET", "/v1/projects/p1/snapshot", token=world["writer"])
    assert snap["sequence"] == 1 and snap["snapshot_id"] == r1["after_snapshot_id"]


def test_same_key_different_payload_is_a_conflict(world) -> None:
    call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"],
         body=mutation({"a": 1}, key="k1", expected=world["head"]))
    status, resp, _ = call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"],
                           body=mutation({"a": 2}, key="k1", expected=world["head"]))
    assert status == 409 and resp["error"] == "IDEMPOTENCY_CONFLICT"


def test_errors_are_typed_and_versioned(world) -> None:
    status, resp, headers = call(world["base"], "GET", "/v1/projects/p1/nope", token=world["writer"])
    assert status == 404
    assert resp["api_version"] == "v1"
    assert headers["X-Api-Version"] == "v1"


# --- E12: telemetry correlation -------------------------------------------


def test_every_response_carries_a_trace_id_and_echoes_a_supplied_one(world) -> None:
    _, _, h1 = call(world["base"], "GET", "/v1/projects/p1/snapshot", token=world["writer"])
    assert h1["X-Trace-Id"]
    _, _, h2 = call(world["base"], "GET", "/v1/projects/p1/snapshot", token=world["writer"], trace="abc123")
    assert h2["X-Trace-Id"] == "abc123"


def test_spans_carry_project_snapshot_actor_and_idempotency_context(world) -> None:
    call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["writer"],
         body=mutation({"a": 1}, expected=world["head"]), trace="t-xyz")
    spans = [s for s in world["exporter"].spans if s.trace_id == "t-xyz"]
    assert spans
    attrs = spans[0].attributes
    assert attrs["project.id"] == "p1"
    assert attrs["actor.id"] == "alice"
    assert attrs["idempotency.key"] == "k1"
    assert attrs["snapshot.id"] == world["head"]
    assert attrs["transition.status"] == "COMMITTED"
    assert attrs["receipt.id"].startswith("transition:")
    assert spans[0].to_otlp_dict()["traceId"] == "t-xyz"


def test_a_failed_request_produces_an_error_span_with_the_typed_code(world) -> None:
    call(world["base"], "POST", "/v1/projects/p1/evidence", token=world["reader"],
         body=mutation({"a": 1}), trace="t-err")
    span = next(s for s in world["exporter"].spans if s.trace_id == "t-err")
    assert span.status == "ERROR"
    assert span.attributes["error.code"] == "FORBIDDEN"


def test_operational_spans_never_carry_receipt_content(world) -> None:
    """A span may reference a receipt id; it must never replace the receipt."""

    tel = Telemetry(SpanExporter())
    with tel.span("x", trace_id="t", attributes={"receipt.id": "r1", "receipt.value": 0.42, "receipt.verdict": "PASS"}):
        pass
    span = tel.exporter.spans[0]
    assert span.attributes.get("receipt.id") == "r1"
    assert "receipt.value" not in span.attributes
    assert "receipt.verdict" not in span.attributes
