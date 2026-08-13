from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.ticker import MaxNLocator


ROOT = Path(__file__).resolve().parents[1]
STRESS_DIR = ROOT / "research" / "unified_problem_solving_v1"
if str(STRESS_DIR) not in sys.path:
    sys.path.insert(0, str(STRESS_DIR))
from run_known_world_stress import generate_results  # noqa: E402

GENERATED = ROOT / "paper" / "figures" / "generated"
DPI = 300


def _style() -> None:
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
        "font.size": 7.0,
        "axes.titlesize": 8.0,
        "axes.labelsize": 7.0,
        "xtick.labelsize": 6.5,
        "ytick.labelsize": 6.5,
        "legend.fontsize": 6.5,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "svg.fonttype": "none",
        "svg.hashsalt": "orion-unified-solver-v1",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


def _save(fig: plt.Figure, stem: Path) -> None:
    stem.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(stem.with_suffix(".pdf"), bbox_inches="tight", metadata={"Creator": "Orion unified solver figure generator", "CreationDate": None, "ModDate": None})
    fig.savefig(stem.with_suffix(".svg"), bbox_inches="tight", metadata={"Creator": "Orion unified solver figure generator"})
    fig.savefig(stem.with_suffix(".png"), bbox_inches="tight", dpi=DPI, metadata={"Software": "Orion unified solver figure generator"})
    plt.close(fig)


def _panel(ax: plt.Axes, label: str) -> None:
    ax.set_title(label, loc="left", fontweight="bold", pad=4)


def render_architecture(output_dir: Path) -> dict[str, Any]:
    _style()
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 7)
    ax.axis("off")

    nodes = [
        ("Human / world", 0.45, 5.6, 1.55, 0.72),
        ("Specification\nfidelity", 2.35, 5.6, 1.55, 0.72),
        ("Solver substrate", 4.35, 5.6, 1.7, 0.72),
        ("Verified\ncertificate", 6.55, 5.6, 1.55, 0.72),
        ("Epistemic /\nauthority state", 8.45, 5.6, 1.35, 0.72),
        ("Map belief\n+ coverage", 3.45, 3.9, 1.55, 0.72),
        ("Atlas / portals\n+ scale", 5.25, 3.9, 1.55, 0.72),
        ("Solvability\ngeometry", 7.05, 3.9, 1.55, 0.72),
        ("Navigation\ndynamics", 8.65, 3.9, 1.2, 0.72),
        ("MDD", 3.75, 2.15, 1.1, 0.65),
        ("VSC", 5.35, 2.15, 1.1, 0.65),
        ("Compute / scale /\nverification control", 7.15, 2.15, 1.85, 0.65),
        ("TaskEpisode / failures / Lessons / Self-Orion", 3.0, 0.55, 5.3, 0.72),
    ]
    boxes: dict[str, tuple[float, float, float, float]] = {}
    for label, x, y, w, h in nodes:
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.03,rounding_size=0.06", linewidth=0.9, fill=False)
        ax.add_patch(box)
        ax.text(x + w / 2, y + h / 2, label, ha="center", va="center", fontsize=7)
        boxes[label] = (x, y, w, h)

    def arrow(a: str, b: str, *, dashed: bool = False, label: str | None = None) -> None:
        ax0, ay0, aw, ah = boxes[a]
        bx0, by0, bw, bh = boxes[b]
        start = (ax0 + aw, ay0 + ah / 2) if bx0 >= ax0 else (ax0, ay0 + ah / 2)
        end = (bx0, by0 + bh / 2) if bx0 >= ax0 else (bx0 + bw, by0 + bh / 2)
        patch = FancyArrowPatch(start, end, arrowstyle="-|>", mutation_scale=8, linewidth=0.8, linestyle="--" if dashed else "-")
        ax.add_patch(patch)
        if label:
            ax.text((start[0] + end[0]) / 2, (start[1] + end[1]) / 2 + 0.16, label, ha="center", va="bottom", fontsize=6)

    arrow("Human / world", "Specification\nfidelity")
    arrow("Specification\nfidelity", "Solver substrate")
    arrow("Solver substrate", "Verified\ncertificate")
    arrow("Verified\ncertificate", "Epistemic /\nauthority state", label="verified evidence only")
    arrow("Map belief\n+ coverage", "Atlas / portals\n+ scale")
    arrow("Atlas / portals\n+ scale", "Solvability\ngeometry")
    arrow("Solvability\ngeometry", "Navigation\ndynamics")
    arrow("MDD", "VSC")
    arrow("VSC", "Compute / scale /\nverification control")

    # Non-authority relationship: solver-plane signals may route but do not promote.
    ax.annotate("routing / proposal only", xy=(9.05, 4.62), xytext=(8.75, 5.18), arrowprops={"arrowstyle": "-|>", "linestyle": "--", "linewidth": 0.8}, fontsize=6, ha="center")
    ax.annotate("episodes + residuals", xy=(5.65, 1.27), xytext=(5.65, 2.0), arrowprops={"arrowstyle": "-|>", "linewidth": 0.8}, fontsize=6, ha="center")
    ax.annotate("fresh-assured methods", xy=(4.95, 2.0), xytext=(4.95, 1.32), arrowprops={"arrowstyle": "-|>", "linestyle": "--", "linewidth": 0.8}, fontsize=6, ha="center")

    ax.text(4.4, 6.65, "Exact legality, uncertain map, fallible geometry, gated authority", ha="center", va="center", fontsize=8, fontweight="bold")
    ax.text(5.0, 3.15, "solver / navigation plane", ha="center", fontsize=6.5)
    ax.text(5.8, 1.72, "meta-control plane", ha="center", fontsize=6.5)
    ax.text(5.65, 0.25, "learning / evolution plane", ha="center", fontsize=6.5)

    _save(fig, output_dir / "unified_solver_architecture")
    return {
        "figure": "unified_solver_architecture",
        "status": "CONCEPTUAL_ARCHITECTURE",
        "claim_boundary": "diagram of implemented/proposed layer separation; not empirical superiority evidence",
        "nodes": [item[0] for item in nodes],
    }


