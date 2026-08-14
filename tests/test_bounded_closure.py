from __future__ import annotations

from rakl.bounded_closure import (
    ClosureVerdict,
    MechanicClosureRecord,
    assess_bounded_closure,
)


def _closed(mechanic_id: str) -> MechanicClosureRecord:
    return MechanicClosureRecord(
        mechanic_id=mechanic_id,
        implementation_present=True,
        tests_present=True,
        evidence_present=True,
        paper_owner_present=True,
        open_question_registered=True,
    )


def test_closure_is_exact_registry_relative_and_not_global_completeness() -> None:
    records = (_closed("epistemic"), _closed("structural"))
    cert = assess_bounded_closure(
        records,
        subject_sha="abc123",
        cutoff="2026-08-14T23:57:00+02:00",
    )

    assert cert.verdict is ClosureVerdict.CLOSED_AT_REGISTERED_CUTOFF
    assert cert.global_completeness_claimed is False
    assert cert.grants_scientific_authority is False
    assert cert.valid_for(records) is True


def test_adding_new_candidate_invalidates_old_closed_certificate() -> None:
    old_records = (_closed("epistemic"), _closed("structural"))
    old_cert = assess_bounded_closure(
        old_records,
        subject_sha="abc123",
        cutoff="2026-08-14T23:57:00+02:00",
    )

    new_candidate = MechanicClosureRecord(
        mechanic_id="new_pursuit_mechanic",
        implementation_present=False,
        tests_present=False,
        evidence_present=False,
        paper_owner_present=True,
        open_question_registered=True,
    )
    current_records = old_records + (new_candidate,)
    current_cert = assess_bounded_closure(
        current_records,
        subject_sha="def456",
        cutoff="2026-08-15T00:01:00+02:00",
    )

    assert old_cert.valid_for(current_records) is False
    assert current_cert.verdict is ClosureVerdict.OPEN_AT_REGISTERED_CUTOFF
    assert current_cert.closed_mechanic_ids == ("epistemic", "structural")


def test_decisive_negative_evidence_can_still_close_bookkeeping_coordinate() -> None:
    # evidence_present means the registered scientific question has a terminal
    # evidence artifact; it does not mean the result was positive.
    negative_but_decided = _closed("negative_net_benefit_mechanic")
    cert = assess_bounded_closure(
        (negative_but_decided,),
        subject_sha="negative-terminal",
        cutoff="2026-08-14",
    )

    assert cert.verdict is ClosureVerdict.CLOSED_AT_REGISTERED_CUTOFF
