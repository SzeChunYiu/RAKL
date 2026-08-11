"""Frozen planted-world tests for the proposal-only preservation receipt.

The fixtures are **synthetic**.  Each unfaithful world is the abstract *shape* of
one cross-domain pattern the motivating issue lists, expressed in neutral ids and
opaque state labels.  No Millennium-problem mathematics is imported into
framework tests: the object under test is a congruence detector, and reproducing
the mathematics would test the fixture author rather than the detector.

The corpus is labelled, and false accepts and false rejects are counted
**separately**.  A detector that rejects every surrogate has a perfect
false-accept rate and is worthless, so the false-reject control is not optional
here — and every faithful fixture must reach the *positive* verdict, not merely
avoid rejection, so that an uninformative probe set cannot pass by vacuity.
"""

from __future__ import annotations

import json
from dataclasses import replace
from enum import Enum
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator  # type: ignore[import-untyped]

from rakl.root_coordinate_preservation import (
    CollisionWitness,
    CoordinateAuthority,
    PreservationVerdict,
    RootCoordinatePreservationReceipt,
    RootCoordinateProbe,
    audit_root_coordinate_preservation,
    find_collision_witnesses,
    receipt_canonical_sha256,
)


class WorldLabel(str, Enum):
    """Ground truth for one planted world."""

    FAITHFUL = "FAITHFUL"
    UNFAITHFUL = "UNFAITHFUL"


def probe(probe_id: str, state: str, outcome: str | None) -> RootCoordinateProbe:
    return RootCoordinateProbe(
        probe_id=probe_id,
        projected_surrogate_state=state,
        registered_root_outcome=outcome,
        evidence_pointer=f"evidence://{probe_id}",
    )


def make_receipt(**overrides: Any) -> RootCoordinatePreservationReceipt:
    base = RootCoordinatePreservationReceipt(
        root_claim_id="ROOT-001",
        root_coordinate="root_obligation_quantity",
        surrogate_or_local_coordinate="local_surrogate_coordinate",
        scope_id="SCOPE-global",
        bridge_map=(("local_surrogate_coordinate", "root_obligation_quantity"),),
        cheapest_hostile_world=(
            "two members of one surrogate class register different root outcomes"
        ),
        public_trace_event_id="TRACE-0100",
        source_authority=CoordinateAuthority.ESTABLISHED,
        target_authority=CoordinateAuthority.PROPOSED,
        enabling_assumptions=("bridge is evaluated only inside the declared scope",),
        non_compensatory_obligations=("root-side identification is not discharged",),
        known_disanalogies=("surrogate is defined locally, the root is not",),
        unproved_interface_edges=(),
        reverification_triggers=("scope widened",),
        scope_conditions=("declared scope only",),
        probes=(
            probe("P1", "class_a", "root_positive"),
            probe("P2", "class_a", "root_positive"),
            probe("P3", "class_b", "root_negative"),
            probe("P4", "class_b", "root_negative"),
        ),
        failure_memory_ids=("FAIL-0001",),
        coverage_receipt_id="COV-0100",
        evidence_pointers=("evidence://contract",),
    )
    return replace(base, **overrides).with_content_hash()


# --- the labelled corpus ------------------------------------------------------
#
# Each entry: (world_id, pattern shape, label, probes).
# Pattern names describe the abstract failure shape only.

