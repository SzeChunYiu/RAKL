"""Frozen UCR evaluator for benefit_L1_composition_v1 (ladder L1-TRANSITION benefit obligation).

Research-local. Frozen with PROTOCOL.json (this file's sha256 is embedded there).
Any edit after the protocol freeze invalidates the protocol hash binding and the
run must be declared CANNOT_CHECK.

Scope
-----
Computes, for a labeled known-answer composition-chain corpus and two arm output files:

  UCR_arm = (# chains where arm declared COMPOSED and gold == UNSUPPORTED)
            / (# chains)                       [ladder.json L1-TRANSITION observable]

  VCA_arm = (# chains where arm declared COMPOSED and gold == SUPPORTED)
            / (# gold SUPPORTED chains)        [frozen over-refusal guard]

plus the paired McNemar exact test on chain-level unsupported-composition
indicators, the equal-n random-suppression null, and the contract-permutation
null (stratified by hop count).

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
GOLD_LABELS = ("SUPPORTED", "UNSUPPORTED")
ARM_DECLARATIONS = ("COMPOSED", "REFUSED")
N_EXPECTED_CHAINS = 400
NULL_DRAWS = 1000
THRESH_DELTA_UCR_PROMOTE = 0.10
THRESH_DELTA_UCR_NEGATIVE = 0.02
THRESH_MCNEMAR_P = 0.001
THRESH_VCA_FLOOR = 0.70
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


REQUIRED_ROW_KEYS = ("chain_id", "gold_label", "label_minted_at", "skeleton", "contract")


def load_corpus(path: str) -> list[dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CannotCheck(f"corpus unreadable: {exc}") from exc
    chains = payload.get("chains")
    if not isinstance(chains, list) or not chains:
        raise CannotCheck("corpus has no chains; denominator would be zero")
    for row in chains:
        for key in REQUIRED_ROW_KEYS:
            if key not in row:
                raise CannotCheck(f"corpus row missing {key!r}")
        if row["gold_label"] not in GOLD_LABELS:
            raise CannotCheck(f"unknown gold label {row['gold_label']!r}")
        if not isinstance(row["skeleton"], list) or len(row["skeleton"]) < 2:
            raise CannotCheck(f"chain {row['chain_id']} skeleton must list >= 2 hops")
    ids = [row["chain_id"] for row in chains]
    if len(ids) != len(set(ids)):
        raise CannotCheck("duplicate chain_id in corpus")
    return sorted(chains, key=lambda row: row["chain_id"])


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
        by_id[row["chain_id"]] = row
    corpus_ids = {row["chain_id"] for row in corpus}
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
        row["chain_id"]
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
# Frozen decision-equivalent arm rules.
#
# arm_a_rule / arm_b_rule MUST match PROTOCOL.json arms.{A,B}.definition
# verbatim; drift between an arm's live declarations on the real corpus and
# the replicated rule here is CANNOT_CHECK (enforced in evaluate()).
# ---------------------------------------------------------------------------

def arm_a_rule(skeleton: list[dict[str, Any]], contract: dict[str, Any]) -> str:
    """Untyped chaining: COMPOSED iff endpoint identifiers connect syntactically.

    The contract block is present in the input record and deliberately ignored.
    """
    del contract
    for i in range(len(skeleton) - 1):
        if skeleton[i]["target_id"] != skeleton[i + 1]["source_id"]:
            return "REFUSED"
    return "COMPOSED"


def arm_b_rule(skeleton: list[dict[str, Any]], contract: dict[str, Any]) -> str:
    """Typed transition algebra: the six licensing conditions of
    FORMAL_SYSTEM_SPECIFICATION.md section 4, decision-equivalent to
    rakl.bridge_composition.evaluate_bridge_path returning
    COMPOSABLE_TRANSFER_HYPOTHESIS_ONLY (COMPOSED) versus any other verdict
    (REFUSED). Fail-closed: an incomplete record is REFUSED, never assumed."""
    n = len(skeleton)
    per_hop = contract.get("per_hop")
    handoffs = contract.get("handoffs")
    if not isinstance(per_hop, list) or len(per_hop) != n:
        return "REFUSED"
    if not isinstance(handoffs, list) or len(handoffs) != n - 1:
        return "REFUSED"
    # 1. interface match + invariant/role handoffs
    for i in range(n - 1):
        if skeleton[i]["target_id"] != skeleton[i + 1]["source_id"]:
            return "REFUSED"
        h = handoffs[i]
        if h.get("junction_id") != skeleton[i]["target_id"]:
            return "REFUSED"
        delivered = set(h.get("roles_delivered", ()))
        consumed = set(h.get("roles_consumed", ()))
        if not consumed or not consumed <= delivered:
            return "REFUSED"
        if h.get("compatibility_passed") is not True:
            return "REFUSED"
    # 2. relation licensing via declared end-to-end invariants: mixed weaker
    # relations cannot silently mint a stronger relation.
    invariants = contract.get("claimed_invariants") or ()
    if not invariants:
        return "REFUSED"  # navigable-only, not a licensed composition
    for hop in per_hop:
        preserved = set(hop.get("preserved", ()))
        broken = set(hop.get("not_preserved", ()))
        for inv in invariants:
            if inv in broken or inv not in preserved:
                return "REFUSED"
    # 3. global scope intersection non-empty
    regime = set(per_hop[0].get("regime", ()))
    for hop in per_hop[1:]:
        regime.intersection_update(hop.get("regime", ()))
    if not regime:
        return "REFUSED"
    # 5. evidence lineage traceable
    if any(not hop.get("evidence_lineage_ids") for hop in per_hop):
        return "REFUSED"
    # 6. declared error composition rule, matching semantics, within tolerance
    rule = contract.get("error_composition_rule") or {}
    if not rule.get("rule_id") or not rule.get("error_semantics_id"):
        return "REFUSED"
    if rule.get("kind") != "ADDITIVE_UPPER_BOUND":
        return "REFUSED"
    tolerance = contract.get("max_accumulated_error")
    if tolerance is None or tolerance < 0:
        return "REFUSED"
    total = 0.0
    for hop in per_hop:
        bound = hop.get("error_bound")
        if bound is None or bound < 0:
            return "REFUSED"
        if hop.get("error_semantics_id") != rule["error_semantics_id"]:
            return "REFUSED"
        total += bound
    if total > tolerance:
        return "REFUSED"
    return "COMPOSED"


def assert_no_rule_drift(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]],
                         rule, arm_name: str) -> None:
    drift = [
        row["chain_id"] for row in corpus
        if rule(row["skeleton"], row["contract"]) != arm[row["chain_id"]]["declaration"]
    ]
    if drift:
        raise CannotCheck(
            f"arm {arm_name} declarations drift from the frozen decision-equivalent rule "
            f"on {len(drift)} chains (e.g. {drift[:3]}); protocol binding broken"
        )


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def unsupported_composition_indicator(gold: str, declaration: str) -> int:
    return 1 if declaration == "COMPOSED" and gold == "UNSUPPORTED" else 0


def ucr(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]]) -> float:
    n = len(corpus)
    bad = sum(
        unsupported_composition_indicator(row["gold_label"], arm[row["chain_id"]]["declaration"])
        for row in corpus
    )
    return bad / n


def vca(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]]) -> float:
    gold_pos = [row for row in corpus if row["gold_label"] == "SUPPORTED"]
    if not gold_pos:
        raise CannotCheck("corpus contains zero gold SUPPORTED chains; VCA guard undefined")
    hits = sum(
        1 for row in gold_pos if arm[row["chain_id"]]["declaration"] == "COMPOSED"
    )
    return hits / len(gold_pos)


def mcnemar_exact(corpus: list[dict[str, Any]], arm_a: dict[str, dict[str, Any]],
                  arm_b: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Two-sided exact McNemar on chain-level unsupported-composition indicators."""
    b_count = 0  # A composes unsupported, B does not
    c_count = 0  # B composes unsupported, A does not
    for row in corpus:
        fa = unsupported_composition_indicator(
            row["gold_label"], arm_a[row["chain_id"]]["declaration"])
        fb = unsupported_composition_indicator(
            row["gold_label"], arm_b[row["chain_id"]]["declaration"])
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
    """Null 1: keep a random size-K_B subset of A's COMPOSED declarations; UCR distribution.

    Tests selectivity-vs-edge: B must beat blind refusal at its own acceptance
    count, else its UCR advantage is a base-rate artifact.
    """
    a_composed = sorted(
        row["chain_id"] for row in corpus
        if arm_a[row["chain_id"]]["declaration"] == "COMPOSED"
    )
    k_b = sum(
        1 for row in corpus if arm_b[row["chain_id"]]["declaration"] == "COMPOSED"
    )
    if k_b >= len(a_composed):
        # Degenerate: B composes at least as many as A; suppression null is
        # uninformative — record and let the verdict logic treat null-1 as
        # NOT_APPLICABLE rather than passed.
        return {"applicable": False, "k_b": k_b, "k_a": len(a_composed)}
    gold = {row["chain_id"]: row["gold_label"] for row in corpus}
    n = len(corpus)
    draws: list[float] = []
    for _ in range(NULL_DRAWS):
        kept = rng.sample(a_composed, k_b)
        bad = sum(1 for cid in kept if gold[cid] == "UNSUPPORTED")
        draws.append(bad / n)
    draws.sort()
    q_index = max(0, int(NULL_QUANTILE * NULL_DRAWS) - 1)
    return {
        "applicable": True,
        "k_b": k_b,
        "k_a": len(a_composed),
        "q05": draws[q_index],
        "mean": sum(draws) / len(draws),
    }


