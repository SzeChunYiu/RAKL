"""Frozen development worlds for the proposal-shadow co-witness challenger.

These synthetic worlds implement QCB-DEV-20260812-v1. They are development
conformance checks, not fresh assurance and not mathematical proof evidence.
"""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema

from rakl.quantifier_cowitness import (
    BinderOccurrence,
    CoWitnessConsumer,
    CoWitnessReview,
    CoWitnessVerdict,
    IdentityRelation,
    JointWitnessObligation,
    QuantifierKind,
    RelationKind,
    audit_cowitness_review,
)

SCHEMAS = Path(__file__).resolve().parents[1] / "schemas"
STAMP = "2026-08-12T17:05:00Z"


def _occ(
    occurrence_id: str,
    binder_id: str,
    symbol: str,
    role: str,
    *,
    scope_id: str = "scope:lemma",
    object_type: str = "positive-real",
) -> BinderOccurrence:
    return BinderOccurrence(
        occurrence_id=occurrence_id,
        binder_id=binder_id,
        display_symbol=symbol,
        quantifier=QuantifierKind.EXISTS,
        scope_id=scope_id,
        object_type=object_type,
        role=role,
        evidence_pointers=(f"evidence:{occurrence_id}",),
    )


def _obligation(*ids: str) -> JointWitnessObligation:
    return JointWitnessObligation(
        obligation_id="joint:" + ":".join(ids),
        occurrence_ids=tuple(ids),
        conclusion_scope="scope:target-route",
        rationale="the target route substitutes one object into every listed role",
        evidence_pointers=("evidence:declared-joint-requirement",),
    )


def _review(
    occurrences: tuple[BinderOccurrence, ...],
    *,
    relations: tuple[IdentityRelation, ...] = (),
    obligations: tuple[JointWitnessObligation, ...] = (),
    activation_requested: bool = True,
    review_id: str = "QCB-review",
) -> CoWitnessReview:
    return CoWitnessReview(
        review_id=review_id,
        atom_id="atom:synthetic-cowitness",
        occurrences=occurrences,
        identity_relations=relations,
        joint_obligations=obligations,
        activation_requested=activation_requested,
        evidence_pointers=("evidence:frozen-development-world",),
        recorded_at_utc=STAMP,
    )


def _audit(review: CoWitnessReview):
    return audit_cowitness_review(
        review,
        expected_atom_id="atom:synthetic-cowitness",
        consumer=CoWitnessConsumer.LOCAL_TO_GLOBAL_GLUING,
        claimed_review_hash=review.review_canonical_sha256,
    )


def test_dev_same_witness_multirole_passes() -> None:
    review = _review(
        (
            _occ("o-radius", "binder:one", "c", "domain-radius"),
            _occ("o-coeff", "binder:one", "c", "forcing-coefficient"),
        ),
        obligations=(_obligation("o-radius", "o-coeff"),),
    )
    result = _audit(review)
    assert result.verdict is CoWitnessVerdict.PASS
    assert result.activated is True
    assert result.grants_gluing_authority is True
    assert result.grants_theorem_authority is False


def test_dev_separate_witnesses_incorrectly_glued_fails() -> None:
    left = _occ("o-left", "binder:left", "a", "domain-threshold", scope_id="scope:left")
    right = _occ("o-right", "binder:right", "b", "response-threshold", scope_id="scope:right")
    review = _review(
        (left, right),
        relations=(
            IdentityRelation(
                relation_id="rel:distinct",
                left_occurrence_id=left.occurrence_id,
                right_occurrence_id=right.occurrence_id,
                kind=RelationKind.DISTINCT_BINDERS,
                evidence_pointers=("evidence:separate-existential-binders",),
            ),
        ),
        obligations=(_obligation("o-left", "o-right"),),
    )
    result = _audit(review)
    assert result.verdict is CoWitnessVerdict.FAIL
    assert "joint_obligation_contains_distinct_binders" in result.reasons


def test_dev_alpha_renamed_equivalent_witness_passes() -> None:
    left = _occ("o-x", "binder:source-x", "x", "cutoff")
    right = _occ("o-y", "binder:normalized-y", "y", "cutoff")
    review = _review(
        (left, right),
        relations=(
            IdentityRelation(
                relation_id="rel:alpha",
                left_occurrence_id="o-x",
                right_occurrence_id="o-y",
                kind=RelationKind.ALPHA_RENAMED_SAME_BINDER,
                evidence_pointers=("evidence:capture-avoiding-alpha-map",),
            ),
        ),
        obligations=(_obligation("o-x", "o-y"),),
    )
    assert _audit(review).verdict is CoWitnessVerdict.PASS


