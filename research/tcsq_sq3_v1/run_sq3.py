#!/usr/bin/env python3
"""TCSQ SQ-3: net solver/cost advantage of a task-conditioned structural quotient.

Where this sits in the TCSQ ladder (``research/tcsq_v0/README.md``):

* ``SQ-1`` (``scripts/tcsq_sq1_oracle_upper_bound.py``) asked whether an *oracle*
  quotient, handed the verifier's dependency graph, still reproduces the exact
  verdict while dropping representation mass.  It is a representation upper bound
  and explicitly disclaims cost.
* ``SQ-2`` (``scripts/tcsq_sq2_intervention_fidelity.py``) asked whether a finite
  registered intervention audit *recovers* the exact dependency set
  (precision/recall/specificity over coordinates).  It also explicitly disclaims
  cost.
* ``SQ-3`` -- this harness -- asks the question both of those refused to answer:
  **after paying for quotient construction, per-instance ledger/projection,
  original-problem verification, and repair of false erasures, does quotienting
  reduce TOTAL cost to solve N tasks against strong controls?**

Design (deterministic known world, seed 461)
--------------------------------------------
Each task is a bounded action-planning instance over a 16-state / 4-action
machine, described by 12 registered coordinates:

  essential            transitions, start, goal, budget, forbidden_actions
  conditionally ess.   overflow_guard  (binds only when the shortest plan is
                                        longer than GUARD_THRESHOLD -- rare)
  nuisance             title, author, notes, render_style, schema_rev,
                       submitted_at

A stream of ``N_TASKS`` tasks is drawn from ``n_distinct`` distinct essential
structures, so the *redundancy rate* ``1 - n_distinct/N_TASKS`` is a controlled
knob.  Nuisance coordinates are re-randomised per task, so two instances of the
same essential structure are genuinely distinct-but-equivalent: only a quotient
that erases nuisance can collapse them.

Arms (SQ-3 gate arm names in brackets)
--------------------------------------
  RAW_NO_QUOTIENT            [RAW]                  solve every task
  SURFACE_HASH_DEDUP         [GENERIC_COMPRESSION]  cache keyed on the rendered
                                                    surface string (catches only
                                                    byte-identical records)
  STRUCTURE_NO_ERASURE       [STRUCTURE_NO_ERASURE] cache keyed on the canonical
                                                    12-coordinate record (format
                                                    normalised, nothing erased)
  TCSQ_VALIDATED_QUOTIENT    [TCSQ]                 erasure ledger DISCOVERED by
                                                    a charged intervention audit,
                                                    materialised through
                                                    ``rakl.semantic_quotient_assurance
                                                    .assured_materialize_validated_quotient``
  ORACLE_QUOTIENT            [ORACLE_QUOTIENT]      same machinery, erasure set
                                                    handed over by the generator,
                                                    zero construction cost

``INCUMBENT_RAKL`` from the SQ-3 gate is NOT implemented here and is reported as
an unfilled arm.

Cost model (one unit = one counted operation, all arms share the unit)
----------------------------------------------------------------------
  solve            one op per (state, action) transition evaluated by BFS
  verify (plan)    one op per replayed action of a reused plan
  verify (refusal) a refusal/no-solution answer cannot be checked by replay, so
                   verifying one costs a FULL solve -- charged, not hidden
  coordinate op    one op per coordinate read / normalised / classified
                     surface dedup      12 (read the whole record)
                     structure dedup    24 (read + canonically normalise)
                     TCSQ / oracle      12 (classify every coordinate into the
                                            erasure ledger for this instance)
                                      + |preserved| (project the class key)
  construction     TCSQ pays PROBE_BUDGET x (1 + 12) solves for the intervention
                   audit that discovers the erasure ledger
  maintenance      every original-problem verification failure re-probes the
                   disagreeing erased coordinates (one solve each), promotes them
                   back into the preserved set, re-keys the whole cache
                   (projection ops per entry) and re-solves the failing task

Correctness is a co-primary, not an afterthought: every reused answer is checked
against the ORIGINAL problem before it is accepted, so a quotient that erases an
essential coordinate pays for its mistake in cost rather than silently returning
a wrong answer.  The error rate the quotient WOULD have had without that check is
reported separately as ``unverified_reuse_error_rate``.

Honesty
-------
Development known-world instrument.  It does not settle whether task-conditioned
structural quotients pay off on natural problems, with LLM solvers, or under any
distribution other than this generator.  Negative cells are reported, not hidden.
Grants no scientific or method-promotion authority.
"""
from __future__ import annotations

import argparse
from collections import deque
from hashlib import sha256
import json
from pathlib import Path
import random
import statistics

