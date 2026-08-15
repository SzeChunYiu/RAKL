"""RFA v1: question/framework adequacy gates and the ancestor-challenge packet.

Covers packet section 05 (noncompensatory adequacy vectors, framework parent
families) and section 07 (the eight-field ancestor challenge packet).

``decide`` is not exercised here; the frozen decision chain and the 37-case
conformance are asserted in their own files and are unaffected.
"""

from __future__ import annotations

import pytest

from rakl.recursive_framework_audit import (
    AncestorChallenge,
    AuditCoordinate,
    FrameworkAdequacyCoordinate,
    FrameworkParentFamily,
    QuestionAdequacyCoordinate,
    assess_framework_adequacy,
    assess_question_adequacy,
    missing_framework_parents,
)


# --- adequacy vectors -------------------------------------------------------


def test_question_adequacy_has_nine_coordinates_and_no_scalar() -> None:
    assert len(tuple(QuestionAdequacyCoordinate)) == 9
    verdict = assess_question_adequacy({c: True for c in QuestionAdequacyCoordinate})
    assert verdict.adequate is True
    assert verdict.blocking_reason == ""
    assert not hasattr(verdict, "score")
    assert verdict.grants_scientific_authority is False
    assert verdict.grants_method_promotion_authority is False


def test_framework_adequacy_has_ten_coordinates() -> None:
    assert len(tuple(FrameworkAdequacyCoordinate)) == 10
    assert assess_framework_adequacy({c: True for c in FrameworkAdequacyCoordinate}).adequate is True


def test_hard_failure_is_noncompensatory_on_every_coordinate() -> None:
    for failing in QuestionAdequacyCoordinate:
        ratings = {c: True for c in QuestionAdequacyCoordinate}
        ratings[failing] = False
        verdict = assess_question_adequacy(ratings)
        assert verdict.adequate is False
        assert verdict.hard_failures == (failing.value,)
        assert "noncompensatory" in verdict.blocking_reason

    for failing_f in FrameworkAdequacyCoordinate:
        ratings_f = {c: True for c in FrameworkAdequacyCoordinate}
        ratings_f[failing_f] = False
        verdict_f = assess_framework_adequacy(ratings_f)
        assert verdict_f.adequate is False
        assert verdict_f.hard_failures == (failing_f.value,)


def test_unrated_coordinate_is_an_unrun_check_not_a_pass() -> None:
    ratings = {c: True for c in QuestionAdequacyCoordinate if c is not QuestionAdequacyCoordinate.IDENTIFIABILITY}
    verdict = assess_question_adequacy(ratings)
    assert verdict.adequate is False
    assert verdict.hard_failures == ()
    assert verdict.unrated == (QuestionAdequacyCoordinate.IDENTIFIABILITY.value,)
    assert "unrun check" in verdict.blocking_reason
    assert assess_question_adequacy({}).unrated == tuple(c.value for c in QuestionAdequacyCoordinate)


def test_framework_parent_portfolio_requires_the_registered_minimum() -> None:
    assert missing_framework_parents(()) == (
        FrameworkParentFamily.DIRECT_MINIMAL_REPRESENTATION,
        FrameworkParentFamily.CANONICAL_DOMAIN_FRAMEWORK,
        FrameworkParentFamily.STRONGEST_RETRIEVED_ALTERNATIVE,
        FrameworkParentFamily.CURRENT_RAKL_COMPILED_FRAMEWORK,
    )
    complete = (
        FrameworkParentFamily.DIRECT_MINIMAL_REPRESENTATION,
        FrameworkParentFamily.CANONICAL_DOMAIN_FRAMEWORK,
        FrameworkParentFamily.STRONGEST_RETRIEVED_ALTERNATIVE,
        FrameworkParentFamily.CURRENT_RAKL_COMPILED_FRAMEWORK,
    )
    assert missing_framework_parents(complete) == ()
    # A synthesized challenger alone does not discharge the parent obligation.
    assert missing_framework_parents((FrameworkParentFamily.SYNTHESIZED_CHALLENGER,)) == complete
    # ...and it is never itself reported as missing.
    assert FrameworkParentFamily.SYNTHESIZED_CHALLENGER not in missing_framework_parents(())


# --- ancestor challenge packet ---------------------------------------------


def _full_challenge(**overrides: object) -> AncestorChallenge:
    fields: dict[str, object] = dict(
        ancestor_fiber_id="parent",
        challenge_evidence_digest="digest",
        failed_local_repair_families=("reparameterize", "recondition"),
        dependent_descendant_ids=("child-a", "child-b"),
        child_fiber_id="child-a",
        residual_id="residual-1",
        local_causes_tested=(AuditCoordinate.ATOM, AuditCoordinate.MEASUREMENT),
        fresh_evidence_epochs=("epoch-2",),
        parent_coordinate_implicated=AuditCoordinate.FRAMEWORK,
        local_vs_parent_discriminator_id="disc-1",
        cost=7,
    )
    fields.update(overrides)
    return AncestorChallenge(**fields)  # type: ignore[arg-type]


def test_packet_is_incomplete_until_every_required_field_is_present() -> None:
    assert _full_challenge().packet_complete is True
    for missing, empty in (
        ("child_fiber_id", ""),
        ("residual_id", ""),
        ("local_causes_tested", ()),
        ("fresh_evidence_epochs", ()),
        ("parent_coordinate_implicated", None),
        ("local_vs_parent_discriminator_id", ""),
    ):
        assert _full_challenge(**{missing: empty}).packet_complete is False


def test_escalation_needs_the_discriminator_not_just_repeated_failure() -> None:
    # Two distinct failed local repair families satisfy the frozen rule the
    # decision chain reads, but without the parent-discriminating witness the
    # packet is not admissible for escalation.
    no_discriminator = _full_challenge(local_vs_parent_discriminator_id="")
    assert no_discriminator.admissible_for_ascent is True
    assert no_discriminator.escalation_admissible is False

    assert _full_challenge().escalation_admissible is True

    one_family = _full_challenge(failed_local_repair_families=("reparameterize",))
    assert one_family.admissible_for_ascent is False
    assert one_family.escalation_admissible is False


def test_supersession_carries_the_whole_packet_and_stales_descendants() -> None:
    challenge = _full_challenge()
    superseded = challenge.with_supersession()
    assert superseded.supersession_registered is True
    assert superseded.packet_complete is True
    for field in (
        "child_fiber_id",
        "residual_id",
        "local_causes_tested",
        "fresh_evidence_epochs",
        "parent_coordinate_implicated",
        "local_vs_parent_discriminator_id",
        "cost",
        "challenge_evidence_digest",
        "dependent_descendant_ids",
    ):
        assert getattr(superseded, field) == getattr(challenge, field)

    assert challenge.descendant_closure_stale("child-a") is False
    assert superseded.descendant_closure_stale("child-a") is True
    assert superseded.descendant_closure_stale("unrelated") is False
    assert superseded.grants_scientific_authority is False


def test_challenge_still_rejects_duplicate_families_and_missing_evidence() -> None:
    with pytest.raises(ValueError, match="distinct"):
        _full_challenge(failed_local_repair_families=("same", "same"))
    with pytest.raises(ValueError, match="requires evidence"):
        _full_challenge(challenge_evidence_digest="")
