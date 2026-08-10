from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from rakl.structural_types import (
    BoundaryCondition,
    StructuralObject,
    StructuralRelation,
    StructuralRole,
    StructuralWitness,
)


class SimilarityQuadrant(str, Enum):
    Q1_HIGH_SEM_HIGH_STRUCT = "Q1_HIGH_SEM_HIGH_STRUCT"
    Q2_LOW_SEM_HIGH_STRUCT = "Q2_LOW_SEM_HIGH_STRUCT"
    Q3_HIGH_SEM_LOW_STRUCT = "Q3_HIGH_SEM_LOW_STRUCT"
    Q4_LOW_SEM_LOW_STRUCT = "Q4_LOW_SEM_LOW_STRUCT"


@dataclass(frozen=True)
class StructuralBenchmarkCase:
    case_id: str
    family: str
    quadrant: SimilarityQuadrant
    semantic_similarity_label: str
    structural_match_expected: bool
    source: StructuralObject
    target: StructuralObject
    witness: StructuralWitness


def _queue_structure(structure_id: str, domain: str, prefix: str) -> StructuralObject:
    return StructuralObject(
        structure_id=structure_id,
        domain=domain,
        qoi="backlog_stability",
        context_id=f"{domain}-steady-flow",
        roles=(
            StructuralRole(f"{prefix}_arrival", "arrival_process"),
            StructuralRole(f"{prefix}_service", "service_capacity"),
            StructuralRole(f"{prefix}_backlog", "accumulated_queue"),
        ),
        relations=(
            StructuralRelation(f"{prefix}_arrival", "competes_with", f"{prefix}_service"),
            StructuralRelation(f"{prefix}_arrival", "increases", f"{prefix}_backlog"),
            StructuralRelation(f"{prefix}_service", "decreases", f"{prefix}_backlog"),
        ),
        invariants=frozenset({"long_run_arrival_gt_service_implies_backlog_growth"}),
        boundaries=(
            BoundaryCondition("flow_regime", "continual"),
            BoundaryCondition("time_scale", "matched"),
        ),
        evidence_ids=(f"evidence:{structure_id}",),
    )


def _finite_batch_queue_decoy(structure_id: str, domain: str, prefix: str) -> StructuralObject:
    """Semantically queue-like but missing the continual-flow stability invariant."""

    return StructuralObject(
        structure_id=structure_id,
        domain=domain,
        qoi="backlog_stability",
        context_id=f"{domain}-finite-batch",
        roles=(
            StructuralRole(f"{prefix}_arrival", "arrival_process"),
            StructuralRole(f"{prefix}_service", "service_capacity"),
            StructuralRole(f"{prefix}_backlog", "accumulated_queue"),
        ),
        relations=(
            StructuralRelation(f"{prefix}_arrival", "loads_once", f"{prefix}_backlog"),
            StructuralRelation(f"{prefix}_service", "decreases", f"{prefix}_backlog"),
        ),
        invariants=frozenset({"finite_batch_eventually_drains_if_service_positive"}),
        boundaries=(
            BoundaryCondition("flow_regime", "finite_batch"),
            BoundaryCondition("time_scale", "matched"),
        ),
        evidence_ids=(f"evidence:{structure_id}",),
    )


def _feedback_structure(structure_id: str, domain: str, prefix: str) -> StructuralObject:
    return StructuralObject(
        structure_id=structure_id,
        domain=domain,
        qoi="growth_amplification",
        context_id=f"{domain}-positive-feedback",
        roles=(
            StructuralRole(f"{prefix}_state", "state"),
            StructuralRole(f"{prefix}_response", "response"),
        ),
        relations=(
            StructuralRelation(f"{prefix}_state", "increases", f"{prefix}_response"),
            StructuralRelation(f"{prefix}_response", "increases", f"{prefix}_state"),
        ),
        invariants=frozenset({"positive_feedback_can_amplify_perturbations"}),
        boundaries=(BoundaryCondition("feedback_sign", "positive"),),
        evidence_ids=(f"evidence:{structure_id}",),
    )