from rakl.semantic_quotient import (
    ProblemRepresentation,
    QuotientProposal,
    QuotientValidationReport,
    QuotientValidationVerdict,
)
from rakl.semantic_quotient_assurance import (
    ResolvedQuotientValidationReceipt,
    assured_materialize_validated_quotient,
)

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RESULT_FILE = HERE / "results" / "sq3.json"

SEED = 461
PAPER2_CONFIRMATORY_SEED_DO_NOT_USE = 2026081202

N_STATES = 16
ACTIONS = ("a", "b", "c", "d")
GUARD_THRESHOLD = 3

N_TASKS = 300
REPLICATES = 20
PROBE_BUDGET = 8
SURFACE_DUPLICATE_FRACTION = 0.12
BOOTSTRAP_RESAMPLES = 4000
DISTINCT_FRACTIONS = (1.0, 0.75, 0.5, 0.25, 0.1, 0.04)

ESSENTIAL_COORDINATES = ("budget", "forbidden_actions", "goal", "start", "transitions")
CONDITIONAL_COORDINATES = ("overflow_guard",)
NUISANCE_COORDINATES = (
    "author",
    "notes",
    "render_style",
    "schema_rev",
    "submitted_at",
    "title",
)
COORDINATES = tuple(
    sorted(ESSENTIAL_COORDINATES + CONDITIONAL_COORDINATES + NUISANCE_COORDINATES)
)
ORACLE_PRESERVED = tuple(sorted(ESSENTIAL_COORDINATES + CONDITIONAL_COORDINATES))

QOI = "verified_bounded_action_plan"
CONTEXT_HASH = "ctx:tcsq-sq3-known-world-v1"

ARMS = (
    "RAW_NO_QUOTIENT",
    "SURFACE_HASH_DEDUP",
    "STRUCTURE_NO_ERASURE",
    "TCSQ_VALIDATED_QUOTIENT",
    "ORACLE_QUOTIENT",
)
CONTROL_ARMS = ("RAW_NO_QUOTIENT", "SURFACE_HASH_DEDUP", "STRUCTURE_NO_ERASURE")

CLAIM_BOUNDARY = (
    "development known-world instrument; one synthetic bounded-planning generator, "
    "one hand-registered coordinate schema, one hand-registered intervention family, "
    "and a hand-specified operation-count cost model. It does NOT settle whether "
    "task-conditioned structural quotients reduce cost on natural problems, with LLM "
    "solvers, on unseen coordinate schemas, or under any other distribution. Grants no "
    "scientific or method-promotion authority."
)


# --------------------------------------------------------------------------
# cost meter
# --------------------------------------------------------------------------
class Meter:
    """Counts world/bookkeeping operations in a single shared unit."""

    def __init__(self) -> None:
        self.buckets: dict[str, int] = {}

    def charge(self, bucket: str, ops: int) -> None:
        if ops < 0:
            raise ValueError("cost must be non-negative")
        self.buckets[bucket] = self.buckets.get(bucket, 0) + ops

    @property
    def total(self) -> int:
        return sum(self.buckets.values())

    def snapshot(self) -> dict[str, int]:
        return dict(sorted(self.buckets.items()))


# --------------------------------------------------------------------------
# known world
# --------------------------------------------------------------------------
def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_essential_structure(rng: random.Random) -> dict[str, object]:
    transitions = [
        [state, action, rng.randrange(N_STATES)]
        for state in range(N_STATES)
        for action in ACTIONS
    ]
    forbidden_count = rng.choice((0, 1, 1, 2))
    forbidden = sorted(rng.sample(ACTIONS, forbidden_count))
    return {
        "transitions": transitions,
        "start": rng.randrange(N_STATES),
        "goal": rng.randrange(N_STATES),
        "budget": rng.randrange(3, 9),
        "forbidden_actions": forbidden,
        "overflow_guard": rng.choice(("strict", "lenient")),
    }


def make_nuisance(rng: random.Random) -> dict[str, object]:
    return {
        "title": f"case-{rng.randrange(10**6)}",
        "author": rng.choice(("ada", "bo", "chi", "dee", "eli")),
        "notes": rng.choice(("urgent", "routine", "revisit", "", "flagged")),
        "render_style": rng.choice(("compact", "wide", "indent2", "indent4")),
        "schema_rev": rng.choice(("r1", "r2", "r3")),
        "submitted_at": f"2026-08-{rng.randrange(1, 29):02d}",
    }


