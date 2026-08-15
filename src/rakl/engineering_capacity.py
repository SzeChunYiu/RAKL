"""Non-compensatory capacity/SLO reference policy for ORION engineering state.

Capacity is an engineering control plane, never an epistemic score.  Exceeding a
registered hard envelope blocks or degrades execution; it cannot be compensated
by high scientific utility.  Canonical history is preserved while rebuildable
views/caches may be compacted or delayed.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class CapacityVerdict(str, Enum):
    WITHIN_ENVELOPE = "WITHIN_ENVELOPE"
    COMPACT_REBUILDABLE_VIEWS = "COMPACT_REBUILDABLE_VIEWS"
    BLOCK_NEW_WORK = "BLOCK_NEW_WORK"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class EngineeringCapacityPolicy:
    policy_id: str
    max_metadata_bytes: int
    max_active_blob_bytes: int
    max_nonterminal_workflows: int
    max_index_lag_snapshots: int
    max_context_tokens: int

    def __post_init__(self) -> None:
        if not self.policy_id.strip():
            raise ValueError("capacity policy id is required")
        if min(
            self.max_metadata_bytes,
            self.max_active_blob_bytes,
            self.max_nonterminal_workflows,
            self.max_index_lag_snapshots,
            self.max_context_tokens,
        ) < 0:
            raise ValueError("capacity limits must be non-negative")


@dataclass(frozen=True)
class EngineeringCapacityObservation:
    project_snapshot_id: str
    metadata_bytes: int | None
    active_blob_bytes: int | None
    nonterminal_workflows: int | None
    index_lag_snapshots: int | None
    context_tokens: int | None

    def __post_init__(self) -> None:
        if not self.project_snapshot_id.strip():
            raise ValueError("snapshot identity is required")
        values = (
            self.metadata_bytes,
            self.active_blob_bytes,
            self.nonterminal_workflows,
            self.index_lag_snapshots,
            self.context_tokens,
        )
        if any(value is not None and value < 0 for value in values):
            raise ValueError("capacity observations cannot be negative")


@dataclass(frozen=True)
class CapacityAssessment:
    verdict: CapacityVerdict
    reasons: Tuple[str, ...]
    preserve_canonical_history: bool = True

    @property
    def grants_scientific_authority(self) -> bool:
        return False


def assess_engineering_capacity(
    observation: EngineeringCapacityObservation,
    policy: EngineeringCapacityPolicy,
) -> CapacityAssessment:
    coordinates = {
        "metadata_bytes": (observation.metadata_bytes, policy.max_metadata_bytes),
        "active_blob_bytes": (observation.active_blob_bytes, policy.max_active_blob_bytes),
        "nonterminal_workflows": (
            observation.nonterminal_workflows,
            policy.max_nonterminal_workflows,
        ),
        "index_lag_snapshots": (observation.index_lag_snapshots, policy.max_index_lag_snapshots),
        "context_tokens": (observation.context_tokens, policy.max_context_tokens),
    }
    missing = tuple(name for name, (value, _) in coordinates.items() if value is None)
    if missing:
        return CapacityAssessment(
            CapacityVerdict.CANNOT_CHECK,
            tuple(f"missing_capacity_observation:{name}" for name in missing),
        )

    exceeded = tuple(
        name for name, (value, limit) in coordinates.items()
        if value is not None and value > limit
    )
    if not exceeded:
        return CapacityAssessment(
            CapacityVerdict.WITHIN_ENVELOPE,
            ("all_registered_capacity_coordinates_within_envelope",),
        )

    # Rebuildable/view-only pressure may be handled by compaction. Canonical
    # metadata/history pressure, workflow overload, or context overflow blocks new
    # work until an operator acts; nothing is silently deleted.
    view_only = set(exceeded) <= {"index_lag_snapshots", "active_blob_bytes"}
    if view_only:
        return CapacityAssessment(
            CapacityVerdict.COMPACT_REBUILDABLE_VIEWS,
            tuple(f"capacity_exceeded:{name}" for name in exceeded)
            + ("canonical_history_must_not_be_deleted",),
        )
    return CapacityAssessment(
        CapacityVerdict.BLOCK_NEW_WORK,
        tuple(f"capacity_exceeded:{name}" for name in exceeded)
        + ("operator_intervention_required_before_new_work",),
    )


# ===========================================================================
# E12 (item 11) — operational metrics for the named engineering operations
#
#   falsifier: an operational metric carries MetricReceipt scientific content,
#              or one of the named operations has no instrument at all.
#
#   `engineering_http.Telemetry` spans HTTP requests and nothing else. The
#   operations an operator is actually paged about — transaction contention,
#   queue and workflow latency, solver cost, status and context compilation,
#   storage/index health, backup freshness, recovery-required runs — had no
#   counters at all. This is that layer: counters, gauges and histograms with
#   an OpenTelemetry-shaped `to_otlp_dict()` and a pluggable `MetricExporter`.
#
#   The separation rule is the same one `_SpanCtx.__exit__` enforces for spans,
#   and it is enforced HERE AT RECORD TIME rather than at export time: a metric
#   may reference a receipt id and may carry nothing else from a receipt.
#   Operational telemetry never becomes scientific authority. `MetricReceipt`
#   authority is unaffected by anything in this section.
#
# E17 (items 19, 20) — declared SLO envelopes
#
#   falsifier: a latency/resource budget is chosen after the measurement, or an
#              envelope is reported MET on too few samples to support it.
#
#   `ENGINEERING_SLO_ENVELOPES` below is the declaration, and it is frozen in
#   source. The capacity campaign IMPORTS it; the campaign does not define its
#   own budgets. Below a budget's `min_samples` floor the verdict is
#   CANNOT_CHECK, never MET.
#
#   What is NOT claimed: that these budgets are production capacity. They are
#   declared engineering envelopes, and a campaign that misses one on laptop
#   hardware has produced a measurement, not a failure to be tuned away.
# ===========================================================================

import math
import threading
import time
from contextlib import contextmanager
from types import MappingProxyType
from typing import Callable, Dict, Iterator, List, Mapping, Optional, Sequence

SCOPE_NAME = "rakl.orion.engineering"
SCOPE_VERSION = "1"

#: Attribute prefixes that would carry scientific content into an operational
#: metric. Mirrors `engineering_http._SpanCtx.__exit__` and extends the rule to
#: the `metric_receipt.` spelling of the same object.
RECEIPT_ATTRIBUTE_PREFIXES = ("receipt.", "metric_receipt.")

#: The only receipt-derived attributes an operational metric may carry: the id,
#: so an operator can correlate, and nothing that could stand in for the receipt.
RECEIPT_REFERENCE_ATTRIBUTES = frozenset({"receipt.id", "metric_receipt.id"})

#: Default histogram bucket bounds, in milliseconds.
DEFAULT_LATENCY_BOUNDS_MS = (1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0, 500.0, 1000.0, 2500.0, 5000.0)


def sanitize_operational_attributes(attributes: Mapping[str, object]) -> Dict[str, str]:
    """Strip receipt content, keep the receipt reference.

    A metric that carried a receipt's effect size, claim text or verdict would
    let an operational dashboard answer a scientific question. Dropping those
    keys here is what keeps the two planes separate.
    """

    out: Dict[str, str] = {}
    for raw_key, raw_value in attributes.items():
        key = str(raw_key)
        if key in RECEIPT_REFERENCE_ATTRIBUTES:
            out[key] = str(raw_value)
            continue
        if any(key.startswith(prefix) for prefix in RECEIPT_ATTRIBUTE_PREFIXES):
            continue
        out[key] = str(raw_value)
    return out


def percentile(values: Sequence[float], quantile: float) -> float:
    """Nearest-rank percentile. Exact on the sample; no interpolation invented."""

    if not values:
        raise ValueError("percentile of an empty sample is not defined")
    if not 0.0 < quantile <= 1.0:
        raise ValueError("quantile must be in (0, 1]")
    ordered = sorted(float(v) for v in values)
    rank = math.ceil(quantile * len(ordered))
    return ordered[min(max(rank - 1, 0), len(ordered) - 1)]


class MetricKind(str, Enum):
    COUNTER = "COUNTER"
    GAUGE = "GAUGE"
    HISTOGRAM = "HISTOGRAM"


_AttrKey = Tuple[Tuple[str, str], ...]


def _attr_key(attributes: Optional[Mapping[str, object]]) -> _AttrKey:
    return tuple(sorted(sanitize_operational_attributes(attributes or {}).items()))


def _otlp_attributes(key: _AttrKey) -> List[dict]:
    return [{"key": k, "value": {"stringValue": v}} for k, v in key]


class _Instrument:
    """Base: a named, unit-carrying instrument with one series per attribute set."""

    kind: MetricKind

    def __init__(self, name: str, *, unit: str = "1", description: str = "") -> None:
        if not name.strip():
            raise ValueError("an instrument needs a name")
        self.name = name
        self.unit = unit
        self.description = description
        self._lock = threading.Lock()

    def series(self) -> Tuple[_AttrKey, ...]:
        raise NotImplementedError

    def to_otlp_dict(self) -> dict:
        raise NotImplementedError

    def _head(self) -> dict:
        return {"name": self.name, "unit": self.unit, "description": self.description}


class Counter(_Instrument):
    """Monotonic. `add` refuses a negative delta rather than silently decrementing."""

    kind = MetricKind.COUNTER

    def __init__(self, name: str, *, unit: str = "1", description: str = "") -> None:
        super().__init__(name, unit=unit, description=description)
        self._values: Dict[_AttrKey, float] = {}

    def add(self, value: float = 1.0, attributes: Optional[Mapping[str, object]] = None) -> None:
        if value < 0:
            raise ValueError(f"counter {self.name!r} is monotonic; refusing a negative delta")
        key = _attr_key(attributes)
        with self._lock:
            self._values[key] = self._values.get(key, 0.0) + float(value)

    def value(self, attributes: Optional[Mapping[str, object]] = None) -> float:
        with self._lock:
            return self._values.get(_attr_key(attributes), 0.0)

    def total(self) -> float:
        with self._lock:
            return sum(self._values.values())

    def by_attribute(self, attribute: str) -> Dict[str, float]:
        """Series totals keyed by one attribute's value. Series lacking it are skipped."""

        out: Dict[str, float] = {}
        with self._lock:
            items = list(self._values.items())
        for key, value in items:
            as_map = dict(key)
            if attribute in as_map:
                out[as_map[attribute]] = out.get(as_map[attribute], 0.0) + value
        return out

    def series(self) -> Tuple[_AttrKey, ...]:
        with self._lock:
            return tuple(self._values)

    def to_otlp_dict(self) -> dict:
        with self._lock:
            points = [
                {"attributes": _otlp_attributes(key), "asDouble": value}
                for key, value in sorted(self._values.items())
            ]
        return {
            **self._head(),
            "sum": {
                "dataPoints": points,
                "aggregationTemporality": "AGGREGATION_TEMPORALITY_CUMULATIVE",
                "isMonotonic": True,
            },
        }


