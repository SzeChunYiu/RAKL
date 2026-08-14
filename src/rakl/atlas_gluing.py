from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple

from .generator_transport import AbstractionLevel


class GluingLayer(str, Enum):
    SEMANTIC = "SEMANTIC"
    MATHEMATICAL = "MATHEMATICAL"
    OBSERVATIONAL = "OBSERVATIONAL"
    QOI = "QOI"
    MECHANISTIC = "MECHANISTIC"


class TransitionVerdict(str, Enum):
    VALID = "VALID"
    REJECT = "REJECT"
    CANNOT_CHECK = "CANNOT_CHECK"


class AtlasGluingVerdict(str, Enum):
    GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY = "GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY"
    PAIRWISE_COMPATIBLE_GLOBAL_UNPROVEN = "PAIRWISE_COMPATIBLE_GLOBAL_UNPROVEN"
    GLOBAL_EXISTS_UNIQUENESS_UNPROVEN = "GLOBAL_EXISTS_UNIQUENESS_UNPROVEN"
    IDENTIFIED_SET_ONLY = "IDENTIFIED_SET_ONLY"
    PARTIAL_ATLAS_ONLY = "PARTIAL_ATLAS_ONLY"
    OBSTRUCTED_ATLAS = "OBSTRUCTED_ATLAS"
    GLOBAL_PROPOSAL_REFUTED_OBSTRUCTION_HISTORY_PRESERVED = (
        "GLOBAL_PROPOSAL_REFUTED_OBSTRUCTION_HISTORY_PRESERVED"
    )
    TRIAL_INVALID = "TRIAL_INVALID"
    CANNOT_CHECK = "CANNOT_CHECK"


class ObstructionType(str, Enum):
    CHART_SCOPE_MISMATCH = "CHART_SCOPE_MISMATCH"
    CONTEXT_MISMATCH = "CONTEXT_MISMATCH"
    ASSUMPTION_CONFLICT = "ASSUMPTION_CONFLICT"
    REGIME_DISJOINT = "REGIME_DISJOINT"
    RELATION_LAYER_NOT_CERTIFIED = "RELATION_LAYER_NOT_CERTIFIED"
    TRANSITION_MAP_FAILURE = "TRANSITION_MAP_FAILURE"
    MAPPING_WITNESS_CONTRADICTION = "MAPPING_WITNESS_CONTRADICTION"
    CYCLE_OR_PATH_INCONSISTENCY = "CYCLE_OR_PATH_INCONSISTENCY"
    GLOBAL_EXISTENCE_FAILURE = "GLOBAL_EXISTENCE_FAILURE"


@dataclass(frozen=True)
class AtlasChart:
    """One local theory/projection chart of a declared atlas object."""

    chart_id: str
    atlas_object_id: str
    question_or_qoi: str
    abstraction_level: AbstractionLevel
    context_id: str
    assumptions: Tuple[str, ...]
    regime: Tuple[str, ...]
    evidence_ids: Tuple[str, ...]


@dataclass(frozen=True)
class OverlapTransition:
    """Evidence-bearing transition map on one declared chart overlap."""

    transition_id: str
    source_chart_id: str
    target_chart_id: str
    overlap_id: str
    mapping_pairs: Tuple[Tuple[str, str], ...]
    preserved: Tuple[str, ...]
    not_preserved: Tuple[str, ...]
    certified_layers: Tuple[GluingLayer, ...]
    context_alignment_passed: Optional[bool]
    assumption_compatibility_passed: Optional[bool]
    regime_overlap: Tuple[str, ...]
    transition_map_passed: Optional[bool]
    evidence_ids: Tuple[str, ...]
    declared_before_outcomes: Optional[bool]


@dataclass(frozen=True)
class CycleConsistencyWitness:
    """Composition/holonomy check for a registered fundamental cycle."""

    cycle_id: str
    chart_path: Tuple[str, ...]
    composition_consistent: Optional[bool]
    evidence_ids: Tuple[str, ...]


@dataclass(frozen=True)
class GluingObstructionCertificate:
    obstruction: ObstructionType
    location_ids: Tuple[str, ...]
    detail: str
    evidence_ids: Tuple[str, ...]


@dataclass(frozen=True)
class TransitionReport:
    verdict: TransitionVerdict
    reasons: Tuple[str, ...]
    obstructions: Tuple[GluingObstructionCertificate, ...] = ()


