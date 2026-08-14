#!/usr/bin/env python3
"""L6-CAPABILITY-QUALIFICATION-V1 evaluator.

Frozen, deterministic, stdlib-only evaluator for the L6 capability-qualification
study (research/l6_capability_qualification_v1/PROTOCOL.json). It consumes a
qualification receipt bundle (JSON) produced by the future execution harness and
emits exactly one typed outcome:

    QUALIFIED       - every qualification coordinate PASSED. Authorizes ONLY the
                      freezing of a separate L6 lift protocol. Not a lift. Not a
                      benefit. Not scientific authority.
    NOT_QUALIFIED   - one or more coordinates FAILED; each failure names the
                      floor condition and its registered remediation lever
                      (global-recovery doctrine: informative, never a dead end).
    CANNOT_CHECK    - the qualification could not be evaluated (instrument
                      defect, missing receipts, store integrity/snapshot
                      failure, unfrozen subject, edge-indeterminate estimate).
                      Never conflated with "checked and fine" or with
                      NOT_QUALIFIED. Exit code 3, distinct from evaluated (0).

Exit codes: 0 evaluated (QUALIFIED or NOT_QUALIFIED), 3 CANNOT_CHECK, 2 usage or
bundle-structure error, 1 selftest failure.

The evaluator is pure: it reads the bundle, writes a JSON report to stdout, and
never touches the episode store, the battery, or any framework module. Gold
labels never pass through this file; it consumes scored booleans whose
independence is enforced upstream by the protocol's instrument contract and
re-checked here as receipts (QC1).

Editing this file after result access voids the run
(no_post_result_threshold_rescue). sha256 of this exact file is embedded in
PROTOCOL.json.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from typing import Any

PROTOCOL_ID = "L6-CAPABILITY-QUALIFICATION-V1"

# --- Frozen battery constants -------------------------------------------------

EXPECTED_FAMILIES: tuple[str, ...] = (
    "STRAIGHT_SUPPORT",
    "STRAIGHT_REFUTATION",
    "SUPPORT_WITH_IRRELEVANT_DISTRACTORS",
    "REFUTATION_WITH_IRRELEVANT_DISTRACTORS",
    "CONTEXT_QOI_NEAR_MISS",
    "SCOPE_RESTRICTION",
    "CONFLICTING_EVIDENCE",
    "MISSING_DECISIVE_EVIDENCE_CANNOT_CHECK",
    "SAME_ROOT_PSEUDO_CORROBORATION",
    "INDEPENDENT_CORROBORATION",
    "CORRECT_VERDICT_WRONG_EVIDENCE_ID_TRAP",
    "EXPERIENCE_APPLICABLE_STRUCTURED_ROUTING",
)
TASKS_PER_FAMILY = 20
N_TASKS = len(EXPECTED_FAMILIES) * TASKS_PER_FAMILY  # 240

# --- Frozen store binding (PR #651 seed corpus snapshot) ----------------------

EXPECTED_STORE_HEAD = "7113f24bbed5b93c0197069078fff9e7189dee0b912fd7d65e35ef16e4c55396"
EXPECTED_SHADOW_EPISODES = 139

# --- Frozen thresholds (justifications in PROTOCOL.json; strictly interior:
# every gate below is demonstrated flippable by a planted selftest world) ------

QC2_WINDOW = (0.20, 0.80)
QC2_CI_ALPHA = 0.05
QC3_MIN_MIXED_FAMILIES = 8
QC3_READOUT_VALIDITY_MIN = 0.90
QC4_FAMILY_WINDOW = (0.10, 0.90)
QC4_MIN_FAMILIES_IN_WINDOW = 8
QC5_MIN_FLIP_PAIRS = 14  # >= 1 per candidate-visible routing field (PR #634 schema)
QC6_MIN_RELEVANT_FAMILY_COVERAGE = 0.50
QC6_MIN_VERIFIED_OUTCOME_FAMILIES = 1
QC8_MIN_DISTINCT_COST_VALUES = 2
AUDIT_MAX_DISAGREEMENT = 0.05

REMEDIATION = {
    "QC2_PARENT_COMPLETION_WINDOW_LOW": (
        "Attribute to ONE stage first: if structured-readout validity < 0.90 the lever is "
        "interface repair under a new versioned challenger identity (issue #447 Stage-2 "
        "pattern); otherwise re-stratify the battery as V2 with registered easier strata. "
        "The V1 receipt is preserved verbatim."
    ),
    "QC2_PARENT_COMPLETION_WINDOW_HIGH": (
        "Battery hardening as V2: registered harder family generators. The V1 receipt is "
        "preserved verbatim."
    ),
    "QC3_NON_DEGENERATE_VARIANCE": (
        "Per-family attribution, then family rebalance as V2 (harder or easier strata for "
        "the degenerate families only); if readout validity is the failing part, interface "
        "repair under a new versioned challenger identity."
    ),
    "QC4_PER_FAMILY_HEADROOM": (
        "Family rebalance as V2 targeting only out-of-window families; preserve the V1 "
        "per-family table."
    ),
    "QC5_ROUTING_SURFACE_REACHABILITY": (
        "Operational defect, not a capability negative: localize the FIRST non-conforming "
        "boundary (store open -> query -> structured-state derivation -> action function), "
        "repair under a versioned successor, re-run qualification."
    ),
    "QC6_EXPERIENCE_RELEVANCE_COVERAGE": (
        "Typed outcome backfill of the seed corpus as migration V2 (re-extraction of "
        "explicit PROMOTED/REFUTED markers from the raw SELF_RAKL receipts per "
        "MIGRATION_RECEIPT.md residual 3), and/or mint new native episodes by running "
        "registered tasks through the parent with receipts, admitted via the proposal-only "
        "shadow flow. Never fabricated outcomes."
    ),
    "QC7_FRESHNESS": (
        "Regenerate exactly the contaminated instances with a fresh registered seed block; "
        "contaminated task ids stay in the receipt."
    ),
    "QC8_COST_TELEMETRY": (
        "Telemetry repair (operational): instrument the parent harness for per-task "
        "wall-clock/token/RSS receipts and re-run."
    ),
}


# --- Exact binomial machinery (stdlib only) -----------------------------------

def _binom_cdf(k: int, n: int, p: float) -> float:
    if p <= 0.0:
        return 1.0
    if p >= 1.0:
        return 1.0 if k >= n else 0.0
    total = 0.0
    for i in range(0, k + 1):
        total += math.comb(n, i) * (p ** i) * ((1.0 - p) ** (n - i))
    return min(1.0, total)


def _binom_sf_geq(k: int, n: int, p: float) -> float:
    """P(X >= k)."""
    if k <= 0:
        return 1.0
    return max(0.0, 1.0 - _binom_cdf(k - 1, n, p))


def clopper_pearson(k: int, n: int, alpha: float) -> tuple[float, float]:
    """Exact two-sided (1-alpha) confidence interval for a binomial proportion."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= k <= n:
        raise ValueError("k out of range")
    half = alpha / 2.0

    if k == 0:
        lo = 0.0
    else:
        f = lambda p: _binom_sf_geq(k, n, p) - half  # increasing in p
        a, b = 0.0, 1.0
        for _ in range(200):
            mid = (a + b) / 2.0
            if f(mid) < 0.0:
                a = mid
            else:
                b = mid
        lo = (a + b) / 2.0

    if k == n:
        hi = 1.0
    else:
        g = lambda p: _binom_cdf(k, n, p) - half  # decreasing in p
        a, b = 0.0, 1.0
        for _ in range(200):
            mid = (a + b) / 2.0
            if g(mid) > 0.0:
                a = mid
            else:
                b = mid
        hi = (a + b) / 2.0

    return (lo, hi)


