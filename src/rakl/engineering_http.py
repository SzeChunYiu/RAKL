"""E10 + E13 + E12: a versioned HTTP service with the mutation contract, auth, and telemetry.

Three fibres share one boundary, so they land as one layer:

E10  API/CLI/service boundary
     falsifier: a mutating request has no idempotency/snapshot contract
     Every mutating request MUST carry: idempotency_key, expected_snapshot_id,
     an authenticated actor, and a content-bound action payload hash. Missing
     any one is a typed 4xx, never a silent default.

E13  auth/access/secrets/security
     falsifier: secret material enters canonical receipt/log, or an infra role
     changes scientific authority
     Bearer tokens are verified against a pluggable identity provider; the
     actor's capabilities gate each route; secrets are referenced by name and
     resolved at use, never carried in receipts; and no role — not even admin —
     can touch the scientific-authority projection through this API.

E12  distributed telemetry correlation
     falsifier: a transition cannot be correlated across worker/database/blob/
     runtime boundaries
     Every request gets a trace_id; every response echoes it; every emitted
     span carries project/snapshot/actor context. Spans go to a pluggable
     exporter with an OpenTelemetry-shaped record. Operational telemetry is
     kept strictly separate from MetricReceipt scientific authority: a span may
     reference a receipt id, never replace one.

Standard library only. A production deployment fronts this with a real server;
the contract is what matters, and the contract is tested here.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Mapping

API_VERSION = "v1"


# --- E13: identity and capability ------------------------------------------


class Capability(str, Enum):
    READ_EVIDENCE = "READ_EVIDENCE"
    WRITE_EVIDENCE = "WRITE_EVIDENCE"
    EXECUTE = "EXECUTE"
    GOVERN = "GOVERN"
    ADMIN = "ADMIN"


@dataclass(frozen=True)
class Actor:
    actor_id: str
    project_ids: frozenset[str]
    capabilities: frozenset[Capability]

    def can(self, cap: Capability, *, project_id: str) -> bool:
        return project_id in self.project_ids and cap in self.capabilities


class IdentityProvider:
    """Pluggable. The reference resolves opaque bearer tokens to actors.

    A production deployment substitutes OIDC/workload identity. The contract
    the API relies on is only `resolve(token) -> Actor | None`.
    """

    def __init__(self) -> None:
        self._tokens: dict[str, Actor] = {}

    def issue(self, actor: Actor) -> str:
        token = secrets.token_urlsafe(24)
        self._tokens[hashlib.sha256(token.encode()).hexdigest()] = actor
        return token

    def resolve(self, token: str) -> Actor | None:
        return self._tokens.get(hashlib.sha256(token.encode()).hexdigest())


class SecretStore:
    """Secrets are referenced by name and resolved at use. Values never enter receipts."""

    def __init__(self) -> None:
        self._values: dict[str, str] = {}
        self._versions: dict[str, int] = {}

    def put(self, name: str, value: str) -> int:
        self._values[name] = value
        self._versions[name] = self._versions.get(name, 0) + 1
        return self._versions[name]

    def resolve(self, name: str) -> str:
        if name not in self._values:
            raise KeyError(f"secret {name!r} is not registered")
        return self._values[name]

    def reference(self, name: str) -> str:
        """The only form of a secret allowed into a receipt or log."""
        return f"secret://{name}@v{self._versions.get(name, 0)}"


# --- E12: telemetry ---------------------------------------------------------


@dataclass(frozen=True)
class Span:
    """OpenTelemetry-shaped span. Operational, never scientific."""

    trace_id: str
    span_id: str
    name: str
    start_ns: int
    end_ns: int
    attributes: Mapping[str, object]
    status: str = "OK"

    def to_otlp_dict(self) -> dict[str, object]:
        return {
            "traceId": self.trace_id,
            "spanId": self.span_id,
            "name": self.name,
            "startTimeUnixNano": self.start_ns,
            "endTimeUnixNano": self.end_ns,
            "attributes": [{"key": k, "value": {"stringValue": str(v)}} for k, v in self.attributes.items()],
            "status": {"code": self.status},
        }


class SpanExporter:
    """Pluggable. Reference collects in memory; production ships OTLP."""

    def __init__(self) -> None:
        self.spans: list[Span] = []
        self._lock = threading.Lock()

    def export(self, span: Span) -> None:
        with self._lock:
            self.spans.append(span)


class Telemetry:
    def __init__(self, exporter: SpanExporter | None = None) -> None:
        self.exporter = exporter or SpanExporter()

    @staticmethod
    def new_trace_id() -> str:
        return secrets.token_hex(16)

    def span(self, name: str, *, trace_id: str, attributes: Mapping[str, object]) -> "_SpanCtx":
        return _SpanCtx(self, name, trace_id, dict(attributes))


class _SpanCtx:
    def __init__(self, tel: Telemetry, name: str, trace_id: str, attrs: dict[str, object]) -> None:
        self.tel, self.name, self.trace_id, self.attrs = tel, name, trace_id, attrs
        self.status = "OK"

    def __enter__(self) -> "_SpanCtx":
        self.start = time.time_ns()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if exc_type is not None:
            self.status = "ERROR"
        # A span may reference a receipt id; it must never carry receipt content.
        forbidden = [k for k in self.attrs if k.startswith("receipt.") and k != "receipt.id"]
        for k in forbidden:
            self.attrs.pop(k)
        self.tel.exporter.export(Span(
            trace_id=self.trace_id, span_id=secrets.token_hex(8), name=self.name,
            start_ns=self.start, end_ns=time.time_ns(), attributes=self.attrs, status=self.status,
        ))


# --- E10: the mutation contract --------------------------------------------


class ApiErrorCode(str, Enum):
    UNAUTHENTICATED = "UNAUTHENTICATED"
    FORBIDDEN = "FORBIDDEN"
    MISSING_IDEMPOTENCY_KEY = "MISSING_IDEMPOTENCY_KEY"
    MISSING_EXPECTED_SNAPSHOT = "MISSING_EXPECTED_SNAPSHOT"
    PAYLOAD_HASH_MISMATCH = "PAYLOAD_HASH_MISMATCH"
    SNAPSHOT_STALE = "SNAPSHOT_STALE"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    AUTHORITY_PROJECTION_IMMUTABLE = "AUTHORITY_PROJECTION_IMMUTABLE"
    NOT_FOUND = "NOT_FOUND"
    CANNOT_CHECK = "CANNOT_CHECK"
    RETRY_REQUIRED = "RETRY_REQUIRED"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


@dataclass(frozen=True)
class ApiError(Exception):
    code: ApiErrorCode
    http_status: int
    detail: str = ""

    def to_dict(self) -> dict[str, object]:
        return {"error": self.code.value, "detail": self.detail, "api_version": API_VERSION}


def content_hash(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


@dataclass
class ProjectState:
    """Minimal in-memory project the reference service mutates. Production binds the real stores."""

    project_id: str
    snapshot_id: str = "snap-0"
    sequence: int = 0
    evidence: list[dict[str, object]] = field(default_factory=list)
    decisions: list[dict[str, object]] = field(default_factory=list)
    idempotency: dict[str, dict[str, object]] = field(default_factory=dict)
    # The scientific-authority projection. Nothing on this API may write it.
    authority_projection_revision: str = "auth-0"


class EngineeringHttpService:
    """The versioned service. Routes are `/v1/projects/{id}/...`."""

    MUTATING_ROUTES = {"evidence", "decisions", "execute", "runs"}
    READ_ROUTES = {"snapshot", "status", "provenance", "plans"}

    def __init__(self, *, idp: IdentityProvider, secrets: SecretStore, telemetry: Telemetry | None = None) -> None:
        self.idp = idp
        self.secrets = secrets
        self.tel = telemetry or Telemetry()
        self.projects: dict[str, ProjectState] = {}
        self._lock = threading.Lock()

    def ensure_project(self, project_id: str) -> ProjectState:
        with self._lock:
            return self.projects.setdefault(project_id, ProjectState(project_id))

    # --- the contract, applied to every mutation ---------------------------

    def _authenticate(self, headers: Mapping[str, str]) -> Actor:
        auth = headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise ApiError(ApiErrorCode.UNAUTHENTICATED, HTTPStatus.UNAUTHORIZED, "bearer token required")
        actor = self.idp.resolve(auth[len("Bearer "):])
        if actor is None:
            raise ApiError(ApiErrorCode.UNAUTHENTICATED, HTTPStatus.UNAUTHORIZED, "token not recognised")
        return actor

    def _authorize(self, actor: Actor, cap: Capability, project_id: str) -> None:
        if not actor.can(cap, project_id=project_id):
            raise ApiError(ApiErrorCode.FORBIDDEN, HTTPStatus.FORBIDDEN,
                           f"actor {actor.actor_id!r} lacks {cap.value} on {project_id!r}")

    def _validate_mutation(self, project: ProjectState, body: Mapping[str, Any]) -> tuple[str, str, dict[str, object]]:
        key = body.get("idempotency_key")
        if not key:
            raise ApiError(ApiErrorCode.MISSING_IDEMPOTENCY_KEY, HTTPStatus.BAD_REQUEST,
                           "every mutating request must carry idempotency_key")
        expected = body.get("expected_snapshot_id")
        if not expected:
            raise ApiError(ApiErrorCode.MISSING_EXPECTED_SNAPSHOT, HTTPStatus.BAD_REQUEST,
                           "every mutating request must carry expected_snapshot_id")
        payload = body.get("payload")
        if not isinstance(payload, dict):
            raise ApiError(ApiErrorCode.PAYLOAD_HASH_MISMATCH, HTTPStatus.BAD_REQUEST, "payload object required")
        declared = body.get("payload_hash")
        if declared != content_hash(payload):
            raise ApiError(ApiErrorCode.PAYLOAD_HASH_MISMATCH, HTTPStatus.BAD_REQUEST,
                           "payload_hash does not bind the payload")
        if "authority_projection_revision" in payload or "scientific_authority" in payload:
            raise ApiError(ApiErrorCode.AUTHORITY_PROJECTION_IMMUTABLE, HTTPStatus.FORBIDDEN,
                           "no API role may write the scientific-authority projection")
        # A replay of an already-committed key is recognised BEFORE staleness:
        # the first attempt moved the head, so a legitimate retry always looks
        # stale. Only a new key is held to the current head.
        prior = project.idempotency.get(str(key))
        if prior is not None:
            if prior["payload_hash"] != content_hash(payload):
                raise ApiError(ApiErrorCode.IDEMPOTENCY_CONFLICT, HTTPStatus.CONFLICT,
                               "idempotency_key already bound to a different payload")
            return str(key), str(expected), payload
        if expected != project.snapshot_id:
            raise ApiError(ApiErrorCode.SNAPSHOT_STALE, HTTPStatus.CONFLICT,
                           f"expected {expected!r} but head is {project.snapshot_id!r}; refresh and retry")
        return str(key), str(expected), payload

    def _apply_idempotent(self, project: ProjectState, key: str, payload_hash: str, apply: Callable[[], dict[str, object]]) -> dict[str, object]:
        prior = project.idempotency.get(key)
        if prior is not None:
            if prior["payload_hash"] != payload_hash:
                raise ApiError(ApiErrorCode.IDEMPOTENCY_CONFLICT, HTTPStatus.CONFLICT,
                               "idempotency_key already bound to a different payload")
            return dict(prior["response"], replayed=True)
        response = apply()
        project.idempotency[key] = {"payload_hash": payload_hash, "response": response}
        return response

    def _advance(self, project: ProjectState) -> str:
        project.sequence += 1
        project.snapshot_id = f"snap-{project.sequence}"
        return project.snapshot_id

    # --- handlers -------------------------------------------------------------

    def handle(self, method: str, path: str, headers: Mapping[str, str], body: bytes) -> tuple[int, dict[str, object], dict[str, str]]:
        trace_id = headers.get("X-Trace-Id") or Telemetry.new_trace_id()
        parts = [p for p in path.split("/") if p]
        resp_headers = {"X-Trace-Id": trace_id, "X-Api-Version": API_VERSION}

        if len(parts) < 3 or parts[0] != API_VERSION or parts[1] != "projects":
            return HTTPStatus.NOT_FOUND, ApiError(ApiErrorCode.NOT_FOUND, 404, "unknown route").to_dict(), resp_headers
        project_id = parts[2]
        resource = parts[3] if len(parts) > 3 else "snapshot"

        with self.tel.span(f"{method} /{resource}", trace_id=trace_id,
                           attributes={"project.id": project_id, "http.method": method}) as span:
            try:
                actor = self._authenticate(headers)
                span.attrs["actor.id"] = actor.actor_id
                project = self.ensure_project(project_id)
                span.attrs["snapshot.id"] = project.snapshot_id

                if method == "GET" and resource in self.READ_ROUTES:
                    self._authorize(actor, Capability.READ_EVIDENCE, project_id)
                    return HTTPStatus.OK, self._read(project, resource), resp_headers

                if method == "POST" and resource in self.MUTATING_ROUTES:
                    cap = {"evidence": Capability.WRITE_EVIDENCE, "decisions": Capability.GOVERN,
                           "execute": Capability.EXECUTE, "runs": Capability.EXECUTE}[resource]
                    self._authorize(actor, cap, project_id)
                    parsed = json.loads(body or b"{}")
                    key, _, payload = self._validate_mutation(project, parsed)
                    phash = content_hash(payload)
                    span.attrs["idempotency.key"] = key
                    span.attrs["payload.hash"] = phash

                    def apply() -> dict[str, object]:
                        with self._lock:
                            before = project.snapshot_id
                            after = self._advance(project)
                            record = {"actor": actor.actor_id, "before": before, "after": after,
                                      "payload_hash": phash, "resource": resource,
                                      # secrets referenced by name only, never by value
                                      "secret_refs": [self.secrets.reference(n) for n in payload.get("secret_names", [])]}
                            (project.evidence if resource == "evidence" else project.decisions).append(record)
                        return {"committed": True, "before_snapshot_id": before, "after_snapshot_id": after,
                                "payload_hash": phash, "api_version": API_VERSION}

                    return HTTPStatus.OK, self._apply_idempotent(project, key, phash, apply), resp_headers

                raise ApiError(ApiErrorCode.NOT_FOUND, HTTPStatus.NOT_FOUND, f"no {method} for /{resource}")
            except ApiError as err:
                span.status = "ERROR"
                span.attrs["error.code"] = err.code.value
                return err.http_status, err.to_dict(), resp_headers

    def _read(self, project: ProjectState, resource: str) -> dict[str, object]:
        base = {"project_id": project.project_id, "snapshot_id": project.snapshot_id, "api_version": API_VERSION}
        if resource == "snapshot":
            return {**base, "sequence": project.sequence,
                    "authority_projection_revision": project.authority_projection_revision}
        if resource == "status":
            return {**base, "evidence_count": len(project.evidence), "decision_count": len(project.decisions)}
        if resource == "provenance":
            return {**base, "evidence": list(project.evidence), "decisions": list(project.decisions)}
        return {**base, "plans": []}


# --- a real HTTP front, stdlib only ---------------------------------------


def serve(service: EngineeringHttpService, *, host: str = "127.0.0.1", port: int = 0) -> ThreadingHTTPServer:
    class Handler(BaseHTTPRequestHandler):
        def _dispatch(self) -> None:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length) if length else b""
            status, payload, extra = service.handle(self.command, self.path, dict(self.headers), body)
            data = json.dumps(payload).encode()
            self.send_response(int(status))
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            for k, v in extra.items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        do_GET = _dispatch
        do_POST = _dispatch

        def log_message(self, *args: object) -> None:  # quiet
            return

    server = ThreadingHTTPServer((host, port), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


__all__ = [
    "API_VERSION", "Actor", "ApiError", "ApiErrorCode", "Capability", "EngineeringHttpService",
    "IdentityProvider", "ProjectState", "SecretStore", "Span", "SpanExporter", "Telemetry",
    "content_hash", "serve",
]
