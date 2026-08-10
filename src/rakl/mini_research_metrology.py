from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json

from .lattice_metrology import compare_lattices, measure_lattice
from .mini_research_demo import _base_lattice
from .typed_lattice import TypedKnowledgeLattice


@dataclass(frozen=True)
class MetrologyPoint:
    round_id: str
    atom_count: int
    occupied_volume_cells: int
    atom_cell_density: float
    witness_count: int
    relation_density: float
    evidence_binding_count: int
    distinct_evidence_sources: int


@dataclass(frozen=True)
class MetrologyTransition:
    from_round: str
    to_round: str
    growth_class: str
    volume_delta_cells: int
    atom_delta: int
    witness_delta: int
    evidence_binding_delta: int
    distinct_evidence_source_delta: int


@dataclass(frozen=True)
class MiniResearchMetrologyReceipt:
    demo_id: str
    volume_definition: str
    density_definition: str
    points: tuple[MetrologyPoint, ...]
    transitions: tuple[MetrologyTransition, ...]
    proves_scientific_superiority: bool


def _finite_snapshot(*, include_replication: bool) -> TypedKnowledgeLattice:
    full = _base_lattice(include_finite=True)
    snapshot = TypedKnowledgeLattice.empty()
    for atom in full.atoms.values():
        if atom.atom_id == "A:finite-law" and not include_replication:
            atom = replace(atom, evidence_ids=("S3",))
        snapshot.add_atom(atom)
    for witness in full.witnesses.values():
        snapshot.add_witness(witness)
    return snapshot


def _point(round_id: str, lattice: TypedKnowledgeLattice) -> MetrologyPoint:
    metrics = measure_lattice(lattice)
    return MetrologyPoint(
        round_id=round_id,
        atom_count=metrics.atom_count,
        occupied_volume_cells=metrics.occupied_volume_cells,
        atom_cell_density=round(metrics.atom_cell_density, 6),
        witness_count=metrics.witness_count,
        relation_density=round(metrics.relation_density, 6),
        evidence_binding_count=metrics.evidence_binding_count,
        distinct_evidence_sources=metrics.distinct_evidence_sources,
    )


def _transition(
    from_round: str,
    to_round: str,
    before: TypedKnowledgeLattice,
    after: TypedKnowledgeLattice,
) -> MetrologyTransition:
    change = compare_lattices(before, after)
    return MetrologyTransition(
        from_round=from_round,
        to_round=to_round,
        growth_class=change.growth_class.value,
        volume_delta_cells=change.volume_delta_cells,
        atom_delta=change.atom_delta,
        witness_delta=change.witness_delta,
        evidence_binding_delta=change.evidence_binding_delta,
        distinct_evidence_source_delta=change.distinct_evidence_source_delta,
    )


def run_mini_research_metrology() -> MiniResearchMetrologyReceipt:
    empty = TypedKnowledgeLattice.empty()
    r0 = _base_lattice(include_finite=False)
    r1 = _finite_snapshot(include_replication=False)
    r2 = r1
    r3 = _finite_snapshot(include_replication=True)

    return MiniResearchMetrologyReceipt(
        demo_id="PENDULUM_CONTEXT_ATLAS_001_METROLOGY_V1",
        volume_definition="count of occupied (fiber_id, atom_kind) cells; discrete proxy, not Euclidean volume",
        density_definition="atoms per occupied cell, with relation and evidence densities reported separately",
        points=(
            _point("EMPTY", empty),
            _point("R0", r0),
            _point("R1", r1),
            _point("R2", r2),
            _point("R3", r3),
        ),
        transitions=(
            _transition("EMPTY", "R0", empty, r0),
            _transition("R0", "R1", r0, r1),
            _transition("R1", "R2", r1, r2),
            _transition("R2", "R3", r2, r3),
        ),
        proves_scientific_superiority=False,
    )


def receipt_json(*, indent: int = 2) -> str:
    return json.dumps(asdict(run_mini_research_metrology()), indent=indent, sort_keys=True) + "\n"


def main() -> int:
    print(receipt_json(), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