class Gauge(_Instrument):
    """Last-value. Storage size, queue depth, index lag, backup age."""

    kind = MetricKind.GAUGE

    def __init__(self, name: str, *, unit: str = "1", description: str = "") -> None:
        super().__init__(name, unit=unit, description=description)
        self._values: Dict[_AttrKey, float] = {}

    def set(self, value: float, attributes: Optional[Mapping[str, object]] = None) -> None:
        key = _attr_key(attributes)
        with self._lock:
            self._values[key] = float(value)

    def value(self, attributes: Optional[Mapping[str, object]] = None) -> Optional[float]:
        with self._lock:
            return self._values.get(_attr_key(attributes))

    def series(self) -> Tuple[_AttrKey, ...]:
        with self._lock:
            return tuple(self._values)

    def to_otlp_dict(self) -> dict:
        with self._lock:
            points = [
                {"attributes": _otlp_attributes(key), "asDouble": value}
                for key, value in sorted(self._values.items())
            ]
        return {**self._head(), "gauge": {"dataPoints": points}}


class Histogram(_Instrument):
    """Explicit-bucket histogram that also retains its raw sample.

    Retaining the sample is deliberate: an SLO verdict on a bucketed p95 is a
    verdict on a bucket boundary, and this layer exists to report measured
    numbers rather than the bound nearest to them.
    """

    kind = MetricKind.HISTOGRAM

    def __init__(
        self,
        name: str,
        *,
        unit: str = "ms",
        description: str = "",
        bounds: Sequence[float] = DEFAULT_LATENCY_BOUNDS_MS,
    ) -> None:
        super().__init__(name, unit=unit, description=description)
        self.bounds = tuple(float(b) for b in bounds)
        if list(self.bounds) != sorted(self.bounds):
            raise ValueError("histogram bounds must be ascending")
        self._samples: Dict[_AttrKey, List[float]] = {}

    def record(self, value: float, attributes: Optional[Mapping[str, object]] = None) -> None:
        key = _attr_key(attributes)
        with self._lock:
            self._samples.setdefault(key, []).append(float(value))

    def samples(self, attributes: Optional[Mapping[str, object]] = None) -> Tuple[float, ...]:
        with self._lock:
            return tuple(self._samples.get(_attr_key(attributes), ()))

    def all_samples(self) -> Tuple[float, ...]:
        with self._lock:
            out: List[float] = []
            for values in self._samples.values():
                out.extend(values)
        return tuple(out)

    def count(self) -> int:
        return len(self.all_samples())

    def percentile(self, quantile: float, attributes: Optional[Mapping[str, object]] = None) -> Optional[float]:
        values = self.samples(attributes) if attributes is not None else self.all_samples()
        if not values:
            return None
        return percentile(values, quantile)

    def series(self) -> Tuple[_AttrKey, ...]:
        with self._lock:
            return tuple(self._samples)

    def _bucket_counts(self, values: Sequence[float]) -> List[int]:
        counts = [0] * (len(self.bounds) + 1)
        for value in values:
            placed = False
            for i, bound in enumerate(self.bounds):
                if value <= bound:
                    counts[i] += 1
                    placed = True
                    break
            if not placed:
                counts[-1] += 1
        return counts

    def to_otlp_dict(self) -> dict:
        with self._lock:
            items = sorted((key, list(values)) for key, values in self._samples.items())
        points = []
        for key, values in items:
            points.append({
                "attributes": _otlp_attributes(key),
                "count": len(values),
                "sum": sum(values),
                "min": min(values) if values else 0.0,
                "max": max(values) if values else 0.0,
                "explicitBounds": list(self.bounds),
                "bucketCounts": self._bucket_counts(values),
            })
        return {
            **self._head(),
            "histogram": {
                "dataPoints": points,
                "aggregationTemporality": "AGGREGATION_TEMPORALITY_CUMULATIVE",
            },
        }


