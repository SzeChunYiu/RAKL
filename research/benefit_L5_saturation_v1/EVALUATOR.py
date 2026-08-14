"""Frozen IoU/budget evaluator for benefit_L5_saturation_v1 (ladder L5-SATURATION benefit obligation).

Research-local. Frozen with PROTOCOL.json (this file's sha256 is embedded there).
Any edit after the protocol freeze invalidates the protocol hash binding and the
run must be declared CANNOT_CHECK.

Scope
-----
Computes, for a labeled known-answer retrieval-stream corpus and two arm output
files (per-world stop rounds):

  IoU_arm(i)  = |collected_relevant_at_stop ∩ F*| / |collected_relevant_at_stop ∪ F*|
                where F* is the generator-known finite relevant-fact basis
                [ladder.json L5-SATURATION observable: set-completeness IoU]
  C_arm(i)    = 1 iff F* ⊆ collected_relevant_at_stop   (completeness indicator)
  saved_B(i)  = (T_MAX - stop_B(i)) / T_MAX             [budget saved]

plus the exact one-sided binomial non-inferiority test on completeness losses,
the budget-permutation null (equal total budget, arbitrary per-world allocation),
the round-signal permutation null, the premature-stop floor on the late-complete
class, the uncertifiable-basis guard class, and the bare-flatness attribution
gate.

It emits exactly one typed verdict: PROMOTE | NEGATIVE | CONDITIONAL | CANNOT_CHECK.
CANNOT_CHECK is a distinct exit code (3) and is never conflated with a clean pass.

Exit codes: 0 = evaluated, 2 = self-test failure, 3 = CANNOT_CHECK, 4 = usage error.

Determinism: all randomness flows from the single --seed argument through
random.Random; iteration orders are sorted. No network. No non-stdlib imports.
Arm B's stop rule replicated here is decision-equivalent to
rakl.epistemic_saturation.audit_bounded_epistemic_saturation
(required_consecutive_flat_rounds=2) applied incrementally; drift between a live
arm's stop rounds and the replica is CANNOT_CHECK.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Frozen constants (mirror PROTOCOL.json; the protocol is authoritative — a
# mismatch between these and PROTOCOL.json is itself CANNOT_CHECK).
# ---------------------------------------------------------------------------
N_EXPECTED_WORLDS = 400
T_MAX = 24                      # rounds; constant across the corpus by design
REQUIRED_FLAT_ROUNDS = 2        # mirrors audit_bounded_epistemic_saturation default
NULL_DRAWS = 1000
NONINF_MARGIN = 0.05            # completeness-loss margin
THRESH_NONINF_P = 0.001
THRESH_MEAN_IOU_DEFICIT = 0.02
THRESH_MEAN_SAVINGS_PROMOTE = 0.10
THRESH_FRAC_SAVED = 0.50
THRESH_MEAN_SAVINGS_NEGATIVE = 0.02
THRESH_LATE_FLOOR = 0.70        # completeness floor on the late-complete class
THRESH_ATTRIBUTION_DELTA = 0.10  # B minus bare-flatness on the trap class
NULL_QUANTILE = 0.05
AUDIT_MAX_DISAGREEMENT = 0.05
FLOOR_CLASS = "S3"
TRAP_CLASS = "S4"
GUARD_CLASS = "S6"
GATE_KEYS = (
    "bounded_discovery_closed", "route_coverage_stable", "omission_audit_passed",
    "nearest_work_audit_passed", "operator_order_stable",
)


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


REQUIRED_ROW_KEYS = ("world_id", "class", "gold_basis", "label_minted_at", "rounds")


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
        if not row["gold_basis"]:
            raise CannotCheck(f"world {row['world_id']} has an empty relevant-fact basis")
        if len(row["rounds"]) != T_MAX:
            raise CannotCheck(
                f"world {row['world_id']} has {len(row['rounds'])} rounds; protocol froze T_MAX={T_MAX}"
            )
        for rnd in row["rounds"]:
            for key in ("new_fact_ids", "other_substantive_updates", "gates", "blocking_fibers"):
                if key not in rnd:
                    raise CannotCheck(f"world {row['world_id']} round missing {key!r}")
            for gate in GATE_KEYS:
                if gate not in rnd["gates"]:
                    raise CannotCheck(f"world {row['world_id']} round missing gate {gate!r}")
    ids = [row["world_id"] for row in worlds]
    if len(ids) != len(set(ids)):
        raise CannotCheck("duplicate world_id in corpus")
    return sorted(worlds, key=lambda row: row["world_id"])


def load_arm(path: str, corpus: list[dict[str, Any]], arm_name: str) -> dict[str, int]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CannotCheck(f"arm {arm_name} output unreadable: {exc}") from exc
    rows = payload.get("stops")
    if not isinstance(rows, list):
        raise CannotCheck(f"arm {arm_name} output has no stops list")
    by_id: dict[str, int] = {}
    for row in rows:
        stop = row.get("stop_round")
        if not isinstance(stop, int) or stop < 1 or stop > T_MAX:
            raise CannotCheck(f"arm {arm_name} stop_round {stop!r} outside [1, {T_MAX}]")
        by_id[row["world_id"]] = stop
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
# Frozen decision-equivalent arm rules (stop rounds).
# ---------------------------------------------------------------------------

def _signal_view(rounds: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """The per-round tuple the stop rule consumes: substantive growth total,
    audit gates, blocking fibers. Collection follows the true delivery
    schedule, not this view (the distinction the signal-permutation null uses)."""
    return [
        {
            "growth_total": len(rnd["new_fact_ids"]) + int(rnd["other_substantive_updates"]),
            "gates": {k: bool(rnd["gates"][k]) for k in GATE_KEYS},
            "blocking_fibers": list(rnd["blocking_fibers"]),
        }
        for rnd in rounds
    ]


def arm_a_stop(record: dict[str, Any]) -> int:
    """Budget-exhaustion stopping: always consume the full stream."""
    del record
    return T_MAX


def arm_b_stop(record: dict[str, Any], signal: list[dict[str, Any]] | None = None) -> int:
    """Saturation stopping: stop at the earliest round r >= REQUIRED_FLAT_ROUNDS
    such that the last REQUIRED_FLAT_ROUNDS rounds all have zero substantive
    growth, all audit gates true, and no blocking fibers — decision-equivalent
    to rakl.epistemic_saturation.audit_bounded_epistemic_saturation
    (required_consecutive_flat_rounds=2) returning BOUNDED_SATURATED when
    applied incrementally after each round. If never certified, run to T_MAX."""
    view = signal if signal is not None else _signal_view(record["rounds"])
    for r in range(REQUIRED_FLAT_ROUNDS, T_MAX + 1):
        window = view[r - REQUIRED_FLAT_ROUNDS:r]
        ok = all(
            item["growth_total"] == 0
            and all(item["gates"][k] for k in GATE_KEYS)
            and not item["blocking_fibers"]
            for item in window
        )
        if ok:
            return r
    return T_MAX


def bare_flatness_stop(record: dict[str, Any]) -> int:
    """Ablation for the attribution gate: stop on flat growth alone, ignoring
    the audit's gate conjuncts. Not an arm; a frozen diagnostic comparator."""
    view = _signal_view(record["rounds"])
    for r in range(REQUIRED_FLAT_ROUNDS, T_MAX + 1):
        window = view[r - REQUIRED_FLAT_ROUNDS:r]
        if all(item["growth_total"] == 0 for item in window):
            return r
    return T_MAX


