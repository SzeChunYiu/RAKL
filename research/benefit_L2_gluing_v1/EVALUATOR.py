"""Frozen WGR evaluator for benefit_L2_gluing_v1 (ladder L2-GLUING benefit obligation).

Research-local. Frozen with PROTOCOL.json (this file's sha256 is embedded there).
Any edit after the protocol freeze invalidates the protocol hash binding and the
run must be declared CANNOT_CHECK.

Scope
-----
Computes, for a labeled known-answer atlas corpus and two arm output files:

  WGR_arm = (# atlases where arm declared GLUE and gold == NOT_GLUEABLE)
            / (# atlases)                        [ladder.json L2-GLUING observable]

  GCA_arm = (# atlases where arm declared GLUE and gold == GLUEABLE)
            / (# gold GLUEABLE atlases)          [frozen over-refusal guard]

plus the paired McNemar exact test on atlas-level wrong-gluing indicators, the
equal-n random-suppression null, the obstruction-block permutation null
(stratified by topology signature), and the mechanized twin bound: every
parity-obstruction row carries a solvable twin with an identical pairwise
record (Lean: covers_agree_on_pairwise_data / parityCover vs consistentCover),
so any pairwise-only arm must err at least once per twin pair
(no_pairwise_predicate_decides_global_realizability, formal/RaklFormal.lean).

It emits exactly one typed verdict: PROMOTE | NEGATIVE | CONDITIONAL | CANNOT_CHECK.
CANNOT_CHECK is a distinct exit code (3) and is never conflated with a clean pass.

Exit codes: 0 = evaluated (verdict in report, any of PROMOTE/NEGATIVE/CONDITIONAL),
            2 = self-test failure, 3 = CANNOT_CHECK, 4 = usage error.

Determinism: all randomness flows from the single --seed argument through
random.Random; iteration orders are sorted. No network. No non-stdlib imports.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Frozen constants (mirror PROTOCOL.json; the protocol is authoritative — a
# mismatch between these and PROTOCOL.json is itself CANNOT_CHECK).
# ---------------------------------------------------------------------------
GOLD_LABELS = ("GLUEABLE", "NOT_GLUEABLE")
ARM_DECLARATIONS = ("GLUE", "REFUSE")
N_EXPECTED_ATLASES = 400
MAX_VARIABLES = 6
NULL_DRAWS = 1000
THRESH_DELTA_WGR_PROMOTE = 0.10
THRESH_DELTA_WGR_NEGATIVE = 0.02
THRESH_MCNEMAR_P = 0.001
THRESH_GCA_FLOOR = 0.70
NULL_QUANTILE = 0.05
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
    "atlas_id", "gold_label", "label_minted_at", "charts", "variables",
    "transitions", "constraint_tables", "cycle_witnesses", "twin_id",
)


def load_corpus(path: str) -> list[dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CannotCheck(f"corpus unreadable: {exc}") from exc
    atlases = payload.get("atlases")
    if not isinstance(atlases, list) or not atlases:
        raise CannotCheck("corpus has no atlases; denominator would be zero")
    for row in atlases:
        for key in REQUIRED_ROW_KEYS:
            if key not in row:
                raise CannotCheck(f"corpus row missing {key!r}")
        if row["gold_label"] not in GOLD_LABELS:
            raise CannotCheck(f"unknown gold label {row['gold_label']!r}")
        if len(row["variables"]) > MAX_VARIABLES:
            raise CannotCheck(
                f"atlas {row['atlas_id']} has {len(row['variables'])} variables; "
                f"protocol froze <= {MAX_VARIABLES} for exact existence search"
            )
    ids = [row["atlas_id"] for row in atlases]
    if len(ids) != len(set(ids)):
        raise CannotCheck("duplicate atlas_id in corpus")
    return sorted(atlases, key=lambda row: row["atlas_id"])


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
        by_id[row["atlas_id"]] = row
    corpus_ids = {row["atlas_id"] for row in corpus}
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
        row["atlas_id"]
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
# Structural helpers (mirror the repaired atlas semantics: topology is
# recomputed from the transition set, never trusted from a declaration).
# ---------------------------------------------------------------------------

def _edges(transitions: list[dict[str, Any]]) -> list[tuple[str, str, str]]:
    out = []
    for t in transitions:
        a, b = sorted((t["left_chart"], t["right_chart"]))
        out.append((a, b, t["overlap_id"]))
    return sorted(set(out))


def _topology(charts: list[str], transitions: list[dict[str, Any]]) -> dict[str, Any]:
    edges = _edges(transitions)
    pair_counts: dict[tuple[str, str], int] = {}
    for a, b, _ in edges:
        pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1
    parent = {c: c for c in charts}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b, _ in edges:
        if a in parent and b in parent:
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb
    components = len({find(c) for c in charts})
    cycles = len(edges) - len(charts) + components
    return {
        "connected": components == 1,
        "independent_cycle_count": cycles,
        "edges": edges,
        "has_parallel_overlap_edges": any(v > 1 for v in pair_counts.values()),
    }


def _satisfiable(variables: list[str], constraint_tables: dict[str, Any]) -> bool:
    """Exhaustive global-section search over binary variables (<= MAX_VARIABLES).

    Each constraint table lists the allowed partial assignments of its chart's
    variables. A global section is one total assignment consistent with every
    chart's table. Exact; no sampling."""
    tables = []
    for chart_id in sorted(constraint_tables):
        entry = constraint_tables[chart_id]
        chart_vars = entry["variables"]
        allowed = {tuple(a) for a in entry["allowed"]}
        tables.append((chart_vars, allowed))
    for assignment in itertools.product([0, 1], repeat=len(variables)):
        values = dict(zip(variables, assignment))
        if all(tuple(values[v] for v in chart_vars) in allowed
               for chart_vars, allowed in tables):
            return True
    return False


