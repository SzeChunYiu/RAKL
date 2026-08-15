"""E11, E15, E17, E19, E20: observatory read model, backup verifier, capacity budgets,
build provenance, and the operator doctor.

Each fibre's falsifier is the design constraint, restated at the top of its section.
Everything here is local, deterministic and tested. What each does NOT claim is
stated inline, because several of these fibres have a second half that needs a
production environment, and pretending otherwise is how "closed" stops meaning
anything.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Callable, Mapping, Sequence

# ---------------------------------------------------------------------------
# E11 — observatory read model
#   falsifier: UI recomputes its own epistemic score, or cannot drill to exact
#              receipts/evidence
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ObservatoryView:
    """A read-only projection of stored status. It carries what it was given.

    The load-bearing property is negative: there is no method on this class
    that computes saturation, freshness or a score. It renders stored values
    and links each to the id of the object it came from, so a reader can drill
    from any displayed number to the exact canonical record.
    """

    project_id: str
    snapshot_id: str
    status_id: str
    saturation_axes: Mapping[str, object]
    route_coverage: Mapping[str, object]
    freshness: str
    residuals: Sequence[str]
    hard_gates: Mapping[str, str]
    controller_decision: str
    costs: Mapping[str, object]
    workflow_states: Mapping[str, str]
    provenance_ids: Mapping[str, str]  # displayed field -> canonical object id

    def render(self) -> str:
        lines = [
            f"ORION OBSERVATORY  project={self.project_id}  snapshot={self.snapshot_id}  status={self.status_id}",
            f"  freshness         {self.freshness}",
            f"  saturation axes   {dict(self.saturation_axes)}",
            f"  route coverage    {dict(self.route_coverage)}",
            f"  residuals         {list(self.residuals)}",
            f"  hard gates        {dict(self.hard_gates)}",
            f"  controller        {self.controller_decision}",
            f"  costs             {dict(self.costs)}",
            f"  workflows         {dict(self.workflow_states)}",
            "  drill-down:",
        ]
        for shown, oid in sorted(self.provenance_ids.items()):
            lines.append(f"    {shown:<18} -> {oid}")
        return "\n".join(lines)


def project_observatory(stored_status: Mapping[str, object]) -> ObservatoryView:
    """Build the view from a stored EpistemicStatus record. Computes nothing.

    Every displayed field is read from the record or from an id it names. If a
    field is absent it renders as absent — it is never derived from other fields.
    """

    def get(key: str, default: object) -> object:
        return stored_status.get(key, default)

    return ObservatoryView(
        project_id=str(get("project_id", "")),
        snapshot_id=str(get("project_snapshot_id", "")),
        status_id=str(get("status_id", "")),
        saturation_axes=dict(get("saturation_axes", {}) or {}),
        route_coverage=dict(get("route_coverage", {}) or {}),
        freshness=str(get("freshness", "UNKNOWN")),
        residuals=tuple(get("residual_ids", ()) or ()),
        hard_gates=dict(get("hard_gates", {}) or {}),
        controller_decision=str(get("controller_decision", "")),
        costs=dict(get("costs", {}) or {}),
        workflow_states=dict(get("workflow_states", {}) or {}),
        provenance_ids=dict(get("provenance_ids", {}) or {}),
    )


# ---------------------------------------------------------------------------
# E15 — backup/restore
#   falsifier: restore does not reproduce exact state
#   Claimed here: a content-addressed backup manifest whose restore is verified
#   byte-for-byte, with corruption and missing-blob detection.
#   NOT claimed: PostgreSQL WAL/PITR semantics — that needs a PostgreSQL.
# ---------------------------------------------------------------------------


class RestoreVerdict(str, Enum):
    EXACT = "EXACT"
    CORRUPTED_BLOB = "CORRUPTED_BLOB"
    MISSING_BLOB = "MISSING_BLOB"
    MANIFEST_TAMPERED = "MANIFEST_TAMPERED"


@dataclass(frozen=True)
class BackupManifest:
    backup_id: str
    created_at: str
    entries: Mapping[str, str]  # relative path -> sha256
    manifest_digest: str = ""

    def __post_init__(self) -> None:
        expected = hashlib.sha256(
            json.dumps({"id": self.backup_id, "at": self.created_at, "entries": dict(sorted(self.entries.items()))},
                       sort_keys=True).encode()
        ).hexdigest()
        if self.manifest_digest and self.manifest_digest != expected:
            raise ValueError("manifest digest does not bind its entries")
        if not self.manifest_digest:
            object.__setattr__(self, "manifest_digest", expected)


def take_backup(root: Path, *, backup_id: str, created_at: str) -> BackupManifest:
    entries = {}
    for p in sorted(root.rglob("*")):
        if p.is_file():
            entries[str(p.relative_to(root))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return BackupManifest(backup_id, created_at, entries)


def verify_restore(root: Path, manifest: BackupManifest) -> tuple[RestoreVerdict, tuple[str, ...]]:
    """Restore into an EMPTY environment must reproduce every byte the manifest names."""

    try:
        BackupManifest(manifest.backup_id, manifest.created_at, manifest.entries, manifest.manifest_digest)
    except ValueError:
        return RestoreVerdict.MANIFEST_TAMPERED, ()
    missing, corrupted = [], []
    for rel, digest in manifest.entries.items():
        p = root / rel
        if not p.exists():
            missing.append(rel)
        elif hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            corrupted.append(rel)
    if missing:
        return RestoreVerdict.MISSING_BLOB, tuple(missing)
    if corrupted:
        return RestoreVerdict.CORRUPTED_BLOB, tuple(corrupted)
    return RestoreVerdict.EXACT, ()


# ---------------------------------------------------------------------------
# E17 — capacity/SLO
#   falsifier: capacity exhaustion yields partial state corruption
#   Claimed here: an explicit resource budget whose exhaustion is a TYPED refusal
#   before any state changes, plus an SLO envelope with measured p50/p95.
#   NOT claimed: production load numbers — those need production hardware.
# ---------------------------------------------------------------------------


class BudgetVerdict(str, Enum):
    ADMITTED = "ADMITTED"
    REFUSED_OVER_BUDGET = "REFUSED_OVER_BUDGET"
    DEGRADED = "DEGRADED"


@dataclass
class ResourceBudget:
    """Admission control. Refusal happens BEFORE any mutation, so exhaustion never half-writes."""

    max_inflight: int
    max_queue: int
    degrade_at_inflight: int
    inflight: int = 0
    queued: int = 0
    refused: int = 0
    degraded: int = 0

    def admit(self) -> BudgetVerdict:
        if self.inflight >= self.max_inflight:
            if self.queued >= self.max_queue:
                self.refused += 1
                return BudgetVerdict.REFUSED_OVER_BUDGET
            self.queued += 1
            return BudgetVerdict.DEGRADED  # queued, not running: backpressure
        self.inflight += 1
        if self.inflight >= self.degrade_at_inflight:
            self.degraded += 1
            return BudgetVerdict.DEGRADED
        return BudgetVerdict.ADMITTED

    def release(self) -> None:
        if self.queued > 0:
            self.queued -= 1
        elif self.inflight > 0:
            self.inflight -= 1


@dataclass(frozen=True)
class SloEnvelope:
    name: str
    p50_ms: float
    p95_ms: float
    samples: int
    budget_p95_ms: float

    @property
    def within(self) -> bool:
        return self.p95_ms <= self.budget_p95_ms


def measure_slo(name: str, op: Callable[[], object], *, samples: int, budget_p95_ms: float) -> SloEnvelope:
    times = []
    for _ in range(samples):
        t0 = time.perf_counter()
        op()
        times.append((time.perf_counter() - t0) * 1000.0)
    times.sort()
    p50 = times[len(times) // 2]
    p95 = times[min(len(times) - 1, int(len(times) * 0.95))]
    return SloEnvelope(name, p50, p95, samples, budget_p95_ms)


# ---------------------------------------------------------------------------
# E19 — build provenance
#   falsifier: declared model/argv/version strings count as executable identity
#   Claimed here: a provenance record binding source commit, lock digest, build
#   procedure digest, artifact digest and config digest, verified against the
#   actual artifact bytes. Mutable tags without a digest are rejected.
# ---------------------------------------------------------------------------


class ProvenanceVerdict(str, Enum):
    VERIFIED = "VERIFIED"
    ARTIFACT_MISMATCH = "ARTIFACT_MISMATCH"
    MUTABLE_TAG_WITHOUT_DIGEST = "MUTABLE_TAG_WITHOUT_DIGEST"
    MISSING_FIELD = "MISSING_FIELD"


@dataclass(frozen=True)
class BuildProvenance:
    source_commit: str
    lock_digest: str
    build_procedure_digest: str
    artifact_ref: str        # e.g. image@sha256:... — must carry a digest
    artifact_digest: str
    config_digest: str
    release_manifest_digest: str

    def verify(self, artifact_bytes: bytes) -> ProvenanceVerdict:
        for f in ("source_commit", "lock_digest", "build_procedure_digest", "artifact_digest",
                  "config_digest", "release_manifest_digest"):
            if not getattr(self, f):
                return ProvenanceVerdict.MISSING_FIELD
        if "@sha256:" not in self.artifact_ref:
            return ProvenanceVerdict.MUTABLE_TAG_WITHOUT_DIGEST
        if hashlib.sha256(artifact_bytes).hexdigest() != self.artifact_digest:
            return ProvenanceVerdict.ARTIFACT_MISMATCH
        return ProvenanceVerdict.VERIFIED


# ---------------------------------------------------------------------------
# E20 — operator doctor
#   falsifier: an operator cannot tell which subsystem is unhealthy
#   Claimed here: a doctor that runs registered probes and reports each with a
#   typed status; a probe that cannot run is CANNOT_CHECK, never OK.
#   NOT claimed: the live drill on a production release.
# ---------------------------------------------------------------------------


class ProbeStatus(str, Enum):
    OK = "OK"
    DEGRADED = "DEGRADED"
    FAIL = "FAIL"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class ProbeResult:
    subsystem: str
    status: ProbeStatus
    detail: str = ""


@dataclass
class OperatorDoctor:
    probes: dict[str, Callable[[], ProbeResult]] = field(default_factory=dict)

    def register(self, subsystem: str, probe: Callable[[], ProbeResult]) -> None:
        self.probes[subsystem] = probe

    def run(self) -> tuple[ProbeResult, ...]:
        out = []
        for name, probe in sorted(self.probes.items()):
            try:
                out.append(probe())
            except Exception as exc:  # noqa: BLE001 — a probe that throws did not check
                out.append(ProbeResult(name, ProbeStatus.CANNOT_CHECK, f"{type(exc).__name__}: {exc}"))
        return tuple(out)

    @staticmethod
    def render(results: Sequence[ProbeResult]) -> str:
        worst = max((r.status for r in results), key=list(ProbeStatus).index, default=ProbeStatus.OK)
        lines = [f"ORION DOCTOR  overall={worst.value}"]
        for r in results:
            lines.append(f"  {r.status.value:<12} {r.subsystem:<22} {r.detail}")
        return "\n".join(lines)


__all__ = [
    "BackupManifest", "BudgetVerdict", "BuildProvenance", "ObservatoryView", "OperatorDoctor",
    "ProbeResult", "ProbeStatus", "ProvenanceVerdict", "ResourceBudget", "RestoreVerdict",
    "SloEnvelope", "measure_slo", "project_observatory", "take_backup", "verify_restore",
]