def _negative_feedback_decoy(structure_id: str, domain: str, prefix: str) -> StructuralObject:
    """Semantically feedback-like but with a stabilizing rather than amplifying loop."""

    return StructuralObject(
        structure_id=structure_id,
        domain=domain,
        qoi="growth_amplification",
        context_id=f"{domain}-negative-feedback",
        roles=(
            StructuralRole(f"{prefix}_state", "state"),
            StructuralRole(f"{prefix}_response", "response"),
        ),
        relations=(
            StructuralRelation(f"{prefix}_state", "increases", f"{prefix}_response"),
            StructuralRelation(f"{prefix}_response", "decreases", f"{prefix}_state"),
        ),
        invariants=frozenset({"negative_feedback_damps_perturbations"}),
        boundaries=(BoundaryCondition("feedback_sign", "negative"),),
        evidence_ids=(f"evidence:{structure_id}",),
    )


def _cascade_structure(structure_id: str, domain: str, prefix: str) -> StructuralObject:
    return StructuralObject(
        structure_id=structure_id,
        domain=domain,
        qoi="cascade_risk",
        context_id=f"{domain}-supercritical-cascade",
        roles=(
            StructuralRole(f"{prefix}_seed", "initial_trigger"),
            StructuralRole(f"{prefix}_susceptible", "susceptible_population"),
            StructuralRole(f"{prefix}_spread", "propagation_process"),
        ),
        relations=(
            StructuralRelation(f"{prefix}_seed", "activates", f"{prefix}_spread"),
            StructuralRelation(f"{prefix}_spread", "recruits", f"{prefix}_susceptible"),
            StructuralRelation(f"{prefix}_susceptible", "feeds", f"{prefix}_spread"),
        ),
        invariants=frozenset({"supercritical_reproduction_can_create_macroscopic_cascade"}),
        boundaries=(
            BoundaryCondition("threshold_regime", "supercritical"),
            BoundaryCondition("connectivity", "sufficient"),
        ),
        evidence_ids=(f"evidence:{structure_id}",),
    )


def _subcritical_cascade_decoy(structure_id: str, domain: str, prefix: str) -> StructuralObject:
    """Semantically cascade-like but structurally subcritical and self-extinguishing."""

    return StructuralObject(
        structure_id=structure_id,
        domain=domain,
        qoi="cascade_risk",
        context_id=f"{domain}-subcritical",
        roles=(
            StructuralRole(f"{prefix}_seed", "initial_trigger"),
            StructuralRole(f"{prefix}_susceptible", "susceptible_population"),
            StructuralRole(f"{prefix}_spread", "propagation_process"),
        ),
        relations=(
            StructuralRelation(f"{prefix}_seed", "activates", f"{prefix}_spread"),
            StructuralRelation(f"{prefix}_spread", "depletes", f"{prefix}_susceptible"),
        ),
        invariants=frozenset({"subcritical_perturbations_die_out"}),
        boundaries=(
            BoundaryCondition("threshold_regime", "subcritical"),
            BoundaryCondition("connectivity", "limited"),
        ),
        evidence_ids=(f"evidence:{structure_id}",),
    )


def _queue_witness(
    witness_id: str,
    source: StructuralObject,
    target: StructuralObject,
    source_prefix: str,
    target_prefix: str,
) -> StructuralWitness:
    return StructuralWitness(
        witness_id=witness_id,
        source_structure_id=source.structure_id,
        target_structure_id=target.structure_id,
        role_mapping=(
            (f"{source_prefix}_arrival", f"{target_prefix}_arrival"),
            (f"{source_prefix}_service", f"{target_prefix}_service"),
            (f"{source_prefix}_backlog", f"{target_prefix}_backlog"),
        ),
        preserved_invariants=frozenset({"long_run_arrival_gt_service_implies_backlog_growth"}),
        non_preserved_properties=frozenset({"domain_specific_priority_rules", "entity_semantics"}),
        required_target_boundaries=(
            BoundaryCondition("flow_regime", "continual"),
            BoundaryCondition("time_scale", "matched"),
        ),
        evidence_ids=(f"witness-evidence:{witness_id}",),
    )


