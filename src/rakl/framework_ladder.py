"""The framework's progressive build, made checkable.

Each layer introduces atoms and becomes able to express something the layers
beneath it cannot. A layer may depend only on layers beneath it. That is the
progressive-build invariant, and it is what "Paper N builds on Paper N-1" means
operationally.

The ladder is not a new taxonomy. It is read off
``docs/FORMAL_SYSTEM_SPECIFICATION.md``, whose sections are already ordered by
dependency. The papers were carved by theme on top of a spec already ordered by
dependency, which is why they do not compose: measured over all ``.tex``, Papers
IV and VI reference all five others while I, II, III reference exactly one each
and V references none — and Paper II, which sits directly above Paper I, cites it
zero times by any phrasing.

Proposal-only. Grants no scientific or promotion authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json

_REPO = Path(__file__).resolve().parents[2]
LADDER_PATH = _REPO / "research" / "framework_ladder" / "ladder.json"


class LadderError(RuntimeError):
    """Raised when the declared ladder is not a well-founded progressive build."""


@dataclass(frozen=True)
class Layer:
    layer_id: str
    name: str
    atoms_introduced: tuple[str, ...]
    depends_on: tuple[str, ...]
    papers_covering: tuple[str, ...]
    benefit_obligation: str
    expresses: str


def load_ladder(path: Path | None = None) -> dict[str, Any]:
    with (path or LADDER_PATH).open(encoding="utf-8") as handle:
        return json.load(handle)


def layers(ladder: dict[str, Any] | None = None) -> tuple[Layer, ...]:
    payload = ladder if ladder is not None else load_ladder()
    return tuple(
        Layer(
            layer_id=entry["layer_id"],
            name=entry["name"],
            atoms_introduced=tuple(entry["atoms_introduced"]),
            depends_on=tuple(entry["depends_on"]),
            papers_covering=tuple(entry["papers_covering"]),
            benefit_obligation=entry["benefit_obligation"],
            expresses=entry["expresses"],
        )
        for entry in payload["layers"]
    )


def structural_problems(ladder: dict[str, Any] | None = None) -> tuple[str, ...]:
    """Ways the declared ladder would fail to be a progressive build.

    A forward dependency is the specific defect that makes "builds on" false: if
    a layer needs an atom introduced above it, the build order is a fiction.
    """
    found = layers(ladder)
    order = {layer.layer_id: index for index, layer in enumerate(found)}
    problems: list[str] = []

    seen_atoms: dict[str, str] = {}
    for layer in found:
        for dep in layer.depends_on:
            if dep not in order:
                problems.append(f"{layer.layer_id}: depends on unknown layer {dep}")
            elif order[dep] >= order[layer.layer_id]:
                problems.append(
                    f"{layer.layer_id}: forward dependency on {dep}; a layer may "
                    "depend only on layers beneath it"
                )
        for atom in layer.atoms_introduced:
            if atom in seen_atoms:
                problems.append(
                    f"{layer.layer_id}: re-introduces atom {atom!r} already "
                    f"introduced by {seen_atoms[atom]}"
                )
            else:
                seen_atoms[atom] = layer.layer_id
        if not layer.benefit_obligation.strip():
            problems.append(f"{layer.layer_id}: no benefit obligation stated")

    # The first layer is the only one permitted to stand on nothing.
    for layer in found[1:]:
        if not layer.depends_on:
            problems.append(
                f"{layer.layer_id}: declares no dependency; only the base layer may "
                "stand on nothing, otherwise the build is not progressive"
            )
    return tuple(problems)


def unhoused_layers(ladder: dict[str, Any] | None = None) -> tuple[str, ...]:
    """Layers no paper covers. An unhoused layer is a gap in the programme."""
    return tuple(layer.layer_id for layer in layers(ladder) if not layer.papers_covering)


def paper_layer_span(ladder: dict[str, Any] | None = None) -> dict[str, list[str]]:
    """Which layers each paper touches, in ladder order."""
    span: dict[str, list[str]] = {}
    for layer in layers(ladder):
        for paper in layer.papers_covering:
            key = paper.split()[0]  # tolerate annotations like "I (only as of PR #623)"
            span.setdefault(key, []).append(layer.layer_id)
    return span


def implied_paper_dependencies(ladder: dict[str, Any] | None = None) -> tuple[tuple[str, str], ...]:
    """Paper-level dependencies implied by the layer ladder.

    If paper P covers a layer that depends on a layer covered only by paper Q,
    then P depends on Q whether or not P cites Q. These are the edges that
    *should* exist in the manuscripts.
    """
    found = layers(ladder)
    owner: dict[str, set[str]] = {}
    for layer in found:
        owner[layer.layer_id] = {p.split()[0] for p in layer.papers_covering}

    edges: set[tuple[str, str]] = set()
    for layer in found:
        for dep in layer.depends_on:
            upstream_papers = owner.get(dep, set())
            for downstream in owner.get(layer.layer_id, set()):
                # If the downstream paper covers the dependency layer itself, it
                # carries its own foundation and owes no citation for it. Only a
                # paper standing on a layer it does not cover incurs the edge.
                if downstream in upstream_papers:
                    continue
                for upstream in upstream_papers:
                    if downstream != upstream:
                        edges.add((downstream, upstream))
    return tuple(sorted(edges))


def missing_paper_citations(ladder: dict[str, Any] | None = None) -> tuple[str, ...]:
    """Implied dependencies that the measured citation graph does not realize.

    This is the concrete form of "the papers do not build on each other": an edge
    the ladder requires and the manuscripts do not contain.
    """
    payload = ladder if ladder is not None else load_ladder()
    measured = payload["measured_paper_coupling"]["edges"]
    gaps: list[str] = []
    for downstream, upstream in implied_paper_dependencies(payload):
        if measured.get(downstream, {}).get(upstream, 0) == 0:
            gaps.append(f"{downstream} depends on {upstream} via the ladder but cites it 0 times")
    return tuple(gaps)


def main() -> int:  # pragma: no cover - thin CLI
    ladder = load_ladder()
    for layer in layers(ladder):
        papers = ", ".join(layer.papers_covering) or "NO PAPER"
        print(f"{layer.layer_id:<22} {papers}")
    problems = structural_problems(ladder)
    unhoused = unhoused_layers(ladder)
    gaps = missing_paper_citations(ladder)
    print(f"\nstructural problems: {len(problems)}")
    for item in problems:
        print(f"  - {item}")
    print(f"unhoused layers: {list(unhoused) or 'none'}")
    print(f"\nladder-implied paper dependencies not realized in the manuscripts: {len(gaps)}")
    for item in gaps:
        print(f"  - {item}")
    return 1 if problems or unhoused else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
