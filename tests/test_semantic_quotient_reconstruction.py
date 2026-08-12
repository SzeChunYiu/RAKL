import pytest

from rakl.semantic_quotient import (
    ProblemRepresentation,
    QuotientProposal,
    QuotientValidationReport,
    QuotientValidationVerdict,
    materialize_validated_quotient,
)
from rakl.semantic_quotient_reconstruction import reconstruct_and_verify_original


def _view():
    source = ProblemRepresentation(
        representation_id="r-reconstruct",
        problem_id="p-reconstruct",
        atom_id="a-reconstruct",
        qoi="throughput",
        context_hash="ctx-reconstruct",
        source_hash="source-reconstruct-hash",
        coordinates=("rate", "unit_label"),
        protected_fields=("rate",),
    )
    proposal = QuotientProposal(
        quotient_id="q-reconstruct",
        source_representation_id=source.representation_id,
        source_hash=source.source_hash,
        qoi=source.qoi,
        context_hash=source.context_hash,
        preserved_coordinates=("rate",),
        erased_coordinates=("unit_label",),
        preserved_invariants=("throughput_value",),
        protected_coordinates=("rate",),
        sufficiency_obligations=("value_preserved",),
        reconstruction_bindings=(("unit", "patients/hour"),),
        falsifiers=("unit_change_changes_value",),
    )
    report = QuotientValidationReport(
        quotient_id=proposal.quotient_id,
        proposal_hash=proposal.content_hash,
        source_hash=source.source_hash,
        verdict=QuotientValidationVerdict.VALID_EXACT,
        verified_obligations=("value_preserved",),
        metamorphic_checks=("unit_label_erasure",),
        protected_coordinate_checks=("rate_preserved",),
        evidence_pointers=("receipt:reconstruction",),
    )
    return materialize_validated_quotient(source, proposal, report)


def test_reconstruction_must_pass_original_verifier_before_final_success() -> None:
    view = _view()

    reconstructed, report = reconstruct_and_verify_original(
        view,
        source_problem_id="p-reconstruct",
        source_hash="source-reconstruct-hash",
        quotient_solution={"value": 7},
        reconstruct=lambda solution, bindings: {
            "value": solution["value"],
            "unit": bindings["unit"],
        },
        verify_original=lambda result: (
            "PASS" if result == {"value": 7, "unit": "patients/hour"} else "FAIL"
        ),
        evidence_pointers=("original-verifier:receipt",),
    )

    assert reconstructed == {"value": 7, "unit": "patients/hour"}
    assert report.original_problem_verified
    assert report.original_problem_verification == "PASS"
    assert len(report.quotient_solution_hash) == 64
    assert len(report.reconstructed_solution_hash) == 64


def test_original_failure_and_cannot_check_remain_distinct() -> None:
    view = _view()
    _, failed = reconstruct_and_verify_original(
        view,
        source_problem_id="p-reconstruct",
        source_hash="source-reconstruct-hash",
        quotient_solution={"value": 8},
        reconstruct=lambda solution, bindings: {**solution, "unit": bindings["unit"]},
        verify_original=lambda _: "FAIL",
    )
    assert not failed.original_problem_verified
    assert failed.original_problem_verification == "FAIL"

    _, unknown = reconstruct_and_verify_original(
        view,
        source_problem_id="p-reconstruct",
        source_hash="source-reconstruct-hash",
        quotient_solution={"value": 8},
        reconstruct=lambda solution, bindings: {**solution, "unit": bindings["unit"]},
        verify_original=lambda _: "CANNOT_CHECK",
    )
    assert not unknown.original_problem_verified
    assert unknown.original_problem_verification == "CANNOT_CHECK"


def test_reconstruction_is_bound_to_source_and_verifier_vocabulary() -> None:
    view = _view()
    with pytest.raises(ValueError, match="source_hash_mismatch"):
        reconstruct_and_verify_original(
            view,
            source_problem_id="p-reconstruct",
            source_hash="wrong",
            quotient_solution={"value": 7},
            reconstruct=lambda solution, _: solution,
            verify_original=lambda _: "PASS",
        )

    with pytest.raises(ValueError, match="PASS_FAIL_OR_CANNOT_CHECK"):
        reconstruct_and_verify_original(
            view,
            source_problem_id="p-reconstruct",
            source_hash="source-reconstruct-hash",
            quotient_solution={"value": 7},
            reconstruct=lambda solution, _: solution,
            verify_original=lambda _: "SUPPORTED",
        )