def _feedback_witness(
    witness_id: str,
    source: StructuralObject,
    target: StructuralObject,
    source_prefix: str,
    target_prefix: str,
) -> StructuralWitness:
    return StructuralWitness(
        witness_id=witness_id,
        source_structure_id=source.structure_id,
        target_structure_id=target.structure_id,
        role_mapping=(
            (f"{source_prefix}_state", f"{target_prefix}_state"),
            (f"{source_prefix}_response", f"{target_prefix}_response"),
        ),
        preserved_invariants=frozenset({"positive_feedback_can_amplify_perturbations"}),
        non_preserved_properties=frozenset({"domain_specific_gain", "entity_semantics"}),
        required_target_boundaries=(BoundaryCondition("feedback_sign", "positive"),),
        evidence_ids=(f"witness-evidence:{witness_id}",),
    )


def _cascade_witness(
    witness_id: str,
    source: StructuralObject,
    target: StructuralObject,
    source_prefix: str,
    target_prefix: str,
) -> StructuralWitness:
    return StructuralWitness(
        witness_id=witness_id,
        source_structure_id=source.structure_id,
        target_structure_id=target.structure_id,
        role_mapping=(
            (f"{source_prefix}_seed", f"{target_prefix}_seed"),
            (f"{source_prefix}_susceptible", f"{target_prefix}_susceptible"),
            (f"{source_prefix}_spread", f"{target_prefix}_spread"),
        ),
        preserved_invariants=frozenset({"supercritical_reproduction_can_create_macroscopic_cascade"}),
        non_preserved_properties=frozenset({"domain_specific_transmission_channel", "entity_semantics"}),
        required_target_boundaries=(
            BoundaryCondition("threshold_regime", "supercritical"),
            BoundaryCondition("connectivity", "sufficient"),
        ),
        evidence_ids=(f"witness-evidence:{witness_id}",),
    )


def make_quadrant_cases() -> tuple[StructuralBenchmarkCase, ...]:
    """Create deterministic cases that decouple surface domain similarity from structure."""

    q1_source = _queue_structure("q1-src", "network-queue", "packet")
    q1_target = _queue_structure("q1-tgt", "network-router", "frame")
    q1 = StructuralBenchmarkCase(
        case_id="q1-queue",
        family="queue",
        quadrant=SimilarityQuadrant.Q1_HIGH_SEM_HIGH_STRUCT,
        semantic_similarity_label="high",
        structural_match_expected=True,
        source=q1_source,
        target=q1_target,
        witness=_queue_witness("w-q1", q1_source, q1_target, "packet", "frame"),
    )

    q2_source = _queue_structure("q2-src", "computer-network", "packet")
    q2_target = _queue_structure("q2-tgt", "emergency-department", "patient")
    q2 = StructuralBenchmarkCase(
        case_id="q2-cross-domain-queue",
        family="queue",
        quadrant=SimilarityQuadrant.Q2_LOW_SEM_HIGH_STRUCT,
        semantic_similarity_label="low",
        structural_match_expected=True,
        source=q2_source,
        target=q2_target,
        witness=_queue_witness("w-q2", q2_source, q2_target, "packet", "patient"),
    )

    q3_source = _queue_structure("q3-src", "warehouse-queue", "order")
    q3_target = _finite_batch_queue_decoy("q3-tgt", "warehouse-queue", "job")
    q3 = StructuralBenchmarkCase(
        case_id="q3-semantic-decoy",
        family="queue",
        quadrant=SimilarityQuadrant.Q3_HIGH_SEM_LOW_STRUCT,
        semantic_similarity_label="high",
        structural_match_expected=False,
        source=q3_source,
        target=q3_target,
        witness=_queue_witness("w-q3", q3_source, q3_target, "order", "job"),
    )

    q4_source = _queue_structure("q4-src", "computer-network", "packet")
    q4_target = _feedback_structure("q4-tgt", "social-amplification", "signal")
    q4 = StructuralBenchmarkCase(
        case_id="q4-negative",
        family="queue-vs-feedback",
        quadrant=SimilarityQuadrant.Q4_LOW_SEM_LOW_STRUCT,
        semantic_similarity_label="low",
        structural_match_expected=False,
        source=q4_source,
        target=q4_target,
        witness=StructuralWitness(
            witness_id="w-q4",
            source_structure_id=q4_source.structure_id,
            target_structure_id=q4_target.structure_id,
            role_mapping=(("packet_arrival", "signal_state"), ("packet_service", "signal_response")),
            preserved_invariants=frozenset(),
            non_preserved_properties=frozenset({"queue_stability"}),
            required_target_boundaries=(),
            evidence_ids=("witness-evidence:w-q4",),
        ),
    )

    return (q1, q2, q3, q4)


