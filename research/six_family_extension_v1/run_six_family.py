#!/usr/bin/env python3
"""Six-family robustness extension of the external-LLM applicability-gate comparator.

CLOSES: Paper II's named-and-frozen open coordinate. Section 03c states that four
family clusters are insufficient for a broad cross-domain law, because the exact
two-sided sign test on four positive family signs is only p = 0.125, and names a
six-family robustness extension as the required future coordinate.

WHAT IS HELD FIXED (nothing about the comparator design is re-tuned here):
  * the SAME three conditions, prompts, label space, parser and call pattern as
    research/llm_comparator_dev_v1/run_comparator.py -- imported, not re-written;
  * the SAME primary metric: false-accept rate = P(model = ACCEPT | gold = REJECT);
  * the SAME model (glm-5.2) in every condition.

WHAT IS NEW:
  * the benchmark is rakl.objective_transfer_benchmark_v2, which adds TWO new
    exact-verifier families (`sched`, `stat`) to the frozen four, leaving the
    frozen four bit-identical;
  * a fresh seed;
  * the analysis is PER FAMILY: each family contributes one sign
        sign_f = +1 iff false_accept(gate, f) < false_accept(direct, f),
    and the six signs enter an exact two-sided sign test. All six positive gives
    the registered target p = 0.03125.

PRE-COMMITTED BEFORE ANY MODEL OUTPUT WAS SCORED (see FROZEN_DESIGN below):
  seed, n per cell, family set, the sign definition, the sign-test statistic, the
  bootstrap procedure and the decision rule. FREE_COT is the compute-matched
  control and also gets a sign test; if the control's sign test is significant
  too, the gate result is NOT attributable to obligation structure.

HONESTY: the real per-family signs are reported whatever they are. If fewer than
six are positive, the honest conclusion is scoped/heterogeneous generalization,
NOT a broad cross-domain law. No model output is ever fabricated: if the endpoint
is unreachable the run aborts and only the gold-only dry run is emitted.

Usage:
  python run_six_family.py --dry-run   # gold + deterministic arms only, no API
  python run_six_family.py             # full three-condition comparator
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import math
import random
import statistics
import sys
from pathlib import Path

import rakl.objective_transfer_benchmark_v2 as V
from rakl.objective_transfer_benchmark_v2 import Decision

HERE = Path(__file__).resolve().parent
RESULTS = HERE / "results"
RAW = RESULTS / "raw_results.jsonl"

FROZEN_DESIGN = {
    "seed": 20260813,
    "n_per_cell": 6,                      # 9 * 6 = 54 items/family, 48 decidable
    "families": list(V.FAMILIES),
    "conditions": ["DIRECT", "FREE_COT", "RAKL_GATE"],
    "model": "glm-5.2",
    "primary_metric": "false_accept_rate = P(model=ACCEPT | exact_verifier_gold=REJECT)",
    "family_sign_rule": "+1 iff false_accept(RAKL_GATE) < false_accept(DIRECT) in that family",
    "sign_test": "exact two-sided sign test over the six family signs; ties dropped",
    "registered_target": "all six signs positive -> p = 0.03125",
    "control": "FREE_COT is compute-matched; its own six-family sign test must NOT "
               "reproduce the gate effect, else the effect is compute, not structure",
    "bootstrap": "10000 paired item resamples within family over gold-REJECT items",
    "bootstrap_seed": 20260813,
}
BOOT_REPS = 10000


# --------------------------------------------------------------------------- #
# analysis primitives (pure; exercised by the dry run without any API access)
# --------------------------------------------------------------------------- #
def false_accept(labels: dict[str, str], items: list[str]) -> float:
    if not items:
        return float("nan")
    return sum(labels.get(i) == "ACCEPT" for i in items) / len(items)


def paired_bootstrap(direct: dict[str, str], gate: dict[str, str],
                     items: list[str], seed: int, reps: int = BOOT_REPS) -> dict[str, float]:
    """Paired item bootstrap: the SAME resampled items score both conditions."""
    rng = random.Random(seed)
    n = len(items)
    d_stat, g_stat, delta = [], [], []
    for _ in range(reps):
        idx = [items[rng.randrange(n)] for _ in range(n)]
        d = sum(direct.get(i) == "ACCEPT" for i in idx) / n
        g = sum(gate.get(i) == "ACCEPT" for i in idx) / n
        d_stat.append(d); g_stat.append(g); delta.append(d - g)
    d_stat.sort(); g_stat.sort(); delta.sort()
    lo, hi = int(0.025 * reps), int(0.975 * reps)
    return {
        "direct": false_accept(direct, items),
        "direct_ci95": [d_stat[lo], d_stat[hi]],
        "gate": false_accept(gate, items),
        "gate_ci95": [g_stat[lo], g_stat[hi]],
        "delta_direct_minus_gate": false_accept(direct, items) - false_accept(gate, items),
        "delta_ci95": [delta[lo], delta[hi]],
        "delta_excludes_zero": bool(delta[lo] > 0 or delta[hi] < 0),
        "n_invalid_items": n,
    }


def sign_summary(per_family_delta: dict[str, float]) -> dict[str, object]:
    signs = {f: (1 if d > 0 else -1 if d < 0 else 0) for f, d in per_family_delta.items()}
    pos = sum(1 for s in signs.values() if s > 0)
    neg = sum(1 for s in signs.values() if s < 0)
    ties = sum(1 for s in signs.values() if s == 0)
    return {
        "signs": signs,
        "n_positive": pos, "n_negative": neg, "n_tied": ties,
        "sign_test_p_two_sided": V.two_sided_sign_test(pos, neg, ties),
        "all_six_positive": pos == 6,
    }


# --------------------------------------------------------------------------- #
# gold-only dry run (no model output involved)
# --------------------------------------------------------------------------- #
def dry_run() -> dict:
    d = FROZEN_DESIGN
    receipt = V.gold_only_receipt(d["seed"], d["n_per_cell"])
    tasks = V.generate(d["seed"], d["n_per_cell"], True)
    gold = {t.item_id: V.verify(t).decision.value for t in tasks}

    # Prove the whole scoring pipeline on gold by feeding it two synthetic
    # deterministic "conditions": the mechanism-only projection standing in for a
    # weak arm and the full applicability contract standing in for a strong arm.
    weak = {t.item_id: V.mechanism_predict(t).value for t in tasks}
    strong = {t.item_id: V.extract(t).decision.value for t in tasks}
    per_family, deltas = {}, {}
    for fam in V.FAMILIES:
        inv = [t.item_id for t in tasks if t.family == fam and gold[t.item_id] == "REJECT"]
        per_family[fam] = paired_bootstrap(weak, strong, inv, d["bootstrap_seed"], reps=2000)
        deltas[fam] = per_family[fam]["delta_direct_minus_gate"]
    return {
        "schema": "paper2-six-family-dry-run-v1",
        "note": "PIPELINE PROOF ONLY. The two arms here are the deterministic "
                "mechanism-only and full-contract projections, NOT model outputs.",
        "frozen_design": d,
        "gold_only_receipt": receipt,
        "pipeline_check_per_family": per_family,
        "pipeline_check_sign_test": sign_summary(deltas),
        "claim_boundary": "GOLD_ONLY_DRY_RUN__NO_MODEL_OUTPUT_ACCESSED",
        "grants_scientific_authority": False,
    }


# --------------------------------------------------------------------------- #
# live three-condition comparator
# --------------------------------------------------------------------------- #
def _load_frozen_comparator():
    sys.path.insert(0, str(HERE.parent / "llm_comparator_dev_v1"))
    import run_comparator as R  # noqa: E402  (frozen prompts/parser/call pattern)
    return R


def live_run(max_workers: int) -> dict:
    R = _load_frozen_comparator()
    d = FROZEN_DESIGN
    assert list(R.PROMPTS) == d["conditions"], "frozen condition set changed"
    assert R.MODEL == d["model"], "frozen model changed"

    tasks = V.generate(d["seed"], d["n_per_cell"], True)
    by_id = {t.item_id: t for t in tasks}
    gold = {t.item_id: V.verify(t).decision.value for t in tasks}

    done: dict[tuple[str, str], str] = {}
    if RAW.exists():                       # resume without re-billing completed calls
        for line in RAW.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                if r["seed"] == d["seed"]:
                    done[(r["item_id"], r["condition"])] = r["model_label"]
    jobs = [(t, c) for t in tasks for c in d["conditions"] if (t.item_id, c) not in done]
    print(f"tasks={len(tasks)} families={len(V.FAMILIES)} "
          f"jobs_total={len(tasks) * 3} cached={len(done)} to_run={len(jobs)}")

    RESULTS.mkdir(parents=True, exist_ok=True)
    errors = 0
    if jobs:
        with RAW.open("a") as fh, cf.ThreadPoolExecutor(max_workers=max_workers) as ex:
            def one(job):
                t, cond = job
                mt = 12 if cond == "DIRECT" else 900
                txt = R.call(R.PROMPTS[cond](t), mt) or ""
                return t, cond, R.parse(txt), txt.startswith("__ERROR__")
            for i, (t, cond, lab, err) in enumerate(ex.map(one, jobs)):
                errors += err
                done[(t.item_id, cond)] = lab
                fh.write(json.dumps({
                    "seed": d["seed"], "item_id": t.item_id, "family": t.family,
                    "item_type": t.item_type, "gold": gold[t.item_id],
                    "condition": cond, "model_label": lab, "api_error": bool(err)}) + "\n")
                fh.flush()
                if (i + 1) % 60 == 0:
                    print(f"  {i + 1}/{len(jobs)}  api_errors={errors}")
    if errors:
        print(f"WARNING: {errors} API errors; those items are recorded as PARSE_FAIL "
              f"and are NOT imputed.", file=sys.stderr)

    labels = {c: {iid: lab for (iid, cc), lab in done.items() if cc == c} for c in d["conditions"]}

    # ---- per-family primary analysis -------------------------------------- #
    per_family, gate_delta, cot_delta = {}, {}, {}
    for fam in V.FAMILIES:
        fam_items = [t.item_id for t in tasks if t.family == fam]
        inv = [i for i in fam_items if gold[i] == "REJECT"]
        hostile = [i for i in fam_items
                   if by_id[i].item_type == "SEMANTIC_NEAR_MISS_INVALID_TRANSFER"]
        boot = paired_bootstrap(labels["DIRECT"], labels["RAKL_GATE"], inv, d["bootstrap_seed"])
        cot = paired_bootstrap(labels["DIRECT"], labels["FREE_COT"], inv, d["bootstrap_seed"])
        per_family[fam] = {
            **boot,
            "free_cot": false_accept(labels["FREE_COT"], inv),
            "free_cot_ci95": cot["gate_ci95"],
            "delta_direct_minus_free_cot": cot["delta_direct_minus_gate"],
            "hostile_near_miss_false_accept": {
                c: false_accept(labels[c], hostile) for c in d["conditions"]},
            "three_way_accuracy": {
                c: sum(labels[c].get(i) == gold[i] for i in fam_items) / len(fam_items)
                for c in d["conditions"]},
            "abstention_rate": {
                c: sum(labels[c].get(i) == "CANNOT_CHECK" for i in fam_items) / len(fam_items)
                for c in d["conditions"]},
            "n_items": len(fam_items),
        }
        gate_delta[fam] = boot["delta_direct_minus_gate"]
        cot_delta[fam] = cot["delta_direct_minus_gate"]

    all_inv = [t.item_id for t in tasks if gold[t.item_id] == "REJECT"]
    pooled = paired_bootstrap(labels["DIRECT"], labels["RAKL_GATE"], all_inv, d["bootstrap_seed"])
    gate_sign = sign_summary(gate_delta)
    cot_sign = sign_summary(cot_delta)

    verdict = (
        "BROAD_SIX_FAMILY_GENERALIZATION_SUPPORTED"
        if gate_sign["all_six_positive"] and cot_sign["sign_test_p_two_sided"] > 0.05
        else "SCOPED_HETEROGENEOUS__NOT_A_BROAD_CROSS_DOMAIN_LAW")

    return {
        "schema": "paper2-six-family-comparator-v1",
        "frozen_design": d,
        "n": len(tasks),
        "n_invalid_items": len(all_inv),
        "gold_counts": {k: sum(1 for v in gold.values() if v == k)
                        for k in ("ACCEPT", "REJECT", "CANNOT_CHECK")},
        "api_errors": errors,
        "parse_fail": {c: sum(v == "PARSE_FAIL" for v in labels[c].values())
                       for c in d["conditions"]},
        "pooled_false_accept": pooled,
        "pooled_three_way_accuracy": {
            c: sum(labels[c].get(i) == gold[i] for i in gold) / len(gold) for c in d["conditions"]},
        "per_family": per_family,
        "family_signs_gate_vs_direct": gate_sign,
        "family_signs_free_cot_vs_direct_CONTROL": cot_sign,
        "verdict": verdict,
        "claim_boundary":
            "Six exact-verifier families, ONE model (glm-5.2), ONE seed, generated "
            "known-world tasks with machine-readable target facts. Supports at most a "
            "six-family robustness claim for the fail-closed applicability GATE AS A "
            "SCAFFOLD on this benchmark. Does NOT establish natural-language witness "
            "extraction, natural-domain scientific transfer, frontier-model "
            "superiority, cross-model generality, or downstream research utility.",
        "grants_scientific_authority": False,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="gold-only pipeline proof; makes no API calls")
    ap.add_argument("--max-workers", type=int, default=10)
    args = ap.parse_args()
    RESULTS.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        out = dry_run()
        (RESULTS / "six_family_dry_run.json").write_text(json.dumps(out, indent=2) + "\n")
        r = out["gold_only_receipt"]
        print(json.dumps({"gold": r["gold_counts"],
                          "per_family_full_exact3": {f: v["full_exact3"] for f, v in r["per_family"].items()},
                          "per_family_mechanism_exact3": {f: v["mechanism_exact3"] for f, v in r["per_family"].items()},
                          "pipeline_sign_test": out["pipeline_check_sign_test"]}, indent=2))
        return
    out = live_run(args.max_workers)
    (RESULTS / "six_family.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({
        "pooled_false_accept": {k: out["pooled_false_accept"][k]
                                for k in ("direct", "gate", "delta_direct_minus_gate", "delta_ci95")},
        "per_family_direct_vs_gate": {f: [round(v["direct"], 4), round(v["gate"], 4)]
                                      for f, v in out["per_family"].items()},
        "family_signs": out["family_signs_gate_vs_direct"],
        "free_cot_control_signs": out["family_signs_free_cot_vs_direct_CONTROL"],
        "verdict": out["verdict"]}, indent=2))


if __name__ == "__main__":
    main()
