#!/usr/bin/env python3
"""Cross-model Phase-1 result figure (frozen Qwen ladder). Reads ../data/<model>_outcomes.jsonl.
Honest labels; instrument measurement, NOT a scientific-authority or promotion signal."""
import json
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
HERE=Path(__file__).resolve().parent; DATA=HERE.parent/"data"; OUT=HERE.parent/"phase1_result"
MODELS=[("0p5b","0.5B","#999999"),("1p5b","1.5B","#56B4E9"),("3b","3B","#0072B2"),("7b","7B","#D55E00")]
EXP=[1,2,4,8,16,32,64]
def same_struct(mfile,family):
    rows=[json.loads(l) for l in open(DATA/mfile)]
    d={r["exposure_count"]:r["accuracy"] for r in rows if r["family"]==family and r["probe_kind"]=="SAME_STRUCTURE"}
    return [d.get(e) for e in EXP]
fig,(axA,axB)=plt.subplots(1,2,figsize=(8.6,3.3))
x=list(range(len(EXP)))
for tag,lbl,col in MODELS:
    axA.plot(x,same_struct(f"{tag}_outcomes.jsonl","state_reachability"),marker="o",ms=4,lw=2,color=col,label=lbl)
axA.axhline(0.5,ls="--",lw=1,color="#222",alpha=.6)
axA.text(0.1,0.52,"chance",fontsize=7,color="#222")
axA.set_title("(a) state\\_reachability (the one learnable family)",fontsize=9,loc="left")
axA.set_ylabel("same-structure accuracy",fontsize=8)
# panel b: the two families that never left chance (7B, representative)
for fam,col in [("balance_conservation","#009E73"),("sequence_composition","#CC79A7")]:
    axB.plot(x,same_struct("7b_outcomes.jsonl",fam),marker="s",ms=4,lw=2,color=col,label=fam.replace("_","\\_"))
axB.axhline(0.5,ls="--",lw=1,color="#222",alpha=.6)
axB.set_title("(b) other two families never left chance (7B)",fontsize=9,loc="left")
axB.set_ylabel("same-structure accuracy",fontsize=8)
for ax in (axA,axB):
    ax.set_xticks(x); ax.set_xticklabels(EXP,fontsize=8); ax.set_xlabel("exposure count",fontsize=8)
    ax.set_ylim(-0.05,1.08); ax.yaxis.set_major_locator(MultipleLocator(0.25))
    ax.grid(axis="y",color="#DDD",lw=.6); ax.set_axisbelow(True)
    for s in ("top","right"): ax.spines[s].set_visible(False)
    ax.legend(fontsize=7,frameon=False,loc="center right")
fig.suptitle("Phase-0/1 exposure instrument on the frozen Qwen ladder (seed 461) — no state-dependent residual; "
             "instrument measurement, not an authority signal",fontsize=8,style="italic",color="#555",y=1.03)
fig.tight_layout(); fig.savefig(str(OUT)+".pdf",bbox_inches="tight"); fig.savefig(str(OUT)+".png",dpi=200,bbox_inches="tight")
print("wrote",OUT.with_suffix(".pdf"))