@dataclass(frozen=True)
class AtlasGluingTrial:
    """Frozen local-to-global synthesis trial for one object/QoI/layer."""

    trial_id: str
    atlas_object_id: str
    question_or_qoi: str
    abstraction_level: AbstractionLevel
    requested_layer: GluingLayer
    charts: Tuple[AtlasChart, ...]
    transitions: Tuple[OverlapTransition, ...]
    cover_connected: Optional[bool]
    cover_has_cycles: Optional[bool]
    cycle_basis_complete: Optional[bool]
    cycle_witnesses: Tuple[CycleConsistencyWitness, ...]
    global_existence_checked: Optional[bool]
    global_exists: Optional[bool]
    uniqueness_checked: Optional[bool]
    unique_global: Optional[bool]
    hidden_labels_exposed: Optional[bool]
    transition_family_frozen_before_outcomes: Optional[bool]
    target_tested: bool = False
    target_passed: Optional[bool] = None


@dataclass(frozen=True)
class AtlasGluingReport:
    verdict: AtlasGluingVerdict
    reasons: Tuple[str, ...]
    obstructions: Tuple[GluingObstructionCertificate, ...]
    transition_reports: Tuple[TransitionReport, ...]

    @property
    def activates_canonical_knowledge(self) -> bool:
        return False

    @property
    def establishes_mechanism_beyond_requested_layer(self) -> bool:
        return False


def _obstruction(
    kind: ObstructionType,
    location_ids: Tuple[str, ...],
    detail: str,
    evidence_ids: Tuple[str, ...] = (),
) -> GluingObstructionCertificate:
    return GluingObstructionCertificate(kind, location_ids, detail, evidence_ids)


def validate_overlap_transition(
    transition: OverlapTransition,
    *,
    requested_layer: GluingLayer,
    chart_ids: Tuple[str, ...],
) -> TransitionReport:
    missing: list[str] = []
    for name, value in (
        ("transition_id", transition.transition_id),
        ("source_chart_id", transition.source_chart_id),
        ("target_chart_id", transition.target_chart_id),
        ("overlap_id", transition.overlap_id),
    ):
        if not value:
            missing.append(f"{name}_missing")
    if not transition.mapping_pairs:
        missing.append("mapping_pairs_missing")
    if not transition.preserved:
        missing.append("preserved_structure_missing")
    if not transition.certified_layers:
        missing.append("certified_layers_missing")
    if not transition.evidence_ids:
        missing.append("transition_evidence_missing")

    if missing:
        return TransitionReport(TransitionVerdict.CANNOT_CHECK, tuple(missing))

    if transition.source_chart_id not in chart_ids or transition.target_chart_id not in chart_ids:
        return TransitionReport(
            TransitionVerdict.REJECT,
            ("transition_references_unknown_chart",),
            (
                _obstruction(
                    ObstructionType.CHART_SCOPE_MISMATCH,
                    (transition.transition_id,),
                    "transition endpoint is outside the declared atlas chart set",
                    transition.evidence_ids,
                ),
            ),
        )
    if transition.source_chart_id == transition.target_chart_id:
        return TransitionReport(
            TransitionVerdict.REJECT,
            ("self_transition_not_an_overlap_witness",),
        )

    if transition.declared_before_outcomes is None:
        return TransitionReport(
            TransitionVerdict.CANNOT_CHECK,
            ("transition_freeze_chronology_unknown",),
        )
    if transition.declared_before_outcomes is False:
        return TransitionReport(
            TransitionVerdict.REJECT,
            ("posthoc_transition_map_definition",),
        )

    contradictory = set(transition.preserved).intersection(transition.not_preserved)
    if contradictory:
        return TransitionReport(
            TransitionVerdict.REJECT,
            ("mapping_witness_self_contradiction",),
            (
                _obstruction(
                    ObstructionType.MAPPING_WITNESS_CONTRADICTION,
                    (transition.transition_id,),
                    "same overlap feature marked PRESERVED and NOT_PRESERVED",
                    transition.evidence_ids,
                ),
            ),
        )

    if any(not source or not target for source, target in transition.mapping_pairs):
        return TransitionReport(TransitionVerdict.REJECT, ("empty_mapping_role",))

    if requested_layer not in transition.certified_layers:
        return TransitionReport(
            TransitionVerdict.REJECT,
            ("requested_gluing_layer_not_certified",),
            (
                _obstruction(
                    ObstructionType.RELATION_LAYER_NOT_CERTIFIED,
                    (transition.transition_id,),
                    f"overlap is not certified at requested layer {requested_layer.value}",
                    transition.evidence_ids,
                ),
            ),
        )

    for field_name, value in (
        ("context_alignment", transition.context_alignment_passed),
        ("assumption_compatibility", transition.assumption_compatibility_passed),
        ("transition_map", transition.transition_map_passed),
    ):
        if value is None:
            return TransitionReport(
                TransitionVerdict.CANNOT_CHECK,
                (f"{field_name}_status_unknown",),
            )

    if transition.context_alignment_passed is False:
        return TransitionReport(
            TransitionVerdict.REJECT,
            ("context_alignment_failed",),
            (
                _obstruction(
                    ObstructionType.CONTEXT_MISMATCH,
                    (transition.transition_id, transition.overlap_id),
                    "population/scale/observation/context alignment failed",
                    transition.evidence_ids,
                ),
            ),
        )
    if transition.assumption_compatibility_passed is False:
        return TransitionReport(
            TransitionVerdict.REJECT,
            ("assumption_compatibility_failed",),
            (
                _obstruction(
                    ObstructionType.ASSUMPTION_CONFLICT,
                    (transition.transition_id, transition.overlap_id),
                    "overlap assumptions are incompatible",
                    transition.evidence_ids,
                ),
            ),
        )
    if not transition.regime_overlap:
        return TransitionReport(
            TransitionVerdict.REJECT,
            ("no_overlap_validity_regime",),
            (
                _obstruction(
                    ObstructionType.REGIME_DISJOINT,
                    (transition.transition_id, transition.overlap_id),
                    "mapped claims have no overlapping validity regime",
                    transition.evidence_ids,
                ),
            ),
        )
    if transition.transition_map_passed is False:
        return TransitionReport(
            TransitionVerdict.REJECT,
            ("transition_map_failed_on_overlap",),
            (
                _obstruction(
                    ObstructionType.TRANSITION_MAP_FAILURE,
                    (transition.transition_id, transition.overlap_id),
                    "restricted local values/relations disagree under the declared map",
                    transition.evidence_ids,
                ),
            ),
        )

    return TransitionReport(
        TransitionVerdict.VALID,
        (
            "overlap_mapping_present",
            "requested_relation_layer_certified",
            "context_and_assumptions_compatible",
            "validity_regime_overlaps",
            "transition_map_passed",
            "preserved_and_not_preserved_explicit",
        ),
    )


