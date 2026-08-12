#!/usr/bin/env python3
"""Reproducible Paper III figure: the preregistered ORACLE capability ladder.

Success rate of the ExperienceBenchmark ORACLE upper-bound arm at each rung of the
frozen model-size ladder, against the registered oracle-pass gate (>= 2/3). Every
rung falls below the gate, so each is classified MODEL_CAPABILITY_FLOOR and the
four-arm causal study stays unauthorized (CAPABLE_MODEL_AVAILABLE = NO_REFUTED).

Values are the committed, manuscript-reported results (section 07a) from the frozen
ORACLE receipts (native jobs noted per rung); success_rate_primary verified in
research/paper2_experience_benchmark_v1_3_2/ORACLE_DECISION_RECEIPT_V1_3_2.json (3B = 0.0).

Run from repo root:  python publication/papers/paper-03-method-evolution-mechanics/figures/make_capability_ladder.py
"""
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent.parent
BLUE, VERM, INK = "#0072B2", "#D55E00", "#222222"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": "#444444",
                     "axes.linewidth": 0.8, "figure.dpi": 300})

# rung label, success rate, job note
LADDER = [
    ("0.5B",    0/3, "job 3476730/31"),
    ("1.5B",    0/3, "job 3476756"),
    ("3B",      0/3, "job 3476778"),
    ("7B",      1/3, "job 3476788"),
    ("7B\n(V2 sealed)", 2/5, "job 3476813"),
]
GATE = 2/3  # registered oracle_pass_min_success_rate

labels = [l for l, _, _ in LADDER]
rates = [r for _, r, _ in LADDER]
x = np.arange(len(labels))

fig, ax = plt.subplots(figsize=(6.0, 3.6))
bars = ax.bar(x, rates, 0.62, color=BLUE)
for r, v in zip(bars, rates):
    ax.text(r.get_x()+r.get_width()/2, v+0.015, f"{v:.2f}", ha="center", va="bottom",
            fontsize=8, color=INK)
ax.axhline(GATE, color=VERM, ls="--", lw=1.2)
ax.text(len(labels)-0.5, GATE+0.015, f"oracle-pass gate = 2/3 ({GATE:.2f})",
        ha="right", va="bottom", color=VERM, fontsize=8)
ax.annotate("every rung below gate  →  MODEL_CAPABILITY_FLOOR\nfour-arm causal study stays unauthorized",
            xy=(1.5, 0.05), xytext=(1.5, 0.52), ha="center", fontsize=7.6, color=INK,
            arrowprops=dict(arrowstyle="-", color="#BBBBBB", lw=0.8))
ax.set_ylim(0, 0.8); ax.set_ylabel("ORACLE success rate")
ax.set_xticks(x); ax.set_xticklabels(labels, fontsize=8)
ax.set_xlabel("preregistered model-size ladder (Qwen2.5-Instruct)")
ax.grid(axis="y", color="#DDDDDD", lw=0.6); ax.set_axisbelow(True)
for s in ("top", "right"): ax.spines[s].set_visible(False)
ax.set_title("ORACLE capability ladder: no rung clears the success gate", fontsize=9, loc="left")
fig.tight_layout()
fig.savefig(str(HERE / "capability_ladder.pdf"), bbox_inches="tight")
fig.savefig(str(HERE / "capability_ladder.png"), bbox_inches="tight", dpi=200)
print("wrote capability_ladder.pdf")
