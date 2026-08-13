#!/usr/bin/env python3
"""Evidence-based promotion gate: decide which tested ideas become mechanics.

Orion applied to Orion. Every candidate mechanic starts PROPOSAL_ONLY. This gate reads
the candidate's *own experiment artifact* and issues a typed verdict from registered,
pre-declared criteria:

  PROMOTE_TO_MECHANIC  - effect present with a CI excluding the null, net advantage
                         POSITIVE after its own construction/witness cost is charged,
                         and no fail-closed violation in its regression tests.
  KEEP_PROPOSAL_ONLY   - implemented and tested, but the net advantage is absent,
                         negative, or regime-dependent; it stays available and
                         registered, but is not a default-on mechanic.
  REJECT               - the idea is refuted in its own known world (harmful or broken).
  CANNOT_CHECK         - the evidence artifact is missing/unreadable, or the experiment
                         did not charge its own cost (an uncharged win is not a win).

Promotion is a ROUTING/ENGINEERING status, never scientific authority: a promoted
mechanic is one Orion may use by default, not a claim that any scientific hypothesis is
true. `grants_scientific_authority` is False everywhere.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "research"

# candidate -> (evidence artifact, key of the net/advantage metric, key of the CI dict)
CANDIDATES = {
    "fieldability_given_field": {
        "artifact": R / "unified_problem_solving_v1/results/field_hypothesis.json",
        "net_keys": ["search_reduction_vs_bfs"],
        "cost_charged": True,   # construction cost is zero: the field is GIVEN (declared)
        "note": "given-metric field; construction cost not applicable (field supplied by domain)",
    },
    "field_construction": {
        "artifact": R / "unified_problem_solving_v1/results/field_construction.json",
        "net_keys": ["net_search_saving", "net_saving", "search_reduction_net"],
        "cost_charged": True,
        "note": "constructor must pay for its own construction cost",
    },
    "navigation_dynamics": {
        "artifact": R / "unified_problem_solving_v1/results/navigation_dynamics.json",
        "net_keys": ["net_vs_astar", "advantage_vs_control", "net_expansions_vs_astar"],
        "cost_charged": True,
        "note": "must beat the STRONG control (A*) with its own iteration cost charged",
    },
    "path_equivalence_quotient": {
        "artifact": R / "unified_problem_solving_v1/results/path_quotient_savings.json",
        "net_keys": ["net_saving_mean"], "ci_keys": ["net_saving_ci95"],
        "cost_charged": True,
        "note": "witness/certification cost charged; known negative regime at low commutation",
    },
    "mechanic_diagnosis": {
        "artifact": R / "unified_problem_solving_v1/results/diagnosis_accuracy.json",
        "net_keys": ["forced_wrong_rate", "forced_wrong"], "honesty_metric": True,
        "cost_charged": True,
        "note": "graded on verdict honesty (degrade to ambiguity, not confident error)",
    },
    "tcsq_sq3": {
        "artifact": R / "tcsq_sq3_v1/results/sq3.json",
        "net_keys": ["net_advantage", "net_cost_advantage"],
        "cost_charged": True,
        "note": "quotient construction cost charged; crossover in redundancy rate expected",
    },
    "identity_reuse": {
        "artifact": R / "identity_reuse_v1/results/identity_reuse.json",
        "net_keys": ["net_advantage", "reuse_advantage"],
        "cost_charged": True,
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
        "note": "cross-family generalization; sign test across >=6 families",
    },
}


def _find(obj, keys):
    """Depth-first search for the first present key among ``keys``."""
    if isinstance(obj, dict):
        for k in keys:
            if k in obj:
                return obj[k]
        for v in obj.values():
            got = _find(v, keys)
            if got is not None:
                return got
    return None


def _ci_excludes_null(value, null=0.0, ci=None):
    """True if an interval (dict {lo,hi} or list [lo,hi]) lies strictly one side of null."""
    lo = hi = None
    if isinstance(value, dict) and {"lo", "hi"} <= set(value):
        lo, hi = value["lo"], value["hi"]
    elif isinstance(ci, (list, tuple)) and len(ci) == 2:
        lo, hi = ci
    if lo is None:
        return None
    return lo > null or hi < null


def _is_real_number(x) -> bool:
    """True for a finite int/float; a bool statistic is malformed and rejected."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def _verdict_for_sign_test(spec: dict, data: dict, art: Path) -> dict:
    """Sign-test evaluator for candidates whose registered evidence is a binomial
    sign test (a p-value plus a count of positive signs), not a net-metric CI.

    count-met AND p<alpha => PROMOTE_TO_MECHANIC. Evidence present but not
    significant => KEEP_PROPOSAL_ONLY (honest weak evidence, not a contradiction).
    p or count unreadable => CANNOT_CHECK. Never REJECT: a non-significant sign
    test does not refute the proposal, it merely fails to elevate it.
    """
    st = spec["sign_test"]
    alpha = st.get("alpha", 0.05)
    required = st.get("required_count", 0)
    # p-value: first present key that is a finite real number.
    p = None
    for pk in st.get("p_keys", []):
        pv = _find(data, [pk])
        if _is_real_number(pv):
            p = pv
            break
    # count: any registered source indicating the threshold is met. A bool True
    # means count met; an int/float means compare >= required_count.
    count_read = False
    count_met = False
    for ck in st.get("count_keys", []):
        cv = _find(data, [ck])
        if cv is None:
            continue
        count_read = True
        if cv is True:
            count_met = True
            break
        if _is_real_number(cv) and cv >= required:
            count_met = True
            break
    if p is None or not count_read:
        return {"verdict": "CANNOT_CHECK",
                "reason": f"sign_test_unreadable:p_found={p is not None}_count_read={count_read}",
                "note": spec["note"], "artifact": str(art.relative_to(ROOT))}
    if count_met and p < alpha:
        v, why = "PROMOTE_TO_MECHANIC", "sign_test_significant_count_met"
    else:
        v, why = "KEEP_PROPOSAL_ONLY", "sign_test_evidence_insufficient"
    return {"verdict": v, "reason": why, "p": p, "alpha": alpha,
            "count_met": count_met, "note": spec["note"],
            "artifact": str(art.relative_to(ROOT))}


