#!/usr/bin/env python3
"""Fresh assurance + falsifiability audit for the oracle-ceiling admissibility gate.

Executes, with seeds disjoint from every Paper IV development artifact:

1. the five fresh-assurance cases declared in
   ``research/paper4_instrument_admissibility_v1/KAPPA_FREEZE_V1.json``
   (expected verdicts frozen there BEFORE this runner existed);
2. the formal admissibility verdict on the preserved reference instrument
   (evidence: ``research/paper4_allocator_attribution_v1/CEILING_BOUNDS.json``);
3. a per-condition black-box falsifiability audit of the gate via
   ``src/rakl/gate_falsifiability.py`` — control condition first, with the
   expected SENSITIVE/INSENSITIVE outcome of every probe declared in this file
   before execution.  Expected-INSENSITIVE rows assert the no-alarm case (e.g.
   fail-closed invariance of CANNOT_CHECK under bound inflation).

Diagnostic only.  Grants no scientific authority; promotes nothing; reverses
no terminal.  A failed expectation is recorded as FAIL, never adjusted.
"""
from __future__ import annotations

import argparse
import json
import random
from dataclasses import asdict
from itertools import combinations_with_replacement
from pathlib import Path

from rakl.gate_falsifiability import audit_gate
from rakl.instrument_admissibility import (
    AdmissibilityVerdict,
    BoundKind,
    CeilingBound,
    CeilingEvidence,
    FrozenAdmissibilityDeclaration,
    OracleComputability,
    decide_instrument_admissibility,
)

FRESH_SEED = 202608141101  # disjoint from 202608140601 (development stress)


# --- expected-dynamics machinery (per-case, deterministic) ---------------------------


def rollout_separable(counts, coords, rates, m0, harms, budget):
    """Expected-dynamics rollout with the v1 harm structure, max-remaining-first."""
    ci = {c: i for i, c in enumerate(coords)}
    m = list(m0)
    remaining = dict(counts)
    for _ in range(budget):
        c = max(coords, key=lambda k: (remaining.get(k, 0), -ci[k]))
        if remaining.get(c, 0) <= 0:
            break
        remaining[c] -= 1
        m[ci[c]] += rates[c] * (1 - m[ci[c]])
        if harms and c != "PRINCIPLE":
            m[ci["PRINCIPLE"]] -= harms["forgetting_per_nonprinciple_example"]
        if harms and c != "RETENTION":
            m[ci["RETENTION"]] -= harms["retention_harm_per_nonretention_example"]
        m = [max(0.0, min(0.999, x)) for x in m]
    return sum(m) / len(coords)


def rollout_synergy(counts, coords, rates, m0, partners, strength, budget):
    """Expected-dynamics rollout with multiplicative cross-coordinate synergy."""
    ci = {c: i for i, c in enumerate(coords)}
    m = list(m0)
    remaining = dict(counts)
    for _ in range(budget):
        c = max(coords, key=lambda k: (remaining.get(k, 0), -ci[k]))
        if remaining.get(c, 0) <= 0:
            break
        remaining[c] -= 1
        gain = rates[c] * (1 - m[ci[c]]) * (1 + strength * m[ci[partners[c]]])
        m[ci[c]] = max(0.0, min(0.999, m[ci[c]] + gain))
    return sum(m) / len(coords)


def hill_climb(score, start, coords):
    cur = dict(start)
    best = score(cur)
    improved = True
    while improved:
        improved = False
        for a in coords:
            for b in coords:
                if a == b or cur.get(a, 0) <= 0:
                    continue
                cand = dict(cur)
                cand[a] -= 1
                cand[b] = cand.get(b, 0) + 1
                val = score(cand)
                if val > best + 1e-12:
                    best, cur, improved = val, cand, True
    return best, cur


def harm_free_upper_bound(coords, rates, m0, budget):
    """Exact optimum of the harm-free separable relaxation (greedy water-filling)."""
    ci = {c: i for i, c in enumerate(coords)}
    val = {c: m0[ci[c]] for c in coords}
    for _ in range(budget):
        best = max(coords, key=lambda c: (rates[c] * (1 - val[c]), -ci[c]))
        val[best] += rates[best] * (1 - val[best])
    return sum(val.values()) / len(coords)


# --- fresh-assurance case construction ----------------------------------------------


