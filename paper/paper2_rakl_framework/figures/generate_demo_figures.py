from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "source_data"
GENERATED = ROOT / "generated"
DEMO = DATA / "MINI_RESEARCH_DEMO_043_RECEIPT.json"
METROLOGY = DATA / "MINI_RESEARCH_METROLOGY_044_RECEIPT.json"
ARCHIVE = DATA / "MINI_ARCHIVE_STORAGE_044_RECEIPT.json"

FIGURE_WIDTH_IN = 7.0
FIGURE_HEIGHT_IN = 2.8
DPI = 300


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7.5,
        "axes.titlesize": 8.0,
        "axes.labelsize": 7.5,
        "xtick.labelsize": 7.0,
        "ytick.labelsize": 7.0,
        "legend.fontsize": 7.0,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def source_data() -> dict[str, dict[str, Any]]:
    demo = _load(DEMO)
    metrology = _load(METROLOGY)
    archive = _load(ARCHIVE)
    points = {row["round_id"]: row for row in metrology["points"]}
    rounds = ["R0", "R1", "R2", "R3"]
    return {
        "fig5": {
            "basis_id": metrology["measurement_basis_id"],
            "basis_fingerprint": metrology["measurement_basis_fingerprint"],
            "rounds": rounds,
            "atom_count": [points[r]["atom_count"] for r in rounds],
            "occupied_cells": [points[r]["occupied_volume_cells"] for r in rounds],
            "blocking_cuts": [1, 0, 0, 0],
            "support_paths": [0, 1, 1, 1],
            "independent_evidence_roots": [6, 7, 7, 8],
        },
        "fig6": {
            "archive_tokens": int(demo["archive_token_estimate"]),
            "active_tokens": int(demo["active_context_tokens"]),
            "raw_unique_bytes": int(archive["original_logical_raw_bytes"]),
            "lossless_stored_bytes": int(archive["original_stored_physical_bytes"]),
            "hot_stored_bytes": int(archive["hot_stored_bytes_after_demotion"]),
            "original_logical_raw_bytes": int(archive["original_logical_raw_bytes"]),
            "refetch_logical_raw_bytes": int(archive["logical_raw_bytes_after_byte_identical_refetch"]),
            "original_physical_bytes": int(archive["original_stored_physical_bytes"]),
            "refetch_physical_bytes": int(archive["stored_physical_bytes_after_byte_identical_refetch"]),
            "rehydration_verified": bool(archive["rehydration_verified"]),
        },
    }


def _panel(ax: plt.Axes, label: str) -> None:
    ax.set_title(label, loc="left", fontweight="bold", fontsize=8.0, pad=5.0)


def _save(fig: plt.Figure, stem: str) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    target = GENERATED / stem
    fig.savefig(target.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(target.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(target.with_suffix(".png"), dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def render_growth(data: dict[str, Any]) -> None:
    _style()
    x = list(range(len(data["rounds"])))
    fig, axes = plt.subplots(1, 3, figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), constrained_layout=True)
    ax = axes[0]
    ax.plot(x, data["atom_count"], marker="o", linewidth=1.4, label="Atoms")
    ax.plot(x, data["occupied_cells"], marker="s", linestyle="--", linewidth=1.2, label="Occupied cells")
    ax.set_title("Atlas geometry")
    ax.set_ylabel("Count")
    ax.set_xticks(x, data["rounds"])
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(0, max(data["atom_count"]) + 1.5)
    ax.legend(frameon=False, loc="lower right")
    _panel(ax, "a")
    ax = axes[1]
    ax.plot(x, data["blocking_cuts"], marker="o", linewidth=1.4, label="Blocking cuts")
    ax.plot(x, data["support_paths"], marker="s", linestyle="--", linewidth=1.2, label="Support paths")
    ax.set_title("Target access")
    ax.set_ylabel("Count")
    ax.set_xticks(x, data["rounds"])
    ax.set_yticks([0, 1])
    ax.set_ylim(-0.08, 1.18)
    ax.legend(frameon=False, loc="center right")
    _panel(ax, "b")
    ax = axes[2]
    ax.plot(x, data["independent_evidence_roots"], marker="o", linewidth=1.4)
    ax.set_title("Evidential robustness")
    ax.set_ylabel("Independent evidence roots")
    ax.set_xticks(x, data["rounds"])
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(min(data["independent_evidence_roots"]) - 0.5, max(data["independent_evidence_roots"]) + 0.7)
    _panel(ax, "c")
    _save(fig, "fig5_demo_growth")


def render_context(data: dict[str, Any]) -> None:
    _style()
    fig, axes = plt.subplots(1, 3, figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), constrained_layout=True)
    ax = axes[0]
    values = [data["archive_tokens"], data["active_tokens"]]
    ax.barh(["Archive", "Active context"], values)
    ax.invert_yaxis()
    ax.set_title("Prompt working set")
    ax.set_xlabel("Token estimate")
    ax.set_xlim(0, max(values) * 1.08)
    _panel(ax, "a")
    ax = axes[1]
    storage = [data["raw_unique_bytes"], data["lossless_stored_bytes"], data["hot_stored_bytes"]]
    ax.barh(["Raw unique", "Lossless stored", "Hot tier"], storage)
    ax.invert_yaxis()
    ax.set_title("Physical evidence storage")
    ax.set_xlabel("Bytes")
    ax.set_xlim(0, max(storage) * 1.08)
    _panel(ax, "b")
    ax = axes[2]
    x = [0, 1]
    width = 0.34
    logical = [data["original_logical_raw_bytes"], data["refetch_logical_raw_bytes"]]
    physical = [data["original_physical_bytes"], data["refetch_physical_bytes"]]
    ax.bar([i - width / 2 for i in x], logical, width=width, label="Logical raw bytes")
    ax.bar([i + width / 2 for i in x], physical, width=width, label="Physical stored bytes")
    ax.set_title("Duplicate refetch")
    ax.set_ylabel("Bytes")
    ax.set_xticks(x, ["Original", "Exact refetch"])
    ax.set_ylim(0, max(logical) * 1.18)
    ax.legend(frameon=False, loc="upper left")
    _panel(ax, "c")
    _save(fig, "fig6_demo_context")


def main() -> int:
    data = source_data()
    render_growth(data["fig5"])
    render_context(data["fig6"])
    for stem, key in [("fig5_demo_growth", "fig5"), ("fig6_demo_context", "fig6")]:
        (GENERATED / f"{stem}.source.json").write_text(json.dumps(data[key], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (ROOT / "fig5_demo_growth.tex").write_text("% GENERATED; do not hand edit.\n\\includegraphics[width=\\linewidth]{figures/generated/fig5_demo_growth.pdf}\n", encoding="utf-8")
    (ROOT / "fig6_demo_context.tex").write_text("% GENERATED; do not hand edit.\n\\includegraphics[width=\\linewidth]{figures/generated/fig6_demo_context.pdf}\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
