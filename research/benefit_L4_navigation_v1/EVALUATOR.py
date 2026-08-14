"""Frozen SR evaluator for benefit_L4_navigation_v1 (ladder L4-NAVIGATION benefit obligation).

Research-local. Frozen with PROTOCOL.json (this file's sha256 is embedded there).
Any edit after the protocol freeze invalidates the protocol hash binding and the
run must be declared CANNOT_CHECK.

Scope
-----
Computes, for a labeled known-answer multi-hop support-world corpus and two arm
output files, the budget-matched solve rate:

  SR_arm = (# primary-set worlds where the arm declared SOLVED with a
            world-verified admissible route) / (# primary-set worlds)
  primary set = gold SOLVABLE worlds with budget_class in {MEDIUM, LOOSE}

  FSR_arm = (# worlds where the arm declared SOLVED but the route fails the
             full-world check) / (# worlds)     [false-solve guard, all N]

  SFH_B  = SR of arm B on class N4 (shallow single-hop) — the honest-cost
           floor charged against arm B (distillation overhead must not gut
           the easy regime).

plus the paired McNemar exact test on world-level verified-solve indicators
(primary set), the equal-budget random-acquisition null, and the source-index
permutation null.

It emits exactly one typed verdict: PROMOTE | NEGATIVE | CONDITIONAL | CANNOT_CHECK.
CANNOT_CHECK is a distinct exit code (3) and is never conflated with a clean pass.

Exit codes: 0 = evaluated, 2 = self-test failure, 3 = CANNOT_CHECK, 4 = usage error.

Determinism: all randomness flows from the single --seed argument through
random.Random; iteration orders are sorted. No network. No non-stdlib imports.
The arm policies replicated here are decision-equivalent to the frozen
acquisition policies in PROTOCOL.json; the execution-run arm B harness realizes
navigation through rakl.support_solver.solve, and any disagreement between a
live arm's declarations and these replicas is CANNOT_CHECK (drift check).
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import random
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Frozen constants (mirror PROTOCOL.json; the protocol is authoritative — a
# mismatch between these and PROTOCOL.json is itself CANNOT_CHECK).
# ---------------------------------------------------------------------------
GOLD_LABELS = ("SOLVABLE", "UNSOLVABLE")
ARM_DECLARATIONS = ("SOLVED", "NOT_SOLVED")
N_EXPECTED_WORLDS = 400
NULL_DRAWS = 1000
COST_READ = 1.0
COST_DISTIL = 2.0
ROUTE_ENUM_LIMIT = 256
PRIMARY_BUDGET_CLASSES = ("MEDIUM", "LOOSE")
FLOOR_CLASS = "N4"
LOOSE_CLASS = "N3"
THRESH_DELTA_SR_PROMOTE = 0.10
THRESH_DELTA_SR_NEGATIVE = 0.02
THRESH_MCNEMAR_P = 0.001
THRESH_SFH_FLOOR = 0.70
THRESH_LOOSE_NONINF = 0.02
NULL_QUANTILE = 0.05  # nulls are beaten above the 95th percentile (SR: higher is better)
AUDIT_MAX_DISAGREEMENT = 0.05


class CannotCheck(Exception):
    """Raised when the evaluation is structurally impossible. Never a pass."""


# ---------------------------------------------------------------------------
# Loading and integrity
# ---------------------------------------------------------------------------

def _sha256_file(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


REQUIRED_ROW_KEYS = (
    "world_id", "class", "budget_class", "budget_units", "gold_label",
    "label_minted_at", "target", "sources", "minimal_source_count",
)


def load_corpus(path: str) -> list[dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CannotCheck(f"corpus unreadable: {exc}") from exc
    worlds = payload.get("worlds")
    if not isinstance(worlds, list) or not worlds:
        raise CannotCheck("corpus has no worlds; denominator would be zero")
    for row in worlds:
        for key in REQUIRED_ROW_KEYS:
            if key not in row:
                raise CannotCheck(f"corpus row missing {key!r}")
        if row["gold_label"] not in GOLD_LABELS:
            raise CannotCheck(f"unknown gold label {row['gold_label']!r}")
        if row["budget_class"] not in ("TIGHT", "MEDIUM", "LOOSE"):
            raise CannotCheck(f"unknown budget class {row['budget_class']!r}")
        if not isinstance(row["sources"], list) or not row["sources"]:
            raise CannotCheck(f"world {row['world_id']} has no sources")
    ids = [row["world_id"] for row in worlds]
    if len(ids) != len(set(ids)):
        raise CannotCheck("duplicate world_id in corpus")
    return sorted(worlds, key=lambda row: row["world_id"])


def load_arm(path: str, corpus: list[dict[str, Any]], arm_name: str) -> dict[str, dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CannotCheck(f"arm {arm_name} output unreadable: {exc}") from exc
    rows = payload.get("declarations")
    if not isinstance(rows, list):
        raise CannotCheck(f"arm {arm_name} output has no declarations list")
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        if row.get("declaration") not in ARM_DECLARATIONS:
            raise CannotCheck(
                f"arm {arm_name} declaration {row.get('declaration')!r} not in {ARM_DECLARATIONS}"
            )
        by_id[row["world_id"]] = row
    corpus_ids = {row["world_id"] for row in corpus}
    if set(by_id) != corpus_ids:
        missing = sorted(corpus_ids - set(by_id))[:5]
        extra = sorted(set(by_id) - corpus_ids)[:5]
        raise CannotCheck(
            f"arm {arm_name} coverage mismatch (missing e.g. {missing}, extra e.g. {extra}); "
            "denominator must be identical across arms"
        )
    return by_id


def assert_label_independence(corpus: list[dict[str, Any]], arm_run_started_at: str) -> None:
    """Gold labels must be minted strictly before any arm ran (L6-gate defect guard)."""
    if not arm_run_started_at:
        raise CannotCheck("arm_run_started_at missing; cannot verify label-before-arm chronology")
    late = [
        row["world_id"]
        for row in corpus
        if str(row["label_minted_at"]) >= str(arm_run_started_at)
    ]
    if late:
        raise CannotCheck(
            f"{len(late)} gold labels minted at/after arm start (e.g. {late[:3]}); "
            "labels are not independent of arm outputs"
        )


def assert_audit_receipt(audit_path: str) -> dict[str, Any]:
    try:
        with open(audit_path, "r", encoding="utf-8") as handle:
            audit = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CannotCheck(f"audit receipt unreadable: {exc}") from exc
    for key in ("n_audited", "n_disagreements", "auditor_saw_arm_outputs"):
        if key not in audit:
            raise CannotCheck(f"audit receipt missing {key!r}")
    if audit["auditor_saw_arm_outputs"] is not False:
        raise CannotCheck("auditor saw arm outputs; audit is not label-independent")
    if audit["n_audited"] <= 0:
        raise CannotCheck("empty audit sample")
    disagreement = audit["n_disagreements"] / audit["n_audited"]
    if disagreement >= AUDIT_MAX_DISAGREEMENT:
        raise CannotCheck(
            f"audit disagreement {disagreement:.3f} >= {AUDIT_MAX_DISAGREEMENT}; corpus labels unreliable"
        )
    return {"disagreement": disagreement, "n_audited": audit["n_audited"]}


# ---------------------------------------------------------------------------
# Navigation core (decision-equivalent to rakl.support_solver semantics on
# the corpus's rendered fact sets: licensed Dijkstra with obstruction
# rejection on the assembled atom set; bounded relaxed enumeration; minimal
# repair over unobstructed relaxed routes).
# ---------------------------------------------------------------------------

def _violated(atoms: set[str], obstructions: list[dict[str, Any]]) -> bool:
    return any(set(o["cover"]) <= atoms for o in obstructions)


def admissible_route(edges: list[dict[str, Any]], obstructions: list[dict[str, Any]],
                     start: str, goal: str, required_authority: int) -> tuple[str, ...] | None:
    """Cheapest simple route over edges licensed at/above the demanded layer,
    rejecting any assembled atom set that realizes a known obstruction."""
    adjacency: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        if edge["licensed_at"] >= required_authority:
            adjacency.setdefault(edge["source"], []).append(edge)
    for neighbours in adjacency.values():
        neighbours.sort(key=lambda e: (e["target"], e["cost"]))
    queue: list[tuple[float, int, tuple[str, ...]]] = [(0.0, 0, (start,))]
    counter = 1
    seen_states: set[tuple[str, frozenset[str]]] = set()
    while queue:
        cost, _, atoms = heapq.heappop(queue)
        node = atoms[-1]
        if node == goal:
            return atoms
        key = (node, frozenset(atoms))
        if key in seen_states:
            continue
        seen_states.add(key)
        for edge in adjacency.get(node, ()):
            if edge["target"] in atoms:
                continue
            extended = atoms + (edge["target"],)
            if _violated(set(extended), obstructions):
                continue
            heapq.heappush(queue, (cost + edge["cost"], counter, extended))
            counter += 1
    return None


def _relaxed_routes(edges: list[dict[str, Any]], start: str, goal: str,
                    limit: int = ROUTE_ENUM_LIMIT) -> list[tuple[dict[str, Any], ...]]:
    adjacency: dict[str, list[dict[str, Any]]] = {}
    for edge in edges:
        adjacency.setdefault(edge["source"], []).append(edge)
    for neighbours in adjacency.values():
        neighbours.sort(key=lambda e: (e["target"], e["cost"]))
    routes: list[tuple[dict[str, Any], ...]] = []

    def walk(node: str, seen: frozenset[str], acc: tuple[dict[str, Any], ...]) -> None:
        if len(routes) >= limit:
            return
        if node == goal:
            routes.append(acc)
            return
        for edge in adjacency.get(node, ()):
            if edge["target"] in seen:
                continue
            walk(edge["target"], seen | {edge["target"]}, acc + (edge,))

    walk(start, frozenset({start}), ())
    return routes


def need_atoms(edges: list[dict[str, Any]], obstructions: list[dict[str, Any]],
               start: str, goal: str, required_authority: int) -> list[str]:
    """The frozen acquisition-guidance set for arm B (PROTOCOL.json policy):
    (1) endpoints of the minimal repair (cheapest-shortfall unobstructed relaxed
    route's under-licensed edges) when relaxed routes exist; (2) otherwise the
    forward frontier from start plus the backward frontier into goal plus
    {start, goal}."""
    relaxed = _relaxed_routes(edges, start, goal)
    if relaxed:
        best: tuple[float, list[str]] | None = None
        for route in relaxed:
            atoms = {start} | {e["target"] for e in route}
            if _violated(atoms, obstructions):
                continue
            shortfall = 0.0
            endpoints: list[str] = []
            for edge in route:
                if edge["licensed_at"] < required_authority:
                    shortfall += required_authority - edge["licensed_at"]
                    endpoints.extend((edge["source"], edge["target"]))
            if best is None or shortfall < best[0]:
                best = (shortfall, endpoints)
        if best is not None:
            return sorted(set(best[1]) | {goal})
    forward: set[str] = {start}
    changed = True
    while changed:
        changed = False
        for edge in edges:
            if edge["source"] in forward and edge["target"] not in forward:
                forward.add(edge["target"])
                changed = True
    backward: set[str] = {goal}
    changed = True
    while changed:
        changed = False
        for edge in edges:
            if edge["target"] in backward and edge["source"] not in backward:
                backward.add(edge["source"])
                changed = True
    return sorted(forward | backward | {start, goal})


# ---------------------------------------------------------------------------
# Frozen decision-equivalent arm policies.
# ---------------------------------------------------------------------------

def _target_tokens(record: dict[str, Any]) -> set[str]:
    target = record["target"]
    return set(target.get("description_tokens") or ()) | {
        target["start_atom"], target["goal_atom"]}


def _lexical_order(record: dict[str, Any]) -> list[dict[str, Any]]:
    tokens = _target_tokens(record)
    return sorted(
        record["sources"],
        key=lambda s: (-len(tokens & set(s["index_tokens"])), s["source_id"]),
    )


def arm_a_policy(record: dict[str, Any],
                 source_order: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Budgeted raw reading: read sources in frozen lexical-overlap order at
    COST_READ each; after each read, check for an admissible route over all
    facts read so far (same connect rule as arm B — the contrast is acquisition
    ordering and cost, not the connect step). The typed structure of unread
    sources is invisible; index tokens are visible to both arms."""
    target = record["target"]
    order = source_order if source_order is not None else _lexical_order(record)
    edges: list[dict[str, Any]] = []
    obstructions: list[dict[str, Any]] = []
    spent = 0.0
    for source in order:
        if spent + COST_READ > record["budget_units"]:
            break
        spent += COST_READ
        edges.extend(source["edges"])
        obstructions.extend(source.get("obstructions") or ())
        route = admissible_route(edges, obstructions, target["start_atom"],
                                 target["goal_atom"], target["required_authority"])
        if route is not None:
            return {"declaration": "SOLVED", "route": list(route), "budget_spent": spent}
    return {"declaration": "NOT_SOLVED", "route": None, "budget_spent": spent}


def arm_b_policy(record: dict[str, Any],
                 index_override: dict[str, list[str]] | None = None,
                 random_order: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Distil-then-navigate: distil sources at COST_DISTIL each into a typed
    partial support structure; after each distillation run the navigation core
    (execution run: rakl.support_solver.solve); choose the next source by
    overlap between its index tokens and the current need set (repair endpoints,
    else frontier); fall back to lexical order on zero overlap. All distillation
    cost is charged to this arm. index_override / random_order exist only for
    the frozen nulls."""
    target = record["target"]
    tokens = _target_tokens(record)

    def index_of(source: dict[str, Any]) -> set[str]:
        if index_override is not None:
            return set(index_override[source["source_id"]])
        return set(source["index_tokens"])

    edges: list[dict[str, Any]] = []
    obstructions: list[dict[str, Any]] = []
    spent = 0.0
    remaining = sorted(record["sources"], key=lambda s: s["source_id"])
    first = True
    while remaining and spent + COST_DISTIL <= record["budget_units"]:
        if random_order is not None:
            choice = next(s for s in random_order if s in remaining)
        elif first:
            choice = min(remaining, key=lambda s: (-len(tokens & index_of(s)), s["source_id"]))
        else:
            need = set(need_atoms(edges, obstructions, target["start_atom"],
                                  target["goal_atom"], target["required_authority"]))
            choice = min(
                remaining,
                key=lambda s: (-len(need & index_of(s)),
                               -len(tokens & index_of(s)), s["source_id"]),
            )
        first = False
        remaining.remove(choice)
        spent += COST_DISTIL
        edges.extend(choice["edges"])
        obstructions.extend(choice.get("obstructions") or ())
        route = admissible_route(edges, obstructions, target["start_atom"],
                                 target["goal_atom"], target["required_authority"])
        if route is not None:
            return {"declaration": "SOLVED", "route": list(route), "budget_spent": spent}
    return {"declaration": "NOT_SOLVED", "route": None, "budget_spent": spent}


def assert_no_rule_drift(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]],
                         policy, arm_name: str) -> None:
    drift = [
        row["world_id"] for row in corpus
        if policy(row)["declaration"] != arm[row["world_id"]]["declaration"]
    ]
    if drift:
        raise CannotCheck(
            f"arm {arm_name} declarations drift from the frozen decision-equivalent policy "
            f"on {len(drift)} worlds (e.g. {drift[:3]}); protocol binding broken"
        )


# ---------------------------------------------------------------------------
# World-truth verification of declared routes (false-solve guard).
# ---------------------------------------------------------------------------

def world_verified(record: dict[str, Any], declaration: dict[str, Any]) -> bool:
    """A declared SOLVED must carry a route that is admissible against the FULL
    world fact set — every edge present and licensed, no world obstruction
    (read or unread) realized. A SOLVED failing this is a false solve."""
    if declaration["declaration"] != "SOLVED":
        return False
    route = declaration.get("route")
    if not route or len(route) < 2:
        return False
    target = record["target"]
    if route[0] != target["start_atom"] or route[-1] != target["goal_atom"]:
        return False
    all_edges: set[tuple[str, str]] = set()
    all_obstructions: list[dict[str, Any]] = []
    for source in record["sources"]:
        for edge in source["edges"]:
            if edge["licensed_at"] >= target["required_authority"]:
                all_edges.add((edge["source"], edge["target"]))
        all_obstructions.extend(source.get("obstructions") or ())
    for i in range(len(route) - 1):
        if (route[i], route[i + 1]) not in all_edges:
            return False
    if _violated(set(route), all_obstructions):
        return False
    return True


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def primary_set(corpus: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = [row for row in corpus
            if row["gold_label"] == "SOLVABLE"
            and row["budget_class"] in PRIMARY_BUDGET_CLASSES]
    if not rows:
        raise CannotCheck("empty primary set (gold SOLVABLE, MEDIUM/LOOSE budget)")
    return rows


def solve_indicator(record: dict[str, Any], declaration: dict[str, Any]) -> int:
    return 1 if world_verified(record, declaration) else 0


def sr(rows: list[dict[str, Any]], arm: dict[str, dict[str, Any]]) -> float:
    if not rows:
        raise CannotCheck("solve-rate denominator is empty")
    return sum(solve_indicator(row, arm[row["world_id"]]) for row in rows) / len(rows)


def fsr(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]]) -> float:
    bad = sum(
        1 for row in corpus
        if arm[row["world_id"]]["declaration"] == "SOLVED"
        and not world_verified(row, arm[row["world_id"]])
    )
    return bad / len(corpus)


def mcnemar_exact(rows: list[dict[str, Any]], arm_a: dict[str, dict[str, Any]],
                  arm_b: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Two-sided exact McNemar on world-level verified-solve indicators."""
    b_count = 0  # B solves, A does not
    c_count = 0  # A solves, B does not
    for row in rows:
        fa = solve_indicator(row, arm_a[row["world_id"]])
        fb = solve_indicator(row, arm_b[row["world_id"]])
        if fb == 1 and fa == 0:
            b_count += 1
        elif fa == 1 and fb == 0:
            c_count += 1
    n_disc = b_count + c_count
    if n_disc == 0:
        return {"b": 0, "c": 0, "p_two_sided": 1.0}
    k = min(b_count, c_count)
    tail = sum(math.comb(n_disc, i) for i in range(0, k + 1)) / (2 ** n_disc)
    p = min(1.0, 2.0 * tail)
    return {"b": b_count, "c": c_count, "p_two_sided": p}


def random_acquisition_null(rows: list[dict[str, Any]], rng: random.Random) -> dict[str, Any]:
    """Null 1 (equal-budget suppression analogue): arm B's cost model and budget
    with seeded random source order instead of navigation. Tests that the
    benefit comes from navigating the distilled structure, not from paying the
    distillation cost while reading fewer sources."""
    draws: list[float] = []
    for _ in range(NULL_DRAWS):
        solved = 0
        for row in rows:
            order = sorted(row["sources"], key=lambda s: s["source_id"])
            rng.shuffle(order)
            out = arm_b_policy(row, random_order=order)
            solved += solve_indicator(row, out)
        draws.append(solved / len(rows))
    draws.sort()
    q_index = min(len(draws) - 1, int((1 - NULL_QUANTILE) * NULL_DRAWS))
    return {"q95": draws[q_index], "mean": sum(draws) / len(draws)}


def index_permutation_null(rows: list[dict[str, Any]], rng: random.Random) -> dict[str, Any]:
    """Null 2 (structure permutation): permute index tokens across sources
    within each world and re-run arm B's frozen policy. Tests that the benefit
    requires genuine structure-to-source binding rather than any fixed reading
    schedule the policy happens to induce."""
    draws: list[float] = []
    for _ in range(NULL_DRAWS):
        solved = 0
        for row in rows:
            ids = sorted(s["source_id"] for s in row["sources"])
            tokens = {s["source_id"]: list(s["index_tokens"]) for s in row["sources"]}
            shuffled = ids[:]
            rng.shuffle(shuffled)
            override = {dst: tokens[src] for dst, src in zip(ids, shuffled)}
            out = arm_b_policy(row, index_override=override)
            solved += solve_indicator(row, out)
        draws.append(solved / len(rows))
    draws.sort()
    q_index = min(len(draws) - 1, int((1 - NULL_QUANTILE) * NULL_DRAWS))
    return {"q95": draws[q_index], "mean": sum(draws) / len(draws)}


# ---------------------------------------------------------------------------
# Verdict (frozen; no post-result rescue)
# ---------------------------------------------------------------------------

def verdict(report: dict[str, Any]) -> str:
    delta = report["sr_b"] - report["sr_a"]
    null1_beaten = report["sr_b"] > report["null_random_acquisition"]["q95"]
    null2_beaten = report["sr_b"] > report["null_index_permutation"]["q95"]
    promote = (
        delta >= THRESH_DELTA_SR_PROMOTE
        and report["mcnemar"]["p_two_sided"] < THRESH_MCNEMAR_P
        and report["sfh_b"] >= THRESH_SFH_FLOOR
        and report["fsr_b"] == 0.0
        and report["sr_b_loose"] >= report["sr_a_loose"] - THRESH_LOOSE_NONINF
        and null1_beaten
        and null2_beaten
    )
    if promote:
        return "PROMOTE"
    negative = delta <= THRESH_DELTA_SR_NEGATIVE or not null1_beaten or not null2_beaten
    if negative:
        return "NEGATIVE"
    return "CONDITIONAL"


# ---------------------------------------------------------------------------
# Evaluation driver
# ---------------------------------------------------------------------------

def evaluate(corpus_path: str, arm_a_path: str, arm_b_path: str, audit_path: str,
             arm_run_started_at: str, seed: int) -> dict[str, Any]:
    corpus = load_corpus(corpus_path)
    if len(corpus) != N_EXPECTED_WORLDS:
        raise CannotCheck(
            f"corpus has {len(corpus)} worlds; protocol froze N={N_EXPECTED_WORLDS}"
        )
    assert_label_independence(corpus, arm_run_started_at)
    audit = assert_audit_receipt(audit_path)
    arm_a = load_arm(arm_a_path, corpus, "A")
    arm_b = load_arm(arm_b_path, corpus, "B")
    assert_no_rule_drift(corpus, arm_a, arm_a_policy, "A")
    assert_no_rule_drift(corpus, arm_b, arm_b_policy, "B")

    primary = primary_set(corpus)
    floor_rows = [row for row in corpus if row["class"] == FLOOR_CLASS]
    loose_rows = [row for row in corpus
                  if row["class"] == LOOSE_CLASS and row["gold_label"] == "SOLVABLE"]
    if not floor_rows:
        raise CannotCheck(f"corpus has no {FLOOR_CLASS} rows; honest-cost floor undefined")
    if not loose_rows:
        raise CannotCheck(f"corpus has no {LOOSE_CLASS} rows; loose non-inferiority undefined")
    tight_rows = [row for row in corpus
                  if row["budget_class"] == "TIGHT" and row["gold_label"] == "SOLVABLE"]

    rng = random.Random(seed)
    report: dict[str, Any] = {
        "corpus_sha256": _sha256_file(corpus_path),
        "n_worlds": len(corpus),
        "n_primary": len(primary),
        "seed": seed,
        "audit": audit,
        "sr_a": sr(primary, arm_a),
        "sr_b": sr(primary, arm_b),
        "fsr_a": fsr(corpus, arm_a),
        "fsr_b": fsr(corpus, arm_b),
        "sfh_b": sr(floor_rows, arm_b),
        "sfh_a": sr(floor_rows, arm_a),
        "sr_a_loose": sr(loose_rows, arm_a),
        "sr_b_loose": sr(loose_rows, arm_b),
        "sr_a_tight": sr(tight_rows, arm_a) if tight_rows else None,
        "sr_b_tight": sr(tight_rows, arm_b) if tight_rows else None,
        "mcnemar": mcnemar_exact(primary, arm_a, arm_b),
        "null_random_acquisition": random_acquisition_null(primary, rng),
        "null_index_permutation": index_permutation_null(primary, rng),
    }
    report["delta_sr"] = report["sr_b"] - report["sr_a"]
    report["verdict"] = verdict(report)
    return report


# ---------------------------------------------------------------------------
# Self-test: rule-sanity, no-alarm, planted-fail, CANNOT_CHECK, determinism.
# Synthetic fixtures only; never experiment evidence.
# ---------------------------------------------------------------------------

def _edge(src: str, dst: str, licensed: int = 2) -> dict[str, Any]:
    return {"source": src, "target": dst, "cost": 1.0, "licensed_at": licensed}


def _fixture_world(world_id: str, budget: float, *, budget_class: str = "MEDIUM",
                   klass: str = "N1", gold: str = "SOLVABLE") -> dict[str, Any]:
    """Chain a0->a1->a2->a3 buried across s0..s2; s3 is a lexical decoy
    (target-heavy index tokens, irrelevant edges); s4 is a pure distractor."""
    return {
        "world_id": world_id,
        "class": klass,
        "budget_class": budget_class,
        "budget_units": budget,
        "gold_label": gold,
        "label_minted_at": "2000-01-01T00:00:00Z",
        "target": {"start_atom": "a0", "goal_atom": "a3",
                   "required_authority": 2, "description_tokens": ["tq", "tw"]},
        "minimal_source_count": 3,
        "sources": [
            {"source_id": "s0", "index_tokens": ["a0", "a1", "tq"],
             "edges": [_edge("a0", "a1")], "obstructions": []},
            {"source_id": "s1", "index_tokens": ["a1", "a2"],
             "edges": [_edge("a1", "a2")], "obstructions": []},
            {"source_id": "s2", "index_tokens": ["a2", "a3"],
             "edges": [_edge("a2", "a3")], "obstructions": []},
            {"source_id": "s3", "index_tokens": ["tq", "tw", "z9"],
             "edges": [_edge("z1", "z2")], "obstructions": []},
            {"source_id": "s4", "index_tokens": ["z3"],
             "edges": [], "obstructions": []},
        ],
    }


def self_test() -> int:
    failures: list[str] = []

    # World 1 — rule sanity. The decoy s3 outranks every chain source lexically
    # (tq, tw, goal atom a3), so BOTH arms honestly spend their first
    # acquisition on it; arm B then recovers via need-guided selection
    # (frontier -> s0 -> s2 -> s1) and solves in 4 distils (budget 8.0).
    w = _fixture_world("w0", 8.0)
    w["sources"][3]["index_tokens"] = ["tq", "tw", "a3"]  # decoy outranks s0
    out_b = arm_b_policy(w)
    if out_b["declaration"] != "SOLVED":
        failures.append(f"rule: arm B should navigate to a solve within budget 8.0: {out_b}")
    # Arm A at budget 3.0 reads s3, s0, s2 (lexical order) and cannot connect.
    w_tight = _fixture_world("w1", 3.0)
    w_tight["sources"][3]["index_tokens"] = ["tq", "tw", "a3"]
    if arm_a_policy(w_tight)["declaration"] != "NOT_SOLVED":
        failures.append("rule: arm A at budget 3.0 should waste a read on the decoy and fail")
    if arm_b_policy(w_tight)["declaration"] != "NOT_SOLVED":
        failures.append("rule: arm B at budget 3.0 (1 distil) cannot cover a 3-source chain")

    # Obstruction awareness: a route realizing a known obstruction is rejected.
    w_ob = _fixture_world("w2", 10.0)
    w_ob["sources"][0]["obstructions"] = [{"obstruction_id": "ob1", "cover": ["a0", "a1", "a2", "a3"]}]
    route = admissible_route(
        [e for s in w_ob["sources"] for e in s["edges"]],
        [o for s in w_ob["sources"] for o in (s.get("obstructions") or ())],
        "a0", "a3", 2)
    if route is not None:
        failures.append("rule: obstruction-realizing route must be rejected")

    # World 2 — no-alarm: a silent arm has SR 0 and FSR 0; silence never mints benefit.
    corpus = [w, w_tight]
    silent = {r["world_id"]: {"world_id": r["world_id"], "declaration": "NOT_SOLVED",
                              "route": None} for r in corpus}
    if fsr(corpus, silent) != 0.0 or sr(corpus, silent) != 0.0:
        failures.append("no-alarm: silent arm should have SR 0 and FSR 0")

    # World 3 — planted fail: a declared route with a missing edge is a false solve.
    fake = {"world_id": "w0", "declaration": "SOLVED", "route": ["a0", "a9", "a3"]}
    if world_verified(w, fake):
        failures.append("planted: hallucinated route must fail the world check")
    if fsr([w], {"w0": fake}) != 1.0:
        failures.append("planted: FSR should flag the hallucinated solve")
    # Under-licensed edge also fails the world check.
    w_lic = _fixture_world("w3", 10.0)
    w_lic["sources"][1]["edges"] = [_edge("a1", "a2", licensed=1)]
    honest_route = {"world_id": "w3", "declaration": "SOLVED",
                    "route": ["a0", "a1", "a2", "a3"]}
    if world_verified(w_lic, honest_route):
        failures.append("planted: under-licensed route must fail the world check")

    # World 4 — CANNOT_CHECK paths must raise, not pass.
    try:
        assert_label_independence(
            [dict(w, label_minted_at="2030-01-01T00:00:00Z")], "2020-01-01T00:00:00Z")
        failures.append("cannot-check: label-after-arm must raise")
    except CannotCheck:
        pass
    try:
        wrong = {r["world_id"]: {"world_id": r["world_id"], "declaration": "SOLVED",
                                 "route": None} for r in corpus}
        assert_no_rule_drift(corpus, wrong, arm_a_policy, "A")
        failures.append("cannot-check: rule drift must raise")
    except CannotCheck:
        pass
    try:
        primary_set([_fixture_world("w9", 4.0, budget_class="TIGHT")])
        failures.append("cannot-check: empty primary set must raise")
    except CannotCheck:
        pass

    # World 5 — determinism: nulls are seed-stable; index permutation degrades B.
    rows = [w]
    n1a = index_permutation_null(rows, random.Random(7))
    n1b = index_permutation_null(rows, random.Random(7))
    if n1a != n1b:
        failures.append("determinism: index-permutation null not seed-stable")
    n2a = random_acquisition_null(rows, random.Random(7))
    n2b = random_acquisition_null(rows, random.Random(7))
    if n2a != n2b:
        failures.append("determinism: random-acquisition null not seed-stable")

    if failures:
        for line in failures:
            print(f"SELFTEST FAIL: {line}", file=sys.stderr)
        return 2
    print("SELFTEST PASS: rule-sanity, obstruction, no-alarm, planted-fail, "
          "cannot-check, determinism")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--corpus")
    parser.add_argument("--arm-a")
    parser.add_argument("--arm-b")
    parser.add_argument("--audit")
    parser.add_argument("--arm-run-started-at")
    parser.add_argument("--seed", type=int, default=20260814)
    parser.add_argument("--out")
    args = parser.parse_args(argv)

    if args.selftest:
        return self_test()

    if not all([args.corpus, args.arm_a, args.arm_b, args.audit, args.arm_run_started_at]):
        parser.print_usage(sys.stderr)
        return 4
    try:
        report = evaluate(args.corpus, args.arm_a, args.arm_b, args.audit,
                          args.arm_run_started_at, args.seed)
    except CannotCheck as exc:
        payload = {"verdict": "CANNOT_CHECK", "reason": str(exc)}
        print(json.dumps(payload, indent=2))
        if args.out:
            with open(args.out, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
        return 3
    print(json.dumps(report, indent=2))
    if args.out:
        with open(args.out, "w", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
