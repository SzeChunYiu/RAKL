"""E12 item 11 + E17 items 19/20 — the metrics layer and the declared SLO envelopes.

Each test names the falsifier it drives. The load itself lives in
`research/orion_engineering_closure_v1/run_capacity_campaign.py`; what is asserted
here is deterministic behaviour, including the negative cases:

    a metric strips MetricReceipt content and keeps only the receipt id
    a bounded ResourceBudget refuses BEFORE the guarded mutation runs
    retry amplification is counted, and is CANNOT_CHECK (None) with no commits
"""

from __future__ import annotations

import json

import pytest

from rakl.engineering_capacity import (
    ENGINEERING_SLO_ENVELOPES,
    INSTRUMENTED_OPERATIONS,
    REQUIRED_SLO_IDS,
    Counter,
    EngineeringOperationMetrics,
    Gauge,
    Histogram,
    MetricExporter,
    MetricKind,
    MetricRegistry,
    SloBudget,
    SloDirection,
    SloStatistic,
    SloVerdict,
    evaluate_slo_envelopes,
    percentile,
    sanitize_operational_attributes,
    time_into,
)
from rakl.engineering_ops import BudgetVerdict, ResourceBudget


# --- the separation rule: no MetricReceipt content in an operational metric ---


def test_metric_attributes_strip_receipt_content_and_keep_only_the_id() -> None:
    kept = sanitize_operational_attributes({
        "receipt.id": "r-9",
        "receipt.value": "0.83",
        "receipt.claim": "the mechanism transfers",
        "receipt.verdict": "PROMOTE",
        "metric_receipt.id": "mr-1",
        "metric_receipt.effect_size": "1.4",
        "project.id": "p",
    })
    assert kept == {"receipt.id": "r-9", "metric_receipt.id": "mr-1", "project.id": "p"}


def test_receipt_content_never_reaches_the_exported_otlp_payload() -> None:
    registry = MetricRegistry(resource_attributes={"service.name": "orion", "receipt.claim": "leaked"})
    counter = registry.counter("orion.txn.commits", "{commit}")
    gauge = registry.gauge("orion.storage.bytes", "By")
    histogram = registry.histogram("orion.txn.latency", "ms")
    poison = {"receipt.id": "r-1", "receipt.effect_size": "1.4", "receipt.claim": "the mechanism transfers"}
    counter.add(1.0, poison)
    gauge.set(10.0, poison)
    histogram.record(2.5, poison)

    exporter = MetricExporter()
    payload = registry.export(exporter)
    text = json.dumps(payload)

    assert exporter.payloads == [payload]
    assert "r-1" in text                      # the reference survives
    assert "receipt.effect_size" not in text  # the content does not
    assert "receipt.claim" not in text
    assert "the mechanism transfers" not in text
    assert "1.4" not in text
    assert "leaked" not in text               # including on the resource


def test_receipt_stripping_happens_at_record_time_not_at_export_time() -> None:
    """A caller mutating its attribute dict after the call cannot smuggle content in."""

    registry = MetricRegistry()
    counter = registry.counter("orion.txn.commits")
    attributes = {"receipt.id": "r-2"}
    counter.add(1.0, attributes)
    attributes["receipt.claim"] = "injected after the fact"
    assert "injected after the fact" not in json.dumps(registry.to_otlp_dict())
    assert counter.value({"receipt.id": "r-2"}) == 1.0


# --- instrument behaviour ---------------------------------------------------


def test_counter_is_monotonic_and_refuses_a_negative_delta() -> None:
    counter = Counter("orion.txn.commits")
    counter.add(2.0)
    with pytest.raises(ValueError):
        counter.add(-1.0)
    assert counter.total() == 2.0


def test_counter_series_are_keyed_by_attributes_and_summed_by_one_of_them() -> None:
    counter = Counter("orion.txn.conflicts")
    counter.add(3.0, {"conflict.class": "sqlite_locked"})
    counter.add(2.0, {"conflict.class": "held_by_live_worker"})
    counter.add(1.0, {"conflict.class": "sqlite_locked"})
    assert counter.by_attribute("conflict.class") == {"sqlite_locked": 4.0, "held_by_live_worker": 2.0}
    assert counter.total() == 6.0


def test_gauge_reports_last_value_and_none_when_never_set() -> None:
    gauge = Gauge("orion.storage.bytes", unit="By")
    assert gauge.value() is None
    gauge.set(100.0)
    gauge.set(140.0)
    assert gauge.value() == 140.0


def test_histogram_percentiles_are_nearest_rank_over_the_real_sample() -> None:
    histogram = Histogram("orion.txn.latency")
    for value in range(1, 101):
        histogram.record(float(value))
    assert histogram.count() == 100
    assert histogram.percentile(0.5) == 50.0
    assert histogram.percentile(0.95) == 95.0
    assert percentile([5.0], 0.95) == 5.0