def assert_no_rule_drift(corpus: list[dict[str, Any]], arm: dict[str, int],
                         rule, arm_name: str) -> None:
    drift = [
        row["world_id"] for row in corpus
        if rule(row) != arm[row["world_id"]]
    ]
    if drift:
        raise CannotCheck(
            f"arm {arm_name} stop rounds drift from the frozen decision-equivalent rule "
            f"on {len(drift)} worlds (e.g. {drift[:3]}); protocol binding broken"
        )


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def collected(record: dict[str, Any], stop_round: int) -> set[str]:
    facts: set[str] = set()
    for rnd in record["rounds"][:stop_round]:
        facts.update(rnd["new_fact_ids"])
    return facts


def iou(record: dict[str, Any], stop_round: int) -> float:
    basis = set(record["gold_basis"])
    got = collected(record, stop_round)
    union = basis | got
    if not union:
        raise CannotCheck(f"world {record['world_id']} has empty basis-union; IoU undefined")
    return len(basis & got) / len(union)


def complete(record: dict[str, Any], stop_round: int) -> bool:
    return set(record["gold_basis"]) <= collected(record, stop_round)


def completeness_rate(rows: list[dict[str, Any]], stops: dict[str, int]) -> float:
    if not rows:
        raise CannotCheck("completeness denominator is empty")
    return sum(1 for row in rows if complete(row, stops[row["world_id"]])) / len(rows)


