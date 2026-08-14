#!/usr/bin/env python3
"""TCSQ SQ-3 SUCCESSOR (#536): family-certificate quotient assurance.

Historical NEGATIVE preserved unchanged at results/sq3.json
(KEEP_PROPOSAL_ONLY; net_advantage mean=-4074.34, lo=-5332.80, hi=-2878.79, n=6).
Root cause (#521): even ORACLE_QUOTIENT (perfect quotient, ZERO construction
cost) LOSES to RAW at every redundancy rate, because per-instance bookkeeping
overhead (ledger 3600 + projection 1800 + verify ~406 ~= 5406 ops / replicate)
dominates when solving is cheap (~8972 ops / 300 tasks ~= 30 ops / task).

This successor attacks the structural root cause with TWO mechanisms and a NEW
cost dimension (solve-cost scale), then sweeps redundancy x solve-cost to find
the crossover surface.

MECHANISM A -- per-family validation. The erasure ledger is a property of the
coordinate schema + QoI, not of an individual task. The historical arm
materialised a per-instance validated quotient view (12 ledger ops / task). The
successor validates the family quotient ONCE (charged intervention audit + one
assured_materialize_validated_quotient call) and each task only PROJECTS its
preserved coordinates onto the family class key (|preserved| ops). The library
contract is satisfied once per family; the per-instance ledger cost amortises
toward 0.

MECHANISM B -- certificate-based verification with retained witnesses. The
historical solve() discards the witness plan for over-budget and guard-refused
negatives, so a reused refusal can only be verified by a FULL re-solve. The
successor retains the witness plan as a compact NEGATIVE CERTIFICATE; a reused
refusal is checked by cheap replay (plan-length ops), not a full re-solve.
Genuinely-unreachable NO_SOLUTION has no compact witness and stays a full
re-solve (honest). HARD GATE: every reused certificate (positive or negative) is
replay-checked against the original problem, so an invalid / mutated certificate
is rejected -- never silently accepted.

NEW DIMENSION -- solve-cost scale. Certificate CHECKING is O(plan length)
(independent of state-space size) while SOLVING is O(states x actions) via BFS.
Scaling the state space makes solving expensive relative to certificate
checking, exposing the regime where reuse amortises.

Claim boundary: development known-world instrument only. Grants no scientific or
method-promotion authority.
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

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
RESULT_FILE = HERE / "results" / "lazy_activation.json"

SEED = 462
PAPER2_CONFIRMATORY_SEED_DO_NOT_USE = 2026081202

GUARD_THRESHOLD = 3
ACTIONS = ("a", "b", "c", "d")

N_TASKS = 240
REPLICATES = 12
PROBE_BUDGET = 8
SURFACE_DUPLICATE_FRACTION = 0.12
BOOTSTRAP_RESAMPLES = 4000
DISTINCT_FRACTIONS = (1.0, 0.75, 0.5, 0.25, 0.1, 0.04)
# solve-cost scale = number of states in the planning machine; BFS solving is
# O(states x actions) while certificate replay is O(plan length).
SOLVE_COST_SCALES = (16, 48, 128, 256)

# Lazy activation parameters
OBSERVATION_WINDOW = 48  # Number of tasks to observe before deciding
ACTIVATION_THRESHOLD = 0.35  # Trigger construction if hit rate > 35%

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
CONTEXT_HASH = "ctx:tcsq-lazy-activation-known-world-v1"

ARMS = (
    "RAW_NO_QUOTIENT",
    "SURFACE_HASH_DEDUP",
    "STRUCTURE_NO_ERASURE",
    "TCSQ_VALIDATED_QUOTIENT",
    "ORACLE_QUOTIENT",
    "FAMILY_CERTIFICATE_QUOTIENT",
    "LAZY_FAMILY_CERTIFICATE_QUOTIENT",
)
CONTROL_ARMS = ("RAW_NO_QUOTIENT", "SURFACE_HASH_DEDUP", "STRUCTURE_NO_ERASURE")

CLAIM_BOUNDARY = (
    "development known-world instrument; one synthetic bounded-planning generator, "
    "one hand-registered coordinate schema, one hand-registered intervention family, "
    "and a hand-specified operation-count cost model. It does NOT settle whether "
    "family-certificate quotients reduce cost on natural problems, with LLM solvers, "
    "on unseen coordinate schemas, or under any other distribution. Grants no "
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
# certificate: the compact reusable proof carried with every cached answer.
# --------------------------------------------------------------------------
# status tuple augmented with a witness.  A SOLVED answer carries the plan
# (positive certificate).  An over-budget / guard-refused negative carries the
# witness plan that would have solved it (negative-witness certificate: cheap to
# replay).  A genuinely-unreachable NO_SOLUTION carries no plan (must be
# re-solved to verify).  The status string is unchanged from the historical
# contract so cross-arm correctness comparison is exact.
CERT_WITNESS = "_witness"  # key on the task dict holding the retained plan


def solve(task: dict[str, object], meter: Meter, bucket: str = "solve") -> tuple[str, tuple[str, ...]]:
    """Exact bounded planner over the original problem. Cost = transitions evaluated."""
    n_states = int(task["_n_states"])  # type: ignore[arg-type]
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
        if depth[state] >= n_states:
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


def witness_plan(task: dict[str, object], meter: Meter, bucket: str = "construction") -> tuple[str, ...]:
    """Return the shortest plan regardless of budget/guard (the witness for a negative).

    Charged at the construction rate because the successor discovers the witness
    during its charged audit pass, never for free.  If the goal is genuinely
    unreachable the witness is empty.
    """
    n_states = int(task["_n_states"])  # type: ignore[arg-type]
    forbidden = set(task["forbidden_actions"])  # type: ignore[arg-type]
    trans = {(s, a): n for s, a, n in task["transitions"]}  # type: ignore[misc]
    start = task["start"]
    goal = task["goal"]
    parents: dict[int, tuple[int, str] | None] = {int(start): None}  # type: ignore[arg-type]
    depth = {int(start): 0}  # type: ignore[arg-type]
    queue: deque[int] = deque([int(start)])  # type: ignore[arg-type]
    ops = 0
    found = False
    while queue:
        state = queue.popleft()
        if state == goal:
            found = True
            break
        if depth[state] >= n_states:
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
    if not found:
        return ()
    path: list[str] = []
    cursor: int | None = int(goal)  # type: ignore[arg-type]
    while parents[cursor] is not None:
        prev, action = parents[cursor]  # type: ignore[misc]
        path.append(action)
        cursor = prev
    return tuple(reversed(path))


def has_compact_certificate(answer: tuple[str, tuple[str, ...]], witness: tuple[str, ...]) -> bool:
    """A negative answer has a compact (replayable) certificate iff a witness plan exists."""
    status, _ = answer
    if status == "SOLVED":
        return True
    return len(witness) > 0  # over-budget / guard-refused retain the witness


def check_certificate(
    task: dict[str, object],
    answer: tuple[str, tuple[str, ...]],
    witness: tuple[str, ...],
    meter: Meter,
    bucket: str = "verify",
) -> bool:
    """Verify a reused answer against the ORIGINAL problem.

    SOLVED and negative-witness answers are replay-checked (plan-length ops).
    A genuinely-unreachable NO_SOLUTION (empty witness) has no compact
    certificate and costs a full re-solve -- charged, never waived.
    """
    status, plan = answer
    if status == "SOLVED":
        return _replay(task, plan, meter, bucket, expect="SOLVED")
    # negative answer
    if len(witness) == 0:
        # genuinely unreachable: no compact witness -> full re-solve
        return solve(task, meter, bucket=bucket) == answer
    # negative-witness: replay the witness, then assert it really is a negative
    # (over budget, or guard-refused) for THIS task's budget/guard values.
    meter.charge(bucket, len(witness))
    forbidden = set(task["forbidden_actions"])  # type: ignore[arg-type]
    trans = {(s, a): n for s, a, n in task["transitions"]}  # type: ignore[misc]
    state = int(task["start"])  # type: ignore[arg-type]
    for action in witness:
        if action in forbidden or (state, action) not in trans:
            return False
        state = trans[(state, action)]
    if state != task["goal"]:
        return False
    plan_len = len(witness)
    budget = int(task["budget"])  # type: ignore[arg-type]
    if status == "NO_SOLUTION":
        # witness reaches goal but must exceed budget for the negative to hold
        return plan_len > budget
    if status == "REFUSED_OVERFLOW":
        return plan_len > GUARD_THRESHOLD and task["overflow_guard"] == "strict"
    return False


def _replay(
    task: dict[str, object],
    plan: tuple[str, ...],
    meter: Meter,
    bucket: str,
    expect: str,
) -> bool:
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


def _plan_reaches_goal(task: dict[str, object], plan: tuple[str, ...]) -> bool:
    """Independent replay: does this exact plan end at the goal?

    Used only by the adversarial audit to decide whether a mutated witness is
    genuinely broken (count as an attack) or coincidentally still valid (skip).
    Not the function under test.
    """
    forbidden = set(task["forbidden_actions"])  # type: ignore[arg-type]
    trans = {(s, a): n for s, a, n in task["transitions"]}  # type: ignore[misc]
    state = int(task["start"])  # type: ignore[arg-type]
    for action in plan:
        if action in forbidden or (state, action) not in trans:
            return False
        state = trans[(state, action)]
    return state == task["goal"]

# --------------------------------------------------------------------------
# known world (solve-cost scale = number of states)
# --------------------------------------------------------------------------
def _canon(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def make_essential_structure(rng: random.Random, n_states: int) -> dict[str, object]:
    transitions = [
        [state, action, rng.randrange(n_states)]
        for state in range(n_states)
        for action in ACTIONS
    ]
    forbidden_count = rng.choice((0, 1, 1, 2))
    forbidden = sorted(rng.sample(ACTIONS, forbidden_count))
    return {
        "transitions": transitions,
        "start": rng.randrange(n_states),
        "goal": rng.randrange(n_states),
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
    style = task["render_style"]
    pad = {"compact": "", "wide": "  ", "indent2": "  ", "indent4": "    "}[str(style)]
    order = COORDINATES if style != "wide" else tuple(reversed(COORDINATES))
    return "\n".join(f"{pad}{name}={_canon(task[name])}" for name in order)


def build_task(base: dict[str, object], nuisance: dict[str, object], index: int, n_states: int) -> dict[str, object]:
    task = dict(base)
    task.update(nuisance)
    task["_index"] = index
    task["_n_states"] = n_states
    task["_surface"] = render_surface(task)
    return task


# --------------------------------------------------------------------------
# registered interventions (only way a charged arm may learn erasure)
# --------------------------------------------------------------------------
def perturbed_value(coordinate: str, value: object, n_states: int) -> object:
    if coordinate == "transitions":
        return [[s, a, (n + 1) % n_states] for s, a, n in value]  # type: ignore[misc]
    if coordinate == "start":
        return (int(value) + 7) % n_states  # type: ignore[arg-type]
    if coordinate == "goal":
        return (int(value) + 9) % n_states  # type: ignore[arg-type]
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
    n_states = int(task["_n_states"])  # type: ignore[arg-type]
    probe[coordinate] = perturbed_value(coordinate, task[coordinate], n_states)
    return probe


def discover_erasure_ledger(
    probes: list[dict[str, object]], meter: Meter
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Charged intervention audit. Returns (preserved, erased) coordinate sets.

    A coordinate is preserved iff its registered intervention changes the exact
    answer on at least one probe task.  The audit never reads the generator's
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


# --------------------------------------------------------------------------
# family-level validated quotient (ONE library materialisation per family)
# --------------------------------------------------------------------------
def materialize_family_quotient(
    representative: dict[str, object],
    preserved: tuple[str, ...],
    erased: tuple[str, ...],
    audit_digest: str,
    label: str,
):
    """Materialise ONE validated quotient view for the coordinate-schema family.

    The library contract (assured_materialize_validated_quotient) is satisfied
    once per family; per-instance tasks only project onto the family class key.
    This is the structural difference from the historical per-instance arm.
    """
    index = representative["_index"]
    source_hash = "sha256:" + sha256(
        _canon({name: representative[name] for name in COORDINATES}).encode("utf-8")
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


def _degraded_raw(
    tasks: list[dict[str, object]],
    meter: Meter,
    label: str,
    oracle: bool,
    preserved: tuple[str, ...],
    erased: tuple[str, ...],
) -> dict[str, object]:
    """Smooth degradation: when the intervention audit discovers a VACUOUS
    quotient (no coordinate determines the answer on the probe sample -- e.g. all
    probes unreachable), the family quotient is invalid and the arm solves every
    task raw.  The failed audit is still charged; nothing is hidden.  This is the
    minimal-degrade behaviour: reuse that is not worth it falls back to solving.
    """
    answers = [solve(task, meter) for task in tasks]
    return {
        "meter": meter,
        "answers": answers,
        "extra": {
            "degraded_to_raw": True,
            "cache_hits": 0,
            "verified_hits": 0,
            "certificate_replays": 0,
            "full_resolve_verifications": 0,
            "verification_failures": 0,
            "invalid_certificate_rejections": 0,
            "initial_preserved": list(preserved),
            "final_preserved": list(preserved),
            "promoted_coordinates": [],
            "recovered_oracle_ledger": tuple(sorted(preserved)) == ORACLE_PRESERVED,
            "stage_costs": meter.snapshot(),
        },
    }

# --------------------------------------------------------------------------
# parent control arms
# --------------------------------------------------------------------------
def run_raw(tasks: list[dict[str, object]]) -> dict[str, object]:
    meter = Meter()
    answers = [solve(task, meter) for task in tasks]
    return {"meter": meter, "answers": answers, "extra": {"stage_costs": meter.snapshot()}}


def run_hash_cache(tasks: list[dict[str, object]], mode: str) -> dict[str, object]:
    """SURFACE_HASH_DEDUP / STRUCTURE_NO_ERASURE (sound: identical record => same answer)."""
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
    return {
        "meter": meter,
        "answers": answers,
        "extra": {"cache_hits": hits, "classes": len(cache), "stage_costs": meter.snapshot()},
    }


def run_tcsq_arm(
    tasks: list[dict[str, object]],
    label: str,
    *,
    oracle: bool,
    probe_budget: int,
) -> dict[str, object]:
    """Historical TCSQ_VALIDATED_QUOTIENT / ORACLE_QUOTIENT (uncharged-witness refusals).

    Preserved verbatim from the historical harness so the successor is compared
    against the SAME strong parent, with per-instance ledger + full-re-solve
    refusal verification (the structural disadvantage the successor removes).
    """
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

    if not preserved:
        # vacuous quotient -> degrade to raw solving (same contract as FCQ arm)
        return _degraded_raw(tasks, meter, label, oracle, preserved, erased)

    initial_preserved = preserved
    cache: dict[str, tuple[tuple[str, tuple[str, ...]], dict[str, object]]] = {}
    answers: list[tuple[str, tuple[str, ...]]] = []
    hits = 0
    verified_hits = 0
    verification_failures = 0
    promotions: list[str] = []

    for task in tasks:
        meter.charge("ledger", len(COORDINATES))
        meter.charge("projection", len(preserved))
        key = class_key(task, preserved)
        if key not in cache:
            answer = solve(task, meter)
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
        verification_failures += 1
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
            "verification_failures": verification_failures,
            "initial_preserved": list(initial_preserved),
            "final_preserved": list(preserved),
            "promoted_coordinates": sorted(set(promotions)),
            "recovered_oracle_ledger": tuple(sorted(initial_preserved)) == ORACLE_PRESERVED,
            "stage_costs": meter.snapshot(),
        },
    }


def verify_against_original(
    task: dict[str, object],
    answer: tuple[str, tuple[str, ...]],
    meter: Meter,
    bucket: str = "verify",
) -> bool:
    """Historical verification: plan replay for SOLVED, FULL re-solve for any refusal."""
    status, plan = answer
    if status != "SOLVED":
        return solve(task, meter, bucket=bucket) == answer
    return _replay(task, plan, meter, bucket, expect="SOLVED")


def reprobe_coordinates(
    task: dict[str, object], coordinates: tuple[str, ...], meter: Meter
) -> tuple[str, ...]:
    baseline = solve(task, meter, bucket="maintenance")
    promoted: list[str] = []
    for coordinate in coordinates:
        changed = solve(intervene(task, coordinate), meter, bucket="maintenance")
        meter.charge("maintenance", 1)
        if changed != baseline:
            promoted.append(coordinate)
    return tuple(sorted(promoted))

# --------------------------------------------------------------------------
# successor: solve-with-witness (one BFS yields answer + witness certificate)
# --------------------------------------------------------------------------
def solve_with_witness(
    task: dict[str, object], meter: Meter, bucket: str = "solve"
) -> tuple[tuple[str, tuple[str, ...]], tuple[str, ...]]:
    """One BFS yields both the exact answer and the witness plan.

    The witness is the shortest plan to goal regardless of budget/guard.  For a
    SOLVED answer the witness IS the plan.  For an over-budget / guard-refused
    negative the witness is the plan that WOULD solve it (the compact negative
    certificate).  For genuinely-unreachable NO_SOLUTION the witness is empty
    (no compact certificate; verification re-solves).  The witness is a byproduct
    of the same BFS traversal, so only the path reconstruction is charged.
    """
    n_states = int(task["_n_states"])  # type: ignore[arg-type]
    forbidden = set(task["forbidden_actions"])  # type: ignore[arg-type]
    trans = {(s, a): n for s, a, n in task["transitions"]}  # type: ignore[misc]
    start = int(task["start"])  # type: ignore[arg-type]
    goal = task["goal"]
    budget = int(task["budget"])  # type: ignore[arg-type]

    parents: dict[int, tuple[int, str] | None] = {start: None}
    depth = {start: 0}
    queue: deque[int] = deque([start])
    ops = 0
    found = None
    while queue:
        state = queue.popleft()
        if state == goal:
            found = state
            break
        if depth[state] >= n_states:
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
        return ("NO_SOLUTION", ()), ()
    # reconstruct the witness (shortest plan to goal)
    path: list[str] = []
    cursor: int | None = int(goal)  # type: ignore[arg-type]
    while parents[cursor] is not None:
        prev, action = parents[cursor]  # type: ignore[misc]
        path.append(action)
        cursor = prev
    witness = tuple(reversed(path))
    meter.charge("construction", len(witness))  # charged path reconstruction
    if len(witness) > budget:
        return ("NO_SOLUTION", ()), witness
    if len(witness) > GUARD_THRESHOLD and task["overflow_guard"] == "strict":
        return ("REFUSED_OVERFLOW", ()), witness
    return ("SOLVED", witness), witness


def run_family_certificate_arm(
    tasks: list[dict[str, object]],
    label: str,
    *,
    oracle: bool,
    probe_budget: int,
) -> dict[str, object]:
    """SUCCESSOR: FAMILY_CERTIFICATE_QUOTIENT.

    Per-family validation (one library materialisation) + certificate-based
    verification with retained witnesses.  Differs from the historical TCSQ arm
    in two structural ways: (A) no per-instance ledger -- the family quotient is
    validated once; (B) reused negatives are replayed from a compact witness
    certificate, not full-re-solved.
    """
    meter = Meter()

    # --- construction: charged intervention audit (oracle skips it) ---
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

    if not preserved:
        # vacuous quotient (probe sample answer-invariant, e.g. all probes
        # unreachable): the family quotient is invalid -> degrade to raw solving.
        return _degraded_raw(tasks, meter, label, oracle, preserved, erased)

    # --- family validation: ONE library materialisation (the structural saving) ---
    meter.charge("family_validation", len(COORDINATES) + len(preserved))
    view = materialize_family_quotient(tasks[0], preserved, erased, audit_digest, label)
    active = view.structural_coordinates  # == preserved

    initial_preserved = preserved
    cache: dict[str, tuple[tuple[str, tuple[str, ...]], tuple[str, ...], dict[str, object]]] = {}
    answers: list[tuple[str, tuple[str, ...]]] = []
    hits = 0
    verified_hits = 0
    certificate_replays = 0
    full_resolve_verifications = 0
    verification_failures = 0
    invalid_certificate_rejections = 0
    promotions: list[str] = []

    for task in tasks:
        meter.charge("projection", len(active))  # only preserved coords read
        key = class_key(task, active)
        if key not in cache:
            answer, witness = solve_with_witness(task, meter)
            cache[key] = (answer, witness, task)
            answers.append(answer)
            continue

        hits += 1
        candidate, witness, representative = cache[key]
        # certificate-based verification against the ORIGINAL problem
        if has_compact_certificate(candidate, witness):
            certificate_replays += 1
        else:
            full_resolve_verifications += 1
        ok = check_certificate(task, candidate, witness, meter)
        if ok:
            verified_hits += 1
            answers.append(candidate)
            continue

        # false erasure: invalid certificate -> never accepted (hard gate)
        invalid_certificate_rejections += 1
        verification_failures += 1
        differing = tuple(
            sorted(name for name in erased if _canon(task[name]) != _canon(representative[name]))
        )
        promoted = reprobe_coordinates(task, differing, meter)
        if promoted:
            preserved = tuple(sorted(set(preserved) | set(promoted)))
            erased = tuple(sorted(set(COORDINATES) - set(preserved)))
            active = preserved
            promotions.extend(promoted)
            rekeyed: dict[str, tuple[tuple[str, tuple[str, ...]], tuple[str, ...], dict[str, object]]] = {}
            for c_ans, c_wit, c_task in cache.values():
                meter.charge("maintenance", len(preserved))
                rekeyed[class_key(c_task, preserved)] = (c_ans, c_wit, c_task)
            cache = rekeyed
        answer, witness = solve_with_witness(task, meter, bucket="repair")
        cache[class_key(task, preserved)] = (answer, witness, task)
        answers.append(answer)

    return {
        "meter": meter,
        "answers": answers,
        "extra": {
            "cache_hits": hits,
            "verified_hits": verified_hits,
            "certificate_replays": certificate_replays,
            "full_resolve_verifications": full_resolve_verifications,
            "verification_failures": verification_failures,
            "invalid_certificate_rejections": invalid_certificate_rejections,
            "initial_preserved": list(initial_preserved),
            "final_preserved": list(preserved),
            "promoted_coordinates": sorted(set(promotions)),
            "recovered_oracle_ledger": tuple(sorted(initial_preserved)) == ORACLE_PRESERVED,
            "stage_costs": meter.snapshot(),
        },
    }


# --------------------------------------------------------------------------
# lazy family certificate quotient: adaptive construction based on observed hit rate
# --------------------------------------------------------------------------
def run_lazy_family_arm(
    tasks: list[dict[str, object]],
    label: str,
    *,
    probe_budget: int,
) -> dict[str, object]:
    """LAZY_FAMILY_CERTIFICATE_QUOTIENT: observe first N tasks, activate only if hit rate > threshold.

    Phase 1 (observation): Observe first OBSERVATION_WINDOW tasks with simple structure-keyed
    caching (no construction cost). Track cache hits to estimate redundancy.

    Phase 2 (decision): If observed hit rate > ACTIVATION_THRESHOLD, trigger full
    FAMILY_CERTIFICATE_QUOTIENT (intervention audit + family validation + certificates).
    Otherwise, continue with raw solving for all remaining tasks (no overhead paid).

    Honest cost accounting: observation period caching, threshold check, and any
    construction are all charged to meter.
    """
    meter = Meter()
    all_answers: list[tuple[str, tuple[str, ...]]] = []
    
    # --- Phase 1: observation window with simple structure caching ---
    obs_cache: dict[str, tuple[str, tuple[str, ...]]] = {}
    obs_hits = 0
    window = min(OBSERVATION_WINDOW, len(tasks))
    
    for idx in range(window):
        task = tasks[idx]
        # Charge for forming the structure key
        meter.charge("key", 2 * len(COORDINATES))
        key = class_key(task, COORDINATES)
        
        if key in obs_cache:
            obs_hits += 1
            all_answers.append(obs_cache[key])
        else:
            answer = solve(task, meter)
            obs_cache[key] = answer
            all_answers.append(answer)
    
    # --- Phase 2: decision ---
    # Charge for the threshold check
    meter.charge("threshold_check", 1)
    observed_hit_rate = obs_hits / window if window > 0 else 0.0
    
    if observed_hit_rate > ACTIVATION_THRESHOLD:
        # ACTIVATE: run full family certificate quotient on remaining tasks
        # First, run the intervention audit and family validation
        probes = tasks[:probe_budget]
        preserved, erased = discover_erasure_ledger(probes, meter)
        audit_digest = "sha256:" + sha256(
            _canon({"preserved": list(preserved), "probes": probe_budget}).encode("utf-8")
        ).hexdigest()
        
        if not preserved:
            # Vacuous quotient -> degrade to raw for remaining tasks
            for idx in range(window, len(tasks)):
                answer = solve(tasks[idx], meter)
                all_answers.append(answer)
            return {
                "meter": meter,
                "answers": all_answers,
                "extra": {
                    "degraded_to_raw": True,
                    "activated": False,
                    "observed_hit_rate": observed_hit_rate,
                    "observation_window_hits": obs_hits,
                    "cache_hits": obs_hits,
                    "verified_hits": obs_hits,  # All obs hits were verified solves
                    "stage_costs": meter.snapshot(),
                },
            }
        
        # Family validation: ONE library materialisation
        meter.charge("family_validation", len(COORDINATES) + len(preserved))
        view = materialize_family_quotient(tasks[window], preserved, erased, audit_digest, label)
        active = view.structural_coordinates
        
        # Process remaining tasks with certificate-based caching
        cache: dict[str, tuple[tuple[str, tuple[str, ...]], tuple[str, ...], dict[str, object]]] = {}
        # Seed cache with observation window tasks that were solved
        for idx in range(window):
            task = tasks[idx]
            key = class_key(task, active)
            if key not in cache:
                # Re-solve with witness for cache seeding
                answer, witness = solve_with_witness(task, meter, bucket="construction")
                cache[key] = (answer, witness, task)
        
        hits = obs_hits
        verified_hits = obs_hits  # All observation hits were verified
        certificate_replays = 0
        full_resolve_verifications = 0
        verification_failures = 0
        invalid_certificate_rejections = 0
        promotions: list[str] = []
        
        for idx in range(window, len(tasks)):
            task = tasks[idx]
            meter.charge("projection", len(active))
            key = class_key(task, active)
            if key not in cache:
                answer, witness = solve_with_witness(task, meter)
                cache[key] = (answer, witness, task)
                all_answers.append(answer)
                continue
            
            hits += 1
            candidate, witness, representative = cache[key]
            if has_compact_certificate(candidate, witness):
                certificate_replays += 1
            else:
                full_resolve_verifications += 1
            ok = check_certificate(task, candidate, witness, meter)
            if ok:
                verified_hits += 1
                all_answers.append(candidate)
                continue
            
            verification_failures += 1
            invalid_certificate_rejections += 1
            differing = tuple(
                sorted(name for name in erased if _canon(task[name]) != _canon(representative[name]))
            )
            promoted = reprobe_coordinates(task, differing, meter)
            if promoted:
                preserved = tuple(sorted(set(preserved) | set(promoted)))
                erased = tuple(sorted(set(COORDINATES) - set(preserved)))
                active = preserved
                promotions.extend(promoted)
                rekeyed: dict[str, tuple[tuple[str, tuple[str, ...]], tuple[str, ...], dict[str, object]]] = {}
                for c_ans, c_wit, c_task in cache.values():
                    meter.charge("maintenance", len(preserved))
                    rekeyed[class_key(c_task, preserved)] = (c_ans, c_wit, c_task)
                cache = rekeyed
            answer, witness = solve_with_witness(task, meter, bucket="repair")
            cache[class_key(task, preserved)] = (answer, witness, task)
            all_answers.append(answer)
        
        return {
            "meter": meter,
            "answers": all_answers,
            "extra": {
                "activated": True,
                "observed_hit_rate": observed_hit_rate,
                "observation_window_hits": obs_hits,
                "cache_hits": hits,
                "verified_hits": verified_hits,
                "certificate_replays": certificate_replays,
                "full_resolve_verifications": full_resolve_verifications,
                "verification_failures": verification_failures,
                "invalid_certificate_rejections": invalid_certificate_rejections,
                "initial_preserved": list(preserved),
                "final_preserved": list(preserved),
                "promoted_coordinates": sorted(set(promotions)),
                "stage_costs": meter.snapshot(),
            },
        }
    else:
        # DO NOT ACTIVATE: continue with raw solving for remaining tasks
        for idx in range(window, len(tasks)):
            answer = solve(tasks[idx], meter)
            all_answers.append(answer)
        
        return {
            "meter": meter,
            "answers": all_answers,
            "extra": {
                "activated": False,
                "observed_hit_rate": observed_hit_rate,
                "observation_window_hits": obs_hits,
                "cache_hits": obs_hits,
                "verified_hits": obs_hits,
                "stage_costs": meter.snapshot(),
            },
        }

# --------------------------------------------------------------------------
# stream construction and replicate execution
# --------------------------------------------------------------------------
def build_stream(rng: random.Random, n_tasks: int, n_distinct: int, n_states: int) -> list[dict[str, object]]:
    bases = [make_essential_structure(rng, n_states) for _ in range(n_distinct)]
    assignment = list(range(n_distinct)) + [
        rng.randrange(n_distinct) for _ in range(n_tasks - n_distinct)
    ]
    rng.shuffle(assignment)
    tasks = [
        build_task(bases[base_index], make_nuisance(rng), index, n_states)
        for index, base_index in enumerate(assignment)
    ]
    duplicate_slots = sorted(
        rng.sample(range(1, n_tasks), int(round(SURFACE_DUPLICATE_FRACTION * n_tasks)))
    )
    for slot in duplicate_slots:
        donor = dict(tasks[rng.randrange(slot)])
        donor["_index"] = slot
        tasks[slot] = donor
    return tasks


def run_replicate(seed: int, n_tasks: int, n_distinct: int, n_states: int, probe_budget: int) -> dict[str, object]:
    rng = random.Random(seed)
    tasks = build_stream(rng, n_tasks, n_distinct, n_states)
    gold_meter = Meter()
    gold = [solve(task, gold_meter) for task in tasks]

    results = {
        "RAW_NO_QUOTIENT": run_raw(tasks),
        "SURFACE_HASH_DEDUP": run_hash_cache(tasks, "surface"),
        "STRUCTURE_NO_ERASURE": run_hash_cache(tasks, "structure"),
        "TCSQ_VALIDATED_QUOTIENT": run_tcsq_arm(
            tasks, f"sq3s-{seed}-tcsq", oracle=False, probe_budget=probe_budget
        ),
        "ORACLE_QUOTIENT": run_tcsq_arm(
            tasks, f"sq3s-{seed}-oracle", oracle=True, probe_budget=probe_budget
        ),
        "FAMILY_CERTIFICATE_QUOTIENT": run_family_certificate_arm(
            tasks, f"sq3s-{seed}-fcq", oracle=False, probe_budget=probe_budget
        ),
        "LAZY_FAMILY_CERTIFICATE_QUOTIENT": run_lazy_family_arm(
            tasks, f"lazy-{seed}-lfcq", probe_budget=probe_budget
        ),
    }

    row: dict[str, object] = {
        "seed": seed,
        "n_tasks": n_tasks,
        "n_distinct": n_distinct,
        "n_states": n_states,
        "gold_status_counts": {
            status: sum(1 for answer in gold if answer[0] == status)
            for status in ("SOLVED", "NO_SOLUTION", "REFUSED_OVERFLOW")
        },
        "arms": {},
    }
    for arm, payload in results.items():
        meter: Meter = payload["meter"]  # type: ignore[assignment]
        answers = payload["answers"]
        correct = sum(1 for produced, truth in zip(answers, gold) if produced == truth)
        row["arms"][arm] = {  # type: ignore[index]
            "total_cost": meter.total,
            "stage_costs": meter.snapshot(),
            "original_problem_success": correct / n_tasks,
            **payload["extra"],  # type: ignore[dict-item]
        }
    return row


# --------------------------------------------------------------------------
# statistics
# --------------------------------------------------------------------------
def bootstrap_ci(values: list[float], rng: random.Random, resamples: int) -> dict[str, float]:
    n = len(values)
    if n == 0:
        return {"mean": 0.0, "lo": 0.0, "hi": 0.0, "n": 0}
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


SUCCESSOR = "LAZY_FAMILY_CERTIFICATE_QUOTIENT"


def summarise_cell(
    rows: list[dict[str, object]], n_states: int, n_distinct: int, boot_seed: int
) -> dict[str, object]:
    n_tasks = int(rows[0]["n_tasks"])
    arms_summary: dict[str, object] = {}
    for arm in ARMS:
        costs = [float(row["arms"][arm]["total_cost"]) for row in rows]  # type: ignore[index]
        accs = [float(row["arms"][arm]["original_problem_success"]) for row in rows]  # type: ignore[index]
        entry: dict[str, object] = {
            "total_cost": bootstrap_ci(costs, random.Random(boot_seed + hash(arm) % 9973), BOOTSTRAP_RESAMPLES),
            "original_problem_success_mean": statistics.fmean(accs),
            "original_problem_success_min": min(accs),
            "stage_costs": rows[0]["arms"][arm]["stage_costs"],  # type: ignore[index]
        }
        arms_summary[arm] = entry

    succ_costs = [float(row["arms"][SUCCESSOR]["total_cost"]) for row in rows]  # type: ignore[index]
    net: dict[str, object] = {}
    for control in CONTROL_ARMS + ("TCSQ_VALIDATED_QUOTIENT", "ORACLE_QUOTIENT"):
        control_costs = [float(row["arms"][control]["total_cost"]) for row in rows]  # type: ignore[index]
        deltas = [c - s for c, s in zip(control_costs, succ_costs)]
        net[f"net_vs_{control}"] = {
            **bootstrap_ci(deltas, random.Random(boot_seed + 17), BOOTSTRAP_RESAMPLES),
            "fraction_replicates_positive": sum(1 for d in deltas if d > 0) / len(deltas),
        }
    best_control = [
        min(float(row["arms"][control]["total_cost"]) for control in CONTROL_ARMS)  # type: ignore[index]
        for row in rows
    ]
    best_deltas = [c - s for c, s in zip(best_control, succ_costs)]
    net["net_vs_best_control"] = {
        **bootstrap_ci(best_deltas, random.Random(boot_seed + 31), BOOTSTRAP_RESAMPLES),
        "fraction_replicates_positive": sum(1 for d in best_deltas if d > 0) / len(best_deltas),
        "relative_to_best_control": statistics.fmean(best_deltas) / statistics.fmean(best_control),
    }

    # Handle optional fields for lazy arm (may not have certificate fields if not activated)
    hits = [int(row["arms"][SUCCESSOR].get("cache_hits", 0)) for row in rows]  # type: ignore[index]
    cert_replays = [int(row["arms"][SUCCESSOR].get("certificate_replays", 0)) for row in rows]  # type: ignore[index]
    full_resolves = [int(row["arms"][SUCCESSOR].get("full_resolve_verifications", 0)) for row in rows]  # type: ignore[index]
    invalid_rej = [int(row["arms"][SUCCESSOR].get("invalid_certificate_rejections", 0)) for row in rows]  # type: ignore[index]

    return {
        "solve_cost_scale": n_states,
        "n_tasks": n_tasks,
        "n_distinct_essential_structures": n_distinct,
        "redundancy_rate": round(1.0 - n_distinct / n_tasks, 4),
        "replicates": len(rows),
        "arms": arms_summary,
        "net_advantage": net,
        "successor_diagnostics": {
            "mean_cache_hits": statistics.fmean([float(h) for h in hits]),
            "mean_certificate_replays": statistics.fmean([float(c) for c in cert_replays]),
            "mean_full_resolve_verifications": statistics.fmean([float(f) for f in full_resolves]),
            "mean_invalid_certificate_rejections": statistics.fmean([float(i) for i in invalid_rej]),
            "original_problem_success_mean": arms_summary[SUCCESSOR]["original_problem_success_mean"],  # type: ignore[index]
        },
    }

# --------------------------------------------------------------------------
# regime analysis (crossover surface over solve_cost_scale x redundancy_rate)
# --------------------------------------------------------------------------
def build_regime_analysis(cells: list[dict[str, object]], boot_seed: int) -> dict[str, object]:
    """Partition cells into positive / negative subsets by their replicate-level
    net_vs_best_control CI, then bootstrap each subset over its cell means.

    A cell is positive iff its CI excludes zero from above (lo > 0); negative iff
    it excludes zero from below (hi < 0). Ambiguous cells (CI straddles zero) are
    excluded from both subsets -- they cannot anchor a crossover claim.
    """
    rng_pos = random.Random(boot_seed + 101)
    rng_neg = random.Random(boot_seed + 202)
    pos_cells: list[dict[str, object]] = []
    neg_cells: list[dict[str, object]] = []
    pos_means: list[float] = []
    neg_means: list[float] = []
    for cell in cells:
        net = cell["net_advantage"]["net_vs_best_control"]  # type: ignore[index]
        point = {
            "solve_cost_scale": cell["solve_cost_scale"],
            "redundancy_rate": cell["redundancy_rate"],
        }
        if net["lo"] > 0:  # type: ignore[index]
            pos_cells.append(point)
            pos_means.append(float(net["mean"]))  # type: ignore[index]
        elif net["hi"] < 0:  # type: ignore[index]
            neg_cells.append(point)
            neg_means.append(float(net["mean"]))  # type: ignore[index]

    all_means = [float(cell["net_advantage"]["net_vs_best_control"]["mean"]) for cell in cells]  # type: ignore[index]
    all_ci = bootstrap_ci(all_means, random.Random(boot_seed + 303), BOOTSTRAP_RESAMPLES)

    def subset_record(cells_l: list[dict[str, object]], means: list[float], rng: random.Random, desc: str) -> dict[str, object]:
        ci = bootstrap_ci(means, rng, BOOTSTRAP_RESAMPLES) if means else {"mean": 0.0, "lo": 0.0, "hi": 0.0, "n": 0}
        return {
            "description": desc,
            "cells": sorted(cells_l, key=lambda c: (c["solve_cost_scale"], c["redundancy_rate"])),  # type: ignore[arg-type]
            "n": len(means),
            "net_saving_mean": ci["mean"],
            "net_saving_ci95": [ci["lo"], ci["hi"]],
        }

    return {
        "all_cells": {
            "n": len(all_means),
            "net_saving_mean": all_ci["mean"],
            "net_saving_ci95": [all_ci["lo"], all_ci["hi"]],
        },
        "positive_subset": subset_record(
            pos_cells, pos_means, rng_pos,
            "solve_cost_scale x redundancy cells whose successor net CI excludes zero from above"),
        "negative_subset": subset_record(
            neg_cells, neg_means, rng_neg,
            "solve_cost_scale x redundancy cells whose successor net CI excludes zero from below"),
    }


# --------------------------------------------------------------------------
# adversarial invalid-certificate hard gate (never accept an invalid cert)
# --------------------------------------------------------------------------
def adversarial_invalid_certificate_audit(seed: int = 20260813) -> dict[str, object]:
    """The hard gate: every reused certificate is replay-checked against the
    original problem.  This audit deliberately manufactures INVALID certificates
    and confirms each one is REJECTED.  Three attack classes:

      1. mutated witness plan (one action flipped) -- replay must fail
      2. wrong-status certificate (SOLVED cert offered for a refused task)
      3. false-erasure collision (two tasks share the preserved key but differ
         on an erased essential coordinate) -- the reused answer must be rejected
         and the task re-solved, never silently accepted
    """
    rng = random.Random(seed)
    n_states = 32
    n_attempts = 0
    n_rejections = 0
    failures: list[str] = []

    for trial in range(40):
        base = make_essential_structure(rng, n_states)
        task = build_task(base, make_nuisance(rng), trial, n_states)
        meter = Meter()
        answer, witness = solve_with_witness(task, meter)

        # attack 1: mutate the witness plan if it has length >= 2
        if len(witness) >= 2:
            mutated = list(witness)
            i = rng.randrange(len(mutated))
            mutated[i] = next(a for a in ACTIONS if a != mutated[i])
            mutated_witness = tuple(mutated)
            # a mutation that still reaches the goal is a different VALID plan,
            # not an invalid certificate -- only count genuinely-broken mutations
            if _plan_reaches_goal(task, mutated_witness):
                continue
            n_attempts += 1
            bad_answer = (answer[0], mutated_witness if answer[0] == "SOLVED" else ())
            if not check_certificate(task, bad_answer, mutated_witness, Meter()):
                n_rejections += 1
            else:
                failures.append(f"trial{trial}:attack1:mutated_witness_accepted")

        # attack 2: wrong-status certificate
        n_attempts += 1
        if answer[0] == "SOLVED":
            wrong = ("REFUSED_OVERFLOW", ())
            ok = check_certificate(task, wrong, witness, Meter())
        else:
            wrong = ("SOLVED", witness)
            ok = check_certificate(task, wrong, witness, Meter())
        if not ok:
            n_rejections += 1
        else:
            failures.append(f"trial{trial}:attack2:wrong_status_accepted")

        # attack 3: false-erasure collision -- a second task with same preserved
        # key but a different goal (erased coordinate changed)
        n_attempts += 1
        sibling = dict(task)
        sibling["goal"] = (int(task["goal"]) + 1) % n_states
        sibling["_index"] = trial + 1000
        sib_answer = solve(sibling, Meter())
        ok = check_certificate(sibling, answer, witness, Meter())
        # the sibling genuinely differs on an erased coordinate, so reusing the
        # original answer is correct ONLY if it happens to also be valid for the
        # sibling; otherwise it MUST be rejected.
        if sib_answer == answer:
            # legitimately the same answer -- not a valid adversarial attempt
            n_attempts -= 1
        elif not ok:
            n_rejections += 1
        else:
            failures.append(f"trial{trial}:attack3:false_erasue_collision_accepted")

    return {
        "hard_gate": "never_accept_an_invalid_reused_certificate",
        "attempts": n_attempts,
        "rejections": n_rejections,
        "rejection_rate": n_rejections / n_attempts if n_attempts else 1.0,
        "all_invalid_certificates_rejected": n_rejections == n_attempts,
        "failure_detail": failures,
    }


# --------------------------------------------------------------------------
# top-level result assembly
# --------------------------------------------------------------------------
def generate_results(
    *,
    seed: int = SEED,
    n_tasks: int = N_TASKS,
    replicates: int = REPLICATES,
    probe_budget: int = PROBE_BUDGET,
    distinct_fractions: tuple[float, ...] = DISTINCT_FRACTIONS,
    solve_cost_scales: tuple[int, ...] = SOLVE_COST_SCALES,
) -> dict[str, object]:
    if seed == PAPER2_CONFIRMATORY_SEED_DO_NOT_USE:
        raise ValueError("SQ3 successor must not use the Paper II confirmatory seed")

    cells: list[dict[str, object]] = []
    for n_states in solve_cost_scales:
        for fraction in distinct_fractions:
            n_distinct = max(1, int(round(fraction * n_tasks)))
            rows = [
                run_replicate(
                    seed * 100_000 + n_states * 1_000 + n_distinct * 10 + replicate,
                    n_tasks,
                    n_distinct,
                    n_states,
                    probe_budget,
                )
                for replicate in range(replicates)
            ]
            cells.append(summarise_cell(rows, n_states, n_distinct, seed + n_states + n_distinct))

    regime = build_regime_analysis(cells, seed + 900)

    # aggregate net advantage across all cells (bootstrap on cell means)
    cell_means = [float(cell["net_advantage"]["net_vs_best_control"]["mean"]) for cell in cells]
    n_cells = len(cell_means)
    agg_rng = random.Random(seed + 42)
    boot_means = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        boot_means.append(sum(cell_means[agg_rng.randrange(n_cells)] for _ in range(n_cells)) / n_cells)
    boot_means.sort()
    net_advantage_aggregate = {
        "mean": statistics.fmean(cell_means),
        "lo": boot_means[int(0.025 * BOOTSTRAP_RESAMPLES)],
        "hi": boot_means[int(0.975 * BOOTSTRAP_RESAMPLES)],
        "n": n_cells,
        "note": "aggregated across solve_cost_scale x redundancy cells by bootstrap on cell means",
    }

    adv = adversarial_invalid_certificate_audit(seed + 777)

    return {
        "schema_version": "rakl.tcsq.lazy_activation.v1",
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
        "historical_parent": "research/tcsq_sq3_v1/results/sq3_successor.json (PROMOTE_CONDITIONALLY, regime-conditional positive at high redundancy only)",
        "mechanisms": {
            "A_lazy_observation": "observe first N tasks with simple structure-keyed caching; no construction cost during observation",
            "B_adaptive_activation": "trigger full intervention audit + family validation + certificates only if observed hit rate exceeds threshold (35%)",
            "C_certificate_reuse": "when activated, retained witness plans enable cheap replay (plan-length ops) instead of full re-solve",
            "target_regime": "low-redundancy regimes where fixed construction cost would dominate benefit; lazy activation avoids paying cost when reuse is unlikely",
        },
        "coordinate_schema": {
            "all": list(COORDINATES),
            "generator_essential": list(ESSENTIAL_COORDINATES),
            "generator_conditionally_essential": list(CONDITIONAL_COORDINATES),
            "generator_nuisance": list(NUISANCE_COORDINATES),
            "oracle_preserved": list(ORACLE_PRESERVED),
        },
        "arms": {
            "RAW_NO_QUOTIENT": "solve every task (parent control)",
            "SURFACE_HASH_DEDUP": "cache keyed on rendered surface string (parent control)",
            "STRUCTURE_NO_ERASURE": "cache keyed on canonical 12-coordinate record (parent control)",
            "TCSQ_VALIDATED_QUOTIENT": "historical per-instance quotient + full-re-solve refusals (strongest classical parent)",
            "ORACLE_QUOTIENT": "generator-supplied erasure, zero construction cost (upper bound parent)",
            "FAMILY_CERTIFICATE_QUOTIENT": "sq3_successor: per-family validation + certificate verification with retained witnesses",
            "LAZY_FAMILY_CERTIFICATE_QUOTIENT": "SUCCESSOR: adaptive construction; observe hit rate, activate only if threshold exceeded",
        },
        "unfilled_gate_arms": ["INCUMBENT_RAKL"],
        "cost_model": {
            "unit": "one counted operation",
            "solve": "one op per (state, action) transition evaluated by exact BFS",
            "construction": "intervention audit + witness path reconstruction (charged)",
            "family_validation": "one library materialisation per family (ledger+projection, charged once)",
            "projection": "|preserved| ops per task to form the class key",
            "verify_replay": "one op per replayed action of a reused certificate",
            "verify_refusal_unreachable": "a genuinely-unreachable negative has no compact witness -> full re-solve, charged",
            "maintenance": "one solve per re-probed coordinate plus |preserved| re-projection ops per cached entry",
        },
        "net_advantage": net_advantage_aggregate,
        "regime_analysis": regime,
        "adversarial_invalid_certificate_gate": adv,
        "cells": cells,
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
    agg = result["net_advantage"]
    print(f"NET_VS_BEST_CONTROL mean={agg['mean']:.1f} [{agg['lo']:.1f},{agg['hi']:.1f}] n={agg['n']}")
    reg = result["regime_analysis"]
    pos = reg["positive_subset"]
    neg = reg["negative_subset"]
    print(f"POSITIVE_SUBSET n={pos['n']} mean={pos['net_saving_mean']:.1f} ci=[{pos['net_saving_ci95'][0]:.1f},{pos['net_saving_ci95'][1]:.1f}]")
    print(f"NEGATIVE_SUBSET n={neg['n']} mean={neg['net_saving_mean']:.1f} ci=[{neg['net_saving_ci95'][0]:.1f},{neg['net_saving_ci95'][1]:.1f}]")
    adv = result["adversarial_invalid_certificate_gate"]
    print(f"INVALID_CERT_GATE rejected={adv['rejections']}/{adv['attempts']} all_rejected={adv['all_invalid_certificates_rejected']}")
    for cell in result["cells"]:  # type: ignore[index]
        net = cell["net_advantage"]["net_vs_best_control"]
        print(
            f"scale={cell['solve_cost_scale']:<4} redundancy={cell['redundancy_rate']:<6} "
            f"net={net['mean']:>10.1f} [{net['lo']:.1f},{net['hi']:.1f}] "
            f"hits={cell['successor_diagnostics']['mean_cache_hits']:.0f} "
            f"cert_replays={cell['successor_diagnostics']['mean_certificate_replays']:.0f}"
        )
    print("AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
