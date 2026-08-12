from __future__ import annotations

from rakl.structural_types import (
    BoundaryCondition,
    StructuralObject,
    StructuralRelation,
    StructuralRole,
)

from .types import FamilyId


def sequence_composition_structure(
    structure_id: str,
    *,
    domain: str,
    composition_tag: str,
    boundary_regime: str,
    representation: str,
) -> StructuralObject:
    """Non-commutative operator-chain family."""

    prefix = structure_id.replace("-", "_")
    return StructuralObject(
        structure_id=structure_id,
        domain=domain,
        qoi="final_state_correctness",
        context_id=f"{domain}-ordered-composition",
        roles=(
            StructuralRole(f"{prefix}_operand", "operand"),
            StructuralRole(f"{prefix}_operator", "operator"),
            StructuralRole(f"{prefix}_result", "result"),
        ),
        relations=(
            StructuralRelation(f"{prefix}_operand", "transformed_by", f"{prefix}_operator"),
            StructuralRelation(f"{prefix}_operator", "yields", f"{prefix}_result"),
        ),
        invariants=frozenset({f"operator_order_fixed:{composition_tag}"}),
        boundaries=(
            BoundaryCondition("composition_regime", composition_tag),
            BoundaryCondition("flow_regime", boundary_regime),
            BoundaryCondition("representation", representation),
        ),
        evidence_ids=(f"generator:training-ladder:{structure_id}",),
    )


def balance_conservation_structure(
    structure_id: str,
    *,
    domain: str,
    composition_tag: str,
    boundary_regime: str,
    representation: str,
) -> StructuralObject:
    """Conservation/balance family."""

    prefix = structure_id.replace("-", "_")
    return StructuralObject(
        structure_id=structure_id,
        domain=domain,
        qoi="balance_holds",
        context_id=f"{domain}-conserved-flow",
        roles=(
            StructuralRole(f"{prefix}_inflow", "inflow"),
            StructuralRole(f"{prefix}_outflow", "outflow"),
            StructuralRole(f"{prefix}_store", "accumulator"),
        ),
        relations=(
            StructuralRelation(f"{prefix}_inflow", "feeds", f"{prefix}_store"),
            StructuralRelation(f"{prefix}_store", "releases", f"{prefix}_outflow"),
        ),
        invariants=frozenset({f"mass_balance:{composition_tag}"}),
        boundaries=(
            BoundaryCondition("closure_regime", boundary_regime),
            BoundaryCondition("composition_tag", composition_tag),
            BoundaryCondition("representation", representation),
        ),
        evidence_ids=(f"generator:training-ladder:{structure_id}",),
    )


def state_reachability_structure(
    structure_id: str,
    *,
    domain: str,
    composition_tag: str,
    boundary_regime: str,
    representation: str,
) -> StructuralObject:
    """Finite-state reachability family."""

    prefix = structure_id.replace("-", "_")
    return StructuralObject(
        structure_id=structure_id,
        domain=domain,
        qoi="target_reachable",
        context_id=f"{domain}-finite-automaton",
        roles=(
            StructuralRole(f"{prefix}_state", "state"),
            StructuralRole(f"{prefix}_event", "event"),
            StructuralRole(f"{prefix}_target", "target"),
        ),
        relations=(
            StructuralRelation(f"{prefix}_state", "consumes", f"{prefix}_event"),
            StructuralRelation(f"{prefix}_event", "advances_toward", f"{prefix}_target"),
        ),
        invariants=frozenset({f"reachability_graph:{composition_tag}"}),
        boundaries=(
            BoundaryCondition("transition_regime", boundary_regime),
            BoundaryCondition("composition_tag", composition_tag),
            BoundaryCondition("representation", representation),
        ),
        evidence_ids=(f"generator:training-ladder:{structure_id}",),
    )


FAMILY_BUILDERS = {
    FamilyId.SEQUENCE_COMPOSITION: sequence_composition_structure,
    FamilyId.BALANCE_CONSERVATION: balance_conservation_structure,
    FamilyId.STATE_REACHABILITY: state_reachability_structure,
}
