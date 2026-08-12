from __future__ import annotations

from rakl.failure_lattice import (
    DifferenceWitness,
    FailureDiagnosisStatus,
    FailureExperience,
    FailureExperienceLattice,
    ObligationStrengthVerdict,
    RealizationDomain,
    ReuseVerdict,
    add_failure_experience,
    assess_method_reuse,
    assess_obligation_strength_claim,
    global_failure_portrait,
    query_related_failures,
)


def _failure(
    *,
    failure_id: str = "F1",
    atom_id: str = "A1",
    candidate_id: str = "C1",
    context_hash: str = "ctx-1",
    method_family: str = "spectral-ratio",
    diagnosis_status: FailureDiagnosisStatus = FailureDiagnosisStatus.SUPPORTED,
) -> FailureExperience:
    return FailureExperience(
        failure_id=failure_id,
        atom_id=atom_id,
        candidate_id=candidate_id,
        context_packet_hash=context_hash,
        research_trace_event_id=f"trace-{failure_id}",
        method_family=method_family,
        failure_mode="reuse defeats recomputation-charging measure",
        residual_signature=("reuse_gap", "unrestricted_DAG"),
        broken_assumptions=("tree_like_recomputation",),
        scope_conditions=("same unrestricted reuse model",),
        competing_diagnoses=("wrong invariant", "model mismatch"),
        selected_diagnosis="model mismatch",
        diagnosis_status=diagnosis_status,
        evidence_pointers=(f"artifact:{failure_id}",),
        falsifier_or_attempt="compare restricted lower bound with unrestricted upper construction",
        observed_result="restricted measure is asymptotically too large to transfer directly",
        artifact_hash=f"sha256:{failure_id}",
        timestamp="2026-08-11T04:00:00+00:00",
    )


def test_failure_experience_is_preserved_and_queryable() -> None:
    lattice = add_failure_experience(FailureExperienceLattice(), _failure())
    related = query_related_failures(
        lattice,
        method_family="spectral-ratio",
        residual_signature=("reuse_gap",),
    )
    assert tuple(item.failure_id for item in related) == ("F1",)
    portrait = global_failure_portrait(lattice)
    assert portrait["experience_count"] == 1
    assert portrait["method_family_counts"] == {"spectral-ratio": 1}


def test_ordinary_failure_is_warning_not_global_blacklist() -> None:
    lattice = add_failure_experience(FailureExperienceLattice(), _failure())
    assessment = assess_method_reuse(
        lattice,
        target_atom_id="A2",
        target_context_hash="ctx-2",
        method_family="spectral-ratio",
        relevant_failure_ids=("F1",),
        difference_witness=None,
    )
    assert assessment.verdict is ReuseVerdict.SAME_CONTEXT_RETRY
    assert assessment.verdict is not ReuseVerdict.GLOBALLY_BLOCKED_BY_VERIFIED_IMPOSSIBILITY


def test_difference_witness_allows_reuse_with_repeat_failure_test() -> None:
    lattice = add_failure_experience(FailureExperienceLattice(), _failure())
    witness = DifferenceWitness(
        target_atom_id="A2",
        target_context_hash="ctx-2",
        method_family="spectral-ratio",
        prior_failure_ids=("F1",),
        changed_structural_coordinates=("reuse budget is explicitly charged",),
        restored_or_replaced_assumptions=("tree-like recomputation replaced by bounded-fusion lemma",),
        prior_falsifier_escape_reason="the old counterexample used uncharged sharing",
        cheapest_repeat_failure_test="run the old sharing construction against the bounded-fusion candidate",
        evidence_pointers=("context:ctx-2",),
    )
    assessment = assess_method_reuse(
        lattice,
        target_atom_id="A2",
        target_context_hash="ctx-2",
        method_family="spectral-ratio",
        relevant_failure_ids=("F1",),
        difference_witness=witness,
    )
    assert assessment.verdict is ReuseVerdict.DIFFERENCE_WITNESSED


def test_only_verified_impossibility_can_block_same_registered_context() -> None:
    lattice = add_failure_experience(
        FailureExperienceLattice(),
        _failure(diagnosis_status=FailureDiagnosisStatus.VERIFIED_IMPOSSIBILITY),
    )
    assessment = assess_method_reuse(
        lattice,
        target_atom_id="A1",
        target_context_hash="ctx-1",
        method_family="spectral-ratio",
        relevant_failure_ids=("F1",),
        difference_witness=None,
    )
    assert assessment.verdict is ReuseVerdict.GLOBALLY_BLOCKED_BY_VERIFIED_IMPOSSIBILITY


def test_same_verified_impossibility_does_not_block_changed_context() -> None:
    lattice = add_failure_experience(
        FailureExperienceLattice(),
        _failure(diagnosis_status=FailureDiagnosisStatus.VERIFIED_IMPOSSIBILITY),
    )
    assessment = assess_method_reuse(
        lattice,
        target_atom_id="A2",
        target_context_hash="ctx-2",
        method_family="spectral-ratio",
        relevant_failure_ids=("F1",),
        difference_witness=DifferenceWitness(
            target_atom_id="A2",
            target_context_hash="ctx-2",
            method_family="spectral-ratio",
            prior_failure_ids=("F1",),
            changed_structural_coordinates=("new model",),
            restored_or_replaced_assumptions=("failed scope no longer applies",),
            prior_falsifier_escape_reason="context changed outside proved impossibility scope",
            cheapest_repeat_failure_test="instantiate old impossibility premises on new context",
            evidence_pointers=("context:ctx-2",),
        ),
    )
    assert assessment.verdict is ReuseVerdict.DIFFERENCE_WITNESSED


