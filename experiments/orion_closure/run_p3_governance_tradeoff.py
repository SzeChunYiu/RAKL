#!/usr/bin/env python3
"""Governance-tradeoff experiment: governed vs ungoverned recursive solver improvement.

Executes research/paper3_governance_tradeoff_v1/PROTOCOL.json, frozen before any
outcome access.  Both arms receive the identical ordered stream of 14 allocator
mutation proposals.

- UNGOVERNED_GREEDY (registered comparator shape MEC-GREEDY_ACCEPT_ON_HELD_OUT_SCALAR):
  accepts a proposal iff its held-out development scalar improves on the current
  incumbent, evaluated on the REFERENCE instrument -- which is formally
  INADMISSIBLE, a fact the arm has no mechanic to discover.
- GOVERNED: refuses the reference instrument (CANNOT_CHECK), evaluates on the
  licensed v2 instrument under frozen screening gates, and promotes at most one
  assurance-green candidate.
- TRUTH METER (experimenter-level): every accepted candidate is evaluated once on
  the licensed instrument at a disjoint truth seed; false promotion = accepted
  candidate whose truth advantage over the arm's prior incumbent has mean <= 0.

Evaluator integrity is MEASURED at end state, not assumed: content-inertness and
noise-acceptance rates for the greedy scalar; a black-box falsifiability battery
for the governed gates.

No scalar verdict.  Output is a Pareto frontier over the frozen outcome vector.
Grants no scientific authority.
"""
from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import Counter
from pathlib import Path

from run_p4_adaptive_development_stress import (
    BASE_RATES,
    LOSS_BIAS,
    apply_batch,
    world_rates,
)
from run_p4_marginal_gain_challenger import V2_WORLDS, v2_initial_mastery
from rakl.gate_falsifiability import audit_gate

COORDS = ["PRINCIPLE", "COMPOSITION", "BOUNDARY", "REPRESENTATION", "TRANSFER", "RETENTION"]
CI = {c: i for i, c in enumerate(COORDS)}
NONP = [c for c in COORDS if c != "PRINCIPLE"]
REPS = 32
BOOT = 10000


# --- policy zoo ---------------------------------------------------------------------


class V1Policy:
    def __init__(self, *, threshold=0.90, cap8=False, deconc=False, retention_floor=0.80):
        self.threshold = threshold
        self.cap8 = cap8
        self.deconc = deconc
        self.retention_floor = retention_floor
        self.principle_spent = 0

    def _redirect(self, m):
        return min(NONP, key=lambda c: (m[CI[c]], CI[c]))

    def select(self, m, round_i, rng):
        batch = []
        floor = "PRINCIPLE"
        if self.cap8 and self.principle_spent >= 8:
            floor = self._redirect(m)
        batch.append(floor)
        if self.deconc:
            order = sorted(NONP, key=lambda c: (m[CI[c]], CI[c]))
            spread = [2, 2, 1, 1, 1]
            for c, k in zip(order, spread):
                batch += [c] * k
        else:
            if m[CI["RETENTION"]] < self.retention_floor:
                target = "RETENTION"
            elif m[CI["PRINCIPLE"]] < self.threshold:
                target = "PRINCIPLE"
                if self.cap8 and self.principle_spent + 1 + 7 > 8:
                    target = self._redirect(m)
            else:
                target = self._redirect(m)
            batch += [target] * 7
        if self.cap8:
            capped = []
            for c in batch:
                if c == "PRINCIPLE" and self.principle_spent >= 8:
                    c = self._redirect(m)
                if c == "PRINCIPLE":
                    self.principle_spent += 1
                capped.append(c)
            batch = capped
        else:
            self.principle_spent += sum(1 for c in batch if c == "PRINCIPLE")
        return batch


class CScalarPolicy:
    def select(self, m, round_i, rng):
        proxies = {c: (1 - m[CI[c]]) + LOSS_BIAS[c] for c in COORDS}
        target = max(COORDS, key=lambda c: (proxies[c], -CI[c]))
        return [target] * 8


