"""E17 items 19 & 20 — the concurrency / capacity campaign.

Item 19 is the declaration: explicit, measurable SLO envelopes with a name and a
budget. Those live in `rakl.engineering_capacity.ENGINEERING_SLO_ENVELOPES` and
this script IMPORTS them. It does not declare its own, and it does not adjust
them: the import direction is what makes "budgets frozen before result access"
structural rather than a promise in the receipt.

Item 20 is the measurement: real threads, several projects, several workers, a
bounded `ResourceBudget`, against `SqliteWorkerWorkflowEngine` and
`EngineeringHttpService`, plus the solver, status and context-compilation costs
the runbook names. Everything reported comes out of a counter or a histogram
this run populated.

What the campaign measures
    W1  workflow concurrency        conflicts by class, retry amplification,
                                    schedule->claim, claim->complete, queue
                                    saturation under a bounded budget
    W2  low-busy-timeout variant    the same load with sqlite's busy timeout cut
                                    to 20ms, so lock contention surfaces as
                                    `database is locked` instead of as latency.
                                    LABELLED, and its latencies are NOT fed to
                                    the shipped-configuration SLOs.
    H1  API concurrency             first-attempt availability, snapshot-stale
                                    conflicts, retry amplification, latency
    S1  solver cost                 compile vs navigate, fibres, research rounds
    T1  status computation          canonical status read/projection
    C1  context compilation         bounded working-set compilation
    G1  storage scaling             db bytes vs canonical record count
    I1  index lag                   events committed since the projection rebuilt
    B1  backup freshness            age of the verified backup
    R1  recovery-required runs      driven, counted
    D1  defect probes               two suspected defects in code this campaign
                                    exercises but does not own

What is NOT claimed
    These are laptop numbers. They are a measurement of this machine under this
    load, not a production capacity statement, and a missed envelope here is a
    measurement to report rather than a budget to move.
"""

from __future__ import annotations

import json
import os
import platform
import sqlite3
import statistics
import sys
import tempfile
import threading
import time
from datetime import datetime, timezone
from http import HTTPStatus
from pathlib import Path

sys.path.insert(0, "src")

from rakl.context_compiler import (  # noqa: E402
    ContextCompileRequest,
    ContextItem,
    compile_epistemic_context,
)
from rakl.engineering_capacity import (  # noqa: E402
    ENGINEERING_SLO_ENVELOPES,
    INSTRUMENTED_OPERATIONS,
    REQUIRED_SLO_IDS,
    EngineeringOperationMetrics,
    MetricExporter,
    SloVerdict,
    evaluate_slo_envelopes,
    percentile,
    time_into,
)
from rakl.engineering_http import (  # noqa: E402
    Actor,
    Capability,
    EngineeringHttpService,
    IdentityProvider,
    SecretStore,
    content_hash,
)
import rakl.engineering_http as engineering_http_module  # noqa: E402
from rakl.engineering_ops import (  # noqa: E402
    Admission,
    AdmissionSlot,
    BudgetVerdict,
    ResourceBudget,
    RestoreVerdict,
    take_backup,
    verify_restore,
)
from rakl.engineering_service import EngineeringReadService  # noqa: E402
from rakl.engineering_state import (  # noqa: E402
    EpistemicAxisStatus,
    EpistemicStatus,
    NextActionClass,
    ProjectSnapshot,
)
from rakl.engineering_store import SqliteEngineeringStateStore  # noqa: E402
from rakl.engineering_workflow import ActivitySpec  # noqa: E402
from rakl.engineering_workflow_workers import ClaimVerdict, SqliteWorkerWorkflowEngine  # noqa: E402
from rakl.recursive_solver import solve_recursive  # noqa: E402
from rakl.structure_space import (  # noqa: E402
    ProblemStructure,
    ReducedStructure,
    StructureSpace,
    compose,
)
from rakl.support_solver import Atom, SupportEdge, SupportStructure, Target, solve  # noqa: E402

OUT = Path("research/orion_engineering_closure_v1/CAPACITY_CAMPAIGN_V1.json")

# --- frozen campaign configuration -----------------------------------------

CONFIG = {
    "workflow_projects": 4,
    "workflow_activities_per_project": 30,
    "workflow_worker_threads": 12,
    "workflow_passes_per_worker": 2,
    # One run of the workflow phase produced p95s of 1356ms, 3408ms and 1295ms
    # against a 2000ms budget on this shared machine: a single run decides that
    # verdict by what else the host is doing. Repeating and pooling makes the
    # verdict rest on the whole sample and puts the spread on the receipt.
    "workflow_repeats": 3,
    # A claimed activity does some work before its receipt is written. Without a
    # hold the lease window is shorter than a thread's turn and no worker ever
    # meets another one holding it, which measures the harness, not the engine.
    "activity_hold_s": 0.002,
    "budget_max_inflight": 4,
    "budget_max_queue": 4,
    "budget_degrade_at_inflight": 3,
    "shipped_sqlite_busy_timeout_s": 5.0,
    "probe_sqlite_busy_timeout_s": 0.02,
    "storage_sample_interval_s": 0.02,
    "index_rebuild_interval_s": 0.02,
    # Harness setting, declared: CPython's default 5ms switch interval lets one
    # thread run thousands of these operations before yielding, so in-process
    # interleaving never happens. 0.5ms makes the threads actually interleave.
    # It changes the scheduler, not the code under test.
    "thread_switch_interval_s": 0.0005,
    "http_writer_threads": 16,
    "http_writes_per_thread": 40,
    "http_max_retries": 12,
    "solver_iterations": 60,
    "solver_chain_structures": 8,
    "status_iterations": 60,
    "context_iterations": 60,
    "context_items": 200,
    "same_key_race_threads": 16,
    # D1 race probe: how long the patched content_hash sleeps inside the
    # unguarded validate->apply window so 16 threads genuinely overlap in it.
    "race_probe_window_sleep_s": 0.005,
    "max_claim_retries": 12,
}

T0 = "2026-08-15T17:00:00+00:00"


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# --- retry wrapper: sqlite lock contention, counted -------------------------


class RetryExhausted(RuntimeError):
    pass


