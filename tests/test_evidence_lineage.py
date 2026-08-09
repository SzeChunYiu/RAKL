from dataclasses import FrozenInstanceError

import pytest

from rakl.evidence_lineage import (
    EvidenceLineageGraph,
    EvidenceLineageNode,
    GeneratorLineageVerdict,
    LineageVerdict,
    assess_evidence_lineage,
    assess_generator_family_with_lineage,
)
from rakl.generator_transport import (
    AbstractionLevel,
    EvidenceScope,
    GeneratorFamilyCandidate,
    GeneratorLift,
)


def _node(
    evidence_id: str,
    *,
    parents: tuple[str, ...] = (),
    alternates: tuple[str, ...] = (),
    specializations: tuple[str, ...] = (),
    complete: bool | None = True,
) -> EvidenceLineageNode:
    return EvidenceLineageNode(
        evidence_id=evidence_id,
        parent_ids=parents,
        alternate_of_ids=alternates,
        specialization_of_ids=specializations,
        ancestry_complete=complete,
    )


def _graph(*nodes: EvidenceLineageNode, declared: bool | None = True) -> EvidenceLineageGraph:
    return EvidenceLineageGraph(
        graph_id="lineage-graph-029",
        nodes=tuple(nodes),
        declared_before_outcomes=declared,
    )


def _lift(
    instance_id: str,
    evidence_id: str,
    lineage_id: str,
    environment_id: str,
) -> GeneratorLift:
    return GeneratorLift(
        instance_id=instance_id,
        instance_domain=f"{instance_id}-science",
        generator_id="ripening-generator",
        question_or_qoi="what controls the state transition?",
        abstraction_level=AbstractionLevel.L3,
        evidence_scope=EvidenceScope.GENERATOR,
        mapping_pairs=(("driver", "generator_driver"),),
        preserved=("state_transition", "feedback"),
        not_preserved=("species_specific_substrate",),
        erased=("species_name",),
        instance_specific=("cultivar",),
        regime=("climacteric",),
        evidence_ids=(evidence_id,),
        evidence_lineage_ids=(lineage_id,),
        environment_id=environment_id,
        intervention_or_query_ids=("intervention-ethylene",),
        commutation_passed=True,
        declared_before_outcomes=True,
    )


def _candidate() -> GeneratorFamilyCandidate:
    return GeneratorFamilyCandidate(
        candidate_id="candidate-029",
        generator_id="ripening-generator",
        question_or_qoi="what controls the state transition?",
        abstraction_level=AbstractionLevel.L3,
        required_core_features=("state_transition", "feedback"),
        lifts=(
            _lift("apple", "paper-apple", "flat-lineage-A", "env-A"),
            _lift("banana", "paper-banana", "flat-lineage-B", "env-B"),
        ),
        declared_before_outcomes=True,
        hidden_labels_exposed=False,
    )


def test_nodes_are_immutable():
    node = _node("paper-a")
    with pytest.raises(FrozenInstanceError):
        node.evidence_id = "changed"  # type: ignore[misc]


def test_shared_direct_parent_is_correlated():
    graph = _graph(
        _node("dataset"),
        _node("paper-a", parents=("dataset",)),
        _node("paper-b", parents=("dataset",)),
    )
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b"))
    assert report.verdict is LineageVerdict.CORRELATED_SUPPORT_ONLY
    assert "dataset" in report.shared_ancestor_ids


def test_shared_remote_root_is_correlated():
    graph = _graph(
        _node("registry"),
        _node("extract-a", parents=("registry",)),
        _node("extract-b", parents=("registry",)),
        _node("paper-a", parents=("extract-a",)),
        _node("paper-b", parents=("extract-b",)),
    )
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b"))
    assert report.verdict is LineageVerdict.CORRELATED_SUPPORT_ONLY
    assert "registry" in report.shared_ancestor_ids


def test_disjoint_complete_roots_are_only_no_known_shared_ancestry():
    graph = _graph(_node("paper-a"), _node("paper-b"))
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b"))
    assert report.verdict is LineageVerdict.NO_KNOWN_SHARED_ANCESTRY
    assert report.establishes_statistical_independence is False
    assert report.statistical_effective_n is None
    assert report.grants_scientific_authority is False
    assert "no_known_shared_ancestry_is_not_statistical_or_epistemic_independence" in report.reasons


def test_unknown_ancestry_fails_closed():
    graph = _graph(_node("paper-a", complete=False), _node("paper-b"))
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b"))
    assert report.verdict is LineageVerdict.CANNOT_CHECK
    assert report.unknown_ancestry_ids == ("paper-a",)


def test_unknown_ancestor_propagates_to_descendant():
    graph = _graph(
        _node("unknown-root", complete=None),
        _node("paper-a", parents=("unknown-root",)),
        _node("paper-b"),
    )
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b"))
    assert report.verdict is LineageVerdict.CANNOT_CHECK
    assert "paper-a" in report.unknown_ancestry_ids


def test_dangling_parent_fails_closed():
    graph = _graph(_node("paper-a", parents=("missing-dataset",)), _node("paper-b"))
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b"))
    assert report.verdict is LineageVerdict.CANNOT_CHECK
    assert "dangling_parent_reference:missing-dataset" in report.reasons


def test_dangling_alternate_fails_closed():
    graph = _graph(_node("paper-a", alternates=("missing-id",)), _node("paper-b"))
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b"))
    assert report.verdict is LineageVerdict.CANNOT_CHECK
    assert "dangling_alternate_reference:missing-id" in report.reasons


