from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable

from .context_compiler import (
    ContextCompileReport,
    ContextCompileRequest,
    ContextCompileVerdict,
    ContextItem,
    compile_epistemic_context,
)
from .reference_profile import get_reference_profile


PROJECT_PROTOCOL_VERSION = "rakl-project-v1"
TASK_PACKET_VERSION = "rakl-task-packet-v1"


class ProjectRuntimeError(RuntimeError):
    pass


class PayloadIntegrityError(ProjectRuntimeError):
    pass


class TaskPacketVerdict(str, Enum):
    READY = "READY"
    CANNOT_COMPILE = "CANNOT_COMPILE"
    CANNOT_MATERIALIZE = "CANNOT_MATERIALIZE"


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=".rakl-tmp-", dir=path.parent)
    temp = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if temp.exists():
            temp.unlink()


@dataclass(frozen=True)
class StoredPayload:
    sha256: str
    size_bytes: int
    path: str

    def to_dict(self) -> dict[str, object]:
        return {"sha256": self.sha256, "size_bytes": self.size_bytes, "path": self.path}


class CanonicalPayloadStore:
    """Append-only, content-addressed canonical payload store.

    Object identity is SHA-256 over exact bytes.  Existing objects are verified before
    reuse; a corrupt object is never silently overwritten because doing so would erase
    evidence of a storage-integrity failure.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def path_for(self, digest: str) -> Path:
        if not _is_sha256(digest):
            raise ValueError("digest must be a lowercase SHA-256 hex string")
        return self.root / digest[:2] / digest

    def put_bytes(self, payload: bytes) -> StoredPayload:
        digest = _sha256(payload)
        target = self.path_for(digest)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.exists():
            existing = target.read_bytes()
            if _sha256(existing) != digest:
                raise PayloadIntegrityError(f"existing object failed digest verification: {digest}")
            return StoredPayload(digest, len(existing), str(target))

        fd, temp_name = tempfile.mkstemp(prefix=".rakl-object-", dir=target.parent)
        temp = Path(temp_name)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            if target.exists():
                existing = target.read_bytes()
                if _sha256(existing) != digest:
                    raise PayloadIntegrityError(f"concurrent object failed digest verification: {digest}")
            else:
                os.replace(temp, target)
            return StoredPayload(digest, len(payload), str(target))
        finally:
            if temp.exists():
                temp.unlink()

    def read_bytes(self, digest: str) -> bytes:
        path = self.path_for(digest)
        if not path.exists():
            raise KeyError(digest)
        payload = path.read_bytes()
        if _sha256(payload) != digest:
            raise PayloadIntegrityError(f"payload digest mismatch: {digest}")
        return payload

    def verify(self, digest: str) -> bool:
        try:
            self.read_bytes(digest)
        except (KeyError, PayloadIntegrityError):
            return False
        return True

    def object_count(self) -> int:
        if not self.root.exists():
            return 0
        return sum(
            1
            for path in self.root.rglob("*")
            if path.is_file() and not path.name.startswith(".rakl-")
        )


@dataclass(frozen=True)
class ProjectManifest:
    project_id: str
    reference_profile: str
    protocol_version: str = PROJECT_PROTOCOL_VERSION

    def __post_init__(self) -> None:
        if not self.project_id.strip():
            raise ValueError("project_id cannot be empty")
        get_reference_profile(self.reference_profile)
        if self.protocol_version != PROJECT_PROTOCOL_VERSION:
            raise ValueError(f"unsupported project protocol: {self.protocol_version}")

    def to_dict(self) -> dict[str, object]:
        return {
            "project_id": self.project_id,
            "reference_profile": self.reference_profile,
            "protocol_version": self.protocol_version,
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "ProjectManifest":
        return cls(
            project_id=str(value["project_id"]),
            reference_profile=str(value["reference_profile"]),
            protocol_version=str(value.get("protocol_version", PROJECT_PROTOCOL_VERSION)),
        )


@dataclass(frozen=True)
class RecordEnvelope:
    record_id: str
    payload_sha256: str
    token_cost: int
    kind: str = "SOURCE_PROJECTION"
    semantic_tags: tuple[str, ...] = ()
    fiber_ids: tuple[str, ...] = ()
    coverage_atoms: tuple[str, ...] = ()
    mandatory: bool = False

    def __post_init__(self) -> None:
        if not self.record_id:
            raise ValueError("record_id cannot be empty")
        if not _is_sha256(self.payload_sha256):
            raise ValueError("payload_sha256 must be a lowercase SHA-256 hex string")
        if self.token_cost <= 0:
            raise ValueError("token_cost must be positive")
        if not self.kind:
            raise ValueError("kind cannot be empty")
        for values, label in (
            (self.semantic_tags, "semantic_tags"),
            (self.fiber_ids, "fiber_ids"),
            (self.coverage_atoms, "coverage_atoms"),
        ):
            if len(set(values)) != len(values):
                raise ValueError(f"duplicate {label}")

    def to_dict(self) -> dict[str, object]:
        return {
            "record_id": self.record_id,
            "payload_sha256": self.payload_sha256,
            "token_cost": self.token_cost,
            "kind": self.kind,
            "semantic_tags": list(self.semantic_tags),
            "fiber_ids": list(self.fiber_ids),
            "coverage_atoms": list(self.coverage_atoms),
            "mandatory": self.mandatory,
        }

    @classmethod
    def from_dict(cls, value: dict[str, object]) -> "RecordEnvelope":
        return cls(
            record_id=str(value["record_id"]),
            payload_sha256=str(value["payload_sha256"]),
            token_cost=int(value["token_cost"]),
            kind=str(value.get("kind", "SOURCE_PROJECTION")),
            semantic_tags=tuple(str(item) for item in value.get("semantic_tags", [])),
            fiber_ids=tuple(str(item) for item in value.get("fiber_ids", [])),
            coverage_atoms=tuple(str(item) for item in value.get("coverage_atoms", [])),
            mandatory=bool(value.get("mandatory", False)),
        )


@dataclass(frozen=True)
class ProjectDoctorReport:
    healthy: bool
    project_id: str | None
    reference_profile: str | None
    record_count: int
    payload_count: int
    issues: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "healthy": self.healthy,
            "project_id": self.project_id,
            "reference_profile": self.reference_profile,
            "record_count": self.record_count,
            "payload_count": self.payload_count,
            "issues": list(self.issues),
        }


@dataclass(frozen=True)
class TaskPacketReport:
    verdict: TaskPacketVerdict
    compile_report: ContextCompileReport
    packet: dict[str, object] | None
    issues: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict.value,
            "compile_report": {
                "verdict": self.compile_report.verdict.value,
                "selected_record_ids": list(self.compile_report.selected_record_ids),
                "omitted_record_ids": list(self.compile_report.omitted_record_ids),
                "used_tokens": self.compile_report.used_tokens,
                "budget_tokens": self.compile_report.budget_tokens,
                "covered_atoms": list(self.compile_report.covered_atoms),
                "missing_required_atoms": list(self.compile_report.missing_required_atoms),
                "rehydration_record_ids": list(self.compile_report.rehydration_record_ids),
                "reasons": list(self.compile_report.reasons),
            },
            "packet": self.packet,
            "issues": list(self.issues),
        }


class RAKLProject:
    def __init__(self, root: Path, manifest: ProjectManifest) -> None:
        self.root = Path(root)
        self.rakl_dir = self.root / ".rakl"
        self.manifest_path = self.rakl_dir / "project.json"
        self.records_dir = self.rakl_dir / "records"
        self.packets_dir = self.rakl_dir / "packets"
        self.store = CanonicalPayloadStore(self.rakl_dir / "store" / "sha256")
        self.manifest = manifest

    @classmethod
    def create(
        cls,
        root: Path | str,
        *,
        project_id: str,
        reference_profile: str = "ordinary-8k",
    ) -> "RAKLProject":
        root_path = Path(root)
        manifest = ProjectManifest(project_id=project_id, reference_profile=reference_profile)
        manifest_path = root_path / ".rakl" / "project.json"
        if manifest_path.exists():
            existing = ProjectManifest.from_dict(json.loads(manifest_path.read_text("utf-8")))
            if existing != manifest:
                raise ProjectRuntimeError("existing project manifest is incompatible; refusing to rewrite")
            return cls(root_path, existing)

        (root_path / ".rakl" / "records").mkdir(parents=True, exist_ok=True)
        (root_path / ".rakl" / "packets").mkdir(parents=True, exist_ok=True)
        (root_path / ".rakl" / "store" / "sha256").mkdir(parents=True, exist_ok=True)
        _atomic_write(manifest_path, _canonical_json_bytes(manifest.to_dict()))
        return cls(root_path, manifest)

    @classmethod
    def open(cls, root: Path | str) -> "RAKLProject":
        root_path = Path(root)
        manifest_path = root_path / ".rakl" / "project.json"
        if not manifest_path.exists():
            raise ProjectRuntimeError(f"not a RAKL project: {root_path}")
        try:
            manifest = ProjectManifest.from_dict(json.loads(manifest_path.read_text("utf-8")))
        except (ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ProjectRuntimeError("invalid RAKL project manifest") from exc
        return cls(root_path, manifest)

    @staticmethod
    def _record_key(record_id: str) -> str:
        return hashlib.sha256(record_id.encode("utf-8")).hexdigest()

    def _record_path(self, record_id: str) -> Path:
        return self.records_dir / f"{self._record_key(record_id)}.json"

    def ingest_bytes(
        self,
        *,
        record_id: str,
        payload: bytes,
        token_cost: int,
        kind: str = "SOURCE_PROJECTION",
        semantic_tags: Iterable[str] = (),
        fiber_ids: Iterable[str] = (),
        coverage_atoms: Iterable[str] = (),
        mandatory: bool = False,
    ) -> RecordEnvelope:
        stored = self.store.put_bytes(payload)
        envelope = RecordEnvelope(
            record_id=record_id,
            payload_sha256=stored.sha256,
            token_cost=token_cost,
            kind=kind,
            semantic_tags=tuple(sorted(set(semantic_tags))),
            fiber_ids=tuple(sorted(set(fiber_ids))),
            coverage_atoms=tuple(sorted(set(coverage_atoms))),
            mandatory=mandatory,
        )
        path = self._record_path(record_id)
        if path.exists():
            existing = RecordEnvelope.from_dict(json.loads(path.read_text("utf-8")))
            if existing.record_id != record_id:
                raise ProjectRuntimeError("record key collision detected")
            if existing != envelope:
                raise ProjectRuntimeError("record_id is immutable and already refers to different content/metadata")
            return existing
        _atomic_write(path, _canonical_json_bytes(envelope.to_dict()))
        return envelope

    def ingest_file(self, path: Path | str, **kwargs: object) -> RecordEnvelope:
        return self.ingest_bytes(payload=Path(path).read_bytes(), **kwargs)

    def records(self) -> tuple[RecordEnvelope, ...]:
        if not self.records_dir.exists():
            return ()
        result: list[RecordEnvelope] = []
        for path in sorted(self.records_dir.glob("*.json")):
            value = json.loads(path.read_text("utf-8"))
            record = RecordEnvelope.from_dict(value)
            if path != self._record_path(record.record_id):
                raise ProjectRuntimeError(f"record metadata key mismatch: {record.record_id}")
            result.append(record)
        return tuple(sorted(result, key=lambda record: record.record_id))

    def doctor(self) -> ProjectDoctorReport:
        issues: list[str] = []
        records: tuple[RecordEnvelope, ...] = ()
        try:
            get_reference_profile(self.manifest.reference_profile)
        except KeyError:
            issues.append(f"unknown_reference_profile:{self.manifest.reference_profile}")
        try:
            records = self.records()
        except (OSError, ValueError, TypeError, KeyError, json.JSONDecodeError, ProjectRuntimeError) as exc:
            issues.append(f"record_index_invalid:{type(exc).__name__}")

        for record in records:
            try:
                self.store.read_bytes(record.payload_sha256)
            except KeyError:
                issues.append(f"missing_payload:{record.record_id}:{record.payload_sha256}")
            except PayloadIntegrityError:
                issues.append(f"payload_integrity_failure:{record.record_id}:{record.payload_sha256}")

        return ProjectDoctorReport(
            healthy=not issues,
            project_id=self.manifest.project_id,
            reference_profile=self.manifest.reference_profile,
            record_count=len(records),
            payload_count=self.store.object_count(),
            issues=tuple(sorted(issues)),
        )

    def epistemic_gate(
        self,
        service: object,
        *,
        target_id: str,
        fiber_id: str,
    ) -> dict[str, object]:
        """Consult the EpistemicStatus gate for this project's current head.

        Closes engineering fiber E9. The gate is passed in rather than imported:
        the runtime must be able to call it without depending on the engineering
        layer, and a caller without a service keeps the previous behaviour.

        The gate is allowed to refuse. An unavailable or stale status is reported
        as ``consulted`` with a reason, never silently omitted — a gate whose
        refusal disappears from the output is not a gate.
        """

        try:
            status = service.current_status(  # type: ignore[attr-defined]
                project_id=self.manifest.project_id,
                target_id=target_id,
                fiber_id=fiber_id,
            )
        except Exception as exc:  # the gate's own refusal types live one layer up
            return {
                "consulted": True,
                "available": False,
                "reason": f"{type(exc).__name__}: {exc}",
                "target_id": target_id,
                "fiber_id": fiber_id,
            }
        return {
            "consulted": True,
            "available": True,
            "target_id": target_id,
            "fiber_id": fiber_id,
            "project_snapshot_id": getattr(status, "project_snapshot_id", None),
            "status_id": getattr(status, "status_id", None),
        }

    def next_action(self, source: object) -> dict[str, object]:
        """Project an incumbent decision head into a next action.

        Closes engineering fiber E4. ``source`` may be a callable returning the
        action — which is how the engineering layer supplies it, as a closure
        over ``next_action_from_incumbent`` — or an object exposing
        ``next_action``. It is passed in rather than imported so the runtime
        gains no dependency on the engineering layer.

        The runtime reports what the head says. It does not decide, it grants
        nothing, and a source that yields no action is reported as carrying
        none rather than as ``wired`` with an empty value: the first version of
        this method duck-typed ``.next_action`` off the shipped
        ``IncumbentStateHeads``, which has no such attribute, and silently
        reported success while carrying nothing.
        """

        action = None
        resolved_by = "none"
        if callable(source):
            action = source()
            resolved_by = "callable"
        else:
            attr = getattr(source, "next_action", None)
            if callable(attr):
                action = attr()
                resolved_by = "next_action_method"
            elif attr is not None:
                action = attr
                resolved_by = "next_action_attribute"

        return {
            "wired": action is not None,
            "resolved_by": resolved_by,
            "next_action": None if action is None else str(action),
            "grants_scientific_authority": False,
        }

    def status(
        self,
        *,
        epistemic_service: object | None = None,
        target_id: str = "",
        fiber_id: str = "",
        heads: object | None = None,
    ) -> dict[str, object]:
        report = self.doctor()
        out: dict[str, object] = {
            "protocol_version": self.manifest.protocol_version,
            "project_id": self.manifest.project_id,
            "reference_profile": self.manifest.reference_profile,
            "record_count": report.record_count,
            "payload_count": report.payload_count,
            "healthy": report.healthy,
            "issues": list(report.issues),
        }
        if epistemic_service is not None:
            out["epistemic_gate"] = self.epistemic_gate(
                epistemic_service, target_id=target_id, fiber_id=fiber_id
            )
        if heads is not None:
            out["decision_heads"] = self.next_action(heads)
        return out

    def compile_task_packet(
        self,
        *,
        operation: str,
        question: str,
        budget_tokens: int | None = None,
        target_fibers: Iterable[str] = (),
        required_coverage_atoms: Iterable[str] = (),
    ) -> TaskPacketReport:
        if not operation.strip():
            raise ValueError("operation cannot be empty")
        if not question.strip():
            raise ValueError("question cannot be empty")

        profile = get_reference_profile(self.manifest.reference_profile)
        budget = profile.input_budget_tokens if budget_tokens is None else budget_tokens
        if budget < 0:
            raise ValueError("budget_tokens cannot be negative")
        if budget > profile.input_budget_tokens:
            raise ValueError(
                f"task budget {budget} exceeds profile input budget {profile.input_budget_tokens}"
            )

        records = self.records()
        items = tuple(
            ContextItem(
                record_id=record.record_id,
                token_cost=record.token_cost,
                coverage_atoms=record.coverage_atoms or record.semantic_tags,
                fiber_ids=record.fiber_ids,
                mandatory=record.mandatory,
            )
            for record in records
        )
        compile_report = compile_epistemic_context(
            items,
            ContextCompileRequest(
                budget_tokens=budget,
                target_fibers=tuple(sorted(set(target_fibers))),
                required_coverage_atoms=tuple(sorted(set(required_coverage_atoms))),
            ),
        )
        if compile_report.verdict != ContextCompileVerdict.COMPILED:
            return TaskPacketReport(
                verdict=TaskPacketVerdict.CANNOT_COMPILE,
                compile_report=compile_report,
                packet=None,
                issues=tuple(compile_report.reasons),
            )

        by_id = {record.record_id: record for record in records}
        materialized: list[dict[str, object]] = []
        issues: list[str] = []
        for record_id in compile_report.selected_record_ids:
            record = by_id[record_id]
            try:
                payload = self.store.read_bytes(record.payload_sha256)
                text = payload.decode("utf-8", errors="strict")
            except UnicodeDecodeError:
                issues.append(f"non_utf8_payload:{record_id}")
                continue
            except (KeyError, PayloadIntegrityError) as exc:
                issues.append(f"unmaterializable_payload:{record_id}:{type(exc).__name__}")
                continue
            materialized.append(
                {
                    "record_id": record.record_id,
                    "kind": record.kind,
                    "sha256": record.payload_sha256,
                    "token_cost": record.token_cost,
                    "mandatory": record.mandatory,
                    "semantic_tags": list(record.semantic_tags),
                    "fiber_ids": list(record.fiber_ids),
                    "coverage_atoms": list(record.coverage_atoms),
                    "text": text,
                }
            )

        if issues:
            return TaskPacketReport(
                verdict=TaskPacketVerdict.CANNOT_MATERIALIZE,
                compile_report=compile_report,
                packet=None,
                issues=tuple(sorted(issues)),
            )

        packet: dict[str, object] = {
            "packet_version": TASK_PACKET_VERSION,
            "project_id": self.manifest.project_id,
            "reference_profile": profile.to_dict(),
            "operation": operation.strip(),
            "question": question.strip(),
            "target_fibers": list(tuple(sorted(set(target_fibers)))),
            "context_budget_tokens": budget,
            "selected_records": materialized,
            "source_digests": [item["sha256"] for item in materialized],
            "epistemic_rules": [
                "projection/context before competition",
                "representation is not mechanism",
                "LLM output is proposal-only",
                "negative evidence remains addressable",
                "missing evidence must be reported rather than guessed",
            ],
            "authority_boundary": {
                "llm_output_authority": "PROPOSAL_ONLY",
                "may_promote_canonical_knowledge": False,
                "may_mint_mechanistic_or_decision_authority": False,
            },
            "required_output": {
                "format": "JSON_OBJECT",
                "fields": [
                    "proposal",
                    "evidence_used",
                    "uncertainties",
                    "contradictions_or_obstructions",
                    "next_discriminator",
                    "status",
                ],
                "allowed_status": [
                    "SUPPORTED_PROPOSAL",
                    "REFUTED_PROPOSAL",
                    "PARTIALLY_IDENTIFIED",
                    "BLOCKED",
                    "CANNOT_CHECK",
                ],
            },
        }
        return TaskPacketReport(
            verdict=TaskPacketVerdict.READY,
            compile_report=compile_report,
            packet=packet,
            issues=(),
        )

    @staticmethod
    def canonical_packet_json(packet: dict[str, object]) -> str:
        return _canonical_json_bytes(packet).decode("utf-8")