def test_dev_compatible_same_role_reuse_passes() -> None:
    review = _review(
        (
            _occ("o-first", "binder:shared", "r", "radius"),
            _occ("o-second", "binder:shared", "r", "radius"),
        ),
        obligations=(_obligation("o-first", "o-second"),),
    )
    assert _audit(review).verdict is CoWitnessVerdict.PASS


def test_dev_same_symbol_independent_constants_fail() -> None:
    left = _occ("o-C1", "binder:statement-1", "C", "upper-bound", scope_id="scope:statement-1")
    right = _occ("o-C2", "binder:statement-2", "C", "lower-bound", scope_id="scope:statement-2")
    review = _review(
        (left, right),
        relations=(
            IdentityRelation(
                relation_id="rel:same-glyph-distinct",
                left_occurrence_id="o-C1",
                right_occurrence_id="o-C2",
                kind=RelationKind.DISTINCT_BINDERS,
                evidence_pointers=("evidence:independent-quantifier-scopes",),
            ),
        ),
        obligations=(_obligation("o-C1", "o-C2"),),
    )
    result = _audit(review)
    assert result.verdict is CoWitnessVerdict.FAIL
    assert "same_display_symbol_is_not_identity_evidence" in result.reasons


def test_dev_missing_identity_evidence_cannot_check() -> None:
    review = _review(
        (
            _occ("o-u", "binder:u", "u", "scale"),
            _occ("o-v", "binder:v", "v", "coefficient"),
        ),
        obligations=(_obligation("o-u", "o-v"),),
    )
    result = _audit(review)
    assert result.verdict is CoWitnessVerdict.CANNOT_CHECK
    assert result.grants_gluing_authority is False
    assert "joint_identity_not_established" in result.reasons


def test_dev_nonactivation_world_stays_inactive() -> None:
    review = _review(
        (
            _occ("o-independent-1", "binder:i1", "C", "bound", scope_id="scope:claim-1"),
            _occ("o-independent-2", "binder:i2", "C", "bound", scope_id="scope:claim-2"),
        ),
        activation_requested=False,
        obligations=(),
    )
    result = _audit(review)
    assert result.verdict is CoWitnessVerdict.PASS
    assert result.activated is False
    assert result.grants_gluing_authority is False
    assert result.reasons == ("joint_witness_review_not_activated",)


def test_unknown_relation_cannot_check_and_conflicting_identity_fails() -> None:
    left = _occ("o-a", "binder:a", "a", "scale")
    right = _occ("o-b", "binder:b", "b", "coefficient")
    unknown = _review(
        (left, right),
        relations=(
            IdentityRelation(
                relation_id="rel:unknown",
                left_occurrence_id="o-a",
                right_occurrence_id="o-b",
                kind=RelationKind.UNKNOWN,
                evidence_pointers=("evidence:identity-unresolved",),
            ),
        ),
        obligations=(_obligation("o-a", "o-b"),),
    )
    assert _audit(unknown).verdict is CoWitnessVerdict.CANNOT_CHECK

    conflicting = _review(
        (left, right),
        relations=(
            IdentityRelation("rel:same", "o-a", "o-b", RelationKind.SAME_WITNESS, ("evidence:same",)),
            IdentityRelation("rel:different", "o-a", "o-b", RelationKind.DISTINCT_BINDERS, ("evidence:different",)),
        ),
        obligations=(_obligation("o-a", "o-b"),),
    )
    assert _audit(conflicting).verdict is CoWitnessVerdict.FAIL


def test_distinctness_propagates_through_identity_closure() -> None:
    """A != B and B == C entail A != C for a requested co-witness."""

    a = _occ("o-a-closure", "binder:a-closure", "k", "domain-radius")
    b = _occ("o-b-closure", "binder:b-closure", "b", "intermediate-role")
    c = _occ("o-c-closure", "binder:c-closure", "k", "forcing-coefficient")
    review = _review(
        (a, b, c),
        relations=(
            IdentityRelation(
                "rel:a-distinct-b",
                a.occurrence_id,
                b.occurrence_id,
                RelationKind.DISTINCT_BINDERS,
                ("evidence:a-and-b-are-independent",),
            ),
            IdentityRelation(
                "rel:b-alpha-c",
                b.occurrence_id,
                c.occurrence_id,
                RelationKind.ALPHA_RENAMED_SAME_BINDER,
                ("evidence:b-to-c-alpha-renaming",),
            ),
        ),
        obligations=(_obligation(a.occurrence_id, c.occurrence_id),),
    )
    result = _audit(review)
    assert result.verdict is CoWitnessVerdict.FAIL
    assert "joint_obligation_contains_distinct_binders" in result.reasons
    assert "same_display_symbol_is_not_identity_evidence" in result.reasons


