from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

import run_storyanalogy_factorized_v1 as V1

SOURCE_SHA = "a74f1799ec6eec32a1d82aea5e036ac70c39feb298554c05da8382bf1d80319c"
ZONE = {"LOW":0,"MID":1,"HIGH":2}


def rel_zone(x: float) -> int:
    return ZONE["LOW"] if x <= 1.0 else ZONE["MID"] if x < 2.0 else ZONE["HIGH"]


def ent_zone(x: float) -> int:
    return ZONE["LOW"] if x <= 1.0 else ZONE["MID"] if x < 2.0 else ZONE["HIGH"]


def zone_state(proba, classes):
    classes=np.asarray(classes,dtype=int); arg=np.argmax(proba,axis=1)
    return classes[arg], proba[np.arange(len(proba)),arg]


def compose(zr, cr, ze, ce, tr, te):
    acc=(zr==ZONE["HIGH"]) & (cr>=tr) & (ze==ZONE["LOW"]) & (ce>=te)
    rej=((zr==ZONE["LOW"]) & (cr>=tr)) | ((ze==ZONE["HIGH"]) & (ce>=te))
    return np.where(acc,V1.L2I["ACCEPT"],np.where(rej,V1.L2I["REJECT"],V1.L2I["CANNOT_CHECK"]))


def ordinal_predict(prel, rel_classes, pent, ent_classes, tr, te):
    zr,cr=zone_state(prel,rel_classes); ze,ce=zone_state(pent,ent_classes)
    return compose(zr,cr,ze,ce,tr,te)