def build_cases(freeze):
    """Return {case_id: (declaration, evidence, expected_verdict, detail)}."""
    kappa = freeze["frozen_kappa"]
    rng = random.Random(FRESH_SEED)
    cases = {}

    def decl(instrument_id, mde=0.05):
        return FrozenAdmissibilityDeclaration(
            instrument_id=instrument_id,
            registered_primary_metric="balanced_mastery_advantage_over_static",
            registered_minimum_detectable_effect=mde,
            frozen_kappa=kappa,
            declared_on=freeze["date"],
            rationale="fresh-assurance case under KAPPA_FREEZE_V1",
        )

    # 1. Every arm structurally forced to one identical allocation: singleton
    #    allocation space, ceiling exactly zero, analytically.
    cases["FRESH_DEGENERATE_ZERO_HEADROOM"] = (
        decl("FRESH_DEGENERATE_ZERO_HEADROOM"),
        CeilingEvidence(
            instrument_id="FRESH_DEGENERATE_ZERO_HEADROOM",
            oracle_computability=OracleComputability.COMPUTABLE,
            equal_budget_verified=True,
            reference_parent_arm_id="D_STATIC_STRUCTURAL",
            bounds=(
                CeilingBound(
                    "singleton_allocation_space",
                    BoundKind.EXACT,
                    0.0,
                    "protocol forces every arm to the identical allocation; "
                    "advantage over the reference parent is identically zero",
                ),
            ),
        ),
        AdmissibilityVerdict.INADMISSIBLE,
        {"construction": "singleton allocation space"},
    )

    # 2. State-divergent initial mastery, high headroom.  Six coordinates,
    #    two deficient (m0=0.10) with the rest near-saturated (m0=0.96);
    #    v1-style harm structure retained.
    coords = ["PRINCIPLE", "COMPOSITION", "BOUNDARY", "REPRESENTATION", "TRANSFER", "RETENTION"]
    rates = {"PRINCIPLE": 0.17, "COMPOSITION": 0.10, "BOUNDARY": 0.09,
             "REPRESENTATION": 0.10, "TRANSFER": 0.08, "RETENTION": 0.11}
    m0 = [0.96, 0.10, 0.96, 0.10, 0.96, 0.96]
    m0 = [max(0.0, min(0.99, x + (rng.random() - 0.5) * 0.02)) for x in m0]
    harms = {"forgetting_per_nonprinciple_example": 0.0025,
             "retention_harm_per_nonretention_example": 0.0015}
    budget = 48
    uniform = {c: budget // len(coords) for c in coords}
    static = rollout_separable(uniform, coords, rates, m0, harms, budget)

    def score2(counts):
        return rollout_separable(counts, coords, rates, m0, harms, budget)

    concentrated = {"PRINCIPLE": 2, "COMPOSITION": 20, "BOUNDARY": 2,
                    "REPRESENTATION": 20, "TRANSFER": 2, "RETENTION": 2}
    best2 = max(hill_climb(score2, uniform, coords)[0],
                hill_climb(score2, concentrated, coords)[0])
    ub2 = harm_free_upper_bound(coords, rates, m0, budget) - static
    cases["FRESH_STATE_DIVERGENT_INITIAL_MASTERY_HIGH_HEADROOM"] = (
        decl("FRESH_STATE_DIVERGENT_INITIAL_MASTERY_HIGH_HEADROOM"),
        CeilingEvidence(
            instrument_id="FRESH_STATE_DIVERGENT_INITIAL_MASTERY_HIGH_HEADROOM",
            oracle_computability=OracleComputability.COMPUTABLE,
            equal_budget_verified=True,
            reference_parent_arm_id="STATIC_UNIFORM_8",
            bounds=(
                CeilingBound("tier2_constructive", BoundKind.LOWER_BOUND, best2 - static,
                             "hill-climb over count vectors, expected dynamics with harms"),
                CeilingBound("tier3_harm_free_relaxation", BoundKind.UPPER_BOUND, ub2,
                             "harm-free separable relaxation, exact greedy water-filling"),
            ),
        ),
        AdmissibilityVerdict.ADMISSIBLE,
        {"construction": "two deficient coordinates at ~0.10, four near-saturated at ~0.96",
         "static_score": static, "constructive_minus_static": best2 - static,
         "upper_bound_minus_static": ub2},
    )

    # 3. Nonseparable cross-coordinate synergy: mutually-partnered deficits.
    #    The separable water-filling optimality argument does not apply, so NO
    #    upper bound is supplied; the gate must reach ADMISSIBLE on the
    #    constructive lower bound alone.
    coords3 = ["ALPHA", "BETA", "GAMMA", "DELTA"]
    rates3 = {"ALPHA": 0.08, "BETA": 0.10, "GAMMA": 0.08, "DELTA": 0.12}
    partners = {"ALPHA": "GAMMA", "GAMMA": "ALPHA", "BETA": "DELTA", "DELTA": "BETA"}
    m03 = [0.02, 0.97, 0.02, 0.97]
    m03 = [max(0.0, min(0.99, x + (rng.random() - 0.5) * 0.02)) for x in m03]
    budget3 = 40
    uniform3 = {c: budget3 // len(coords3) for c in coords3}
    static3 = rollout_synergy(uniform3, coords3, rates3, m03, partners, 1.0, budget3)

    def score3(counts):
        return rollout_synergy(counts, coords3, rates3, m03, partners, 1.0, budget3)

    concentrated3 = {"ALPHA": 19, "BETA": 1, "GAMMA": 19, "DELTA": 1}
    best3 = max(hill_climb(score3, uniform3, coords3)[0],
                hill_climb(score3, concentrated3, coords3)[0])
    cases["FRESH_NONSEPARABLE_CROSS_COORDINATE_SYNERGY"] = (
        decl("FRESH_NONSEPARABLE_CROSS_COORDINATE_SYNERGY"),
        CeilingEvidence(
            instrument_id="FRESH_NONSEPARABLE_CROSS_COORDINATE_SYNERGY",
            oracle_computability=OracleComputability.COMPUTABLE,
            equal_budget_verified=True,
            reference_parent_arm_id="STATIC_UNIFORM_10",
            bounds=(
                CeilingBound("tier2_constructive", BoundKind.LOWER_BOUND, best3 - static3,
                             "hill-climb over count vectors, expected synergy dynamics; "
                             "no monotone separable relaxation exists, so no upper bound"),
            ),
        ),
        AdmissibilityVerdict.ADMISSIBLE,
        {"construction": "mutually-partnered deficits, multiplicative synergy strength 1.0",
         "static_score": static3, "constructive_minus_static": best3 - static3},
    )

    # 4. Real-model stub: generative parameters unknown, oracle uncomputable.
    #    Even a large CLAIMED lower bound must not produce ADMISSIBLE.
    cases["FRESH_UNCOMPUTABLE_ORACLE_STUB"] = (
        decl("FRESH_UNCOMPUTABLE_ORACLE_STUB"),
        CeilingEvidence(
            instrument_id="FRESH_UNCOMPUTABLE_ORACLE_STUB",
            oracle_computability=OracleComputability.UNCOMPUTABLE,
            equal_budget_verified=True,
            reference_parent_arm_id="STATIC_PARENT",
            bounds=(
                CeilingBound("claimed_headroom", BoundKind.LOWER_BOUND, 0.40,
                             "asserted without a computable oracle"),
            ),
        ),
        AdmissibilityVerdict.CANNOT_CHECK,
        {"construction": "generative parameters withheld"},
    )

    # 5. Exactly-solvable two-coordinate instrument whose exact optimum sits in
    #    the open interval (MDE, kappa*MDE): above the MDE, below the frozen
    #    threshold.  The deficient coordinate's initial mastery is swept
    #    deterministically until the exact advantage lands in the band.
    mde5 = 0.05
    lo, hi = mde5, kappa * mde5
    coords5 = ["WEAK", "STRONG"]
    rates5 = {"WEAK": 0.09, "STRONG": 0.12}
    budget5 = 10
    chosen = None
    for step in range(0, 900):
        m0w = 0.90 - step * 0.001
        m05 = [m0w, 0.93]
        best_exact = None
        for kw in range(budget5 + 1):
            counts = {"WEAK": kw, "STRONG": budget5 - kw}
            v = rollout_separable(counts, coords5, rates5, m05, None, budget5)
            if best_exact is None or v > best_exact:
                best_exact = v
        static5 = rollout_separable({"WEAK": 5, "STRONG": 5}, coords5, rates5, m05, None, budget5)
        adv = best_exact - static5
        if lo < adv < hi:
            chosen = (m0w, adv, static5)
            break
    if chosen is None:
        raise SystemExit("FRESH_CEILING_MARGINALLY_ABOVE_MDE: no parameter landed in band")
    m0w, adv5, static5 = chosen
    cases["FRESH_CEILING_MARGINALLY_ABOVE_MDE"] = (
        decl("FRESH_CEILING_MARGINALLY_ABOVE_MDE", mde=mde5),
        CeilingEvidence(
            instrument_id="FRESH_CEILING_MARGINALLY_ABOVE_MDE",
            oracle_computability=OracleComputability.COMPUTABLE,
            equal_budget_verified=True,
            reference_parent_arm_id="STATIC_UNIFORM_5",
            bounds=(
                CeilingBound("exact_enumeration", BoundKind.EXACT, adv5,
                             "brute-force enumeration of every count vector, "
                             "deterministic expected dynamics"),
            ),
        ),
        AdmissibilityVerdict.INADMISSIBLE,
        {"construction": f"deficient initial mastery swept to {m0w:.3f}",
         "exact_advantage": adv5, "band": [lo, hi], "static_score": static5},
    )
    return cases


def reference_case(freeze, ceiling_bounds):
    decl = FrozenAdmissibilityDeclaration(
        instrument_id="research/orion_p1_p4_closure_v2/P4_ADAPTIVE_PROTOCOL_FREEZE.json",
        registered_primary_metric="E_minus_D_balanced_mastery",
        registered_minimum_detectable_effect=ceiling_bounds[
            "frozen_hard_gate_E_minus_D_balanced_mean_min"],
        frozen_kappa=freeze["frozen_kappa"],
        declared_on=freeze["date"],
        rationale="formalization of the preserved reference-instrument ceiling; "
                  "see KAPPA_FREEZE_V1 chronology_disclosure",
    )
    tiers = ceiling_bounds["bounds_on_achievable_advantage_over_static"]
    evidence = CeilingEvidence(
        instrument_id=decl.instrument_id,
        oracle_computability=OracleComputability.COMPUTABLE,
        equal_budget_verified=True,
        reference_parent_arm_id="D_STATIC_STRUCTURAL",
        bounds=(
            CeilingBound("tier1_greedy_oracle_policy", BoundKind.LOWER_BOUND,
                         tiers["tier_1_greedy_oracle_policy_stochastic_mean"],
                         "greedy oracle policy rollout (stochastic mean)"),
            CeilingBound("tier2_constructive", BoundKind.LOWER_BOUND,
                         tiers["tier_2_constructive_best_found_expected_dynamics_mean"],
                         "hill-climb over count vectors, expected dynamics"),
            CeilingBound("tier3_harm_free_relaxation", BoundKind.UPPER_BOUND,
                         tiers["tier_3_rigorous_upper_bound_harm_free_relaxation_mean"],
                         "harm-free separable relaxation, exact greedy water-filling"),
        ),
    )
    return decl, evidence


# --- falsifiability audit ------------------------------------------------------------


def rows_from(evidence: CeilingEvidence):
    rows = [
        {"row": "bound", "bound_id": b.bound_id, "kind": b.kind.value, "value": b.value}
        for b in evidence.bounds
    ]
    rows.append({
        "row": "status",
        "oracle_computability": evidence.oracle_computability.value,
        "equal_budget_verified": evidence.equal_budget_verified,
    })
    return rows


def evidence_from_rows(rows, template: CeilingEvidence) -> CeilingEvidence:
    bounds = []
    computability = template.oracle_computability
    equal_budget = template.equal_budget_verified
    for row in rows:
        if row.get("row") == "bound":
            bounds.append(CeilingBound(row["bound_id"], BoundKind(row["kind"]),
                                       row["value"], "perturbed"))
        elif row.get("row") == "status":
            computability = OracleComputability(row["oracle_computability"])
            equal_budget = bool(row["equal_budget_verified"])
    return CeilingEvidence(
        instrument_id=template.instrument_id,
        oracle_computability=computability,
        equal_budget_verified=equal_budget,
        reference_parent_arm_id=template.reference_parent_arm_id,
        bounds=tuple(bounds),
    )


def _map_bounds(fn):
    """Perturb every bound value with ONE shared draw per trial.

    The draw is shared deliberately: an earlier version drew an independent
    factor per bound row, which sometimes scaled a lower bound above an upper
    bound — genuinely inconsistent evidence that the gate correctly refuses as
    CANNOT_CHECK.  Those flips were false alarms of the probe harness, not gate
    sensitivity; a shared draw preserves bound ordering.  The correction is a
    probe repair made after observing the first audit run and is recorded here
    rather than hidden; the gate itself was not changed.
    """
    def perturb(evidence_rows, rng):
        draw = rng.random()
        out = []
        for row in evidence_rows:
            row = dict(row)
            if row.get("row") == "bound":
                row["value"] = fn(row["value"], draw)
            out.append(row)
        return out
    return perturb


def _set_status(**updates):
    def perturb(evidence_rows, rng):
        out = []
        for row in evidence_rows:
            row = dict(row)
            if row.get("row") == "status":
                row.update(updates)
            out.append(row)
        return out
    return perturb


def _drop_kind(kind):
    def perturb(evidence_rows, rng):
        return [row for row in evidence_rows
                if not (row.get("row") == "bound" and row["kind"] == kind)]
    return perturb


PROBES = {
    "attenuate_bounds": _map_bounds(lambda v, u: v * (1e-4 + u * (1e-2 - 1e-4))),
    "inflate_bounds": _map_bounds(lambda v, u: v * (20.0 + u * 80.0)),
    "add_headroom": _map_bounds(lambda v, u: v + 0.2 + u * 0.8),
    "mark_oracle_uncomputable": _set_status(oracle_computability="UNCOMPUTABLE"),
    "mark_oracle_computable": _set_status(oracle_computability="COMPUTABLE"),
    "unset_equal_budget": _set_status(equal_budget_verified=False),
    "drop_upper_bounds": _drop_kind("UPPER_BOUND"),
    "drop_lower_bounds": _drop_kind("LOWER_BOUND"),
}

# Expected probe outcomes, declared before execution.  S = SENSITIVE (the probe
# must be able to move the verdict), I = INSENSITIVE (the verdict must NOT move
# — an asserted no-alarm case).  The control condition is audited first.
EXPECTED = {
    "CONTROL_FRESH_STATE_DIVERGENT_INITIAL_MASTERY_HIGH_HEADROOM": {
        "attenuate_bounds": "SENSITIVE",
        "inflate_bounds": "INSENSITIVE",
        "mark_oracle_uncomputable": "SENSITIVE",
        "unset_equal_budget": "SENSITIVE",
        "drop_lower_bounds": "SENSITIVE",
        "drop_upper_bounds": "INSENSITIVE",
    },
    "REFERENCE_P4_DEVELOPMENT_STRESS_INSTRUMENT": {
        "inflate_bounds": "SENSITIVE",
        "attenuate_bounds": "INSENSITIVE",
        "mark_oracle_uncomputable": "SENSITIVE",
        "unset_equal_budget": "SENSITIVE",
        "drop_upper_bounds": "SENSITIVE",
        "drop_lower_bounds": "INSENSITIVE",
    },
    "FRESH_DEGENERATE_ZERO_HEADROOM": {
        "add_headroom": "SENSITIVE",
        "attenuate_bounds": "INSENSITIVE",
        "inflate_bounds": "INSENSITIVE",
        "mark_oracle_uncomputable": "SENSITIVE",
        "unset_equal_budget": "SENSITIVE",
    },
    "FRESH_NONSEPARABLE_CROSS_COORDINATE_SYNERGY": {
        "attenuate_bounds": "SENSITIVE",
        "inflate_bounds": "INSENSITIVE",
        "mark_oracle_uncomputable": "SENSITIVE",
        "unset_equal_budget": "SENSITIVE",
        "drop_lower_bounds": "SENSITIVE",
    },
    "FRESH_UNCOMPUTABLE_ORACLE_STUB": {
        "inflate_bounds": "INSENSITIVE",
        "attenuate_bounds": "INSENSITIVE",
        "add_headroom": "INSENSITIVE",
        "mark_oracle_computable": "SENSITIVE",
    },
    "FRESH_CEILING_MARGINALLY_ABOVE_MDE": {
        "inflate_bounds": "SENSITIVE",
        "attenuate_bounds": "INSENSITIVE",
        "mark_oracle_uncomputable": "SENSITIVE",
        "unset_equal_budget": "SENSITIVE",
    },
}


def audit_condition(condition_id, decl, evidence, expected):
    baseline = decide_instrument_admissibility(decl, evidence).verdict

    def gate(rows):
        return decide_instrument_admissibility(
            decl, evidence_from_rows(rows, evidence)
        ).verdict is baseline

    report = audit_gate(
        gate,
        rows_from(evidence),
        gate_id=condition_id,
        perturbations={k: PROBES[k] for k in expected},
        trials=32,
        seed=FRESH_SEED,
    )
    probe_rows = []
    all_match = True
    by_id = {p.probe_id: p for p in report.probes}
    for probe_id, want in expected.items():
        got = by_id[probe_id].outcome.value if probe_id in by_id else "MISSING"
        match = got == want
        all_match = all_match and match
        probe_rows.append({
            "probe_id": probe_id,
            "expected": want,
            "observed": got,
            "flips": by_id[probe_id].flips if probe_id in by_id else None,
            "trials": by_id[probe_id].trials if probe_id in by_id else None,
            "match": match,
        })
    return {
        "condition_id": condition_id,
        "baseline_verdict": baseline.value,
        "gate_falsifiability_verdict": report.verdict.value,
        "probes": probe_rows,
        "condition_pass": all_match and report.verdict.value == "FALSIFIABLE",
    }


def serialize_decision(decision):
    d = asdict(decision)
    for k, v in list(d.items()):
        if hasattr(v, "value"):
            d[k] = v.value
    d["grants_scientific_authority"] = decision.grants_scientific_authority
    d["licenses_comparison_execution"] = decision.licenses_comparison_execution
    d["upgradeable_by_outcome_access"] = decision.upgradeable_by_outcome_access
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--freeze", required=True)
    ap.add_argument("--reference-bounds", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    freeze = json.loads(Path(args.freeze).read_text())
    ceiling_bounds = json.loads(Path(args.reference_bounds).read_text())
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    # 1. fresh-assurance verdicts
    cases = build_cases(freeze)
    case_rows = []
    all_pass = True
    for case_id, (decl, evidence, expected_verdict, detail) in cases.items():
        decision = decide_instrument_admissibility(decl, evidence)
        match = decision.verdict is expected_verdict
        all_pass = all_pass and match
        case_rows.append({
            "case_id": case_id,
            "expected_verdict": expected_verdict.value,
            "decision": serialize_decision(decision),
            "match": match,
            "detail": detail,
        })

    # 2. reference-instrument formal verdict
    ref_decl, ref_evidence = reference_case(freeze, ceiling_bounds)
    ref_decision = decide_instrument_admissibility(ref_decl, ref_evidence)
    reference_receipt = {
        "schema_version": "p4-reference-instrument-admissibility-v1",
        "date": freeze["date"],
        "kind": "FORMAL_ADMISSIBILITY_VERDICT_ON_PRESERVED_REFERENCE_INSTRUMENT",
        "evidence_source": args.reference_bounds,
        "kappa_freeze": args.freeze,
        "chronology": "ceiling computed before this freeze; verdict is a formalization "
                      "of a preserved finding and is kappa-insensitive for kappa > 0.4914 "
                      "(see KAPPA_FREEZE_V1 chronology_disclosure)",
        "decision": serialize_decision(ref_decision),
        "consequence": "the frozen development-stress comparison would not have been "
                       "licensed for confirmatory execution; the preserved adaptive-v1 "
                       "negative and every existing terminal remain byte-unchanged",
        "grants_scientific_authority": False,
    }
    (out / "REFERENCE_INSTRUMENT_ADMISSIBILITY.json").write_text(
        json.dumps(reference_receipt, indent=2) + "\n")

    # 3. falsifiability audit, control first
    conditions = [
        ("CONTROL_FRESH_STATE_DIVERGENT_INITIAL_MASTERY_HIGH_HEADROOM",
         *cases["FRESH_STATE_DIVERGENT_INITIAL_MASTERY_HIGH_HEADROOM"][:2]),
        ("REFERENCE_P4_DEVELOPMENT_STRESS_INSTRUMENT", ref_decl, ref_evidence),
        ("FRESH_DEGENERATE_ZERO_HEADROOM", *cases["FRESH_DEGENERATE_ZERO_HEADROOM"][:2]),
        ("FRESH_NONSEPARABLE_CROSS_COORDINATE_SYNERGY",
         *cases["FRESH_NONSEPARABLE_CROSS_COORDINATE_SYNERGY"][:2]),
        ("FRESH_UNCOMPUTABLE_ORACLE_STUB", *cases["FRESH_UNCOMPUTABLE_ORACLE_STUB"][:2]),
        ("FRESH_CEILING_MARGINALLY_ABOVE_MDE",
         *cases["FRESH_CEILING_MARGINALLY_ABOVE_MDE"][:2]),
    ]
    audit_rows = []
    audit_pass = True
    for condition_id, decl, evidence in conditions:
        row = audit_condition(condition_id, decl, evidence, EXPECTED[condition_id])
        audit_rows.append(row)
        audit_pass = audit_pass and row["condition_pass"]

    (out / "GATE_FALSIFIABILITY_AUDIT.json").write_text(json.dumps({
        "schema_version": "p4-gate-falsifiability-audit-v1",
        "date": freeze["date"],
        "kind": "PER_CONDITION_BLACK_BOX_FALSIFIABILITY_AUDIT",
        "auditor": "src/rakl/gate_falsifiability.py::audit_gate",
        "note": "expected outcomes were declared in the runner before execution; "
                "INSENSITIVE-expected rows assert the no-alarm case; control first",
        "conditions": audit_rows,
        "all_conditions_pass": audit_pass,
        "grants_scientific_authority": False,
    }, indent=2) + "\n")

    # Same-system ablation (packet obligation): replace the oracle upper bound
    # with the strongest implementable policy score only.  This is exactly the
    # drop_upper_bounds probe; on the reference instrument it must flip
    # INADMISSIBLE -> CANNOT_CHECK, showing the upper-bound component carries
    # the mechanic (a policy score alone can never license INADMISSIBLE).
    ref_audit = next(r for r in audit_rows
                     if r["condition_id"] == "REFERENCE_P4_DEVELOPMENT_STRESS_INSTRUMENT")
    drop_upper = next(p for p in ref_audit["probes"] if p["probe_id"] == "drop_upper_bounds")
    ablation = {
        "obligation": "same_system_ablation from PACKET_oracle_ceiling_calibration_gate_v1",
        "implementation": "drop_upper_bounds probe on the reference instrument: evidence "
                          "reduced to implementable policy scores (tier 1 greedy, tier 2 "
                          "constructive) with the tier-3 upper bound removed",
        "verdict_changed": drop_upper["observed"] == "SENSITIVE",
        "flips": drop_upper["flips"],
        "trials": drop_upper["trials"],
        "reading": "the INADMISSIBLE verdict is carried by the upper-bound component; "
                   "without it the gate fails closed to CANNOT_CHECK rather than "
                   "reducing to strongest-parent reporting — the novelty residual "
                   "is not withdrawn"
        if drop_upper["observed"] == "SENSITIVE" else
        "verdicts unchanged without the oracle component — the gate reduces to "
        "strongest-parent reporting and the novelty residual must be withdrawn",
    }

    (out / "GATE_ASSURANCE_RECEIPT.json").write_text(json.dumps({
        "schema_version": "p4-instrument-admissibility-assurance-v1",
        "date": freeze["date"],
        "kind": "FRESH_ASSURANCE_KNOWN_ANSWER_BATTERY",
        "benchmark_id": freeze["fresh_assurance_benchmark_id"],
        "seed": FRESH_SEED,
        "seed_disjoint_from": freeze["fresh_assurance_seed_disjoint_from"],
        "cases": case_rows,
        "all_expectations_met": all_pass,
        "falsifiability_audit": "GATE_FALSIFIABILITY_AUDIT.json",
        "falsifiability_all_conditions_pass": audit_pass,
        "same_system_ablation": ablation,
        "grants_scientific_authority": False,
    }, indent=2) + "\n")

    print(json.dumps({
        "fresh_assurance_all_expectations_met": all_pass,
        "falsifiability_all_conditions_pass": audit_pass,
        "reference_verdict": ref_decision.verdict.value,
        "cases": {r["case_id"]: r["decision"]["verdict"] for r in case_rows},
    }, indent=2))


if __name__ == "__main__":
    main()