def noninferiority_exact(corpus: list[dict[str, Any]], arm_a: dict[str, int],
                         arm_b: dict[str, int]) -> dict[str, Any]:
    """Exact one-sided binomial: b_obs = worlds where A is complete and B is not
    (no offset credit for the reverse; conservative). PROMOTE requires
    P(Binom(N, NONINF_MARGIN) <= b_obs) < THRESH_NONINF_P, i.e. the completeness
    loss is confidently below the margin."""
    n = len(corpus)
    b_obs = 0
    c_obs = 0
    for row in corpus:
        ca = complete(row, arm_a[row["world_id"]])
        cb = complete(row, arm_b[row["world_id"]])
        if ca and not cb:
            b_obs += 1
        elif cb and not ca:
            c_obs += 1
    p = sum(
        math.comb(n, i) * (NONINF_MARGIN ** i) * ((1 - NONINF_MARGIN) ** (n - i))
        for i in range(0, b_obs + 1)
    )
    return {"b": b_obs, "c": c_obs, "n": n, "p_one_sided": p,
            "loss_rate": b_obs / n}


def budget_permutation_null(corpus: list[dict[str, Any]], arm_b: dict[str, int],
                            rng: random.Random) -> dict[str, Any]:
    """Null 1 (equal-total-budget arbitrary allocation): permute arm B's own
    stop-round multiset across worlds; total consumed budget is identical by
    construction, allocation is arbitrary. Tests that B's completeness comes
    from stopping at the RIGHT time per world, not from its budget
    distribution. Beaten above the 95th percentile."""
    stops = [arm_b[row["world_id"]] for row in corpus]
    draws: list[float] = []
    for _ in range(NULL_DRAWS):
        permuted = stops[:]
        rng.shuffle(permuted)
        rate = sum(
            1 for row, stop in zip(corpus, permuted) if complete(row, stop)
        ) / len(corpus)
        draws.append(rate)
    draws.sort()
    q_index = min(len(draws) - 1, int((1 - NULL_QUANTILE) * NULL_DRAWS))
    return {"q95": draws[q_index], "mean": sum(draws) / len(draws)}


def signal_permutation_null(corpus: list[dict[str, Any]], rng: random.Random) -> dict[str, Any]:
    """Null 2 (structure permutation): permute the per-round signal view
    (growth totals + gates + fibers) across rounds within each world; re-run
    arm B's frozen stop rule on the permuted signal while collection follows
    the TRUE delivery schedule. Tests that the benefit requires genuine
    growth-signal binding rather than stopping at some base-rate time.
    Beaten above the 95th percentile."""
    draws: list[float] = []
    for _ in range(NULL_DRAWS):
        rate = 0
        for row in corpus:
            view = _signal_view(row["rounds"])
            rng.shuffle(view)
            stop = arm_b_stop(row, signal=view)
            rate += 1 if complete(row, stop) else 0
        draws.append(rate / len(corpus))
    draws.sort()
    q_index = min(len(draws) - 1, int((1 - NULL_QUANTILE) * NULL_DRAWS))
    return {"q95": draws[q_index], "mean": sum(draws) / len(draws)}


# ---------------------------------------------------------------------------
# Verdict (frozen; no post-result rescue)
# ---------------------------------------------------------------------------