class MetricExporter:
    """Pluggable. Reference collects in memory; production ships OTLP.

    Deliberately the same shape as `engineering_http.SpanExporter`.
    """

    def __init__(self) -> None:
        self.payloads: List[dict] = []
        self._lock = threading.Lock()

    def export(self, payload: Mapping[str, object]) -> None:
        with self._lock:
            self.payloads.append(dict(payload))


class MetricRegistry:
    """Get-or-create instrument registry with an OTLP-shaped export."""

    def __init__(self, resource_attributes: Optional[Mapping[str, object]] = None) -> None:
        self.resource_attributes = sanitize_operational_attributes(resource_attributes or {})
        self._instruments: Dict[str, _Instrument] = {}
        self._lock = threading.Lock()

    def _get_or_create(self, name: str, factory: Callable[[], _Instrument], kind: MetricKind) -> _Instrument:
        with self._lock:
            existing = self._instruments.get(name)
            if existing is not None:
                if existing.kind is not kind:
                    raise ValueError(
                        f"instrument {name!r} already registered as {existing.kind.value}, not {kind.value}"
                    )
                return existing
            created = factory()
            self._instruments[name] = created
            return created

    def counter(self, name: str, unit: str = "1", description: str = "") -> Counter:
        return self._get_or_create(
            name, lambda: Counter(name, unit=unit, description=description), MetricKind.COUNTER
        )  # type: ignore[return-value]

    def gauge(self, name: str, unit: str = "1", description: str = "") -> Gauge:
        return self._get_or_create(
            name, lambda: Gauge(name, unit=unit, description=description), MetricKind.GAUGE
        )  # type: ignore[return-value]

    def histogram(
        self,
        name: str,
        unit: str = "ms",
        description: str = "",
        bounds: Sequence[float] = DEFAULT_LATENCY_BOUNDS_MS,
    ) -> Histogram:
        return self._get_or_create(
            name,
            lambda: Histogram(name, unit=unit, description=description, bounds=bounds),
            MetricKind.HISTOGRAM,
        )  # type: ignore[return-value]

    def get(self, name: str) -> Optional[_Instrument]:
        with self._lock:
            return self._instruments.get(name)

    def names(self) -> Tuple[str, ...]:
        with self._lock:
            return tuple(sorted(self._instruments))

    def to_otlp_dict(self) -> dict:
        with self._lock:
            instruments = [self._instruments[n] for n in sorted(self._instruments)]
        return {
            "resourceMetrics": [{
                "resource": {"attributes": _otlp_attributes(tuple(sorted(self.resource_attributes.items())))},
                "scopeMetrics": [{
                    "scope": {"name": SCOPE_NAME, "version": SCOPE_VERSION},
                    "metrics": [i.to_otlp_dict() for i in instruments],
                }],
            }]
        }

    def export(self, exporter: MetricExporter) -> dict:
        payload = self.to_otlp_dict()
        exporter.export(payload)
        return payload


