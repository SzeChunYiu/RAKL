#!/usr/bin/env python3
"""Evidence-based promotion gate: decide which tested ideas become mechanics.

Orion applied to Orion. Every candidate mechanic starts PROPOSAL_ONLY. This gate
reads the candidate's own experiment artifact and issues a typed routing verdict
from registered, pre-declared criteria.

A positive/conditional verdict for a *new* candidate is additionally subject to
the RSHEA mechanic-research-packet gate introduced by #546/#570/#573. Historical
candidates that predate that contract are preserved as an explicit, frozen
legacy set; they are not retroactively called preregistered. Any future candidate
outside that set must bind a valid fresh research packet before a positive or
conditional promotion can survive this gate.

Promotion is a ROUTING/ENGINEERING status, never scientific authority. A promoted
mechanic is one Orion may use by default in its supported scope; it is not a claim
that a scientific hypothesis is true. ``grants_scientific_authority`` is False.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rakl.applicability import build_applicability_contract  # noqa: E402
from rakl.mechanic_research_packet import (  # noqa: E402
    MechanicResearchPacketVerdict,
    validate_mechanic_research_packet,
)
from rakl.mechanic_research_packet_io import load_packet_set  # noqa: E402

sys.path.insert(0, str(ROOT / "tools"))
from telemetry_schema import (  # noqa: E402
    ClaimClass,
    EFFICIENCY_CLAIM_CLASSES,
    telemetry_completeness_status,
)

R = ROOT / "research"
PACKET_SET_PATH = R / "mechanic_research_packets_v1/PAPER5_PAPER6_SUCCESSORS.json"

# Exact candidate IDs that existed before the #546/#570 packet contract became
# incumbent. They keep their historical engineering verdicts, but are explicitly
# tagged LEGACY_PRE_PACKET and may not be used as precedent for adding another
# packet-free candidate. A successor/revalidation must use a new candidate id.
PRE_PACKET_LEGACY_CANDIDATES = frozenset(
    {
        "fieldability_given_field",
        "field_construction",
        "field_construction_successor",
        "navigation_dynamics",
        "navigation_dynamics_successor",
        "navigation_dynamics_parallel",
        "path_equivalence_quotient",
        "mechanic_diagnosis",
        "diagnosis_active_successor",
        "tcsq_sq3",
        "tcsq_sq3_successor",
        "identity_reuse",
        "six_family_law",
    }
)

# candidate -> evidence contract
CANDIDATES = {
    "fieldability_given_field": {
        "artifact": R / "unified_problem_solving_v1/results/field_hypothesis.json",
        "net_keys": ["search_reduction_vs_bfs"],
        "cost_charged": True,
        "claim_class": ClaimClass.PERFORMANCE,
        "cost_fields": None,
        "note": "given-metric field; construction cost not applicable (field supplied by domain)",
    },
    "field_construction": {
        "artifact": R / "unified_problem_solving_v1/results/field_construction.json",
        "net_keys": ["net_search_saving", "net_saving", "search_reduction_net"],
        "cost_charged": True,
        "claim_class": ClaimClass.EFFICIENCY,
        "cost_fields": ["construction_cost"],
        "note": "constructor must pay for its own construction cost",
    },
    "field_construction_successor": {
        "artifact": R / "unified_problem_solving_v1/results/field_construction_successor.json",
        "net_keys": ["net_advantage_over_strongest_parent"],
        "cost_charged": True,
        "claim_class": ClaimClass.EFFICIENCY,
        "cost_fields": ["construction_cost"],
        "note": (
            "goal-set reachability-grounded exact field successor (#538); "
            "correct oracle but dominated by cheaper proxies/abstractions"
        ),
    },
    "navigation_dynamics": {
        "artifact": R / "unified_problem_solving_v1/results/navigation_dynamics.json",
        "net_keys": ["net_vs_astar", "advantage_vs_control", "net_expansions_vs_astar"],
        "cost_charged": True,
        "claim_class": ClaimClass.EFFICIENCY,
        "cost_fields": None,
        "note": "must beat the STRONG control (A*) with its own iteration cost charged",
    },
    "navigation_dynamics_successor": {
        "artifact": R / "unified_problem_solving_v1/results/navigation_dynamics_successor.json",
        "net_keys": ["net_vs_strong_parent", "net_vs_astar"],
        "cost_charged": True,
        "claim_class": ClaimClass.EFFICIENCY,
        "cost_fields": ["cost_model"],
        "note": (
            "successor (#537): must beat the strongest amortized parent "
            "with all build+update+query costs charged"
        ),
    },
    "navigation_dynamics_parallel": {
        "artifact": R / "navigation_dynamics_parallel_v1/results/navigation_dynamics_parallel.json",
        "net_keys": ["net_vs_strong_parent", "net_vs_astar"],
        "cost_charged": True,
        "claim_class": ClaimClass.EFFICIENCY,
        "cost_fields": ["cost_model"],
        "note": "parallel-round-depth revival (#537); same mechanic, different registered cost consumer",
    },
    "path_equivalence_quotient": {
        "artifact": R / "unified_problem_solving_v1/results/path_quotient_savings.json",
        "net_keys": ["net_saving_mean"],
        "ci_keys": ["net_saving_ci95"],
        "cost_charged": True,
        "claim_class": ClaimClass.EFFICIENCY,
        "cost_fields": ["verification_cost"],
        "note": "witness/certification cost charged; known negative regime at low commutation",
    },
    "mechanic_diagnosis": {
        "artifact": R / "unified_problem_solving_v1/results/diagnosis_accuracy.json",
        "net_keys": ["forced_wrong_rate", "forced_wrong"],
        "honesty_metric": True,
        "cost_charged": True,
        "claim_class": ClaimClass.CORRECTNESS,
        "cost_fields": None,
        "note": "graded on verdict honesty (degrade to ambiguity, not confident error)",
    },
    "diagnosis_active_successor": {
        "artifact": R / "unified_problem_solving_v1/results/diagnosis_active_successor.json",
        "net_keys": ["net_advantage"],
        "cost_charged": True,
        "claim_class": ClaimClass.CORRECTNESS,
        "cost_fields": ["mean_probe_cost"],
        "note": "leakage-free active sequential diagnosis; honest negative preserved",
    },
    "tcsq_sq3": {
        "artifact": R / "tcsq_sq3_v1/results/sq3.json",
        "net_keys": ["net_advantage", "net_cost_advantage"],
        "cost_charged": True,
        "claim_class": ClaimClass.EFFICIENCY,
        "cost_fields": ["cost_model"],
        "note": "quotient construction cost charged",
    },
    "tcsq_sq3_successor": {
        "artifact": R / "tcsq_sq3_v1/results/sq3_successor.json",
        "net_keys": ["net_advantage"],
        "cost_charged": True,
        "claim_class": ClaimClass.EFFICIENCY,
        "cost_fields": ["cost_model"],
        "note": "per-family validation + certificate verification; regime-conditional successor",
    },
    "identity_reuse": {
        "artifact": R / "identity_reuse_v1/results/identity_reuse.json",
        "net_keys": ["net_advantage", "reuse_advantage"],
        "cost_charged": True,
        "claim_class": ClaimClass.CACHE_REUSE,
        "cost_fields": ["exact_cost", "generic_cost"],
        "note": "exact reuse vs re-derivation; stale-reuse error rate is a hard constraint",
    },
    "six_family_law": {
        "artifact": R / "six_family_extension_v1/results/six_family.json",
        "net_keys": ["sign_test_p", "signs_positive"],
        "sign_test": {
            "p_keys": ["sign_test_p", "sign_test_p_two_sided"],
            "count_keys": ["all_six_positive", "n_positive"],
            "alpha": 0.05,
            "required_count": 6,
        },
        "cost_charged": True,
        "claim_class": ClaimClass.CORRECTNESS,
        "cost_fields": None,
        "note": "cross-family generalization; sign test across >=6 families",
    },
}


def _find(obj, keys):
    """Depth-first search for the first present key among ``keys``."""
    if isinstance(obj, dict):
        for key in keys:
            if key in obj:
                return obj[key]
        for value in obj.values():
            got = _find(value, keys)
            if got is not None:
                return got
    return None


def _ci_excludes_null(value, null=0.0, ci=None):
    """True if an interval lies strictly on one side of ``null``."""
    lo = hi = None
    if isinstance(value, dict) and {"lo", "hi"} <= set(value):
        lo, hi = value["lo"], value["hi"]
    elif isinstance(ci, (list, tuple)) and len(ci) == 2:
        lo, hi = ci
    if lo is None:
        return None
    return lo > null or hi < null


def _is_real_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _verdict_for_sign_test(spec: dict, data: dict, art: Path) -> dict:
    st = spec["sign_test"]
    alpha = st.get("alpha", 0.05)
    required = st.get("required_count", 0)
    p = None
    for key in st.get("p_keys", []):
        candidate = _find(data, [key])
        if _is_real_number(candidate):
            p = candidate
            break
    count_read = False
    count_met = False
    for key in st.get("count_keys", []):
        candidate = _find(data, [key])
        if candidate is None:
            continue
        count_read = True
        if candidate is True or (_is_real_number(candidate) and candidate >= required):
            count_met = True
            break
    if p is None or not count_read:
        return {
            "verdict": "CANNOT_CHECK",
            "reason": f"sign_test_unreadable:p_found={p is not None}_count_read={count_read}",
            "note": spec["note"],
            "artifact": str(art.relative_to(ROOT)),
        }
    if count_met and p < alpha:
        verdict, reason = "PROMOTE_TO_MECHANIC", "sign_test_significant_count_met"
    else:
        verdict, reason = "KEEP_PROPOSAL_ONLY", "sign_test_evidence_insufficient"
    return {
        "verdict": verdict,
        "reason": reason,
        "p": p,
        "alpha": alpha,
        "count_met": count_met,
        "note": spec["note"],
        "artifact": str(art.relative_to(ROOT)),
    }


def _verdict_for_net_metric(spec: dict, data: dict, art: Path) -> dict:
    net = _find(data, spec["net_keys"])
    ci = _find(data, spec.get("ci_keys", [])) if spec.get("ci_keys") else None
    if net is None:
        return {
            "verdict": "CANNOT_CHECK",
            "reason": f"no_net_metric_among:{spec['net_keys']}",
            "note": spec["note"],
            "artifact": str(art.relative_to(ROOT)),
        }

    # Regime evidence is consumed before a pooled mean. A crossover may only
    # promote conditionally and must carry one machine-readable applicability
    # contract shared with runtime routing.
    contract = build_applicability_contract(data.get("regime_analysis"))
    if contract is not None:
        if contract["positive_regime_significant"]:
            verdict = "PROMOTE_CONDITIONALLY"
            reason = "regime_crossover_positive_subregime_ci_excludes_null"
        else:
            verdict = "KEEP_PROPOSAL_ONLY"
            reason = "regime_crossover_no_clean_positive_subregime"
        return {
            "verdict": verdict,
            "reason": reason,
            "net": net,
            "applicability": contract,
            "note": spec["note"],
            "artifact": str(art.relative_to(ROOT)),
        }

    excludes = _ci_excludes_null(net, ci=ci)
    mean = net.get("mean") if isinstance(net, dict) else net
    if excludes is True and _is_real_number(mean) and mean > 0:
        verdict, reason = "PROMOTE_TO_MECHANIC", "positive_net_with_ci_excluding_null_cost_charged"
    elif excludes is True and _is_real_number(mean) and mean < 0:
        verdict, reason = "KEEP_PROPOSAL_ONLY", "net_negative_in_tested_regime"
    elif excludes is False:
        verdict, reason = "KEEP_PROPOSAL_ONLY", "ci_includes_null_no_distinguishable_advantage"
    else:
        verdict, reason = "KEEP_PROPOSAL_ONLY", "net_metric_present_but_interval_unavailable"
    return {
        "verdict": verdict,
        "reason": reason,
        "net": net,
        "note": spec["note"],
        "artifact": str(art.relative_to(ROOT)),
    }


def _apply_telemetry_gate(spec: dict, data: dict, base: dict) -> dict:
    claim_class = spec.get("claim_class")
    out = dict(base)
    if not claim_class:
        return out
    telemetry = telemetry_completeness_status(
        data,
        claim_class,
        economic_cost_fields=spec.get("cost_fields"),
    )
    out["telemetry"] = telemetry
    if (
        claim_class in EFFICIENCY_CLAIM_CLASSES
        and base.get("verdict") == "PROMOTE_TO_MECHANIC"
        and telemetry["status"] != "COMPLETE"
    ):
        if telemetry["status"] == "INVALID_PROSPECTIVE":
            out["verdict"] = "KEEP_PROPOSAL_ONLY"
            out["reason"] = "telemetry_invalid_prospective_collectors_unconfigured"
        else:
            out["verdict"] = "CANNOT_CHECK"
            out["reason"] = "telemetry_incomplete_for_claim_class"
        out["blocked_promotion"] = telemetry["missing"]
        out["pre_telemetry_verdict"] = base.get("verdict")
    return out


def _load_packet_set_safe():
    try:
        return load_packet_set(PACKET_SET_PATH), None
    except Exception as exc:  # packet infrastructure itself fails closed
        return None, f"{type(exc).__name__}:{exc}"


def _research_packet_status(name: str, spec: dict, *, packet_set=None) -> dict:
    if name in PRE_PACKET_LEGACY_CANDIDATES:
        return {
            "status": "LEGACY_PRE_PACKET",
            "gate_required": False,
            "eligible": True,
            "variant_id": None,
            "note": "historical candidate predates #546/#570; successor must use a new id and valid packet",
        }

    variant_id = spec.get("research_packet_variant_id")
    if not variant_id:
        return {
            "status": "MISSING",
            "gate_required": True,
            "eligible": False,
            "variant_id": None,
            "reasons": ["research_packet_variant_id_missing"],
        }

    error = None
    if packet_set is None:
        packet_set, error = _load_packet_set_safe()
    if packet_set is None:
        return {
            "status": "CANNOT_CHECK",
            "gate_required": True,
            "eligible": False,
            "variant_id": variant_id,
            "reasons": [f"packet_set_unavailable:{error}"],
        }

    packet = next((item for item in packet_set.packets if item.variant_id == variant_id), None)
    if packet is None:
        return {
            "status": "MISSING",
            "gate_required": True,
            "eligible": False,
            "variant_id": variant_id,
            "reasons": ["research_packet_not_found"],
        }

    report = validate_mechanic_research_packet(packet)
    expected_mechanic_id = spec.get("research_packet_mechanic_id")
    reasons = list(report.reasons)
    if expected_mechanic_id and packet.mechanic_id != expected_mechanic_id:
        reasons.append("research_packet_mechanic_id_mismatch")

    eligible = (
        report.verdict is MechanicResearchPacketVerdict.READY_FOR_EXISTING_PROMOTION_GATE
        and not reasons
    )
    return {
        "status": "VALID" if eligible else report.verdict.value,
        "gate_required": True,
        "eligible": eligible,
        "variant_id": variant_id,
        "packet_id": packet.packet_id,
        "packet_content_sha256": packet.packet_content_sha256,
        "reasons": reasons,
    }


def _apply_research_packet_gate(name: str, spec: dict, base: dict, *, packet_set=None) -> dict:
    out = dict(base)
    status = _research_packet_status(name, spec, packet_set=packet_set)
    out["research_packet"] = status
    if not status["gate_required"] or status["eligible"]:
        return out
    if out.get("verdict") in {"PROMOTE_TO_MECHANIC", "PROMOTE_CONDITIONALLY"}:
        out["pre_research_packet_verdict"] = out["verdict"]
        out["verdict"] = "KEEP_PROPOSAL_ONLY"
        out["reason"] = "research_packet_missing_or_invalid"
        out["blocked_promotion"] = status.get("reasons", [status["status"]])
    return out


def candidate_registration_problems(*, candidates=None, packet_set=None) -> tuple[str, ...]:
    """Validate that every post-contract candidate is packet-bound before CI can pass."""
    candidates = CANDIDATES if candidates is None else candidates
    problems: list[str] = []
    for name, spec in candidates.items():
        if name in PRE_PACKET_LEGACY_CANDIDATES:
            continue
        status = _research_packet_status(name, spec, packet_set=packet_set)
        if not status["eligible"]:
            rendered = ",".join(status.get("reasons", (status["status"],)))
            problems.append(f"{name}:{rendered}")
    return tuple(problems)


def verdict_for(name: str, spec: dict, *, packet_set=None) -> dict:
    art = spec["artifact"]
    if not art.is_file():
        base = {
            "verdict": "CANNOT_CHECK",
            "reason": "evidence_artifact_missing",
            "artifact": str(art.relative_to(ROOT)),
        }
        return _apply_research_packet_gate(name, spec, base, packet_set=packet_set)
    try:
        data = json.loads(art.read_text())
    except Exception as exc:
        base = {"verdict": "CANNOT_CHECK", "reason": f"unreadable:{type(exc).__name__}"}
        return _apply_research_packet_gate(name, spec, base, packet_set=packet_set)
    if data.get("grants_scientific_authority") is not False:
        base = {"verdict": "CANNOT_CHECK", "reason": "artifact_does_not_disclaim_authority"}
        return _apply_research_packet_gate(name, spec, base, packet_set=packet_set)

    if "sign_test" in spec:
        base = _verdict_for_sign_test(spec, data, art)
    else:
        base = _verdict_for_net_metric(spec, data, art)
    base = _apply_telemetry_gate(spec, data, base)
    return _apply_research_packet_gate(name, spec, base, packet_set=packet_set)


def main() -> int:
    packet_set, packet_error = _load_packet_set_safe()
    rows = {
        name: verdict_for(name, spec, packet_set=packet_set)
        for name, spec in CANDIDATES.items()
    }
    registration_problems = candidate_registration_problems(
        candidates=CANDIDATES,
        packet_set=packet_set,
    )
    out = {
        "schema_version": "orion-promotion-gate-v2",
        "policy": (
            "promotion is routing/engineering status, never scientific authority; "
            "post-#570 candidates require a valid frozen mechanic research packet"
        ),
        "grants_scientific_authority": False,
        "research_packet_contract": {
            "packet_set": str(PACKET_SET_PATH.relative_to(ROOT)),
            "packet_set_error": packet_error,
            "legacy_cutoff_candidate_ids": sorted(PRE_PACKET_LEGACY_CANDIDATES),
            "registration_problems": list(registration_problems),
        },
        "candidates": rows,
        "promoted": sorted(name for name, row in rows.items() if row["verdict"] == "PROMOTE_TO_MECHANIC"),
        "conditionally_promoted": sorted(
            name for name, row in rows.items() if row["verdict"] == "PROMOTE_CONDITIONALLY"
        ),
        "proposal_only": sorted(name for name, row in rows.items() if row["verdict"] == "KEEP_PROPOSAL_ONLY"),
        "cannot_check": sorted(name for name, row in rows.items() if row["verdict"] == "CANNOT_CHECK"),
    }
    dest = R / "unified_problem_solving_v1/results/PROMOTION_GATE.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, sort_keys=True))

    for name, row in sorted(rows.items()):
        print(f"  {row['verdict']:20s} {name}  ({row['reason']})")
    print(
        f"PROMOTED={len(out['promoted'])} "
        f"CONDITIONAL={len(out['conditionally_promoted'])} "
        f"PROPOSAL_ONLY={len(out['proposal_only'])} "
        f"CANNOT_CHECK={len(out['cannot_check'])}"
    )
    print(f"RESEARCH_PACKET_REGISTRATION_PROBLEMS={len(registration_problems)}")
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    return 1 if registration_problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