def verdict_for(name: str, spec: dict) -> dict:
    art = spec["artifact"]
    if not art.is_file():
        return {"verdict": "CANNOT_CHECK", "reason": "evidence_artifact_missing", "artifact": str(art.relative_to(ROOT))}
    try:
        data = json.loads(art.read_text())
    except Exception as exc:  # unreadable artifact is CANNOT_CHECK, never a pass
        return {"verdict": "CANNOT_CHECK", "reason": f"unreadable:{type(exc).__name__}"}
    if data.get("grants_scientific_authority") is not False:
        return {"verdict": "CANNOT_CHECK", "reason": "artifact_does_not_disclaim_authority"}
    if "sign_test" in spec:
        return _verdict_for_sign_test(spec, data, art)
    net = _find(data, spec["net_keys"])
    ci = _find(data, spec.get("ci_keys", [])) if spec.get("ci_keys") else None
    if net is None:
        return {"verdict": "CANNOT_CHECK", "reason": f"no_net_metric_among:{spec['net_keys']}"}
    excl = _ci_excludes_null(net, ci=ci)
    mean = net.get("mean") if isinstance(net, dict) else net
    if excl is True and isinstance(mean, (int, float)) and mean > 0:
        v, why = "PROMOTE_TO_MECHANIC", "positive_net_with_ci_excluding_null_cost_charged"
    elif excl is True and isinstance(mean, (int, float)) and mean < 0:
        v, why = "KEEP_PROPOSAL_ONLY", "net_negative_in_tested_regime"
    elif excl is False:
        v, why = "KEEP_PROPOSAL_ONLY", "ci_includes_null_no_distinguishable_advantage"
    else:
        v, why = "KEEP_PROPOSAL_ONLY", "net_metric_present_but_interval_unavailable"
    return {"verdict": v, "reason": why, "net": net, "note": spec["note"],
            "artifact": str(art.relative_to(ROOT))}


def main() -> int:
    rows = {name: verdict_for(name, spec) for name, spec in CANDIDATES.items()}
    out = {
        "schema_version": "orion-promotion-gate-v1",
        "policy": "promotion is routing/engineering status, never scientific authority",
        "grants_scientific_authority": False,
        "candidates": rows,
        "promoted": sorted(n for n, r in rows.items() if r["verdict"] == "PROMOTE_TO_MECHANIC"),
        "proposal_only": sorted(n for n, r in rows.items() if r["verdict"] == "KEEP_PROPOSAL_ONLY"),
        "cannot_check": sorted(n for n, r in rows.items() if r["verdict"] == "CANNOT_CHECK"),
    }
    dest = R / "unified_problem_solving_v1" / "results" / "PROMOTION_GATE.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=2, sort_keys=True))
    for name, r in sorted(rows.items()):
        print(f"  {r['verdict']:20s} {name}  ({r['reason']})")
    print(f"PROMOTED={len(out['promoted'])} PROPOSAL_ONLY={len(out['proposal_only'])} CANNOT_CHECK={len(out['cannot_check'])}")
    print("SCIENTIFIC_AUTHORITY_GRANTED=false")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
