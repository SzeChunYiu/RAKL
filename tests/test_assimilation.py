from dataclasses import replace
import json
from pathlib import Path

import pytest

from rakl.assimilation import (
    AssimilationEvidence,
    AssimilationVerdict,
    MethodOperatorContract,
    evaluate_method_assimilation,
)


def base_contract() -> MethodOperatorContract:
    return MethodOperatorContract(
        component_id="external.claim_evidence_linker",
        source_framework="ExampleFramework",
        source_version="abc123",
        target_fiber="claim_extraction",
        input_schema=("claim", "source"),
        output_schema=("evidence_packet",),
        context_scope=("scientific_text",),
        assumptions=("source_text_available",),
        provenance_ids=("paper:primary",),
        may_mint=frozenset({"SOURCE_LINKED"}),
        must_not_mint=frozenset({"MECHANISM_IDENTIFIED"}),
        transition_map_id="tm:claim-evidence:v1",
        failure_modes=("span_misalignment",),
        dependency_ids=("parser:v1",),
        benchmark_id="bench:claim-evidence:v1",
    )


def base_evidence() -> AssimilationEvidence:
    return AssimilationEvidence(
        provenance_verified=True,
        transition_verified=True,
        authority_scope_verified=True,
        frozen_benchmark_registered=True,
        assumptions_declared=True,
        context_scope_declared=True,
        external_observation=True,
        equivalent_to_incumbent=False,
        compatible_with_incumbent=True,
        negative_history_match=False,
        requested_authorities=frozenset({"SOURCE_LINKED"}),
    )


def verdict(contract=None, evidence=None):
    report = evaluate_method_assimilation(
        contract or base_contract(), evidence or base_evidence()
    )
    assert report.activates_method is False
    return report.verdict


def test_clean_candidate_is_only_shadow_eligible():
    assert verdict() is AssimilationVerdict.ELIGIBLE_FOR_SHADOW


def test_self_contradictory_authority_contract_is_rejected():
    contract = replace(
        base_contract(),
        may_mint=frozenset({"SOURCE_LINKED", "MECHANISM_IDENTIFIED"}),
    )
    assert verdict(contract=contract) is AssimilationVerdict.REJECT


def test_requested_authority_outside_envelope_is_rejected():
    evidence = replace(
        base_evidence(),
        requested_authorities=frozenset({"SOURCE_LINKED", "DECISION_USABLE"}),
    )
    assert verdict(evidence=evidence) is AssimilationVerdict.REJECT


@pytest.mark.parametrize(
    "field",
    [
        "provenance_verified",
        "authority_scope_verified",
        "context_scope_declared",
        "equivalent_to_incumbent",
    ],
)
def test_unknown_required_or_comparison_evidence_cannot_check(field):
    evidence = replace(base_evidence(), **{field: None})
    assert verdict(evidence=evidence) is AssimilationVerdict.CANNOT_CHECK


def test_candidate_self_report_is_not_external_evidence():
    evidence = replace(base_evidence(), external_observation=False)
    assert verdict(evidence=evidence) is AssimilationVerdict.CANNOT_CHECK


def test_missing_transition_map_cannot_check():
    contract = replace(base_contract(), transition_map_id=None)
    assert verdict(contract=contract) is AssimilationVerdict.CANNOT_CHECK


@pytest.mark.parametrize(
    "field",
    [
        "transition_verified",
        "frozen_benchmark_registered",
        "assumptions_declared",
    ],
)
def test_known_failed_gate_blocks_shadow_eligibility(field):
    evidence = replace(base_evidence(), **{field: False})
    assert verdict(evidence=evidence) is AssimilationVerdict.BLOCK


def test_semantic_equivalent_deduplicates_instead_of_multiplying_methods():
    evidence = replace(base_evidence(), equivalent_to_incumbent=True)
    assert verdict(evidence=evidence) is AssimilationVerdict.EQUIVALENT_TO_INCUMBENT


def test_incompatible_method_is_preserved_as_parallel_local_view():
    evidence = replace(base_evidence(), compatible_with_incumbent=False)
    assert verdict(evidence=evidence) is AssimilationVerdict.PARALLEL_LOCAL_VIEW


def test_known_negative_history_repeat_is_rejected():
    evidence = replace(base_evidence(), negative_history_match=True)
    assert verdict(evidence=evidence) is AssimilationVerdict.REJECT


def test_contract_is_frozen_and_authority_order_is_set_based():
    contract = base_contract()
    with pytest.raises(Exception):
        contract.component_id = "mutated"
    permuted = replace(
        contract,
        may_mint=frozenset(reversed(tuple(contract.may_mint))),
        must_not_mint=frozenset(reversed(tuple(contract.must_not_mint))),
    )
    assert verdict(contract=permuted) is AssimilationVerdict.ELIGIBLE_FOR_SHADOW


def test_frozen_benchmark_is_transport_renumbered_without_changed_predictions():
    path = Path(__file__).parents[1] / "research" / "SELF_RAKL_RESEARCH_013_FROZEN_BENCHMARK.json"
    data = json.loads(path.read_text())
    assert data["status"] == "FROZEN_BEFORE_IMPLEMENTATION_ON_ROUND_013_BRANCH"
    assert data["starting_main_sha"] == "959899f3689b29bba97e5172c9071888473f511f"
    assert data["supersedes_transport_identity_only"]["behavioral_predictions_changed"] is False
    assert data["supersedes_transport_identity_only"]["thresholds_or_falsifiers_changed"] is False
    ids = {world["id"] for world in data["worlds"]}
    assert len(ids) == 15
    assert {
        "clean_candidate",
        "self_contradictory_authority_contract",
        "candidate_self_report_only",
        "incompatible_but_locally_valid",
        "known_negative_history_repeat",
    }.issubset(ids)