# ---------------------------------------------------------------------------
# Frozen decision-equivalent arm rules.
#
# arm_a_rule / arm_b_rule MUST match PROTOCOL.json arms.{A,B}.definition
# verbatim; drift between an arm's live declarations on the real corpus and
# the replicated rule here is CANNOT_CHECK (enforced in evaluate()).
# ---------------------------------------------------------------------------

def arm_a_rule(row: dict[str, Any]) -> str:
    """Pairwise-only compatibility: GLUE iff every overlap transition passes its
    pairwise checks with a complete pairwise record. Cycle witnesses, topology
    and constraint tables are present in the input record and deliberately
    ignored — this is the obstruction-blind distillation of
    formal/RaklFormal.lean (PairwiseRealizable)."""
    for t in row["transitions"]:
        if t.get("fields_complete_pairwise") is not True:
            return "REFUSE"
        if t.get("pairwise_pass") is not True:
            return "REFUSE"
    return "GLUE"


def arm_b_rule(row: dict[str, Any]) -> str:
    """Obstruction-retaining gluing, decision-equivalent to
    rakl.atlas_gluing.evaluate_atlas_gluing (repaired declared-topology
    semantics) returning an existence-entailing verdict
    (GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY or GLOBAL_EXISTS_UNIQUENESS_UNPROVEN)
    mapped to GLUE, versus every other verdict mapped to REFUSE.
    Fail-closed: incomplete obstruction records REFUSE, never assumed."""
    transitions = row["transitions"]
    for t in transitions:
        if t.get("fields_complete_pairwise") is not True:
            return "REFUSE"
        if t.get("pairwise_pass") is not True:
            return "REFUSE"
    topo = _topology(row["charts"], transitions)
    if not topo["connected"]:
        return "REFUSE"
    if topo["has_parallel_overlap_edges"]:
        return "REFUSE"  # cycle-basis completeness unrecomputable -> CANNOT_CHECK -> refuse
    if topo["independent_cycle_count"] > 0:
        witnesses = row["cycle_witnesses"]
        if len(witnesses) != topo["independent_cycle_count"]:
            return "REFUSE"
        edge_set = {(a, b) for a, b, _ in topo["edges"]}
        for w in witnesses:
            if not w.get("evidence_ids"):
                return "REFUSE"  # incomplete obstruction record (class G6 charge)
            path = w.get("chart_path", [])
            if len(path) < 3 or path[0] != path[-1]:
                return "REFUSE"
            for i in range(len(path) - 1):
                a, b = sorted((path[i], path[i + 1]))
                if (a, b) not in edge_set:
                    return "REFUSE"
            if w.get("composition_consistent") is not True:
                return "REFUSE"  # holonomy obstruction retained -> OBSTRUCTED_ATLAS
    if not _satisfiable(row["variables"], row["constraint_tables"]):
        return "REFUSE"  # explicit global-existence check failed
    return "GLUE"


