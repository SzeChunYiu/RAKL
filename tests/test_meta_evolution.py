from __future__ import annotations

import json
from pathlib import Path

import pytest

from rakl.evolution import EvolutionVerdict
from rakl.mechanic_diagnosis import MechanicCause
from rakl.meta_evolution import (
    CandidateDelta,
    EvolutionLayer,
    EvolutionPortrait,
    GenomeMutation,
    MethodGenome,
    MutationPolicy,
    SelfEvolutionAction,
    assess_mutation_governance,
    materialize_challenger_genome,
    pareto_frontier,
    plan_self_evolution,
    update_mutation_policy,
)


_BENCHMARK_PATH = (
    Path(__file__).resolve().parents[1]
    / "research"
    / "SELF_RAKL_RESEARCH_044_FROZEN_BENCHMARK.json"
)


def _benchmark() -> dict[str, object]:
    return json.loads(_BENCHMARK_PATH.read_text(encoding="utf-8"))


def test_frozen_routing_cases() -> None:
    benchmark = _benchmark()
    assert benchmark["status"] == "FROZEN_BEFORE_IMPLEMENTATION"
    for case in benchmark["routing_cases"]:
        causes = tuple(MechanicCause(name) for name in case["causes"])
        portrait = EvolutionPortrait(
            causes=causes,
            stagnant=bool(case["stagnant"]),
            knowledge_gain_positive=bool(case.get("knowledge_gain_positive", False)),
            same_layer_failed_generations=int(case.get("same_layer_failed_generations", 0)),
            current_topology=case.get("current_topology"),
            registered_topology_challengers=tuple(case.get("registered_topology_challengers", ())),
        )
        plan = plan_self_evolution(portrait)

        expected_action = SelfEvolutionAction(
            case.get("expected_action", SelfEvolutionAction.PROPOSE_MUTATION.value)
        )
        assert plan.action is expected_action, case["id"]
        assert [layer.value for layer in plan.target_layers] == [
            value for value in case.get("expected_contains", ()) if value in [layer.value for layer in plan.target_layers]
        ] or set(case.get("expected_contains", ())) <= {layer.value for layer in plan.target_layers}, case["id"]
        for excluded in case.get("expected_excludes", ()):
            assert excluded not in {layer.value for layer in plan.target_layers}, case["id"]
        if "expected_primary" in case:
            assert plan.primary_layer is EvolutionLayer(case["expected_primary"]), case["id"]
        if "expected_reason_contains" in case:
            assert case["expected_reason_contains"] in plan.reasons, case["id"]
        if "expected_requires_outer_assurance" in case:
            assert plan.requires_outer_assurance is case["expected_requires_outer_assurance"], case["id"]
        if "expected_incumbent_topology_protected" in case:
            assert plan.incumbent_topology_protected is case["expected_incumbent_topology_protected"], case["id"]
        assert plan.grants_scientific_authority is False
        assert plan.grants_method_promotion_authority is False


def test_frozen_pareto_cases_do_not_scalarize_tradeoffs() -> None:
    for case in _benchmark()["pareto_cases"]:
        # The frozen benchmark records the candidate key as "id"; CandidateDelta's
        # field is candidate_id. The frozen artifact stays untouched — adapt here.
        frontier = pareto_frontier(
            CandidateDelta(
                candidate_id=candidate["id"],
                **{key: value for key, value in candidate.items() if key != "id"},
            )
            for candidate in case["candidates"]
        )
        assert [candidate.candidate_id for candidate in frontier] == case["expected_frontier"], case["id"]


def test_frozen_meta_policy_credit_assignment() -> None:
    for case in _benchmark()["meta_policy_cases"]:
        policy = MutationPolicy.from_mapping(case["weights"])
        updated = update_mutation_policy(
            policy,
            operator_id=case["operator"],
            outcome=EvolutionVerdict(case["outcome"]),
        ).as_dict()
        if case["expected_relation"] == "representation_reset_gt_local_patch":
            assert updated["representation_reset"] > updated["local_patch"], case["id"]
        elif case["expected_relation"] == "representation_reset_lt_local_patch":
            assert updated["representation_reset"] < updated["local_patch"], case["id"]
        else:  # pragma: no cover - a new frozen relation must receive an explicit test rule
            raise AssertionError(f"unregistered relation: {case['expected_relation']}")


def test_frozen_governance_cases_keep_outer_authority_boundary() -> None:
    for case in _benchmark()["governance_cases"]:
        assessment = assess_mutation_governance(
            target_layer=EvolutionLayer(case["target_layer"]),
            outer_assurance_frozen=bool(case["outer_assurance_frozen"]),
        )
        if "expected_proposal_allowed" in case:
            assert assessment.proposal_allowed is case["expected_proposal_allowed"], case["id"]
        if "expected_eligible_for_auto_promotion" in case:
            assert assessment.eligible_for_auto_promotion is case["expected_eligible_for_auto_promotion"], case["id"]
        if "expected_grants_scientific_authority" in case:
            assert assessment.grants_scientific_authority is case["expected_grants_scientific_authority"], case["id"]


def test_genome_accepts_non_fractal_and_new_representation_substrates() -> None:
    parent = MethodGenome(
        version_id="parent",
        representation_id="semantic_tree_v1",
        topology_id="recursive_fractal_v1",
        mutation_language_id="typed_delta_v1",
    )
    topology_mutation = GenomeMutation(
        mutation_id="m-topology",
        operator_id="topology_synthesis",
        target_layer=EvolutionLayer.TOPOLOGY,
        replacement_id="dynamic_hypergraph_blackboard_v0",
        rationale="challenge recursive fractal lock-in",
        falsifier_ids=("held_out_topology_benchmark",),
    )
    child = materialize_challenger_genome(parent, topology_mutation, child_version_id="child-topology")
    assert child.topology_id == "dynamic_hypergraph_blackboard_v0"
    assert child.representation_id == parent.representation_id

    representation_mutation = GenomeMutation(
        mutation_id="m-representation",
        operator_id="representation_reset",
        target_layer=EvolutionLayer.REPRESENTATION,
        replacement_id="constraint_hypergraph_latent_chart_v0",
        rationale="invent a substrate where residual locality is easier to expose",
    )
    grandchild = materialize_challenger_genome(
        child,
        representation_mutation,
        child_version_id="child-representation",
    )
    assert grandchild.representation_id == "constraint_hypergraph_latent_chart_v0"
    assert grandchild.topology_id == child.topology_id


def test_mutation_language_can_mutate_but_constitution_cannot_be_ordinary_genome_edit() -> None:
    parent = MethodGenome(version_id="parent")
    language_mutation = GenomeMutation(
        mutation_id="m-language",
        operator_id="meta_operator_invention",
        target_layer=EvolutionLayer.MUTATION_LANGUAGE,
        replacement_id="program_synthesis_mutation_dsl_v2",
        rationale="expand the space of expressible self-modifications",
    )
    child = materialize_challenger_genome(parent, language_mutation, child_version_id="child")
    assert child.mutation_language_id == "program_synthesis_mutation_dsl_v2"
    assert language_mutation.grants_scientific_authority is False
    assert language_mutation.grants_method_promotion_authority is False

    with pytest.raises(ValueError, match="constitutional amendments"):
        GenomeMutation(
            mutation_id="m-constitution",
            operator_id="ordinary_mutator",
            target_layer=EvolutionLayer.CONSTITUTION,
            replacement_id="constitution_v_next",
            rationale="must go through amendment governance instead",
        )