def _base_witness(**overrides: object) -> DifferenceWitness:
    payload = dict(
        target_atom_id="A-target",
        target_context_hash="ctx-target",
        method_family="obligation-strength",
        prior_failure_ids=("F-ambient",),
        changed_structural_coordinates=("hidden coordinate differs",),
        restored_or_replaced_assumptions=("target realizability explicit",),
        prior_falsifier_escape_reason="ambient non-identification is not target attainability",
        cheapest_repeat_failure_test="check whether the ambient pair embeds into the target theory",
        evidence_pointers=("artifact:witness",),
    )
    payload.update(overrides)
    return DifferenceWitness(**payload)  # type: ignore[arg-type]


def test_ambient_synthetic_pair_rejected_as_target_domain_attainability() -> None:
    """Case (1): same observed statistic, different hidden ambient coordinate."""
    witness = _base_witness(
        realization_domain=RealizationDomain.AMBIENT_REPRESENTATION,
        changed_structural_coordinates=(
            "two ambient objects share observed statistic S but differ on hidden coordinate H",
        ),
    )
    assessment = assess_obligation_strength_claim(witness)
    assert assessment.verdict is ObligationStrengthVerdict.REPRESENTATION_ONLY
    assert assessment.may_certify_target_obligation_weakening is False


def test_genuine_target_pair_accepted_for_obligation_strength() -> None:
    """Case (2): hostile pair realized inside the fixed target theory."""
    witness = _base_witness(
        realization_domain=RealizationDomain.TARGET_DOMAIN,
        changed_structural_coordinates=("target-theory hostile pair (x,y) with distinct QoI",),
    )
    assessment = assess_obligation_strength_claim(witness)
    assert assessment.verdict is ObligationStrengthVerdict.ACCEPTED_TARGET_DOMAIN
    assert assessment.may_certify_target_obligation_weakening is True


def test_transferred_pair_accepted_only_when_assumptions_bound() -> None:
    """Case (3): transfer accepted only with complete source→target binding."""
    incomplete = _base_witness(
        realization_domain=RealizationDomain.TRANSFERRED_WITH_WITNESS,
        transfer_source_context_hash="ctx-source",
        # deliberately omit mapping / assumptions / disanalogies
    )
    rejected = assess_obligation_strength_claim(incomplete)
    assert rejected.verdict is ObligationStrengthVerdict.REJECTED_INCOMPLETE_TRANSFER
    assert rejected.may_certify_target_obligation_weakening is False
    assert "transfer_assumptions_missing" in rejected.reasons

    complete = _base_witness(
        realization_domain=RealizationDomain.TRANSFERRED_WITH_WITNESS,
        transfer_source_context_hash="ctx-source",
        transfer_role_mapping=("source.x -> target.x", "source.y -> target.y"),
        transfer_shared_constraints=("same QoI signature", "same locality class"),
        transfer_disanalogies=("source allows ambient re-encoding; target forbids it",),
        transfer_assumptions=("embedding preserves falsifier polarity",),
    )
    accepted = assess_obligation_strength_claim(complete)
    assert accepted.verdict is ObligationStrengthVerdict.ACCEPTED_TRANSFERRED_WITH_WITNESS
    assert accepted.may_certify_target_obligation_weakening is True


def test_unspecified_realization_domain_is_cannot_check() -> None:
    assert assess_obligation_strength_claim(None).verdict is ObligationStrengthVerdict.CANNOT_CHECK
    assert (
        assess_obligation_strength_claim(_base_witness()).verdict
        is ObligationStrengthVerdict.CANNOT_CHECK
    )
    assert assess_obligation_strength_claim(None).may_certify_target_obligation_weakening is False


def test_ordinary_method_reuse_unaffected_by_missing_realization_domain() -> None:
    lattice = add_failure_experience(FailureExperienceLattice(), _failure())
    witness = DifferenceWitness(
        target_atom_id="A2",
        target_context_hash="ctx-2",
        method_family="spectral-ratio",
        prior_failure_ids=("F1",),
        changed_structural_coordinates=("reuse budget is explicitly charged",),
        restored_or_replaced_assumptions=("tree-like recomputation replaced by bounded-fusion lemma",),
        prior_falsifier_escape_reason="the old counterexample used uncharged sharing",
        cheapest_repeat_failure_test="run the old sharing construction against the bounded-fusion candidate",
        evidence_pointers=("context:ctx-2",),
    )
    assessment = assess_method_reuse(
        lattice,
        target_atom_id="A2",
        target_context_hash="ctx-2",
        method_family="spectral-ratio",
        relevant_failure_ids=("F1",),
        difference_witness=witness,
    )
    assert assessment.verdict is ReuseVerdict.DIFFERENCE_WITNESSED
    assert assess_obligation_strength_claim(witness).verdict is ObligationStrengthVerdict.CANNOT_CHECK