def with_lock_retry(metrics: EngineeringOperationMetrics, op, *, label: str, max_retries: int,
                    phase: str):
    """Run `op`, counting every `database is locked` as a conflict and a retry.

    Backoff is exponential from 1ms. A conflict that is never retried to success
    is recorded as a conflict that was given up on, not as a silent failure.
    """

    delay = 0.001
    attempts = 0
    while True:
        try:
            with time_into(metrics.txn_latency_ms, {"op": label}):
                result = op()
            metrics.record_commit(phase=phase)  # one durable transaction committed
            return result
        except sqlite3.OperationalError as exc:
            message = str(exc).lower()
            if "locked" not in message and "busy" not in message:
                raise
            attempts += 1
            if attempts > max_retries:
                metrics.record_conflict("sqlite_locked", retried=False, phase=phase)
                raise RetryExhausted(f"{label}: {exc}") from exc
            metrics.record_conflict("sqlite_locked", phase=phase)
            time.sleep(delay)
            delay = min(delay * 2, 0.25)


# --- W1 / W2: workflow concurrency -----------------------------------------


def _low_timeout_engine(path: Path, timeout_s: float) -> SqliteWorkerWorkflowEngine:
    class _Probe(SqliteWorkerWorkflowEngine):
        def _connect(self) -> sqlite3.Connection:  # type: ignore[override]
            db = sqlite3.connect(self.path, timeout=timeout_s)
            db.row_factory = sqlite3.Row
            return db

    return _Probe(path)


def _row_counts(path: Path) -> dict:
    db = sqlite3.connect(path, timeout=10.0)
    try:
        counts = {}
        for table in ("worker_activities", "leases", "worker_events"):
            counts[table] = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        db.close()
    counts["total"] = sum(counts.values())
    return counts


def run_workflow_phase(
    metrics: EngineeringOperationMetrics,
    root: Path,
    *,
    label: str,
    engine_factory,
    sample_storage: bool,
) -> tuple[dict, list[float], list[int]]:
    phase = f"workflow::{label}"
    db_path = root / f"workflow-{label}.sqlite3"
    engine = engine_factory(db_path)
    projects = [f"proj-{i}" for i in range(CONFIG["workflow_projects"])]
    per_project = CONFIG["workflow_activities_per_project"]

    scheduled_at: dict[tuple[str, str], float] = {}
    tasks: list[tuple[str, str]] = []
    for project in projects:
        for index in range(per_project):
            activity_id = f"{project}-act-{index}"
            spec = ActivitySpec(
                activity_id=activity_id,
                invocation_id=f"inv-{activity_id}",
                input_digest=f"{index:064d}",
                retry_safe=True,
                external_effect=False,
                max_attempts=5,
            )
            with_lock_retry(
                metrics,
                lambda p=project, s=spec: engine.schedule(p, s, idempotency_key=f"idem-{s.activity_id}"),
                label="schedule",
                max_retries=CONFIG["max_claim_retries"],
                phase=phase,
            )
            scheduled_at[(project, activity_id)] = time.perf_counter()
            tasks.append((project, activity_id))

    budget = ResourceBudget(
        max_inflight=CONFIG["budget_max_inflight"],
        max_queue=CONFIG["budget_max_queue"],
        degrade_at_inflight=CONFIG["budget_degrade_at_inflight"],
    )
    budget_lock = threading.Lock()
    stop = threading.Event()
    outcomes: dict[str, int] = {}
    outcome_lock = threading.Lock()
    workflow_latency_ms: list[float] = []

    def bump(name: str, count: int = 1) -> None:
        with outcome_lock:
            outcomes[name] = outcomes.get(name, 0) + count

    # storage growth + index lag samplers
    storage_samples: list[dict] = []
    index_lag_samples: list[int] = []

    def storage_sampler() -> None:
        while not stop.is_set():
            try:
                size = db_path.stat().st_size
                counts = _row_counts(db_path)
                if counts["total"] > 0:
                    ratio = size / counts["total"]
                    metrics.storage_bytes.set(float(size))
                    metrics.storage_rows.set(float(counts["total"]))
                    metrics.storage_growth_bytes_per_record.record(ratio)
                    storage_samples.append({"db_bytes": size, "records": counts["total"],
                                            "bytes_per_record": ratio})
            except sqlite3.Error:
                pass
            stop.wait(CONFIG["storage_sample_interval_s"])

    def index_projection() -> None:
        """A rebuildable projection. Lag = events committed since the last rebuild."""

        last_included = 0
        while not stop.is_set():
            try:
                db = sqlite3.connect(db_path, timeout=10.0)
                try:
                    total = db.execute("SELECT COUNT(*) FROM worker_events").fetchone()[0]
                    # the rebuild itself: recount terminal activities from the log
                    db.execute(
                        "SELECT workflow_id, COUNT(*) FROM worker_events "
                        "WHERE kind='ACTIVITY_COMPLETED' GROUP BY workflow_id"
                    ).fetchall()
                finally:
                    db.close()
                lag = max(total - last_included, 0)
                last_included = total
                metrics.index_lag_events.set(float(lag))
                metrics.index_lag_samples.record(float(lag))
                index_lag_samples.append(lag)
            except sqlite3.Error:
                pass
            stop.wait(CONFIG["index_rebuild_interval_s"])

    def worker(worker_index: int) -> None:
        offset = (worker_index * 7) % len(tasks)
        order = tasks[offset:] + tasks[:offset]
        for _ in range(CONFIG["workflow_passes_per_worker"]):
            for project, activity_id in order:
                with budget_lock:
                    admission = budget.admit()
                    depth = budget.queued
                metrics.workflow_queue_depth.set(float(depth))
                if admission.verdict is BudgetVerdict.REFUSED_OVER_BUDGET:
                    metrics.workflow_queue_refusals.add(1.0)
                    bump("budget_refused")
                    continue
                try:
                    now = int(time.time())
                    try:
                        result = with_lock_retry(
                            metrics,
                            lambda: engine.claim(project, activity_id,
                                                 worker_id=f"w{worker_index}", now=now, ttl=30),
                            label="claim",
                            max_retries=CONFIG["max_claim_retries"],
                            phase=phase,
                        )
                    except RetryExhausted:
                        bump("claim_retry_exhausted")
                        continue
                    claimed_at = time.perf_counter()
                    bump(result.verdict.value)
                    if result.verdict is ClaimVerdict.HELD_BY_LIVE_WORKER:
                        metrics.record_conflict("held_by_live_worker", retried=False, phase=phase)
                        continue
                    if result.verdict is ClaimVerdict.RECOVERY_REQUIRED:
                        metrics.recovery_required_runs.add(1.0)
                        continue
                    if result.lease is None:
                        continue
                    metrics.workflow_schedule_to_claim_ms.record(
                        (claimed_at - scheduled_at[(project, activity_id)]) * 1000.0)
                    with_lock_retry(
                        metrics,
                        lambda l=result.lease: engine.heartbeat(l, now=int(time.time())),
                        label="heartbeat",
                        max_retries=CONFIG["max_claim_retries"],
                        phase=phase,
                    )
                    time.sleep(CONFIG["activity_hold_s"])  # the activity's own work
                    try:
                        ok = with_lock_retry(
                            metrics,
                            lambda l=result.lease: engine.complete(l, result_digest=f"{0:064d}"),
                            label="complete",
                            max_retries=CONFIG["max_claim_retries"],
                            phase=phase,
                        )
                    except RetryExhausted:
                        bump("complete_retry_exhausted")
                        continue
                    if ok:
                        completed_at = time.perf_counter()
                        metrics.workflow_claim_to_complete_ms.record((completed_at - claimed_at) * 1000.0)
                        workflow_latency_ms.append(
                            (completed_at - scheduled_at[(project, activity_id)]) * 1000.0)
                        bump("completed")
                    else:
                        bump("complete_refused_no_lease")
                finally:
                    with budget_lock:
                        budget.release(admission)

    samplers = []
    if sample_storage:
        samplers = [threading.Thread(target=storage_sampler, daemon=True),
                    threading.Thread(target=index_projection, daemon=True)]
        for thread in samplers:
            thread.start()

    started = time.perf_counter()
    threads = [threading.Thread(target=worker, args=(i,))
               for i in range(CONFIG["workflow_worker_threads"])]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    wall_s = time.perf_counter() - started
    stop.set()
    for thread in samplers:
        thread.join(timeout=2.0)

    final_counts = _row_counts(db_path)
    db_bytes = db_path.stat().st_size
    db = sqlite3.connect(db_path, timeout=10.0)
    try:
        terminal = db.execute(
            "SELECT status, COUNT(*) FROM worker_activities GROUP BY status").fetchall()
    finally:
        db.close()

    return {
        "label": label,
        "activities_scheduled": len(tasks),
        "wall_seconds": wall_s,
        "worker_threads": CONFIG["workflow_worker_threads"],
        "claim_outcomes": dict(sorted(outcomes.items())),
        "terminal_status_counts": {row[0]: row[1] for row in terminal},
        "budget": {"max_inflight": budget.max_inflight, "max_queue": budget.max_queue,
                   "refused": budget.refused, "degraded": budget.degraded,
                   "inflight_at_end": budget.inflight, "queued_at_end": budget.queued},
        "retry_exhausted": (outcomes.get("claim_retry_exhausted", 0)
                            + outcomes.get("complete_retry_exhausted", 0)),
        "db_bytes_final": db_bytes,
        "records_final": final_counts,
        "bytes_per_record_final": db_bytes / final_counts["total"] if final_counts["total"] else None,
        "storage_samples": len(storage_samples),
        "storage_sample_first_last": (storage_samples[:1] + storage_samples[-1:]) if storage_samples else [],
        "index_lag_samples": len(index_lag_samples),
        "index_lag_max": max(index_lag_samples) if index_lag_samples else None,
        "workflow_latency_ms_samples": len(workflow_latency_ms),
        "workflow_latency_p95_ms": percentile(workflow_latency_ms, 0.95) if workflow_latency_ms else None,
    }, workflow_latency_ms, list(index_lag_samples)