UNFAITHFUL_WORLDS: tuple[tuple[str, str, tuple[RootCoordinateProbe, ...]], ...] = (
    (
        "W1",
        "richness_not_charged_to_root_cost",
        (
            probe("W1-a", "richness_maximal", "root_cost_zero"),
            probe("W1-b", "richness_maximal", "root_cost_maximal"),
            probe("W1-c", "richness_minimal", "root_cost_zero"),
        ),
    ),
    (
        "W2",
        "unconditional_norm_does_not_transport_sign",
        (
            probe("W2-a", "norm_positive", "target_sign_positive"),
            probe("W2-b", "norm_positive", "target_sign_indeterminate"),
            probe("W2-c", "norm_zero", "target_sign_indeterminate"),
        ),
    ),
    (
        "W3",
        "local_corrections_inflate_discrete_order",
        (
            probe("W3-a", "discrete_order_2", "analytic_order_1"),
            probe("W3-b", "discrete_order_2", "analytic_order_2"),
            probe("W3-c", "discrete_order_0", "analytic_order_0"),
        ),
    ),
    (
        "W4",
        "detector_output_is_not_kernel_vanishing",
        (
            probe("W4-a", "detector_fires", "obstruction_vanishes"),
            probe("W4-b", "detector_fires", "obstruction_persists"),
            probe("W4-c", "detector_silent", "obstruction_persists"),
        ),
    ),
    (
        "W5",
        "abstract_lemma_lacks_same_theory_binding",
        (
            probe("W5-a", "abstract_exclusion_holds", "same_theory_exclusion_holds"),
            probe("W5-b", "abstract_exclusion_holds", "same_theory_exclusion_fails"),
            probe("W5-c", "abstract_exclusion_fails", "same_theory_exclusion_fails"),
        ),
    ),
    (
        "W6",
        "local_rigidity_misses_noncompact_escape",
        (
            probe("W6-a", "local_decay_rigid", "global_rigidity_holds"),
            probe("W6-b", "local_decay_rigid", "global_rigidity_fails"),
            probe("W6-c", "local_decay_loose", "global_rigidity_fails"),
        ),
    ),
    (
        "W7",
        "equal_projected_state_different_registered_downstream_outcome",
        (
            probe("W7-a", "coarse_projection_s0", "downstream_reachable"),
            probe("W7-b", "coarse_projection_s0", "downstream_unreachable"),
            probe("W7-c", "coarse_projection_s1", "downstream_reachable"),
            probe("W7-d", "coarse_projection_s1", "downstream_reachable"),
        ),
    ),
)

FAITHFUL_WORLDS: tuple[tuple[str, str, tuple[RootCoordinateProbe, ...]], ...] = (
    (
        "C1",
        "refined_projection_is_locally_congruent",
        (
            probe("C1-a", "refined_projection_s0_in", "downstream_reachable"),
            probe("C1-b", "refined_projection_s0_in", "downstream_reachable"),
            probe("C1-c", "refined_projection_s0_out", "downstream_unreachable"),
            probe("C1-d", "refined_projection_s0_out", "downstream_unreachable"),
        ),
    ),
    (
        "C2",
        "coarse_state_is_genuinely_sufficient_under_its_hypothesis",
        (
            probe("C2-a", "coarse_class_x", "root_positive"),
            probe("C2-b", "coarse_class_x", "root_positive"),
            probe("C2-c", "coarse_class_x", "root_positive"),
            probe("C2-d", "coarse_class_y", "root_negative"),
            probe("C2-e", "coarse_class_y", "root_negative"),
        ),
    ),
    (
        "C3",
        "near_miss_surrogate_separates_the_root_outcomes",
        (
            probe("C3-a", "rate_fast", "root_cost_zero"),
            probe("C3-b", "rate_fast", "root_cost_zero"),
            probe("C3-c", "rate_slow", "root_cost_maximal"),
            probe("C3-d", "rate_slow", "root_cost_maximal"),
        ),
    ),
    (
        "C4",
        "detector_is_faithful_once_the_kernel_is_charged",
        (
            probe("C4-a", "detector_fires_kernel_charged", "obstruction_vanishes"),
            probe("C4-b", "detector_fires_kernel_charged", "obstruction_vanishes"),
            probe("C4-c", "detector_silent_kernel_charged", "obstruction_persists"),
            probe("C4-d", "detector_silent_kernel_charged", "obstruction_persists"),
        ),
    ),
)

CORPUS: tuple[tuple[str, str, WorldLabel, tuple[RootCoordinateProbe, ...]], ...] = (
    tuple(
        (world_id, pattern, WorldLabel.UNFAITHFUL, probes)
        for world_id, pattern, probes in UNFAITHFUL_WORLDS
    )
    + tuple(
        (world_id, pattern, WorldLabel.FAITHFUL, probes)
        for world_id, pattern, probes in FAITHFUL_WORLDS
    )
)


# --- separated error accounting -----------------------------------------------


