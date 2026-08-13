#!/usr/bin/env python3
"""Plot the field-hypothesis known-world result. Development evidence; no authority."""
import json
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
HERE=Path(__file__).resolve().parent
d=json.load(open(HERE/"results"/"field_hypothesis.json"))
pw=d["per_world"]
pred=[w["predictiveness"] for w in pw if w["predictiveness"] is not None]
redu=[w["reduction"] for w in pw]
BLUE,VERM,INK="#0072B2","#D55E00","#222222"
fig,(a,b)=plt.subplots(1,2,figsize=(8.4,3.2))
a.hist(pred,bins=24,color=BLUE,alpha=.85,edgecolor="white",linewidth=.4)
fp=d["field_descent_predicts_true_progress"]
a.axvline(fp["mean"],color=INK,lw=2); a.axvline(0.5,color=VERM,ls="--",lw=1)
a.text(0.5,a.get_ylim()[1]*0.9,"chance",color=VERM,fontsize=7,ha="center")
a.set_title(f"(a) cheap-field descent predicts true progress\nmean {fp['mean']:.2f} [{fp['lo']:.2f},{fp['hi']:.2f}] ; ~{(1-fp['mean'])*100:.0f}% false-attractor tail",fontsize=8.5,loc="left")
a.set_xlabel("per-world fraction where field descent = verified progress",fontsize=8); a.set_ylabel("worlds",fontsize=8)
b.hist(redu,bins=24,color="#009E73",alpha=.85,edgecolor="white",linewidth=.4)
sr=d["search_reduction_vs_bfs"]
b.axvline(sr["mean"],color=INK,lw=2); b.axvline(0,color=VERM,ls="--",lw=1)
b.set_title(f"(b) search reduction vs uninformed BFS\nmean {sr['mean']:.2f} [{sr['lo']:.2f},{sr['hi']:.2f}] ; reduces search in {d['fraction_worlds_field_reduces_search']*100:.1f}% of worlds",fontsize=8.5,loc="left")
b.set_xlabel("1 - nodes(field-guided)/nodes(BFS)",fontsize=8); b.set_ylabel("worlds",fontsize=8)
for ax in (a,b):
    for s in ("top","right"): ax.spines[s].set_visible(False)
    ax.grid(axis="y",color="#EEE",lw=.6); ax.set_axisbelow(True)
fig.suptitle(f"Solvability-field hypothesis on {d['worlds']} random known worlds (seed {d['seed']}) — "
             "development known-world evidence, not an authority signal",fontsize=8,style="italic",color="#555",y=1.02)
fig.tight_layout()
for ext in ("pdf","png"):
    fig.savefig(str(HERE/f"results/field_hypothesis.{ext}"),bbox_inches="tight",dpi=200 if ext=="png" else None)
print("wrote field_hypothesis.pdf/.png")