# --- H1: API concurrency ----------------------------------------------------


HTTP_PHASE = "api::evidence"


def run_http_phase(metrics: EngineeringOperationMetrics) -> tuple[dict, list[float]]:
    idp, secret_store = IdentityProvider(), SecretStore()
    service = EngineeringHttpService(idp=idp, secrets=secret_store)
    actor = Actor("writer", frozenset({"p"}),
                  frozenset({Capability.READ_EVIDENCE, Capability.WRITE_EVIDENCE}))
    token = idp.issue(actor)
    headers = {"Authorization": f"Bearer {token}"}
    service.ensure_project("p")

    availability_samples: list[float] = []
    lock = threading.Lock()
    outcomes: dict[str, int] = {}
    retry_exhausted = 0
    eventual_success = 0
    first_attempt_total = 0
    unhandled_exceptions = 0

    def bump(name: str) -> None:
        with lock:
            outcomes[name] = outcomes.get(name, 0) + 1

    def head_snapshot() -> str:
        status, body, _ = service.handle("GET", "/v1/projects/p/snapshot", headers, b"")
        return str(body["snapshot_id"])

    start_together = threading.Barrier(CONFIG["http_writer_threads"])

    def writer(index: int) -> None:
        nonlocal retry_exhausted, eventual_success, first_attempt_total, unhandled_exceptions
        start_together.wait()
        for n in range(CONFIG["http_writes_per_thread"]):
            payload = {"note": f"w{index}-{n}"}
            body = {
                "idempotency_key": f"key-{index}-{n}",
                "expected_snapshot_id": head_snapshot(),
                "payload": payload,
                "payload_hash": content_hash(payload),
            }
            attempts = 0
            first = True
            while True:
                try:
                    with time_into(metrics.api_latency_ms, {"route": "evidence"}):
                        status, response, _ = service.handle(
                            "POST", "/v1/projects/p/evidence", headers,
                            json.dumps(body).encode())
                except Exception as exc:  # noqa: BLE001 — an untyped failure is unavailability
                    with lock:
                        unhandled_exceptions += 1
                        if first:
                            first_attempt_total += 1
                            availability_samples.append(0.0)
                    bump(f"EXCEPTION:{type(exc).__name__}")
                    break
                code = str(response.get("error", int(status)))
                metrics.api_requests.add(1.0, {"outcome": code})
                bump(code)
                if first:
                    with lock:
                        first_attempt_total += 1
                        availability_samples.append(1.0 if int(status) == HTTPStatus.OK else 0.0)
                    first = False
                if int(status) == HTTPStatus.OK:
                    metrics.record_commit(phase=HTTP_PHASE)
                    with lock:
                        eventual_success += 1
                    break
                if response.get("error") == "SNAPSHOT_STALE":
                    attempts += 1
                    if attempts > CONFIG["http_max_retries"]:
                        metrics.record_conflict("snapshot_stale", retried=False, phase=HTTP_PHASE)
                        with lock:
                            retry_exhausted += 1
                        break
                    metrics.record_conflict("snapshot_stale", phase=HTTP_PHASE)
                    body["expected_snapshot_id"] = head_snapshot()
                    continue
                if response.get("error") == "IDEMPOTENCY_CONFLICT":
                    metrics.record_conflict("idempotency_conflict", retried=False, phase=HTTP_PHASE)
                    break
                break

    threads = [threading.Thread(target=writer, args=(i,))
               for i in range(CONFIG["http_writer_threads"])]
    started = time.perf_counter()
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    wall_s = time.perf_counter() - started

    project = service.projects["p"]
    return {
        "requests_first_attempt": first_attempt_total,
        "responses_by_code": dict(sorted(outcomes.items())),
        "first_attempt_success_ratio": (
            sum(availability_samples) / len(availability_samples) if availability_samples else None),
        "eventual_success": eventual_success,
        "eventual_success_ratio": eventual_success / first_attempt_total if first_attempt_total else None,
        "retry_exhausted": retry_exhausted,
        "unhandled_exceptions": unhandled_exceptions,
        "final_sequence": project.sequence,
        "evidence_records": len(project.evidence),
        "wall_seconds": wall_s,
    }, availability_samples


