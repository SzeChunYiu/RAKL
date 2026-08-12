#!/usr/bin/env python3
"""Reproducible Paper I figures.

(1) projection_collision.pdf -- the projection-sufficiency collision structure:
    a 7x15 matrix over projection architectures x adversarial failure families,
    each cell = whether that architecture SEPARATES the minimal twin pair or
    COLLIDES it. Computed live from rakl.epistemic_projection_benchmark.audit_all
    (the same code behind Table 1). Shows that only the typed authority projection
    separates every family -- and, crucially, the *pattern* of collisions, not
    just an aggregate accuracy number.

(2) pendulum_series.pdf -- the small-amplitude period series
    T/T0 = 1 + theta0^2/16 + 11 theta0^4/3072 + ...  vs the exact elliptic-integral
    period (2/pi) K(sin(theta0/2)), making the "amplitude independence is only
    approximate" point visceral.

Run from repo root (package installed):  python publication/papers/paper-01-epistemic-mechanics/figures/make_paper1_figures.py
Colorblind-safe; print-oriented.
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.ticker import MultipleLocator
from scipy.special import ellipk

HERE = Path(__file__).resolve().parent
BLUE, VERM, INK = "#0072B2", "#D55E00", "#222222"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#444444",
                     "axes.linewidth": 0.8, "figure.dpi": 300})

# ---------- Figure 1: collision heatmap ----------
from rakl.epistemic_projection_benchmark import audit_all
arch = audit_all()["architectures"]
# canonical family order from any full collision list
fams = sorted({f for v in arch.values() for f in v["collision_pairs"]})
order = ["TEXT_MEMORY_ONLY", "SCALAR_CONFIDENCE", "PAIRWISE_COMPATIBILITY_ONLY",
         "MAJORITY_OR_REVIEWER_VOTE", "PROVENANCE_ONLY", "SIMPLE_TRANSACTIONAL_STATE",
         "RAKL_TYPED_AUTHORITY"]
order = [a for a in order if a in arch] + [a for a in arch if a not in order]
short = {"TEXT_MEMORY_ONLY": "Text memory", "SCALAR_CONFIDENCE": "Scalar confidence",
         "PAIRWISE_COMPATIBILITY_ONLY": "Pairwise compat.", "MAJORITY_OR_REVIEWER_VOTE": "Majority/vote",
         "PROVENANCE_ONLY": "Provenance only", "SIMPLE_TRANSACTIONAL_STATE": "Transactional state",
         "RAKL_TYPED_AUTHORITY": "Typed authority (RAKL)"}
# 1 = separated, 0 = collided
M = np.array([[0 if f in set(arch[a]["collision_pairs"]) else 1 for f in fams] for a in order])

figH, axH = plt.subplots(figsize=(9.4, 3.6))
cmap = ListedColormap(["#ECECEC", BLUE])
axH.imshow(M, cmap=cmap, vmin=0, vmax=1, aspect="auto")
axH.set_xticks(range(len(fams))); axH.set_xticklabels([f.split("_")[0] for f in fams], fontsize=7)
axH.set_yticks(range(len(order))); axH.set_yticklabels([short.get(a, a) for a in order], fontsize=8)
for i in range(len(order)):
    sep = int(M[i].sum())
    axH.text(len(fams)-0.4, i, f"{sep}/15", va="center", ha="left", fontsize=7.4,
             color=(BLUE if sep == len(fams) else INK))
axH.set_xticks(np.arange(-.5, len(fams), 1), minor=True)
axH.set_yticks(np.arange(-.5, len(order), 1), minor=True)
axH.grid(which="minor", color="white", lw=1.4); axH.tick_params(which="minor", length=0)
axH.set_xlabel("adversarial failure family (F01–F15)")
axH.set_title("Twin-pair separation by projection architecture  "
              "(blue = separated, grey = collided)", fontsize=9, loc="left")
figH.tight_layout()
figH.savefig(str(HERE / "projection_collision.pdf"), bbox_inches="tight")
figH.savefig(str(HERE / "projection_collision.png"), bbox_inches="tight", dpi=200)

# ---------- Figure 2: pendulum series vs exact ----------
th = np.linspace(0.01, np.deg2rad(170), 400)
exact = (2/np.pi) * ellipk(np.sin(th/2)**2)         # scipy ellipk takes m=k^2
s2 = 1 + th**2/16                                    # 2-term
s3 = 1 + th**2/16 + 11*th**4/3072                    # 3-term
deg = np.rad2deg(th)
figP, axP = plt.subplots(figsize=(5.2, 3.5))
axP.plot(deg, exact, color=INK, lw=2.0, label="exact  $(2/\\pi)K(\\sin(\\theta_0/2))$")
axP.plot(deg, s2, color=BLUE, lw=1.6, ls="--", label="series to $\\theta_0^2$")
axP.plot(deg, s3, color=VERM, lw=1.6, ls=":", label="series to $\\theta_0^4$")
axP.set_xlabel("amplitude $\\theta_0$ (degrees)"); axP.set_ylabel("$T/T_0$")
axP.set_xlim(0, 170); axP.set_ylim(0.98, 1.7)
axP.xaxis.set_major_locator(MultipleLocator(30))
axP.grid(color="#DDDDDD", lw=0.6); axP.set_axisbelow(True)
for s in ("top", "right"): axP.spines[s].set_visible(False)
axP.legend(frameon=False, fontsize=8, loc="upper left")
axP.set_title("Pendulum period: amplitude-independence is only approximate", fontsize=9, loc="left")
figP.tight_layout()
figP.savefig(str(HERE / "pendulum_series.pdf"), bbox_inches="tight")
figP.savefig(str(HERE / "pendulum_series.png"), bbox_inches="tight", dpi=200)
print("wrote projection_collision.pdf and pendulum_series.pdf; typed separates",
      int(M[order.index('RAKL_TYPED_AUTHORITY')].sum()), "/", len(fams))