class MGPolicy:
    def __init__(self, *, alpha=0.5, floor_slots=1, init=0.10, ret_emergency=False):
        self.alpha = alpha
        self.floor_slots = floor_slots
        self.init = init
        self.ret_emergency = ret_emergency
        self.rhat = {c: init for c in COORDS}
        self.prev_m = None
        self.prev_counts = None

    def select(self, m, round_i, rng):
        if self.prev_m is not None:
            for c, k in self.prev_counts.items():
                if k <= 0:
                    continue
                m_old, m_new = self.prev_m[CI[c]], m[CI[c]]
                denom = max(1e-6, 1.0 - m_old)
                frac = min(1.0, max(1e-6, 1.0 - (m_new - m_old) / denom))
                r_obs = min(0.5, max(0.01, 1.0 - frac ** (1.0 / k)))
                self.rhat[c] = (1 - self.alpha) * self.rhat[c] + self.alpha * r_obs
        batch = ["PRINCIPLE"] * self.floor_slots
        mt = list(m)
        for _ in range(self.floor_slots):
            mt[CI["PRINCIPLE"]] += self.rhat["PRINCIPLE"] * (1 - mt[CI["PRINCIPLE"]])
        if self.ret_emergency and m[CI["RETENTION"]] < 0.6 and len(batch) < 8:
            batch.append("RETENTION")
            mt[CI["RETENTION"]] += self.rhat["RETENTION"] * (1 - mt[CI["RETENTION"]])
        while len(batch) < 8:
            c = max(COORDS, key=lambda c2: (self.rhat[c2] * (1 - mt[CI[c2]]), -CI[c2]))
            batch.append(c)
            mt[CI[c]] += self.rhat[c] * (1 - mt[CI[c]])
        self.prev_m = list(m)
        self.prev_counts = Counter(batch)
        return batch


class RandomPolicy:
    def select(self, m, round_i, rng):
        return [rng.choice(COORDS) for _ in range(8)]


class StaticPolicy:
    def select(self, m, round_i, rng):
        schedule = COORDS * 8
        return schedule[round_i * 8:(round_i + 1) * 8]


def make_policy(pid):
    return {
        "M01_V1_ARGMIN_LEVEL": lambda: V1Policy(),
        "M02_V1_CAP_PRINCIPLE_8": lambda: V1Policy(cap8=True),
        "M03_V1_DECONCENTRATE": lambda: V1Policy(deconc=True),
        "M04_V1_CAP_AND_DECONC": lambda: V1Policy(cap8=True, deconc=True),
        "M05_SCALAR_DEFICIT_BLOCK": lambda: CScalarPolicy(),
        "M06_MG_EMA050": lambda: MGPolicy(alpha=0.5),
        "M07_MG_EMA025": lambda: MGPolicy(alpha=0.25),
        "M08_MG_EMA075": lambda: MGPolicy(alpha=0.75),
        "M09_MG_NOFLOOR": lambda: MGPolicy(floor_slots=0),
        "M10_MG_FLOOR2": lambda: MGPolicy(floor_slots=2),
        "M11_MG_RET_EMERGENCY": lambda: MGPolicy(ret_emergency=True),
        "M12_RANDOM_ALLOCATION": lambda: RandomPolicy(),
        "M13_MG_INIT_012": lambda: MGPolicy(init=0.12),
        "M14_V1_THRESHOLD_080": lambda: V1Policy(threshold=0.80),
        "D_STATIC_STRUCTURAL": lambda: StaticPolicy(),
    }[pid]


# --- instruments --------------------------------------------------------------------


def instrument_worlds(kind, ref_freeze, v2_proto):
    if kind == "reference":
        return ref_freeze["worlds"], ref_freeze
    return list(V2_WORLDS), v2_proto


def initial_mastery(kind, world, ref_freeze, v2_proto):
    if kind == "reference":
        return list(ref_freeze["initial_mastery"])
    return v2_initial_mastery(world, v2_proto["deficit_m0"], v2_proto["complement_m0"])