def test_derivation_cycle_invalidates_trial():
    graph = _graph(
        _node("paper-a", parents=("paper-b",)),
        _node("paper-b", parents=("paper-a",)),
    )
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b"))
    assert report.verdict is LineageVerdict.TRIAL_INVALID
    assert "lineage_derivation_cycle" in report.reasons


def test_alternate_ids_collapse_to_same_evidence_entity():
    graph = _graph(
        _node("paper-a", alternates=("paper-a-copy",)),
        _node("paper-a-copy", alternates=("paper-a",)),
    )
    report = assess_evidence_lineage(graph, ("paper-a", "paper-a-copy"))
    assert report.verdict is LineageVerdict.CORRELATED_SUPPORT_ONLY
    assert report.provenance_component_count == 1


def test_specializations_share_common_source():
    graph = _graph(
        _node("registry-release"),
        _node("paper-a", specializations=("registry-release",)),
        _node("paper-b", specializations=("registry-release",)),
    )
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b"))
    assert report.verdict is LineageVerdict.CORRELATED_SUPPORT_ONLY
    assert "registry-release" in report.shared_ancestor_ids


def test_mixed_shared_and_unique_roots_remains_correlated():
    graph = _graph(
        _node("shared-root"),
        _node("unique-a"),
        _node("unique-b"),
        _node("paper-a", parents=("shared-root", "unique-a")),
        _node("paper-b", parents=("shared-root", "unique-b")),
    )
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b"))
    assert report.verdict is LineageVerdict.CORRELATED_SUPPORT_ONLY
    assert "shared-root" in report.shared_ancestor_ids


def test_three_items_form_two_provenance_components():
    graph = _graph(
        _node("shared-root"),
        _node("paper-a", parents=("shared-root",)),
        _node("paper-b", parents=("shared-root",)),
        _node("paper-c"),
    )
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b", "paper-c"))
    assert report.provenance_component_count == 2
    assert report.verdict is LineageVerdict.CORRELATED_SUPPORT_ONLY


def test_duplicate_evidence_ids_invalid_even_when_objects_differ():
    graph = _graph(_node("paper-a"), _node("paper-a", parents=()))
    report = assess_evidence_lineage(graph, ("paper-a",))
    assert report.verdict is LineageVerdict.TRIAL_INVALID
    assert "duplicate_evidence_id:paper-a" in report.reasons


def test_empty_selection_is_cannot_check():
    report = assess_evidence_lineage(_graph(_node("paper-a")), ())
    assert report.verdict is LineageVerdict.CANNOT_CHECK
    assert report.reasons == ("selected_evidence_missing",)


def test_unregistered_selected_item_is_cannot_check():
    report = assess_evidence_lineage(_graph(_node("paper-a")), ("paper-a", "paper-b"))
    assert report.verdict is LineageVerdict.CANNOT_CHECK
    assert "selected_evidence_unregistered:paper-b" in report.reasons


def test_posthoc_graph_invalidates_trial():
    report = assess_evidence_lineage(
        _graph(_node("paper-a"), _node("paper-b"), declared=False),
        ("paper-a", "paper-b"),
    )
    assert report.verdict is LineageVerdict.TRIAL_INVALID


def test_graph_and_selection_order_do_not_change_report():
    nodes = (
        _node("root"),
        _node("paper-a", parents=("root",)),
        _node("paper-b", parents=("root",)),
        _node("paper-c"),
    )
    first = assess_evidence_lineage(_graph(*nodes), ("paper-a", "paper-b", "paper-c"))
    second = assess_evidence_lineage(
        _graph(*tuple(reversed(nodes))),
        ("paper-c", "paper-b", "paper-a"),
    )
    assert first == second


def test_generator_flat_lineage_ids_are_downgraded_by_shared_graph_root():
    graph = _graph(
        _node("shared-dataset"),
        _node("paper-apple", parents=("shared-dataset",)),
        _node("paper-banana", parents=("shared-dataset",)),
    )
    report = assess_generator_family_with_lineage(_candidate(), graph)
    assert report.verdict is GeneratorLineageVerdict.CORRELATED_SUPPORT_ONLY
    assert report.grants_target_authority is False
    assert report.activates_canonical_knowledge is False
    assert report.lineage_report is not None
    assert report.lineage_report.verdict is LineageVerdict.CORRELATED_SUPPORT_ONLY


def test_generator_unknown_ancestry_fails_closed():
    graph = _graph(
        _node("paper-apple", complete=False),
        _node("paper-banana"),
    )
    report = assess_generator_family_with_lineage(_candidate(), graph)
    assert report.verdict is GeneratorLineageVerdict.CANNOT_CHECK


def test_generator_disjoint_provenance_retains_proposal_without_authority():
    graph = _graph(_node("paper-apple"), _node("paper-banana"))
    report = assess_generator_family_with_lineage(_candidate(), graph)
    assert report.verdict is GeneratorLineageVerdict.CORROBORATED_PROPOSAL_ONLY
    assert report.grants_target_authority is False
    assert report.activates_canonical_knowledge is False
    assert report.lineage_report is not None
    assert report.lineage_report.establishes_statistical_independence is False


def test_lineage_graph_never_invents_numeric_effective_n():
    graph = _graph(_node("paper-a"), _node("paper-b"), _node("paper-c"))
    report = assess_evidence_lineage(graph, ("paper-a", "paper-b", "paper-c"))
    assert report.provenance_component_count == 3
    assert report.statistical_effective_n is None
