from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import json

from .lattice_metrology import (
    EpistemicStateSummary,
    LatticeMeasurementBasis,
    compare_epistemic_state,
    compare_lattices,
    measure_lattice,
)
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
    basis_comparable: bool


@dataclass(frozen=True)
class TargetValueTransition:
    from_round: str
    to_round: str
    blocking_cuts_closed: int
    support_paths_opened: int
    evidence_roots_added: int
    negative_history_objects_added: int
    target_access_improved: bool
    evidential_robustness_improved: bool
    completely_flat: bool


@dataclass(frozen=True)
class MiniResearchMetrologyReceipt:
    demo_id: str
    measurement_basis_id: str
    measurement_basis_fingerprint: str
    volume_definition: str
    density_definition: str
    value_definition: str
    points: tuple[MetrologyPoint, ...]
    transitions: tuple[MetrologyTransition, ...]
    target_value_transitions: tuple[TargetValueTransition, ...]
    proves_scientific_superiority: bool


def _basis() -> LatticeMeasurementBasis:
    return LatticeMeasurementBasis(
        basis_id="PENDULUM_FIBER_KIND_METROLOGY_V1",
        fiber_partition_semantics=(
            "fixed demo research fibers F:period, F:context, F:target and F:mechanism; "
            "volume counts occupied (fiber_id, KnowledgeAtomKind) cells"
        ),
        kind_schema_version="KnowledgeAtomKind:round043-v1",
        identity_policy_id="exact-canonical-key-plus-context:v1",
        context_schema_id="pendulum-earth-moon-amplitude-regime:v1",
    )


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
    basis: LatticeMeasurementBasis,
) -> MetrologyTransition:
    change = compare_lattices(
        before,
        after,
        before_basis=basis,
        after_basis=basis,
    )
    return MetrologyTransition(
        from_round=from_round,
        to_round=to_round,
        growth_class=change.growth_class.value,
        volume_delta_cells=change.volume_delta_cells,
        atom_delta=change.atom_delta,
        witness_delta=change.witness_delta,
        evidence_binding_delta=change.evidence_binding_delta,
        distinct_evidence_source_delta=change.distinct_evidence_source_delta,
        basis_comparable=change.basis_comparable,
    )


def _value_transition(
    from_round: str,
    to_round: str,
    before: EpistemicStateSummary,
    after: EpistemicStateSummary,
) -> TargetValueTransition:
    gain = compare_epistemic_state(before, after)
    return TargetValueTransition(
        from_round=from_round,
        to_round=to_round,
        blocking_cuts_closed=gain.blocking_cuts_closed,
        support_paths_opened=gain.support_paths_opened,
        evidence_roots_added=gain.independent_evidence_roots_added,
        negative_history_objects_added=gain.negative_history_objects_added,
        target_access_improved=gain.target_access_improved,
        evidential_robustness_improved=gain.evidential_robustness_improved,
        completely_flat=gain.completely_flat,
    )


def run_mini_research_metrology() -> MiniResearchMetrologyReceipt:
    basis = _basis()
    empty = TypedKnowledgeLattice.empty()
    r0 = _base_lattice(include_finite=False)
    r1 = _finite_snapshot(include_replication=False)
    r2 = r1
    r3 = _finite_snapshot(include_replication=True)

    e0 = EpistemicStateSummary(1, 0, 6, 1)
    e1 = EpistemicStateSummary(0, 1, 7, 1)
    e2 = EpistemicStateSummary(0, 1, 7, 1)
    e3 = EpistemicStateSummary(0, 1, 8, 1)

    return MiniResearchMetrologyReceipt(
        demo_id="PENDULUM_CONTEXT_ATLAS_001_METROLOGY_V2",
        measurement_basis_id=basis.basis_id,
        measurement_basis_fingerprint=basis.fingerprint,
        volume_definition=(
            "count of occupied (fiber_id, atom_kind) cells under one frozen measurement-basis fingerprint; "
            "discrete proxy, not Euclidean volume"
        ),
        density_definition="atoms per occupied cell, with relation and evidence densities reported separately",
        value_definition=(
            "non-compensatory target coordinates: blocking cuts closed, support paths opened, "
            "independent evidence roots added and negative-history objects added"
        ),
        points=(
            _point("EMPTY", empty),
            _point("R0", r0),
            _point("R1", r1),
            _point("R2", r2),
            _point("R3", r3),
        ),
        transitions=(
            _transition("EMPTY", "R0", empty, r0, basis),
            _transition("R0", "R1", r0, r1, basis),
            _transition("R1", "R2", r1, r2, basis),
            _transition("R2", "R3", r2, r3, basis),
        ),
        target_value_transitions=(
            _value_transition("R0", "R1", e0, e1),
            _value_transition("R1", "R2", e1, e2),
            _value_transition("R2", "R3", e2, e3),
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