@dataclass(frozen=True)
class _CoverTopology:
    """Topology facts recomputed from the validated transition set.

    The declared cover graph has the charts as vertices and one edge per
    distinct (unordered chart pair, overlap_id). Two transitions witnessing the
    same overlap in opposite directions are one edge; distinct overlaps between
    the same chart pair are parallel edges.
    """

    connected: bool
    independent_cycle_count: int
    undirected_edges: frozenset[frozenset[str]]
    has_parallel_overlap_edges: bool


def _recompute_cover_topology(
    chart_ids: Tuple[str, ...],
    transitions: Tuple[OverlapTransition, ...],
) -> _CoverTopology:
    vertices = set(chart_ids)
    overlap_edges: set[Tuple[frozenset[str], str]] = set()
    undirected_edges: set[frozenset[str]] = set()
    adjacency: dict[str, set[str]] = {chart_id: set() for chart_id in vertices}
    for transition in transitions:
        pair = frozenset((transition.source_chart_id, transition.target_chart_id))
        overlap_edges.add((pair, transition.overlap_id))
        undirected_edges.add(pair)
        adjacency[transition.source_chart_id].add(transition.target_chart_id)
        adjacency[transition.target_chart_id].add(transition.source_chart_id)

    components = 0
    seen: set[str] = set()
    for vertex in sorted(vertices):
        if vertex in seen:
            continue
        components += 1
        stack = [vertex]
        seen.add(vertex)
        while stack:
            current = stack.pop()
            for neighbour in adjacency[current]:
                if neighbour not in seen:
                    seen.add(neighbour)
                    stack.append(neighbour)

    return _CoverTopology(
        connected=components == 1,
        independent_cycle_count=len(overlap_edges) - len(vertices) + components,
        undirected_edges=frozenset(undirected_edges),
        has_parallel_overlap_edges=len(overlap_edges) > len(undirected_edges),
    )