def assert_no_rule_drift(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]],
                         rule, arm_name: str) -> None:
    drift = [
        row["atlas_id"] for row in corpus
        if rule(row) != arm[row["atlas_id"]]["declaration"]
    ]
    if drift:
        raise CannotCheck(
            f"arm {arm_name} declarations drift from the frozen decision-equivalent rule "
            f"on {len(drift)} atlases (e.g. {drift[:3]}); protocol binding broken"
        )


# ---------------------------------------------------------------------------
# Mechanized twin bound (Lean ObstructionBlindness, instantiated as data)
# ---------------------------------------------------------------------------

def _pairwise_record(row: dict[str, Any]) -> str:
    """Canonical serialization of exactly the fields a pairwise-only arm reads."""
    record = sorted(
        (t["left_chart"], t["right_chart"], t["overlap_id"],
         bool(t["pairwise_pass"]), bool(t["fields_complete_pairwise"]),
         json.dumps(t.get("overlap_restrictions", None), sort_keys=True))
        for t in row["transitions"]
    )
    return json.dumps(record, sort_keys=True)


def twin_bound_check(corpus: list[dict[str, Any]],
                     arm_a: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Verify the corpus twin invariant and the pairwise impossibility bound.

    Twin invariant: each NOT_GLUEABLE parity row's twin_id names a GLUEABLE row
    whose pairwise record is byte-identical (covers_agree_on_pairwise_data).
    Bound: a pairwise-only arm must, on each twin pair, either wrongly glue the
    parity row or wrongly refuse the solvable twin
    (no_pairwise_predicate_decides_global_realizability). Arm A is declared
    pairwise-only, so a violated bound means the twin invariant or the arm's
    pairwise-only claim is broken — CANNOT_CHECK either way."""
    by_id = {row["atlas_id"]: row for row in corpus}
    pairs: list[tuple[str, str]] = []
    for row in corpus:
        twin = row.get("twin_id")
        if row["gold_label"] == "NOT_GLUEABLE" and twin:
            if twin not in by_id:
                raise CannotCheck(f"twin_id {twin!r} of {row['atlas_id']} not in corpus")
            other = by_id[twin]
            if other["gold_label"] != "GLUEABLE":
                raise CannotCheck(
                    f"twin {twin!r} of parity row {row['atlas_id']} is not GLUEABLE"
                )
            if _pairwise_record(row) != _pairwise_record(other):
                raise CannotCheck(
                    f"twin pair ({row['atlas_id']}, {twin}) has divergent pairwise "
                    "records; the mechanized construction is not faithfully instantiated"
                )
            pairs.append((row["atlas_id"], twin))
    if not pairs:
        raise CannotCheck(
            "corpus contains no twinned parity pairs; the mechanized construction "
            "(prop:obstruction-blind) is not instantiated"
        )
    violations = []
    for parity_id, twin_id in pairs:
        wrong_glue = arm_a[parity_id]["declaration"] == "GLUE"
        wrong_refusal = arm_a[twin_id]["declaration"] == "REFUSE"
        if not (wrong_glue or wrong_refusal):
            violations.append((parity_id, twin_id))
    if violations:
        raise CannotCheck(
            f"pairwise-only arm A beat the mechanized impossibility bound on "
            f"{len(violations)} twin pairs (e.g. {violations[:3]}); either the twin "
            "invariant is broken or arm A read non-pairwise fields"
        )
    return {"n_twin_pairs": len(pairs), "bound_holds_for_arm_a": True}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def wrong_gluing_indicator(gold: str, declaration: str) -> int:
    return 1 if declaration == "GLUE" and gold == "NOT_GLUEABLE" else 0


def wgr(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]]) -> float:
    n = len(corpus)
    bad = sum(
        wrong_gluing_indicator(row["gold_label"], arm[row["atlas_id"]]["declaration"])
        for row in corpus
    )
    return bad / n


def gca(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]]) -> float:
    gold_pos = [row for row in corpus if row["gold_label"] == "GLUEABLE"]
    if not gold_pos:
        raise CannotCheck("corpus contains zero gold GLUEABLE atlases; GCA guard undefined")
    hits = sum(
        1 for row in gold_pos if arm[row["atlas_id"]]["declaration"] == "GLUE"
    )
    return hits / len(gold_pos)


def mcnemar_exact(corpus: list[dict[str, Any]], arm_a: dict[str, dict[str, Any]],
                  arm_b: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Two-sided exact McNemar on atlas-level wrong-gluing indicators."""
    b_count = 0  # A wrong-glues, B does not
    c_count = 0  # B wrong-glues, A does not
    for row in corpus:
        fa = wrong_gluing_indicator(row["gold_label"], arm_a[row["atlas_id"]]["declaration"])
        fb = wrong_gluing_indicator(row["gold_label"], arm_b[row["atlas_id"]]["declaration"])
        if fa == 1 and fb == 0:
            b_count += 1
        elif fa == 0 and fb == 1:
            c_count += 1
    n_disc = b_count + c_count
    if n_disc == 0:
        return {"b": 0, "c": 0, "p_two_sided": 1.0}
    k = min(b_count, c_count)
    tail = sum(math.comb(n_disc, i) for i in range(0, k + 1)) / (2 ** n_disc)
    p = min(1.0, 2.0 * tail)
    return {"b": b_count, "c": c_count, "p_two_sided": p}


def equal_n_suppression_null(corpus: list[dict[str, Any]], arm_a: dict[str, dict[str, Any]],
                             arm_b: dict[str, dict[str, Any]], rng: random.Random) -> dict[str, Any]:
    """Null 1: keep a random size-K_B subset of A's GLUE declarations; WGR distribution.

    Tests selectivity-vs-edge: B must beat blind refusal at its own acceptance
    count, else its WGR advantage is a base-rate artifact."""
    a_glued = sorted(
        row["atlas_id"] for row in corpus
        if arm_a[row["atlas_id"]]["declaration"] == "GLUE"
    )
    k_b = sum(
        1 for row in corpus if arm_b[row["atlas_id"]]["declaration"] == "GLUE"
    )
    if k_b >= len(a_glued):
        return {"applicable": False, "k_b": k_b, "k_a": len(a_glued)}
    gold = {row["atlas_id"]: row["gold_label"] for row in corpus}
    n = len(corpus)
    draws: list[float] = []
    for _ in range(NULL_DRAWS):
        kept = rng.sample(a_glued, k_b)
        bad = sum(1 for aid in kept if gold[aid] == "NOT_GLUEABLE")
        draws.append(bad / n)
    draws.sort()
    q_index = max(0, int(NULL_QUANTILE * NULL_DRAWS) - 1)
    return {
        "applicable": True,
        "k_b": k_b,
        "k_a": len(a_glued),
        "q05": draws[q_index],
        "mean": sum(draws) / len(draws),
    }


def _stratum_signature(row: dict[str, Any]) -> str:
    edges = _edges(row["transitions"])
    return json.dumps({
        "n_charts": len(row["charts"]),
        "n_variables": len(row["variables"]),
        "edge_pairs": [[a, b] for a, b, _ in edges],
    }, sort_keys=True)


def obstruction_permutation_null(corpus: list[dict[str, Any]], rng: random.Random) -> dict[str, Any]:
    """Null 2: permute the obstruction-relevant block (cycle-witness consistency
    values + constraint tables) across atlases with identical topology
    signature, re-run arm B's frozen decision-equivalent rule, collect the WGR
    distribution.

    Tests that B's advantage requires genuine obstruction-instance binding
    rather than refusing a fixed fraction of cyclic covers."""
    strata: dict[str, list[int]] = {}
    for idx, row in enumerate(corpus):
        strata.setdefault(_stratum_signature(row), []).append(idx)
    blocks = [
        {"cycle_witnesses": row["cycle_witnesses"],
         "constraint_tables": row["constraint_tables"]}
        for row in corpus
    ]
    n = len(corpus)
    draws: list[float] = []
    for _ in range(NULL_DRAWS):
        permuted: list[dict[str, Any]] = list(blocks)
        for indices in strata.values():
            shuffled = indices[:]
            rng.shuffle(shuffled)
            for src, dst in zip(indices, shuffled):
                permuted[dst] = blocks[src]
        bad = 0
        for row, block in zip(corpus, permuted):
            candidate = dict(row)
            candidate["cycle_witnesses"] = block["cycle_witnesses"]
            candidate["constraint_tables"] = block["constraint_tables"]
            declaration = arm_b_rule(candidate)
            bad += wrong_gluing_indicator(row["gold_label"], declaration)
        draws.append(bad / n)
    draws.sort()
    q_index = max(0, int(NULL_QUANTILE * NULL_DRAWS) - 1)
    return {"q05": draws[q_index], "mean": sum(draws) / len(draws)}


# ---------------------------------------------------------------------------
# Verdict (frozen; no post-result rescue)
# ---------------------------------------------------------------------------

def verdict(report: dict[str, Any]) -> str:
    delta = report["wgr_a"] - report["wgr_b"]
    null1 = report["null_equal_n_suppression"]
    null2 = report["null_obstruction_permutation"]
    null1_beaten = bool(null1.get("applicable")) and report["wgr_b"] < null1["q05"]
    null2_beaten = report["wgr_b"] < null2["q05"]
    promote = (
        delta >= THRESH_DELTA_WGR_PROMOTE
        and report["mcnemar"]["p_two_sided"] < THRESH_MCNEMAR_P
        and report["gca_b"] >= THRESH_GCA_FLOOR
        and null1_beaten
        and null2_beaten
    )
    if promote:
        return "PROMOTE"
    negative = delta <= THRESH_DELTA_WGR_NEGATIVE or (
        bool(null1.get("applicable")) and not null1_beaten
    ) or not null2_beaten
    if negative:
        return "NEGATIVE"
    return "CONDITIONAL"


# ---------------------------------------------------------------------------
# Evaluation driver
# ---------------------------------------------------------------------------

def evaluate(corpus_path: str, arm_a_path: str, arm_b_path: str, audit_path: str,
             arm_run_started_at: str, seed: int) -> dict[str, Any]:
    corpus = load_corpus(corpus_path)
    if len(corpus) != N_EXPECTED_ATLASES:
        raise CannotCheck(
            f"corpus has {len(corpus)} atlases; protocol froze N={N_EXPECTED_ATLASES}"
        )
    assert_label_independence(corpus, arm_run_started_at)
    audit = assert_audit_receipt(audit_path)
    arm_a = load_arm(arm_a_path, corpus, "A")
    arm_b = load_arm(arm_b_path, corpus, "B")
    assert_no_rule_drift(corpus, arm_a, arm_a_rule, "A")
    assert_no_rule_drift(corpus, arm_b, arm_b_rule, "B")
    twin_bound = twin_bound_check(corpus, arm_a)

    rng = random.Random(seed)
    report: dict[str, Any] = {
        "corpus_sha256": _sha256_file(corpus_path),
        "n_atlases": len(corpus),
        "seed": seed,
        "audit": audit,
        "twin_bound": twin_bound,
        "wgr_a": wgr(corpus, arm_a),
        "wgr_b": wgr(corpus, arm_b),
        "gca_a": gca(corpus, arm_a),
        "gca_b": gca(corpus, arm_b),
        "mcnemar": mcnemar_exact(corpus, arm_a, arm_b),
        "null_equal_n_suppression": equal_n_suppression_null(corpus, arm_a, arm_b, rng),
        "null_obstruction_permutation": obstruction_permutation_null(corpus, rng),
    }
    report["delta_wgr"] = report["wgr_a"] - report["wgr_b"]
    report["verdict"] = verdict(report)
    return report


# ---------------------------------------------------------------------------
# Self-test: no-alarm world, planted-fail world, CANNOT_CHECK world,
# determinism, and the mechanized parity triangle itself.
# Synthetic fixtures only; never experiment evidence.
# ---------------------------------------------------------------------------

def _triangle(atlas_id: str, gold: str, parity: bool, twin_id: str | None,
              witness_evidence: bool = True) -> dict[str, Any]:
    """Three charts XY/YZ/XZ over variables x,y,z — the Lean construction.

    parity=False: agreement on all three overlaps (consistentCover, GLUEABLE).
    parity=True: agreement on XY/YZ, disagreement on XZ (parityCover,
    NOT_GLUEABLE). Both have identical pairwise records: every overlap
    restriction is total (parity_restrictions_are_total)."""
    agree = [[0, 0], [1, 1]]
    disagree = [[0, 1], [1, 0]]
    transitions = [
        {"left_chart": "XY", "right_chart": "YZ", "overlap_id": "y",
         "pairwise_pass": True, "fields_complete_pairwise": True,
         "overlap_restrictions": {"XY": [0, 1], "YZ": [0, 1]}},
        {"left_chart": "YZ", "right_chart": "XZ", "overlap_id": "z",
         "pairwise_pass": True, "fields_complete_pairwise": True,
         "overlap_restrictions": {"YZ": [0, 1], "XZ": [0, 1]}},
        {"left_chart": "XY", "right_chart": "XZ", "overlap_id": "x",
         "pairwise_pass": True, "fields_complete_pairwise": True,
         "overlap_restrictions": {"XY": [0, 1], "XZ": [0, 1]}},
    ]
    return {
        "atlas_id": atlas_id,
        "gold_label": gold,
        "label_minted_at": "2000-01-01T00:00:00Z",
        "charts": ["XY", "YZ", "XZ"],
        "variables": ["x", "y", "z"],
        "transitions": transitions,
        "constraint_tables": {
            "XY": {"variables": ["x", "y"], "allowed": agree},
            "YZ": {"variables": ["y", "z"], "allowed": agree},
            "XZ": {"variables": ["x", "z"], "allowed": disagree if parity else agree},
        },
        "cycle_witnesses": [
            {"cycle_id": "c0", "chart_path": ["XY", "YZ", "XZ", "XY"],
             "composition_consistent": not parity,
             "evidence_ids": ["ev0"] if witness_evidence else []},
        ],
        "twin_id": twin_id,
    }


def self_test() -> int:
    failures: list[str] = []

    parity = _triangle("st_parity", "NOT_GLUEABLE", parity=True, twin_id="st_twin")
    twin = _triangle("st_twin", "GLUEABLE", parity=False, twin_id=None)
    corpus = [parity, twin]

    # World 1 — the mechanized construction: identical pairwise records,
    # divergent global realizability; A glues both, B separates them.
    if _pairwise_record(parity) != _pairwise_record(twin):
        failures.append("parity: twin pairwise records must be identical")
    if _satisfiable(parity["variables"], parity["constraint_tables"]):
        failures.append("parity: parity cover must have no global section")
    if not _satisfiable(twin["variables"], twin["constraint_tables"]):
        failures.append("parity: consistent cover must have a global section")
    if arm_a_rule(parity) != "GLUE" or arm_a_rule(twin) != "GLUE":
        failures.append("parity: pairwise-only arm must glue both covers")
    if arm_b_rule(parity) != "REFUSE":
        failures.append("parity: obstruction arm must refuse the parity cover")
    if arm_b_rule(twin) != "GLUE":
        failures.append("parity: obstruction arm must glue the consistent cover")

    # World 2 — incomplete obstruction record: only B refuses (class G6 shape).
    incomplete = _triangle("st_inc", "GLUEABLE", parity=False, twin_id=None,
                           witness_evidence=False)
    if arm_a_rule(incomplete) != "GLUE":
        failures.append("g6: pairwise arm must not read cycle-witness fields")
    if arm_b_rule(incomplete) != "REFUSE":
        failures.append("g6: obstruction arm must fail closed on incomplete witness")

    # World 3 — no-alarm and planted-fail metrics.
    arm_a_out = {r["atlas_id"]: {"atlas_id": r["atlas_id"], "declaration": arm_a_rule(r)}
                 for r in corpus}
    arm_b_out = {r["atlas_id"]: {"atlas_id": r["atlas_id"], "declaration": arm_b_rule(r)}
                 for r in corpus}
    if wgr(corpus, arm_b_out) != 0.0:
        failures.append("no-alarm: obstruction arm WGR should be 0")
    if wgr(corpus, arm_a_out) != 0.5:
        failures.append("planted: pairwise arm WGR should be 1/2")
    if gca(corpus, arm_a_out) != 1.0 or gca(corpus, arm_b_out) != 1.0:
        failures.append("metrics: both arms should accept the solvable twin")
    mc = mcnemar_exact(corpus, arm_a_out, arm_b_out)
    if mc["b"] != 1 or mc["c"] != 0:
        failures.append(f"planted: McNemar discordants wrong: {mc}")
    silent = {r["atlas_id"]: {"atlas_id": r["atlas_id"], "declaration": "REFUSE"}
              for r in corpus}
    if wgr(corpus, silent) != 0.0 or gca(corpus, silent) != 0.0:
        failures.append("no-alarm: silence must show 0 WGR and 0 GCA (suppression visible)")

    # World 4 — twin bound: honest arm A satisfies the bound; an arm that
    # separates the twins while claiming to be pairwise-only is CANNOT_CHECK.
    try:
        result = twin_bound_check(corpus, arm_a_out)
        if result["n_twin_pairs"] != 1:
            failures.append("twin: expected exactly one twin pair")
    except CannotCheck as exc:
        failures.append(f"twin: honest pairwise arm should satisfy the bound: {exc}")
    impossible = {
        "st_parity": {"atlas_id": "st_parity", "declaration": "REFUSE"},
        "st_twin": {"atlas_id": "st_twin", "declaration": "GLUE"},
    }
    try:
        twin_bound_check(corpus, impossible)
        failures.append("twin: pairwise-impossible separation must raise CANNOT_CHECK")
    except CannotCheck:
        pass

    # World 5 — CANNOT_CHECK paths must raise, not pass.
    try:
        gca([parity], {"st_parity": {"declaration": "REFUSE"}})
        failures.append("cannot-check: zero gold GLUEABLE must raise")
    except CannotCheck:
        pass
    try:
        assert_label_independence(
            [dict(parity, label_minted_at="2030-01-01T00:00:00Z")],
            "2020-01-01T00:00:00Z",
        )
        failures.append("cannot-check: label-after-arm must raise")
    except CannotCheck:
        pass
    try:
        assert_no_rule_drift(corpus, silent, arm_a_rule, "A")
        failures.append("cannot-check: rule drift must raise")
    except CannotCheck:
        pass

    # World 6 — null 2 determinism: same seed, same distribution summary.
    n1 = obstruction_permutation_null(corpus, random.Random(7))
    n2 = obstruction_permutation_null(corpus, random.Random(7))
    if n1 != n2:
        failures.append("determinism: null 2 not seed-stable")

    if failures:
        for line in failures:
            print(f"SELFTEST FAIL: {line}", file=sys.stderr)
        return 2
    print("SELFTEST PASS: parity-construction, g6-charge, no-alarm, planted-fail, "
          "twin-bound, cannot-check, determinism")
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
