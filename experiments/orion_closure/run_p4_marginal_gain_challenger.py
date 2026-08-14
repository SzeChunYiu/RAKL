#!/usr/bin/env python3
"""Instrument v2 + marginal-gain challenger for the Paper IV allocation question.

The preserved reference instrument is formally INADMISSIBLE
(``research/paper4_instrument_admissibility_v1/REFERENCE_INSTRUMENT_ADMISSIBILITY.json``):
a rigorous upper bound on ANY equal-budget policy's advantage over the static
parent (+0.0246) sits below the frozen 0.05 gate.  Its diagnosed structural
causes: world-independent round-0 learner state, near-optimality of equal
spread under concave separable gains, and coarse allocation granularity.

Instrument v2 repairs exactly the first cause — the one the sealed packet's
GENUINE_HEADROOM counterexample names: worlds differ in INITIAL learner state
(a world-specific deficient coordinate pair), so state information is
decision-relevant.  Gains/harms dynamics are imported UNCHANGED from the
frozen parent runner (``apply_batch``); total budget stays 48 per arm.

Phases:

- ``ceiling``: compute static score, tier-2 constructive lower bound and
  tier-3 harm-free upper bound for a candidate instrument configuration, and
  run the admissibility gate under KAPPA_FREEZE_V1.  No arm outcome is
  accessed.  Every configuration tried is appended to INSTRUMENT_DESIGN_LOG.
- ``run --phase develop``: execute the six arms on the development seed.
- ``run --phase assurance``: execute ONCE on the disjoint assurance seed and
  evaluate the frozen hard gates.  The honest sign is whatever it is.

Grants no scientific authority.  A positive terminal here is model-free
development evidence only: it does not touch the 7B Phase-2 evaluator, does
not activate training-policy authority, and does not reverse the preserved
adaptive-v1 negative.
"""
from __future__ import annotations

import argparse
import json
import statistics
from collections import Counter
from pathlib import Path

import random

from run_p4_adaptive_development_stress import BASE_RATES, apply_batch, select_batch
from rakl.instrument_admissibility import (
    BoundKind,
    CeilingBound,
    CeilingEvidence,
    FrozenAdmissibilityDeclaration,
    OracleComputability,
    decide_instrument_admissibility,
)

COORDS = ["PRINCIPLE", "COMPOSITION", "BOUNDARY", "REPRESENTATION", "TRANSFER", "RETENTION"]
CI = {c: i for i, c in enumerate(COORDS)}

#: world -> deficient coordinate pair.  PRINCIPLE and RETENTION each appear so
#: that neither the v1 guard rails nor their absence is uniformly favoured.
V2_WORLDS = {
    "DEFICIT_COMPOSITION_REPRESENTATION": ("COMPOSITION", "REPRESENTATION"),
    "DEFICIT_BOUNDARY_TRANSFER": ("BOUNDARY", "TRANSFER"),
    "DEFICIT_PRINCIPLE_COMPOSITION": ("PRINCIPLE", "COMPOSITION"),
    "DEFICIT_RETENTION_REPRESENTATION": ("RETENTION", "REPRESENTATION"),
    "DEFICIT_TRANSFER_COMPOSITION": ("TRANSFER", "COMPOSITION"),
    "DEFICIT_BOUNDARY_RETENTION": ("BOUNDARY", "RETENTION"),
}


def v2_initial_mastery(world, deficit_m0, complement_m0):
    lo, hi = V2_WORLDS[world]
    return [deficit_m0 if c in (lo, hi) else complement_m0 for c in COORDS]