def _witness_path_in_transition_graph(
    witness: CycleConsistencyWitness,
    chart_ids: Tuple[str, ...],
    undirected_edges: frozenset[frozenset[str]],
) -> bool:
    path = witness.chart_path
    if path[0] != path[-1]:
        return False
    if any(chart_id not in chart_ids for chart_id in path):
        return False
    for source, target in zip(path, path[1:]):
        if source == target or frozenset((source, target)) not in undirected_edges:
            return False
    return True


def _witness_cycle_space_rank(
    witnesses: Tuple[CycleConsistencyWitness, ...],
    undirected_edges: frozenset[frozenset[str]],
) -> int:
    """GF(2) rank of the witness cycles in the cover graph's cycle space.

    Only meaningful when the cover graph has no parallel overlap edges, because
    a chart path cannot disambiguate which of two parallel overlaps it uses.
    """

    edge_index = {
        edge: index
        for index, edge in enumerate(
            sorted(tuple(sorted(edge)) for edge in undirected_edges)
        )
    }
    basis: dict[int, int] = {}
    for witness in witnesses:
        vector = 0
        for source, target in zip(witness.chart_path, witness.chart_path[1:]):
            vector ^= 1 << edge_index[tuple(sorted((source, target)))]
        while vector:
            leading_bit = vector.bit_length() - 1
            if leading_bit in basis:
                vector ^= basis[leading_bit]
            else:
                basis[leading_bit] = vector
                break
    return len(basis)


def _declared_topology_mismatch_report(
    mismatched_fields: Tuple[str, ...],
    transition_reports: Tuple[TransitionReport, ...],
) -> AtlasGluingReport:
    return AtlasGluingReport(
        AtlasGluingVerdict.CANNOT_CHECK,
        tuple(f"declared_topology_mismatch:{field}" for field in mismatched_fields),
        (),
        transition_reports,
    )