def test_the_corpus_has_no_false_accepts() -> None:
    """Every planted unfaithful surrogate must be rejected."""

    missed = [
        f"{world_id}({pattern})"
        for world_id, pattern, label, probes in CORPUS
        if label is WorldLabel.UNFAITHFUL
        and not audit_root_coordinate_preservation(
            make_receipt(probes=probes)
        ).surrogate_rejected
    ]
    assert missed == [], f"false accepts — unfaithful surrogates not rejected: {missed}"


def test_the_corpus_has_no_false_rejects() -> None:
    """No genuinely faithful surrogate may be rejected.

    A receipt that rejects every surrogate is worthless; this is the control
    that proves this one does not.
    """

    rejected = [
        f"{world_id}({pattern})"
        for world_id, pattern, label, probes in CORPUS
        if label is WorldLabel.FAITHFUL
        and audit_root_coordinate_preservation(
            make_receipt(probes=probes)
        ).surrogate_rejected
    ]
    assert rejected == [], f"false rejects — faithful surrogates rejected: {rejected}"


def test_every_faithful_world_reaches_the_positive_verdict_not_merely_silence() -> None:
    """Guards the false-reject control against passing by vacuity.

    An uninformative probe set is also 'not rejected'.  Requiring the positive
    verdict forces every faithful fixture to be a probe set in which a collision
    genuinely could have surfaced.
    """

    for world_id, pattern, label, probes in CORPUS:
        if label is not WorldLabel.FAITHFUL:
            continue
        report = audit_root_coordinate_preservation(make_receipt(probes=probes))
        assert report.verdict is PreservationVerdict.NO_COLLISION_IN_BOUND_PROBE_SET, (
            f"{world_id}({pattern}) did not reach the positive verdict"
        )
        assert report.licenses_expensive_candidate_search is True
        assert report.informative_class_count >= 1


@pytest.mark.parametrize(
    "world_id, pattern, probes",
    [(w, p, pr) for w, p, pr in UNFAITHFUL_WORLDS],
)
def test_each_unfaithful_world_yields_a_named_collision_witness(
    world_id: str, pattern: str, probes: tuple[RootCoordinateProbe, ...]
) -> None:
    report = audit_root_coordinate_preservation(make_receipt(probes=probes))
    assert report.verdict is PreservationVerdict.SURROGATE_REJECTED_COLLISION_WITNESSED
    assert report.collision_witnesses, f"{world_id}({pattern}) produced no witness"
    for witness in report.collision_witnesses:
        assert len(witness.divergent_root_outcomes) >= 2
        assert len(witness.probe_ids) >= 2


def test_the_planted_world_named_by_the_issue_comment_is_detected() -> None:
    """`equal_projected_state / different_registered_downstream_outcome`."""

    _, _, probes = UNFAITHFUL_WORLDS[6]
    report = audit_root_coordinate_preservation(make_receipt(probes=probes))
    assert report.surrogate_rejected is True
    assert report.collision_witnesses == (
        CollisionWitness(
            projected_surrogate_state="coarse_projection_s0",
            probe_ids=("W7-a", "W7-b"),
            divergent_root_outcomes=("downstream_reachable", "downstream_unreachable"),
        ),
    )


# --- an uninformative probe set is not a licence -----------------------------


def test_an_empty_probe_set_is_uninformative_not_clean() -> None:
    report = audit_root_coordinate_preservation(make_receipt(probes=()))
    assert report.verdict is PreservationVerdict.PROBE_SET_UNINFORMATIVE
    assert report.licenses_expensive_candidate_search is False


def test_a_probe_set_of_singleton_classes_is_uninformative() -> None:
    """No class holds two probes, so no collision could ever surface."""

    report = audit_root_coordinate_preservation(
        make_receipt(
            probes=(
                probe("S1", "class_a", "root_positive"),
                probe("S2", "class_b", "root_negative"),
                probe("S3", "class_c", "root_positive"),
            )
        )
    )
    assert report.verdict is PreservationVerdict.PROBE_SET_UNINFORMATIVE
    assert report.informative_class_count == 0
    assert "absence_of_a_collision_here_is_structural_not_evidential" in report.reasons


def test_one_informative_class_is_enough_to_be_checkable() -> None:
    """No-alarm control for the informativeness gate."""

    report = audit_root_coordinate_preservation(
        make_receipt(
            probes=(
                probe("S1", "class_a", "root_positive"),
                probe("S2", "class_a", "root_positive"),
                probe("S3", "class_b", "root_negative"),
            )
        )
    )
    assert report.verdict is PreservationVerdict.NO_COLLISION_IN_BOUND_PROBE_SET
    assert report.informative_class_count == 1


