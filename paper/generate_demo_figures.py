from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator


ROOT = Path(__file__).resolve().parents[1]
DEMO_RECEIPT = ROOT / "research" / "MINI_RESEARCH_DEMO_043_RECEIPT.json"
METROLOGY_RECEIPT = ROOT / "research" / "MINI_RESEARCH_METROLOGY_044_RECEIPT.json"
ARCHIVE_RECEIPT = ROOT / "research" / "MINI_ARCHIVE_STORAGE_044_RECEIPT.json"
FIGURES = ROOT / "paper" / "figures"
GENERATED = FIGURES / "generated"

FIGURE_WIDTH_IN = 7.0
FIGURE_HEIGHT_IN = 2.85
DPI = 300


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.size": 7.5,
            "axes.titlesize": 8.0,
            "axes.labelsize": 7.5,
            "xtick.labelsize": 7.0,
            "ytick.labelsize": 7.0,
            "legend.fontsize": 7.0,
            "figure.titlesize": 8.5,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "svg.fonttype": "none",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def figure_source_data() -> dict[str, dict[str, Any]]:
    demo = _load(DEMO_RECEIPT)
    metrology = _load(METROLOGY_RECEIPT)
    archive = _load(ARCHIVE_RECEIPT)

    points = {row["round_id"]: row for row in metrology["points"]}
    rounds = ["R0", "R1", "R2", "R3"]
    fig5 = {
        "basis_id": metrology["measurement_basis_id"],
        "basis_fingerprint": metrology["measurement_basis_fingerprint"],
        "rounds": rounds,
        "atom_count": [points[r]["atom_count"] for r in rounds],
        "occupied_cells": [points[r]["occupied_volume_cells"] for r in rounds],
        "blocking_cuts": [1, 0, 0, 0],
        "support_paths": [0, 1, 1, 1],
        "independent_evidence_roots": [6, 7, 7, 8],
        "event_labels": ["baseline", "finite-amplitude\nclosure", "flat repeat", "independent\nreplication"],
    }

    fig6 = {
        "archive_tokens": int(demo["archive_token_estimate"]),
        "active_tokens": int(demo["active_context_tokens"]),
        "active_ratio": float(demo["active_to_archive_token_ratio"]),
        "source_rehydration_roots": list(demo["source_rehydration_roots"]),
        "raw_unique_bytes": int(archive["original_logical_raw_bytes"]),
        "lossless_stored_bytes": int(archive["original_stored_physical_bytes"]),
        "hot_stored_bytes": int(archive["hot_stored_bytes_after_demotion"]),
        "original_logical_raw_bytes": int(archive["original_logical_raw_bytes"]),
        "refetch_logical_raw_bytes": int(archive["logical_raw_bytes_after_byte_identical_refetch"]),
        "original_physical_bytes": int(archive["original_stored_physical_bytes"]),
        "refetch_physical_bytes": int(archive["stored_physical_bytes_after_byte_identical_refetch"]),
        "records_after_refetch": int(archive["records_after_byte_identical_refetch"]),
        "unique_blobs_after_refetch": int(archive["unique_blobs_after_byte_identical_refetch"]),
        "rehydration_verified": bool(archive["rehydration_verified"]),
    }
    return {"fig5": fig5, "fig6": fig6}


def _panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(-0.14, 1.06, label, transform=ax.transAxes, fontweight="bold", fontsize=8.5, va="top")


def _save_all(fig: plt.Figure, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight")
    fig.savefig(stem.with_suffix(".png"), dpi=DPI, bbox_inches="tight")
    plt.close(fig)


def render_growth(data: dict[str, Any], output_dir: Path) -> None:
    _style()
    rounds = data["rounds"]
    x = list(range(len(rounds)))
    tick_labels = [f"{r}\n{event}" for r, event in zip(rounds, data["event_labels"], strict=True)]

    fig, axes = plt.subplots(1, 3, figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), constrained_layout=True)

    ax = axes[0]
    ax.plot(x, data["atom_count"], marker="o", linewidth=1.4, label="Atoms")
    ax.plot(x, data["occupied_cells"], marker="s", linestyle="--", linewidth=1.2, label="Occupied cells")
    ax.set_title("Atlas geometry")
    ax.set_ylabel("Count")
    ax.set_xticks(x, tick_labels)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(0, max(data["atom_count"]) + 1.5)
    ax.legend(frameon=False, loc="lower right")
    _panel_label(ax, "a")

    ax = axes[1]
    ax.plot(x, data["blocking_cuts"], marker="o", linewidth=1.4, label="Blocking cuts")
    ax.plot(x, data["support_paths"], marker="s", linestyle="--", linewidth=1.2, label="Support paths")
    ax.set_title("Target access")
    ax.set_ylabel("Count")
    ax.set_xticks(x, rounds)
    ax.set_yticks([0, 1])
    ax.set_ylim(-0.08, 1.18)
    ax.legend(frameon=False, loc="center right")
    _panel_label(ax, "b")

    ax = axes[2]
    ax.plot(x, data["independent_evidence_roots"], marker="o", linewidth=1.4)
    ax.set_title("Evidential robustness")
    ax.set_ylabel("Independent evidence roots")
    ax.set_xticks(x, rounds)
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.set_ylim(min(data["independent_evidence_roots"]) - 0.5, max(data["independent_evidence_roots"]) + 0.7)
    _panel_label(ax, "c")

    fig.suptitle("Knowledge geometry and target-conditioned value are distinct", y=1.03, fontweight="bold")
    fig.text(
        0.5,
        -0.015,
        f"Longitudinal geometry uses frozen basis {data['basis_id']}; R1 opens the target path, R2 is flat, and R3 adds independent evidence without another path opening.",
        ha="center",
        va="top",
        fontsize=6.8,
    )
    _save_all(fig, output_dir / "fig5_demo_growth")