def evaluate_atlas_gluing(trial: AtlasGluingTrial) -> AtlasGluingReport:
    """Fail-closed local-to-global synthesis diagnostic.

    Pairwise compatibility is never promoted to a global scientific object by
    itself. A global portrait requires explicit global-existence and uniqueness
    evidence in addition to overlap/cycle checks. The result remains proposal-only.

    Declared topology coordinates (cover connectivity, cycle existence, cycle
    basis completeness, cycle witnesses) are never trusted blindly: they are
    recomputed from the validated transition set, and a declaration refuted by
    recomputation yields ``CANNOT_CHECK`` with a typed
    ``declared_topology_mismatch:<field>`` reason. Recomputation can refute an
    optimistic declaration but cannot verify semantic sufficiency, so a
    pessimistic declaration (e.g. ``cover_connected=False`` on a syntactically
    connected graph) keeps its fail-closed verdict. A coordinate that cannot be
    recomputed from the available inputs is marked
    ``declared_topology_untrusted:<field>`` instead of being assumed true.
    """

    empty_report = AtlasGluingReport

    if trial.hidden_labels_exposed is None:
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("hidden_label_exposure_status_unknown",),
            (),
            (),
        )
    if trial.hidden_labels_exposed:
        return empty_report(
            AtlasGluingVerdict.TRIAL_INVALID,
            ("hidden_global_identity_or_benchmark_labels_exposed",),
            (),
            (),
        )
    if trial.transition_family_frozen_before_outcomes is None:
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("transition_family_freeze_chronology_unknown",),
            (),
            (),
        )
    if trial.transition_family_frozen_before_outcomes is False:
        return empty_report(
            AtlasGluingVerdict.TRIAL_INVALID,
            ("posthoc_transition_family_or_overlap_predicate_adaptation",),
            (),
            (),
        )

    if not trial.trial_id or not trial.atlas_object_id or not trial.question_or_qoi:
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("trial_identity_or_qoi_missing",),
            (),
            (),
        )
    if len(trial.charts) < 2:
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("at_least_two_charts_required",),
            (),
            (),
        )

    chart_ids = tuple(chart.chart_id for chart in trial.charts)
    if any(not chart_id for chart_id in chart_ids) or len(set(chart_ids)) != len(chart_ids):
        return empty_report(
            AtlasGluingVerdict.TRIAL_INVALID,
            ("chart_identity_missing_or_duplicated",),
            (),
            (),
        )

    chart_obstructions: list[GluingObstructionCertificate] = []
    for chart in trial.charts:
        if not chart.evidence_ids or not chart.context_id or not chart.regime:
            return empty_report(
                AtlasGluingVerdict.CANNOT_CHECK,
                (f"chart_contract_incomplete:{chart.chart_id}",),
                (),
                (),
            )
        mismatches: list[str] = []
        if chart.atlas_object_id != trial.atlas_object_id:
            mismatches.append("atlas_object")
        if chart.question_or_qoi != trial.question_or_qoi:
            mismatches.append("question_or_qoi")
        if chart.abstraction_level != trial.abstraction_level:
            mismatches.append("abstraction_level")
        if mismatches:
            chart_obstructions.append(
                _obstruction(
                    ObstructionType.CHART_SCOPE_MISMATCH,
                    (chart.chart_id,),
                    "chart mismatch: " + ",".join(mismatches),
                    chart.evidence_ids,
                )
            )

    if chart_obstructions:
        return empty_report(
            AtlasGluingVerdict.OBSTRUCTED_ATLAS,
            ("one_or_more_charts_do_not_describe_the_declared_atlas_scope",),
            tuple(chart_obstructions),
            (),
        )

    if not trial.transitions:
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("overlap_transitions_missing",),
            (),
            (),
        )

    transition_reports = tuple(
        validate_overlap_transition(
            transition,
            requested_layer=trial.requested_layer,
            chart_ids=chart_ids,
        )
        for transition in trial.transitions
    )
    if any(report.verdict is TransitionVerdict.CANNOT_CHECK for report in transition_reports):
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("one_or_more_overlap_transitions_incomplete",),
            tuple(
                obstruction
                for report in transition_reports
                for obstruction in report.obstructions
            ),
            transition_reports,
        )
    rejected = tuple(
        obstruction
        for report in transition_reports
        if report.verdict is TransitionVerdict.REJECT
        for obstruction in report.obstructions
    )
    if any(report.verdict is TransitionVerdict.REJECT for report in transition_reports):
        return empty_report(
            AtlasGluingVerdict.OBSTRUCTED_ATLAS,
            ("one_or_more_overlap_transitions_rejected",),
            rejected,
            transition_reports,
        )

    topology = _recompute_cover_topology(chart_ids, trial.transitions)
    declared_topology_mismatches: list[str] = []

    if trial.cover_connected is None:
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("cover_connectivity_unknown",),
            (),
            transition_reports,
        )
    if trial.cover_connected is False:
        return empty_report(
            AtlasGluingVerdict.PARTIAL_ATLAS_ONLY,
            ("compatible_components_lack_a_witnessed_global_bridge",),
            (),
            transition_reports,
        )
    if not topology.connected:
        declared_topology_mismatches.append("cover_connected")

    if trial.cover_has_cycles is None:
        if declared_topology_mismatches:
            return _declared_topology_mismatch_report(
                tuple(declared_topology_mismatches), transition_reports
            )
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("cover_cycle_structure_unknown",),
            (),
            transition_reports,
        )
    if bool(trial.cover_has_cycles) != (topology.independent_cycle_count > 0):
        declared_topology_mismatches.append("cover_has_cycles")
    if declared_topology_mismatches:
        return _declared_topology_mismatch_report(
            tuple(declared_topology_mismatches), transition_reports
        )

    if trial.cover_has_cycles:
        if trial.cycle_basis_complete is None:
            return empty_report(
                AtlasGluingVerdict.CANNOT_CHECK,
                ("cycle_basis_completeness_unknown",),
                (),
                transition_reports,
            )
        if trial.cycle_basis_complete is False or not trial.cycle_witnesses:
            return empty_report(
                AtlasGluingVerdict.CANNOT_CHECK,
                ("cyclic_cover_without_complete_cycle_basis_checks",),
                (),
                transition_reports,
            )
        for witness in trial.cycle_witnesses:
            if not witness.cycle_id or len(witness.chart_path) < 3 or not witness.evidence_ids:
                return empty_report(
                    AtlasGluingVerdict.CANNOT_CHECK,
                    ("cycle_witness_incomplete",),
                    (),
                    transition_reports,
                )
            if not _witness_path_in_transition_graph(
                witness, chart_ids, topology.undirected_edges
            ):
                return empty_report(
                    AtlasGluingVerdict.CANNOT_CHECK,
                    (
                        "declared_topology_mismatch:cycle_witnesses",
                        "cycle_witness_path_not_in_declared_transition_graph:"
                        + witness.cycle_id,
                    ),
                    (),
                    transition_reports,
                )
            if witness.composition_consistent is None:
                return empty_report(
                    AtlasGluingVerdict.CANNOT_CHECK,
                    (f"cycle_consistency_unknown:{witness.cycle_id}",),
                    (),
                    transition_reports,
                )
            if witness.composition_consistent is False:
                obstruction = _obstruction(
                    ObstructionType.CYCLE_OR_PATH_INCONSISTENCY,
                    (witness.cycle_id, *witness.chart_path),
                    "transition composition is path-dependent/inconsistent around a registered cycle",
                    witness.evidence_ids,
                )
                return empty_report(
                    AtlasGluingVerdict.OBSTRUCTED_ATLAS,
                    ("pairwise_compatibility_does_not_survive_cycle_composition",),
                    (obstruction,),
                    transition_reports,
                )

        if topology.has_parallel_overlap_edges:
            return empty_report(
                AtlasGluingVerdict.CANNOT_CHECK,
                (
                    "declared_topology_untrusted:cycle_basis_complete",
                    "parallel_overlap_edges_make_cycle_basis_completeness"
                    "_unrecomputable_from_chart_paths",
                ),
                (),
                transition_reports,
            )
        witness_rank = _witness_cycle_space_rank(
            trial.cycle_witnesses, topology.undirected_edges
        )
        if witness_rank < topology.independent_cycle_count:
            return empty_report(
                AtlasGluingVerdict.CANNOT_CHECK,
                ("declared_topology_mismatch:cycle_basis_complete",),
                (),
                transition_reports,
            )

    if trial.global_existence_checked is None:
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("global_existence_check_status_unknown",),
            (),
            transition_reports,
        )
    if trial.global_existence_checked is False:
        return empty_report(
            AtlasGluingVerdict.PAIRWISE_COMPATIBLE_GLOBAL_UNPROVEN,
            (
                "local_overlap_checks_passed",
                "global_existence_not_established",
                "no_local_to_global_theorem_assumed_for_arbitrary_scientific_charts",
            ),
            (),
            transition_reports,
        )
    if trial.global_exists is None:
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("global_existence_outcome_unknown",),
            (),
            transition_reports,
        )
    if trial.global_exists is False:
        obstruction = _obstruction(
            ObstructionType.GLOBAL_EXISTENCE_FAILURE,
            (trial.trial_id,),
            "explicit global candidate/existence test failed despite accepted local checks",
        )
        return empty_report(
            AtlasGluingVerdict.OBSTRUCTED_ATLAS,
            ("global_section_or_consistent_global_candidate_not_found",),
            (obstruction,),
            transition_reports,
        )

    if trial.uniqueness_checked is None:
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("global_uniqueness_check_status_unknown",),
            (),
            transition_reports,
        )
    if trial.uniqueness_checked is False:
        return empty_report(
            AtlasGluingVerdict.GLOBAL_EXISTS_UNIQUENESS_UNPROVEN,
            ("global_candidate_exists_but_identifiability_or_uniqueness_unchecked",),
            (),
            transition_reports,
        )
    if trial.unique_global is None:
        return empty_report(
            AtlasGluingVerdict.CANNOT_CHECK,
            ("global_uniqueness_outcome_unknown",),
            (),
            transition_reports,
        )
    if trial.unique_global is False:
        return empty_report(
            AtlasGluingVerdict.IDENTIFIED_SET_ONLY,
            (
                "multiple_global_states_fit_the_same_compatible_local_charts",
                "retain_identified_set_instead_of_forcing_one_global_theory",
            ),
            (),
            transition_reports,
        )

    if trial.target_tested:
        if trial.target_passed is None:
            return empty_report(
                AtlasGluingVerdict.CANNOT_CHECK,
                ("target_test_outcome_unknown",),
                (),
                transition_reports,
            )
        if trial.target_passed is False:
            return empty_report(
                AtlasGluingVerdict.GLOBAL_PROPOSAL_REFUTED_OBSTRUCTION_HISTORY_PRESERVED,
                (
                    "global_gluing_witness_was_coherent",
                    "native_target_test_refuted_the_synthesized_proposal",
                    "gluing_and_refutation_history_both_preserved",
                ),
                (),
                transition_reports,
            )

    return empty_report(
        AtlasGluingVerdict.GLUED_GLOBAL_PORTRAIT_PROPOSAL_ONLY,
        (
            "all_declared_overlap_transitions_passed",
            "cycle_or_path_consistency_passed_when_required",
            "global_candidate_exists_and_is_unique_for_the_declared_scope",
            "ordinary_evidence_promotion_still_required",
        ),
        (),
        transition_reports,
    )