class MarginalGainPolicy:
    """F_MARGINAL_GAIN_V4: per-slot believed-marginal-gain water-filling.

    Replaces both attributed v1 defects at once:

    - argmin mastery LEVEL -> argmax believed marginal GAIN ``r̂·(1−m)``, with
      ``r̂`` estimated online from observed between-round mastery increments
      (no access to true world rates);
    - whole-round single-target blocks -> per-slot allocation against a
      believed state that saturates as slots are spent, so concentration dies
      out mechanically rather than by a special rule.

    Guard rails are demoted from budget-consuming targets to constraints: the
    only remaining special slot is the one PRINCIPLE repetition-floor slot per
    round that every vector arm carries.  There is no principle-until-0.90
    target and no whole-batch retention repair; retention protection must
    emerge from the gain term or fail the frozen hard-safety gate.
    """

    def __init__(self):
        self.rhat = {c: 0.10 for c in COORDS}
        self.prev_m = None
        self.prev_counts = None

    def observe_and_select(self, m):
        if self.prev_m is not None:
            for c, k in self.prev_counts.items():
                if k <= 0:
                    continue
                m_old = self.prev_m[CI[c]]
                m_new = m[CI[c]]
                denom = max(1e-6, 1.0 - m_old)
                frac = 1.0 - (m_new - m_old) / denom
                frac = min(1.0, max(1e-6, frac))
                r_obs = 1.0 - frac ** (1.0 / k)
                r_obs = min(0.5, max(0.01, r_obs))
                self.rhat[c] = 0.5 * self.rhat[c] + 0.5 * r_obs
        batch = ["PRINCIPLE"]
        mt = list(m)
        mt[CI["PRINCIPLE"]] += self.rhat["PRINCIPLE"] * (1 - mt[CI["PRINCIPLE"]])
        for _ in range(7):
            c = max(COORDS, key=lambda c2: (self.rhat[c2] * (1 - mt[CI[c2]]), -CI[c2]))
            batch.append(c)
            mt[CI[c]] += self.rhat[c] * (1 - mt[CI[c]])
        self.prev_m = list(m)
        self.prev_counts = Counter(batch)
        return batch


# --- ceiling phase -------------------------------------------------------------------


def expected_rollout(counts, world, protocol):
    """Deterministic expected-dynamics rollout of a count vector (v1 harm structure)."""
    m = list(v2_initial_mastery(world, protocol["deficit_m0"], protocol["complement_m0"]))
    remaining = dict(counts)
    for _ in range(protocol["budget"]):
        c = max(COORDS, key=lambda k: (remaining.get(k, 0), -CI[k]))
        if remaining.get(c, 0) <= 0:
            break
        remaining[c] -= 1
        m[CI[c]] += BASE_RATES[c] * (1 - m[CI[c]])
        if c != "PRINCIPLE":
            m[CI["PRINCIPLE"]] -= protocol["forgetting_per_nonprinciple_example"]
        if c != "RETENTION":
            m[CI["RETENTION"]] -= protocol["retention_harm_per_nonretention_example"]
        m = [max(0.0, min(0.999, x)) for x in m]
    return sum(m) / 6


def hill_climb(start, world, protocol):
    cur = dict(start)
    best = expected_rollout(cur, world, protocol)
    improved = True
    while improved:
        improved = False
        for a in COORDS:
            for b in COORDS:
                if a == b or cur.get(a, 0) <= 0:
                    continue
                cand = dict(cur)
                cand[a] -= 1
                cand[b] = cand.get(b, 0) + 1
                val = expected_rollout(cand, world, protocol)
                if val > best + 1e-12:
                    best, cur, improved = val, cand, True
    return best


def harm_free_upper(world, protocol):
    val = {c: v for c, v in zip(
        COORDS, v2_initial_mastery(world, protocol["deficit_m0"], protocol["complement_m0"]))}
    for _ in range(protocol["budget"]):
        best = max(COORDS, key=lambda c: (BASE_RATES[c] * (1 - val[c]), -CI[c]))
        val[best] += BASE_RATES[best] * (1 - val[best])
    return sum(val.values()) / 6


def expected_c_scalar_rollout(world, protocol):
    """Deterministic expected-dynamics rollout of the C_SCALAR_LOSS_AWARE policy.

    Needed so every registered contrast gate — not only the primary F−D gate —
    can be admissibility-checked before outcomes.  Freezing a margin against C
    that the instrument cannot resolve would recreate the reference
    instrument's defect one contrast down.
    """
    from run_p4_adaptive_development_stress import LOSS_BIAS

    m = list(v2_initial_mastery(world, protocol["deficit_m0"], protocol["complement_m0"]))
    for _ in range(protocol["rounds"]):
        proxies = {c: (1 - m[CI[c]]) + LOSS_BIAS[c] for c in COORDS}
        target = max(COORDS, key=lambda c: (proxies[c], -CI[c]))
        for _ in range(protocol["batch_size"]):
            m[CI[target]] += BASE_RATES[target] * (1 - m[CI[target]])
            if target != "PRINCIPLE":
                m[CI["PRINCIPLE"]] -= protocol["forgetting_per_nonprinciple_example"]
            if target != "RETENTION":
                m[CI["RETENTION"]] -= protocol["retention_harm_per_nonretention_example"]
            m = [max(0.0, min(0.999, x)) for x in m]
    return sum(m) / 6