# --- Bundle evaluation --------------------------------------------------------

REQUIRED_SECTIONS = (
    "subject_freeze",
    "instrument",
    "battery",
    "freshness",
    "store",
    "relevance",
    "parent_results",
)


class BundleError(ValueError):
    """Structural bundle defect (exit 2)."""


def _coord(status: str, measured: Any, threshold: Any, **extra: Any) -> dict:
    row = {"status": status, "measured": measured, "threshold": threshold}
    row.update(extra)
    return row


def _fail(name: str, measured: Any, threshold: Any, lever_key: str, **extra: Any) -> dict:
    return _coord(
        "FAIL", measured, threshold, remediation_lever=REMEDIATION[lever_key], **extra
    )


def evaluate(bundle: dict) -> dict:
    """Pure evaluation of one qualification receipt bundle."""
    for section in REQUIRED_SECTIONS:
        if section not in bundle:
            return _cannot_check([f"MISSING_SECTION:{section}"], coordinates={})

    coordinates: dict[str, dict] = {}
    cc_reasons: list[str] = []

    # ---- Subject freeze (execution precondition; no model shopping) ----------
    sf = bundle["subject_freeze"]
    if not (
        sf.get("frozen") is True
        and sf.get("frozen_before_battery") is True
        and isinstance(sf.get("subject_hash"), str)
        and len(sf.get("subject_hash", "")) == 64
    ):
        cc_reasons.append("SUBJECT_NOT_FROZEN")

    # ---- QC1 instrument validity (checked before any parent metric is read) --
    inst = bundle["instrument"]
    qc1_defects: list[str] = []
    role = inst.get("role_semantics_audit", {})
    if role.get("passed") is not True:
        qc1_defects.append("ROLE_SEMANTICS_UNDEFINED")
    if role.get("audit_input_was_text_only") is not True:
        qc1_defects.append("ROLE_AUDIT_SAW_OUTCOMES")
    gold = inst.get("gold_independence", {})
    if gold.get("oracle_file_present") is not True:
        qc1_defects.append("GOLD_ORACLE_MISSING")
    if gold.get("oracle_imports_candidate") is not False:
        qc1_defects.append("GOLD_ORACLE_IMPORTS_CANDIDATE")
    if gold.get("oracle_output_fed_to_candidate") is not False:
        qc1_defects.append("GOLD_FED_TO_CANDIDATE")
    if gold.get("forbidden_inputs_absent") is not True:
        qc1_defects.append("GOLD_USED_FORBIDDEN_INPUT")
    if gold.get("gold_committed_before_parent_run") is not True:
        qc1_defects.append("GOLD_NOT_COMMITTED_BEFORE_RUN")
    audit = inst.get("human_audit", {})
    if audit.get("auditor_saw_arm_outputs") is not False:
        qc1_defects.append("AUDITOR_SAW_ARM_OUTPUTS")
    disagreement = audit.get("disagreement")
    if not isinstance(disagreement, (int, float)) or disagreement >= AUDIT_MAX_DISAGREEMENT:
        qc1_defects.append("AUDIT_DISAGREEMENT_EXCESSIVE")
    if qc1_defects:
        coordinates["QC1_INSTRUMENT_VALIDITY"] = _coord(
            "CANNOT_CHECK", qc1_defects, "all instrument receipts clean"
        )
        cc_reasons.append("INSTRUMENT_DEFECT:" + ",".join(sorted(qc1_defects)))
    else:
        coordinates["QC1_INSTRUMENT_VALIDITY"] = _coord(
            "PASS", "clean", "all instrument receipts clean"
        )

    # ---- Battery structure ---------------------------------------------------
    battery = bundle["battery"]
    tasks = battery.get("task_records", [])
    family_counts: dict[str, int] = {}
    task_ids = set()
    for record in tasks:
        family_counts[record["family"]] = family_counts.get(record["family"], 0) + 1
        task_ids.add(record["task_id"])
    structure_defects: list[str] = []
    if len(tasks) != N_TASKS or len(task_ids) != N_TASKS:
        structure_defects.append(f"task_count:{len(tasks)}/unique:{len(task_ids)}!={N_TASKS}")
    for family in EXPECTED_FAMILIES:
        if family_counts.get(family, 0) != TASKS_PER_FAMILY:
            structure_defects.append(f"family:{family}:{family_counts.get(family, 0)}")
    unknown = sorted(set(family_counts) - set(EXPECTED_FAMILIES))
    if unknown:
        structure_defects.append("unknown_families:" + ",".join(unknown))
    if structure_defects:
        cc_reasons.append("BATTERY_STRUCTURE:" + ";".join(structure_defects))

    results = bundle["parent_results"]
    result_ids = {r["task_id"] for r in results}
    if not structure_defects and result_ids != task_ids:
        cc_reasons.append("PARENT_RESULTS_DO_NOT_COVER_BATTERY")

    # ---- QC5 routing-surface reachability ------------------------------------
    store = bundle["store"]
    if store.get("open_verdict") != "VALID":
        coordinates["QC5_ROUTING_SURFACE_REACHABILITY"] = _coord(
            "CANNOT_CHECK", store.get("open_verdict"), "VALID"
        )
        cc_reasons.append("STORE_INTEGRITY_FAILURE")
    elif (
        store.get("head_hash") != EXPECTED_STORE_HEAD
        or store.get("expected_head_hash") != EXPECTED_STORE_HEAD
    ):
        coordinates["QC5_ROUTING_SURFACE_REACHABILITY"] = _coord(
            "CANNOT_CHECK", store.get("head_hash"), EXPECTED_STORE_HEAD
        )
        cc_reasons.append("STORE_SNAPSHOT_MISMATCH")
    elif int(store.get("admission_upgrades_detected", -1)) != 0:
        coordinates["QC5_ROUTING_SURFACE_REACHABILITY"] = _coord(
            "CANNOT_CHECK", store.get("admission_upgrades_detected"), 0
        )
        cc_reasons.append("SHADOW_POSTURE_VIOLATED")
    elif int(store.get("episodes_shadow_count", -1)) != EXPECTED_SHADOW_EPISODES:
        coordinates["QC5_ROUTING_SURFACE_REACHABILITY"] = _coord(
            "CANNOT_CHECK", store.get("episodes_shadow_count"), EXPECTED_SHADOW_EPISODES
        )
        cc_reasons.append("STORE_SNAPSHOT_MISMATCH")
    else:
        query = store.get("query_battery", {})
        sens = store.get("content_sensitivity", {})
        pairs_total = int(sens.get("flip_pairs_total", 0))
        pairs_flipped = int(sens.get("flip_pairs_flipped", -1))
        reachable = (
            query.get("deterministic") is True
            and query.get("nonempty") is True
            and pairs_total >= QC5_MIN_FLIP_PAIRS
            and pairs_flipped == pairs_total
        )
        measured = {
            "query_deterministic": query.get("deterministic"),
            "query_nonempty": query.get("nonempty"),
            "flip_pairs": f"{pairs_flipped}/{pairs_total}",
        }
        threshold = {
            "query_deterministic": True,
            "query_nonempty": True,
            "flip_pairs": f"all, total >= {QC5_MIN_FLIP_PAIRS}",
        }
        if reachable:
            coordinates["QC5_ROUTING_SURFACE_REACHABILITY"] = _coord(
                "PASS", measured, threshold
            )
        else:
            coordinates["QC5_ROUTING_SURFACE_REACHABILITY"] = _fail(
                "QC5", measured, threshold, "QC5_ROUTING_SURFACE_REACHABILITY"
            )

    # Structural CC stops metric interpretation here (fail-closed).
    if cc_reasons:
        return _cannot_check(cc_reasons, coordinates)

    # ---- QC2 parent completion window (all-N denominator) --------------------
    completed = sum(1 for r in results if r["completed"] is True)
    p_hat = completed / N_TASKS
    ci_lo, ci_hi = clopper_pearson(completed, N_TASKS, QC2_CI_ALPHA)
    lo_edge, hi_edge = QC2_WINDOW
    straddles = (ci_lo < lo_edge < ci_hi) or (ci_lo < hi_edge < ci_hi)
    qc2_measured = {
        "p_hat": round(p_hat, 6),
        "ci95": [round(ci_lo, 6), round(ci_hi, 6)],
        "completed": completed,
        "n": N_TASKS,
    }
    if straddles:
        coordinates["QC2_PARENT_COMPLETION_WINDOW"] = _coord(
            "CANNOT_CHECK", qc2_measured, list(QC2_WINDOW),
            note="exact 95% CI contains a window edge; registered +120-task extension",
        )
        cc_reasons.append("QC2_EDGE_INDETERMINATE")
    elif p_hat < lo_edge:
        coordinates["QC2_PARENT_COMPLETION_WINDOW"] = _fail(
            "QC2", qc2_measured, list(QC2_WINDOW), "QC2_PARENT_COMPLETION_WINDOW_LOW"
        )
    elif p_hat > hi_edge:
        coordinates["QC2_PARENT_COMPLETION_WINDOW"] = _fail(
            "QC2", qc2_measured, list(QC2_WINDOW), "QC2_PARENT_COMPLETION_WINDOW_HIGH"
        )
    else:
        coordinates["QC2_PARENT_COMPLETION_WINDOW"] = _coord(
            "PASS", qc2_measured, list(QC2_WINDOW)
        )

    # ---- QC3 non-degenerate variance ----------------------------------------
    by_family: dict[str, list[dict]] = {family: [] for family in EXPECTED_FAMILIES}
    task_family = {t["task_id"]: t["family"] for t in tasks}
    for r in results:
        by_family[task_family[r["task_id"]]].append(r)
    mixed = 0
    family_rates: dict[str, float] = {}
    for family, rows in by_family.items():
        wins = sum(1 for r in rows if r["completed"] is True)
        family_rates[family] = wins / len(rows)
        if 0 < wins < len(rows):
            mixed += 1
    readout_valid = sum(1 for r in results if r["structured_readout_valid"] is True)
    readout_rate = readout_valid / N_TASKS
    qc3_measured = {
        "mixed_families": mixed,
        "readout_validity": round(readout_rate, 6),
    }
    qc3_threshold = {
        "mixed_families_min": QC3_MIN_MIXED_FAMILIES,
        "readout_validity_min": QC3_READOUT_VALIDITY_MIN,
    }
    if mixed >= QC3_MIN_MIXED_FAMILIES and readout_rate >= QC3_READOUT_VALIDITY_MIN:
        coordinates["QC3_NON_DEGENERATE_VARIANCE"] = _coord(
            "PASS", qc3_measured, qc3_threshold
        )
    else:
        coordinates["QC3_NON_DEGENERATE_VARIANCE"] = _fail(
            "QC3", qc3_measured, qc3_threshold, "QC3_NON_DEGENERATE_VARIANCE"
        )

    # ---- QC4 per-family headroom ---------------------------------------------
    fam_lo, fam_hi = QC4_FAMILY_WINDOW
    in_window = sum(1 for rate in family_rates.values() if fam_lo <= rate <= fam_hi)
    qc4_measured = {
        "families_in_window": in_window,
        "family_rates": {k: round(v, 4) for k, v in sorted(family_rates.items())},
    }
    qc4_threshold = {
        "families_in_window_min": QC4_MIN_FAMILIES_IN_WINDOW,
        "window": list(QC4_FAMILY_WINDOW),
    }
    if in_window >= QC4_MIN_FAMILIES_IN_WINDOW:
        coordinates["QC4_PER_FAMILY_HEADROOM"] = _coord("PASS", qc4_measured, qc4_threshold)
    else:
        coordinates["QC4_PER_FAMILY_HEADROOM"] = _fail(
            "QC4", qc4_measured, qc4_threshold, "QC4_PER_FAMILY_HEADROOM"
        )

    # ---- QC6 experience-relevance coverage -----------------------------------
    relevance = bundle["relevance"]
    fam_total = int(relevance.get("families_total", 0))
    fam_relevant = int(relevance.get("families_with_relevant_episode", 0))
    fam_verified = int(relevance.get("families_with_verified_outcome_episode", 0))
    coverage = fam_relevant / fam_total if fam_total else 0.0
    qc6_measured = {
        "relevant_family_coverage": round(coverage, 6),
        "families_with_verified_outcome_episode": fam_verified,
    }
    qc6_threshold = {
        "relevant_family_coverage_min": QC6_MIN_RELEVANT_FAMILY_COVERAGE,
        "families_with_verified_outcome_episode_min": QC6_MIN_VERIFIED_OUTCOME_FAMILIES,
    }
    if fam_total != len(EXPECTED_FAMILIES):
        coordinates["QC6_EXPERIENCE_RELEVANCE_COVERAGE"] = _coord(
            "CANNOT_CHECK", qc6_measured, qc6_threshold
        )
        cc_reasons.append("RELEVANCE_RECEIPT_MALFORMED")
    elif (
        coverage >= QC6_MIN_RELEVANT_FAMILY_COVERAGE
        and fam_verified >= QC6_MIN_VERIFIED_OUTCOME_FAMILIES
    ):
        coordinates["QC6_EXPERIENCE_RELEVANCE_COVERAGE"] = _coord(
            "PASS", qc6_measured, qc6_threshold
        )
    else:
        coordinates["QC6_EXPERIENCE_RELEVANCE_COVERAGE"] = _fail(
            "QC6", qc6_measured, qc6_threshold, "QC6_EXPERIENCE_RELEVANCE_COVERAGE"
        )

    # ---- QC7 freshness (zero tolerance) --------------------------------------
    fresh = bundle["freshness"]
    contamination = (
        list(fresh.get("contaminated_task_ids", ["MISSING"]))
        + list(fresh.get("artifact_hash_collisions", ["MISSING"]))
        + list(fresh.get("signature_collisions", ["MISSING"]))
        + list(fresh.get("id_collisions", ["MISSING"]))
    )
    checked_head = fresh.get("checked_against_head_hash")
    qc7_measured = {
        "contaminated": sorted(set(contamination)),
        "checked_against_head_hash": checked_head,
    }
    if checked_head != EXPECTED_STORE_HEAD:
        coordinates["QC7_FRESHNESS"] = _coord(
            "CANNOT_CHECK", qc7_measured, "checked against frozen store head"
        )
        cc_reasons.append("FRESHNESS_CHECK_WRONG_SNAPSHOT")
    elif contamination:
        coordinates["QC7_FRESHNESS"] = _fail(
            "QC7", qc7_measured, "zero contaminated instances", "QC7_FRESHNESS"
        )
    else:
        coordinates["QC7_FRESHNESS"] = _coord(
            "PASS", qc7_measured, "zero contaminated instances"
        )

    # ---- QC8 cost telemetry ---------------------------------------------------
    costs = []
    cost_missing = 0
    for r in results:
        cost = r.get("cost")
        if not isinstance(cost, dict) or not isinstance(cost.get("wall_ms"), (int, float)):
            cost_missing += 1
        else:
            costs.append(float(cost["wall_ms"]))
    distinct = len(set(costs))
    qc8_measured = {
        "cost_receipts_missing": cost_missing,
        "distinct_wall_ms_values": distinct,
        "all_zero": bool(costs) and all(c == 0.0 for c in costs),
    }
    qc8_threshold = {
        "cost_receipts_missing": 0,
        "distinct_wall_ms_values_min": QC8_MIN_DISTINCT_COST_VALUES,
        "all_zero": False,
    }
    if (
        cost_missing == 0
        and distinct >= QC8_MIN_DISTINCT_COST_VALUES
        and not qc8_measured["all_zero"]
    ):
        coordinates["QC8_COST_TELEMETRY"] = _coord("PASS", qc8_measured, qc8_threshold)
    else:
        coordinates["QC8_COST_TELEMETRY"] = _fail(
            "QC8", qc8_measured, qc8_threshold, "QC8_COST_TELEMETRY"
        )

    if cc_reasons:
        return _cannot_check(cc_reasons, coordinates)

    failed = sorted(
        name for name, row in coordinates.items() if row["status"] == "FAIL"
    )
    verdict = "NOT_QUALIFIED" if failed else "QUALIFIED"
    return {
        "protocol_id": PROTOCOL_ID,
        "verdict": verdict,
        "failed_coordinates": failed,
        "coordinates": coordinates,
        "authorizes": (
            "freezing a separate L6 lift protocol only" if verdict == "QUALIFIED" else None
        ),
        "grants_scientific_authority": False,
        "is_lift_evidence": False,
    }