def choose_ordinal(prel,rc,pent,ec,y):
    best=None
    grid=[0.40,0.45,0.50,0.55,0.60,0.65,0.70,0.75,0.80,0.85,0.90]
    for tr in grid:
        for te in grid:
            pred=ordinal_predict(prel,rc,pent,ec,tr,te); m=V1.metrics(y,pred)
            if m["invalid_false_accept"]>0.15+1e-15 or m["valid_accept"]<0.50-1e-15:
                continue
            key=(m["exact3"],-m["invalid_false_accept"],m["valid_accept"],-tr,-te)
            if best is None or key>best[0]: best=(key,tr,te,pred,m)
    return None if best is None else best[1:]


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",required=True); a=ap.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(V1.URL,timeout=120) as r: raw=r.read()
    sha=hashlib.sha256(raw).hexdigest()
    if sha!=SOURCE_SHA:
        receipt={"schema_version":"paper2-storyanalogy-ordinal-result-v2","terminal":"RESOURCE_BLOCKED","reason":"source_sha256_changed","expected":SOURCE_SHA,"observed":sha,"grants_scientific_authority":False}
        (out/"FINAL_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n"); return 3
    rows=V1.load_text_rows(raw); assign,components=V1.partitions(rows)
    bp={p:sorted(i for i,v in assign.items() if v==p) for p in ("DEV","CALIBRATION","CONFIRMATORY")}
    surfaces={r["idx"]:V1.pair_surface(r["s1"],r["s2"]) for r in rows if r["idx"] in assign}
    stories={r["idx"]:(V1.norm_text(r["s1"]),V1.norm_text(r["s2"])) for r in rows if r["idx"] in assign}
    domains={r["idx"]:r["domain"] for r in rows if r["idx"] in assign}
    labels=V1.load_labels(raw,set(bp["DEV"]+bp["CALIBRATION"]))
    ydev=np.array([V1.L2I[labels[i]["gold"]] for i in bp["DEV"]]); ycal=np.array([V1.L2I[labels[i]["gold"]] for i in bp["CALIBRATION"]])
    vec=V1.build_vectorizer(); Xdev=vec.fit_transform([surfaces[i] for i in bp["DEV"]]); Xcal=vec.transform([surfaces[i] for i in bp["CALIBRATION"]])

    # Strongest frozen parent family from v1.
    direct=V1.clf(20260814); direct.fit(Xdev,ydev); pdir=direct.predict_proba(Xcal)
    dtau,p_parent,m_parent=V1.choose_direct(pdir,direct.classes_,ycal)

    rdev=np.array([rel_zone(labels[i]["relation"]) for i in bp["DEV"]]); edev=np.array([ent_zone(labels[i]["entity"]) for i in bp["DEV"]])
    rhead=V1.clf(20260816); ehead=V1.clf(20260817); rhead.fit(Xdev,rdev); ehead.fit(Xdev,edev)
    prel=rhead.predict_proba(Xcal); pent=ehead.predict_proba(Xcal)
    chosen=choose_ordinal(prel,rhead.classes_,pent,ehead.classes_,ycal)
    if chosen is None:
        receipt={"schema_version":"paper2-storyanalogy-ordinal-result-v2","terminal":"DEVELOPMENT_NEGATIVE_ORDINAL_NO_SAFE_THRESHOLD","source_sha256":sha,"partitions":{k:len(v) for k,v in bp.items()},"parent_calibration":m_parent,"confirmatory_labels_scored_or_used":False,"grants_scientific_authority":False}
        (out/"FINAL_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n"); return 1
    tr,te,pred,m_cand=chosen

    # Pre-confirmatory falsifiability battery.
    rng=np.random.default_rng(2026081401); s1=np.array([stories[i][0] for i in bp["CALIBRATION"]],dtype=object); s2=np.array([stories[i][1] for i in bp["CALIBRATION"]],dtype=object)
    xd=vec.transform([V1.pair_surface(x,y) for x,y in zip(s1[rng.permutation(len(s1))],s2[rng.permutation(len(s2))])])
    pred_d=ordinal_predict(rhead.predict_proba(xd),rhead.classes_,ehead.predict_proba(xd),ehead.classes_,tr,te); text_drop=m_cand["exact3"]-V1.metrics(ycal,pred_d)["exact3"]
    rr=np.random.default_rng(2026081602); er=np.random.default_rng(2026081603)
    pred_rs=ordinal_predict(prel[rr.permutation(len(prel))],rhead.classes_,pent,ehead.classes_,tr,te); pred_es=ordinal_predict(prel,rhead.classes_,pent[er.permutation(len(pent))],ehead.classes_,tr,te)
    pred_swap=ordinal_predict(pent,ehead.classes_,prel,rhead.classes_,tr,te)
    zr,cr=zone_state(prel,rhead.classes_); ze,ce=zone_state(pent,ehead.classes_)
    zr_c=zr.copy(); zr_c[zr_c==ZONE["MID"]]=ZONE["LOW"]; pred_rm=compose(zr_c,cr,ze,ce,tr,te)
    ze_c=ze.copy(); ze_c[ze_c==ZONE["MID"]]=ZONE["HIGH"]; pred_em=compose(zr,cr,ze_c,ce,tr,te)
    def mutation(predx):
        return {"changed_fraction":float(np.mean(predx!=pred)),"exact3_drop":m_cand["exact3"]-V1.metrics(ycal,predx)["exact3"]}
    m_rs,m_es,m_sw,m_rm,m_em=map(mutation,[pred_rs,pred_es,pred_swap,pred_rm,pred_em])
    gr=np.random.default_rng(2026081604); ys=ycal[gr.permutation(len(ycal))]; shuf_adv=float(np.mean(pred==ys)-np.mean(p_parent==ys))
    const={n:V1.metrics(ycal,np.full(len(ycal),V1.L2I[n],dtype=int)) for n in V1.LABELS}; triv=not any(x["valid_accept"]>=0.65 and x["invalid_false_accept"]<=0.15 for x in const.values())
    probes={
      "TEXT_DESTRUCTION":{"drop":text_drop,"pass":text_drop>=0.10-1e-15},
      "RELATION_ZONE_SHUFFLE":{**m_rs,"pass":m_rs["changed_fraction"]>=0.05-1e-15},
      "ENTITY_ZONE_SHUFFLE":{**m_es,"pass":m_es["changed_fraction"]>=0.05-1e-15},
      "HEAD_SWAP":{**m_sw,"pass":m_sw["changed_fraction"]>=0.05-1e-15},
      "RELATION_MID_COLLAPSE_TO_LOW":{**m_rm,"pass":m_rm["changed_fraction"]>=0.05-1e-15 or m_rm["exact3_drop"]>=0.05-1e-15},
      "ENTITY_MID_COLLAPSE_TO_HIGH":{**m_em,"pass":m_em["changed_fraction"]>=0.05-1e-15 or m_em["exact3_drop"]>=0.05-1e-15},
      "GOLD_SHUFFLE":{"advantage":shuf_adv,"pass":shuf_adv<0.02},
      "TRIVIAL_CONTROLS":{"metrics":const,"pass":triv}
    }
    if not all(x["pass"] for x in probes.values()):
        receipt={"schema_version":"paper2-storyanalogy-ordinal-result-v2","terminal":"INSTRUMENT_NOT_FALSIFIABLE_ORDINAL_V2","source_sha256":sha,"partitions":{k:len(v) for k,v in bp.items()},"candidate_calibration":{"tau_rel":tr,"tau_ent":te,"metrics":m_cand},"parent_calibration":{"tau":dtau,"metrics":m_parent},"falsifiability":probes,"confirmatory_labels_scored_or_used":False,"grants_scientific_authority":False}
        (out/"FINAL_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n"); return 2

    # Confirmation is opened only after the development and falsifiability gates above.
    lc=V1.load_labels(raw,set(bp["CONFIRMATORY"])); yc=np.array([V1.L2I[lc[i]["gold"]] for i in bp["CONFIRMATORY"]]); Xc=vec.transform([surfaces[i] for i in bp["CONFIRMATORY"]])
    pc=ordinal_predict(rhead.predict_proba(Xc),rhead.classes_,ehead.predict_proba(Xc),ehead.classes_,tr,te); pp=V1.direct_predict(direct.predict_proba(Xc),direct.classes_,dtau)
    mc,mp=V1.metrics(yc,pc),V1.metrics(yc,pp); point,ci=V1.bootstrap_diff(pc==yc,pp==yc)
    dom={}
    for d in sorted(set(domains[i] for i in bp["CONFIRMATORY"])):
        pos=np.array([j for j,i in enumerate(bp["CONFIRMATORY"]) if domains[i]==d]); dom[d]={"candidate":V1.metrics(yc[pos],pc[pos]),"parent":V1.metrics(yc[pos],pp[pos])}
    gate={"n_min":len(yc)>=1000,"three_classes":len(set(yc))==3,"adv_point":point>=0.02-1e-15,"adv_ci_lower":ci[0]>0,"valid_accept":mc["valid_accept"]>=0.65-1e-15,"false_accept":mc["invalid_false_accept"]<=0.15+1e-15,"cc_recall":mc["cannot_check_recall"]>=0.40-1e-15,"falsifiability":all(x["pass"] for x in probes.values())}
    if all(gate.values()): terminal="PROMOTE_CONDITIONALLY_EXTERNAL_HUMAN_ORDINAL_STRUCTURAL_ANALOGY_FACTORISATION_V2"
    elif mc["invalid_false_accept"]>0.15: terminal="NEGATIVE_ORDINAL_UNSAFE_FALSE_ACCEPT"
    elif mc["valid_accept"]<0.65: terminal="NEGATIVE_ORDINAL_OVERREFUSES_VALID_ANALOGIES"
    else: terminal="NEGATIVE_ORDINAL_NO_RESIDUAL_OVER_DIRECT_TEXT_PARENT"
    receipt={"schema_version":"paper2-storyanalogy-ordinal-result-v2","terminal":terminal,"source_sha256":sha,"n_rows":len(rows),"partitions":{k:len(v) for k,v in bp.items()},"candidate_calibration":{"tau_rel":tr,"tau_ent":te,"metrics":m_cand},"parent_calibration":{"tau":dtau,"metrics":m_parent},"falsifiability":probes,"confirmatory":{"candidate":mc,"parent":mp,"paired_exact3_advantage":point,"bootstrap_95ci":ci,"bootstrap_repetitions":10000,"domain_breakdown":dom},"promotion_gate":gate,"grants_scientific_authority":False,"claim_boundary":"External-human StoryAnalogy ordinal factorization only; no scientific authority, source-span witness, universal transfer, or end-to-end ORION utility."}
    (out/"FINAL_RECEIPT.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n"); return 0 if terminal.startswith("PROMOTE_") else 1

if __name__=="__main__": raise SystemExit(main())
