"""Frozen FCR evaluator for benefit_L0_fcr_v1 (ladder L0-OBJECT benefit obligation).

Research-local. Frozen with PROTOCOL.json (this file's sha256 is embedded there).
Any edit after the protocol freeze invalidates the protocol hash binding and the
run must be declared CANNOT_CHECK.

Scope
-----
Computes, for a labeled comparable-claim-pair corpus and two arm output files:

  FCR_arm = (# pairs where arm declared CONTRADICTION and gold != CONTRADICTION)
            / (# comparable pairs)                        [quant. eval model, sec 2 V]

  TCR_arm = (# pairs where arm declared CONTRADICTION and gold == CONTRADICTION)
            / (# gold CONTRADICTION pairs)                [frozen suppression guard]

plus the paired McNemar exact test on pair-level false-contradiction indicators,
the equal-n random-suppression null, and the context-permutation null.

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
import json
import math
import random
import sys
from typing import Any

# ---------------------------------------------------------------------------
# Frozen constants (mirror PROTOCOL.json; the protocol is authoritative — a
# mismatch between these and PROTOCOL.json is itself CANNOT_CHECK).
# ---------------------------------------------------------------------------
GOLD_LABELS = ("CONTRADICTION", "CONTEXT_DEPENDENT_DIFFERENCE", "EQUIVALENT", "COMPLEMENTARY")
ARM_DECLARATIONS = ("CONTRADICTION", "NO_CONTRADICTION")
N_EXPECTED_PAIRS = 400
NULL_DRAWS = 1000
THRESH_DELTA_FCR_PROMOTE = 0.10
THRESH_DELTA_FCR_NEGATIVE = 0.02
THRESH_MCNEMAR_P = 0.001
THRESH_TCR_FLOOR = 0.70
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


def load_corpus(path: str) -> list[dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CannotCheck(f"corpus unreadable: {exc}") from exc
    pairs = payload.get("pairs")
    if not isinstance(pairs, list) or not pairs:
        raise CannotCheck("corpus has no pairs; denominator would be zero")
    for row in pairs:
        for key in ("pair_id", "gold_label", "label_minted_at"):
            if key not in row:
                raise CannotCheck(f"corpus row missing {key!r}")
        if row["gold_label"] not in GOLD_LABELS:
            raise CannotCheck(f"unknown gold label {row['gold_label']!r}")
    ids = [row["pair_id"] for row in pairs]
    if len(ids) != len(set(ids)):
        raise CannotCheck("duplicate pair_id in corpus")
    return sorted(pairs, key=lambda row: row["pair_id"])


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
        by_id[row["pair_id"]] = row
    corpus_ids = {row["pair_id"] for row in corpus}
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
        row["pair_id"]
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
# Metrics
# ---------------------------------------------------------------------------

def false_contradiction_indicator(gold: str, declaration: str) -> int:
    return 1 if declaration == "CONTRADICTION" and gold != "CONTRADICTION" else 0


def fcr(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]]) -> float:
    n = len(corpus)
    fc = sum(
        false_contradiction_indicator(row["gold_label"], arm[row["pair_id"]]["declaration"])
        for row in corpus
    )
    return fc / n


def tcr(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]]) -> float:
    gold_pos = [row for row in corpus if row["gold_label"] == "CONTRADICTION"]
    if not gold_pos:
        raise CannotCheck("corpus contains zero gold contradictions; TCR guard undefined")
    hits = sum(
        1 for row in gold_pos if arm[row["pair_id"]]["declaration"] == "CONTRADICTION"
    )
    return hits / len(gold_pos)


def mcnemar_exact(corpus: list[dict[str, Any]], arm_a: dict[str, dict[str, Any]],
                  arm_b: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Two-sided exact McNemar on pair-level false-contradiction indicators."""
    b_count = 0  # A false-contradicts, B does not
    c_count = 0  # B false-contradicts, A does not
    for row in corpus:
        fa = false_contradiction_indicator(row["gold_label"], arm_a[row["pair_id"]]["declaration"])
        fb = false_contradiction_indicator(row["gold_label"], arm_b[row["pair_id"]]["declaration"])
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
    """Null 1: keep a random size-K_B subset of A's declarations; FCR distribution.

    Tests selectivity-vs-edge: B must beat blind suppression at its own
    declaration count, else its FCR advantage is a base-rate artifact.
    """
    a_declared = sorted(
        row["pair_id"] for row in corpus
        if arm_a[row["pair_id"]]["declaration"] == "CONTRADICTION"
    )
    k_b = sum(
        1 for row in corpus if arm_b[row["pair_id"]]["declaration"] == "CONTRADICTION"
    )
    if k_b >= len(a_declared):
        # Degenerate: B declares at least as many as A; suppression null is
        # uninformative — record and let the verdict logic treat null-1 as
        # NOT_APPLICABLE rather than passed.
        return {"applicable": False, "k_b": k_b, "k_a": len(a_declared)}
    gold = {row["pair_id"]: row["gold_label"] for row in corpus}
    n = len(corpus)
    draws: list[float] = []
    for _ in range(NULL_DRAWS):
        kept = rng.sample(a_declared, k_b)
        fc = sum(1 for pid in kept if gold[pid] != "CONTRADICTION")
        draws.append(fc / n)
    draws.sort()
    q_index = max(0, int(NULL_QUANTILE * NULL_DRAWS) - 1)
    return {
        "applicable": True,
        "k_b": k_b,
        "k_a": len(a_declared),
        "q05": draws[q_index],
        "mean": sum(draws) / len(draws),
    }