def make_multifamily_cases() -> tuple[StructuralBenchmarkCase, ...]:
    """Add independent Q2/Q3 mechanism families without changing the legacy quartet.

    The extra cases are intentionally paired: each family contains a low-semantic valid
    transfer and a high-semantic invalid transfer.  This keeps the cheap mechanism test
    focused on information that semantic similarity alone cannot supply.
    """

    cases = list(make_quadrant_cases())

    feedback_source = _feedback_structure("feedback-q2-src", "viral-marketing", "adoption")
    feedback_target = _feedback_structure("feedback-q2-tgt", "bank-run", "withdrawal")
    cases.append(
        StructuralBenchmarkCase(
            case_id="q2-cross-domain-positive-feedback",
            family="positive-feedback",
            quadrant=SimilarityQuadrant.Q2_LOW_SEM_HIGH_STRUCT,
            semantic_similarity_label="low",
            structural_match_expected=True,
            source=feedback_source,
            target=feedback_target,
            witness=_feedback_witness(
                "w-feedback-q2", feedback_source, feedback_target, "adoption", "withdrawal"
            ),
        )
    )

    feedback_decoy_source = _feedback_structure("feedback-q3-src", "control-feedback", "loop")
    feedback_decoy_target = _negative_feedback_decoy("feedback-q3-tgt", "control-feedback", "regulator")
    cases.append(
        StructuralBenchmarkCase(
            case_id="q3-feedback-sign-decoy",
            family="positive-feedback",
            quadrant=SimilarityQuadrant.Q3_HIGH_SEM_LOW_STRUCT,
            semantic_similarity_label="high",
            structural_match_expected=False,
            source=feedback_decoy_source,
            target=feedback_decoy_target,
            witness=_feedback_witness(
                "w-feedback-q3", feedback_decoy_source, feedback_decoy_target, "loop", "regulator"
            ),
        )
    )

    cascade_source = _cascade_structure("cascade-q2-src", "epidemic-spread", "infection")
    cascade_target = _cascade_structure("cascade-q2-tgt", "power-grid-failure", "outage")
    cases.append(
        StructuralBenchmarkCase(
            case_id="q2-cross-domain-threshold-cascade",
            family="threshold-cascade",
            quadrant=SimilarityQuadrant.Q2_LOW_SEM_HIGH_STRUCT,
            semantic_similarity_label="low",
            structural_match_expected=True,
            source=cascade_source,
            target=cascade_target,
            witness=_cascade_witness(
                "w-cascade-q2", cascade_source, cascade_target, "infection", "outage"
            ),
        )
    )

    cascade_decoy_source = _cascade_structure("cascade-q3-src", "epidemic-cascade", "case")
    cascade_decoy_target = _subcritical_cascade_decoy(
        "cascade-q3-tgt", "epidemic-cascade", "cluster"
    )
    cases.append(
        StructuralBenchmarkCase(
            case_id="q3-subcritical-cascade-decoy",
            family="threshold-cascade",
            quadrant=SimilarityQuadrant.Q3_HIGH_SEM_LOW_STRUCT,
            semantic_similarity_label="high",
            structural_match_expected=False,
            source=cascade_decoy_source,
            target=cascade_decoy_target,
            witness=_cascade_witness(
                "w-cascade-q3", cascade_decoy_source, cascade_decoy_target, "case", "cluster"
            ),
        )
    )

    return tuple(cases)
