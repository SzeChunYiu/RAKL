from dataclasses import dataclass

import pytest

from rakl.semantic_quotient import (
    ProblemRepresentation,
    QuotientProposal,
    QuotientValidationReport,
    QuotientValidationVerdict,
    materialize_validated_quotient,
    quotient_problem_atom,
    validate_proposal_contract,
)


def _source() -> ProblemRepresentation:
    return ProblemRepresentation(
        representation_id="r1",
        problem_id="p1",
        atom_id="a1",
        qoi="stability",
        context_hash="ctx",
        source_hash="src",
        coordinates=("arrival", "service", "color"),
        protected_fields=("arrival", "service"),
        provenance_ids=("prov",),
    )


def _proposal(**kwargs: object) -> QuotientProposal:
    base: dict[str, object] = dict(
        quotient_id="q1",
        source_representation_id="r1",
        source_hash="src",
        qoi="stability",
        context_hash="ctx",
        preserved_coordinates=("arrival", "service"),
        erased_coordinates=("color",),
        preserved_invariants=("arrival_gt_service",),
        protected_coordinates=("arrival", "service"),
        sufficiency_obligations=("answer_preserved",),
        falsifiers=("counterexample_changes_answer",),
        reconstruction_bindings=(("output_unit", "patients/hour"),),
        forbidden_losses=("causal_direction",),
    )
    base.update(kwargs)
    return QuotientProposal(**base)


def _report(proposal: QuotientProposal, **kwargs: object) -> QuotientValidationReport:
    base: dict[str, object] = dict(
        quotient_id=proposal.quotient_id,
        proposal_hash=proposal.content_hash,
        source_hash="src",
        verdict=QuotientValidationVerdict.VALID_EXACT,
        verified_obligations=("answer_preserved",),
        metamorphic_checks=("rename_color_invariant",),
        protected_coordinate_checks=("arrival_present", "service_present"),
        evidence_pointers=("receipt:test",),
    )
    base.update(kwargs)
    return QuotientValidationReport(**base)


def test_valid_exact_materializes_and_hashes_deterministically() -> None:
    source, proposal = _source(), _proposal()
    view = materialize_validated_quotient(
        source,
        proposal,
        _report(proposal),
        desired_effects=("reduce_backlog",),
    )
    assert view.structural_coordinates == ("arrival", "service")
    assert view.erased_coordinates == ("color",)
    assert len(view.content_hash) == 64
    assert view.content_hash == view.content_hash


def test_protected_coordinate_erasure_is_rejected() -> None:
    source = _source()
    proposal = _proposal(
        preserved_coordinates=("service",),
        erased_coordinates=("arrival", "color"),
        protected_coordinates=("arrival", "service"),
    )
    reasons = validate_proposal_contract(source, proposal)
    assert "protected_coordinate_erased" in reasons
    assert "protected_coordinate_not_preserved" in reasons


def test_coordinate_partition_must_be_complete_and_disjoint() -> None:
    source = _source()
    overlap = _proposal(
        preserved_coordinates=("arrival", "service", "color"),
        erased_coordinates=("color",),
    )
    assert "coordinate_partition_conflict" in validate_proposal_contract(source, overlap)

    incomplete = _proposal(erased_coordinates=())
    assert "source_coordinate_unclassified" in validate_proposal_contract(source, incomplete)


def test_unknown_or_failed_sufficiency_fails_closed() -> None:
    source, proposal = _source(), _proposal()
    cannot_check = _report(
        proposal,
        verified_obligations=(),
        unknown_obligations=("answer_preserved",),
        verdict=QuotientValidationVerdict.CANNOT_CHECK,
    )
    with pytest.raises(ValueError, match="quotient_not_validated_for_solver_use"):
        materialize_validated_quotient(source, proposal, cannot_check)

    failed = _report(
        proposal,
        verified_obligations=(),
        failed_obligations=("answer_preserved",),
    )
    with pytest.raises(ValueError, match="failed_sufficiency"):
        materialize_validated_quotient(source, proposal, failed)


def test_approximate_requires_metric_and_tolerance() -> None:
    source, proposal = _source(), _proposal()
    missing_bound = _report(
        proposal,
        verdict=QuotientValidationVerdict.VALID_APPROXIMATE,
    )
    with pytest.raises(ValueError, match="metric_and_tolerance"):
        materialize_validated_quotient(source, proposal, missing_bound)

    bounded = _report(
        proposal,
        verdict=QuotientValidationVerdict.VALID_APPROXIMATE,
        approximation_metric="absolute_error",
        approximation_tolerance=0.01,
    )
    assert (
        materialize_validated_quotient(source, proposal, bounded).validation_verdict
        is QuotientValidationVerdict.VALID_APPROXIMATE
    )


def test_source_hash_qoi_and_context_are_bound() -> None:
    source = _source()
    assert "source_hash_mismatch" in validate_proposal_contract(
        source, _proposal(source_hash="other")
    )
    assert "qoi_mismatch" in validate_proposal_contract(source, _proposal(qoi="latency"))
    assert "context_hash_mismatch" in validate_proposal_contract(
        source, _proposal(context_hash="other")
    )


@dataclass(frozen=True)
class _Atom:
    atom_id: str
    goal: str
    context_hash: str
    structural_coordinates: tuple[str, ...]
    desired_effects: tuple[str, ...]


def test_quotient_problem_atom_is_derived_not_mutated() -> None:
    source, proposal = _source(), _proposal()
    view = materialize_validated_quotient(
        source,
        proposal,
        _report(proposal),
        desired_effects=("reduce_backlog",),
    )
    raw = _Atom(
        "a1",
        "solve",
        "ctx",
        ("arrival", "service", "color"),
        ("raw_effect",),
    )
    derived = quotient_problem_atom(raw, view)
    assert raw.structural_coordinates == ("arrival", "service", "color")
    assert derived.structural_coordinates == ("arrival", "service")
    assert derived.desired_effects == ("reduce_backlog",)


def test_wrong_atom_or_context_cannot_use_view() -> None:
    source, proposal = _source(), _proposal()
    view = materialize_validated_quotient(source, proposal, _report(proposal))
    with pytest.raises(ValueError, match="source_atom"):
        quotient_problem_atom(_Atom("wrong", "solve", "ctx", ("a",), ("x",)), view)
    with pytest.raises(ValueError, match="context"):
        quotient_problem_atom(_Atom("a1", "solve", "wrong", ("a",), ("x",)), view)
