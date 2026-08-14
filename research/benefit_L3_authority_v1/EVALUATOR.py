"""Frozen ALR evaluator for benefit_L3_authority_v1 (ladder L3-AUTHORITY benefit obligation).

Research-local. Frozen with PROTOCOL.json (this file's sha256 is embedded there).
Any edit after the protocol freeze invalidates the protocol hash binding and the
run must be declared CANNOT_CHECK.

Scope
-----
Computes, for a labeled known-answer authority-upgrade corpus and two arm output files:

  ALR_arm = (# claims where arm declared UPGRADE and gold == UNSUPPORTED)
            / (# claims)                       [ladder.json L3-AUTHORITY observable: ALR]

  VUA_arm = (# claims where arm declared UPGRADE and gold == SUPPORTED)
            / (# gold SUPPORTED claims)        [frozen over-refusal guard]

plus the paired McNemar exact test on claim-level unsupported-upgrade indicators,
the equal-n random-suppression null, and the evidence-record-permutation null
(stratified by binding arity).

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
ARM_DECLARATIONS = ("UPGRADE", "REFUSED")
N_EXPECTED_CLAIMS = 400
NULL_DRAWS = 1000
THRESH_DELTA_ALR_PROMOTE = 0.10
THRESH_DELTA_ALR_NEGATIVE = 0.02
THRESH_MCNEMAR_P = 0.001
THRESH_VUA_FLOOR = 0.70
NULL_QUANTILE = 0.05
AUDIT_MAX_DISAGREEMENT = 0.05

SCIENTIFIC_KINDS = ("EXTERNAL_OBSERVATION", "DERIVED_REPORT")
SUPPORT_VERDICT = "REVIEWED_SUPPORT_PROPOSAL_ONLY"
REFUTE_VERDICT = "REVIEWED_REFUTATION_PROPOSAL_ONLY"
CONTEXT_VERDICT = "REVIEWED_CONTEXT_PROPOSAL_ONLY"
RELATION_BY_VERDICT = {
    SUPPORT_VERDICT: "SUPPORTS",
    REFUTE_VERDICT: "REFUTES",
    CONTEXT_VERDICT: "CONTEXT_ONLY",
}


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
    "claim_id", "gold_label", "label_minted_at", "claim", "proposal",
    "registry", "bindings", "frozen_before_promotion", "missing_obligations",
)


def load_corpus(path: str) -> list[dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        raise CannotCheck(f"corpus unreadable: {exc}") from exc
    claims = payload.get("claims")
    if not isinstance(claims, list) or not claims:
        raise CannotCheck("corpus has no claims; denominator would be zero")
    for row in claims:
        for key in REQUIRED_ROW_KEYS:
            if key not in row:
                raise CannotCheck(f"corpus row missing {key!r}")
        if row["gold_label"] not in GOLD_LABELS:
            raise CannotCheck(f"unknown gold label {row['gold_label']!r}")
        prefix = f"{row['claim_id']}:"
        for evidence_id in row["registry"]:
            if not evidence_id.startswith(prefix):
                raise CannotCheck(
                    f"claim {row['claim_id']} registry id {evidence_id!r} violates the "
                    "canonical positional id scheme required by the permutation null"
                )
    ids = [row["claim_id"] for row in claims]
    if len(ids) != len(set(ids)):
        raise CannotCheck("duplicate claim_id in corpus")
    return sorted(claims, key=lambda row: row["claim_id"])


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
        by_id[row["claim_id"]] = row
    corpus_ids = {row["claim_id"] for row in corpus}
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
        row["claim_id"]
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

def arm_a_rule(record: dict[str, Any]) -> str:
    """Ungoverned upgrade: UPGRADE iff every cited evidence id resolves in the
    registry (syntactic reference resolution). Review verdicts, content hashes,
    lineage, scope, axis licensing and freeze chronology are present in the
    record and deliberately ignored. Refuses dangling references (class A7)
    rather than upgrading everything — the strongest honest ungoverned arm.
    """
    evidence_ids = record["proposal"].get("evidence_ids") or []
    if not evidence_ids:
        return "REFUSED"
    registry = record["registry"]
    for evidence_id in evidence_ids:
        if evidence_id not in registry:
            return "REFUSED"
    return "UPGRADE"


def _terminal_root(evidence_id: str, registry: dict[str, Any]) -> str:
    current = evidence_id
    seen: set[str] = set()
    while current in registry and current not in seen:
        seen.add(current)
        upstream = registry[current].get("upstream_evidence_id")
        if upstream is None:
            return current
        current = upstream
    return current


def arm_b_rule(record: dict[str, Any]) -> str:
    """Certificate-gated upgrade: decision-equivalent to
    rakl.evidence_binding_certificate.evaluate_evidence_binding_for_promotion
    returning VALID_FOR_PROMOTION_CHALLENGER (UPGRADE) versus any other verdict
    — INVALID, CONFLICT_REQUIRES_RESOLUTION, CANNOT_CHECK (REFUSED). Fail-closed:
    an incomplete or unverifiable record is REFUSED, never assumed."""
    claim = record["claim"]
    proposal = record["proposal"]
    registry = record["registry"]
    bindings = record["bindings"]

    if record["frozen_before_promotion"] is not True:
        return "REFUSED"  # None => CANNOT_CHECK, False => INVALID; both refuse
    if record["missing_obligations"]:
        return "REFUSED"
    if not bindings:
        return "REFUSED"
    if proposal.get("claim_id") != claim["claim_id"]:
        return "REFUSED"
    if proposal.get("scope_id") != claim["scope"]:
        return "REFUSED"

    evidence_ids = [item["evidence_id"] for item in bindings]
    link_ids = [item["link"]["link_id"] for item in bindings]
    proposal_ids = list(proposal.get("evidence_ids") or [])
    if len(set(evidence_ids)) != len(evidence_ids):
        return "REFUSED"
    if len(set(link_ids)) != len(link_ids):
        return "REFUSED"
    if len(set(proposal_ids)) != len(proposal_ids):
        return "REFUSED"

    support_ids: list[str] = []
    refutation_ids: list[str] = []
    for item in bindings:
        link = item["link"]
        report = item["report"]
        registered = registry.get(item["evidence_id"])
        if registered is None:
            return "REFUSED"
        if link["claim_id"] != claim["claim_id"] or report["claim_id"] != claim["claim_id"]:
            return "REFUSED"
        if report["link_id"] != link["link_id"]:
            return "REFUSED"
        if report["source_id"] != link["source_id"]:
            return "REFUSED"
        if report["proposed_relation"] != link["proposed_relation"]:
            return "REFUSED"
        if registered["content_sha256"] != link["source_sha256"]:
            return "REFUSED"  # tampered/mismatched lineage content
        if report["locator_verified"] is not True:
            return "REFUSED"
        if report["semantic_review_verified"] is not True:
            return "REFUSED"
        verdict_value = report["verdict"]
        if verdict_value not in RELATION_BY_VERDICT:
            return "REFUSED"  # contradiction / insufficient / unreviewed / invalid
        if report.get("reviewed_relation") != RELATION_BY_VERDICT[verdict_value]:
            return "REFUSED"
        if verdict_value == SUPPORT_VERDICT:
            support_ids.append(item["evidence_id"])
        elif verdict_value == REFUTE_VERDICT:
            refutation_ids.append(item["evidence_id"])

    if refutation_ids:
        return "REFUSED"  # bound refuting evidence => conflict
    if not support_ids:
        return "REFUSED"
    if sorted(proposal_ids) != sorted(support_ids):
        return "REFUSED"

    scientific = [registry[eid] for eid in support_ids
                  if registry[eid].get("kind") in SCIENTIFIC_KINDS]
    if len(scientific) != len(support_ids):
        return "REFUSED"  # experience objects bound as scientific support
    axis = proposal.get("axis")
    if not any(axis in (entry.get("supports_axes") or ()) for entry in scientific):
        return "REFUSED"  # reviewed support does not license the requested axis

    roots = {_terminal_root(eid, registry) for eid in support_ids}
    if len(support_ids) > 1 and len(roots) < len(support_ids):
        return "REFUSED"  # lineage collapses to fewer independent roots
    return "UPGRADE"


def assert_no_rule_drift(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]],
                         rule, arm_name: str) -> None:
    drift = [
        row["claim_id"] for row in corpus
        if rule(row) != arm[row["claim_id"]]["declaration"]
    ]
    if drift:
        raise CannotCheck(
            f"arm {arm_name} declarations drift from the frozen decision-equivalent rule "
            f"on {len(drift)} claims (e.g. {drift[:3]}); protocol binding broken"
        )


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def unsupported_upgrade_indicator(gold: str, declaration: str) -> int:
    return 1 if declaration == "UPGRADE" and gold == "UNSUPPORTED" else 0


def alr(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]]) -> float:
    n = len(corpus)
    bad = sum(
        unsupported_upgrade_indicator(row["gold_label"], arm[row["claim_id"]]["declaration"])
        for row in corpus
    )
    return bad / n


def vua(corpus: list[dict[str, Any]], arm: dict[str, dict[str, Any]]) -> float:
    gold_pos = [row for row in corpus if row["gold_label"] == "SUPPORTED"]
    if not gold_pos:
        raise CannotCheck("corpus contains zero gold SUPPORTED claims; VUA guard undefined")
    hits = sum(
        1 for row in gold_pos if arm[row["claim_id"]]["declaration"] == "UPGRADE"
    )
    return hits / len(gold_pos)


def mcnemar_exact(corpus: list[dict[str, Any]], arm_a: dict[str, dict[str, Any]],
                  arm_b: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Two-sided exact McNemar on claim-level unsupported-upgrade indicators."""
    b_count = 0  # A leaks authority, B does not
    c_count = 0  # B leaks authority, A does not
    for row in corpus:
        fa = unsupported_upgrade_indicator(
            row["gold_label"], arm_a[row["claim_id"]]["declaration"])
        fb = unsupported_upgrade_indicator(
            row["gold_label"], arm_b[row["claim_id"]]["declaration"])
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
    """Null 1: keep a random size-K_B subset of A's UPGRADE declarations; ALR distribution.

    Tests selectivity-vs-edge: B must beat blind refusal at its own acceptance
    count, else its ALR advantage is a base-rate artifact.
    """
    a_upgraded = sorted(
        row["claim_id"] for row in corpus
        if arm_a[row["claim_id"]]["declaration"] == "UPGRADE"
    )
    k_b = sum(
        1 for row in corpus if arm_b[row["claim_id"]]["declaration"] == "UPGRADE"
    )
    if k_b >= len(a_upgraded):
        return {"applicable": False, "k_b": k_b, "k_a": len(a_upgraded)}
    gold = {row["claim_id"]: row["gold_label"] for row in corpus}
    n = len(corpus)
    draws: list[float] = []
    for _ in range(NULL_DRAWS):
        kept = rng.sample(a_upgraded, k_b)
        bad = sum(1 for cid in kept if gold[cid] == "UNSUPPORTED")
        draws.append(bad / n)
    draws.sort()
    q_index = max(0, int(NULL_QUANTILE * NULL_DRAWS) - 1)
    return {
        "applicable": True,
        "k_b": k_b,
        "k_a": len(a_upgraded),
        "q05": draws[q_index],
        "mean": sum(draws) / len(draws),
    }