# --- S1: solver cost --------------------------------------------------------


def build_space(n_structures: int) -> tuple[StructureSpace, ProblemStructure, str, str]:
    space = StructureSpace(space_id="capacity-campaign")
    for i in range(n_structures):
        atoms = tuple(Atom(atom_id=f"a{2 * i + k}") for k in range(3))
        edges = (
            SupportEdge(source=f"a{2 * i}", target=f"a{2 * i + 1}", cost=1.0, licensed_at=0),
            SupportEdge(source=f"a{2 * i + 1}", target=f"a{2 * i + 2}", cost=1.0, licensed_at=0),
        )
        space.accumulate(ReducedStructure(
            structure=SupportStructure(structure_id=f"s{i}", atoms=atoms, edges=edges),
            roles=frozenset({f"r{i}"}),
            provenance=f"campaign::{i}",
            established_at=0,
        ))
    problem = ProblemStructure(
        problem_id="capacity-problem",
        qoi="capacity",
        required_roles=frozenset(f"r{i}" for i in range(n_structures)),
        required_authority=0,
    )
    return space, problem, "a0", f"a{2 * n_structures}"


def run_solver_phase(metrics: EngineeringOperationMetrics) -> dict:
    space, problem, start, goal = build_space(CONFIG["solver_chain_structures"])
    target = Target(target_id=problem.problem_id, qoi=problem.qoi, goal_atom=goal, required_authority=0)
    outcomes: dict[str, int] = {}
    for _ in range(CONFIG["solver_iterations"]):
        with time_into(metrics.solver_compile_ms, {"phase": "compose"}):
            composed = compose(space, problem, start=start, goal=goal)
        with time_into(metrics.solver_navigate_ms, {"phase": "navigate"}):
            report = solve(composed, target, start=start)
        outcomes[report.outcome.value] = outcomes.get(report.outcome.value, 0) + 1

    # the recursive loop: fibres opened and research rounds, counted from the trace
    open_problem = ProblemStructure(
        problem_id="capacity-open",
        qoi="capacity",
        required_roles=problem.required_roles | frozenset({"missing_a", "missing_b", "missing_c"}),
        required_authority=0,
    )
    events: dict[str, int] = {}

    def observer(event) -> None:
        events[event.kind] = events.get(event.kind, 0) + 1
        if event.kind == "FIBER_OPENED":
            metrics.solver_fibres_opened.add(1.0)
        elif event.kind == "RESEARCH_ROUND":
            metrics.solver_research_rounds.add(1.0)

    recursive = solve_recursive(
        space, open_problem, start=start, goal=goal,
        researcher=lambda fiber: (),
        decomposer=lambda atom: None,
        observer=observer,
    )
    return {
        "iterations": CONFIG["solver_iterations"],
        "structures_in_space": len(space.structures),
        "navigate_outcomes": outcomes,
        "recursive_events": dict(sorted(events.items())),
        "fibres_opened": metrics.solver_fibres_opened.total(),
        "research_rounds_counted": metrics.solver_research_rounds.total(),
        "research_rounds_reported_by_solver": recursive.research_rounds_spent,
        "recursive_outcome": recursive.report.outcome.value,
    }


# --- T1: status computation -------------------------------------------------


def run_status_phase(metrics: EngineeringOperationMetrics, root: Path) -> dict:
    store = SqliteEngineeringStateStore(root / "state.sqlite3")
    snapshot = ProjectSnapshot(
        project_id="p", sequence=0, previous_snapshot_id=None,
        evidence_cutoff="e:0", semantic_state_revision="s:0", metric_ledger_head="m:0",
        episode_store_head="ep:0", saturation_basis_ids=("b",), authority_projection_revision="a:0",
        controller_epoch_id="epoch", created_at_utc=T0,
    )
    head = store.initialize_project(snapshot)
    status = EpistemicStatus(
        project_snapshot_id=head.snapshot_id, target_id="t", fiber_id="f",
        axis_statuses=(EpistemicAxisStatus("KNOWLEDGE", True, 0, ("r1",)),),
        required_routes=("r1",), covered_routes=("r1",), missing_routes=(),
        active_residual_ids=(), freshness_stale=False, required_authority=0,
        available_support_paths=1, blocking_cut_ids=(), hard_gate_ids=("sat",),
        next_action=NextActionClass.COMPILE_SOLVER_VIEW, reasons=("ready",),
        metric_receipt_ids=("metric",), basis_fingerprints=("basis",),
    )
    store.record_epistemic_status(status)
    service = EngineeringReadService(store)
    status_ids = set()
    for _ in range(CONFIG["status_iterations"]):
        with time_into(metrics.status_computation_ms, {"op": "current_status"}):
            read = service.current_status(project_id="p", target_id="t", fiber_id="f")
        status_ids.add(read.status_id)
    return {
        "iterations": CONFIG["status_iterations"],
        "distinct_status_ids": len(status_ids),
        "samples": metrics.status_computation_ms.count(),
    }


# --- C1: context compilation ------------------------------------------------


def run_context_phase(metrics: EngineeringOperationMetrics) -> dict:
    items = tuple(
        ContextItem(
            record_id=f"rec-{i}",
            token_cost=10 + (i % 40),
            coverage_atoms=(f"atom-{i % 25}", f"atom-{(i + 7) % 25}"),
            fiber_ids=(f"fiber-{i % 5}",),
            mandatory=(i % 50 == 0),
        )
        for i in range(CONFIG["context_items"])
    )
    request = ContextCompileRequest(budget_tokens=1500, target_fibers=("fiber-0", "fiber-1"))
    verdicts: dict[str, int] = {}
    used = []
    for _ in range(CONFIG["context_iterations"]):
        with time_into(metrics.context_compilation_ms, {"op": "compile"}):
            report = compile_epistemic_context(items, request)
        verdicts[report.verdict.value] = verdicts.get(report.verdict.value, 0) + 1
        used.append(report.used_tokens)
    return {
        "iterations": CONFIG["context_iterations"],
        "items": len(items),
        "verdicts": verdicts,
        "used_tokens_mean": statistics.fmean(used),
        "budget_tokens": request.budget_tokens,
    }