class _Elapsed:
    """Handle a `time_into` block can read after it closes."""

    def __init__(self) -> None:
        self.elapsed_ms: Optional[float] = None


@contextmanager
def time_into(
    histogram: Histogram, attributes: Optional[Mapping[str, object]] = None
) -> Iterator[_Elapsed]:
    """Time a block into a histogram. Records on the error path too."""

    handle = _Elapsed()
    start = time.perf_counter()
    try:
        yield handle
    finally:
        handle.elapsed_ms = (time.perf_counter() - start) * 1000.0
        histogram.record(handle.elapsed_ms, attributes)


#: Which instrument answers for which named operation. The campaign and the
#: test both assert against this map, so a named operation cannot quietly lose
#: its instrument.
INSTRUMENTED_OPERATIONS: Mapping[str, Tuple[str, ...]] = MappingProxyType({
    "transaction_conflicts_and_retries": (
        "orion.txn.commits", "orion.txn.conflicts", "orion.txn.retries", "orion.txn.latency",
    ),
    "queue_and_workflow_latency": (
        "orion.workflow.schedule_to_claim", "orion.workflow.claim_to_complete",
        "orion.workflow.queue_depth", "orion.workflow.queue_refusals",
    ),
    "solver_cost": (
        "orion.solver.compile.duration", "orion.solver.navigate.duration",
        "orion.solver.fibres_opened", "orion.solver.research_rounds",
    ),
    "status_computation_time": ("orion.status.computation.duration",),
    "context_compilation_time": ("orion.context.compilation.duration",),
    "storage_and_index_health": (
        "orion.storage.bytes", "orion.storage.rows",
        "orion.storage.growth_bytes_per_record", "orion.index.lag_events",
    ),
    "backup_freshness": ("orion.backup.age",),
    "recovery_required_runs": ("orion.recovery_required.runs",),
})