def _restamp(value: str | None, src_prefix: str, dst_prefix: str) -> str | None:
    if value is None:
        return None
    if value.startswith(src_prefix):
        return dst_prefix + value[len(src_prefix):]
    return value


def transplant_evidence_block(src_row: dict[str, Any], dst_row: dict[str, Any]) -> dict[str, Any]:
    """Move src's evidence-record block onto dst, re-stamping canonical positional
    identifiers ('{claim_id}:e{k}', '{claim_id}:l{k}') to the receiving claim.
    Semantic content (review verdicts, verification flags, kinds, licensed axes,
    hash consistency, lineage topology, freeze chronology, obligations) moves;
    claim/proposal identity stays with the receiver.
    """
    src_prefix = f"{src_row['claim_id']}:"
    dst_prefix = f"{dst_row['claim_id']}:"
    registry = {}
    for evidence_id, entry in src_row["registry"].items():
        stamped = dict(entry)
        stamped["upstream_evidence_id"] = _restamp(
            entry.get("upstream_evidence_id"), src_prefix, dst_prefix)
        registry[_restamp(evidence_id, src_prefix, dst_prefix)] = stamped
    bindings = []
    for item in src_row["bindings"]:
        link = dict(item["link"])
        report = dict(item["report"])
        link["link_id"] = _restamp(link["link_id"], src_prefix, dst_prefix)
        report["link_id"] = _restamp(report["link_id"], src_prefix, dst_prefix)
        link["claim_id"] = dst_row["claim"]["claim_id"]
        report["claim_id"] = dst_row["claim"]["claim_id"]
        bindings.append({
            "evidence_id": _restamp(item["evidence_id"], src_prefix, dst_prefix),
            "link": link,
            "report": report,
        })
    hybrid = dict(dst_row)
    hybrid["registry"] = registry
    hybrid["bindings"] = bindings
    hybrid["frozen_before_promotion"] = src_row["frozen_before_promotion"]
    hybrid["missing_obligations"] = src_row["missing_obligations"]
    return hybrid