def test_known_nonexistential_failure_dominates_unknown_quantifier() -> None:
    """UNKNOWN cannot mask a definitive FORALL obstruction."""

    unknown = _occ("o-unknown-q", "binder:mixed-q", "q", "unknown-role")
    universal = _occ("o-forall-q", "binder:mixed-q", "q", "universal-role")
    unknown = BinderOccurrence(
        **{**unknown.__dict__, "quantifier": QuantifierKind.UNKNOWN}
    )
    universal = BinderOccurrence(
        **{**universal.__dict__, "quantifier": QuantifierKind.FORALL}
    )
    review = _review(
        (unknown, universal),
        obligations=(_obligation(unknown.occurrence_id, universal.occurrence_id),),
    )
    result = _audit(review)
    assert result.verdict is CoWitnessVerdict.FAIL
    assert "joint_obligation_quantifier_unknown" in result.reasons
    assert "joint_obligation_requires_existential_occurrences" in result.reasons


def test_type_mismatch_fails_even_when_identity_is_asserted() -> None:
    review = _review(
        (
            _occ("o-real", "binder:shared", "z", "radius", object_type="positive-real"),
            _occ("o-int", "binder:shared", "z", "index", object_type="natural-number"),
        ),
        obligations=(_obligation("o-real", "o-int"),),
    )
    result = _audit(review)
    assert result.verdict is CoWitnessVerdict.FAIL
    assert "joint_obligation_object_type_mismatch" in result.reasons


def test_missing_stale_identity_and_theorem_consumers_fail_closed() -> None:
    missing = audit_cowitness_review(
        None,
        expected_atom_id="atom:synthetic-cowitness",
        consumer=CoWitnessConsumer.REVIEW,
    )
    assert missing.verdict is CoWitnessVerdict.CANNOT_CHECK

    review = _review(
        (_occ("o-one", "binder:one", "x", "role-1"), _occ("o-two", "binder:one", "x", "role-2")),
        obligations=(_obligation("o-one", "o-two"),),
    )
    stale = audit_cowitness_review(
        review,
        expected_atom_id=review.atom_id,
        consumer=CoWitnessConsumer.REVIEW,
        claimed_review_hash="0" * 64,
    )
    assert stale.verdict is CoWitnessVerdict.CANNOT_CHECK

    theorem = audit_cowitness_review(
        review,
        expected_atom_id=review.atom_id,
        consumer=CoWitnessConsumer.THEOREM_AUTHORITY,
    )
    assert theorem.verdict is CoWitnessVerdict.FAIL
    assert theorem.grants_theorem_authority is False


def test_document_hash_schema_and_preregistration_chronology() -> None:
    review = _review(
        (_occ("o-one", "binder:one", "x", "role-1"), _occ("o-two", "binder:one", "x", "role-2")),
        obligations=(_obligation("o-one", "o-two"),),
    )
    document = review.document()
    schema = json.loads((SCHEMAS / "quantifier-cowitness-review-v1.schema.json").read_text())
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(document, schema)
    assert document["authority_claim"] == "ROUTING_GLUING_ONLY_NOT_THEOREM"
    assert document["review_canonical_sha256"] == review.review_canonical_sha256

    prereg = json.loads(
        (
            Path(__file__).resolve().parents[1]
            / "research/self_rakl_upgrades/quantifier_cowitness_20260812/CLASS_B_PREREGISTRATION.json"
        ).read_text()
    )
    assert prereg["parent"]["main_sha"] == "d21592b0ff8da988deabb923fd549891ff8ad9f0"
    assert prereg["fresh_assurance_plan"]["status"].startswith("CANNOT_CHECK")
    assert prereg["candidate"]["implementation_mode"] == "PROPOSAL_SHADOW_COMPANION_NOT_PROTECTED_CONSUMER"