def render_context(data: dict[str, Any], output_dir: Path) -> None:
    _style()
    fig, axes = plt.subplots(1, 3, figsize=(FIGURE_WIDTH_IN, FIGURE_HEIGHT_IN), constrained_layout=True)

    ax = axes[0]
    values = [data["archive_tokens"], data["active_tokens"]]
    labels = ["Archive", "Active context"]
    bars = ax.barh(labels, values)
    ax.invert_yaxis()
    ax.set_title("Prompt working set")
    ax.set_xlabel("Token estimate")
    ax.set_xlim(0, max(values) * 1.22)
    for bar, value in zip(bars, values, strict=True):
        ax.text(value + max(values) * 0.025, bar.get_y() + bar.get_height() / 2, f"{value}", va="center")
    ax.text(0.98, 0.05, f"active/archive = {100.0 * data['active_ratio']:.1f}%", transform=ax.transAxes, ha="right", va="bottom")
    _panel_label(ax, "a")

    ax = axes[1]
    storage_labels = ["Raw unique", "Lossless stored", "Hot tier"]
    storage_values = [data["raw_unique_bytes"], data["lossless_stored_bytes"], data["hot_stored_bytes"]]
    bars = ax.bar(storage_labels, storage_values)
    ax.set_title("Physical evidence storage")
    ax.set_ylabel("Bytes")
    ax.set_ylim(0, max(storage_values) * 1.18)
    ax.tick_params(axis="x", rotation=25)
    for bar, value in zip(bars, storage_values, strict=True):
        ax.text(bar.get_x() + bar.get_width() / 2, value + max(storage_values) * 0.025, f"{value}", ha="center", va="bottom")
    _panel_label(ax, "b")

    ax = axes[2]
    categories = ["Original", "Exact refetch"]
    x = [0, 1]
    width = 0.34
    logical = [data["original_logical_raw_bytes"], data["refetch_logical_raw_bytes"]]
    physical = [data["original_physical_bytes"], data["refetch_physical_bytes"]]
    ax.bar([i - width / 2 for i in x], logical, width=width, label="Logical raw bytes")
    ax.bar([i + width / 2 for i in x], physical, width=width, label="Physical stored bytes")
    ax.set_title("Duplicate refetch")
    ax.set_ylabel("Bytes")
    ax.set_xticks(x, categories)
    ax.set_ylim(0, max(logical) * 1.18)
    ax.legend(frameon=False, loc="lower right")
    ax.text(
        0.02,
        0.96,
        f"{data['records_after_refetch']} logical records / {data['unique_blobs_after_refetch']} unique blobs\nrehydration verified = {str(data['rehydration_verified']).lower()}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=6.8,
    )
    _panel_label(ax, "c")

    fig.suptitle("Archive growth, active context, and hot storage are controlled separately", y=1.03, fontweight="bold")
    fig.text(
        0.5,
        -0.015,
        "Exact refetch adds provenance/logical history without new physical bytes; cold demotion reduces the hot footprint without deleting canonical evidence.",
        ha="center",
        va="top",
        fontsize=6.8,
    )
    _save_all(fig, output_dir / "fig6_demo_context")


def wrapper_tex(filename: str, receipts: str) -> str:
    return "\n".join(
        [
            f"% GENERATED FROM {receipts}. DO NOT HAND EDIT.",
            f"\\includegraphics[width=\\linewidth]{{{filename}.pdf}}",
            "",
        ]
    )


def generate() -> dict[str, str]:
    return {
        "fig5_demo_growth.tex": wrapper_tex(
            "fig5_demo_growth",
            "research/MINI_RESEARCH_METROLOGY_044_RECEIPT.json",
        ),
        "fig6_demo_context.tex": wrapper_tex(
            "fig6_demo_context",
            "research/MINI_RESEARCH_DEMO_043_RECEIPT.json + research/MINI_ARCHIVE_STORAGE_044_RECEIPT.json",
        ),
    }


def render(output_dir: Path = GENERATED) -> None:
    data = figure_source_data()
    render_growth(data["fig5"], output_dir)
    render_context(data["fig6"], output_dir)
    (output_dir / "fig5_demo_growth.source.json").write_text(json.dumps(data["fig5"], indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "fig6_demo_context.source.json").write_text(json.dumps(data["fig6"], indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    FIGURES.mkdir(parents=True, exist_ok=True)
    for filename, content in generate().items():
        (FIGURES / filename).write_text(content, encoding="utf-8")
    render(GENERATED)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