def verdict(report: dict[str, Any]) -> str:
    noninf = report["noninferiority"]
    null1_beaten = report["completeness_b"] > report["null_budget_permutation"]["q95"]
    null2_beaten = report["completeness_b"] > report["null_signal_permutation"]["q95"]
    promote = (
        noninf["p_one_sided"] < THRESH_NONINF_P
        and report["mean_iou_b"] >= report["mean_iou_a"] - THRESH_MEAN_IOU_DEFICIT
        and report["mean_savings_b"] >= THRESH_MEAN_SAVINGS_PROMOTE
        and report["frac_worlds_saved_b"] >= THRESH_FRAC_SAVED
        and report["late_floor_b"] >= THRESH_LATE_FLOOR
        and report["guard_class_early_stops_b"] == 0
        and report["attribution_delta_trap"] >= THRESH_ATTRIBUTION_DELTA
        and null1_beaten
        and null2_beaten
    )
    if promote:
        return "PROMOTE"
    negative = (
        noninf["loss_rate"] >= NONINF_MARGIN
        or report["mean_savings_b"] <= THRESH_MEAN_SAVINGS_NEGATIVE
        or not null1_beaten
        or not null2_beaten
    )
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
    assert_no_rule_drift(corpus, arm_a, arm_a_stop, "A")
    assert_no_rule_drift(corpus, arm_b, arm_b_stop, "B")

    late_rows = [row for row in corpus if row["class"] == FLOOR_CLASS]
    trap_rows = [row for row in corpus if row["class"] == TRAP_CLASS]
    guard_rows = [row for row in corpus if row["class"] == GUARD_CLASS]
    for name, rows in (("S3", late_rows), ("S4", trap_rows), ("S6", guard_rows)):
        if not rows:
            raise CannotCheck(f"corpus has no {name} rows; a frozen gate is undefined")

    ious_a = [iou(row, arm_a[row["world_id"]]) for row in corpus]
    ious_b = [iou(row, arm_b[row["world_id"]]) for row in corpus]
    savings_b = [(T_MAX - arm_b[row["world_id"]]) / T_MAX for row in corpus]
    flat_stops = {row["world_id"]: bare_flatness_stop(row) for row in corpus}

    rng = random.Random(seed)
    report: dict[str, Any] = {
        "corpus_sha256": _sha256_file(corpus_path),
        "n_worlds": len(corpus),
        "seed": seed,
        "audit": audit,
        "mean_iou_a": sum(ious_a) / len(ious_a),
        "mean_iou_b": sum(ious_b) / len(ious_b),
        "completeness_a": completeness_rate(corpus, arm_a),
        "completeness_b": completeness_rate(corpus, arm_b),
        "mean_savings_b": sum(savings_b) / len(savings_b),
        "frac_worlds_saved_b": sum(1 for s in savings_b if s > 0) / len(savings_b),
        "noninferiority": noninferiority_exact(corpus, arm_a, arm_b),
        "late_floor_b": completeness_rate(late_rows, arm_b),
        "guard_class_early_stops_b": sum(
            1 for row in guard_rows if arm_b[row["world_id"]] < T_MAX
        ),
        "attribution_delta_trap": (
            completeness_rate(trap_rows, arm_b)
            - completeness_rate(trap_rows, flat_stops)
        ),
        "null_budget_permutation": budget_permutation_null(corpus, arm_b, rng),
        "null_signal_permutation": signal_permutation_null(corpus, rng),
    }
    report["verdict"] = verdict(report)
    return report


# ---------------------------------------------------------------------------
# Self-test: rule-sanity, trap/attribution, no-alarm, planted-fail,
# CANNOT_CHECK, determinism. Synthetic fixtures only; never experiment evidence.
# ---------------------------------------------------------------------------

def _round(new_facts: list[str], *, other: int = 0, gates_ok: bool = True,
           fibers: list[str] | None = None) -> dict[str, Any]:
    return {
        "new_fact_ids": new_facts,
        "other_substantive_updates": other,
        "gates": {k: gates_ok for k in GATE_KEYS},
        "blocking_fibers": fibers or [],
    }


def _world(world_id: str, klass: str, basis: list[str],
           rounds: list[dict[str, Any]]) -> dict[str, Any]:
    while len(rounds) < T_MAX:
        rounds.append(_round([]))
    return {
        "world_id": world_id,
        "class": klass,
        "gold_basis": basis,
        "label_minted_at": "2000-01-01T00:00:00Z",
        "rounds": rounds[:T_MAX],
    }


