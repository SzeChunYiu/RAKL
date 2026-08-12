#!/usr/bin/env python3
"""Reproducible Paper II objective-lane results figure.

Reads the committed, frozen PRIMARY confirmatory evidence (four-family v1) from
research/empirical_10_of_10_v1/PAPER3/OBJECTIVE/ and renders a two-panel figure:

  Panel A: three-way exact accuracy and invalid-transfer false-accept rate for
           each projection arm, ordered by increasing applicability structure.
  Panel B: paired binary-Brier reduction of each control relative to the full
           applicability contract, with item-bootstrap 95% CIs and the
           preregistered 0.05 material-effect threshold.

This visualizes ONLY the already-reported primary four-family result. It does not
touch the pending six-family robustness confirmatory freeze.

Run from repo root:  python publication/papers/paper-02-structural-mechanics/figures/make_objective_results_figure.py
Colorblind-safe (Okabe-Ito) palette; print-oriented (no color-only encoding).
"""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

REPO = Path(__file__).resolve().parents[4]
EV = Path(__file__).resolve().parent.parent / "data"
OUT = Path(__file__).resolve().parent.parent / "objective_results"

pr = json.loads((EV / "PREDICTIVE_RESULTS.json").read_text())
pi = json.loads((EV / "PAIRED_INFERENCE.json").read_text())

# Okabe-Ito colorblind-safe
BLUE, VERM, INK, MUTE = "#0072B2", "#D55E00", "#222222", "#888888"

ARMS = [
    ("LEXICAL_JACCARD", "Lexical\n(Jaccard)"),
    ("RELATIONAL_ONLY", "Relational\nonly"),
    ("MECHANISM_DERIVED_EFFECT_ONLY", "Mechanism\nonly"),
    ("COORDINATE_ABLATED_TWIN", "Coord.-ablated\ntwin"),
    ("FULL_APPLICABILITY_CONTRACT", "Full\ncontract"),
]
labels = [l for _, l in ARMS]
exact3 = [pr["arms"][k]["exact3"] for k, _ in ARMS]
false_acc = [pr["arms"][k].get("invalid_false_accept", 0.0) for k, _ in ARMS]

plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#444444",
                     "axes.linewidth": 0.8, "figure.dpi": 300})
fig, (axA, axB) = plt.subplots(1, 2, figsize=(9.2, 3.5),
                               gridspec_kw={"width_ratios": [1.55, 1.0]})

# ---- Panel A: grouped bars ----
import numpy as np
x = np.arange(len(labels)); w = 0.38
b1 = axA.bar(x - w/2, exact3, w, label="3-way exact accuracy", color=BLUE)
b2 = axA.bar(x + w/2, false_acc, w, label="invalid-transfer false-accept", color=VERM)
for bars, vals in ((b1, exact3), (b2, false_acc)):
    for r, v in zip(bars, vals):
        axA.text(r.get_x()+r.get_width()/2, v+0.015, f"{v:.2f}",
                 ha="center", va="bottom", fontsize=7.2, color=INK)
axA.set_ylim(0, 1.08); axA.set_ylabel("rate")
axA.set_xticks(x); axA.set_xticklabels(labels, fontsize=7.6)
axA.yaxis.set_major_locator(MultipleLocator(0.25))
axA.grid(axis="y", color="#DDDDDD", lw=0.6); axA.set_axisbelow(True)
for s in ("top", "right"): axA.spines[s].set_visible(False)
axA.legend(frameon=False, fontsize=7.6, loc="upper left", ncol=1)
axA.set_title("(a) Accuracy and false-accept by projection arm", fontsize=9, loc="left")

# ---- Panel B: paired Brier reduction forest ----
contrasts = [
    ("LEXICAL_MINUS_FULL_DELTA", "Lexical − Full"),
    ("RELATIONAL_MINUS_FULL_DELTA", "Relational − Full"),
    ("MECHANISM_MINUS_FULL_DELTA", "Mechanism − Full"),
]
deltas = [pi["paired_binary_brier"][k] for k, _ in contrasts]
cis = [pi["paired_item_bootstrap_95ci"][k] for k, _ in contrasts]
yy = np.arange(len(contrasts))[::-1]
for y, dlt, (lo, hi) in zip(yy, deltas, cis):
    axB.plot([lo, hi], [y, y], color=INK, lw=1.6, solid_capstyle="round", zorder=3)
    axB.plot(dlt, y, "o", ms=6, color=BLUE, zorder=4)
    axB.text(hi+0.012, y, f"{dlt:.3f}", va="center", fontsize=7.4, color=INK)
mde = pi["registered_mde_binary_brier"]
axB.axvline(mde, color=VERM, ls="--", lw=1.1)
axB.text(mde+0.006, len(contrasts)-0.5, f"preregistered\nMDE = {mde}",
         color=VERM, fontsize=7.0, va="top")
axB.set_yticks(yy); axB.set_yticklabels([l for _, l in contrasts], fontsize=8)
axB.set_xlim(0, 0.46); axB.set_xlabel("paired binary-Brier reduction vs full contract")
axB.xaxis.set_major_locator(MultipleLocator(0.1))
axB.grid(axis="x", color="#DDDDDD", lw=0.6); axB.set_axisbelow(True)
for s in ("top", "right", "left"): axB.spines[s].set_visible(False)
axB.tick_params(axis="y", length=0)
axB.set_title(f"(b) Paired reduction vs full contract (95% CI, n={pi['n_decidable']})",
              fontsize=9, loc="left")

fig.tight_layout(w_pad=2.0)
fig.savefig(str(OUT)+".pdf", bbox_inches="tight")
fig.savefig(str(OUT)+".png", bbox_inches="tight", dpi=200)
print("wrote", OUT.with_suffix(".pdf"))