# --- B1 / R1: backup freshness and recovery-required runs -------------------


def run_backup_and_recovery_phase(metrics: EngineeringOperationMetrics, root: Path) -> dict:
    backup_root = root / "backup-src"
    backup_root.mkdir(parents=True, exist_ok=True)
    (backup_root / "canonical.json").write_text(json.dumps({"snapshot": "snap-0"}))
    taken_at = time.time()
    manifest = take_backup(backup_root, backup_id="cap-1", created_at=now_utc())
    verdict, detail = verify_restore(backup_root, manifest)
    age_s = time.time() - taken_at
    metrics.backup_age_seconds.set(age_s)

    engine = SqliteWorkerWorkflowEngine(root / "recovery.sqlite3")
    driven = []
    for index, (retry_safe, external) in enumerate(((True, True), (False, False))):
        activity_id = f"rec-act-{index}"
        spec = ActivitySpec(activity_id=activity_id, invocation_id=f"inv-{activity_id}",
                            input_digest=f"{index:064d}", retry_safe=retry_safe,
                            external_effect=external, max_attempts=5)
        engine.schedule("wf-recovery", spec, idempotency_key=f"idem-{activity_id}")
        first = engine.claim("wf-recovery", activity_id, worker_id="dead", now=1000, ttl=5)
        assert first.lease is not None
        engine.mark_effect_started(first.lease)
        # the holder dies: no heartbeat, lease expires, another worker arrives
        second = engine.claim("wf-recovery", activity_id, worker_id="live", now=1100, ttl=5)
        if second.verdict is ClaimVerdict.RECOVERY_REQUIRED:
            metrics.recovery_required_runs.add(1.0)
        driven.append({"activity_id": activity_id, "retry_safe": retry_safe,
                       "external_effect": external, "verdict": second.verdict.value})

    return {
        "backup_verdict": verdict.value,
        "backup_detail": list(detail),
        "backup_entries": len(manifest.entries),
        "backup_age_seconds": age_s,
        "backup_is_exact": verdict is RestoreVerdict.EXACT,
        "driven_recovery_cases": driven,
        "recovery_required_runs_total": metrics.recovery_required_runs.total(),
    }


# --- D1: defect probes ------------------------------------------------------


def probe_http_same_key_race() -> dict:
    """`_validate_mutation` and `_apply_idempotent` read the head and the
    idempotency map outside `EngineeringHttpService._lock`. If that races, one
    logical mutation commits more than once."""

    idp, secret_store = IdentityProvider(), SecretStore()
    service = EngineeringHttpService(idp=idp, secrets=secret_store)
    actor = Actor("writer", frozenset({"p"}), frozenset({Capability.WRITE_EVIDENCE}))
    token = idp.issue(actor)
    headers = {"Authorization": f"Bearer {token}"}
    project = service.ensure_project("p")
    payload = {"note": "one logical mutation"}
    body = json.dumps({
        "idempotency_key": "the-one-key",
        "expected_snapshot_id": project.snapshot_id,
        "payload": payload,
        "payload_hash": content_hash(payload),
    }).encode()

    barrier = threading.Barrier(CONFIG["same_key_race_threads"])
    results: list[tuple[int, dict]] = []
    lock = threading.Lock()
    window_entries = {"count": 0}
    window_lock = threading.Lock()

    # Widen the unguarded window. `_validate_mutation` and `handle` call the
    # module-level `content_hash` BEFORE `_apply_idempotent` reads the
    # idempotency map, all outside `self._lock`. Sleeping inside it (sleep
    # releases the GIL) parks every thread in the window at once, so the read
    # of `project.idempotency` genuinely overlaps with other threads' apply().
    real_content_hash = engineering_http_module.content_hash

    def slow_content_hash(payload):
        with window_lock:
            window_entries["count"] += 1
        time.sleep(CONFIG["race_probe_window_sleep_s"])
        return real_content_hash(payload)

    # And hold the mutation itself open. `_apply_idempotent` reads
    # `project.idempotency.get(key)` OUTSIDE the lock, then calls apply() which
    # takes the lock, then writes the map entry after the lock is released. A
    # mutation that takes milliseconds (a real store write) is the production
    # shape of that critical section; a lock whose acquire sleeps first is how
    # the probe gives it that shape without touching the service code.
    class _SlowLock:
        def __init__(self, inner):
            self.inner = inner
            self.acquisitions = 0

        def __enter__(self):
            time.sleep(CONFIG["race_probe_window_sleep_s"])
            self.acquisitions += 1
            return self.inner.__enter__()

        def __exit__(self, *exc):
            return self.inner.__exit__(*exc)

    slow_lock = _SlowLock(service._lock)
    service._lock = slow_lock
    engineering_http_module.content_hash = slow_content_hash
    try:
        def fire() -> None:
            barrier.wait()
            status, response, _ = service.handle("POST", "/v1/projects/p/evidence", headers, body)
            with lock:
                results.append((int(status), response))

        threads = [threading.Thread(target=fire) for _ in range(CONFIG["same_key_race_threads"])]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
    finally:
        engineering_http_module.content_hash = real_content_hash
        service._lock = slow_lock.inner

    committed_fresh = [r for _, r in results if r.get("committed") and not r.get("replayed")]
    after_ids = {r.get("after_snapshot_id") for _, r in results if r.get("after_snapshot_id")}
    observed = project.sequence > 1 or len(project.evidence) > 1
    return {
        "probe": "http_same_idempotency_key_race",
        "threads": CONFIG["same_key_race_threads"],
        "expected_invariant": "one logical mutation advances the head exactly once",
        "final_sequence": project.sequence,
        "evidence_records": len(project.evidence),
        "fresh_commit_responses": len(committed_fresh),
        "distinct_after_snapshot_ids": sorted(x for x in after_ids if x),
        "verdict": "DEFECT_OBSERVED" if observed else "NOT_OBSERVED_IN_THIS_RUN",
        "duplicate_commits": max(project.sequence - 1, 0),
        "window_widened_by": (
            f"module-level content_hash patched to sleep {CONFIG['race_probe_window_sleep_s']}s "
            f"(entered {window_entries['count']} times across {CONFIG['same_key_race_threads']} threads) "
            f"AND service._lock wrapped so acquire sleeps {CONFIG['race_probe_window_sleep_s']}s "
            f"before taking the real lock ({slow_lock.acquisitions} acquisitions)"),
        "mutation_lock_acquisitions": slow_lock.acquisitions,
        "history": [
            {"attempt": 1, "window_widened": "none", "verdict": "NOT_OBSERVED_IN_THIS_RUN",
             "note": ("one handle() call completed in tens of microseconds against a 0.5ms switch "
                      "interval, so the window was never entered; that result carried no power")},
            {"attempt": 2, "window_widened": "content_hash sleeps 5ms (validate path only)",
             "verdict": "NOT_OBSERVED_IN_THIS_RUN", "duplicate_commits": 0,
             "note": ("all 16 threads read prior=None in _validate_mutation, but the second read in "
                      "_apply_idempotent, the apply() and the map write are microseconds apart with "
                      "no GIL yield between them; the first thread to wake wrote the map entry before "
                      "any other thread re-read it. The window that matters is read->apply->write, "
                      "not the validate path")},
        ],
        "power_note": (
            "with the mutation held open for milliseconds, every thread reads "
            "project.idempotency before any thread has written it; a NOT_OBSERVED here would "
            "be a real absence, not a timing artefact"),
    }