def _cannot_check(reasons: list[str], coordinates: dict) -> dict:
    return {
        "protocol_id": PROTOCOL_ID,
        "verdict": "CANNOT_CHECK",
        "cannot_check_reasons": sorted(set(reasons)),
        "failed_coordinates": [],
        "coordinates": coordinates,
        "authorizes": None,
        "grants_scientific_authority": False,
        "is_lift_evidence": False,
    }


# --- Selftest worlds (synthetic, NON-EVIDENTIAL) ------------------------------

def _clean_bundle() -> dict:
    tasks = []
    results = []
    index = 0
    for family in EXPECTED_FAMILIES:
        for j in range(TASKS_PER_FAMILY):
            task_id = f"T-{index:03d}"
            tasks.append(
                {
                    "task_id": task_id,
                    "family": family,
                    "content_hash": f"{index:064x}",
                    "problem_signature": [family, f"instance:{j}"],
                    "gold_scoreable": True,
                }
            )
            results.append(
                {
                    "task_id": task_id,
                    "family": family,
                    "completed": j % 2 == 0,
                    "structured_readout_valid": True,
                    "declared_cannot_check": False,
                    "gold_cannot_check": family
                    == "MISSING_DECISIVE_EVIDENCE_CANNOT_CHECK",
                    "cost": {"wall_ms": 100 + index, "tokens": 0, "peak_rss_kb": 4096},
                }
            )
            index += 1
    return {
        "subject_freeze": {
            "frozen": True,
            "frozen_before_battery": True,
            "subject_hash": "a" * 64,
        },
        "instrument": {
            "role_semantics_audit": {"passed": True, "audit_input_was_text_only": True},
            "gold_independence": {
                "oracle_file_present": True,
                "oracle_imports_candidate": False,
                "oracle_output_fed_to_candidate": False,
                "forbidden_inputs_absent": True,
                "gold_committed_before_parent_run": True,
            },
            "human_audit": {
                "n": 24,
                "disagreement": 0.02,
                "auditor_saw_arm_outputs": False,
            },
        },
        "battery": {"n_tasks": N_TASKS, "generator_seed": 202608141600, "task_records": tasks},
        "freshness": {
            "checked_against_head_hash": EXPECTED_STORE_HEAD,
            "contaminated_task_ids": [],
            "artifact_hash_collisions": [],
            "signature_collisions": [],
            "id_collisions": [],
        },
        "store": {
            "open_verdict": "VALID",
            "head_hash": EXPECTED_STORE_HEAD,
            "expected_head_hash": EXPECTED_STORE_HEAD,
            "record_count": EXPECTED_SHADOW_EPISODES,
            "episodes_shadow_count": EXPECTED_SHADOW_EPISODES,
            "admission_upgrades_detected": 0,
            "query_battery": {"deterministic": True, "nonempty": True},
            "content_sensitivity": {"flip_pairs_total": 28, "flip_pairs_flipped": 28},
        },
        "relevance": {
            "families_total": len(EXPECTED_FAMILIES),
            "families_with_relevant_episode": 8,
            "families_with_verified_outcome_episode": 2,
        },
        "parent_results": results,
    }


