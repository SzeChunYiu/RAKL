"""E10 + E13 + E12: a versioned HTTP service over the REAL engineering stores.

Three fibres share one boundary, so they land as one layer:

E10  API/CLI/service boundary
     falsifier: a mutating request has no idempotency/snapshot contract
     Every mutating request MUST carry: idempotency_key, expected_snapshot_id,
     an authenticated actor, and a content-bound action payload hash. Missing
     any one is a typed 4xx, never a silent default. Every mutation that
     reaches the store returns a real `StateTransitionReceipt` — on COMMITTED,
     RETRY_REQUIRED, ABORTED, RECOVERY_REQUIRED and CANNOT_CHECK alike — with
     `status` in the `TransitionStatus` vocabulary.

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
     span carries project/snapshot/actor context. Operational telemetry is
     kept strictly separate from MetricReceipt scientific authority.

Where state lives — and where it does NOT:

  * The project head, snapshots, evidence, semantic atlas, transitions,
    epistemic statuses, controller decisions and workflow runs are all in the
    `SqliteAtomicEngineeringCoordinator`'s database plus the `BlobStore`. This
    module holds no in-memory project state, no idempotency map and no
    counter. The first version of this service kept a private `snap-N`
    sequence and an in-process idempotency dict, both consulted outside any
    lock; sixteen concurrent requests with one idempotency key produced
    sixteen commits. Every mutation now goes through one store transaction
    (`BEGIN IMMEDIATE`) that performs the head compare-and-swap and the
    idempotency check together, so there is no check-then-act left to race.

  * Staleness is a RECEIPT, not an error. A stale `expected_snapshot_id` is
    handed to the store, which records and returns a RETRY_REQUIRED receipt.
    An `expected_snapshot_id` that names no snapshot of the project at all is
    a malformed request (typed 4xx) — no transition request can exist for a
    before-state that never existed.

  * The client's `payload_hash` binds the client's payload (API contract).
    The store's `action_payload_hash` binds the mutation batch the service
    derives from that payload, computed exactly as `engineering_atomic` does
    (`evidence_action_payload_hash` / `semantic_action_payload_hash`). Both
    are reported; they are different things and are not conflated.

  * `POST /v1/projects` is genesis, not a transition: there is no before
    snapshot, so it returns the initial `ProjectSnapshot`, not a receipt. The
    authority projection revision is fixed at genesis and is not settable
    through this API. This is the one documented exception to
    "every mutation returns a receipt".

Standard library only. A production deployment fronts this with a real
server; the contract is what matters, and the contract is tested over a live
socket in tests/test_engineering_http.py and tests/test_engineering_http_routes.py.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import tempfile
import threading
import time
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Mapping
from urllib.parse import parse_qs, urlsplit

from .engineering_api import EngineeringServiceFacade
from .engineering_atomic import SqliteAtomicEngineeringCoordinator
from .engineering_blob import LocalFilesystemBlobStore
from .engineering_control_store import ControlArtifactKind, ControlArtifactProjection, SqliteControlProjectionStore
from .engineering_evidence_store import EvidenceMutationBatch, EvidenceRecord
from .engineering_semantic_store import (
    RelationWitnessVersion,
    SemanticAtomVersion,
    SemanticFiber,
    SemanticMutationBatch,
)
from .engineering_service import EpistemicStatusUnavailable
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
    EngineeringStoreError,
    IdempotencyConflict,
    ProjectNotInitialized,
    metadata_transition_payload_hash,
)
from .engineering_workflow import ActivitySpec, SqliteReferenceWorkflowEngine, WorkflowIntegrityError

API_VERSION = "v1"

# Genesis constants. The authority projection is NOT settable through this API,
# at genesis or ever; it is fixed here and only the scientific-authority
# machinery — which this service does not expose — may move it.
GENESIS_AUTHORITY_PROJECTION_REVISION = "authority-projection:genesis"
GENESIS_METRIC_LEDGER_HEAD = "metric-ledger:genesis"
GENESIS_EPISODE_STORE_HEAD = "episode-store:genesis"
GENESIS_CONTROLLER_EPOCH_ID = "controller-epoch:genesis"

ACTION_INGEST_EVIDENCE = "INGEST_EVIDENCE"
ACTION_RESEARCH_ROUND = "UPDATE_SEMANTIC_ATLAS"
ACTION_EXECUTE = "EXECUTE_CONTROLLER_DECISION"

# HTTP status per TransitionStatus. The receipt is the body in every case.
RECEIPT_HTTP_STATUS: dict[TransitionStatus, int] = {
    TransitionStatus.COMMITTED: HTTPStatus.OK,
    TransitionStatus.RETRY_REQUIRED: HTTPStatus.CONFLICT,
    TransitionStatus.ABORTED: HTTPStatus.UNPROCESSABLE_ENTITY,
    TransitionStatus.RECOVERY_REQUIRED: HTTPStatus.SERVICE_UNAVAILABLE,
    TransitionStatus.CANNOT_CHECK: HTTPStatus.SERVICE_UNAVAILABLE,
}


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
    INVALID_REQUEST = "INVALID_REQUEST"
    MISSING_IDEMPOTENCY_KEY = "MISSING_IDEMPOTENCY_KEY"
    MISSING_EXPECTED_SNAPSHOT = "MISSING_EXPECTED_SNAPSHOT"
    PAYLOAD_HASH_MISMATCH = "PAYLOAD_HASH_MISMATCH"
    SNAPSHOT_STALE = "SNAPSHOT_STALE"  # kept in the vocabulary; staleness itself is now a RETRY_REQUIRED receipt
    UNKNOWN_SNAPSHOT = "UNKNOWN_SNAPSHOT"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    AUTHORITY_PROJECTION_IMMUTABLE = "AUTHORITY_PROJECTION_IMMUTABLE"
    PROJECT_NOT_INITIALIZED = "PROJECT_NOT_INITIALIZED"
    PROJECT_ALREADY_INITIALIZED = "PROJECT_ALREADY_INITIALIZED"
    NOT_FOUND = "NOT_FOUND"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ApiError(Exception):
    code: ApiErrorCode
    http_status: int
    detail: str = ""

    def to_dict(self) -> dict[str, object]:
        return {"error": self.code.value, "detail": self.detail, "api_version": API_VERSION}


def content_hash(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class MutationEnvelope:
    """The validated E10 envelope. Nothing here has touched the store yet."""

    idempotency_key: str
    expected_snapshot_id: str
    payload: dict[str, Any]
    payload_hash: str


@dataclass(frozen=True)
class MutationOutcome:
    receipt: StateTransitionReceipt
    replayed: bool
    persisted: bool
    head_snapshot_id: str | None
    extra: Mapping[str, object]


_Built = tuple[
    StateTransitionRequest,
    Callable[[], StateTransitionReceipt],
    Callable[[StateTransitionReceipt], bool],
]


class EngineeringHttpService:
    """The versioned service. Routes are `/v1/projects` and `/v1/projects/{id}/...`."""

    def __init__(
        self,
        *,
        idp: IdentityProvider,
        secrets: SecretStore,
        telemetry: Telemetry | None = None,
        coordinator: SqliteAtomicEngineeringCoordinator | None = None,
        blob_store: BlobStore | None = None,
        controls: SqliteControlProjectionStore | None = None,
        workflows: SqliteReferenceWorkflowEngine | None = None,
    ) -> None:
        self.idp = idp
        self.secrets = secrets
        self.tel = telemetry or Telemetry()
        if coordinator is None or blob_store is None:
            # Ephemeral REAL stores for a service constructed without any. This is
            # still the store code path — a temp directory, not an in-memory dict.
            root = Path(tempfile.mkdtemp(prefix="orion-http-"))
            coordinator = coordinator or SqliteAtomicEngineeringCoordinator(root / "orion.sqlite3")
            blob_store = blob_store or LocalFilesystemBlobStore(root / "blobs")
            self.storage_root: Path | None = root
        else:
            self.storage_root = None
        self.coordinator = coordinator
        self.blobs = blob_store
        self.state = coordinator.state
        self.facade = EngineeringServiceFacade(coordinator.state)
        self.controls = controls or SqliteControlProjectionStore(coordinator.path)
        self.workflows = workflows or SqliteReferenceWorkflowEngine(coordinator.path)

    # --- auth ------------------------------------------------------------------

    def _authenticate(self, headers: Mapping[str, str]) -> Actor:
        auth = headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            raise ApiError(ApiErrorCode.UNAUTHENTICATED, HTTPStatus.UNAUTHORIZED, "bearer token required")
        actor = self.idp.resolve(auth[len("Bearer "):])
        if actor is None:
            raise ApiError(ApiErrorCode.UNAUTHENTICATED, HTTPStatus.UNAUTHORIZED, "token not recognised")
        return actor

    @staticmethod
    def _authorize(actor: Actor, cap: Capability, project_id: str) -> None:
        if not actor.can(cap, project_id=project_id):
            raise ApiError(ApiErrorCode.FORBIDDEN, HTTPStatus.FORBIDDEN,
                           f"actor {actor.actor_id!r} lacks {cap.value} on {project_id!r}")

    # --- envelope ---------------------------------------------------------------

    @staticmethod
    def _parse_body(body: bytes) -> dict[str, Any]:
        try:
            parsed = json.loads(body or b"{}")
        except json.JSONDecodeError as exc:
            raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, f"body is not JSON: {exc.msg}")
        if not isinstance(parsed, dict):
            raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, "body must be a JSON object")
        return parsed

    @staticmethod
    def _validate_mutation(body: Mapping[str, Any]) -> MutationEnvelope:
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
        phash = content_hash(payload)
        if declared != phash:
            raise ApiError(ApiErrorCode.PAYLOAD_HASH_MISMATCH, HTTPStatus.BAD_REQUEST,
                           "payload_hash does not bind the payload")
        if "authority_projection_revision" in payload or "scientific_authority" in payload:
            raise ApiError(ApiErrorCode.AUTHORITY_PROJECTION_IMMUTABLE, HTTPStatus.FORBIDDEN,
                           "no API role may write the scientific-authority projection")
        return MutationEnvelope(str(key), str(expected), payload, phash)

    # --- store lookups shared by routes ---------------------------------------

    def _head(self, project_id: str) -> ProjectSnapshot:
        try:
            return self.state.head(project_id)
        except ProjectNotInitialized:
            raise ApiError(ApiErrorCode.PROJECT_NOT_INITIALIZED, HTTPStatus.NOT_FOUND,
                           f"project {project_id!r} has no head; POST /v1/projects first")

    def _snapshot_of(self, project_id: str, snapshot_id: str) -> ProjectSnapshot:
        try:
            snapshot = self.state.get_snapshot(snapshot_id)
        except KeyError:
            raise ApiError(ApiErrorCode.UNKNOWN_SNAPSHOT, HTTPStatus.NOT_FOUND,
                           f"{snapshot_id!r} names no snapshot of {project_id!r}")
        if snapshot.project_id != project_id:
            raise ApiError(ApiErrorCode.UNKNOWN_SNAPSHOT, HTTPStatus.NOT_FOUND,
                           f"{snapshot_id!r} names no snapshot of {project_id!r}")
        return snapshot

    def _connect_ro(self) -> sqlite3.Connection:
        db = sqlite3.connect(f"file:{self.coordinator.path}?mode=ro", uri=True, timeout=10.0)
        db.row_factory = sqlite3.Row
        return db

    def _transition_by_id_or_key(self, project_id: str, ident: str) -> StateTransitionReceipt | None:
        with closing(self._connect_ro()) as db:
            row = db.execute(
                "SELECT payload_json FROM transitions WHERE project_id=? AND (transition_id=? OR idempotency_key=?)",
                (project_id, ident, ident),
            ).fetchone()
        return None if row is None else StateTransitionReceipt.from_dict(json.loads(row["payload_json"]))

    def _decision(self, project_id: str, decision_id: str, snapshot_id: str | None = None) -> ControlArtifactProjection | None:
        with closing(self._connect_ro()) as db:
            rows = db.execute(
                "SELECT payload_json FROM control_projection WHERE kind=? AND source_object_id=?",
                (ControlArtifactKind.CONTROLLER_DECISION.value, decision_id),
            ).fetchall()
        for row in rows:
            record = SqliteControlProjectionStore._from_dict(json.loads(row["payload_json"]))
            if record.canonical_payload.get("project_id") != project_id:
                continue
            if snapshot_id is not None and record.project_snapshot_id != snapshot_id:
                continue
            return record
        return None

    def _snapshot_id_at_sequence(self, project_id: str, sequence: int) -> str | None:
        with closing(self._connect_ro()) as db:
            row = db.execute(
                "SELECT snapshot_id FROM snapshots WHERE project_id=? AND sequence=?", (project_id, sequence)
            ).fetchone()
        return None if row is None else str(row["snapshot_id"])

    # --- the one mutation path -----------------------------------------------

    def _run_mutation(
        self,
        *,
        project_id: str,
        actor: Actor,
        env: MutationEnvelope,
        build: Callable[[ProjectSnapshot, str], "_Built"],
        after_commit: Callable[[StateTransitionReceipt], Mapping[str, object]] | None = None,
    ) -> MutationOutcome:
        """Validate the before-snapshot, then let the STORE decide.

        ``build(before, created_at)`` constructs the transition request, a thunk
        that performs the store commit, and a predicate saying whether a prior
        receipt under this key is the SAME logical mutation. Idempotent replay is
        decided by content, not by wall clock: the same key with the same content
        is a replay of the stored receipt; different content is a typed conflict.
        Concurrent first arrivals are serialised by the store's own transaction;
        the loser's IdempotencyConflict (its created_at differs) is resolved by
        the same content predicate.
        """

        before = self._snapshot_of(project_id, env.expected_snapshot_id)  # unknown before-state: malformed request
        head_after: Callable[[], str | None] = lambda: self._safe_head_id(project_id)

        prior = self.state.transition_receipt(project_id, env.idempotency_key)
        request, commit, matches_prior = build(before, _now_utc())
        if prior is not None:
            if not matches_prior(prior):
                raise ApiError(ApiErrorCode.IDEMPOTENCY_CONFLICT, HTTPStatus.CONFLICT,
                               "idempotency_key already bound to a different payload")
            extra = after_commit(prior) if (after_commit and prior.status is TransitionStatus.COMMITTED) else {}
            return MutationOutcome(prior, True, True, head_after(), extra)

        try:
            receipt = commit()
            replayed = False
        except IdempotencyConflict:
            # lost a same-key race to a concurrent first arrival: resolve by content
            prior = self.state.transition_receipt(project_id, env.idempotency_key)
            if prior is None or not matches_prior(prior):
                raise ApiError(ApiErrorCode.IDEMPOTENCY_CONFLICT, HTTPStatus.CONFLICT,
                               "idempotency_key already bound to a different payload")
            receipt, replayed = prior, True
        except EngineeringIntegrityError as exc:
            # the store refused before any effect: a typed ABORTED receipt, persisted
            receipt = self._record_noncommitted(request, TransitionStatus.ABORTED, (f"store_refused:{exc}",))
            replayed = False
        except (sqlite3.OperationalError, EngineeringStoreError, OSError) as exc:
            # ambiguity: the store may or may not have applied the effect
            try:
                receipt = self.facade.record_recovery_required(
                    request=request, reasons=(f"store_error_after_dispatch:{type(exc).__name__}",),
                    created_at_utc=_now_utc(),
                )
                persisted = True
            except Exception as inner:  # noqa: BLE001 — the store is unreachable; the receipt cannot be durable
                receipt = self._unpersisted_receipt(
                    request, TransitionStatus.CANNOT_CHECK,
                    (f"store_unreachable:{type(exc).__name__}", f"receipt_not_persisted:{type(inner).__name__}"),
                )
                persisted = False
            return MutationOutcome(receipt, False, persisted, head_after(), {})

        extra = after_commit(receipt) if (after_commit and receipt.status is TransitionStatus.COMMITTED) else {}
        return MutationOutcome(receipt, replayed, True, head_after(), extra)

    def _safe_head_id(self, project_id: str) -> str | None:
        try:
            return self.state.head(project_id).snapshot_id
        except Exception:  # noqa: BLE001
            return None

    def _record_noncommitted(self, request: StateTransitionRequest, status: TransitionStatus, reasons: tuple[str, ...]) -> StateTransitionReceipt:
        try:
            return self.state.record_noncommitted_transition(
                request, status=status, reasons=reasons, created_at_utc=_now_utc()
            )
        except IdempotencyConflict:
            prior = self.state.transition_receipt(request.project_id, request.idempotency_key)
            if prior is not None:
                return prior
            raise

    @staticmethod
    def _unpersisted_receipt(request: StateTransitionRequest, status: TransitionStatus, reasons: tuple[str, ...]) -> StateTransitionReceipt:
        return StateTransitionReceipt(
            project_id=request.project_id, before_snapshot_id=request.before_snapshot_id, after_snapshot_id=None,
            action=request.action, action_payload_hash=request.action_payload_hash,
            idempotency_key=request.idempotency_key, request_hash=request.request_hash,
            process_identity=request.process_identity, read_set=request.read_set, write_set=request.write_set,
            produced_artifact_ids=(), metric_receipt_ids=(), residual_ids=(), status=status, reasons=reasons,
            created_at_utc=_now_utc(),
        )

    @staticmethod
    def _next_snapshot(before: ProjectSnapshot, created_at: str, **changes: object) -> ProjectSnapshot:
        fields = dict(before.to_dict())
        fields.pop("snapshot_id")
        fields.update(sequence=before.sequence + 1, previous_snapshot_id=before.snapshot_id, created_at_utc=created_at)
        fields.update(changes)
        return ProjectSnapshot.from_dict(fields)

    # --- evidence -----------------------------------------------------------------

    def _evidence_records(self, project_id: str, actor: Actor, env: MutationEnvelope, sequence: int) -> tuple[EvidenceRecord, ...]:
        """Payload -> evidence records. Bytes go to the blob store FIRST (orphans are safe).

        ``payload.records`` is a list of ``{logical_record_id, content|content_utf8,
        source_identity, source_version, provenance, secret_names}``. Without
        ``records`` the payload itself is one record whose bytes are its canonical
        JSON. Secrets are referenced by name only; a value never enters a record.
        """

        specs = env.payload.get("records")
        if specs is None:
            specs = [env.payload]
        if not isinstance(specs, list) or not specs:
            raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, "payload.records must be a non-empty list")
        records = []
        for index, spec in enumerate(specs):
            if not isinstance(spec, dict):
                raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, "each evidence record must be an object")
            if "content_utf8" in spec:
                content = str(spec["content_utf8"]).encode("utf-8")
            else:
                content = json.dumps(spec.get("content", spec), sort_keys=True, separators=(",", ":")).encode("utf-8")
            digest = self.blobs.put_if_absent(content)
            names = spec.get("secret_names", [])
            if not isinstance(names, list):
                raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, "secret_names must be a list")
            provenance = {
                "actor": actor.actor_id,
                "client_payload_hash": env.payload_hash,
                "provenance": spec.get("provenance", {}),
                "secret_refs": [self.secrets.reference(str(n)) for n in names],
            }
            records.append(EvidenceRecord(
                project_id=project_id,
                logical_record_id=str(spec.get("logical_record_id") or f"record:{env.idempotency_key}:{index}"),
                payload_sha256=digest,
                source_identity=str(spec.get("source_identity") or f"actor:{actor.actor_id}"),
                source_version=None if spec.get("source_version") is None else str(spec["source_version"]),
                provenance_payload=provenance,
                created_sequence=sequence,
            ))
        return tuple(records)

    def _mutate_evidence(self, project_id: str, actor: Actor, env: MutationEnvelope) -> MutationOutcome:
        def build(before: ProjectSnapshot, created_at: str):
            sequence = before.sequence + 1
            batch = EvidenceMutationBatch(
                project_id=project_id, sequence=sequence,
                base_evidence_revision=self.coordinator.evidence.evidence_revision(project_id, before.sequence),
                records=self._evidence_records(project_id, actor, env, sequence),
            )
            request = StateTransitionRequest(
                project_id=project_id, before_snapshot_id=before.snapshot_id, action=ACTION_INGEST_EVIDENCE,
                action_payload_hash=self.coordinator.evidence_action_payload_hash(batch),
                idempotency_key=env.idempotency_key, process_identity=f"api:{actor.actor_id}",
                read_set=("evidence",), write_set=("evidence",), created_at_utc=created_at,
            )

            def commit() -> StateTransitionReceipt:
                after = self._next_snapshot(before, created_at,
                                            evidence_cutoff=self.coordinator.evidence.preview_batch_revision(batch))
                return self.coordinator.commit_evidence_transition(
                    request, batch, after, blob_store=self.blobs, created_at_utc=created_at,
                ).transition_receipt

            # same key + same batch hash == same logical mutation
            return request, commit, lambda prior: prior.action_payload_hash == request.action_payload_hash

        return self._run_mutation(project_id=project_id, actor=actor, env=env, build=build)

    # --- research rounds (semantic atlas) ------------------------------------------

    @staticmethod
    def _semantic_batch(payload: Mapping[str, Any], sequence: int, base_revision: str) -> SemanticMutationBatch:
        try:
            fibers = tuple(
                SemanticFiber(str(f["fiber_id"]), f.get("parent_fiber_id"), created_from_sequence=sequence)
                for f in payload.get("new_fibers", [])
            )
            atoms = tuple(
                SemanticAtomVersion(
                    atom_id=str(a["atom_id"]), fiber_id=str(a["fiber_id"]), kind=str(a["kind"]), label=str(a["label"]),
                    evidence_ids=tuple(str(e) for e in a.get("evidence_ids", [])), payload=dict(a.get("payload", {})),
                    valid_from_sequence=sequence, supersedes_version_id=a.get("supersedes_version_id"),
                )
                for a in payload.get("atom_versions", [])
            )
            witnesses = tuple(
                RelationWitnessVersion(
                    witness_id=str(w["witness_id"]), left_atom_id=str(w["left_atom_id"]),
                    right_atom_id=str(w["right_atom_id"]), relation_type=str(w["relation_type"]),
                    reason=str(w["reason"]), condition=w.get("condition"),
                    evidence_ids=tuple(str(e) for e in w.get("evidence_ids", [])), payload=dict(w.get("payload", {})),
                    valid_from_sequence=sequence, supersedes_version_id=w.get("supersedes_version_id"),
                )
                for w in payload.get("witness_versions", [])
            )
        except (KeyError, TypeError, ValueError, AttributeError) as exc:
            raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, f"malformed research round: {exc}")
        if not (fibers or atoms or witnesses):
            raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST,
                           "a research round must carry new_fibers, atom_versions or witness_versions")
        return SemanticMutationBatch(sequence=sequence, base_semantic_revision=base_revision,
                                     new_fibers=fibers, atom_versions=atoms, witness_versions=witnesses)

    def _mutate_research_round(self, project_id: str, actor: Actor, env: MutationEnvelope) -> MutationOutcome:
        def build(before: ProjectSnapshot, created_at: str):
            sequence = before.sequence + 1
            batch = self._semantic_batch(env.payload, sequence, self.coordinator.semantic.semantic_revision(before.sequence))
            request = StateTransitionRequest(
                project_id=project_id, before_snapshot_id=before.snapshot_id, action=ACTION_RESEARCH_ROUND,
                action_payload_hash=self.coordinator.semantic_action_payload_hash(batch),
                idempotency_key=env.idempotency_key, process_identity=f"api:{actor.actor_id}",
                read_set=("semantic",), write_set=("semantic",), created_at_utc=created_at,
            )

            def commit() -> StateTransitionReceipt:
                after = self._next_snapshot(before, created_at,
                                            semantic_state_revision=self.coordinator.semantic.preview_batch_revision(batch))
                return self.coordinator.commit_semantic_transition(
                    request, batch, after, created_at_utc=created_at,
                    produced_artifact_ids=tuple(a.version_id for a in batch.atom_versions),
                ).transition_receipt

            return request, commit, lambda prior: prior.action_payload_hash == request.action_payload_hash

        return self._run_mutation(project_id=project_id, actor=actor, env=env, build=build)

    # --- actions:plan / actions:execute ---------------------------------------------

    def _plan(self, project_id: str, body: Mapping[str, Any]) -> dict[str, object]:
        target, fiber = body.get("target"), body.get("fiber")
        if not target or not fiber:
            raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, "target and fiber are required")
        head = self._head(project_id)
        try:
            plan = self.facade.plan_action(project_id=project_id, target_id=str(target), fiber_id=str(fiber))
            status = self.facade.reads.current_status(project_id=project_id, target_id=str(target), fiber_id=str(fiber))
        except EpistemicStatusUnavailable as exc:
            raise ApiError(ApiErrorCode.CANNOT_CHECK, HTTPStatus.CONFLICT,
                           f"no canonical EpistemicStatus at head {head.snapshot_id} for target/fiber: {exc}")
        plan_dict = {
            "api_version": plan.api_version, "project_id": plan.project_id,
            "project_snapshot_id": plan.project_snapshot_id, "status_id": plan.status_id,
            "target_id": plan.target_id, "fiber_id": plan.fiber_id, "next_action": plan.next_action,
            "reasons": list(plan.reasons), "hard_gate_ids": list(plan.hard_gate_ids),
        }
        decision_id = "decision:" + canonical_sha256(plan_dict)
        self.controls.record(ControlArtifactProjection(
            project_snapshot_id=plan.project_snapshot_id, kind=ControlArtifactKind.CONTROLLER_DECISION,
            source_object_id=decision_id, canonical_payload=plan_dict, source_receipt_ids=status.metric_receipt_ids,
        ))
        return {"decision_id": decision_id, "plan": plan_dict, "grants_scientific_authority": False,
                "api_version": API_VERSION}

    def _mutate_execute(self, project_id: str, actor: Actor, env: MutationEnvelope) -> MutationOutcome:
        decision_id = env.payload.get("decision_id")
        if not decision_id:
            raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, "payload.decision_id is required")
        try:
            spec = ActivitySpec(
                activity_id=str(env.payload.get("activity_id") or f"activity:{env.idempotency_key}"),
                invocation_id=str(env.payload.get("invocation_id") or f"invocation:{env.idempotency_key}"),
                input_digest=canonical_sha256({"decision_id": decision_id}),
                retry_safe=bool(env.payload.get("retry_safe", False)),
                external_effect=bool(env.payload.get("external_effect", False)),
                max_attempts=int(env.payload.get("max_attempts", 3)),
            )
        except (TypeError, ValueError) as exc:
            raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, f"malformed activity spec: {exc}")
        workflow_id = f"workflow:{project_id}:{env.idempotency_key}"
        epoch_id = "controller-epoch:" + canonical_sha256(
            {"decision_id": decision_id, "idempotency_key": env.idempotency_key})
        abort_reason = f"decision_not_bound_to_expected_snapshot:{decision_id}"

        def build(before: ProjectSnapshot, created_at: str) -> _Built:
            # The after snapshot is built FIRST; the store-layer action_payload_hash
            # binds it (X08). The client's payload_hash stays an API-layer binding.
            after = self._next_snapshot(before, created_at, controller_epoch_id=epoch_id)
            request = StateTransitionRequest(
                project_id=project_id, before_snapshot_id=before.snapshot_id, action=ACTION_EXECUTE,
                action_payload_hash=metadata_transition_payload_hash(after),
                idempotency_key=env.idempotency_key, process_identity=f"api:{actor.actor_id}",
                read_set=("controller_decision",), write_set=("controller_epoch", "workflow"),
                created_at_utc=created_at,
            )

            def commit() -> StateTransitionReceipt:
                unbound = self._decision(project_id, str(decision_id), before.snapshot_id) is None
                if unbound and self.state.head(project_id).snapshot_id == before.snapshot_id:
                    # current head, decision genuinely not bound to it: ABORTED. If the head
                    # has moved, fall through and let the store's CAS say RETRY_REQUIRED —
                    # replanning on the new head subsumes the missing binding.
                    return self._record_noncommitted(request, TransitionStatus.ABORTED, (abort_reason,))
                return self.facade.commit_metadata_transition(
                    request=request, after_snapshot=after, created_at_utc=created_at,
                    produced_artifact_ids=(workflow_id, spec.invocation_id),
                )

            def matches_prior(prior: StateTransitionReceipt) -> bool:
                # The after snapshot carries the clock, so its hash cannot be the
                # replay key. The logical content is (decision_id, key) -> epoch, and
                # the activity spec, which the workflow engine pins per activity id.
                if prior.action != ACTION_EXECUTE or prior.before_snapshot_id != before.snapshot_id:
                    return False
                if prior.status is TransitionStatus.COMMITTED:
                    if self.state.get_snapshot(str(prior.after_snapshot_id)).controller_epoch_id != epoch_id:
                        return False
                    try:
                        scheduled = self.workflows.activity(workflow_id, spec.activity_id)
                    except KeyError:
                        return True  # committed but never scheduled: after_commit heals it
                    return scheduled.spec == spec
                return abort_reason in prior.reasons

            return request, commit, matches_prior

        def after_commit(receipt: StateTransitionReceipt) -> Mapping[str, object]:
            # Durable run, bound to the AFTER snapshot the receipt named. Idempotent on
            # replay, so a crash between commit and schedule heals on the next retry.
            try:
                self.workflows.start_workflow(workflow_id=workflow_id, project_id=project_id,
                                              project_snapshot_id=str(receipt.after_snapshot_id))
                self.workflows.schedule_activity(workflow_id, spec)
            except WorkflowIntegrityError as exc:
                return {"workflow_id": workflow_id, "invocation_id": spec.invocation_id, "run_scheduled": False,
                        "run_error": f"{type(exc).__name__}: {exc}"}
            return {"workflow_id": workflow_id, "invocation_id": spec.invocation_id, "run_scheduled": True}

        return self._run_mutation(project_id=project_id, actor=actor, env=env, build=build, after_commit=after_commit)

    # --- project genesis ---------------------------------------------------------

    def _create_project(self, actor: Actor, body: Mapping[str, Any]) -> tuple[int, dict[str, object]]:
        project_id = body.get("project_id")
        if not project_id or not str(project_id).strip():
            raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, "project_id is required")
        project_id = str(project_id)
        self._authorize(actor, Capability.ADMIN, project_id)
        if "authority_projection_revision" in body:
            raise ApiError(ApiErrorCode.AUTHORITY_PROJECTION_IMMUTABLE, HTTPStatus.FORBIDDEN,
                           "the authority projection is fixed at genesis and not settable through this API")
        settable = {
            "metric_ledger_head": str(body.get("metric_ledger_head", GENESIS_METRIC_LEDGER_HEAD)),
            "episode_store_head": str(body.get("episode_store_head", GENESIS_EPISODE_STORE_HEAD)),
            "saturation_basis_ids": tuple(str(x) for x in body.get("saturation_basis_ids", [])),
            "controller_epoch_id": str(body.get("controller_epoch_id", GENESIS_CONTROLLER_EPOCH_ID)),
        }
        try:
            existing = self.state.head(project_id)
        except ProjectNotInitialized:
            existing = None
        if existing is not None:
            genesis = self._snapshot_id_at_sequence(project_id, 0)
            root = self.state.get_snapshot(genesis) if genesis else existing
            if any(getattr(root, k) != v for k, v in settable.items()):
                raise ApiError(ApiErrorCode.PROJECT_ALREADY_INITIALIZED, HTTPStatus.CONFLICT,
                               f"project {project_id!r} was initialized with different genesis fields")
            return HTTPStatus.OK, {"created": False, "snapshot": existing.to_dict(), "genesis_snapshot_id": root.snapshot_id,
                                   "api_version": API_VERSION}
        try:
            snapshot = ProjectSnapshot(
                project_id=project_id, sequence=0, previous_snapshot_id=None,
                evidence_cutoff=self.coordinator.evidence.evidence_revision(project_id, 0),
                semantic_state_revision=self.coordinator.semantic.semantic_revision(0),
                authority_projection_revision=GENESIS_AUTHORITY_PROJECTION_REVISION,
                created_at_utc=_now_utc(), **settable,
            )
        except ValueError as exc:
            raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, f"invalid genesis fields: {exc}")
        try:
            snapshot = self.coordinator.initialize_empty_project(snapshot)
        except EngineeringStoreError:
            # lost a concurrent genesis race: report the winner
            winner = self._head(project_id)
            return HTTPStatus.OK, {"created": False, "snapshot": winner.to_dict(), "genesis_snapshot_id": winner.snapshot_id,
                                   "api_version": API_VERSION}
        return HTTPStatus.CREATED, {"created": True, "snapshot": snapshot.to_dict(), "genesis_snapshot_id": snapshot.snapshot_id,
                                    "api_version": API_VERSION}

    # --- reads -----------------------------------------------------------------------

    def _epistemic_status(self, project_id: str, query: Mapping[str, list[str]]) -> dict[str, object]:
        target = (query.get("target") or [""])[0]
        fiber = (query.get("fiber") or [""])[0]
        if not target or not fiber:
            raise ApiError(ApiErrorCode.INVALID_REQUEST, HTTPStatus.BAD_REQUEST, "query must name target and fiber")
        snapshot_id = (query.get("snapshot") or [""])[0]
        head = self._head(project_id)
        if snapshot_id:
            snapshot = self._snapshot_of(project_id, snapshot_id)
            status = self.state.latest_epistemic_status(project_snapshot_id=snapshot.snapshot_id, target_id=target, fiber_id=fiber)
            if status is None:
                raise ApiError(ApiErrorCode.NOT_FOUND, HTTPStatus.NOT_FOUND,
                               f"no EpistemicStatus at snapshot {snapshot_id} for target={target!r} fiber={fiber!r}")
        else:
            try:
                status = self.facade.reads.current_status(project_id=project_id, target_id=target, fiber_id=fiber)
            except EpistemicStatusUnavailable as exc:
                raise ApiError(ApiErrorCode.NOT_FOUND, HTTPStatus.NOT_FOUND, str(exc))
        # The canonical object, verbatim. No scalar saturation percentage is synthesised.
        return {**status.to_dict(), "head_snapshot_id": head.snapshot_id,
                "grants_scientific_authority": False, "api_version": API_VERSION}

    def _provenance(self, project_id: str, entity_id: str | None) -> dict[str, object]:
        head = self._head(project_id)
        records = self.coordinator.evidence.records_at(project_id, head.sequence)
        if entity_id is None:
            return {"project_id": project_id, "head_snapshot_id": head.snapshot_id,
                    "evidence": [r.to_dict() for r in records], "api_version": API_VERSION}
        for record in records:
            if entity_id in (record.evidence_id, record.logical_record_id):
                try:
                    blob: Mapping[str, object] = {"verified": True, **self.blobs.stat(record.payload_sha256)}
                except (KeyError, EngineeringIntegrityError, OSError) as exc:
                    blob = {"verified": False, "error": type(exc).__name__}
                return {"entity_id": entity_id, "kind": "EVIDENCE_RECORD", "record": record.to_dict(),
                        "committed_snapshot_id": self._snapshot_id_at_sequence(project_id, record.created_sequence),
                        "blob": blob, "head_snapshot_id": head.snapshot_id, "api_version": API_VERSION}
        receipt = self._transition_by_id_or_key(project_id, entity_id)
        if receipt is not None:
            return {"entity_id": entity_id, "kind": "TRANSITION_RECEIPT", "receipt": receipt.to_dict(),
                    "head_snapshot_id": head.snapshot_id, "api_version": API_VERSION}
        decision = self._decision(project_id, entity_id)
        if decision is not None:
            return {"entity_id": entity_id, "kind": "CONTROLLER_DECISION", "decision": decision.to_dict(),
                    "head_snapshot_id": head.snapshot_id, "api_version": API_VERSION}
        raise ApiError(ApiErrorCode.NOT_FOUND, HTTPStatus.NOT_FOUND, f"no evidence, transition or decision {entity_id!r}")

    def _run(self, project_id: str, invocation_id: str) -> dict[str, object]:
        with closing(self._connect_ro()) as db:
            row = db.execute(
                """SELECT a.workflow_id, a.activity_id FROM workflow_activities a
                   JOIN workflows w ON w.workflow_id = a.workflow_id
                   WHERE w.project_id=? AND json_extract(a.spec_json,'$.invocation_id')=?""",
                (project_id, invocation_id),
            ).fetchone()
        if row is None:
            raise ApiError(ApiErrorCode.NOT_FOUND, HTTPStatus.NOT_FOUND, f"no run with invocation {invocation_id!r}")
        workflow = self.workflows.workflow(row["workflow_id"])
        activity = self.workflows.activity(row["workflow_id"], row["activity_id"])
        events = self.workflows.events(row["workflow_id"])
        return {
            "invocation_id": invocation_id,
            "workflow": {"workflow_id": workflow.workflow_id, "project_id": workflow.project_id,
                         "project_snapshot_id": workflow.project_snapshot_id, "status": workflow.status.value,
                         "head_event_hash": workflow.head_event_hash},
            "activity": {"activity_id": activity.spec.activity_id, "spec": activity.spec.to_dict(),
                         "status": activity.status.value, "attempt_count": activity.attempt_count,
                         "result_digest": activity.result_digest, "last_error": activity.last_error},
            "events": [e.to_dict() for e in events],
            "history_intact": self.workflows.verify_history(row["workflow_id"]),
            "api_version": API_VERSION,
        }

    # --- dispatch --------------------------------------------------------------------

    @staticmethod
    def _receipt_response(outcome: MutationOutcome, env: MutationEnvelope) -> tuple[int, dict[str, object]]:
        body: dict[str, object] = {
            **outcome.receipt.to_dict(),
            "api_version": API_VERSION,
            "replayed": outcome.replayed,
            "persisted": outcome.persisted,
            "head_snapshot_id": outcome.head_snapshot_id,
            "client_payload_hash": env.payload_hash,
            "grants_scientific_authority": False,
            **dict(outcome.extra),
        }
        return RECEIPT_HTTP_STATUS[outcome.receipt.status], body

    def handle(self, method: str, path: str, headers: Mapping[str, str], body: bytes) -> tuple[int, dict[str, object], dict[str, str]]:
        trace_id = headers.get("X-Trace-Id") or Telemetry.new_trace_id()
        split = urlsplit(path)
        parts = [p for p in split.path.split("/") if p]
        query = parse_qs(split.query)
        resp_headers = {"X-Trace-Id": trace_id, "X-Api-Version": API_VERSION}

        if len(parts) < 2 or parts[0] != API_VERSION or parts[1] != "projects":
            return HTTPStatus.NOT_FOUND, ApiError(ApiErrorCode.NOT_FOUND, 404, "unknown route").to_dict(), resp_headers

        project_id = parts[2] if len(parts) > 2 else ""
        resource = parts[3] if len(parts) > 3 else "head"
        ident = parts[4] if len(parts) > 4 else None
        span_name = f"{method} /{resource}" if project_id else f"{method} /projects"

        with self.tel.span(span_name, trace_id=trace_id,
                           attributes={"project.id": project_id, "http.method": method}) as span:
            try:
                actor = self._authenticate(headers)
                span.attrs["actor.id"] = actor.actor_id

                if not project_id:
                    if method != "POST":
                        raise ApiError(ApiErrorCode.NOT_FOUND, HTTPStatus.NOT_FOUND, "no GET for /projects")
                    status, payload = self._create_project(actor, self._parse_body(body))
                    span.attrs["snapshot.id"] = payload["snapshot"]["snapshot_id"]  # type: ignore[index]
                    return status, payload, resp_headers

                head_id = self._safe_head_id(project_id)
                if head_id is not None:
                    span.attrs["snapshot.id"] = head_id

                if method == "GET":
                    self._authorize(actor, Capability.READ_EVIDENCE, project_id)
                    return HTTPStatus.OK, self._read(project_id, resource, ident, query), resp_headers

                if method == "POST":
                    if resource == "actions:plan" and ident is None:
                        self._authorize(actor, Capability.GOVERN, project_id)
                        return HTTPStatus.OK, self._plan(project_id, self._parse_body(body)), resp_headers
                    mutators = {"evidence": (Capability.WRITE_EVIDENCE, self._mutate_evidence),
                                "research-rounds": (Capability.EXECUTE, self._mutate_research_round),
                                "actions:execute": (Capability.EXECUTE, self._mutate_execute)}
                    if resource in mutators and ident is None:
                        cap, mutate = mutators[resource]
                        self._authorize(actor, cap, project_id)
                        env = self._validate_mutation(self._parse_body(body))
                        span.attrs["idempotency.key"] = env.idempotency_key
                        span.attrs["payload.hash"] = env.payload_hash
                        outcome = mutate(project_id, actor, env)
                        span.attrs["transition.status"] = outcome.receipt.status.value
                        span.attrs["receipt.id"] = outcome.receipt.transition_id
                        status, payload = self._receipt_response(outcome, env)
                        return status, payload, resp_headers

                raise ApiError(ApiErrorCode.NOT_FOUND, HTTPStatus.NOT_FOUND, f"no {method} for /{resource}")
            except ApiError as err:
                span.status = "ERROR"
                span.attrs["error.code"] = err.code.value
                return err.http_status, err.to_dict(), resp_headers

    def _read(self, project_id: str, resource: str, ident: str | None, query: Mapping[str, list[str]]) -> dict[str, object]:
        if resource in ("head", "snapshot") and ident is None:  # `/snapshot` is the pre-doc alias of `/head`
            return {**self._head(project_id).to_dict(), "api_version": API_VERSION}
        if resource == "snapshots" and ident:
            return {**self._snapshot_of(project_id, ident).to_dict(), "api_version": API_VERSION}
        if resource == "epistemic-status" and ident is None:
            return self._epistemic_status(project_id, query)
        if resource == "transitions" and ident:
            receipt = self._transition_by_id_or_key(project_id, ident)
            if receipt is None:
                raise ApiError(ApiErrorCode.NOT_FOUND, HTTPStatus.NOT_FOUND, f"no transition {ident!r}")
            return {**receipt.to_dict(), "grants_scientific_authority": False, "api_version": API_VERSION}
        if resource == "decisions" and ident:
            decision = self._decision(project_id, ident, (query.get("snapshot") or [None])[0])
            if decision is None:
                raise ApiError(ApiErrorCode.NOT_FOUND, HTTPStatus.NOT_FOUND, f"no decision {ident!r}")
            return {**decision.to_dict(), "decision_id": ident, "grants_scientific_authority": False, "api_version": API_VERSION}
        if resource == "runs" and ident:
            self._head(project_id)
            return self._run(project_id, ident)
        if resource == "provenance":
            return self._provenance(project_id, ident)
        raise ApiError(ApiErrorCode.NOT_FOUND, HTTPStatus.NOT_FOUND, f"no GET for /{resource}")


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
    "GENESIS_AUTHORITY_PROJECTION_REVISION", "IdentityProvider", "MutationEnvelope", "MutationOutcome",
    "RECEIPT_HTTP_STATUS", "SecretStore", "Span", "SpanExporter", "Telemetry", "content_hash", "serve",
]