def self_test() -> int:
    failures: list[str] = []

    # Standard world: basis lands in rounds 1-2, gates true throughout.
    std = _world("v0", "S1", ["f0", "f1"], [_round(["f0"]), _round(["f1"])])
    if arm_b_stop(std) != 4:
        failures.append(f"rule: B should stop at round 4 (2 flat rounds after r2), got {arm_b_stop(std)}")
    if arm_a_stop(std) != T_MAX:
        failures.append("rule: A must consume the full budget")
    if not complete(std, 4) or iou(std, 4) != 1.0:
        failures.append("rule: B's stop should retain the full basis (IoU 1.0)")

    # Trap world (S4 semantics): interior flat pair with gates FALSE (the
    # bounded-discovery audit knows the route family is not exhausted), then
    # the last basis fact arrives. Full rule survives; bare flatness stops early.
    trap = _world("v1", "S4", ["f0", "f1"],
                  [_round(["f0"]), _round([], gates_ok=False),
                   _round([], gates_ok=False), _round(["f1"])])
    b_stop = arm_b_stop(trap)
    if not complete(trap, b_stop):
        failures.append(f"trap: full audit rule must survive the false-flat window, stop {b_stop}")
    f_stop = bare_flatness_stop(trap)
    if complete(trap, f_stop):
        failures.append(f"trap: bare flatness should stop prematurely, stop {f_stop}")

    # Guard world (S6 semantics): growth never certifiably closed - B must not stop.
    guard_rounds = [_round([f"g{i}"], gates_ok=False) for i in range(T_MAX)]
    guard = _world("v2", "S6", [f"g{i}" for i in range(T_MAX)], guard_rounds)
    if arm_b_stop(guard) != T_MAX:
        failures.append("guard: B must run to T_MAX when saturation is never certifiable")

    # No-alarm: stopping at T_MAX is always complete when the stream delivers
    # the basis; savings never come from silence (stop=1 loses the basis).
    if not complete(std, T_MAX):
        failures.append("no-alarm: full-budget stop should be complete")
    if complete(std, 1):
        failures.append("no-alarm: an absurdly early stop must be visibly incomplete")

    # Planted fail: B stopping before the basis completes is counted as a loss.
    arm_a_fix = {"v0": T_MAX}
    arm_b_bad = {"v0": 1}
    noninf = noninferiority_exact([std], arm_a_fix, arm_b_bad)
    if noninf["b"] != 1:
        failures.append(f"planted: completeness loss must be counted, got {noninf}")
    if noninf["p_one_sided"] < THRESH_NONINF_P:
        failures.append("planted: a real loss must not pass the non-inferiority test")

    # CANNOT_CHECK paths must raise, not pass.
    try:
        load_corpus_rows = [dict(std, rounds=std["rounds"][:3])]
        for row in load_corpus_rows:
            if len(row["rounds"]) != T_MAX:
                raise CannotCheck("short world")
        failures.append("cannot-check: short round list must raise")
    except CannotCheck:
        pass
    try:
        assert_label_independence(
            [dict(std, label_minted_at="2030-01-01T00:00:00Z")], "2020-01-01T00:00:00Z")
        failures.append("cannot-check: label-after-arm must raise")
    except CannotCheck:
        pass
    try:
        assert_no_rule_drift([std], {"v0": 7}, arm_b_stop, "B")
        failures.append("cannot-check: rule drift must raise")
    except CannotCheck:
        pass
    try:
        completeness_rate([], {})
        failures.append("cannot-check: empty denominator must raise")
    except CannotCheck:
        pass

    # Determinism: nulls are seed-stable.
    corpus = [std, trap]
    stops_b = {row["world_id"]: arm_b_stop(row) for row in corpus}
    n1a = budget_permutation_null(corpus, stops_b, random.Random(7))
    n1b = budget_permutation_null(corpus, stops_b, random.Random(7))
    if n1a != n1b:
        failures.append("determinism: budget-permutation null not seed-stable")
    n2a = signal_permutation_null(corpus, random.Random(7))
    n2b = signal_permutation_null(corpus, random.Random(7))
    if n2a != n2b:
        failures.append("determinism: signal-permutation null not seed-stable")

    if failures:
        for line in failures:
            print(f"SELFTEST FAIL: {line}", file=sys.stderr)
        return 2
    print("SELFTEST PASS: rule-sanity, trap-attribution, guard, no-alarm, "
          "planted-fail, cannot-check, determinism")
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