def evidence_permutation_null(corpus: list[dict[str, Any]], rng: random.Random) -> dict[str, Any]:
    """Null 2: permute evidence-record blocks across claims with equal binding
    and proposal-evidence arity, re-run arm B's frozen decision-equivalent rule,
    collect the ALR distribution.

    Tests that B's advantage requires genuine review/lineage binding rather
    than refusing at some base rate. Claim and proposal identity stay with
    their rows; only evidence-record content moves (identity re-stamped).
    """
    strata: dict[tuple[int, int], list[int]] = {}
    for idx, row in enumerate(corpus):
        key = (len(row["bindings"]), len(row["proposal"].get("evidence_ids") or []))
        strata.setdefault(key, []).append(idx)
    n = len(corpus)
    draws: list[float] = []
    for _ in range(NULL_DRAWS):
        assignment = list(range(n))
        for indices in strata.values():
            shuffled = indices[:]
            rng.shuffle(shuffled)
            for src, dst in zip(indices, shuffled):
                assignment[dst] = src
        bad = 0
        for dst_idx, src_idx in enumerate(assignment):
            dst_row = corpus[dst_idx]
            hybrid = (dst_row if src_idx == dst_idx
                      else transplant_evidence_block(corpus[src_idx], dst_row))
            declaration = arm_b_rule(hybrid)
            bad += unsupported_upgrade_indicator(dst_row["gold_label"], declaration)
        draws.append(bad / n)
    draws.sort()
    q_index = max(0, int(NULL_QUANTILE * NULL_DRAWS) - 1)
    return {"q05": draws[q_index], "mean": sum(draws) / len(draws)}


