from __future__ import annotations

from rakl.failure_lattice import (
    DifferenceWitness,
    FailureDiagnosisStatus,
    FailureExperience,
    FailureExperienceLattice,
    ReuseVerdict,
    add_failure_experience,
    assess_method_reuse,
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