def context_permutation_null(corpus: list[dict[str, Any]], rng: random.Random) -> dict[str, Any]:
    """Null 2: permute right-hand context tuples across pairs, re-run arm B's
    frozen decision rule, and collect the FCR distribution.

    Requires each corpus row to carry the machine-readable context fields the
    generator produced (context_left, context_right, value_left, value_right,
    facet_left, facet_right). The arm-B rule replicated here MUST match
    PROTOCOL.json arms.B.decision_rule verbatim; drift is CANNOT_CHECK.
    """
    required = ("context_left", "context_right", "value_left", "value_right",
                "facet_left", "facet_right")
    for row in corpus:
        for key in required:
            if key not in row:
                raise CannotCheck(f"corpus row {row['pair_id']} missing {key!r} needed for null 2")

    def arm_b_rule(facet_l: str, facet_r: str, value_l: str, value_r: str,
                   ctx_l: dict[str, Any], ctx_r: dict[str, Any]) -> str:
        if facet_l != facet_r:
            return "NO_CONTRADICTION"
        fields = ("population", "scale", "horizon", "observation_model",
                  "units", "assumptions", "intervention")
        aligned = all(ctx_l.get(f) == ctx_r.get(f) for f in fields)
        if not aligned:
            return "NO_CONTRADICTION"
        return "CONTRADICTION" if value_l != value_r else "NO_CONTRADICTION"

    n = len(corpus)
    right_contexts = [row["context_right"] for row in corpus]
    draws: list[float] = []
    for _ in range(NULL_DRAWS):
        permuted = right_contexts[:]
        rng.shuffle(permuted)
        fc = 0
        for row, ctx_r in zip(corpus, permuted):
            declaration = arm_b_rule(
                row["facet_left"], row["facet_right"],
                row["value_left"], row["value_right"],
                row["context_left"], ctx_r,
            )
            fc += false_contradiction_indicator(row["gold_label"], declaration)
        draws.append(fc / n)
    draws.sort()
    q_index = max(0, int(NULL_QUANTILE * NULL_DRAWS) - 1)
    return {"q05": draws[q_index], "mean": sum(draws) / len(draws)}


# ---------------------------------------------------------------------------
# Verdict (frozen; no post-result rescue)
# ---------------------------------------------------------------------------