def test_unobserved_root_outcomes_are_excluded_and_reported() -> None:
    report = audit_root_coordinate_preservation(
        make_receipt(
            probes=(
                probe("U1", "class_a", None),
                probe("U2", "class_a", None),
                probe("U3", "class_b", "root_negative"),
            )
        )
    )
    assert report.verdict is PreservationVerdict.PROBE_SET_UNINFORMATIVE
    assert report.unobserved_probe_ids == ("U1", "U2")
    assert report.observed_probe_count == 1


def test_an_unobserved_probe_cannot_manufacture_a_collision() -> None:
    """A null root outcome witnesses neither agreement nor disagreement."""

    witnesses = find_collision_witnesses(
        (
            probe("N1", "class_a", "root_positive"),
            probe("N2", "class_a", None),
        )
    )
    assert witnesses == ()


# --- a rejection is scoped, never a blacklist --------------------------------


def test_a_coordinate_rejected_globally_survives_at_a_narrower_scope() -> None:
    """AGENTS.md: a prior failure is a warning, not a blacklist."""

    _, _, colliding = UNFAITHFUL_WORLDS[6]
    global_report = audit_root_coordinate_preservation(
        make_receipt(scope_id="SCOPE-global", probes=colliding)
    )
    assert global_report.surrogate_rejected is True

    narrowed = audit_root_coordinate_preservation(
        make_receipt(
            scope_id="SCOPE-narrowed",
            scope_conditions=("restricted to the separating antecedent",),
            probes=(
                probe("N-a", "coarse_projection_s0_restricted", "downstream_reachable"),
                probe("N-b", "coarse_projection_s0_restricted", "downstream_reachable"),
                probe(
                    "N-c", "coarse_projection_s1_restricted", "downstream_unreachable"
                ),
                probe(
                    "N-d", "coarse_projection_s1_restricted", "downstream_unreachable"
                ),
            ),
        )
    )
    assert narrowed.surrogate_rejected is False
    assert narrowed.verdict is PreservationVerdict.NO_COLLISION_IN_BOUND_PROBE_SET
    assert narrowed.scope_id == "SCOPE-narrowed"


def test_no_report_blacklists_the_coordinate() -> None:
    _, _, colliding = UNFAITHFUL_WORLDS[0]
    report = audit_root_coordinate_preservation(make_receipt(probes=colliding))
    assert report.blacklists_the_coordinate is False
    assert "rejection_is_scoped_a_narrower_scope_needs_its_own_receipt" in report.reasons


# --- the contract fails closed ------------------------------------------------


def test_a_missing_cheapest_hostile_world_fails_closed() -> None:
    """The issue names this field load-bearing."""

    report = audit_root_coordinate_preservation(make_receipt(cheapest_hostile_world=""))
    assert report.verdict is PreservationVerdict.CONTRACT_INCOMPLETE
    assert "cheapest_hostile_world_missing" in report.reasons
    assert report.licenses_expensive_candidate_search is False


def test_a_missing_bridge_map_fails_closed() -> None:
    report = audit_root_coordinate_preservation(make_receipt(bridge_map=()))
    assert report.verdict is PreservationVerdict.CONTRACT_INCOMPLETE
    assert "bridge_map_missing" in report.reasons


def test_no_receipt_at_all_is_cannot_check_not_a_pass() -> None:
    report = audit_root_coordinate_preservation(None)
    assert report.verdict is PreservationVerdict.CANNOT_CHECK
    assert report.licenses_expensive_candidate_search is False


def test_a_tampered_receipt_cannot_be_checked() -> None:
    honest = make_receipt()
    tampered = replace(honest, cheapest_hostile_world="something more convenient")
    report = audit_root_coordinate_preservation(tampered)
    assert report.verdict is PreservationVerdict.CANNOT_CHECK
    assert any("content_hash" in reason for reason in report.reasons)