def contract_permutation_null(corpus: list[dict[str, Any]], rng: random.Random) -> dict[str, Any]:
    """Null 2: permute contract blocks across chains with equal hop count,
    re-run arm B's frozen decision-equivalent rule, collect the UCR distribution.

    Tests that B's advantage requires genuine chain-contract binding rather
    than refusing at some base rate. Skeletons (and hence junction identities)
    stay with their chains; only licensing content moves.
    """
    strata: dict[int, list[int]] = {}
    for idx, row in enumerate(corpus):
        strata.setdefault(len(row["skeleton"]), []).append(idx)
    n = len(corpus)
    draws: list[float] = []
    contracts = [row["contract"] for row in corpus]
    for _ in range(NULL_DRAWS):
        permuted: list[dict[str, Any]] = list(contracts)
        for indices in strata.values():
            shuffled = indices[:]
            rng.shuffle(shuffled)
            for src, dst in zip(indices, shuffled):
                permuted[dst] = contracts[src]
        bad = 0
        for row, contract in zip(corpus, permuted):
            declaration = arm_b_rule(row["skeleton"], contract)
            bad += unsupported_composition_indicator(row["gold_label"], declaration)
        draws.append(bad / n)
    draws.sort()
    q_index = max(0, int(NULL_QUANTILE * NULL_DRAWS) - 1)
    return {"q05": draws[q_index], "mean": sum(draws) / len(draws)}