def render_surface(task: dict[str, object]) -> str:
    """Rendered record with formatting jitter driven by nuisance coordinates.

    SURFACE_HASH_DEDUP keys on this string, so only byte-identical records
    collide; STRUCTURE_NO_ERASURE keys on the canonical coordinate map and so
    is immune to the formatting jitter but still erases nothing.
    """
    style = task["render_style"]
    pad = {"compact": "", "wide": "  ", "indent2": "  ", "indent4": "    "}[str(style)]
    order = COORDINATES if style != "wide" else tuple(reversed(COORDINATES))
    return "\n".join(f"{pad}{name}={_canon(task[name])}" for name in order)


def build_task(base: dict[str, object], nuisance: dict[str, object], index: int) -> dict[str, object]:
    task = dict(base)
    task.update(nuisance)
    task["_index"] = index
    task["_surface"] = ""
    task["_surface"] = render_surface(task)
    return task


def solve(task: dict[str, object], meter: Meter, bucket: str = "solve") -> tuple[str, tuple[str, ...]]:
    """Exact bounded planner over the original problem. Cost = transitions evaluated."""
    forbidden = set(task["forbidden_actions"])  # type: ignore[arg-type]
    trans = {(s, a): n for s, a, n in task["transitions"]}  # type: ignore[misc]
    start = task["start"]
    goal = task["goal"]
    budget = int(task["budget"])  # type: ignore[arg-type]

    parents: dict[int, tuple[int, str] | None] = {int(start): None}  # type: ignore[arg-type]
    depth = {int(start): 0}  # type: ignore[arg-type]
    queue: deque[int] = deque([int(start)])  # type: ignore[arg-type]
    ops = 0
    found = None
    while queue:
        state = queue.popleft()
        if state == goal:
            found = state
            break
        if depth[state] >= N_STATES:
            continue
        for action in ACTIONS:
            ops += 1
            if action in forbidden:
                continue
            nxt = trans[(state, action)]
            if nxt not in depth:
                depth[nxt] = depth[state] + 1
                parents[nxt] = (state, action)
                queue.append(nxt)
    meter.charge(bucket, ops)

    if found is None:
        return ("NO_SOLUTION", ())
    path: list[str] = []
    cursor: int | None = int(goal)  # type: ignore[arg-type]
    while parents[cursor] is not None:
        prev, action = parents[cursor]  # type: ignore[misc]
        path.append(action)
        cursor = prev
    plan = tuple(reversed(path))
    if len(plan) > budget:
        return ("NO_SOLUTION", ())
    if len(plan) > GUARD_THRESHOLD and task["overflow_guard"] == "strict":
        return ("REFUSED_OVERFLOW", ())
    return ("SOLVED", plan)


def verify_against_original(
    task: dict[str, object],
    answer: tuple[str, tuple[str, ...]],
    meter: Meter,
    bucket: str = "verify",
) -> bool:
    """Check a reused answer against the ORIGINAL problem.

    A positive plan is checked by replay (cheap). A refusal / no-solution answer
    cannot be checked by replay -- establishing it costs a full solve, which is
    charged, not waived.
    """
    status, plan = answer
    if status != "SOLVED":
        return solve(task, meter, bucket=bucket) == answer
    forbidden = set(task["forbidden_actions"])  # type: ignore[arg-type]
    trans = {(s, a): n for s, a, n in task["transitions"]}  # type: ignore[misc]
    state = int(task["start"])  # type: ignore[arg-type]
    ops = 0
    for action in plan:
        ops += 1
        if action in forbidden or (state, action) not in trans:
            meter.charge(bucket, ops)
            return False
        state = trans[(state, action)]
    meter.charge(bucket, max(1, ops))
    if state != task["goal"]:
        return False
    if len(plan) > int(task["budget"]):  # type: ignore[arg-type]
        return False
    if len(plan) > GUARD_THRESHOLD and task["overflow_guard"] == "strict":
        return False
    return True


# --------------------------------------------------------------------------
# registered interventions (the only way the TCSQ arm may learn about erasure)
# --------------------------------------------------------------------------
def perturbed_value(coordinate: str, value: object) -> object:
    if coordinate == "transitions":
        return [[s, a, (n + 1) % N_STATES] for s, a, n in value]  # type: ignore[misc]
    if coordinate == "start":
        return (int(value) + 7) % N_STATES  # type: ignore[arg-type]
    if coordinate == "goal":
        return (int(value) + 9) % N_STATES  # type: ignore[arg-type]
    if coordinate == "budget":
        return 1
    if coordinate == "forbidden_actions":
        return ["a", "b", "c"]
    if coordinate == "overflow_guard":
        return "lenient" if value == "strict" else "strict"
    if coordinate in NUISANCE_COORDINATES:
        return "INTERVENTION_NUISANCE_PROBE"
    raise KeyError(f"no registered intervention for {coordinate}")


def intervene(task: dict[str, object], coordinate: str) -> dict[str, object]:
    probe = dict(task)
    probe[coordinate] = perturbed_value(coordinate, task[coordinate])
    return probe