def render_field_amortization(results: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    _style()
    data = results["field_amortization"]
    q = [row["queries"] for row in data["points"]]
    ratio = [row["field_over_baseline"] for row in data["points"]]
    fig, ax = plt.subplots(figsize=(4.2, 2.8))
    ax.plot(q, ratio, linewidth=1.5, marker="o", markersize=2.5, markevery=4, label="Compiled field / baseline work")
    ax.axhline(1.0, linewidth=0.8, linestyle="--", label="break-even")
    ax.axvline(data["break_even_queries_continuous"], linewidth=0.8, linestyle=":")
    ax.annotate(f"break-even = {data['break_even_queries_continuous']:.1f} uses", xy=(data["break_even_queries_continuous"], 1.0), xytext=(13, 1.65), arrowprops={"arrowstyle": "->", "linewidth": 0.7}, fontsize=6.5)
    ax.set_xlabel("Queries reusing the same compiled field")
    ax.set_ylabel("Total work ratio")
    ax.set_ylim(0, max(ratio) * 1.05)
    ax.set_xlim(1, max(q))
    ax.legend(frameon=False)
    ax.text(0.99, 0.02, "Development known world; build cost included", transform=ax.transAxes, ha="right", va="bottom", fontsize=6)
    _save(fig, output_dir / "unified_field_amortization")
    return data


def render_local_vs_closed_loop(results: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    _style()
    data = results["local_navigation"]
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.65), constrained_layout=True)

    ax = axes[0]
    labels = ["Local action\nalignment", "Strict greedy\nsuccess", "Bounded best-first\nsuccess"]
    values = [data["local_action_alignment"], float(data["strict_greedy_success"]), float(data["bounded_best_first_success"])]
    bars = ax.bar(range(3), values)
    ax.set_ylim(0, 1.08)
    ax.set_xticks(range(3), labels)
    ax.set_ylabel("Fraction / binary success")
    for rect, value in zip(bars, values):
        ax.text(rect.get_x() + rect.get_width()/2, value + 0.025, f"{value:.2f}", ha="center", va="bottom", fontsize=6.5)
    _panel(ax, "a  Local accuracy is not closed-loop navigation")

    ax = axes[1]
    greedy = data["strict_greedy_route"]
    branch = data["bounded_best_first_route"]
    ax.plot(range(len(greedy)), [1] * len(greedy), marker="o", linewidth=1.1, label="Strict greedy")
    ax.plot(range(len(branch)), [0] * len(branch), marker="s", linestyle="--", linewidth=1.1, label="Bounded best-first")
    ax.text(len(greedy) - 1, 1.08, greedy[-1], ha="center", fontsize=6.5)
    ax.text(len(branch) - 1, 0.08, branch[-1], ha="center", fontsize=6.5)
    ax.set_yticks([0, 1], ["success", "trap"])
    ax.set_xlabel("Decision depth")
    ax.set_ylim(-0.35, 1.35)
    ax.legend(frameon=False, loc="center left")
    _panel(ax, "b  Branch retention recovers the route")
    _save(fig, output_dir / "unified_local_vs_closed_loop")
    return data