class EngineeringOperationMetrics:
    """Every named engineering operation, instrumented.

    Nothing here reads or writes a `MetricReceipt`. Attribute sanitisation runs
    on every record, so an operator wiring a receipt field into a metric label
    loses the field rather than smuggling it into the operational plane.
    """

    def __init__(
        self,
        registry: Optional[MetricRegistry] = None,
        resource_attributes: Optional[Mapping[str, object]] = None,
    ) -> None:
        self.registry = registry if registry is not None else MetricRegistry(resource_attributes)
        r = self.registry

        # transaction conflicts and retries
        self.txn_commits = r.counter("orion.txn.commits", "{commit}", "transactions that committed")
        self.txn_conflicts = r.counter("orion.txn.conflicts", "{conflict}", "serialization/lock conflicts by class")
        self.txn_retries = r.counter("orion.txn.retries", "{retry}", "retries issued after a conflict")
        self.txn_latency_ms = r.histogram("orion.txn.latency", "ms", "one durable transaction, attempt to commit")

        # queue and workflow latency
        self.workflow_schedule_to_claim_ms = r.histogram(
            "orion.workflow.schedule_to_claim", "ms", "activity scheduled until a worker holds its lease")
        self.workflow_claim_to_complete_ms = r.histogram(
            "orion.workflow.claim_to_complete", "ms", "lease acquired until the terminal receipt is written")
        self.workflow_queue_depth = r.gauge("orion.workflow.queue_depth", "{item}", "admission-controlled queue depth")
        self.workflow_queue_refusals = r.counter(
            "orion.workflow.queue_refusals", "{refusal}", "admissions refused before any mutation")

        # solver cost
        self.solver_compile_ms = r.histogram("orion.solver.compile.duration", "ms", "structure-space composition")
        self.solver_navigate_ms = r.histogram("orion.solver.navigate.duration", "ms", "support-structure navigation")
        self.solver_fibres_opened = r.counter("orion.solver.fibres_opened", "{fibre}", "fibres opened by the solver")
        self.solver_research_rounds = r.counter(
            "orion.solver.research_rounds", "{round}", "targeted research rounds spent")

        # status computation time
        self.status_computation_ms = r.histogram(
            "orion.status.computation.duration", "ms", "canonical EpistemicStatus read/projection")

        # context compilation time
        self.context_compilation_ms = r.histogram(
            "orion.context.compilation.duration", "ms", "bounded working-set compilation")

        # storage / index health
        self.storage_bytes = r.gauge("orion.storage.bytes", "By", "durable store size on disk")
        self.storage_rows = r.gauge("orion.storage.rows", "{row}", "durable store row count")
        self.storage_growth_bytes_per_record = r.histogram(
            "orion.storage.growth_bytes_per_record", "By", "store bytes per canonical record",
            bounds=(64.0, 128.0, 256.0, 512.0, 1024.0, 2048.0, 4096.0, 8192.0, 16384.0))
        self.index_lag_events = r.gauge("orion.index.lag_events", "{event}", "events committed since last rebuild")
        self.index_lag_samples = r.histogram(
            "orion.index.lag_events.samples", "{event}", "sampled index lag",
            bounds=(1.0, 2.0, 5.0, 10.0, 25.0, 50.0, 100.0, 250.0))

        # backup freshness
        self.backup_age_seconds = r.gauge("orion.backup.age", "s", "age of the most recent verified backup")

        # recovery-required runs
        self.recovery_required_runs = r.counter(
            "orion.recovery_required.runs", "{run}", "runs that terminated RECOVERY_REQUIRED")

        # the API surface these ride on
        self.api_requests = r.counter("orion.api.requests", "{request}", "API requests by outcome")
        self.api_latency_ms = r.histogram("orion.api.latency", "ms", "API request latency")

    # --- conflict accounting -------------------------------------------------

    def record_commit(self, count: float = 1.0, phase: Optional[str] = None) -> None:
        """One durable transaction that committed. `phase` scopes the denominator.

        Retry amplification computed against a denominator pooled across phases
        would divide one phase's retries by another phase's commits, so the
        phase label is what keeps the ratio meaningful.
        """

        self.txn_commits.add(count, {"phase": phase} if phase else None)

    def record_conflict(
        self, conflict_class: str, *, retried: bool = True, phase: Optional[str] = None
    ) -> None:
        """One conflict, classified. `retried=False` records a conflict that was given up on."""

        attributes = {"conflict.class": conflict_class}
        if phase:
            attributes["phase"] = phase
        self.txn_conflicts.add(1.0, attributes)
        if retried:
            self.txn_retries.add(1.0, attributes)

    def conflicts_by_class(self) -> Dict[str, float]:
        return self.txn_conflicts.by_attribute("conflict.class")

    def retries_by_class(self) -> Dict[str, float]:
        return self.txn_retries.by_attribute("conflict.class")

    def retry_amplification(self) -> Optional[float]:
        """Retries issued per successful commit. None when nothing committed."""

        commits = self.txn_commits.total()
        if commits <= 0:
            return None
        return self.txn_retries.total() / commits

    def retry_amplification_by_class(self) -> Dict[str, Optional[float]]:
        commits = self.txn_commits.total()
        if commits <= 0:
            return {name: None for name in self.retries_by_class()}
        return {name: value / commits for name, value in self.retries_by_class().items()}

    def commits_by_phase(self) -> Dict[str, float]:
        return self.txn_commits.by_attribute("phase")

    def retries_by_phase(self) -> Dict[str, float]:
        return self.txn_retries.by_attribute("phase")

    def retry_amplification_by_phase(self) -> Dict[str, Optional[float]]:
        """Retries per commit, each phase against its own commits.

        A phase that recorded retries but no commit is None — CANNOT_CHECK —
        rather than an infinite or zero ratio.
        """

        commits = self.commits_by_phase()
        retries = self.retries_by_phase()
        out: Dict[str, Optional[float]] = {}
        for phase in sorted(set(commits) | set(retries)):
            committed = commits.get(phase, 0.0)
            out[phase] = retries.get(phase, 0.0) / committed if committed > 0 else None
        return out

    def export(self, exporter: MetricExporter) -> dict:
        return self.registry.export(exporter)