def rates_for(kind, world):
    if kind == "reference":
        return world_rates(world)
    return BASE_RATES


_eval_cache = {}


def eval_policy(pid, kind, seed, ref_freeze, v2_proto):
    """Evaluate a policy: per-replicate balanced mastery and safety, paired by irng."""
    key = (pid, kind, seed)
    if key in _eval_cache:
        return _eval_cache[key]
    worlds, proto = instrument_worlds(kind, ref_freeze, v2_proto)
    arm_idx = (sum(ord(ch) for ch in pid) * 131) % 97  # deterministic across processes
    rows = []
    for world_idx, world in enumerate(worlds):
        rates = rates_for(kind, world)
        m0w = initial_mastery(kind, world, ref_freeze, v2_proto)
        for rep in range(REPS):
            irng = random.Random(seed + world_idx * 100000 + rep * 101)
            m = [max(0.0, min(0.99, x + (irng.random() - 0.5) * 0.02)) for x in m0w]
            rng = random.Random(seed + world_idx * 100000 + rep * 101 + arm_idx * 10000000)
            policy = make_policy(pid)()
            for rd in range(6):
                batch = policy.select(m, rd, rng)
                m = apply_batch(m, batch, rates, world, rng, proto, CI)
            rows.append({
                "world": world,
                "rep": rep,
                "balanced": sum(m) / 6,
                "safety": min(m[CI["PRINCIPLE"]], m[CI["BOUNDARY"]], m[CI["RETENTION"]]),
            })
    result = {
        "pid": pid,
        "balanced_mean": statistics.mean(r["balanced"] for r in rows),
        "safety_mean": statistics.mean(r["safety"] for r in rows),
        "rows": rows,
    }
    _eval_cache[key] = result
    return result


def paired_diff(a, b, metric="balanced"):
    return [ra[metric] - rb[metric] for ra, rb in zip(a["rows"], b["rows"])]


def boot_ci(vals, seed):
    br = random.Random(seed)
    n = len(vals)
    means = sorted(
        sum(vals[br.randrange(n)] for _ in range(n)) / n for _ in range(BOOT)
    )
    return statistics.mean(vals), [means[int(BOOT * 0.025)], means[int(BOOT * 0.975) - 1]]


# --- arms ---------------------------------------------------------------------------


def run_greedy(stream, seeds, ref_freeze, v2_proto):
    seed = seeds["greedy_dev_reference"]
    incumbent = "D_STATIC_STRUCTURAL"
    inc_eval = eval_policy(incumbent, "reference", seed, ref_freeze, v2_proto)
    decisions = []
    chain = []
    units = 0
    for pid in stream:
        ev = eval_policy(pid, "reference", seed, ref_freeze, v2_proto)
        units += 1
        improvement = ev["balanced_mean"] - inc_eval["balanced_mean"]
        accept = improvement > 0
        diffs = paired_diff(ev, inc_eval)
        _, ci = boot_ci(diffs, seed + 777 + units)
        decisions.append({
            "proposal": pid,
            "incumbent_before": incumbent,
            "dev_scalar": ev["balanced_mean"],
            "incumbent_scalar": inc_eval["balanced_mean"],
            "improvement": improvement,
            "paired_diff_ci": ci,
            "noise_acceptance": bool(accept and not (ci[0] > 0)),
            "decision": "ACCEPT" if accept else "REJECT",
            "refusals_or_cannot_check": 0,
        })
        if accept:
            chain.append({"proposal": pid, "prior_incumbent": incumbent})
            incumbent = pid
            inc_eval = ev
    return {"final_incumbent": incumbent, "decisions": decisions, "chain": chain,
            "eval_units": units}


