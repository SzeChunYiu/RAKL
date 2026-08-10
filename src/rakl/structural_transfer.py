from __future__ import annotations

from rakl.structural_types import (
    StructuralObject,
    StructuralRelation,
    StructuralWitness,
    TransferAssessment,
    TransferDecision,
)


def _mapped_relation(
    relation: StructuralRelation,
    role_map: dict[str, str],
) -> tuple[str, str, str, bool] | None:
    source = role_map.get(relation.source_role)
    target = role_map.get(relation.target_role)
    if source is None or target is None:
        return None
    return (source, relation.relation_type, target, relation.directed)


def assess_transfer(
    source: StructuralObject,
    target: StructuralObject,
    witness: StructuralWitness,
) -> TransferAssessment:
    """Validate a directional, QoI-scoped structural transfer witness.

    The gate refuses transfer when the mapping fails to preserve source relations or
    declared invariants, when target boundary conditions do not match, or when the target
    QoI differs.  Surface/domain labels never enter the positive license condition.
    """

    reasons: list[str] = []
    if witness.source_structure_id != source.structure_id:
        reasons.append("source_identity_mismatch")
    if witness.target_structure_id != target.structure_id:
        reasons.append("target_identity_mismatch")
    if reasons:
        return TransferAssessment(
            decision=TransferDecision.CANNOT_CHECK,
            reasons=tuple(reasons),
            preserved_relation_count=0,
            required_relation_count=len(source.relations),
            preserved_invariant_count=0,
            required_invariant_count=len(source.invariants),
        )

    if source.qoi != target.qoi:
        reasons.append("qoi_mismatch")

    role_map = dict(witness.role_mapping)
    if not source.role_ids.issubset(role_map):
        reasons.append("incomplete_source_role_mapping")
    if not set(role_map.values()).issubset(target.role_ids):
        reasons.append("target_role_missing")

    target_relations = {relation.signature for relation in target.relations}
    preserved_relations = 0
    for relation in source.relations:
        mapped = _mapped_relation(relation, role_map)
        if mapped is not None and mapped in target_relations:
            preserved_relations += 1
        else:
            reasons.append(
                "relation_not_preserved:"
                f"{relation.source_role}:{relation.relation_type}:{relation.target_role}"
            )

    required_invariants = source.invariants
    declared_preserved = witness.preserved_invariants
    if not declared_preserved.issubset(source.invariants):
        reasons.append("witness_claims_unknown_source_invariant")
    if not declared_preserved.issubset(target.invariants):
        reasons.append("declared_invariant_missing_in_target")
    preserved_invariants = len(required_invariants.intersection(declared_preserved).intersection(target.invariants))
    if preserved_invariants != len(required_invariants):
        reasons.append("source_invariants_not_fully_preserved")

    target_boundaries = target.boundary_map
    for required in witness.required_target_boundaries:
        if target_boundaries.get(required.key) != required.value:
            reasons.append(f"boundary_mismatch:{required.key}")

    if not witness.evidence_ids:
        reasons.append("missing_witness_evidence")

    decision = TransferDecision.LICENSED if not reasons else TransferDecision.REJECTED
    return TransferAssessment(
        decision=decision,
        reasons=tuple(reasons),
        preserved_relation_count=preserved_relations,
        required_relation_count=len(source.relations),
        preserved_invariant_count=preserved_invariants,
        required_invariant_count=len(required_invariants),
    )


def structural_overlap_score(source: StructuralObject, target: StructuralObject) -> float:
    """Simple transparent baseline over relation/invariant type signatures.

    This is a diagnostic baseline, not a claim of a new graph similarity metric.  Role
    names are intentionally omitted; relation types and invariants are compared as sets.
    """

    source_features = {f"rel:{r.relation_type}:{int(r.directed)}" for r in source.relations}
    target_features = {f"rel:{r.relation_type}:{int(r.directed)}" for r in target.relations}
    source_features |= {f"inv:{item}" for item in source.invariants}
    target_features |= {f"inv:{item}" for item in target.invariants}
    union = source_features | target_features
    if not union:
        return 1.0
    return len(source_features & target_features) / len(union)