def ceiling_phase(protocol, freeze, outdir):
    uniform = {c: 8 for c in COORDS}
    per_world = {}
    for world in V2_WORLDS:
        lo, hi = V2_WORLDS[world]
        static = expected_rollout(uniform, world, protocol)
        c_scalar = expected_c_scalar_rollout(world, protocol)
        concentrated = {c: 2 for c in COORDS}
        concentrated[lo] += 12
        concentrated[hi] += 12
        # 2*2 + 14 + 14 + remaining -> rebalance to exactly the budget
        total = sum(concentrated.values())
        concentrated["PRINCIPLE"] += protocol["budget"] - total
        best = max(hill_climb(uniform, world, protocol),
                   hill_climb(concentrated, world, protocol))
        per_world[world] = {
            "static": static,
            "c_scalar_expected": c_scalar,
            "constructive_best_minus_static": best - static,
            "constructive_best_minus_c_scalar": best - c_scalar,
            "harm_free_upper_minus_static": harm_free_upper(world, protocol) - static,
        }
    n = len(V2_WORLDS)
    tier2 = sum(v["constructive_best_minus_static"] for v in per_world.values()) / n
    tier2_vs_c = sum(v["constructive_best_minus_c_scalar"] for v in per_world.values()) / n
    tier3 = sum(v["harm_free_upper_minus_static"] for v in per_world.values()) / n

    declaration = FrozenAdmissibilityDeclaration(
        instrument_id=protocol["instrument_id"],
        registered_primary_metric="F_minus_D_balanced_mastery",
        registered_minimum_detectable_effect=protocol["mde_primary"],
        frozen_kappa=freeze["frozen_kappa"],
        declared_on=protocol["date"],
        rationale="instrument v2 licensing under KAPPA_FREEZE_V1 before any arm outcome",
    )
    evidence = CeilingEvidence(
        instrument_id=protocol["instrument_id"],
        oracle_computability=OracleComputability.COMPUTABLE,
        equal_budget_verified=True,
        reference_parent_arm_id="D_STATIC_STRUCTURAL",
        bounds=(
            CeilingBound("tier2_constructive", BoundKind.LOWER_BOUND, tier2,
                         "hill-climb over count vectors, expected dynamics with harms"),
            CeilingBound("tier3_harm_free_relaxation", BoundKind.UPPER_BOUND, tier3,
                         "harm-free separable relaxation, exact greedy water-filling"),
        ),
    )
    decision = decide_instrument_admissibility(declaration, evidence)
    record = {
        "schema_version": "p4-instrument-v2-ceiling-v1",
        "date": protocol["date"],
        "kind": "INSTRUMENT_LICENSING_CEILING_NO_ARM_OUTCOME_ACCESSED",
        "config": {k: protocol[k] for k in
                   ("instrument_id", "deficit_m0", "complement_m0", "budget", "mde_primary",
                    "forgetting_per_nonprinciple_example",
                    "retention_harm_per_nonretention_example")},
        "per_world": per_world,
        "tier2_constructive_mean": tier2,
        "tier2_constructive_minus_c_scalar_mean": tier2_vs_c,
        "tier3_upper_bound_mean": tier3,
        "kappa_threshold": freeze["frozen_kappa"] * protocol["mde_primary"],
        "verdict": decision.verdict.value,
        "licensing_bound_id": decision.licensing_bound_id,
        "verdict_kappa_range": decision.verdict_kappa_range,
        "declaration_sha256": decision.declaration_sha256,
        "ceiling_compute_cost": {
            "hill_climb_rollouts": "O(worlds * iterations * 30 neighbour rollouts)",
            "charged_to": "this comparison's total cost per the sealed packet",
        },
        "grants_scientific_authority": False,
    }
    log = Path(outdir) / "INSTRUMENT_DESIGN_LOG.jsonl"
    with log.open("a") as f:
        f.write(json.dumps(record, sort_keys=True) + "\n")
    (Path(outdir) / "INSTRUMENT_V2_CEILING.json").write_text(
        json.dumps(record, indent=2) + "\n")
    return record


# --- arm execution -------------------------------------------------------------------