# ---------------------------------------------------------------------------
# Verdict (frozen; no post-result rescue)
# ---------------------------------------------------------------------------

def verdict(report: dict[str, Any]) -> str:
    delta = report["ucr_a"] - report["ucr_b"]
    null1 = report["null_equal_n_suppression"]
    null2 = report["null_contract_permutation"]
    null1_beaten = bool(null1.get("applicable")) and report["ucr_b"] < null1["q05"]
    null2_beaten = report["ucr_b"] < null2["q05"]
    promote = (
        delta >= THRESH_DELTA_UCR_PROMOTE
        and report["mcnemar"]["p_two_sided"] < THRESH_MCNEMAR_P
        and report["vca_b"] >= THRESH_VCA_FLOOR
        and null1_beaten
        and null2_beaten
    )
    if promote:
        return "PROMOTE"
    negative = delta <= THRESH_DELTA_UCR_NEGATIVE or (
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
    if len(corpus) != N_EXPECTED_CHAINS:
        raise CannotCheck(
            f"corpus has {len(corpus)} chains; protocol froze N={N_EXPECTED_CHAINS}"
        )
    assert_label_independence(corpus, arm_run_started_at)
    audit = assert_audit_receipt(audit_path)
    arm_a = load_arm(arm_a_path, corpus, "A")
    arm_b = load_arm(arm_b_path, corpus, "B")
    assert_no_rule_drift(corpus, arm_a, arm_a_rule, "A")
    assert_no_rule_drift(corpus, arm_b, arm_b_rule, "B")

    rng = random.Random(seed)
    report: dict[str, Any] = {
        "corpus_sha256": _sha256_file(corpus_path),
        "n_chains": len(corpus),
        "seed": seed,
        "audit": audit,
        "ucr_a": ucr(corpus, arm_a),
        "ucr_b": ucr(corpus, arm_b),
        "vca_a": vca(corpus, arm_a),
        "vca_b": vca(corpus, arm_b),
        "mcnemar": mcnemar_exact(corpus, arm_a, arm_b),
        "null_equal_n_suppression": equal_n_suppression_null(corpus, arm_a, arm_b, rng),
        "null_contract_permutation": contract_permutation_null(corpus, rng),
    }
    report["delta_ucr"] = report["ucr_a"] - report["ucr_b"]
    report["verdict"] = verdict(report)
    return report


# ---------------------------------------------------------------------------
# Self-test: no-alarm world, planted-fail world, CANNOT_CHECK world,
# determinism. Synthetic fixtures only; never experiment evidence.
# ---------------------------------------------------------------------------

def _chain(chain_id: str, gold: str, skeleton: list[tuple[str, str]],
           contract: dict[str, Any]) -> dict[str, Any]:
    return {
        "chain_id": chain_id,
        "gold_label": gold,
        "label_minted_at": "2000-01-01T00:00:00Z",
        "skeleton": [{"source_id": s, "target_id": t} for s, t in skeleton],
        "contract": contract,
    }


def _good_contract(n_hops: int) -> dict[str, Any]:
    return {
        "per_hop": [
            {
                "regime": ["r1"],
                "preserved": ["inv1"],
                "not_preserved": [],
                "evidence_lineage_ids": [f"ev{i}"],
                "error_bound": 0.01,
                "error_semantics_id": "abs",
            }
            for i in range(n_hops)
        ],
        "handoffs": [
            {
                "junction_id": f"o{i + 1}",
                "roles_delivered": ["role1"],
                "roles_consumed": ["role1"],
                "compatibility_passed": True,
            }
            for i in range(n_hops - 1)
        ],
        "claimed_invariants": ["inv1"],
        "max_accumulated_error": 1.0,
        "error_composition_rule": {
            "rule_id": "rule1", "error_semantics_id": "abs", "kind": "ADDITIVE_UPPER_BOUND",
        },
    }


def self_test() -> int:
    failures: list[str] = []
    skeleton2 = [("o0", "o1"), ("o1", "o2")]

    good = _good_contract(2)
    broken = json.loads(json.dumps(good))
    broken["per_hop"][1]["not_preserved"] = ["inv1"]
    broken["per_hop"][1]["preserved"] = []

    corpus = [
        _chain("st000", "SUPPORTED", skeleton2, good),
        _chain("st001", "UNSUPPORTED", skeleton2, broken),
    ]

    # World 1 — rule sanity: A composes both (connectivity only); B composes the
    # supported chain and refuses the invariant-broken one.
    if arm_a_rule(corpus[0]["skeleton"], corpus[0]["contract"]) != "COMPOSED":
        failures.append("rule: arm A should compose a connected chain")
    if arm_a_rule(corpus[1]["skeleton"], corpus[1]["contract"]) != "COMPOSED":
        failures.append("rule: arm A ignores contracts and should compose")
    if arm_b_rule(corpus[0]["skeleton"], corpus[0]["contract"]) != "COMPOSED":
        failures.append("rule: arm B should compose a fully licensed chain")
    if arm_b_rule(corpus[1]["skeleton"], corpus[1]["contract"]) != "REFUSED":
        failures.append("rule: arm B should refuse a broken-invariant chain")
    disconnected = [("o0", "o1"), ("oX", "o2")]
    if arm_a_rule([{"source_id": s, "target_id": t} for s, t in disconnected], good) != "REFUSED":
        failures.append("rule: arm A should refuse a syntactically disconnected chain")

    # World 2 — no-alarm: honest arms produce zero UCR; a silent arm's
    # suppression is visible in VCA, and silence never mints benefit.
    arm_silent = {r["chain_id"]: {"chain_id": r["chain_id"], "declaration": "REFUSED"}
                  for r in corpus}
    arm_honest = {r["chain_id"]: {"chain_id": r["chain_id"],
                                  "declaration": "COMPOSED" if r["gold_label"] == "SUPPORTED"
                                  else "REFUSED"}
                  for r in corpus}
    if ucr(corpus, arm_silent) != 0.0:
        failures.append("no-alarm: silent arm UCR should be 0")
    if ucr(corpus, arm_honest) != 0.0:
        failures.append("no-alarm: honest arm UCR should be 0")
    if vca(corpus, arm_silent) != 0.0:
        failures.append("no-alarm: silent arm VCA should be 0 (over-refusal visible)")

    # World 3 — planted fail: an arm composes a known-unsupported chain.
    arm_trigger = dict(arm_honest)
    arm_trigger["st001"] = {"chain_id": "st001", "declaration": "COMPOSED"}
    if ucr(corpus, arm_trigger) != 0.5:
        failures.append("planted: UCR should be 1/2")
    mc = mcnemar_exact(corpus, arm_trigger, arm_honest)
    if mc["b"] != 1 or mc["c"] != 0:
        failures.append(f"planted: McNemar discordants wrong: {mc}")

    # World 4 — CANNOT_CHECK paths must raise, not pass.
    try:
        vca([_chain("x", "UNSUPPORTED", skeleton2, broken)],
            {"x": {"declaration": "REFUSED"}})
        failures.append("cannot-check: zero gold SUPPORTED must raise")
    except CannotCheck:
        pass
    try:
        assert_label_independence(
            [_chain("x", "SUPPORTED", skeleton2, good) | {"label_minted_at": "2030-01-01T00:00:00Z"}],
            "2020-01-01T00:00:00Z",
        )
        failures.append("cannot-check: label-after-arm must raise")
    except CannotCheck:
        pass
    try:
        assert_no_rule_drift(corpus, arm_silent, arm_a_rule, "A")
        failures.append("cannot-check: rule drift must raise")
    except CannotCheck:
        pass

    # World 5 — null 2 determinism: same seed, same distribution summary.
    n1 = contract_permutation_null(corpus, random.Random(7))
    n2 = contract_permutation_null(corpus, random.Random(7))
    if n1 != n2:
        failures.append("determinism: null 2 not seed-stable")

    if failures:
        for line in failures:
            print(f"SELFTEST FAIL: {line}", file=sys.stderr)
        return 2
    print("SELFTEST PASS: rule-sanity, no-alarm, planted-fail, cannot-check, determinism")
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
