from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Mapping

from .project_runtime import RAKLProject


EXECUTION_PROTOCOL_VERSION = "rakl-execution-v1"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _atomic_text(path: Path, text: str) -> None:
    # Project-runtime metadata already uses an atomic replace protocol.  Here the
    # event/ref files are immutable once created, so exclusive creation is enough.
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    fd = os.open(path, flags, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise


class ExecutionStatus(str, Enum):
    PREPARED = "PREPARED"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED_PROCESS = "FAILED_PROCESS"
    FAILED_PROTOCOL = "FAILED_PROTOCOL"
    FAILED_START = "FAILED_START"
    TIMED_OUT = "TIMED_OUT"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"


TERMINAL_STATUSES = frozenset(
    {
        ExecutionStatus.COMPLETED,
        ExecutionStatus.FAILED_PROCESS,
        ExecutionStatus.FAILED_PROTOCOL,
        ExecutionStatus.FAILED_START,
        ExecutionStatus.TIMED_OUT,
    }
)


@dataclass(frozen=True)
class RunnerContract:
    runner_id: str
    model_id: str
    model_version: str
    argv: tuple[str, ...]
    timeout_seconds: float = 120.0
    expects_json: bool = True
    retry_safe: bool = False
    allowed_env_names: tuple[str, ...] = ()
    environment_revision: str = "none"

    def __post_init__(self) -> None:
        if not self.runner_id.strip():
            raise ValueError("runner_id cannot be empty")
        if not self.model_id.strip():
            raise ValueError("model_id cannot be empty")
        if not self.model_version.strip():
            raise ValueError("model_version cannot be empty")
        if not self.argv or not self.argv[0]:
            raise ValueError("argv must contain an executable")
        if not Path(self.argv[0]).is_absolute():
            raise ValueError("runner executable must be an absolute path")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if len(set(self.allowed_env_names)) != len(self.allowed_env_names):
            raise ValueError("duplicate allowed environment variable names")
        if any(not name or "=" in name for name in self.allowed_env_names):
            raise ValueError("invalid allowed environment variable name")
        if self.allowed_env_names and not self.environment_revision.strip():
            raise ValueError("environment_revision is required when environment variables are used")

    def public_dict(self) -> dict[str, object]:
        return {
            "runner_id": self.runner_id,
            "model_id": self.model_id,
            "model_version": self.model_version,
            "argv": list(self.argv),
            "argv_sha256": _sha256(_canonical_bytes(list(self.argv))),
            "timeout_seconds": self.timeout_seconds,
            "expects_json": self.expects_json,
            "retry_safe": self.retry_safe,
            "allowed_env_names": list(sorted(self.allowed_env_names)),
            "environment_revision": self.environment_revision,
            "shell": False,
        }


@dataclass(frozen=True)
class ExecutionSpec:
    protocol_version: str
    packet_sha256: str
    runner: RunnerContract
    generation_config: dict[str, object]
    execution_nonce: str

    @classmethod
    def build(
        cls,
        *,
        packet_bytes: bytes,
        runner: RunnerContract,
        generation_config: Mapping[str, object] | None = None,
        execution_nonce: str = "default",
    ) -> "ExecutionSpec":
        config = dict(generation_config or {})
        # Fail before execution if config is not canonical-JSON serializable.
        _canonical_bytes(config)
        if not execution_nonce:
            raise ValueError("execution_nonce cannot be empty")
        return cls(
            protocol_version=EXECUTION_PROTOCOL_VERSION,
            packet_sha256=_sha256(packet_bytes),
            runner=runner,
            generation_config=config,
            execution_nonce=execution_nonce,
        )

    def identity_dict(self) -> dict[str, object]:
        return {
            "protocol_version": self.protocol_version,
            "packet_sha256": self.packet_sha256,
            "runner": self.runner.public_dict(),
            "generation_config": self.generation_config,
            "execution_nonce": self.execution_nonce,
        }

    @property
    def invocation_id(self) -> str:
        return _sha256(_canonical_bytes(self.identity_dict()))


@dataclass(frozen=True)
class ExecutionEvent:
    invocation_id: str
    sequence: int
    attempt: int
    status: ExecutionStatus
    timestamp_utc: str
    previous_event_sha256: str | None
    details: dict[str, object]

    def to_dict(self) -> dict[str, object]:
        return {
            "invocation_id": self.invocation_id,
            "sequence": self.sequence,
            "attempt": self.attempt,
            "status": self.status.value,
            "timestamp_utc": self.timestamp_utc,
            "previous_event_sha256": self.previous_event_sha256,
            "details": self.details,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "ExecutionEvent":
        return cls(
            invocation_id=str(value["invocation_id"]),
            sequence=int(value["sequence"]),
            attempt=int(value["attempt"]),
            status=ExecutionStatus(str(value["status"])),
            timestamp_utc=str(value["timestamp_utc"]),
            previous_event_sha256=(
                None if value.get("previous_event_sha256") is None else str(value["previous_event_sha256"])
            ),
            details=dict(value.get("details", {})),
        )


@dataclass(frozen=True)
class ExecutionReceipt:
    invocation_id: str
    status: ExecutionStatus
    packet_sha256: str
    runner: dict[str, object]
    generation_config: dict[str, object]
    execution_nonce: str
    attempt: int
    started_at_utc: str | None
    completed_at_utc: str
    duration_ms: int | None
    exit_code: int | None
    stdout_sha256: str | None
    stderr_sha256: str | None
    stdout_size_bytes: int
    stderr_size_bytes: int
    event_chain_head_sha256: str
    protocol_valid: bool | None
    output_authority: str = "PROPOSAL_ONLY"
    may_promote_canonical_knowledge: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "invocation_id": self.invocation_id,
            "status": self.status.value,
            "packet_sha256": self.packet_sha256,
            "runner": self.runner,
            "generation_config": self.generation_config,
            "execution_nonce": self.execution_nonce,
            "attempt": self.attempt,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": self.completed_at_utc,
            "duration_ms": self.duration_ms,
            "exit_code": self.exit_code,
            "stdout_sha256": self.stdout_sha256,
            "stderr_sha256": self.stderr_sha256,
            "stdout_size_bytes": self.stdout_size_bytes,
            "stderr_size_bytes": self.stderr_size_bytes,
            "event_chain_head_sha256": self.event_chain_head_sha256,
            "protocol_valid": self.protocol_valid,
            "output_authority": self.output_authority,
            "may_promote_canonical_knowledge": self.may_promote_canonical_knowledge,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> "ExecutionReceipt":
        return cls(
            invocation_id=str(value["invocation_id"]),
            status=ExecutionStatus(str(value["status"])),
            packet_sha256=str(value["packet_sha256"]),
            runner=dict(value["runner"]),
            generation_config=dict(value.get("generation_config", {})),
            execution_nonce=str(value["execution_nonce"]),
            attempt=int(value["attempt"]),
            started_at_utc=None if value.get("started_at_utc") is None else str(value["started_at_utc"]),
            completed_at_utc=str(value["completed_at_utc"]),
            duration_ms=None if value.get("duration_ms") is None else int(value["duration_ms"]),
            exit_code=None if value.get("exit_code") is None else int(value["exit_code"]),
            stdout_sha256=None if value.get("stdout_sha256") is None else str(value["stdout_sha256"]),
            stderr_sha256=None if value.get("stderr_sha256") is None else str(value["stderr_sha256"]),
            stdout_size_bytes=int(value.get("stdout_size_bytes", 0)),
            stderr_size_bytes=int(value.get("stderr_size_bytes", 0)),
            event_chain_head_sha256=str(value["event_chain_head_sha256"]),
            protocol_valid=None if value.get("protocol_valid") is None else bool(value["protocol_valid"]),
            output_authority=str(value.get("output_authority", "PROPOSAL_ONLY")),
            may_promote_canonical_knowledge=bool(value.get("may_promote_canonical_knowledge", False)),
        )


@dataclass(frozen=True)
class ExecutionResult:
    status: ExecutionStatus
    invocation_id: str
    receipt: ExecutionReceipt | None
    replayed: bool
    reason: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "invocation_id": self.invocation_id,
            "replayed": self.replayed,
            "reason": self.reason,
            "receipt": None if self.receipt is None else self.receipt.to_dict(),
        }


class ExecutionLedger:
    def __init__(self, project: RAKLProject, spec: ExecutionSpec) -> None:
        self.project = project
        self.spec = spec
        self.run_dir = project.rakl_dir / "runs" / spec.invocation_id
        self.events_dir = self.run_dir / "events"
        self.spec_ref = self.run_dir / "spec.ref"
        self.receipt_ref = self.run_dir / "receipt.ref"

    def ensure_spec(self) -> None:
        payload = _canonical_bytes(self.spec.identity_dict())
        stored = self.project.store.put_bytes(payload)
        self.run_dir.mkdir(parents=True, exist_ok=True)
        if self.spec_ref.exists():
            existing = self.spec_ref.read_text("utf-8").strip()
            if existing != stored.sha256:
                raise RuntimeError("execution spec reference mismatch")
        else:
            _atomic_text(self.spec_ref, stored.sha256 + "\n")

        reloaded = self.project.store.read_bytes(stored.sha256)
        if _sha256(reloaded) != stored.sha256 or self.spec.invocation_id != _sha256(reloaded):
            # invocation id is SHA over exactly the canonical identity object.
            raise RuntimeError("execution spec identity verification failed")

    def _event_refs(self) -> list[Path]:
        if not self.events_dir.exists():
            return []
        return sorted(self.events_dir.glob("*.ref"))

    def events(self) -> tuple[tuple[ExecutionEvent, str], ...]:
        result: list[tuple[ExecutionEvent, str]] = []
        previous: str | None = None
        for expected_sequence, path in enumerate(self._event_refs(), start=1):
            digest = path.read_text("utf-8").strip()
            payload = self.project.store.read_bytes(digest)
            if _sha256(payload) != digest:
                raise RuntimeError("event digest mismatch")
            event = ExecutionEvent.from_dict(json.loads(payload.decode("utf-8")))
            if event.invocation_id != self.spec.invocation_id:
                raise RuntimeError("event invocation identity mismatch")
            if event.sequence != expected_sequence:
                raise RuntimeError("event sequence mismatch")
            if event.previous_event_sha256 != previous:
                raise RuntimeError("event chain mismatch")
            if path.name != f"{expected_sequence:06d}.ref":
                raise RuntimeError("event reference filename mismatch")
            result.append((event, digest))
            previous = digest
        return tuple(result)

    def append(self, *, attempt: int, status: ExecutionStatus, details: Mapping[str, object] | None = None) -> tuple[ExecutionEvent, str]:
        existing = self.events()
        sequence = len(existing) + 1
        previous = existing[-1][1] if existing else None
        event = ExecutionEvent(
            invocation_id=self.spec.invocation_id,
            sequence=sequence,
            attempt=attempt,
            status=status,
            timestamp_utc=_utc_now(),
            previous_event_sha256=previous,
            details=dict(details or {}),
        )
        payload = _canonical_bytes(event.to_dict())
        stored = self.project.store.put_bytes(payload)
        ref = self.events_dir / f"{sequence:06d}.ref"
        _atomic_text(ref, stored.sha256 + "\n")
        return event, stored.sha256

    def load_receipt(self) -> ExecutionReceipt | None:
        if not self.receipt_ref.exists():
            return None
        digest = self.receipt_ref.read_text("utf-8").strip()
        payload = self.project.store.read_bytes(digest)
        if _sha256(payload) != digest:
            raise RuntimeError("receipt digest mismatch")
        receipt = ExecutionReceipt.from_dict(json.loads(payload.decode("utf-8")))
        if receipt.invocation_id != self.spec.invocation_id:
            raise RuntimeError("receipt invocation identity mismatch")
        self.verify_receipt(receipt)
        return receipt

    def verify_receipt(self, receipt: ExecutionReceipt) -> None:
        events = self.events()
        if not events:
            raise RuntimeError("receipt exists without execution events")
        terminal_event, head_digest = events[-1]
        if terminal_event.status not in TERMINAL_STATUSES:
            raise RuntimeError("receipt event chain does not end in a terminal state")
        if receipt.status != terminal_event.status:
            raise RuntimeError("receipt status mismatch")
        if receipt.event_chain_head_sha256 != head_digest:
            raise RuntimeError("receipt event chain head mismatch")
        if receipt.packet_sha256 != self.spec.packet_sha256:
            raise RuntimeError("receipt packet identity mismatch")
        if receipt.output_authority != "PROPOSAL_ONLY" or receipt.may_promote_canonical_knowledge:
            raise RuntimeError("receipt authority boundary invalid")

    def commit_receipt(self, receipt: ExecutionReceipt) -> ExecutionReceipt:
        self.verify_receipt(receipt)
        payload = _canonical_bytes(receipt.to_dict())
        stored = self.project.store.put_bytes(payload)
        if self.receipt_ref.exists():
            existing = self.receipt_ref.read_text("utf-8").strip()
            if existing != stored.sha256:
                raise RuntimeError("attempted to replace an immutable execution receipt")
        else:
            _atomic_text(self.receipt_ref, stored.sha256 + "\n")
        return receipt


class ExecutionManager:
    def __init__(self, project: RAKLProject) -> None:
        self.project = project

    def build_spec(
        self,
        *,
        packet_bytes: bytes,
        runner: RunnerContract,
        generation_config: Mapping[str, object] | None = None,
        execution_nonce: str = "default",
    ) -> ExecutionSpec:
        return ExecutionSpec.build(
            packet_bytes=packet_bytes,
            runner=runner,
            generation_config=generation_config,
            execution_nonce=execution_nonce,
        )

    def execute(
        self,
        *,
        packet_bytes: bytes,
        runner: RunnerContract,
        generation_config: Mapping[str, object] | None = None,
        execution_nonce: str = "default",
        environment: Mapping[str, str] | None = None,
    ) -> ExecutionResult:
        # The runner receives exact task-packet bytes on stdin.  Config is bound into
        # invocation identity and receipt but is not injected into the packet.
        try:
            parsed_packet = json.loads(packet_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError("task packet must be valid UTF-8 JSON") from exc
        if not isinstance(parsed_packet, dict):
            raise ValueError("task packet must be a JSON object")

        supplied_env = dict(environment or {})
        allowed = set(runner.allowed_env_names)
        if set(supplied_env) - allowed:
            raise ValueError("environment contains variables not allowed by runner contract")
        missing = allowed - set(supplied_env)
        if missing:
            raise ValueError(f"missing declared runner environment variables: {sorted(missing)}")

        spec = self.build_spec(
            packet_bytes=packet_bytes,
            runner=runner,
            generation_config=generation_config,
            execution_nonce=execution_nonce,
        )
        ledger = ExecutionLedger(self.project, spec)
        ledger.ensure_spec()
        # Preserve the exact packet in the project CAS regardless of whether the
        # caller originally provided it as an external file.
        stored_packet = self.project.store.put_bytes(packet_bytes)
        if stored_packet.sha256 != spec.packet_sha256:
            raise RuntimeError("task packet digest changed during storage")

        existing_receipt = ledger.load_receipt()
        if existing_receipt is not None:
            return ExecutionResult(
                status=existing_receipt.status,
                invocation_id=spec.invocation_id,
                receipt=existing_receipt,
                replayed=True,
            )

        events = ledger.events()
        attempt = 1
        if events:
            last_event, _ = events[-1]
            if last_event.status in TERMINAL_STATUSES:
                receipt = self._recover_terminal_receipt(spec, ledger, events)
                return ExecutionResult(
                    status=receipt.status,
                    invocation_id=spec.invocation_id,
                    receipt=receipt,
                    replayed=True,
                )
            if last_event.status == ExecutionStatus.RUNNING:
                return ExecutionResult(
                    status=ExecutionStatus.RECOVERY_REQUIRED,
                    invocation_id=spec.invocation_id,
                    receipt=None,
                    replayed=True,
                    reason="prior_attempt_may_still_have_executed",
                )
            if last_event.status in {ExecutionStatus.PREPARED, ExecutionStatus.RECOVERY_REQUIRED}:
                if not runner.retry_safe:
                    if last_event.status != ExecutionStatus.RECOVERY_REQUIRED:
                        ledger.append(
                            attempt=last_event.attempt,
                            status=ExecutionStatus.RECOVERY_REQUIRED,
                            details={"reason": "non_idempotent_ambiguous_prepared_attempt"},
                        )
                    return ExecutionResult(
                        status=ExecutionStatus.RECOVERY_REQUIRED,
                        invocation_id=spec.invocation_id,
                        receipt=None,
                        replayed=True,
                        reason="non_idempotent_ambiguous_prepared_attempt",
                    )
                attempt = max(event.attempt for event, _ in events) + 1

        prepared, _ = ledger.append(
            attempt=attempt,
            status=ExecutionStatus.PREPARED,
            details={"environment_names": list(sorted(runner.allowed_env_names))},
        )
        running, _ = ledger.append(
            attempt=attempt,
            status=ExecutionStatus.RUNNING,
            details={"prepared_sequence": prepared.sequence},
        )
        started_at = running.timestamp_utc
        started = time.monotonic()

        stdout = b""
        stderr = b""
        exit_code: int | None = None
        protocol_valid: bool | None = None
        status: ExecutionStatus
        terminal_details: dict[str, object] = {}

        try:
            completed = subprocess.run(
                list(runner.argv),
                input=packet_bytes,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=runner.timeout_seconds,
                check=False,
                shell=False,
                cwd=self.project.root,
                env=supplied_env,
            )
            stdout = completed.stdout or b""
            stderr = completed.stderr or b""
            exit_code = completed.returncode
            if exit_code != 0:
                status = ExecutionStatus.FAILED_PROCESS
                protocol_valid = None
            elif runner.expects_json:
                try:
                    parsed_output = json.loads(stdout.decode("utf-8"))
                    protocol_valid = isinstance(parsed_output, dict)
                except (UnicodeDecodeError, json.JSONDecodeError):
                    protocol_valid = False
                status = ExecutionStatus.COMPLETED if protocol_valid else ExecutionStatus.FAILED_PROTOCOL
            else:
                protocol_valid = None
                status = ExecutionStatus.COMPLETED
        except subprocess.TimeoutExpired as exc:
            status = ExecutionStatus.TIMED_OUT
            protocol_valid = None
            stdout = exc.stdout or b""
            stderr = exc.stderr or b""
            terminal_details["timeout_seconds"] = runner.timeout_seconds
        except OSError as exc:
            status = ExecutionStatus.FAILED_START
            protocol_valid = None
            terminal_details["start_error_type"] = type(exc).__name__

        duration_ms = max(0, round((time.monotonic() - started) * 1000))
        stdout_obj = self.project.store.put_bytes(stdout) if status != ExecutionStatus.FAILED_START else None
        stderr_obj = self.project.store.put_bytes(stderr) if status != ExecutionStatus.FAILED_START else None
        terminal_details.update(
            {
                "exit_code": exit_code,
                "stdout_sha256": None if stdout_obj is None else stdout_obj.sha256,
                "stderr_sha256": None if stderr_obj is None else stderr_obj.sha256,
                "protocol_valid": protocol_valid,
                "duration_ms": duration_ms,
            }
        )
        terminal_event, terminal_digest = ledger.append(
            attempt=attempt,
            status=status,
            details=terminal_details,
        )
        receipt = ExecutionReceipt(
            invocation_id=spec.invocation_id,
            status=status,
            packet_sha256=spec.packet_sha256,
            runner=runner.public_dict(),
            generation_config=spec.generation_config,
            execution_nonce=spec.execution_nonce,
            attempt=attempt,
            started_at_utc=started_at,
            completed_at_utc=terminal_event.timestamp_utc,
            duration_ms=duration_ms,
            exit_code=exit_code,
            stdout_sha256=None if stdout_obj is None else stdout_obj.sha256,
            stderr_sha256=None if stderr_obj is None else stderr_obj.sha256,
            stdout_size_bytes=len(stdout),
            stderr_size_bytes=len(stderr),
            event_chain_head_sha256=terminal_digest,
            protocol_valid=protocol_valid,
        )
        ledger.commit_receipt(receipt)
        return ExecutionResult(
            status=status,
            invocation_id=spec.invocation_id,
            receipt=receipt,
            replayed=False,
        )

    def _recover_terminal_receipt(
        self,
        spec: ExecutionSpec,
        ledger: ExecutionLedger,
        events: tuple[tuple[ExecutionEvent, str], ...],
    ) -> ExecutionReceipt:
        terminal, digest = events[-1]
        details = terminal.details
        running = [event for event, _ in events if event.attempt == terminal.attempt and event.status == ExecutionStatus.RUNNING]
        started_at = running[-1].timestamp_utc if running else None
        receipt = ExecutionReceipt(
            invocation_id=spec.invocation_id,
            status=terminal.status,
            packet_sha256=spec.packet_sha256,
            runner=spec.runner.public_dict(),
            generation_config=spec.generation_config,
            execution_nonce=spec.execution_nonce,
            attempt=terminal.attempt,
            started_at_utc=started_at,
            completed_at_utc=terminal.timestamp_utc,
            duration_ms=None if details.get("duration_ms") is None else int(details["duration_ms"]),
            exit_code=None if details.get("exit_code") is None else int(details["exit_code"]),
            stdout_sha256=None if details.get("stdout_sha256") is None else str(details["stdout_sha256"]),
            stderr_sha256=None if details.get("stderr_sha256") is None else str(details["stderr_sha256"]),
            stdout_size_bytes=(
                0
                if details.get("stdout_sha256") is None
                else len(self.project.store.read_bytes(str(details["stdout_sha256"])))
            ),
            stderr_size_bytes=(
                0
                if details.get("stderr_sha256") is None
                else len(self.project.store.read_bytes(str(details["stderr_sha256"])))
            ),
            event_chain_head_sha256=digest,
            protocol_valid=None if details.get("protocol_valid") is None else bool(details["protocol_valid"]),
        )
        return ledger.commit_receipt(receipt)

    def read_stdout(self, receipt: ExecutionReceipt) -> bytes:
        if receipt.stdout_sha256 is None:
            return b""
        return self.project.store.read_bytes(receipt.stdout_sha256)

    def read_stderr(self, receipt: ExecutionReceipt) -> bytes:
        if receipt.stderr_sha256 is None:
            return b""
        return self.project.store.read_bytes(receipt.stderr_sha256)
