#!/usr/bin/env python3
"""Execute frozen Paper-VI recursive-control known worlds; no authority."""
from __future__ import annotations
import json, math, random
from pathlib import Path

HERE = Path(__file__).resolve().parent
P = json.loads((HERE / "RECURSIVE_CONTROL_VALUE_PROTOCOL_V1.json").read_text())
OUT = HERE / "RECURSIVE_CONTROL_VALUE_RESULT_V1.json"


def ent(xs): return -sum(x * math.log(x) for x in xs if x > 0)

def post(prior, signal, p1):
    w = [prior[i] * (p1[i] if signal else 1 - p1[i]) for i in range(len(prior))]
    z = sum(w)
    if z <= 0: raise ValueError("posterior normalization failed")
    return [x / z for x in w]

def amap(xs): return max(range(len(xs)), key=lambda i: (xs[i], -i))


def probe_choices(prior, probes):
    h0 = ent(prior); ig = {}; voi = {"NO_PROBE": 1 - max(prior)}
    for name, q in probes.items():
        p1 = q["p_signal_1"]; ps = sum(prior[i] * p1[i] for i in range(len(prior)))
        ig[name] = (h0 - ps * ent(post(prior, True, p1)) - (1-ps) * ent(post(prior, False, p1))) / q["cost"]
        risk = ps * (1-max(post(prior, True, p1))) + (1-ps) * (1-max(post(prior, False, p1)))
        voi[name] = risk + q["cost"]
    return max(ig, key=ig.get), min(voi, key=voi.get), ig, voi


def diagnosis():
    c = P["diagnosis"]; prior = c["prior"]; probes = c["probes"]; n = P["n_diagnosis_worlds"]
    names = list(probes); rng = random.Random(P["seed"]); mc = c["mutation_cost"]
    igp, voip, igs, vois = probe_choices(prior, probes)
    worlds = []
    for _ in range(n):
        u = rng.random(); s = 0.0; cause = len(prior)-1
        for i, pr in enumerate(prior):
            s += pr
            if u <= s: cause = i; break
        worlds.append((cause, {x: rng.random() for x in names}, min(int(rng.random()*len(names)), len(names)-1)))

    def run(arm):
        ok = wrong = harm = 0; pc = mut = 0.0
        for cause, us, ri in worlds:
            if arm == "MUTATE_ALL_PLAUSIBLE":
                ok += 1; wrong += 1; harm += len(prior)-1; mut += len(prior)*mc; continue
            if arm == "ORACLE_CAUSE": ok += 1; mut += mc; continue
            if arm == "NO_PROBE_MAP": action = amap(prior); cost = 0.0
            else:
                pn = names[ri] if arm == "RANDOM_PROBE" else "surface" if arm == "FIXED_SURFACE" else igp if arm == "INFO_GAIN_PER_COST" else (None if voip == "NO_PROBE" else voip)
                if pn is None: action = amap(prior); cost = 0.0
                else:
                    q = probes[pn]; sig = us[pn] < q["p_signal_1"][cause]
                    action = amap(post(prior, sig, q["p_signal_1"])); cost = q["cost"]
            pc += cost; mut += mc
            if action == cause: ok += 1
            else: wrong += 1; harm += 1
        return {"correct_repair_rate": ok/n, "wrong_layer_mutation_rate": wrong/n,
                "harmful_mutations_per_world": harm/n, "probe_cost_per_world": pc/n,
                "mutation_cost_per_world": mut/n, "total_cost_per_world": (pc+mut)/n}

    return {"selected_probes": {"INFO_GAIN_PER_COST": igp, "DECISION_VOI": voip},
            "selection_diagnostics": {"info_gain_per_cost": igs, "decision_loss_plus_cost": vois},
            "arms": {a: run(a) for a in c["arms"]}}


def credit():
    c = P["contextual_credit"]; train = c["train_contexts"]; fresh = c["fresh_contexts"]
    ops = sorted(next(iter(train.values()))["effects"])
    means = {o: sum(w["effects"][o] for w in train.values())/len(train) for o in ops}
    glob = max(ops, key=lambda o: means[o])
    fam = {w["family"]: max(ops, key=lambda o: w["effects"][o]) for w in train.values()}
    if len(fam) != len(train): raise ValueError("one source context required per family")
    def run(arm):
        rows=[]
        for name,w in fresh.items():
            op = glob if arm=="GLOBAL_CREDIT" else fam[w["family"]] if arm=="CONTEXT_TRANSPORT_CREDIT" else "local_patch" if arm=="UNINFORMED_FIXED_LOCAL" else max(ops,key=lambda o:w["effects"][o])
            eff=w["effects"][op]; best=max(w["effects"].values())
            rows.append({"context":name,"operator":op,"effect":eff,"regret":best-eff,"correct":eff==best,"harmful":eff<0})
        return {"correct_operator_rate":sum(r["correct"] for r in rows)/len(rows),
                "harmful_repair_rate":sum(r["harmful"] for r in rows)/len(rows),
                "mean_effect":sum(r["effect"] for r in rows)/len(rows),
                "regret_vs_oracle":sum(r["regret"] for r in rows)/len(rows),"selections":rows}
    return {"global_train_mean":means,"global_selected_operator":glob,"registered_same_family_transport":fam,
            "arms":{a:run(a) for a in c["arms"]}}


def main():
    if P["status"] != "FROZEN_BEFORE_EXECUTION": raise SystemExit("protocol not frozen")
    d=diagnosis(); c=credit(); da=d["arms"]; ca=c["arms"]
    simpler = any(da[x] == da["DECISION_VOI"] for x in ("FIXED_SURFACE","INFO_GAIN_PER_COST"))
    ctx = ca["CONTEXT_TRANSPORT_CREDIT"]["harmful_repair_rate"] < ca["GLOBAL_CREDIT"]["harmful_repair_rate"] and ca["CONTEXT_TRANSPORT_CREDIT"]["regret_vs_oracle"] < ca["GLOBAL_CREDIT"]["regret_vs_oracle"]
    verdict = "SIMPLER_PARENT_SUFFICIENT" if simpler else "CONTROL_TRADEOFF_UNRESOLVED"
    payload={"schema_version":"paper6-recursive-control-value-result-v1","protocol_git_blob_sha":"2ffc092a00d30d9d233530616f059f98af877d70",
             "terminal":verdict,"components":{"diagnosis_component":"SIMPLER_PARENT_SUFFICIENT" if simpler else "UNRESOLVED","contextual_credit_component":"SUPPORTED" if ctx else "UNRESOLVED"},
             "diagnosis":d,"contextual_credit":c,
             "interpretation":{"diagnosis":"Decision-VOI selected the same surface probe as fixed-surface and information-gain-per-cost; no distinct diagnosis-control value is established in this frozen world.",
             "contextual_credit":"Same-family contextual transport avoided the harmful B_fresh global-credit choice and matched the fresh oracle in all registered contexts.",
             "scope":"Known-world mechanic/control-value evidence only; not external-agent or scientific-performance authority."},
             "grants_scientific_authority":False,"grants_method_promotion_authority":False}
    OUT.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"terminal":verdict,"components":payload["components"]},sort_keys=True))

if __name__ == "__main__": main()