def render_verification_pareto(results: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    _style()
    data = results["verification_pareto"]
    fig, ax = plt.subplots(figsize=(4.4, 3.1))
    markers = ["o", "s", "^", "D"]
    for marker, row in zip(markers, data["points"]):
        ax.scatter(row["false_reject_given_valid"], row["false_accept_given_invalid"], s=30, marker=marker)
        ax.annotate(f"{row['strategy']}\ncost={row['expected_cost']:.1f}", (row["false_reject_given_valid"], row["false_accept_given_invalid"]), xytext=(4, 4), textcoords="offset points", fontsize=6.2)
    ax.set_xlabel("False reject | globally valid")
    ax.set_ylabel("False accept | globally invalid")
    ax.set_xlim(left=-0.005)
    ax.set_ylim(bottom=-0.005)
    ax.text(0.99, 0.98, "lower-left is better; cost annotated", transform=ax.transAxes, ha="right", va="top", fontsize=6)
    _save(fig, output_dir / "unified_verification_pareto")
    return data


def render_path_quotient(results: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    _style()
    data = results["path_quotient"]
    m = [row["independent_transformations"] for row in data["points"]]
    histories = [row["sequential_histories"] for row in data["points"]]
    classes = [row["exact_partial_order_classes"] for row in data["points"]]
    fig, ax = plt.subplots(figsize=(4.2, 2.9))
    ax.semilogy(m, histories, marker="o", linewidth=1.4, label="Sequential histories")
    ax.semilogy(m, classes, marker="s", linestyle="--", linewidth=1.2, label="Exact partial-order classes")
    ax.set_xlabel("Pairwise-independent transformations")
    ax.set_ylabel("Representations of execution order")
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    ax.legend(frameon=False)
    ax.annotate("3,628,800 orderings → 1 class", xy=(10, histories[-1]), xytext=(5.8, histories[-1] / 35), arrowprops={"arrowstyle": "->", "linewidth": 0.7}, fontsize=6.5)
    _save(fig, output_dir / "unified_path_quotient")
    return data


def render(output_dir: Path = GENERATED) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = generate_results()
    source = {
        "schema_version": "orion-unified-solver-figure-source-v1",
        "known_world_results": results,
        "architecture": render_architecture(output_dir),
    }
    render_field_amortization(results, output_dir)
    render_local_vs_closed_loop(results, output_dir)
    render_verification_pareto(results, output_dir)
    render_path_quotient(results, output_dir)
    (output_dir / "unified_solver_known_world.source.json").write_text(json.dumps(source, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return source


def main() -> int:
    render(GENERATED)
    print(f"UNIFIED_SOLVER_FIGURES={GENERATED}")
    print("FIGURE_CLAIM_LEVEL=development_known_world_or_conceptual_only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
