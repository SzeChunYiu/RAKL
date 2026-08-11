"""Planted worlds for the root-coordinate preservation receipt (issue #124).

All fixtures are **synthetic**. The six historical cases in the issue were used
to derive the abstract *shapes* of the worlds below; no Millennium-problem
mathematics is imported into framework tests, and no world asserts anything
about any real open problem.

Both error directions are reported separately, because a receipt that rejects
every surrogate is worthless:

* **false accept** — a planted defect that is not refuted;
* **false reject** — a faithful or honestly-open bridge that is refuted.

The controls matter as much as the detections. ``faithful_surrogate`` must pass,
and ``faithful_but_unobserved`` must come back ``CANNOT_CHECK`` rather than
congruent: an unavailable hostile world is never evidence of faithfulness.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Tuple

import jsonschema
import pytest

from rakl.root_coordinate_preservation import (
    BridgeEdge,
    CoordinateAuthority,
    EdgeProofStatus,
    Obligation,
    PreservationVerdict,
    RegisteredStateObservation,
    RootCoordinatePreservationReceipt,
    audit_root_coordinate_preservation,
    find_congruence_violations,
)

SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schemas"
    / "root-coordinate-preservation-receipt-v1.schema.json"
)


def _edge(
    edge_id: str = "E-1",
    proof_status: EdgeProofStatus = EdgeProofStatus.PROVED,
) -> BridgeEdge:
    return BridgeEdge(
        edge_id=edge_id,
        source_coordinate="surrogate.projected_measure",
        target_coordinate="root.registered_obligation",
        interface_map="pi: registered_state -> projected_state",
        proof_status=proof_status,
        enabling_assumptions=("projection is defined on the whole registered domain",),
    )


def _receipt(**overrides: object) -> RootCoordinatePreservationReceipt:
    base = dict(
        receipt_id="RCP-1",
        root_claim_id="ROOT-1",
        root_coordinate="root.registered_obligation",
        surrogate_coordinate="surrogate.projected_measure",
        bridge_edges=(_edge(),),
        obligations=(
            Obligation(
                obligation_id="OB-1",
                description="root obligation that surrogate gains may not pay for",
                non_compensatory=True,
            ),
        ),
        known_disanalogies=("surrogate is defined on a coarser state space",),
        source_authority=CoordinateAuthority.ESTABLISHED,
        target_authority=CoordinateAuthority.PROPOSAL_ONLY,
        cheapest_hostile_world="two registered states share a projection but differ downstream",
        registered_observations=(
            RegisteredStateObservation("S-1", "P-a", "OUT-1"),
            RegisteredStateObservation("S-2", "P-b", "OUT-2"),
        ),
        reverification_triggers=("projection redefined", "new registered state family added"),
    )
    base.update(overrides)
    return RootCoordinatePreservationReceipt(**base)  # type: ignore[arg-type]


@dataclass(frozen=True)
class World:
    label: str
    receipt: RootCoordinatePreservationReceipt
    expected: PreservationVerdict
    #: True when the world plants a real defect that MUST be refuted.
    planted_defect: bool


def _worlds() -> Tuple[World, ...]:
    return (
        # Shape 1: representation richness is not charged by the root cost.
        World(
            "richness_not_charged",
            _receipt(
                registered_observations=(
                    RegisteredStateObservation("S-rich", "P-same", "OUT-expensive"),
                    RegisteredStateObservation("S-sparse", "P-same", "OUT-free"),
                )
            ),
            PreservationVerdict.SURROGATE_BRIDGE_REFUTED,
            True,
        ),
        # Shape 2: a valid local positivity result is not transported yet.
        World(
            "positivity_not_transported",
            _receipt(bridge_edges=(_edge(proof_status=EdgeProofStatus.UNPROVED),)),
            PreservationVerdict.INTERFACE_UNPROVED,
            False,
        ),
        # Shape 3: a discrete order and a continuous order disagree on a pair.
        World(
            "discrete_order_mismatch",
            _receipt(
                registered_observations=(
                    RegisteredStateObservation("S-a", "P-order-1", "OUT-order-1"),
                    RegisteredStateObservation("S-b", "P-order-1", "OUT-order-2"),
                    RegisteredStateObservation("S-c", "P-order-2", "OUT-order-2"),
                )
            ),
            PreservationVerdict.SURROGATE_BRIDGE_REFUTED,
            True,
        ),
        # Shape 4: detector output alone is claimed to discharge a root obligation.
        World(
            "detector_output_not_source",
            _receipt(
                obligations=(
                    Obligation(
                        obligation_id="OB-source",
                        description="an independently defined source must be exhibited",
                        non_compensatory=True,
                        discharged_by_surrogate_evidence_only=True,
                    ),
                )
            ),
            PreservationVerdict.SURROGATE_BRIDGE_REFUTED,
            True,
        ),
        # Shape 5: a correct abstract lemma still needs several transport edges.
        World(
            "abstract_lemma_needs_transport",
            _receipt(
                bridge_edges=(
                    _edge("E-binding", EdgeProofStatus.PROVED),
                    _edge("E-uniformity", EdgeProofStatus.UNPROVED),
                    _edge("E-scaling", EdgeProofStatus.UNSPECIFIED),
                )
            ),
            PreservationVerdict.INTERFACE_UNPROVED,
            False,
        ),
        # Shape 6: a local/centered coordinate misses a far-field distinction.
        World(
            "local_decay_misses_far_field",
            _receipt(
                registered_observations=(
                    RegisteredStateObservation("S-centered-1", "P-local", "OUT-controlled"),
                    RegisteredStateObservation("S-centered-2", "P-local", "OUT-controlled"),
                    RegisteredStateObservation("S-far-field", "P-local", "OUT-escapes"),
                )
            ),
            PreservationVerdict.SURROGATE_BRIDGE_REFUTED,
            True,
        ),
        # Control: a genuinely faithful surrogate must NOT be rejected.
        World(
            "faithful_surrogate",
            _receipt(
                registered_observations=(
                    RegisteredStateObservation("S-1", "P-a", "OUT-1"),
                    RegisteredStateObservation("S-1-bis", "P-a", "OUT-1"),
                    RegisteredStateObservation("S-2", "P-b", "OUT-2"),
                )
            ),
            PreservationVerdict.BRIDGE_LOCALLY_CONGRUENT,
            False,
        ),
        # Control: no observations is not faithfulness.
        World(
            "faithful_but_unobserved",
            _receipt(registered_observations=()),
            PreservationVerdict.CANNOT_CHECK,
            False,
        ),
        # Control: a conditional edge is an open interface, not a discharged one.
        World(
            "conditional_edge_is_not_discharged",
            _receipt(bridge_edges=(_edge(proof_status=EdgeProofStatus.CONDITIONAL),)),
            PreservationVerdict.INTERFACE_UNPROVED,
            False,
        ),
    )


@pytest.mark.parametrize("world", _worlds(), ids=lambda world: world.label)
def test_each_world_gets_its_expected_verdict(world: World) -> None:
    report = audit_root_coordinate_preservation(world.receipt)
    assert report.verdict is world.expected, (
        f"{world.label}: expected {world.expected.value}, got {report.verdict.value} "
        f"(reasons={report.reasons})"
    )


def test_false_accept_and_false_reject_are_reported_separately() -> None:
    """Both error directions, counted independently.

    A receipt that refuses every surrogate would show zero false accepts and a
    pile of false rejects; only reporting the pair makes that visible.
    """

    false_accepts: list[str] = []
    false_rejects: list[str] = []

    for world in _worlds():
        report = audit_root_coordinate_preservation(world.receipt)
        refuted = report.verdict is PreservationVerdict.SURROGATE_BRIDGE_REFUTED
        if world.planted_defect and not refuted:
            false_accepts.append(world.label)
        if not world.planted_defect and refuted:
            false_rejects.append(world.label)

    planted = [world.label for world in _worlds() if world.planted_defect]
    faithful = [world.label for world in _worlds() if not world.planted_defect]

    # Lower bounds, not exact counts: adding a tenth world must not turn this
    # red for a reason unrelated to the discriminator. A degenerate empty world
    # set would fail here rather than pass with two empty error lists.
    assert len(planted) >= 4
    assert len(faithful) >= 4
    assert false_accepts == [], f"false accepts: {false_accepts}"
    assert false_rejects == [], f"false rejects: {false_rejects}"


def test_the_planted_state_projection_world_is_detected() -> None:
    """`equal_projected_state / different_registered_downstream_outcome`."""

    receipt = _receipt(
        registered_observations=(
            RegisteredStateObservation("S-1", "P-collision", "OUT-reachable"),
            RegisteredStateObservation("S-2", "P-collision", "OUT-unreachable"),
        )
    )
    report = audit_root_coordinate_preservation(receipt)

    assert report.verdict is PreservationVerdict.SURROGATE_BRIDGE_REFUTED
    assert report.congruence_violations == (("S-1", "S-2"),)
    assert any(
        reason.startswith("equal_projected_state_different_registered_downstream_outcome")
        for reason in report.reasons
    )


def test_absent_hostile_world_is_never_evidence_of_faithfulness() -> None:
    """A named regression risk in the issue, asserted rather than intended."""

    report = audit_root_coordinate_preservation(_receipt(registered_observations=()))

    assert report.verdict is PreservationVerdict.CANNOT_CHECK
    assert report.verdict is not PreservationVerdict.BRIDGE_LOCALLY_CONGRUENT


def test_an_open_interface_does_not_stop_surrogate_investment() -> None:
    """False-reject guard: an unproved edge is a residual, not a blacklist."""

    open_interface = audit_root_coordinate_preservation(
        _receipt(bridge_edges=(_edge(proof_status=EdgeProofStatus.UNPROVED),))
    )
    refuted = audit_root_coordinate_preservation(
        _receipt(
            registered_observations=(
                RegisteredStateObservation("S-1", "P-same", "OUT-1"),
                RegisteredStateObservation("S-2", "P-same", "OUT-2"),
            )
        )
    )

    assert open_interface.surrogate_may_be_prioritized
    assert not refuted.surrogate_may_be_prioritized


def test_no_verdict_ever_claims_root_progress() -> None:
    for world in _worlds():
        report = audit_root_coordinate_preservation(world.receipt)
        assert not report.advances_root_claim, world.label


def test_report_exposes_no_solution_authority() -> None:
    """Composition boundary: GluingReport's authority semantics must not leak.

    ``GluingReport.grants_solution_authority`` is local-to-global solution
    assembly. This object acts earlier and is search control only, so no
    equivalent surface may appear here.
    """

    report = audit_root_coordinate_preservation(_receipt())

    # Asserted over the report's actual public surface, not over module text: a
    # source grep would pass vacuously and keep passing whatever surface someone
    # later adds. This fails the moment any `grants_*_authority`-style property
    # appears, under any name.
    authority_surfaces = [
        name for name in dir(report) if not name.startswith("_") and "authority" in name.lower()
    ]
    assert authority_surfaces == [], authority_surfaces


def test_receipt_requires_a_cheapest_hostile_world() -> None:
    with pytest.raises(ValueError, match="cheapest hostile world"):
        _receipt(cheapest_hostile_world="")


def test_receipt_rejects_a_self_surrogate() -> None:
    with pytest.raises(ValueError, match="cannot be its own surrogate"):
        _receipt(surrogate_coordinate="root.registered_obligation")


def test_receipt_without_bridge_edges_cannot_check() -> None:
    report = audit_root_coordinate_preservation(_receipt(bridge_edges=()))
    assert report.verdict is PreservationVerdict.CANNOT_CHECK


def test_congruence_helper_is_order_independent() -> None:
    observations = (
        RegisteredStateObservation("S-1", "P", "OUT-1"),
        RegisteredStateObservation("S-2", "P", "OUT-2"),
    )
    forward = find_congruence_violations(observations)
    backward = find_congruence_violations(tuple(reversed(observations)))

    assert {frozenset(pair) for pair in forward} == {frozenset(pair) for pair in backward}


def test_document_validates_against_its_schema() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    for world in _worlds():
        jsonschema.validate(world.receipt.document(), schema)


def test_document_hash_covers_the_bridge_and_the_hostile_world() -> None:
    original = _receipt()
    for field_name, value in (
        ("cheapest_hostile_world", "a different world"),
        ("bridge_edges", (_edge(proof_status=EdgeProofStatus.UNPROVED),)),
        ("surrogate_coordinate", "surrogate.other"),
    ):
        mutated = replace(original, **{field_name: value})
        assert (
            mutated.document()["receipt_canonical_sha256"]
            != original.document()["receipt_canonical_sha256"]
        ), field_name
