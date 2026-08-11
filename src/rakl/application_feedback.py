"""Fail-closed, proposal-only application feedback ingestion.

The application repository is an evidence producer, never an authority over the
RAKL framework.  This module verifies an immutable, content-bound transport
bundle and emits an immutable quarantine receipt.  It deliberately exposes no
API that mutates the research-tool inventory, failure lattice, method registry,
or promotion state.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Mapping, Sequence, Tuple
from urllib.parse import urlparse

from .failure_lattice import FailureDiagnosisStatus, FailureExperience
from .research_tool_inventory import ResearchTool, ResearchToolAuthority


BUNDLE_SCHEMA_VERSION = "application-feedback-bundle-v1"
RECEIPT_SCHEMA_VERSION = "application-feedback-import-receipt-v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_GIT_OID_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


class FeedbackKind(str, Enum):
    FAILURE_EXPERIENCE = "FAILURE_EXPERIENCE"
    TOOL_CANDIDATE = "TOOL_CANDIDATE"
    META_OBSERVATION = "META_OBSERVATION"


class FeedbackImportVerdict(str, Enum):
    QUARANTINED_PROPOSAL = "QUARANTINED_PROPOSAL"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


def canonical_json_bytes(value: object) -> bytes:
    """Return the UTF-8 RFC-8259-compatible representation used for hashing."""

    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def canonical_json_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def _bundle_hash(document: Mapping[str, object]) -> str:
    subject = dict(document)
    subject.pop("bundle_canonical_sha256", None)
    return canonical_json_sha256(subject)


@dataclass(frozen=True)
class RepositoryPin:
    repository_namespace: str
    repository_url: str
    commit_sha: str
    tree_sha: str

    def to_dict(self) -> dict[str, str]:
        return {
            "repository_namespace": self.repository_namespace,
            "repository_url": self.repository_url,
            "commit_sha": self.commit_sha,
            "tree_sha": self.tree_sha,
        }


@dataclass(frozen=True)
class FeedbackItem:
    item_id: str
    kind: FeedbackKind
    source_path: str
    source_blob_sha: str
    payload_json: str
    payload_canonical_sha256: str
    result_id: str
    result_sha256: str
    trace_event_id: str
    trace_sha256: str
    context_sha256: str
    observed_at_utc: str
    supersedes: Tuple[str, ...] = ()

    @property
    def payload(self) -> dict[str, object]:
        # Return a new object so callers cannot mutate the immutable transport.
        return json.loads(self.payload_json)

    def to_dict(self) -> dict[str, object]:
        return {
            "item_id": self.item_id,
            "kind": self.kind.value,
            "source": {
                "path": self.source_path,
                "git_blob_sha": self.source_blob_sha,
            },
            "payload": self.payload,
            "payload_canonical_sha256": self.payload_canonical_sha256,
            "application_bindings": {
                "result_id": self.result_id,
                "result_sha256": self.result_sha256,
                "trace_event_id": self.trace_event_id,
                "trace_sha256": self.trace_sha256,
                "context_sha256": self.context_sha256,
                "observed_at_utc": self.observed_at_utc,
            },
            "supersedes": list(self.supersedes),
        }


@dataclass(frozen=True)
class ApplicationFeedbackBundle:
    schema_version: str
    bundle_id: str
    bundle_canonical_sha256: str
    producer: RepositoryPin
    framework_repository_url: str
    framework_commit_sha: str
    framework_version: str
    requested_authority: str
    proposal_only: bool
    inventory_mutation_allowed: bool
    failure_lattice_mutation_allowed: bool
    promotion_allowed: bool
    previous_bundle_id: str | None
    previous_bundle_canonical_sha256: str | None
    items: Tuple[FeedbackItem, ...]

    def to_dict(self) -> dict[str, object]:
        previous: dict[str, str] | None = None
        if self.previous_bundle_id is not None:
            previous = {
                "bundle_id": self.previous_bundle_id,
                "bundle_canonical_sha256": self.previous_bundle_canonical_sha256 or "",
            }
        return {
            "schema_version": self.schema_version,
            "bundle_id": self.bundle_id,
            "bundle_canonical_sha256": self.bundle_canonical_sha256,
            "producer": self.producer.to_dict(),
            "framework_requirement": {
                "repository_url": self.framework_repository_url,
                "commit_sha": self.framework_commit_sha,
                "version": self.framework_version,
            },
            "authority_envelope": {
                "requested_authority": self.requested_authority,
                "proposal_only": self.proposal_only,
                "inventory_mutation_allowed": self.inventory_mutation_allowed,
                "failure_lattice_mutation_allowed": self.failure_lattice_mutation_allowed,
                "promotion_allowed": self.promotion_allowed,
            },
            "previous_bundle": previous,
            "items": [item.to_dict() for item in self.items],
        }


@dataclass(frozen=True)
class FeedbackImportReceipt:
    schema_version: str
    receipt_id: str
    bundle_id: str
    bundle_canonical_sha256: str
    producer: RepositoryPin | None
    verdict: FeedbackImportVerdict
    reasons: Tuple[str, ...]
    requested_authority: str | None
    effective_authority: str
    quarantined_item_ids: Tuple[str, ...]
    item_records: Tuple[Tuple[str, str, str], ...]
    preserved_item_ids: Tuple[str, ...]
    supersession_edges: Tuple[Tuple[str, str], ...]
    authority_downgrades: Tuple[str, ...]
    inventory_mutation_performed: bool = False
    failure_lattice_mutation_performed: bool = False

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    @property
    def grants_method_promotion(self) -> bool:
        return False

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "receipt_id": self.receipt_id,
            "bundle_id": self.bundle_id,
            "bundle_canonical_sha256": self.bundle_canonical_sha256,
            "producer": self.producer.to_dict() if self.producer else None,
            "verdict": self.verdict.value,
            "reasons": list(self.reasons),
            "requested_authority": self.requested_authority,
            "effective_authority": self.effective_authority,
            "quarantined_item_ids": list(self.quarantined_item_ids),
            "item_records": [
                {"item_id": item_id, "kind": kind, "payload_canonical_sha256": digest}
                for item_id, kind, digest in self.item_records
            ],
            "preserved_item_ids": list(self.preserved_item_ids),
            "supersession_edges": [
                {"source_item_id": source, "superseded_item_id": target}
                for source, target in self.supersession_edges
            ],
            "authority_downgrades": list(self.authority_downgrades),
            "mutation": {
                "inventory_mutation_performed": self.inventory_mutation_performed,
                "failure_lattice_mutation_performed": self.failure_lattice_mutation_performed,
            },
            "grants_scientific_authority": False,
            "grants_method_promotion": False,
        }


def _mapping(value: object, *, name: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name}_missing_or_invalid")
    return value


def _required_text(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key}_missing")
    return value.strip()


def _payload_strings(
    payload: Mapping[str, object], key: str, *, default: Sequence[str] | None = None
) -> Tuple[str, ...]:
    value = payload.get(key, list(default) if default is not None else None)
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"payload field {key!r} must be a string array")
    return tuple(value)


def parse_application_feedback_bundle(
    document: Mapping[str, object],
) -> ApplicationFeedbackBundle:
    """Parse a structurally valid v1 document into deeply immutable records."""

    if document.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        raise ValueError("unknown_bundle_schema_version")
    producer_data = _mapping(document.get("producer"), name="producer")
    producer = RepositoryPin(
        repository_namespace=_required_text(producer_data, "repository_namespace"),
        repository_url=_required_text(producer_data, "repository_url"),
        commit_sha=_required_text(producer_data, "commit_sha"),
        tree_sha=_required_text(producer_data, "tree_sha"),
    )
    framework = _mapping(document.get("framework_requirement"), name="framework_requirement")
    authority = _mapping(document.get("authority_envelope"), name="authority_envelope")
    raw_items = document.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValueError("items_missing_or_invalid")
    items: list[FeedbackItem] = []
    for index, raw in enumerate(raw_items):
        item = _mapping(raw, name=f"item_{index}")
        source = _mapping(item.get("source"), name=f"item_{index}_source")
        bindings = _mapping(
            item.get("application_bindings"), name=f"item_{index}_application_bindings"
        )
        payload = _mapping(item.get("payload"), name=f"item_{index}_payload")
        raw_supersedes = item.get("supersedes", [])
        if not isinstance(raw_supersedes, list) or not all(
            isinstance(value, str) and value.strip() for value in raw_supersedes
        ):
            raise ValueError(f"item_{index}:supersedes_invalid")
        try:
            kind = FeedbackKind(_required_text(item, "kind"))
        except ValueError as exc:
            raise ValueError(f"item_{index}:kind_unknown") from exc
        items.append(
            FeedbackItem(
                item_id=_required_text(item, "item_id"),
                kind=kind,
                source_path=_required_text(source, "path"),
                source_blob_sha=_required_text(source, "git_blob_sha"),
                payload_json=canonical_json_bytes(payload).decode("utf-8"),
                payload_canonical_sha256=_required_text(item, "payload_canonical_sha256"),
                result_id=_required_text(bindings, "result_id"),
                result_sha256=_required_text(bindings, "result_sha256"),
                trace_event_id=_required_text(bindings, "trace_event_id"),
                trace_sha256=_required_text(bindings, "trace_sha256"),
                context_sha256=_required_text(bindings, "context_sha256"),
                observed_at_utc=_required_text(bindings, "observed_at_utc"),
                supersedes=tuple(value.strip() for value in raw_supersedes),
            )
        )
    previous_data = document.get("previous_bundle")
    previous_id: str | None = None
    previous_hash: str | None = None
    if previous_data is not None:
        previous = _mapping(previous_data, name="previous_bundle")
        previous_id = _required_text(previous, "bundle_id")
        previous_hash = _required_text(previous, "bundle_canonical_sha256")
    return ApplicationFeedbackBundle(
        schema_version=BUNDLE_SCHEMA_VERSION,
        bundle_id=_required_text(document, "bundle_id"),
        bundle_canonical_sha256=_required_text(document, "bundle_canonical_sha256"),
        producer=producer,
        framework_repository_url=_required_text(framework, "repository_url"),
        framework_commit_sha=_required_text(framework, "commit_sha"),
        framework_version=_required_text(framework, "version"),
        requested_authority=_required_text(authority, "requested_authority"),
        proposal_only=authority.get("proposal_only") is True,
        inventory_mutation_allowed=authority.get("inventory_mutation_allowed") is True,
        failure_lattice_mutation_allowed=authority.get("failure_lattice_mutation_allowed") is True,
        promotion_allowed=authority.get("promotion_allowed") is True,
        previous_bundle_id=previous_id,
        previous_bundle_canonical_sha256=previous_hash,
        items=tuple(items),
    )


def _parse_time(value: str) -> bool:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def _safe_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(value) and not path.is_absolute() and ".." not in path.parts and "\\" not in value


def _git(repo: Path, *args: str) -> tuple[bool, str]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            capture_output=True,
            text=False,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, ""
    if result.returncode != 0:
        return False, ""
    return True, result.stdout.decode("utf-8", errors="strict").strip()


def _git_bytes(repo: Path, *args: str) -> tuple[bool, bytes]:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo), *args],
            check=False,
            capture_output=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False, b""
    return (result.returncode == 0, result.stdout if result.returncode == 0 else b"")


def _normalize_repo_url(value: str) -> str:
    normalized = value.strip().rstrip("/")
    return normalized[:-4] if normalized.endswith(".git") else normalized


def _namespace_from_repo_url(value: str) -> str | None:
    """Derive the stable host/path namespace for common remote URL forms."""

    normalized = _normalize_repo_url(value)
    parsed = urlparse(normalized)
    if parsed.scheme and parsed.hostname:
        path = parsed.path.strip("/")
        return f"{parsed.hostname.lower()}/{path}" if path else parsed.hostname.lower()
    match = re.fullmatch(r"(?:[^@]+@)?([^:]+):(.+)", normalized)
    if match:
        return f"{match.group(1).lower()}/{match.group(2).strip('/')}"
    return None


def _receipt(
    *,
    bundle: ApplicationFeedbackBundle | None,
    raw_document: Mapping[str, object],
    verdict: FeedbackImportVerdict,
    reasons: Sequence[str],
    prior_receipts: Sequence[FeedbackImportReceipt],
) -> FeedbackImportReceipt:
    bundle_id_raw = raw_document.get("bundle_id")
    bundle_hash_raw = raw_document.get("bundle_canonical_sha256")
    bundle_id = bundle.bundle_id if bundle else (bundle_id_raw if isinstance(bundle_id_raw, str) else "UNBOUND")
    bundle_hash = (
        bundle.bundle_canonical_sha256
        if bundle
        else (bundle_hash_raw if isinstance(bundle_hash_raw, str) else _bundle_hash(raw_document))
    )
    current_records = (
        tuple((item.item_id, item.kind.value, item.payload_canonical_sha256) for item in bundle.items)
        if bundle and verdict is FeedbackImportVerdict.QUARANTINED_PROPOSAL
        else ()
    )
    prior_records = tuple(record for prior in prior_receipts for record in prior.item_records)
    preserved = set(item_id for item_id, _, _ in prior_records)
    if bundle and verdict is FeedbackImportVerdict.QUARANTINED_PROPOSAL:
        preserved.update(
            item.item_id for item in bundle.items if item.kind is FeedbackKind.FAILURE_EXPERIENCE
        )
    supersession_edges = (
        tuple(
            sorted(
                (item.item_id, target)
                for item in bundle.items
                for target in item.supersedes
            )
        )
        if bundle and verdict is FeedbackImportVerdict.QUARANTINED_PROPOSAL
        else ()
    )
    requested = bundle.requested_authority if bundle else None
    downgrades: tuple[str, ...] = ()
    if requested and requested != ResearchToolAuthority.HEURISTIC.value:
        downgrades = (f"foreign_authority_downgraded:{requested}->HEURISTIC",)
    reason_tuple = tuple(sorted(set(reasons)))
    seed = {
        "schema_version": RECEIPT_SCHEMA_VERSION,
        "bundle_id": bundle_id,
        "bundle_canonical_sha256": bundle_hash,
        "producer": bundle.producer.to_dict() if bundle else None,
        "verdict": verdict.value,
        "reasons": list(reason_tuple),
        "requested_authority": requested,
        "effective_authority": ResearchToolAuthority.HEURISTIC.value,
        "quarantined_item_ids": [row[0] for row in current_records],
        "item_records": current_records,
        "preserved_item_ids": sorted(preserved),
        "supersession_edges": supersession_edges,
        "authority_downgrades": downgrades,
    }
    receipt_id = f"rakl::application-feedback-import::{canonical_json_sha256(seed)}"
    return FeedbackImportReceipt(
        schema_version=RECEIPT_SCHEMA_VERSION,
        receipt_id=receipt_id,
        bundle_id=bundle_id,
        bundle_canonical_sha256=bundle_hash,
        producer=bundle.producer if bundle else None,
        verdict=verdict,
        reasons=reason_tuple,
        requested_authority=requested,
        effective_authority=ResearchToolAuthority.HEURISTIC.value,
        quarantined_item_ids=tuple(row[0] for row in current_records),
        item_records=current_records,
        preserved_item_ids=tuple(sorted(preserved)),
        supersession_edges=supersession_edges,
        authority_downgrades=downgrades,
    )


def import_application_feedback(
    document: Mapping[str, object],
    *,
    source_repository: Path,
    current_framework_commit_sha: str,
    current_framework_version: str,
    prior_receipts: Sequence[FeedbackImportReceipt] = (),
) -> FeedbackImportReceipt:
    """Audit a bundle and return a deterministic proposal-only receipt.

    ``QUARANTINED_PROPOSAL`` means only that transport and chronology bindings
    passed.  It is not evidence that a lesson is true, reusable, novel, or a
    valid framework change.
    """

    if document.get("schema_version") != BUNDLE_SCHEMA_VERSION:
        return _receipt(
            bundle=None,
            raw_document=document,
            verdict=FeedbackImportVerdict.CANNOT_CHECK,
            reasons=("unknown_bundle_schema_version",),
            prior_receipts=prior_receipts,
        )
    # Collect identity-reference omissions before constructing the immutable
    # value objects.  Reporting all missing refs makes the negative receipt a
    # useful repair packet rather than exposing only the first parser failure.
    missing_refs: list[str] = []
    raw_items = document.get("items")
    if isinstance(raw_items, list):
        for index, raw_item in enumerate(raw_items):
            if not isinstance(raw_item, Mapping):
                continue
            raw_id = raw_item.get("item_id")
            label = raw_id if isinstance(raw_id, str) and raw_id else str(index)
            bindings = raw_item.get("application_bindings")
            if not isinstance(bindings, Mapping):
                missing_refs.append(f"item:{label}:application_bindings_missing")
                continue
            for key in ("result_id", "trace_event_id"):
                value = bindings.get(key)
                if not isinstance(value, str) or not value.strip():
                    missing_refs.append(f"item:{label}:{key}_missing")
    if missing_refs:
        return _receipt(
            bundle=None,
            raw_document=document,
            verdict=FeedbackImportVerdict.CANNOT_CHECK,
            reasons=missing_refs,
            prior_receipts=prior_receipts,
        )
    try:
        bundle = parse_application_feedback_bundle(document)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        return _receipt(
            bundle=None,
            raw_document=document,
            verdict=FeedbackImportVerdict.CANNOT_CHECK,
            reasons=(str(exc),),
            prior_receipts=prior_receipts,
        )

    for prior in prior_receipts:
        if prior.bundle_id != bundle.bundle_id:
            continue
        if prior.bundle_canonical_sha256 == bundle.bundle_canonical_sha256:
            return prior
        return _receipt(
            bundle=bundle,
            raw_document=document,
            verdict=FeedbackImportVerdict.REJECT,
            reasons=("bundle_id_collision",),
            prior_receipts=prior_receipts,
        )

    reject: list[str] = []
    cannot: list[str] = []
    declared_hash = bundle.bundle_canonical_sha256
    if not _SHA256_RE.fullmatch(declared_hash) or declared_hash != _bundle_hash(document):
        reject.append("bundle_canonical_sha256_mismatch")
    if not _GIT_OID_RE.fullmatch(bundle.producer.commit_sha):
        reject.append("producer_commit_sha_invalid")
    if not _GIT_OID_RE.fullmatch(bundle.producer.tree_sha):
        reject.append("producer_tree_sha_invalid")
    namespace_prefix = bundle.producer.repository_namespace + "::"
    derived_namespace = _namespace_from_repo_url(bundle.producer.repository_url)
    if derived_namespace is not None and derived_namespace != bundle.producer.repository_namespace:
        reject.append("producer_namespace_repository_mismatch")
    if not bundle.bundle_id.startswith(namespace_prefix):
        reject.append("bundle_id_not_namespaced")
    item_ids = tuple(item.item_id for item in bundle.items)
    if len(set(item_ids)) != len(item_ids):
        reject.append("duplicate_item_id_in_bundle")
    for item in bundle.items:
        prefix = f"item:{item.item_id}:"
        if not item.item_id.startswith(namespace_prefix):
            reject.append(prefix + "item_id_not_namespaced")
        if not _safe_path(item.source_path):
            reject.append(prefix + "source_path_invalid")
        if not _GIT_OID_RE.fullmatch(item.source_blob_sha):
            reject.append(prefix + "source_blob_invalid")
        if not _SHA256_RE.fullmatch(item.payload_canonical_sha256):
            reject.append(prefix + "payload_canonical_sha256_invalid")
        elif canonical_json_sha256(item.payload) != item.payload_canonical_sha256:
            reject.append(prefix + "payload_canonical_sha256_mismatch")
        for name, digest in (
            ("result_sha256", item.result_sha256),
            ("trace_sha256", item.trace_sha256),
            ("context_sha256", item.context_sha256),
        ):
            if not _SHA256_RE.fullmatch(digest):
                reject.append(prefix + name + "_invalid")
        if not item.result_id:
            cannot.append(prefix + "result_id_missing")
        if not item.trace_event_id:
            cannot.append(prefix + "trace_event_id_missing")
        if not _parse_time(item.observed_at_utc):
            cannot.append(prefix + "observed_at_utc_missing_or_invalid")
        if item.item_id in item.supersedes:
            reject.append(prefix + "cannot_supersede_self")
        if len(set(item.supersedes)) != len(item.supersedes):
            reject.append(prefix + "duplicate_supersession_target")
        payload = item.payload
        if item.kind is FeedbackKind.FAILURE_EXPERIENCE:
            required = {
                "failure_id",
                "atom_id",
                "candidate_id",
                "context_packet_hash",
                "research_trace_event_id",
                "method_family",
                "failure_mode",
                "residual_signature",
                "scope_conditions",
                "competing_diagnoses",
                "diagnosis_status",
                "evidence_pointers",
                "falsifier_or_attempt",
                "observed_result",
                "artifact_hash",
                "timestamp",
            }
            for key in sorted(required - payload.keys()):
                cannot.append(prefix + f"failure_payload_{key}_missing")
            if payload.get("research_trace_event_id") != item.trace_event_id:
                reject.append(prefix + "payload_trace_identity_mismatch")
            if payload.get("context_packet_hash") != item.context_sha256:
                reject.append(prefix + "payload_context_identity_mismatch")
            if payload.get("artifact_hash") != item.result_sha256:
                reject.append(prefix + "payload_result_hash_mismatch")
        elif item.kind is FeedbackKind.TOOL_CANDIDATE:
            required = {
                "tool_id",
                "name",
                "kind",
                "abstraction",
                "source_atom_id",
                "source_candidate_id",
                "source_result_ids",
                "source_context_hash",
                "preconditions",
                "structural_signature",
                "operation",
                "guaranteed_effects",
                "non_guarantees",
                "validation_obligations",
                "evidence_pointers",
                "artifact_hash",
            }
            for key in sorted(required - payload.keys()):
                cannot.append(prefix + f"tool_payload_{key}_missing")
            source_results = payload.get("source_result_ids")
            if not isinstance(source_results, list) or item.result_id not in source_results:
                reject.append(prefix + "payload_result_identity_mismatch")
            if payload.get("source_context_hash") != item.context_sha256:
                reject.append(prefix + "payload_context_identity_mismatch")
            if payload.get("artifact_hash") != item.result_sha256:
                reject.append(prefix + "payload_result_hash_mismatch")
        else:
            required = {
                "observation_id",
                "method_surface",
                "observation",
                "evidence_pointers",
                "candidate_framework_delta",
                "validation_status",
            }
            for key in sorted(required - payload.keys()):
                cannot.append(prefix + f"meta_payload_{key}_missing")
            pointers = payload.get("evidence_pointers")
            if not isinstance(pointers, list) or not {
                item.result_id,
                item.trace_event_id,
            }.issubset(set(str(value) for value in pointers)):
                reject.append(prefix + "payload_result_trace_identity_mismatch")

    if (
        not bundle.proposal_only
        or bundle.inventory_mutation_allowed
        or bundle.failure_lattice_mutation_allowed
        or bundle.promotion_allowed
    ):
        reject.append("authority_envelope_not_proposal_only")
    if bundle.framework_commit_sha != current_framework_commit_sha:
        cannot.append("framework_commit_pin_stale")
    if bundle.framework_version != current_framework_version:
        cannot.append("framework_version_pin_stale")

    prior_by_bundle = {prior.bundle_id: prior for prior in prior_receipts}
    prior_items = {
        item_id: (kind, payload_hash)
        for prior in prior_receipts
        for item_id, kind, payload_hash in prior.item_records
    }
    if bundle.previous_bundle_id is not None:
        previous_receipt = prior_by_bundle.get(bundle.previous_bundle_id)
        if previous_receipt is None:
            cannot.append("previous_bundle_receipt_missing")
        elif previous_receipt.bundle_canonical_sha256 != bundle.previous_bundle_canonical_sha256:
            reject.append("previous_bundle_hash_mismatch")
    elif any(item.supersedes for item in bundle.items):
        cannot.append("previous_bundle_binding_missing_for_supersession")
    for item in bundle.items:
        prior_record = prior_items.get(item.item_id)
        if prior_record is not None:
            if prior_record[1] == item.payload_canonical_sha256:
                reject.append(f"duplicate_item_id_across_bundles:{item.item_id}")
            else:
                reject.append(f"item_id_collision:{item.item_id}")
        for target in item.supersedes:
            if target not in prior_items:
                cannot.append(f"supersession_target_missing:{target}")
    successor_sets: dict[str, set[str]] = {}
    for item in bundle.items:
        for target in item.supersedes:
            successor_sets.setdefault(target, set()).add(item.item_id)
    for target, successors in sorted(successor_sets.items()):
        if len(successors) > 1:
            reject.append(f"ambiguous_supersession:{target}")

    repo = Path(source_repository)
    ok, head = _git(repo, "rev-parse", "HEAD")
    if not ok:
        cannot.append("producer_repository_unavailable")
    elif head != bundle.producer.commit_sha:
        cannot.append("producer_checkout_not_at_pinned_commit")
    ok, remote = _git(repo, "remote", "get-url", "origin")
    if not ok:
        cannot.append("producer_origin_url_unavailable")
    elif _normalize_repo_url(remote) != _normalize_repo_url(bundle.producer.repository_url):
        reject.append("producer_repository_url_mismatch")
    ok, tree = _git(repo, "rev-parse", f"{bundle.producer.commit_sha}^{{tree}}")
    if not ok:
        cannot.append("producer_commit_unavailable")
    elif tree != bundle.producer.tree_sha:
        reject.append("producer_tree_mismatch")

    if ok:
        typed, object_type = _git(repo, "cat-file", "-t", bundle.producer.commit_sha)
        if not typed:
            cannot.append("producer_commit_type_unavailable")
        elif object_type != "commit":
            reject.append("producer_pin_is_not_commit")
        for item in bundle.items:
            prefix = f"item:{item.item_id}:"
            found, blob = _git(
                repo, "rev-parse", f"{bundle.producer.commit_sha}:{item.source_path}"
            )
            if not found:
                cannot.append(prefix + "source_path_missing_at_commit")
                continue
            if blob != item.source_blob_sha:
                reject.append(prefix + "source_blob_mismatch")
                continue
            typed, object_type = _git(repo, "cat-file", "-t", blob)
            if not typed:
                cannot.append(prefix + "source_object_type_unavailable")
                continue
            if object_type != "blob":
                reject.append(prefix + "source_object_is_not_blob")
                continue
            loaded, source_bytes = _git_bytes(
                repo, "show", f"{bundle.producer.commit_sha}:{item.source_path}"
            )
            if not loaded:
                cannot.append(prefix + "source_blob_unreadable")
                continue
            try:
                source_payload = json.loads(source_bytes)
            except (UnicodeDecodeError, json.JSONDecodeError):
                reject.append(prefix + "source_payload_not_json")
                continue
            if canonical_json_sha256(source_payload) != item.payload_canonical_sha256:
                reject.append(prefix + "source_payload_hash_mismatch")

    if reject:
        verdict = FeedbackImportVerdict.REJECT
        reasons = reject + cannot
    elif cannot:
        verdict = FeedbackImportVerdict.CANNOT_CHECK
        reasons = cannot
    else:
        verdict = FeedbackImportVerdict.QUARANTINED_PROPOSAL
        reasons = [
            "all_transport_bindings_verified",
            "application_feedback_remains_proposal_only",
            "no_inventory_lattice_or_promotion_mutation_performed",
        ]
    return _receipt(
        bundle=bundle,
        raw_document=document,
        verdict=verdict,
        reasons=reasons,
        prior_receipts=prior_receipts,
    )


def _stage_item(
    bundle: ApplicationFeedbackBundle,
    receipt: FeedbackImportReceipt,
    item_id: str,
    kind: FeedbackKind,
) -> FeedbackItem:
    if receipt.verdict is not FeedbackImportVerdict.QUARANTINED_PROPOSAL:
        raise ValueError("staging requires an acceptable quarantined receipt")
    if (
        receipt.bundle_id != bundle.bundle_id
        or receipt.bundle_canonical_sha256 != bundle.bundle_canonical_sha256
    ):
        raise ValueError("receipt is not bound to this feedback bundle")
    if item_id not in receipt.quarantined_item_ids:
        raise ValueError("feedback item is not quarantined by this receipt")
    matches = tuple(item for item in bundle.items if item.item_id == item_id)
    if len(matches) != 1 or matches[0].kind is not kind:
        raise ValueError(f"feedback item is not a {kind.value}")
    return matches[0]


def stage_feedback_failure(
    bundle: ApplicationFeedbackBundle,
    receipt: FeedbackImportReceipt,
    item_id: str,
) -> FailureExperience:
    """Materialize a failure proposal without adding it to a lattice."""

    item = _stage_item(bundle, receipt, item_id, FeedbackKind.FAILURE_EXPERIENCE)
    payload = item.payload
    return FailureExperience(
        failure_id=str(payload["failure_id"]),
        atom_id=str(payload["atom_id"]),
        candidate_id=str(payload["candidate_id"]),
        context_packet_hash=str(payload["context_packet_hash"]),
        research_trace_event_id=str(payload["research_trace_event_id"]),
        method_family=str(payload["method_family"]),
        failure_mode=str(payload["failure_mode"]),
        residual_signature=_payload_strings(payload, "residual_signature"),
        broken_assumptions=_payload_strings(payload, "broken_assumptions"),
        scope_conditions=_payload_strings(payload, "scope_conditions"),
        competing_diagnoses=_payload_strings(payload, "competing_diagnoses"),
        selected_diagnosis=str(payload["selected_diagnosis"]),
        diagnosis_status=FailureDiagnosisStatus(str(payload["diagnosis_status"])),
        evidence_pointers=_payload_strings(payload, "evidence_pointers"),
        falsifier_or_attempt=str(payload["falsifier_or_attempt"]),
        observed_result=str(payload["observed_result"]),
        artifact_hash=str(payload["artifact_hash"]),
        timestamp=str(payload["timestamp"]),
        local_repair_attempts=_payload_strings(payload, "local_repair_attempts", default=()),
    )


def stage_feedback_tool_candidate(
    bundle: ApplicationFeedbackBundle,
    receipt: FeedbackImportReceipt,
    item_id: str,
) -> ResearchTool:
    """Materialize a HEURISTIC candidate without adding it to an inventory."""

    item = _stage_item(bundle, receipt, item_id, FeedbackKind.TOOL_CANDIDATE)
    payload = item.payload
    obligations = list(_payload_strings(payload, "validation_obligations"))
    for required in ("DifferenceWitness", "ToolApplicabilityWitness"):
        if required not in obligations:
            obligations.append(required)
    return ResearchTool(
        tool_id=str(payload["tool_id"]),
        name=str(payload["name"]),
        kind=str(payload["kind"]),
        abstraction=str(payload["abstraction"]),
        source_atom_id=str(payload["source_atom_id"]),
        source_candidate_id=str(payload["source_candidate_id"]),
        source_result_ids=_payload_strings(payload, "source_result_ids"),
        source_context_hash=str(payload["source_context_hash"]),
        authority=ResearchToolAuthority.HEURISTIC,
        preconditions=_payload_strings(payload, "preconditions"),
        structural_signature=_payload_strings(payload, "structural_signature"),
        operation=str(payload["operation"]),
        guaranteed_effects=_payload_strings(payload, "guaranteed_effects"),
        non_guarantees=_payload_strings(payload, "non_guarantees"),
        validation_obligations=tuple(obligations),
        evidence_pointers=_payload_strings(payload, "evidence_pointers"),
        known_failure_ids=_payload_strings(payload, "known_failure_ids", default=()),
        successful_reuse_ids=_payload_strings(payload, "successful_reuse_ids", default=()),
        proof_backing=_payload_strings(payload, "proof_backing", default=()),
        artifact_hash=str(payload["artifact_hash"]),
    )


def stage_feedback_meta_observation(
    bundle: ApplicationFeedbackBundle,
    receipt: FeedbackImportReceipt,
    item_id: str,
) -> dict[str, object]:
    """Return a detached unvalidated meta-observation proposal."""

    item = _stage_item(bundle, receipt, item_id, FeedbackKind.META_OBSERVATION)
    payload = item.payload
    payload["validation_status"] = "UNVALIDATED_PROPOSAL"
    payload["import_state"] = "QUARANTINED_PROPOSAL"
    payload["grants_method_promotion"] = False
    return payload