def select_batch_v2(arm, m, round_i, rng, policy):
    if arm == "F_MARGINAL_GAIN_V4":
        return policy.observe_and_select(m)
    return select_batch(arm, m, round_i, rng, COORDS, CI)


def mean_ci(vals, seed):
    br = random.Random(seed)
    n = len(vals)
    means = []
    for _ in range(10000):
        means.append(sum(vals[br.randrange(n)] for _ in range(n)) / n)
    means.sort()
    return statistics.mean(vals), [means[250], means[9749]]


def run_phase(protocol, phase, outdir):
    seed = protocol["seeds"][phase]
    arms = protocol["arms"]
    records = []
    for world_idx, world in enumerate(V2_WORLDS):
        m0_world = v2_initial_mastery(world, protocol["deficit_m0"], protocol["complement_m0"])
        for rep in range(protocol["replicates_per_world"]):
            irng = random.Random(seed + world_idx * 100000 + rep * 101)
            m_init = [max(0.0, min(0.99, x + (irng.random() - 0.5) * 0.02)) for x in m0_world]
            for arm_idx, arm in enumerate(arms):
                rng = random.Random(seed + world_idx * 100000 + rep * 101 + arm_idx * 10000000)
                m = list(m_init)
                policy = MarginalGainPolicy() if arm == "F_MARGINAL_GAIN_V4" else None
                counts = Counter()
                for rd in range(protocol["rounds"]):
                    batch = select_batch_v2(arm, m, rd, rng, policy)
                    counts.update(batch)
                    m = apply_batch(m, batch, BASE_RATES, world, rng, protocol, CI)
                records.append({
                    "world": world, "rep": rep, "arm": arm,
                    "balanced_mastery": sum(m) / 6,
                    "hard_safety_min": min(m[CI["PRINCIPLE"]], m[CI["BOUNDARY"]],
                                           m[CI["RETENTION"]]),
                    "counts": dict(counts),
                    "examples": sum(counts.values()),
                })

    by = {(r["world"], r["rep"], r["arm"]): r for r in records}

    def diffs(a, b, metric):
        return [by[(w, rep, a)][metric] - by[(w, rep, b)][metric]
                for w in V2_WORLDS for rep in range(protocol["replicates_per_world"])]

    summary = {}
    for arm in arms:
        rs = [r for r in records if r["arm"] == arm]
        mean_counts = {c: statistics.mean(r["counts"].get(c, 0) for r in rs) for c in COORDS}
        summary[arm] = {
            "balanced_mastery_mean": statistics.mean(r["balanced_mastery"] for r in rs),
            "hard_safety_min_mean": statistics.mean(r["hard_safety_min"] for r in rs),
            "examples_mean": statistics.mean(r["examples"] for r in rs),
            "mean_counts": mean_counts,
        }

    fd_mean, fd_ci = mean_ci(diffs("F_MARGINAL_GAIN_V4", "D_STATIC_STRUCTURAL",
                                   "balanced_mastery"), seed + 699)
    fc_mean, fc_ci = mean_ci(diffs("F_MARGINAL_GAIN_V4", "C_SCALAR_LOSS_AWARE",
                                   "balanced_mastery"), seed + 700)
    fs_mean, fs_ci = mean_ci(diffs("F_MARGINAL_GAIN_V4", "D_STATIC_STRUCTURAL",
                                   "hard_safety_min"), seed + 701)
    ed_mean, ed_ci = mean_ci(diffs("E_VECTOR_ADAPTIVE", "D_STATIC_STRUCTURAL",
                                   "balanced_mastery"), seed + 702)
    per_world_fd = {}
    for w in V2_WORLDS:
        vals = [by[(w, rep, "F_MARGINAL_GAIN_V4")]["balanced_mastery"]
                - by[(w, rep, "D_STATIC_STRUCTURAL")]["balanced_mastery"]
                for rep in range(protocol["replicates_per_world"])]
        per_world_fd[w] = statistics.mean(vals)

    parents = ["A_UNIFORM_RANDOM", "B_DIVERSITY", "C_SCALAR_LOSS_AWARE", "D_STATIC_STRUCTURAL"]
    strongest_parent = max(parents, key=lambda a: summary[a]["balanced_mastery_mean"])
    fp_mean, fp_ci = mean_ci(diffs("F_MARGINAL_GAIN_V4", strongest_parent,
                                   "balanced_mastery"), seed + 703)

    result = {
        "schema_version": "p4-marginal-gain-challenger-result-v1",
        "date": protocol["date"],
        "phase": phase,
        "scope": "MODEL_FREE_DEVELOPMENT_STRESS_NOT_7B_CONFIRMATORY",
        "instrument_id": protocol["instrument_id"],
        "seed": seed,
        "n_world_replicates": len(V2_WORLDS) * protocol["replicates_per_world"],
        "arms": summary,
        "contrasts": {
            "F_minus_D_balanced_mastery": {"mean": fd_mean, "bootstrap_95ci": fd_ci},
            "F_minus_C_balanced_mastery": {"mean": fc_mean, "bootstrap_95ci": fc_ci},
            "F_minus_D_hard_safety_min": {"mean": fs_mean, "bootstrap_95ci": fs_ci},
            "E_minus_D_balanced_mastery": {"mean": ed_mean, "bootstrap_95ci": ed_ci},
            "F_minus_strongest_parent_balanced_mastery": {
                "strongest_parent": strongest_parent, "mean": fp_mean,
                "bootstrap_95ci": fp_ci},
            "per_world_F_minus_D": per_world_fd,
        },
        "grants_scientific_authority": False,
        "changes_7b_phase2_evaluator": False,
        "activates_training_policy_authority": False,
        "reverses_parent_negative": False,
    }

    if phase == "assurance":
        gates = protocol["hard_gate"]
        gate_results = {
            "P2_F_minus_D_balanced_mean_min": (
                fd_mean >= gates["F_minus_D_balanced_mean_min"] and fd_ci[0] > 0),
            "P3_F_minus_C_balanced_mean_min": (
                fc_mean >= gates["F_minus_C_balanced_mean_min"] and fc_ci[0] > 0),
            "P3b_F_minus_strongest_parent_min": (
                fp_mean >= gates["F_minus_strongest_parent_min"] and fp_ci[0] > 0),
            "P4_F_safety_harm_vs_D_min": fs_mean >= gates["F_safety_harm_vs_D_min"],
            "P5_all_worlds_F_minus_D_positive": all(v > 0 for v in per_world_fd.values()),
            "P6_v1_negative_persists_in_licensed_instrument": ed_mean < 0,
        }
        primary_pass = all(v for k, v in gate_results.items() if k.startswith(("P2", "P3", "P4", "P5")))
        result["hard_gate_results"] = gate_results
        result["terminal"] = (
            "DEVELOPMENT_POSITIVE_MARGINAL_GAIN_CHALLENGER_IN_LICENSED_INSTRUMENT"
            if primary_pass else
            "SECOND_DEVELOPMENT_NEGATIVE_MARGINAL_GAIN_CHALLENGER"
        )

    name = "ASSURANCE_RECEIPT.json" if phase == "assurance" else "DEVELOPMENT_RECEIPT.json"
    (Path(outdir) / name).write_text(json.dumps(result, indent=2) + "\n")
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["ceiling", "run"])
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--freeze", default="research/paper4_instrument_admissibility_v1/KAPPA_FREEZE_V1.json")
    ap.add_argument("--phase", choices=["develop", "assurance"])
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    protocol = json.loads(Path(args.protocol).read_text())
    Path(args.outdir).mkdir(parents=True, exist_ok=True)
    if args.mode == "ceiling":
        freeze = json.loads(Path(args.freeze).read_text())
        record = ceiling_phase(protocol, freeze, args.outdir)
        print(json.dumps({k: record[k] for k in
                          ("verdict", "tier2_constructive_mean", "tier3_upper_bound_mean",
                           "kappa_threshold", "verdict_kappa_range")}, indent=2))
    else:
        if not args.phase:
            raise SystemExit("--phase required for run")
        if args.phase == "assurance":
            ceiling = json.loads((Path(args.outdir) / "INSTRUMENT_V2_CEILING.json").read_text())
            if ceiling["verdict"] != "ADMISSIBLE":
                raise SystemExit("instrument not licensed: admissibility verdict is "
                                 + ceiling["verdict"])
        result = run_phase(protocol, args.phase, args.outdir)
        out = {"phase": args.phase,
               "contrasts": {k: v for k, v in result["contrasts"].items()
                             if k != "per_world_F_minus_D"}}
        if "hard_gate_results" in result:
            out["hard_gate_results"] = result["hard_gate_results"]
            out["terminal"] = result["terminal"]
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