def run_governed(stream, seeds, ref_freeze, v2_proto, gates):
    dev_seed = seeds["governed_dev_licensed"]
    asr_seed = seeds["governed_assurance_licensed"]
    d_dev = eval_policy("D_STATIC_STRUCTURAL", "v2", dev_seed, ref_freeze, v2_proto)
    decisions = []
    survivors = []
    units = 4  # declared qualification cost: reference INADMISSIBLE verdict + v2 licensing
    for pid in stream:
        # The reference-instrument comparison is refused: INADMISSIBLE receipt on file.
        ev = eval_policy(pid, "v2", dev_seed, ref_freeze, v2_proto)
        units += 1
        fd = ev["balanced_mean"] - d_dev["balanced_mean"]
        fs = ev["safety_mean"] - d_dev["safety_mean"]
        screen_pass = fd >= gates["fd_min"] and fs >= gates["safety_min"]
        decisions.append({
            "proposal": pid,
            "reference_instrument": "REFUSED_CANNOT_CHECK_INSTRUMENT_INADMISSIBLE",
            "dev_fd": fd,
            "dev_safety_harm": fs,
            "screen": "PASS" if screen_pass else "FAIL",
        })
        if screen_pass:
            survivors.append((fd, pid))
    promotion = None
    if survivors:
        survivors.sort(reverse=True)
        best = survivors[0][1]
        ev = eval_policy(best, "v2", asr_seed, ref_freeze, v2_proto)
        d_asr = eval_policy("D_STATIC_STRUCTURAL", "v2", asr_seed, ref_freeze, v2_proto)
        units += 1
        diffs = paired_diff(ev, d_asr)
        fd_mean, fd_ci = boot_ci(diffs, asr_seed + 888)
        fs_mean = ev["safety_mean"] - d_asr["safety_mean"]
        per_world = {}
        for w in set(r["world"] for r in ev["rows"]):
            vals = [ra["balanced"] - rb["balanced"]
                    for ra, rb in zip(ev["rows"], d_asr["rows"]) if ra["world"] == w]
            per_world[w] = statistics.mean(vals)
        green = (fd_mean >= gates["fd_min"] and fd_ci[0] > 0
                 and fs_mean >= gates["safety_min"]
                 and all(v > 0 for v in per_world.values()))
        promotion = {
            "candidate": best,
            "assurance_fd": fd_mean,
            "assurance_fd_ci": fd_ci,
            "assurance_safety_harm": fs_mean,
            "per_world_fd": per_world,
            "gates_green": green,
            "decision": "PROMOTE" if green else "REJECT_AT_ASSURANCE",
        }
    return {"decisions": decisions, "promotion": promotion, "eval_units": units,
            "final_incumbent": (promotion["candidate"]
                                if promotion and promotion["gates_green"]
                                else "D_STATIC_STRUCTURAL")}


def truth_meter(candidates_with_priors, seeds, ref_freeze, v2_proto):
    seed = seeds["truth_meter_licensed_assurance"]
    d_truth = eval_policy("D_STATIC_STRUCTURAL", "v2", seed, ref_freeze, v2_proto)

    def truth_fd(pid):
        if pid == "D_STATIC_STRUCTURAL":
            return 0.0
        ev = eval_policy(pid, "v2", seed, ref_freeze, v2_proto)
        return ev["balanced_mean"] - d_truth["balanced_mean"]

    rows = []
    for cand, prior in candidates_with_priors:
        adv = truth_fd(cand) - truth_fd(prior)
        rows.append({
            "candidate": cand,
            "prior_incumbent": prior,
            "truth_fd_candidate": truth_fd(cand),
            "truth_fd_prior": truth_fd(prior),
            "truth_advantage_over_prior": adv,
            "false_promotion": bool(adv <= 0),
        })
    return rows


# --- evaluator integrity ------------------------------------------------------------