#: The observation this probe was written for, preserved verbatim from the run
#: that found it (untokened `release()`, before the fix landed).
_BUDGET_PROBE_HISTORY = [{
    "attempt": 1,
    "api": "untokened admit()/release()",
    "observation": ("after 4 admits (inflight=4) and a 5th admit (queued=1), releasing an ADMITTED "
                    "holder left inflight=4 and took queued to 0; six further admit/release cycles "
                    "all left inflight=4, queued=0, refused=0"),
    "inflight_after_four_admits": 4,
    "queued_after_fifth_admit": 1,
    "inflight_after_admitted_holder_released": 4,
    "ratchet_trace": [{"inflight": 4, "queued": 0, "refused": 0}] * 6,
    "verdict": "DEFECT_OBSERVED",
}, {
    "attempt": 2,
    "api": "tokened, Admission(verdict, slot) with the slot frozen at admit time",
    "observation": ("same trace: releasing the ADMITTED holder promoted the queued 5th caller "
                    "(inflight 4->3->4, queued 1->0), but the promoted caller's token still said "
                    "QUEUED, so its own release was a no-op. After every admission was released "
                    "inflight was 1, not 0: one slot leaked per promotion for the life of the budget"),
    "inflight_after_full_drain": 1,
    "verdict": "FIX_INCOMPLETE_LEAK_ON_FULL_DRAIN",
}]


def probe_resource_budget_release() -> dict:
    """Same trace as the original observation, on the tokened API, plus the
    invariant that decides whether the fix is complete: when every admission
    ever handed out has been released, inflight and queued are both zero.

    Interim counts can be argued either way (a promoted waiter is or is not
    "inflight"); the drain cannot. A budget that does not return to zero after
    every holder is gone has leaked a slot for the life of the process."""

    budget = ResourceBudget(max_inflight=4, max_queue=2, degrade_at_inflight=4)
    trace = []
    held: list[Admission] = []
    for _ in range(4):
        held.append(budget.admit())                 # four real holders
        trace.append(f"{held[-1].verdict.value}/{held[-1].slot.value}")
    inflight_after_admits = budget.inflight
    fifth = budget.admit()                          # a fifth: queued
    trace.append(f"{fifth.verdict.value}/{fifth.slot.value}")
    queued_after = budget.queued
    budget.release(held[0])                         # an ADMITTED holder finishes
    after_first_release = {"inflight": budget.inflight, "queued": budget.queued}
    ratchet = []
    for _ in range(6):
        cycle = budget.admit()
        budget.release(cycle)
        ratchet.append({"inflight": budget.inflight, "queued": budget.queued,
                        "refused": budget.refused, "slot": cycle.slot.value})
    outstanding = held[1:] + [fifth]
    drain_trace = []
    for admission in outstanding:
        budget.release(admission)
        drain_trace.append({"released_slot": admission.slot.value,
                            "inflight": budget.inflight, "queued": budget.queued})
    drained = budget.inflight == 0 and budget.queued == 0
    return {
        "probe": "resource_budget_release_accounting",
        "expected_invariant": ("releasing an admitted holder frees an inflight slot, and once every "
                               "admission has been released inflight == queued == 0"),
        "history": _BUDGET_PROBE_HISTORY,
        "api": "tokened admit() -> Admission; release(admission)",
        "admit_trace": trace,
        "inflight_after_four_admits": inflight_after_admits,
        "queued_after_fifth_admit": queued_after,
        "after_admitted_holder_released": after_first_release,
        "ratchet_trace": ratchet,
        "drain_trace": drain_trace,
        "inflight_after_full_drain": budget.inflight,
        "queued_after_full_drain": budget.queued,
        "leaked_slots_after_full_drain": budget.inflight + budget.queued,
        "verdict": "FIXED_VERIFIED" if drained else "FIX_INCOMPLETE_LEAK_ON_FULL_DRAIN",
        "detail": ("every admission released and the budget returned to zero" if drained else
                   "every admission released, yet the budget did not return to zero: a promoted "
                   "waiter's token still says QUEUED, so its release is a no-op and the inflight "
                   "slot it was promoted into is never freed"),
    }


# --- assembly ---------------------------------------------------------------


def hardware_context() -> dict:
    return {
        "note": "LAPTOP HARDWARE. These are measurements of this machine under this "
                "load. They are not a production capacity statement, and a missed "
                "envelope here is a measurement to report, not a budget to move.",
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "python": platform.python_version(),
        "sqlite_library_version": sqlite3.sqlite_version,
        "cpu_count": os.cpu_count(),
        "load_average_1_5_15": list(os.getloadavg()),
        "shared_machine_caveat": (
            "the load average above is the whole machine's, not this campaign's. This host runs "
            "other work, so wall-clock envelopes (workflow latency in particular) vary run to run; "
            "counted quantities (conflicts, refusals, retries, records) do not."),
        "measured_at_utc": now_utc(),
    }