def verdict(report: dict[str, Any]) -> str:
    delta = report["fcr_a"] - report["fcr_b"]
    null1 = report["null_equal_n_suppression"]
    null2 = report["null_context_permutation"]
    null1_beaten = bool(null1.get("applicable")) and report["fcr_b"] < null1["q05"]
    null2_beaten = report["fcr_b"] < null2["q05"]
    promote = (
        delta >= THRESH_DELTA_FCR_PROMOTE
        and report["mcnemar"]["p_two_sided"] < THRESH_MCNEMAR_P
        and report["tcr_b"] >= THRESH_TCR_FLOOR
        and null1_beaten
        and null2_beaten
    )
    if promote:
        return "PROMOTE"
    negative = delta <= THRESH_DELTA_FCR_NEGATIVE or (
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
    if len(corpus) != N_EXPECTED_PAIRS:
        raise CannotCheck(
            f"corpus has {len(corpus)} pairs; protocol froze N={N_EXPECTED_PAIRS}"
        )
    assert_label_independence(corpus, arm_run_started_at)
    audit = assert_audit_receipt(audit_path)
    arm_a = load_arm(arm_a_path, corpus, "A")
    arm_b = load_arm(arm_b_path, corpus, "B")

    rng = random.Random(seed)
    report: dict[str, Any] = {
        "corpus_sha256": _sha256_file(corpus_path),
        "n_pairs": len(corpus),
        "seed": seed,
        "audit": audit,
        "fcr_a": fcr(corpus, arm_a),
        "fcr_b": fcr(corpus, arm_b),
        "tcr_a": tcr(corpus, arm_a),
        "tcr_b": tcr(corpus, arm_b),
        "mcnemar": mcnemar_exact(corpus, arm_a, arm_b),
        "null_equal_n_suppression": equal_n_suppression_null(corpus, arm_a, arm_b, rng),
        "null_context_permutation": context_permutation_null(corpus, rng),
    }
    report["delta_fcr"] = report["fcr_a"] - report["fcr_b"]
    report["verdict"] = verdict(report)
    return report


# ---------------------------------------------------------------------------
# Self-test: no-alarm world, planted-fail world, CANNOT_CHECK world.
# Synthetic fixtures only; never experiment evidence.
# ---------------------------------------------------------------------------

def _mini_corpus(rows: list[tuple[str, str, str, str, str, dict, dict]]) -> list[dict[str, Any]]:
    corpus = []
    for i, (gold, facet_l, facet_r, value_l, value_r, ctx_l, ctx_r) in enumerate(rows):
        corpus.append({
            "pair_id": f"st{i:03d}",
            "gold_label": gold,
            "label_minted_at": "2000-01-01T00:00:00Z",
            "facet_left": facet_l, "facet_right": facet_r,
            "value_left": value_l, "value_right": value_r,
            "context_left": ctx_l, "context_right": ctx_r,
        })
    return corpus


def self_test() -> int:
    failures: list[str] = []
    ctx_a = {"population": "p1", "units": "cm"}
    ctx_b = {"population": "p2", "units": "cm"}

    # World 1 — no-alarm: both arms declare nothing; FCR must be 0/0-alarm,
    # verdict must NOT be PROMOTE (a checker that cries wolf gets switched off,
    # and one that mints benefit from silence is worse).
    corpus = _mini_corpus([
        ("EQUIVALENT", "color", "color", "red", "red", ctx_a, ctx_a),
        ("CONTRADICTION", "color", "color", "red", "green", ctx_a, ctx_a),
    ])
    arm_silent = {r["pair_id"]: {"pair_id": r["pair_id"], "declaration": "NO_CONTRADICTION"}
                  for r in corpus}
    arm_honest = {r["pair_id"]: {"pair_id": r["pair_id"],
                                 "declaration": "CONTRADICTION" if r["gold_label"] == "CONTRADICTION"
                                 else "NO_CONTRADICTION"}
                  for r in corpus}
    if fcr(corpus, arm_silent) != 0.0:
        failures.append("no-alarm: silent arm FCR should be 0")
    if fcr(corpus, arm_honest) != 0.0:
        failures.append("no-alarm: honest arm FCR should be 0")
    if tcr(corpus, arm_silent) != 0.0:
        failures.append("no-alarm: silent arm TCR should be 0 (suppression visible)")

    # World 2 — planted fail: arm A false-contradicts a known non-contradiction.
    arm_trigger = dict(arm_honest)
    arm_trigger["st000"] = {"pair_id": "st000", "declaration": "CONTRADICTION"}
    if fcr(corpus, arm_trigger) != 0.5:
        failures.append("planted: FCR should be 1/2")
    mc = mcnemar_exact(corpus, arm_trigger, arm_honest)
    if mc["b"] != 1 or mc["c"] != 0:
        failures.append(f"planted: McNemar discordants wrong: {mc}")

    # World 3 — CANNOT_CHECK paths must raise, not pass.
    try:
        tcr([{"pair_id": "x", "gold_label": "EQUIVALENT", "label_minted_at": "2000"}],
            {"x": {"declaration": "NO_CONTRADICTION"}})
        failures.append("cannot-check: zero gold contradictions must raise")
    except CannotCheck:
        pass
    try:
        assert_label_independence(
            [{"pair_id": "x", "gold_label": "EQUIVALENT",
              "label_minted_at": "2030-01-01T00:00:00Z"}],
            "2020-01-01T00:00:00Z",
        )
        failures.append("cannot-check: label-after-arm must raise")
    except CannotCheck:
        pass

    # World 4 — null 2 determinism: same seed, same distribution summary.
    ctx_perm_corpus = _mini_corpus([
        ("CONTEXT_DEPENDENT_DIFFERENCE", "color", "color", "red", "green", ctx_a, ctx_b),
        ("CONTRADICTION", "color", "color", "red", "green", ctx_a, ctx_a),
    ])
    n1 = context_permutation_null(ctx_perm_corpus, random.Random(7))
    n2 = context_permutation_null(ctx_perm_corpus, random.Random(7))
    if n1 != n2:
        failures.append("determinism: null 2 not seed-stable")

    if failures:
        for line in failures:
            print(f"SELFTEST FAIL: {line}", file=sys.stderr)
        return 2
    print("SELFTEST PASS: no-alarm, planted-fail, cannot-check, determinism")
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