def greedy_integrity(greedy, seeds, ref_freeze, v2_proto):
    """Content-inertness: would the planted dud have been accepted at each acceptance?"""
    seed = seeds["greedy_dev_reference"]
    dud = eval_policy("M12_RANDOM_ALLOCATION", "reference", seed, ref_freeze, v2_proto)
    rows = []
    for d in greedy["decisions"]:
        if d["decision"] != "ACCEPT":
            continue
        rows.append({
            "proposal": d["proposal"],
            "content_inert": bool(dud["balanced_mean"] > d["incumbent_scalar"]),
            "noise_acceptance": d["noise_acceptance"],
        })
    n = len(rows)
    return {
        "acceptances": n,
        "content_inert_rate": (sum(r["content_inert"] for r in rows) / n) if n else None,
        "noise_acceptance_rate": (sum(r["noise_acceptance"] for r in rows) / n) if n else None,
        "per_acceptance": rows,
        "reading": "an acceptance is content-inert when the planted random-allocation dud "
                   "would also have been accepted at that decision point; it is a noise "
                   "acceptance when the paired-diff 95% CI includes zero",
    }


def governed_integrity(promotion, gates):
    """Black-box falsifiability battery on the assurance-gate evidence."""
    if promotion is None:
        return {"verdict": "CANNOT_CHECK", "reason": "no assurance evidence produced"}
    evidence = [
        {"metric": "fd_mean", "value": promotion["assurance_fd"]},
        {"metric": "fd_ci_low", "value": promotion["assurance_fd_ci"][0]},
        {"metric": "safety_harm", "value": promotion["assurance_safety_harm"]},
        {"metric": "worlds_min", "value": min(promotion["per_world_fd"].values())},
    ]
    baseline = promotion["gates_green"]

    def gate(rows):
        vals = {r["metric"]: r["value"] for r in rows}
        green = (vals["fd_mean"] >= gates["fd_min"] and vals["fd_ci_low"] > 0
                 and vals["safety_harm"] >= gates["safety_min"]
                 and vals["worlds_min"] > 0)
        return green == baseline

    def scale_all(factor_lo, factor_hi):
        def perturb(rows, rng):
            f = factor_lo + rng.random() * (factor_hi - factor_lo)
            return [{**r, "value": r["value"] * f} for r in rows]
        return perturb

    def poison_safety(rows, rng):
        return [{**r, "value": (-0.5 if r["metric"] == "safety_harm" else r["value"])}
                for r in rows]

    report = audit_gate(
        gate, evidence, gate_id="governed_assurance_gate_end_state",
        perturbations={
            "attenuate_contrasts": scale_all(1e-3, 1e-2),
            "poison_safety_bound": poison_safety,
        },
        trials=16, seed=20260814,
    )
    return {
        "verdict": report.verdict.value,
        "probes": [{"probe": p.probe_id, "outcome": p.outcome.value, "flips": p.flips}
                   for p in report.probes],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--protocol", required=True)
    ap.add_argument("--reference-freeze", required=True)
    ap.add_argument("--v2-protocol", required=True)
    ap.add_argument("--outdir", required=True)
    args = ap.parse_args()
    protocol = json.loads(Path(args.protocol).read_text())
    ref_freeze = json.loads(Path(args.reference_freeze).read_text())
    v2_proto = json.loads(Path(args.v2_protocol).read_text())
    seeds = protocol["seeds"]
    stream = [p["id"] for p in protocol["frozen_proposal_stream"]["proposals"]]
    gates = {"fd_min": 0.05, "safety_min": -0.01}

    greedy = run_greedy(stream, seeds, ref_freeze, v2_proto)
    governed = run_governed(stream, seeds, ref_freeze, v2_proto, gates)

    greedy_truth = truth_meter(
        [(c["proposal"], c["prior_incumbent"]) for c in greedy["chain"]],
        seeds, ref_freeze, v2_proto)
    governed_truth = truth_meter(
        [(governed["promotion"]["candidate"], "D_STATIC_STRUCTURAL")]
        if governed["promotion"] and governed["promotion"]["gates_green"] else [],
        seeds, ref_freeze, v2_proto)

    g_int = greedy_integrity(greedy, seeds, ref_freeze, v2_proto)
    gov_int = governed_integrity(governed["promotion"], gates)

    d_ref = eval_policy("D_STATIC_STRUCTURAL", "reference",
                        seeds["greedy_dev_reference"], ref_freeze, v2_proto)
    greedy_final_dev_gain = (
        eval_policy(greedy["final_incumbent"], "reference",
                    seeds["greedy_dev_reference"], ref_freeze, v2_proto)["balanced_mean"]
        - d_ref["balanced_mean"]) if greedy["final_incumbent"] != "D_STATIC_STRUCTURAL" else 0.0

    frontier = {
        "UNGOVERNED_GREEDY": {
            "development_gain_own_instrument": greedy_final_dev_gain,
            "final_incumbent": greedy["final_incumbent"],
            "accepted_count": len(greedy["chain"]),
            "fresh_assurance_gain_final_incumbent":
                next((r["truth_fd_candidate"] for r in reversed(greedy_truth)
                      if r["candidate"] == greedy["final_incumbent"]), 0.0),
            "false_promotions": sum(r["false_promotion"] for r in greedy_truth),
            "honest_terminal_rate": 0.0,
            "content_inert_rate": g_int["content_inert_rate"],
            "noise_acceptance_rate": g_int["noise_acceptance_rate"],
            "eval_units": greedy["eval_units"],
        },
        "GOVERNED": {
            "development_gain_licensed_instrument": (
                governed["promotion"]["assurance_fd"]
                if governed["promotion"] and governed["promotion"]["gates_green"] else 0.0),
            "final_incumbent": governed["final_incumbent"],
            "promoted_count": int(bool(governed["promotion"]
                                       and governed["promotion"]["gates_green"])),
            "fresh_assurance_gain_final_incumbent":
                (governed_truth[0]["truth_fd_candidate"] if governed_truth else 0.0),
            "false_promotions": sum(r["false_promotion"] for r in governed_truth),
            "honest_terminal_rate": sum(
                1 for d in governed["decisions"]
                if d["reference_instrument"].startswith("REFUSED")) / len(stream),
            "evaluator_integrity": gov_int["verdict"],
            "eval_units": governed["eval_units"],
        },
        "cited_receipt_cells": protocol["additional_frontier_cells_from_receipts"],
    }

    predictions = {
        "TP1_greedy_has_false_promotion": frontier["UNGOVERNED_GREEDY"]["false_promotions"] >= 1,
        "TP2_greedy_wins_raw_throughput": (
            frontier["UNGOVERNED_GREEDY"]["accepted_count"]
            > frontier["GOVERNED"]["promoted_count"]),
        "TP3_half_of_acceptances_noise_or_inert": (
            g_int["acceptances"] > 0 and (
                sum(1 for r in g_int["per_acceptance"]
                    if r["content_inert"] or r["noise_acceptance"]) / g_int["acceptances"]
            ) >= 0.5),
        "TP4_governed_le1_promotion_zero_false": (
            frontier["GOVERNED"]["promoted_count"] <= 1
            and frontier["GOVERNED"]["false_promotions"] == 0),
        "TP5_greedy_final_transfers_positively": (
            frontier["UNGOVERNED_GREEDY"]["fresh_assurance_gain_final_incumbent"] > 0),
    }

    receipt = {
        "schema_version": "p3-governance-tradeoff-result-v1",
        "date": protocol["date"],
        "protocol": args.protocol,
        "scope": "MODEL_FREE_DEVELOPMENT_STRESS_NOT_REAL_MODEL",
        "frontier": frontier,
        "greedy_decisions": greedy["decisions"],
        "greedy_truth_meter": greedy_truth,
        "governed_decisions": governed["decisions"],
        "governed_promotion": governed["promotion"],
        "governed_truth_meter": governed_truth,
        "greedy_evaluator_integrity": g_int,
        "governed_evaluator_integrity": gov_int,
        "predictions_read_from_data": predictions,
        "no_scalar_verdict": True,
        "grants_scientific_authority": False,
    }
    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "TRADEOFF_RECEIPT.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"frontier": frontier, "predictions": predictions}, indent=2))


if __name__ == "__main__":
    main()