def test_histogram_otlp_bucket_counts_sum_to_the_sample_count() -> None:
    histogram = Histogram("orion.txn.latency", bounds=(1.0, 10.0))
    for value in (0.5, 5.0, 5.0, 50.0):
        histogram.record(value)
    point = histogram.to_otlp_dict()["histogram"]["dataPoints"][0]
    assert point["bucketCounts"] == [1, 2, 1]
    assert sum(point["bucketCounts"]) == point["count"] == 4
    assert point["sum"] == pytest.approx(60.5)


def test_registry_refuses_to_reuse_a_name_with_a_different_instrument_kind() -> None:
    registry = MetricRegistry()
    registry.counter("orion.txn.commits")
    assert registry.get("orion.txn.commits").kind is MetricKind.COUNTER
    with pytest.raises(ValueError):
        registry.gauge("orion.txn.commits")


def test_time_into_records_on_the_error_path_too() -> None:
    histogram = Histogram("orion.solver.compile.duration")
    with pytest.raises(RuntimeError):
        with time_into(histogram, {"phase": "compile"}):
            raise RuntimeError("compilation blew up")
    assert histogram.count() == 1
    assert histogram.all_samples()[0] >= 0.0


# --- every named operation actually has an instrument -----------------------


def test_every_named_operation_is_instrumented() -> None:
    metrics = EngineeringOperationMetrics()
    names = set(metrics.registry.names())
    missing = {
        operation: [n for n in instruments if n not in names]
        for operation, instruments in INSTRUMENTED_OPERATIONS.items()
    }
    assert not any(missing.values()), missing


def test_instrumented_operations_cover_the_named_operations_of_e12_item_11() -> None:
    assert set(INSTRUMENTED_OPERATIONS) == {
        "transaction_conflicts_and_retries",
        "queue_and_workflow_latency",
        "solver_cost",
        "status_computation_time",
        "context_compilation_time",
        "storage_and_index_health",
        "backup_freshness",
        "recovery_required_runs",
    }


# --- retry amplification is counted, not assumed ----------------------------


def test_retry_amplification_is_counted_per_class_and_overall() -> None:
    metrics = EngineeringOperationMetrics()
    for _ in range(3):
        metrics.record_conflict("sqlite_locked")
    metrics.record_conflict("held_by_live_worker")
    metrics.record_conflict("snapshot_stale", retried=False)  # a conflict given up on
    for _ in range(2):
        metrics.record_commit()

    assert metrics.conflicts_by_class() == {
        "sqlite_locked": 3.0, "held_by_live_worker": 1.0, "snapshot_stale": 1.0,
    }
    assert metrics.retries_by_class() == {"sqlite_locked": 3.0, "held_by_live_worker": 1.0}
    assert metrics.retry_amplification() == pytest.approx(2.0)  # 4 retries / 2 commits
    assert metrics.retry_amplification_by_class()["sqlite_locked"] == pytest.approx(1.5)


def test_retry_amplification_is_scoped_per_phase_so_denominators_do_not_mix() -> None:
    """Pooling the denominator divides one phase's retries by another's commits."""

    metrics = EngineeringOperationMetrics()
    for _ in range(6):
        metrics.record_conflict("sqlite_locked", phase="workflow")
    for _ in range(3):
        metrics.record_commit(phase="workflow")
    for _ in range(97):
        metrics.record_commit(phase="api")

    assert metrics.commits_by_phase() == {"workflow": 3.0, "api": 97.0}
    assert metrics.retries_by_phase() == {"workflow": 6.0}
    per_phase = metrics.retry_amplification_by_phase()
    assert per_phase["workflow"] == pytest.approx(2.0)   # 6 retries / 3 workflow commits
    assert per_phase["api"] == pytest.approx(0.0)
    # pooled across both phases the workflow signal all but disappears
    assert metrics.retry_amplification() == pytest.approx(0.06)


def test_a_phase_with_retries_but_no_commit_is_none_not_a_ratio() -> None:
    metrics = EngineeringOperationMetrics()
    metrics.record_conflict("sqlite_locked", phase="workflow")
    metrics.record_commit(phase="api")
    assert metrics.retry_amplification_by_phase() == {"workflow": None, "api": 0.0}


def test_retry_amplification_with_no_commit_is_none_not_zero() -> None:
    """Nothing committed is CANNOT_CHECK, and a fabricated 0.0 would read as healthy."""

    metrics = EngineeringOperationMetrics()
    metrics.record_conflict("sqlite_locked")
    assert metrics.retry_amplification() is None
    assert metrics.retry_amplification_by_class() == {"sqlite_locked": None}