def test_duplicate_probe_ids_fail_closed() -> None:
    report = audit_root_coordinate_preservation(
        make_receipt(
            probes=(
                probe("D1", "class_a", "root_positive"),
                probe("D1", "class_a", "root_negative"),
            )
        )
    )
    assert report.verdict is PreservationVerdict.CONTRACT_INCOMPLETE
    assert "duplicate_probe_id" in report.reasons


# --- the positive verdict stays honest ---------------------------------------


def test_the_positive_verdict_is_not_a_faithfulness_proof() -> None:
    report = audit_root_coordinate_preservation(make_receipt())
    assert report.verdict is PreservationVerdict.NO_COLLISION_IN_BOUND_PROBE_SET
    assert report.proves_surrogate_faithfulness is False
    assert "this_is_not_a_faithfulness_proof" in report.reasons


def test_open_interface_edges_are_reported_on_the_positive_path() -> None:
    report = audit_root_coordinate_preservation(
        make_receipt(unproved_interface_edges=("surrogate-to-root transport unproved",))
    )
    assert report.verdict is PreservationVerdict.NO_COLLISION_IN_BOUND_PROBE_SET
    assert "unproved_interface_edges_remain_open" in report.reasons


def test_a_missing_coverage_receipt_is_reported_not_assumed() -> None:
    report = audit_root_coordinate_preservation(make_receipt(coverage_receipt_id=None))
    assert (
        "no_coverage_receipt_referenced_probe_universe_remains_unbound"
        in report.reasons
    )


@pytest.mark.parametrize(
    "probes",
    [
        make_receipt().probes,
        UNFAITHFUL_WORLDS[0][2],
        (),
    ],
)
def test_no_report_grants_authority(
    probes: tuple[RootCoordinateProbe, ...]
) -> None:
    report = audit_root_coordinate_preservation(make_receipt(probes=probes))
    assert report.grants_theorem_authority is False
    assert report.grants_proof_authority is False
    assert report.grants_tool_authority is False
    assert report.grants_gluing_authority is False
    assert report.grants_novelty_authority is False
    assert report.grants_framework_authority is False
    assert report.proves_surrogate_faithfulness is False
    assert report.claims_probe_universe_complete is False


# --- content binding ----------------------------------------------------------


def test_the_content_hash_covers_the_probe_set() -> None:
    original = make_receipt()
    altered = make_receipt(probes=UNFAITHFUL_WORLDS[0][2])
    assert original.receipt_canonical_sha256 != altered.receipt_canonical_sha256


def test_the_content_hash_covers_the_scope() -> None:
    assert (
        make_receipt().receipt_canonical_sha256
        != make_receipt(scope_id="SCOPE-other").receipt_canonical_sha256
    )


def test_the_content_hash_excludes_itself() -> None:
    receipt = make_receipt()
    assert receipt_canonical_sha256(receipt.to_dict()) == (
        receipt.receipt_canonical_sha256
    )


# --- schema -------------------------------------------------------------------


def _schema() -> dict[str, Any]:
    root = Path(__file__).resolve().parents[1]
    return json.loads(
        (root / "schemas/root-coordinate-preservation-receipt-v1.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_receipt_documents_validate_against_the_frozen_schema() -> None:
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema)
    for _, _, _, probes in CORPUS:
        validator.validate(make_receipt(probes=probes).to_dict())
    validator.validate(make_receipt(coverage_receipt_id=None, probes=()).to_dict())


def test_schema_rejects_a_receipt_claiming_faithfulness_was_proved() -> None:
    validator = Draft202012Validator(_schema())
    document = make_receipt().to_dict()
    document["proves_surrogate_faithfulness"] = True
    assert not validator.is_valid(document)


def test_schema_rejects_a_receipt_claiming_theorem_authority() -> None:
    validator = Draft202012Validator(_schema())
    document = make_receipt().to_dict()
    document["grants_theorem_authority"] = True
    assert not validator.is_valid(document)


def test_schema_rejects_a_receipt_without_a_cheapest_hostile_world() -> None:
    validator = Draft202012Validator(_schema())
    document = make_receipt().to_dict()
    document["cheapest_hostile_world"] = ""
    assert not validator.is_valid(document)


def test_schema_rejects_an_empty_bridge_map() -> None:
    validator = Draft202012Validator(_schema())
    document = make_receipt().to_dict()
    document["bridge_map"] = []
    assert not validator.is_valid(document)