def main() -> int:
    previous_switch_interval = sys.getswitchinterval()
    sys.setswitchinterval(CONFIG["thread_switch_interval_s"])
    metrics = EngineeringOperationMetrics(resource_attributes={"service.name": "orion-capacity-campaign"})
    started = time.perf_counter()

    with tempfile.TemporaryDirectory(prefix="orion-capacity-") as tmp:
        root = Path(tmp)
        w1_repeats: list[dict] = []
        workflow_latency_ms: list[float] = []
        index_lag_cold_start: list[int] = []
        index_lag_steady_state: list[int] = []
        index_lag_all: list[int] = []
        for repeat in range(CONFIG["workflow_repeats"]):
            print(f"W1  workflow concurrency (shipped 5s busy timeout) repeat {repeat + 1}"
                  f"/{CONFIG['workflow_repeats']}")
            result, latencies, lag = run_workflow_phase(
                metrics, root, label=f"shipped-{repeat}",
                engine_factory=SqliteWorkerWorkflowEngine, sample_storage=True)
            w1_repeats.append(result)
            workflow_latency_ms.extend(latencies)
            index_lag_all.extend(lag)
            if lag:
                # the first rebuild of a repeat has an empty baseline: it reports
                # every event the schedule burst committed. Cold start and steady
                # state are different operational statements.
                index_lag_cold_start.append(lag[0])
                index_lag_steady_state.extend(lag[1:])
        w1 = w1_repeats[-1]

        print("W2  workflow concurrency (probe: 20ms busy timeout)")
        probe_metrics = EngineeringOperationMetrics()
        w2, _, _ = run_workflow_phase(
            probe_metrics, root, label="low-busy-timeout",
            engine_factory=lambda p: _low_timeout_engine(p, CONFIG["probe_sqlite_busy_timeout_s"]),
            sample_storage=False)

        print("H1  API concurrency")
        h1, availability_samples = run_http_phase(metrics)

        print("S1  solver cost")
        s1 = run_solver_phase(metrics)

        print("T1  status computation")
        t1 = run_status_phase(metrics, root)

        print("C1  context compilation")
        c1 = run_context_phase(metrics)

        print("B1/R1  backup freshness and recovery-required runs")
        b1 = run_backup_and_recovery_phase(metrics, root)

        print("D1  defect probes")
        d1 = [probe_http_same_key_race(), probe_resource_budget_release()]

    samples_by_slo = {
        "transaction_latency_ms": metrics.txn_latency_ms.all_samples(),
        "workflow_latency_ms": workflow_latency_ms,
        "status_computation_ms": metrics.status_computation_ms.all_samples(),
        "solver_compilation_ms": metrics.solver_compile_ms.all_samples(),
        "solver_navigation_ms": metrics.solver_navigate_ms.all_samples(),
        "context_compilation_ms": metrics.context_compilation_ms.all_samples(),
        "storage_growth_bytes_per_record": metrics.storage_growth_bytes_per_record.all_samples(),
        "index_lag_events": index_lag_all,
        "api_availability_ratio": availability_samples,
    }
    readings = evaluate_slo_envelopes(samples_by_slo)

    exporter = MetricExporter()
    otlp = metrics.export(exporter)
    otlp_text = json.dumps(otlp)
    leaked = sorted({
        key for key in ("receipt.value", "receipt.claim", "receipt.effect_size",
                        "metric_receipt.value", "receipt.verdict")
        if key in otlp_text
    })

    acquisitions = sum(r["claim_outcomes"].get("ACQUIRED", 0) for r in w1_repeats)
    terminal_totals: dict[str, int] = {}
    for r in w1_repeats:
        for status, count in r["terminal_status_counts"].items():
            terminal_totals[status] = terminal_totals.get(status, 0) + count
    shipped_locked = metrics.conflicts_by_class().get("sqlite_locked", 0.0)
    probe_locked = probe_metrics.conflicts_by_class().get("sqlite_locked", 0.0)
    findings = [
        (f"under the shipped {CONFIG['shipped_sqlite_busy_timeout_s']}s sqlite busy timeout the "
         f"workflow load produced {shipped_locked:.0f} `database is locked` errors; lock contention "
         f"was absorbed as latency (claim/complete p95 {metrics.txn_latency_ms.percentile(0.95):.3f} ms "
         f"over {metrics.txn_latency_ms.count()} attempts), not surfaced as a conflict"),
        (f"with the busy timeout cut to {CONFIG['probe_sqlite_busy_timeout_s']}s the same load produced "
         f"{probe_locked:.0f} lock conflicts and a retry amplification of "
         f"{probe_metrics.retry_amplification():.4f} retries per commit"),
        (f"the workflow-layer conflict that does fire under the shipped configuration is the lease: "
         f"{metrics.conflicts_by_class().get('held_by_live_worker', 0.0):.0f} HELD_BY_LIVE_WORKER "
         f"verdicts across {acquisitions} acquisitions"),
        (f"the bounded budget (max_inflight={CONFIG['budget_max_inflight']}, "
         f"max_queue={CONFIG['budget_max_queue']}) refused "
         f"{metrics.workflow_queue_refusals.total():.0f} admissions before any mutation; every "
         f"scheduled activity still reached exactly one terminal receipt "
         f"({terminal_totals})"),
        (f"concurrent writers to one project head saw a first-attempt success ratio of "
         f"{h1['first_attempt_success_ratio']:.4f} ({h1['responses_by_code'].get('SNAPSHOT_STALE', 0)} "
         f"SNAPSHOT_STALE over {h1['requests_first_attempt']} first attempts); after bounded retry the "
         f"eventual success ratio was {h1['eventual_success_ratio']:.4f} with "
         f"{h1['unhandled_exceptions']} untyped failures"),
        (f"storage held {w1['records_final']['total']} canonical records in "
         f"{w1['db_bytes_final']} bytes, {w1['bytes_per_record_final']:.1f} bytes per record"),
        (f"the index-lag envelope is missed at cold start, not in steady state: pooled p95 "
         f"{percentile(index_lag_all, 0.95) if index_lag_all else None} events against a first-rebuild-"
         f"per-repeat set of {index_lag_cold_start} and a steady-state p95 of "
         f"{percentile(index_lag_steady_state, 0.95) if index_lag_steady_state else None} events"),
        (f"the same workflow load repeated {CONFIG['workflow_repeats']}x produced per-repeat "
         f"workflow-latency p95s of "
         f"{[round(r['workflow_latency_p95_ms'], 1) for r in w1_repeats]} ms against a "
         f"{ENGINEERING_SLO_ENVELOPES['workflow_latency_ms'].budget} ms budget; the reported verdict "
         f"is on the pooled {len(workflow_latency_ms)}-sample distribution"),
    ]

    receipt = {
        "schema_version": "orion-capacity-campaign-v1",
        "fibres": ["E17 item 19 (declared SLO envelopes)", "E17 item 20 (concurrency/load campaign)",
                   "E12 item 11 (named-operation instrumentation)"],
        "grants_scientific_authority": False,
        "hardware_context": hardware_context(),
        "budgets_frozen_before_execution": True,
        "budget_source": "rakl.engineering_capacity.ENGINEERING_SLO_ENVELOPES (imported, not declared here)",
        "configuration": dict(CONFIG),
        "harness_settings": {
            "python_thread_switch_interval_s_default": previous_switch_interval,
            "python_thread_switch_interval_s_used": sys.getswitchinterval(),
            "why": ("CPython's default switch interval lets one thread run thousands of these "
                    "operations before yielding, so nothing interleaves in-process. This changes "
                    "the scheduler, not the code under test."),
        },
        "declared_slo_envelopes": {k: v.to_dict() for k, v in sorted(ENGINEERING_SLO_ENVELOPES.items())},
        "required_slo_ids": list(REQUIRED_SLO_IDS),
        "instrumented_operations": {k: list(v) for k, v in INSTRUMENTED_OPERATIONS.items()},
        "measurements": {
            "W1_workflow_concurrency_shipped_config": {
                "repeats": w1_repeats,
                "workflow_latency_p95_ms_per_repeat": [r["workflow_latency_p95_ms"] for r in w1_repeats],
                "workflow_latency_pooled_samples": len(workflow_latency_ms),
                "acquisitions_total": acquisitions,
                "terminal_status_counts_total": terminal_totals,
                "why_repeated": (
                    "a single run of this phase decided the workflow-latency verdict by what else "
                    "this shared host was doing; the verdict below is on the pooled sample and the "
                    "per-repeat spread is stated"),
            },
            "I1_index_lag_cold_start_vs_steady_state": {
                "envelope_reading_is_on_the_pooled_sample": True,
                "first_rebuild_per_repeat_events": index_lag_cold_start,
                "cold_start_note": (
                    "the first rebuild of each repeat has an empty baseline, so it reports every "
                    "event the schedule burst committed. The envelope verdict stands as measured; "
                    "the steady-state figure below is reported alongside it, not in place of it."),
                "steady_state_samples": len(index_lag_steady_state),
                "steady_state_p50_events": (
                    percentile(index_lag_steady_state, 0.5) if index_lag_steady_state else None),
                "steady_state_p95_events": (
                    percentile(index_lag_steady_state, 0.95) if index_lag_steady_state else None),
                "steady_state_max_events": max(index_lag_steady_state) if index_lag_steady_state else None,
            },
            "W2_workflow_concurrency_low_busy_timeout_probe": {
                **w2,
                "probe_note": (
                    f"sqlite busy timeout patched from {CONFIG['shipped_sqlite_busy_timeout_s']}s "
                    f"to {CONFIG['probe_sqlite_busy_timeout_s']}s so lock contention surfaces as "
                    "`database is locked` instead of being absorbed as latency. Latencies from "
                    "this variant are NOT fed into the SLO evaluation."),
                "sqlite_locked_conflicts": probe_metrics.conflicts_by_class().get("sqlite_locked", 0.0),
                "conflicts_by_class": probe_metrics.conflicts_by_class(),
                "retry_amplification": probe_metrics.retry_amplification(),
            },
            "H1_api_concurrency": h1,
            "S1_solver_cost": s1,
            "T1_status_computation": t1,
            "C1_context_compilation": c1,
            "B1_R1_backup_and_recovery": b1,
        },
        "contention": {
            "conflicts_by_class": metrics.conflicts_by_class(),
            "retries_by_class": metrics.retries_by_class(),
            "commits_total": metrics.txn_commits.total(),
            "commits_by_phase": metrics.commits_by_phase(),
            "retries_by_phase": metrics.retries_by_phase(),
            "retry_amplification_by_phase": metrics.retry_amplification_by_phase(),
            "retry_amplification_pooled": metrics.retry_amplification(),
            "retry_amplification_definition":
                "retries issued / transactions that committed, each phase against its own commits",
            "denominator_composition": (
                "a committed transaction is any durable BEGIN IMMEDIATE that succeeded, which "
                "includes claims that committed a no-op because the activity was ALREADY_COMPLETED. "
                "Under this load most of the workflow denominator is such no-op claims, so these "
                "are retries per durable transaction, not retries per unit of work."),
            "workflow_claim_outcomes_behind_the_denominator": {
                "acquired": acquisitions,
                "already_completed": sum(r["claim_outcomes"].get("ALREADY_COMPLETED", 0)
                                         for r in w1_repeats),
                "held_by_live_worker": sum(r["claim_outcomes"].get("HELD_BY_LIVE_WORKER", 0)
                                           for r in w1_repeats),
            },
        },
        "queue_saturation": {
            "budget": w1["budget"],
            "refusals_counted": metrics.workflow_queue_refusals.total(),
            "final_queue_depth_gauge": metrics.workflow_queue_depth.value(),
        },
        "storage_scaling": {
            "db_bytes_final": w1["db_bytes_final"],
            "records_final": w1["records_final"],
            "bytes_per_record_final": w1["bytes_per_record_final"],
            "bytes_per_record_samples": len(samples_by_slo["storage_growth_bytes_per_record"]),
            "sample_first_last": w1["storage_sample_first_last"],
        },
        "slo_readings": [r.to_dict() for r in readings],
        "slo_summary": {
            "met": sorted(r.slo_id for r in readings if r.verdict is SloVerdict.MET),
            "missed": sorted(r.slo_id for r in readings if r.verdict is SloVerdict.MISSED),
            "cannot_check": sorted(r.slo_id for r in readings if r.verdict is SloVerdict.CANNOT_CHECK),
        },
        "receipt_separation_check": {
            "rule": "an operational metric may reference a receipt id and carry no other receipt content",
            "otlp_payload_bytes": len(otlp_text),
            "receipt_content_keys_found_in_export": leaked,
            "held": not leaked,
        },
        "findings": findings,
        "defect_probes": d1,
        "not_claimed": [
            "production capacity: every number here is laptop hardware under this load",
            "a distributed multi-process campaign: workers are threads in one process",
            "PostgreSQL serializable behaviour: the durable engine under test is SQLite",
            "that a met envelope on this machine will be met on any other",
        ],
        "campaign_wall_seconds": time.perf_counter() - started,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(f"\nwrote {OUT}")
    print(f"  MET         {receipt['slo_summary']['met']}")
    print(f"  MISSED      {receipt['slo_summary']['missed']}")
    print(f"  CANNOT_CHECK{receipt['slo_summary']['cannot_check']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