# --- E17: the declared envelopes -------------------------------------------


class SloStatistic(str, Enum):
    P50 = "p50"
    P95 = "p95"
    P99 = "p99"
    MEAN = "mean"
    MIN = "min"
    MAX = "max"


class SloDirection(str, Enum):
    AT_MOST = "AT_MOST"
    AT_LEAST = "AT_LEAST"


class SloVerdict(str, Enum):
    MET = "MET"
    MISSED = "MISSED"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class SloReading:
    """A measured envelope. Every number here came from a sample, or is None."""

    slo_id: str
    verdict: SloVerdict
    statistic: SloStatistic
    direction: SloDirection
    unit: str
    budget: float
    measured: Optional[float]
    p50: Optional[float]
    p95: Optional[float]
    mean: Optional[float]
    minimum: Optional[float]
    maximum: Optional[float]
    samples: int
    detail: str = ""

    @property
    def grants_scientific_authority(self) -> bool:
        return False

    def to_dict(self) -> dict:
        return {
            "slo_id": self.slo_id,
            "verdict": self.verdict.value,
            "statistic": self.statistic.value,
            "direction": self.direction.value,
            "unit": self.unit,
            "budget": self.budget,
            "measured": self.measured,
            "p50": self.p50,
            "p95": self.p95,
            "mean": self.mean,
            "min": self.minimum,
            "max": self.maximum,
            "samples": self.samples,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class SloBudget:
    """A declared budget. Declared in source, before the measurement exists."""

    slo_id: str
    description: str
    unit: str
    budget: float
    statistic: SloStatistic
    direction: SloDirection
    min_samples: int

    def __post_init__(self) -> None:
        if not self.slo_id.strip():
            raise ValueError("an SLO needs an id")
        if self.min_samples < 1:
            raise ValueError("an SLO needs a positive minimum-sample floor")

    def evaluate(self, samples: Sequence[float]) -> SloReading:
        values = [float(v) for v in samples]
        count = len(values)
        if count < self.min_samples:
            return SloReading(
                slo_id=self.slo_id, verdict=SloVerdict.CANNOT_CHECK, statistic=self.statistic,
                direction=self.direction, unit=self.unit, budget=self.budget, measured=None,
                p50=None, p95=None, mean=None, minimum=None, maximum=None, samples=count,
                detail=(f"{count} sample(s) is below the declared floor of {self.min_samples}; "
                        "too few to support a verdict"),
            )
        p50 = percentile(values, 0.5)
        p95 = percentile(values, 0.95)
        mean = sum(values) / count
        measured = {
            SloStatistic.P50: p50,
            SloStatistic.P95: p95,
            SloStatistic.P99: percentile(values, 0.99),
            SloStatistic.MEAN: mean,
            SloStatistic.MIN: min(values),
            SloStatistic.MAX: max(values),
        }[self.statistic]
        met = measured <= self.budget if self.direction is SloDirection.AT_MOST else measured >= self.budget
        return SloReading(
            slo_id=self.slo_id, verdict=SloVerdict.MET if met else SloVerdict.MISSED,
            statistic=self.statistic, direction=self.direction, unit=self.unit, budget=self.budget,
            measured=measured, p50=p50, p95=p95, mean=mean, minimum=min(values), maximum=max(values),
            samples=count,
            detail=(f"{self.statistic.value}={measured:.4f} {self.unit} vs budget "
                    f"{self.direction.value} {self.budget} {self.unit}"),
        )

    def to_dict(self) -> dict:
        return {
            "slo_id": self.slo_id, "description": self.description, "unit": self.unit,
            "budget": self.budget, "statistic": self.statistic.value,
            "direction": self.direction.value, "min_samples": self.min_samples,
        }


def _slo(
    slo_id: str, description: str, unit: str, budget: float,
    statistic: SloStatistic, direction: SloDirection, min_samples: int,
) -> SloBudget:
    return SloBudget(slo_id, description, unit, budget, statistic, direction, min_samples)


#: The frozen declaration. A campaign imports this; it never declares its own.
ENGINEERING_SLO_ENVELOPES: Mapping[str, SloBudget] = MappingProxyType({
    b.slo_id: b for b in (
        _slo("transaction_latency_ms",
             "one durable workflow transaction, attempt to commit, under concurrency",
             "ms", 250.0, SloStatistic.P95, SloDirection.AT_MOST, 50),
        _slo("workflow_latency_ms",
             "activity scheduled until its terminal receipt is written",
             "ms", 2000.0, SloStatistic.P95, SloDirection.AT_MOST, 50),
        _slo("status_computation_ms",
             "canonical EpistemicStatus read and projection for one snapshot",
             "ms", 50.0, SloStatistic.P95, SloDirection.AT_MOST, 30),
        _slo("solver_compilation_ms",
             "structure-space match and composition for one problem",
             "ms", 100.0, SloStatistic.P95, SloDirection.AT_MOST, 30),
        _slo("solver_navigation_ms",
             "support-structure navigation for one composed problem",
             "ms", 100.0, SloStatistic.P95, SloDirection.AT_MOST, 30),
        _slo("context_compilation_ms",
             "bounded working-set compilation for one budgeted request",
             "ms", 50.0, SloStatistic.P95, SloDirection.AT_MOST, 30),
        _slo("storage_growth_bytes_per_record",
             "durable store bytes divided by canonical records held",
             "By", 4096.0, SloStatistic.MEAN, SloDirection.AT_MOST, 5),
        _slo("index_lag_events",
             "canonical events committed since the rebuildable projection last rebuilt",
             "{event}", 25.0, SloStatistic.P95, SloDirection.AT_MOST, 10),
        _slo("api_availability_ratio",
             "first-attempt 2xx responses over all first attempts under concurrent load",
             "1", 0.99, SloStatistic.MEAN, SloDirection.AT_LEAST, 50),
    )
})

#: The eight envelopes E17 item 19 requires. `context_compilation_ms` is
#: declared as well because the operation is instrumented; it is not on this list.
REQUIRED_SLO_IDS: Tuple[str, ...] = (
    "transaction_latency_ms", "workflow_latency_ms", "status_computation_ms",
    "solver_compilation_ms", "solver_navigation_ms", "storage_growth_bytes_per_record",
    "index_lag_events", "api_availability_ratio",
)


def evaluate_slo_envelopes(
    samples_by_slo: Mapping[str, Sequence[float]],
    envelopes: Mapping[str, SloBudget] = ENGINEERING_SLO_ENVELOPES,
) -> Tuple[SloReading, ...]:
    """Evaluate every declared envelope. An unmeasured envelope is CANNOT_CHECK.

    Silence is never a pass: an envelope with no samples reports CANNOT_CHECK
    with the reason, so a campaign cannot claim coverage it did not measure.
    """

    readings: List[SloReading] = []
    for slo_id in sorted(envelopes):
        budget = envelopes[slo_id]
        samples = samples_by_slo.get(slo_id)
        if samples is None:
            readings.append(SloReading(
                slo_id=slo_id, verdict=SloVerdict.CANNOT_CHECK, statistic=budget.statistic,
                direction=budget.direction, unit=budget.unit, budget=budget.budget, measured=None,
                p50=None, p95=None, mean=None, minimum=None, maximum=None, samples=0,
                detail="no measurement was supplied for this envelope",
            ))
            continue
        readings.append(budget.evaluate(samples))
    return tuple(readings)