# --- the bounded budget refuses BEFORE any mutation -------------------------


def test_bounded_budget_refuses_before_the_guarded_mutation_runs() -> None:
    budget = ResourceBudget(max_inflight=2, max_queue=1, degrade_at_inflight=2)
    metrics = EngineeringOperationMetrics()
    committed: list[int] = []

    def guarded(n: int) -> str:
        admission = budget.admit()
        if admission.verdict is BudgetVerdict.REFUSED_OVER_BUDGET:
            # nothing was admitted, so nothing is released and nothing mutates
            metrics.workflow_queue_refusals.add(1.0)
            return "REFUSED"
        committed.append(n)  # the mutation, reached only after admission
        return admission.verdict.value

    outcomes = [guarded(n) for n in range(4)]

    assert outcomes[-1] == "REFUSED"
    assert budget.refused == 1
    assert metrics.workflow_queue_refusals.total() == 1.0
    # the refused call performed no mutation at all
    assert committed == [0, 1, 2]
    assert len(committed) == len([o for o in outcomes if o != "REFUSED"])


def test_queue_depth_gauge_tracks_the_admission_controlled_queue() -> None:
    budget = ResourceBudget(max_inflight=1, max_queue=2, degrade_at_inflight=1)
    metrics = EngineeringOperationMetrics()
    for _ in range(3):
        budget.admit()  # tokens intentionally not released: the gauge tracks the live queue
        metrics.workflow_queue_depth.set(float(budget.queued))
    assert budget.queued == 2
    assert metrics.workflow_queue_depth.value() == 2.0


# --- declared SLO envelopes -------------------------------------------------


def test_the_eight_required_envelopes_are_declared_in_source() -> None:
    for slo_id in REQUIRED_SLO_IDS:
        assert slo_id in ENGINEERING_SLO_ENVELOPES, slo_id
    assert len(REQUIRED_SLO_IDS) == 8


def test_every_declared_envelope_names_a_budget_a_statistic_and_a_direction() -> None:
    for slo_id, budget in ENGINEERING_SLO_ENVELOPES.items():
        assert budget.slo_id == slo_id
        assert budget.unit
        assert budget.description
        assert isinstance(budget.statistic, SloStatistic)
        assert isinstance(budget.direction, SloDirection)
        assert budget.min_samples >= 1


def test_an_envelope_below_its_sample_floor_is_cannot_check_never_met() -> None:
    budget = ENGINEERING_SLO_ENVELOPES["transaction_latency_ms"]
    reading = budget.evaluate([1.0] * (budget.min_samples - 1))
    assert reading.verdict is SloVerdict.CANNOT_CHECK
    assert reading.measured is None and reading.p95 is None
    assert str(budget.min_samples) in reading.detail


def test_at_most_and_at_least_envelopes_both_evaluate_against_the_measurement() -> None:
    at_most = SloBudget("lat", "d", "ms", 10.0, SloStatistic.P95, SloDirection.AT_MOST, 5)
    assert at_most.evaluate([1.0] * 20).verdict is SloVerdict.MET
    # nearest-rank p95 of n=20 is the 19th ordered sample, so a single outlier
    # is genuinely outside the statistic; two are not.
    assert at_most.evaluate([1.0] * 19 + [999.0]).verdict is SloVerdict.MET
    missed = at_most.evaluate([1.0] * 18 + [999.0] * 2)
    assert missed.verdict is SloVerdict.MISSED
    assert missed.measured == 999.0

    at_least = SloBudget("avail", "d", "1", 0.99, SloStatistic.MEAN, SloDirection.AT_LEAST, 5)
    assert at_least.evaluate([1.0] * 10).verdict is SloVerdict.MET
    assert at_least.evaluate([1.0] * 9 + [0.0]).verdict is SloVerdict.MISSED


def test_an_unmeasured_envelope_is_cannot_check_not_a_silent_pass() -> None:
    readings = {r.slo_id: r for r in evaluate_slo_envelopes({})}
    assert set(readings) == set(ENGINEERING_SLO_ENVELOPES)
    assert all(r.verdict is SloVerdict.CANNOT_CHECK for r in readings.values())
    assert all(r.samples == 0 for r in readings.values())
    assert "no measurement" in readings["api_availability_ratio"].detail


def test_slo_readings_never_grant_scientific_authority() -> None:
    reading = ENGINEERING_SLO_ENVELOPES["status_computation_ms"].evaluate([1.0] * 40)
    assert reading.verdict is SloVerdict.MET
    assert reading.grants_scientific_authority is False
    assert reading.to_dict()["samples"] == 40