def _set_completion_rate(bundle: dict, rate: float) -> None:
    """Deterministically set the global completion pattern, keeping families mixed
    where possible."""
    per_family = max(0, min(TASKS_PER_FAMILY, round(rate * TASKS_PER_FAMILY)))
    counters: dict[str, int] = {}
    for r in bundle["parent_results"]:
        seen = counters.get(r["family"], 0)
        r["completed"] = seen < per_family
        counters[r["family"]] = seen + 1


def _selftest() -> int:
    failures: list[str] = []

    def expect(name: str, condition: bool) -> None:
        if not condition:
            failures.append(name)

    # Determinism.
    a = json.dumps(evaluate(_clean_bundle()), sort_keys=True)
    b = json.dumps(evaluate(_clean_bundle()), sort_keys=True)
    expect("determinism", a == b)

    # Clean world -> QUALIFIED.
    report = evaluate(_clean_bundle())
    expect("clean_qualified", report["verdict"] == "QUALIFIED")
    expect("clean_no_failed", report["failed_coordinates"] == [])

    # Planted per-gate FAIL worlds: each gate is individually flippable
    # (falsifiability-by-construction at the evaluator level).
    world = _clean_bundle()
    _set_completion_rate(world, 0.10)
    report = evaluate(world)
    expect(
        "qc2_low",
        report["verdict"] == "NOT_QUALIFIED"
        and "QC2_PARENT_COMPLETION_WINDOW" in report["failed_coordinates"],
    )

    world = _clean_bundle()
    _set_completion_rate(world, 0.95)
    report = evaluate(world)
    expect(
        "qc2_high",
        report["verdict"] == "NOT_QUALIFIED"
        and "QC2_PARENT_COMPLETION_WINDOW" in report["failed_coordinates"],
    )

    world = _clean_bundle()  # 6 families all-success, 6 families all-failure:
    for i, r in enumerate(world["parent_results"]):
        r["completed"] = (i // TASKS_PER_FAMILY) < 6
    report = evaluate(world)
    expect(
        "qc3_degenerate",
        report["verdict"] == "NOT_QUALIFIED"
        and "QC3_NON_DEGENERATE_VARIANCE" in report["failed_coordinates"]
        and "QC4_PER_FAMILY_HEADROOM" in report["failed_coordinates"],
    )

    world = _clean_bundle()
    for i, r in enumerate(world["parent_results"]):
        if i % 5 == 0:
            r["structured_readout_valid"] = False  # 20% invalid readout
    report = evaluate(world)
    expect(
        "qc3_readout",
        report["verdict"] == "NOT_QUALIFIED"
        and "QC3_NON_DEGENERATE_VARIANCE" in report["failed_coordinates"],
    )

    world = _clean_bundle()
    world["store"]["content_sensitivity"]["flip_pairs_flipped"] = 27
    report = evaluate(world)
    expect(
        "qc5_flip",
        report["verdict"] == "NOT_QUALIFIED"
        and "QC5_ROUTING_SURFACE_REACHABILITY" in report["failed_coordinates"],
    )

    world = _clean_bundle()
    world["relevance"]["families_with_relevant_episode"] = 3
    report = evaluate(world)
    expect(
        "qc6_coverage",
        report["verdict"] == "NOT_QUALIFIED"
        and "QC6_EXPERIENCE_RELEVANCE_COVERAGE" in report["failed_coordinates"],
    )

    world = _clean_bundle()
    world["relevance"]["families_with_verified_outcome_episode"] = 0
    report = evaluate(world)
    expect(
        "qc6_verified_starvation",
        report["verdict"] == "NOT_QUALIFIED"
        and "QC6_EXPERIENCE_RELEVANCE_COVERAGE" in report["failed_coordinates"],
    )

    world = _clean_bundle()
    world["freshness"]["contaminated_task_ids"] = ["T-007"]
    report = evaluate(world)
    expect(
        "qc7_contaminated",
        report["verdict"] == "NOT_QUALIFIED"
        and "QC7_FRESHNESS" in report["failed_coordinates"],
    )

    world = _clean_bundle()
    for r in world["parent_results"]:
        r["cost"] = {"wall_ms": 0}
    report = evaluate(world)
    expect(
        "qc8_degenerate_cost",
        report["verdict"] == "NOT_QUALIFIED"
        and "QC8_COST_TELEMETRY" in report["failed_coordinates"],
    )

    # Every FAIL row must carry its remediation lever (informative, not a dead end).
    world = _clean_bundle()
    _set_completion_rate(world, 0.10)
    report = evaluate(world)
    row = report["coordinates"]["QC2_PARENT_COMPLETION_WINDOW"]
    expect("fail_carries_lever", bool(row.get("remediation_lever")))

    # CANNOT_CHECK worlds (structurally distinct from NOT_QUALIFIED).
    world = _clean_bundle()
    world["instrument"]["role_semantics_audit"]["passed"] = False
    report = evaluate(world)
    expect(
        "cc_instrument",
        report["verdict"] == "CANNOT_CHECK"
        and any(
            reason.startswith("INSTRUMENT_DEFECT")
            for reason in report["cannot_check_reasons"]
        ),
    )

    world = _clean_bundle()
    world["instrument"]["gold_independence"]["oracle_imports_candidate"] = True
    report = evaluate(world)
    expect("cc_gold_dependence", report["verdict"] == "CANNOT_CHECK")

    world = _clean_bundle()
    world["store"]["open_verdict"] = "BROKEN_CHAIN"
    report = evaluate(world)
    expect(
        "cc_store_invalid",
        report["verdict"] == "CANNOT_CHECK"
        and "STORE_INTEGRITY_FAILURE" in report["cannot_check_reasons"],
    )

    world = _clean_bundle()
    world["store"]["head_hash"] = "0" * 64
    report = evaluate(world)
    expect(
        "cc_store_snapshot",
        report["verdict"] == "CANNOT_CHECK"
        and "STORE_SNAPSHOT_MISMATCH" in report["cannot_check_reasons"],
    )

    world = _clean_bundle()
    world["store"]["admission_upgrades_detected"] = 1
    report = evaluate(world)
    expect(
        "cc_shadow_posture",
        report["verdict"] == "CANNOT_CHECK"
        and "SHADOW_POSTURE_VIOLATED" in report["cannot_check_reasons"],
    )

    world = _clean_bundle()
    world["subject_freeze"]["frozen"] = False
    report = evaluate(world)
    expect(
        "cc_subject_unfrozen",
        report["verdict"] == "CANNOT_CHECK"
        and "SUBJECT_NOT_FROZEN" in report["cannot_check_reasons"],
    )

    world = _clean_bundle()
    del world["relevance"]
    report = evaluate(world)
    expect(
        "cc_missing_section",
        report["verdict"] == "CANNOT_CHECK"
        and "MISSING_SECTION:relevance" in report["cannot_check_reasons"],
    )

    world = _clean_bundle()
    _set_completion_rate(world, 0.21)  # exact CI contains the 0.20 edge
    report = evaluate(world)
    expect(
        "cc_qc2_edge",
        report["verdict"] == "CANNOT_CHECK"
        and "QC2_EDGE_INDETERMINATE" in report["cannot_check_reasons"],
    )

    world = _clean_bundle()
    world["freshness"]["checked_against_head_hash"] = "1" * 64
    report = evaluate(world)
    expect(
        "cc_freshness_snapshot",
        report["verdict"] == "CANNOT_CHECK"
        and "FRESHNESS_CHECK_WRONG_SNAPSHOT" in report["cannot_check_reasons"],
    )

    # Clopper-Pearson sanity: exact interval must bracket p_hat and be interior.
    lo, hi = clopper_pearson(120, 240, 0.05)
    expect("cp_brackets", lo < 0.5 < hi and 0.43 < lo < 0.47 and 0.53 < hi < 0.57)
    lo0, hi0 = clopper_pearson(0, 240, 0.05)
    expect("cp_zero", lo0 == 0.0 and 0.0 < hi0 < 0.03)

    if failures:
        print("SELFTEST FAIL: " + ", ".join(failures))
        return 1
    print("SELFTEST PASS (all worlds: clean, per-gate planted FAIL, CANNOT_CHECK, determinism)")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--bundle", help="path to qualification receipt bundle JSON")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        return _selftest()
    if not args.bundle:
        parser.print_usage()
        return 2
    try:
        with open(args.bundle, "r", encoding="utf-8") as handle:
            bundle = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"verdict": "CANNOT_CHECK", "cannot_check_reasons": [f"BUNDLE_UNREADABLE:{exc}"]}))
        return 3
    try:
        report = evaluate(bundle)
    except (KeyError, TypeError, ValueError) as exc:
        print(json.dumps({"verdict": "CANNOT_CHECK", "cannot_check_reasons": [f"BUNDLE_MALFORMED:{exc}"]}))
        return 3
    print(json.dumps(report, sort_keys=True, indent=1))
    return 3 if report["verdict"] == "CANNOT_CHECK" else 0


if __name__ == "__main__":
    sys.exit(main())