def discover_erasure_ledger(
    probes: list[dict[str, object]], meter: Meter
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Charged intervention audit. Returns (preserved, erased) coordinate sets.

    This is the SQ-2 procedure executed as a *cost-bearing* construction step:
    a coordinate is preserved iff its registered intervention changes the exact
    answer on at least one probe task. The audit never reads the generator's
    essential/nuisance labels.
    """
    baselines = [solve(task, meter, bucket="construction") for task in probes]
    sensitive: set[str] = set()
    for coordinate in COORDINATES:
        for task, baseline in zip(probes, baselines):
            changed = solve(intervene(task, coordinate), meter, bucket="construction")
            meter.charge("construction", 1)
            if changed != baseline:
                sensitive.add(coordinate)
                break
    preserved = tuple(sorted(sensitive))
    erased = tuple(sorted(set(COORDINATES) - sensitive))
    return preserved, erased


def reprobe_coordinates(
    task: dict[str, object], coordinates: tuple[str, ...], meter: Meter
) -> tuple[str, ...]:
    """Maintenance re-probe on a task that broke original-problem verification."""
    baseline = solve(task, meter, bucket="maintenance")
    promoted: list[str] = []
    for coordinate in coordinates:
        changed = solve(intervene(task, coordinate), meter, bucket="maintenance")
        meter.charge("maintenance", 1)
        if changed != baseline:
            promoted.append(coordinate)
    return tuple(sorted(promoted))


# --------------------------------------------------------------------------
# TCSQ view construction through the real rakl API
# --------------------------------------------------------------------------
def build_validated_view(
    task: dict[str, object],
    preserved: tuple[str, ...],
    erased: tuple[str, ...],
    audit_digest: str,
    label: str,
):
    """Materialise a per-instance validated quotient view via the assured entry point.

    Everything the solver later relies on (which coordinates survive) is read
    back off the ``ValidatedQuotientView`` produced by
    ``assured_materialize_validated_quotient``; the harness never bypasses the
    partition/obligation/evidence contract in ``rakl.semantic_quotient``.
    """
    index = task["_index"]
    source_hash = "sha256:" + sha256(
        _canon({name: task[name] for name in COORDINATES}).encode("utf-8")
    ).hexdigest()
    source = ProblemRepresentation(
        representation_id=f"{label}:rep:{index}",
        problem_id=f"{label}:problem:{index}",
        atom_id=f"{label}:atom:{index}",
        qoi=QOI,
        context_hash=CONTEXT_HASH,
        source_hash=source_hash,
        coordinates=COORDINATES,
    )
    obligation = "erased_coordinates_did_not_change_the_exact_answer_on_the_charged_probe_sample"
    proposal = QuotientProposal(
        quotient_id=f"{label}:quotient:{index}",
        source_representation_id=source.representation_id,
        source_hash=source_hash,
        qoi=QOI,
        context_hash=CONTEXT_HASH,
        preserved_coordinates=preserved,
        erased_coordinates=erased,
        equivalence_generators=("registered_coordinate_substitution_orbit",),
        preserved_invariants=("exact_bounded_plan_answer_of_the_original_problem",),
        sufficiency_obligations=(obligation,),
        falsifiers=("original_problem_verification_failure_on_any_reused_answer",),
        forbidden_losses=(),
        proposer_kind="RULE_BASED_INTERVENTION_AUDIT",
        evidence_pointers=(audit_digest,),
    )
    report = QuotientValidationReport(
        quotient_id=proposal.quotient_id,
        proposal_hash=proposal.content_hash,
        source_hash=source_hash,
        verdict=QuotientValidationVerdict.VALID_EXACT,
        verified_obligations=(obligation,),
        oracle_checks=("known_world_registered_intervention_audit",),
        evidence_pointers=(audit_digest,),
    )
    receipt = ResolvedQuotientValidationReceipt(
        receipt_id=f"{label}:receipt:{index}",
        validation_report_hash=report.content_hash,
        proposal_hash=proposal.content_hash,
        source_hash=source_hash,
        verifier_id="known_world_intervention_auditor_v1",
        evidence_content_hashes=(audit_digest,),
    )
    return assured_materialize_validated_quotient(
        source,
        proposal,
        report,
        validation_receipt=receipt,
        resolved_receipt_ids=(receipt.receipt_id,),
        desired_effects=(QOI,),
    )


def class_key(task: dict[str, object], preserved: tuple[str, ...]) -> str:
    return _canon([[name, task[name]] for name in preserved])


# --------------------------------------------------------------------------
# arms
# --------------------------------------------------------------------------
def run_raw(tasks: list[dict[str, object]]) -> dict[str, object]:
    meter = Meter()
    answers = [solve(task, meter) for task in tasks]
    return {"meter": meter, "answers": answers, "extra": {}}


def run_hash_cache(tasks: list[dict[str, object]], mode: str) -> dict[str, object]:
    """SURFACE_HASH_DEDUP / STRUCTURE_NO_ERASURE.

    Both are sound by construction: a hit means every coordinate is identical, so
    the cached answer is the answer to the same problem and needs no verification.
    """
    meter = Meter()
    cache: dict[str, tuple[str, tuple[str, ...]]] = {}
    answers = []
    hits = 0
    for task in tasks:
        if mode == "surface":
            meter.charge("key", len(COORDINATES))
            key = str(task["_surface"])
        else:
            meter.charge("key", 2 * len(COORDINATES))
            key = class_key(task, COORDINATES)
        if key in cache:
            hits += 1
            answers.append(cache[key])
            continue
        answer = solve(task, meter)
        cache[key] = answer
        answers.append(answer)
    return {"meter": meter, "answers": answers, "extra": {"cache_hits": hits, "classes": len(cache)}}


def run_quotient_arm(
    tasks: list[dict[str, object]],
    label: str,
    *,
    oracle: bool,
    probe_budget: int,
) -> dict[str, object]:
    """TCSQ_VALIDATED_QUOTIENT (oracle=False) / ORACLE_QUOTIENT (oracle=True)."""
    meter = Meter()

    if oracle:
        preserved = ORACLE_PRESERVED
        erased = tuple(sorted(set(COORDINATES) - set(preserved)))
        audit_digest = "sha256:oracle-generator-supplied-erasure-ledger"
    else:
        probes = tasks[:probe_budget]
        preserved, erased = discover_erasure_ledger(probes, meter)
        audit_digest = "sha256:" + sha256(
            _canon({"preserved": list(preserved), "probes": probe_budget}).encode("utf-8")
        ).hexdigest()

    initial_preserved = preserved
    cache: dict[str, tuple[tuple[str, tuple[str, ...]], dict[str, object]]] = {}
    answers: list[tuple[str, tuple[str, ...]]] = []
    hits = 0
    verified_hits = 0
    verification_failures = 0
    unverified_errors = 0
    promotions: list[str] = []
    verification_free_ops = 0

    for task in tasks:
        # per-instance erasure ledger materialised through the rakl API
        meter.charge("ledger", len(COORDINATES))
        view = build_validated_view(task, preserved, erased, audit_digest, label)
        active = view.structural_coordinates
        meter.charge("projection", len(active))
        verification_free_ops += len(COORDINATES) + len(active)

        key = class_key(task, active)
        if key not in cache:
            before = meter.total
            answer = solve(task, meter)
            verification_free_ops += meter.total - before
            cache[key] = (answer, task)
            answers.append(answer)
            continue

        hits += 1
        candidate, representative = cache[key]
        ok = verify_against_original(task, candidate, meter)
        if ok:
            verified_hits += 1
            answers.append(candidate)
            continue

        # false erasure: the quotient collapsed two genuinely different problems
        verification_failures += 1
        unverified_errors += 1
        differing = tuple(
            sorted(name for name in erased if _canon(task[name]) != _canon(representative[name]))
        )
        promoted = reprobe_coordinates(task, differing, meter)
        if promoted:
            preserved = tuple(sorted(set(preserved) | set(promoted)))
            erased = tuple(sorted(set(COORDINATES) - set(preserved)))
            promotions.extend(promoted)
            rekeyed: dict[str, tuple[tuple[str, tuple[str, ...]], dict[str, object]]] = {}
            for cached_answer, cached_task in cache.values():
                meter.charge("maintenance", len(preserved))
                rekeyed[class_key(cached_task, preserved)] = (cached_answer, cached_task)
            cache = rekeyed
        answer = solve(task, meter, bucket="repair")
        cache[class_key(task, preserved)] = (answer, task)
        answers.append(answer)

    return {
        "meter": meter,
        "answers": answers,
        "extra": {
            "cache_hits": hits,
            "verified_hits": verified_hits,
            "classes": len(cache),
            "verification_failures": verification_failures,
            "unverified_reuse_errors": unverified_errors,
            "initial_preserved": list(initial_preserved),
            "final_preserved": list(preserved),
            "promoted_coordinates": sorted(set(promotions)),
            "recovered_oracle_ledger": tuple(sorted(initial_preserved)) == ORACLE_PRESERVED,
            "cost_without_verification": verification_free_ops,
        },
    }


# --------------------------------------------------------------------------
# stream construction and replicate execution
# --------------------------------------------------------------------------
def build_stream(rng: random.Random, n_tasks: int, n_distinct: int) -> list[dict[str, object]]:
    bases = [make_essential_structure(rng) for _ in range(n_distinct)]
    assignment = list(range(n_distinct)) + [
        rng.randrange(n_distinct) for _ in range(n_tasks - n_distinct)
    ]
    rng.shuffle(assignment)
    tasks = [
        build_task(bases[base_index], make_nuisance(rng), index)
        for index, base_index in enumerate(assignment)
    ]
    # inject exact surface duplicates so SURFACE_HASH_DEDUP is a live control
    duplicate_slots = sorted(
        rng.sample(range(1, n_tasks), int(round(SURFACE_DUPLICATE_FRACTION * n_tasks)))
    )
    for slot in duplicate_slots:
        donor = dict(tasks[rng.randrange(slot)])
        donor["_index"] = slot
        tasks[slot] = donor
    return tasks


def run_replicate(seed: int, n_tasks: int, n_distinct: int, probe_budget: int) -> dict[str, object]:
    rng = random.Random(seed)
    tasks = build_stream(rng, n_tasks, n_distinct)
    gold_meter = Meter()
    gold = [solve(task, gold_meter) for task in tasks]

    results = {
        "RAW_NO_QUOTIENT": run_raw(tasks),
        "SURFACE_HASH_DEDUP": run_hash_cache(tasks, "surface"),
        "STRUCTURE_NO_ERASURE": run_hash_cache(tasks, "structure"),
        "TCSQ_VALIDATED_QUOTIENT": run_quotient_arm(
            tasks, f"sq3-{seed}-tcsq", oracle=False, probe_budget=probe_budget
        ),
        "ORACLE_QUOTIENT": run_quotient_arm(
            tasks, f"sq3-{seed}-oracle", oracle=True, probe_budget=probe_budget
        ),
    }

    row: dict[str, object] = {
        "seed": seed,
        "n_tasks": n_tasks,
        "n_distinct": n_distinct,
        "gold_status_counts": {
            status: sum(1 for answer in gold if answer[0] == status)
            for status in ("SOLVED", "NO_SOLUTION", "REFUSED_OVERFLOW")
        },
        "guard_binding_fraction": sum(
            1
            for task, answer in zip(tasks, gold)
            if answer[0] == "REFUSED_OVERFLOW"
            or (answer[0] == "SOLVED" and len(answer[1]) > GUARD_THRESHOLD)
        )
        / n_tasks,
        "arms": {},
    }
    for arm, payload in results.items():
        meter: Meter = payload["meter"]  # type: ignore[assignment]
        answers = payload["answers"]
        correct = sum(1 for produced, truth in zip(answers, gold) if produced == truth)
        row["arms"][arm] = {  # type: ignore[index]
            "total_cost": meter.total,
            "cost_breakdown": meter.snapshot(),
            "original_problem_success": correct / n_tasks,
            **payload["extra"],  # type: ignore[dict-item]
        }
    return row


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------
def bootstrap_ci(values: list[float], rng: random.Random, resamples: int) -> dict[str, float]:
    n = len(values)
    means = []
    for _ in range(resamples):
        means.append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return {
        "mean": statistics.fmean(values),
        "lo": means[int(0.025 * resamples)],
        "hi": means[int(0.975 * resamples)],
        "n": n,
    }


def summarise_cell(rows: list[dict[str, object]], n_tasks: int, n_distinct: int, boot_seed: int) -> dict[str, object]:
    arms_summary: dict[str, object] = {}
    for arm in ARMS:
        costs = [float(row["arms"][arm]["total_cost"]) for row in rows]  # type: ignore[index]
        accs = [float(row["arms"][arm]["original_problem_success"]) for row in rows]  # type: ignore[index]
        arms_summary[arm] = {
            "total_cost": bootstrap_ci(costs, random.Random(boot_seed + hash(arm) % 9973), BOOTSTRAP_RESAMPLES),
            "original_problem_success_mean": statistics.fmean(accs),
            "original_problem_success_min": min(accs),
        }

    tcsq_costs = [float(row["arms"]["TCSQ_VALIDATED_QUOTIENT"]["total_cost"]) for row in rows]  # type: ignore[index]
    net: dict[str, object] = {}
    for control in CONTROL_ARMS + ("ORACLE_QUOTIENT",):
        control_costs = [float(row["arms"][control]["total_cost"]) for row in rows]  # type: ignore[index]
        deltas = [c - t for c, t in zip(control_costs, tcsq_costs)]
        net[f"net_vs_{control}"] = {
            **bootstrap_ci(deltas, random.Random(boot_seed + 17), BOOTSTRAP_RESAMPLES),
            "fraction_replicates_negative": sum(1 for d in deltas if d < 0) / len(deltas),
        }
    best_control = [
        min(float(row["arms"][control]["total_cost"]) for control in CONTROL_ARMS)  # type: ignore[index]
        for row in rows
    ]
    best_deltas = [c - t for c, t in zip(best_control, tcsq_costs)]
    net["net_vs_best_control"] = {
        **bootstrap_ci(best_deltas, random.Random(boot_seed + 31), BOOTSTRAP_RESAMPLES),
        "fraction_replicates_negative": sum(1 for d in best_deltas if d < 0) / len(best_deltas),
        "relative_to_best_control": statistics.fmean(best_deltas) / statistics.fmean(best_control),
    }

    failures = [int(row["arms"]["TCSQ_VALIDATED_QUOTIENT"]["verification_failures"]) for row in rows]  # type: ignore[index]
    hits = [int(row["arms"]["TCSQ_VALIDATED_QUOTIENT"]["cache_hits"]) for row in rows]  # type: ignore[index]
    recovered = [bool(row["arms"]["TCSQ_VALIDATED_QUOTIENT"]["recovered_oracle_ledger"]) for row in rows]  # type: ignore[index]
    return {
        "n_tasks": n_tasks,
        "n_distinct_essential_structures": n_distinct,
        "redundancy_rate": round(1.0 - n_distinct / n_tasks, 4),
        "replicates": len(rows),
        "arms": arms_summary,
        "net_advantage": net,
        "tcsq_diagnostics": {
            "mean_cache_hits": statistics.fmean([float(h) for h in hits]),
            "mean_original_problem_verification_failures": statistics.fmean([float(f) for f in failures]),
            "unverified_reuse_error_rate": (
                sum(failures) / sum(hits) if sum(hits) else 0.0
            ),
            "fraction_replicates_recovering_exact_oracle_ledger": sum(recovered) / len(recovered),
            "mean_guard_binding_fraction": statistics.fmean(
                [float(row["guard_binding_fraction"]) for row in rows]
            ),
        },
    }


def generate_results(
    *,
    seed: int = SEED,
    n_tasks: int = N_TASKS,
    replicates: int = REPLICATES,
    probe_budget: int = PROBE_BUDGET,
    distinct_fractions: tuple[float, ...] = DISTINCT_FRACTIONS,
) -> dict[str, object]:
    if seed == PAPER2_CONFIRMATORY_SEED_DO_NOT_USE:
        raise ValueError("SQ3 must not use the Paper II confirmatory seed")

    cells = []
    for fraction in distinct_fractions:
        n_distinct = max(1, int(round(fraction * n_tasks)))
        rows = [
            run_replicate(
                seed * 100_000 + n_distinct * 100 + replicate,
                n_tasks,
                n_distinct,
                probe_budget,
            )
            for replicate in range(replicates)
        ]
        cells.append(summarise_cell(rows, n_tasks, n_distinct, seed + n_distinct))

    positive = [
        cell for cell in cells
        if cell["net_advantage"]["net_vs_best_control"]["lo"] > 0  # type: ignore[index]
    ]
    crossover = min((cell["redundancy_rate"] for cell in positive), default=None)  # type: ignore[misc]

    # Top-level aggregate net advantage (hoisted for gate)
    # Honest aggregate: bootstrap on per-cell means across all redundancy rates
    cell_means = [cell["net_advantage"]["net_vs_best_control"]["mean"] for cell in cells]
    n_cells = len(cell_means)
    aggregate_boot = random.Random(seed + 42)
    boot_means = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        boot_means.append(sum(cell_means[aggregate_boot.randrange(n_cells)] for _ in range(n_cells)) / n_cells)
    boot_means.sort()
    net_advantage_aggregate = {
        "mean": statistics.fmean(cell_means),
        "lo": boot_means[int(0.025 * BOOTSTRAP_RESAMPLES)],
        "hi": boot_means[int(0.975 * BOOTSTRAP_RESAMPLES)],
        "n": n_cells,
        "note": "aggregated across redundancy-rate cells by bootstrap on cell means",
    }

    return {
        "schema_version": "rakl.tcsq.sq3.net_cost_advantage.v1",
        "status": "DEVELOPMENT_KNOWN_WORLD_NET_COST_INSTRUMENT_ONLY",
        "seed": seed,
        "paper2_confirmatory_seed_used": False,
        "n_tasks_per_replicate": n_tasks,
        "replicates_per_cell": replicates,
        "probe_budget": probe_budget,
        "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
        "claim_boundary": CLAIM_BOUNDARY,
        "grants_scientific_authority": False,
        "grants_method_promotion": False,
        "coordinate_schema": {
            "all": list(COORDINATES),
            "generator_essential": list(ESSENTIAL_COORDINATES),
            "generator_conditionally_essential": list(CONDITIONAL_COORDINATES),
            "generator_nuisance": list(NUISANCE_COORDINATES),
            "oracle_preserved": list(ORACLE_PRESERVED),
        },
        "arms": {
            "RAW_NO_QUOTIENT": "solve every task; SQ-3 gate arm RAW",
            "SURFACE_HASH_DEDUP": "cache keyed on the rendered surface string; gate arm GENERIC_COMPRESSION",
            "STRUCTURE_NO_ERASURE": "cache keyed on the canonical 12-coordinate record; gate arm STRUCTURE_NO_ERASURE",
            "TCSQ_VALIDATED_QUOTIENT": "erasure ledger discovered by a charged intervention audit and materialised through assured_materialize_validated_quotient; gate arm TCSQ",
            "ORACLE_QUOTIENT": "generator-supplied erasure ledger, zero construction cost; gate arm ORACLE_QUOTIENT",
        },
        "unfilled_gate_arms": ["INCUMBENT_RAKL"],
        "cost_model": {
            "unit": "one counted operation",
            "solve": "one op per (state, action) transition evaluated by exact BFS",
            "verify_plan": "one op per replayed action of a reused plan",
            "verify_refusal": "a refusal/no-solution answer is verified by a full re-solve, charged in full",
            "surface_key": f"{len(COORDINATES)} ops (read the whole record)",
            "structure_key": f"{2 * len(COORDINATES)} ops (read + canonically normalise)",
            "quotient_ledger": f"{len(COORDINATES)} ops per instance (classify every coordinate) + |preserved| projection ops",
            "construction": "probe_budget x (1 + n_coordinates) solves for the intervention audit",
            "maintenance": "one solve per re-probed coordinate plus |preserved| re-projection ops per cached entry",
        },
        "api_notes": [
            "every TCSQ/ORACLE instance goes through rakl.semantic_quotient_assurance."
            "assured_materialize_validated_quotient, so the coordinate partition, sufficiency-"
            "obligation, evidence and receipt-resolution contracts are enforced by the library",
            "the sufficiency obligation the harness declares is explicitly probe-sample scoped; "
            "the library cannot detect that a VALID_EXACT verdict rests on finite evidence, and "
            "in this world it does not -- the false erasures are found only by downstream "
            "original-problem verification, which is the honest limit of the contract",
            "the intervention audit never reads the generator's essential/nuisance labels; the "
            "ORACLE_QUOTIENT arm does, which is why it is an upper bound and not a method",
        ],
        "net_advantage": net_advantage_aggregate,
        "cells": cells,
        "redundancy_crossover": {
            "definition": "smallest redundancy rate whose bootstrap 95% CI for net_vs_best_control excludes zero from above",
            "redundancy_rate": crossover,
            "cells_with_negative_mean_net": [
                {
                    "redundancy_rate": cell["redundancy_rate"],
                    "net_vs_best_control_mean": cell["net_advantage"]["net_vs_best_control"]["mean"],  # type: ignore[index]
                }
                for cell in cells
                if cell["net_advantage"]["net_vs_best_control"]["mean"] < 0  # type: ignore[index,operator]
            ],
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--tasks", type=int, default=N_TASKS)
    parser.add_argument("--replicates", type=int, default=REPLICATES)
    parser.add_argument("--probe-budget", type=int, default=PROBE_BUDGET)
    args = parser.parse_args()

    result = generate_results(
        seed=args.seed,
        n_tasks=args.tasks,
        replicates=args.replicates,
        probe_budget=args.probe_budget,
    )
    RESULT_FILE.parent.mkdir(parents=True, exist_ok=True)
    RESULT_FILE.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"WROTE={RESULT_FILE.relative_to(ROOT)}")
    print(f"SEED={result['seed']}")
    for cell in result["cells"]:  # type: ignore[index]
        net = cell["net_advantage"]["net_vs_best_control"]
        diag = cell["tcsq_diagnostics"]
        print(
            f"redundancy={cell['redundancy_rate']:<6} "
            f"net_vs_best_control={net['mean']:>10.1f} "
            f"[{net['lo']:.1f},{net['hi']:.1f}] "
            f"neg_frac={net['fraction_replicates_negative']:.2f} "
            f"tcsq_success={cell['arms']['TCSQ_VALIDATED_QUOTIENT']['original_problem_success_mean']:.3f} "
            f"unverified_err={diag['unverified_reuse_error_rate']:.4f}"
        )
    print(f"REDUNDANCY_CROSSOVER={result['redundancy_crossover']['redundancy_rate']}")
    print("AUTHORITY_GRANTED=false")
    print("METHOD_PROMOTION_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