# ---------------------------------------------------------------------------
# Verdict (frozen; no post-result rescue)
# ---------------------------------------------------------------------------

def verdict(report: dict[str, Any]) -> str:
    delta = report["alr_a"] - report["alr_b"]
    null1 = report["null_equal_n_suppression"]
    null2 = report["null_evidence_permutation"]
    null1_beaten = bool(null1.get("applicable")) and report["alr_b"] < null1["q05"]
    null2_beaten = report["alr_b"] < null2["q05"]
    promote = (
        delta >= THRESH_DELTA_ALR_PROMOTE
        and report["mcnemar"]["p_two_sided"] < THRESH_MCNEMAR_P
        and report["vua_b"] >= THRESH_VUA_FLOOR
        and null1_beaten
        and null2_beaten
    )
    if promote:
        return "PROMOTE"
    negative = delta <= THRESH_DELTA_ALR_NEGATIVE or (
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
    if len(corpus) != N_EXPECTED_CLAIMS:
        raise CannotCheck(
            f"corpus has {len(corpus)} claims; protocol froze N={N_EXPECTED_CLAIMS}"
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
        "n_claims": len(corpus),
        "seed": seed,
        "audit": audit,
        "alr_a": alr(corpus, arm_a),
        "alr_b": alr(corpus, arm_b),
        "vua_a": vua(corpus, arm_a),
        "vua_b": vua(corpus, arm_b),
        "mcnemar": mcnemar_exact(corpus, arm_a, arm_b),
        "null_equal_n_suppression": equal_n_suppression_null(corpus, arm_a, arm_b, rng),
        "null_evidence_permutation": evidence_permutation_null(corpus, rng),
    }
    report["delta_alr"] = report["alr_a"] - report["alr_b"]
    report["verdict"] = verdict(report)
    return report


# ---------------------------------------------------------------------------
# Self-test: rule-sanity, no-alarm, planted-fail, CANNOT_CHECK, determinism.
# Synthetic fixtures only; never experiment evidence.
# ---------------------------------------------------------------------------

def _record(claim_id: str, gold: str, *, hash_ok: bool = True, axis_ok: bool = True,
            dangling: bool = False) -> dict[str, Any]:
    eid = f"{claim_id}:e0"
    registry = {} if dangling else {
        eid: {
            "content_sha256": "h_true" if hash_ok else "h_other",
            "kind": "EXTERNAL_OBSERVATION",
            "supports_axes": ["M"] if axis_ok else ["R"],
            "upstream_evidence_id": None,
        }
    }
    return {
        "claim_id": claim_id,
        "gold_label": gold,
        "label_minted_at": "2000-01-01T00:00:00Z",
        "claim": {"claim_id": claim_id, "text_sha256": "t", "scope": "s1"},
        "proposal": {"proposal_id": f"{claim_id}:p", "claim_id": claim_id,
                     "axis": "M", "scope_id": "s1", "evidence_ids": [eid]},
        "registry": registry,
        "bindings": [] if dangling else [{
            "evidence_id": eid,
            "link": {"link_id": f"{claim_id}:l0", "claim_id": claim_id,
                     "source_id": "src0", "source_sha256": "h_true",
                     "proposed_relation": "SUPPORTS"},
            "report": {"link_id": f"{claim_id}:l0", "claim_id": claim_id,
                       "source_id": "src0", "verdict": SUPPORT_VERDICT,
                       "reviewed_relation": "SUPPORTS", "proposed_relation": "SUPPORTS",
                       "locator_verified": True, "semantic_review_verified": True},
        }],
        "frozen_before_promotion": True,
        "missing_obligations": [],
    }


def self_test() -> int:
    failures: list[str] = []

    valid = _record("c0", "SUPPORTED")
    tampered = _record("c1", "UNSUPPORTED", hash_ok=False)
    axis_leak = _record("c2", "UNSUPPORTED", axis_ok=False)
    dangling = _record("c3", "UNSUPPORTED", dangling=True)
    corpus = [valid, tampered]

    # World 1 — rule sanity: A upgrades on syntactic resolution alone; B gates.
    if arm_a_rule(valid) != "UPGRADE":
        failures.append("rule: arm A should upgrade a resolvable proposal")
    if arm_a_rule(tampered) != "UPGRADE":
        failures.append("rule: arm A ignores lineage content and should upgrade")
    if arm_a_rule(dangling) != "REFUSED":
        failures.append("rule: arm A should refuse dangling evidence ids")
    if arm_b_rule(valid) != "UPGRADE":
        failures.append("rule: arm B should upgrade a fully certified claim")
    if arm_b_rule(tampered) != "REFUSED":
        failures.append("rule: arm B should refuse a content-hash-broken lineage")
    if arm_b_rule(axis_leak) != "REFUSED":
        failures.append("rule: arm B should refuse an unlicensed-axis upgrade")

    # World 2 — no-alarm: honest arms produce zero ALR; a silent arm's
    # suppression is visible in VUA, and silence never mints benefit.
    arm_silent = {r["claim_id"]: {"claim_id": r["claim_id"], "declaration": "REFUSED"}
                  for r in corpus}
    arm_honest = {r["claim_id"]: {"claim_id": r["claim_id"],
                                  "declaration": "UPGRADE" if r["gold_label"] == "SUPPORTED"
                                  else "REFUSED"}
                  for r in corpus}
    if alr(corpus, arm_silent) != 0.0:
        failures.append("no-alarm: silent arm ALR should be 0")
    if alr(corpus, arm_honest) != 0.0:
        failures.append("no-alarm: honest arm ALR should be 0")
    if vua(corpus, arm_silent) != 0.0:
        failures.append("no-alarm: silent arm VUA should be 0 (over-refusal visible)")

    # World 3 — planted fail: an arm upgrades a known-unsupported claim.
    arm_trigger = dict(arm_honest)
    arm_trigger["c1"] = {"claim_id": "c1", "declaration": "UPGRADE"}
    if alr(corpus, arm_trigger) != 0.5:
        failures.append("planted: ALR should be 1/2")
    mc = mcnemar_exact(corpus, arm_trigger, arm_honest)
    if mc["b"] != 1 or mc["c"] != 0:
        failures.append(f"planted: McNemar discordants wrong: {mc}")

    # World 4 — CANNOT_CHECK paths must raise, not pass.
    try:
        vua([tampered], {"c1": {"declaration": "REFUSED"}})
        failures.append("cannot-check: zero gold SUPPORTED must raise")
    except CannotCheck:
        pass
    try:
        assert_label_independence(
            [dict(valid, label_minted_at="2030-01-01T00:00:00Z")],
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

    # World 5 — transplant + determinism: permutation null is well-defined on
    # canonical ids and seed-stable; a valid block transplanted onto the
    # tampered claim upgrades it (the null can move, so it can discriminate).
    hybrid = transplant_evidence_block(valid, tampered)
    if arm_b_rule(hybrid) != "UPGRADE":
        failures.append("transplant: valid block re-stamped onto another claim should upgrade")
    n1 = evidence_permutation_null(corpus, random.Random(7))
    n2 = evidence_permutation_null(corpus, random.Random(7))
    if n1 != n2:
        failures.append("determinism: null 2 not seed-stable")

    if failures:
        for line in failures:
            print(f"SELFTEST FAIL: {line}", file=sys.stderr)
        return 2
    print("SELFTEST PASS: rule-sanity, no-alarm, planted-fail, cannot-check, "
          "transplant, determinism")
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
