#!/usr/bin/env python3
"""Plot the development-tier LLM comparator result with bootstrap 95% CIs.
Reads raw_results.jsonl; renders comparator_result.pdf/.png. Honest labels; dev-tier."""
import json, numpy as np
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

HERE=Path(__file__).resolve().parent
rows=[json.loads(l) for l in open(HERE/"raw_results.jsonl") if l.strip()]
CONDS=["DIRECT","FREE_COT","RAKL_GATE"]
LBL={"DIRECT":"Direct\n(plain)","FREE_COT":"Free CoT\n(control)","RAKL_GATE":"Orion gate\n(obligations)"}
BLUE,VERM,INK,GREEN="#0072B2","#D55E00","#222222","#009E73"
COL={"DIRECT":INK,"FREE_COT":"#888888","RAKL_GATE":BLUE}
rng=np.random.default_rng(7)

def by(cond): return {r["item_id"]:r for r in rows if r["condition"]==cond}
def boot(mask_vals, stat, B=20000):
    v=np.array(mask_vals,float); idx=rng.integers(0,len(v),(B,len(v)))
    s=stat(v[idx]); return v.mean() if len(v) else 0, np.percentile(s,2.5), np.percentile(s,97.5)

# per condition: false-accept on invalid (gold==REJECT), and 3-way accuracy (all)
FA={}; ACC={}
for c in CONDS:
    d=by(c)
    inv=[1.0 if d[i]["model"]=="ACCEPT" else 0.0 for i in d if d[i]["gold"]=="REJECT"]
    allc=[1.0 if d[i]["model"]==d[i]["gold"] else 0.0 for i in d]
    FA[c]=boot(inv, lambda a:a.mean(1))
    ACC[c]=boot(allc, lambda a:a.mean(1))

fig,(axA,axB)=plt.subplots(1,2,figsize=(8.4,3.4))
x=np.arange(3)
for ax,data,title,ylab,better in [
    (axA,FA,"(a) Invalid-transfer false-accept  (lower = safer)","false-accept rate on gold-REJECT","down"),
    (axB,ACC,"(b) Three-way accuracy  (higher = better)","accuracy vs exact-verifier gold","up")]:
    m=[data[c][0] for c in CONDS]; lo=[data[c][0]-data[c][1] for c in CONDS]; hi=[data[c][2]-data[c][0] for c in CONDS]
    bars=ax.bar(x,m,0.62,color=[COL[c] for c in CONDS],
                yerr=[lo,hi],capsize=4,error_kw=dict(lw=1,ecolor=INK))
    for xi,mi in zip(x,m): ax.text(xi,mi+ (max(m)*0.02+0.012),f"{mi:.2f}",ha="center",va="bottom",fontsize=8,color=INK)
    ax.set_xticks(x); ax.set_xticklabels([LBL[c] for c in CONDS],fontsize=8)
    ax.set_ylim(0, max(max(m)+0.18,0.7)); ax.set_ylabel(ylab,fontsize=8)
    ax.yaxis.set_major_locator(MultipleLocator(0.2)); ax.grid(axis="y",color="#DDD",lw=0.6); ax.set_axisbelow(True)
    for s in ("top","right"): ax.spines[s].set_visible(False)
    ax.set_title(title,fontsize=9,loc="left")
fig.suptitle("GLM 5.2 on ~504 fresh transfer tasks (exact-verifier gold; seed 20260812) — CONFIRMATORY",
             fontsize=8.5,style="italic",color="#555",y=1.02,x=0.5)
fig.tight_layout()
fig.savefig(HERE/"comparator_result.pdf",bbox_inches="tight")
fig.savefig(HERE/"comparator_result.png",bbox_inches="tight",dpi=200)
print("false-accept 95% CIs:")
for c in CONDS: print(f"  {c:10} FA={FA[c][0]:.3f} [{FA[c][1]:.3f},{FA[c][2]:.3f}]  ACC={ACC[c][0]:.3f} [{ACC[c][1]:.3f},{ACC[c][2]:.3f}]")
