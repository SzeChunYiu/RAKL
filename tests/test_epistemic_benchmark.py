from rakl.epistemic_benchmark import (
    AgentRunRecord,
    AuthorityLevel,
    ClaimDecision,
    EpistemicTaskWorld,
    EvidenceAccess,
    EvidenceTopology,
    FailureClass,
    evaluate_run,
)


def world(failure_class: FailureClass, **kwargs) -> EpistemicTaskWorld:
    defaults = dict(
        task_id=f"task-{failure_class.value.lower()}",
        failure_class=failure_class,
        topology=EvidenceTopology.CONTRADICTION_RICH,
        context_id="target-context",
        target_qoi="target-qoi",
        evidence_ids=("e1", "e2", "e3"),
        independent_evidence_roots=("e1", "e3"),
        mandatory_evidence_ids=("e1",),
        protected_evaluator_id="frozen-evaluator",
    )
    defaults.update(kwargs)
    return EpistemicTaskWorld(**defaults)


def run_for(w: EpistemicTaskWorld, **kwargs) -> AgentRunRecord:
    defaults = dict(
        run_id="run-1",
        task_id=w.task_id,
        architecture_id="test-arm",
        evidence_access=EvidenceAccess.COMPLETE_SEALED,
        evidence_seen_ids=w.evidence_ids,
        independent_root_ids_claimed=w.independent_evidence_roots,
        claims=(),
        negative_history_retained=w.negative_history_ids,
        evaluator_id_used=w.protected_evaluator_id,
        discovered_mechanism_ids=(() if w.hidden_mechanism_id is None else (w.hidden_mechanism_id,)),
    )
    defaults.update(kwargs)
    return AgentRunRecord(**defaults)


def test_prediction_evidence_cannot_mint_mechanism_authority() -> None:
    w = world(FailureClass.PREDICTION_TO_MECHANISM)
    claim = ClaimDecision(
        claim_id="c",
        authority=AuthorityLevel.MECHANISM,
        context_id=w.context_id,
        qoi=w.target_qoi,
        evidence_ids=("e1",),
        mechanism_id="m1",
    )
    metrics = evaluate_run(w, run_for(w, claims=(claim,)))
    assert metrics.unsupported_authority_upgrades == 1
    assert "unsupported_authority_upgrade" in metrics.blocking_failures


def test_mechanism_does_not_imply_unique_identification() -> None:
    w = world(FailureClass.MECHANISM_TO_IDENTIFICATION)
    claim = ClaimDecision(
        claim_id="c",
        authority=AuthorityLevel.IDENTIFICATION,
        context_id=w.context_id,
        qoi=w.target_qoi,
        evidence_ids=("e1",),
        identified=True,
    )
    assert evaluate_run(w, run_for(w, claims=(claim,))).unsupported_authority_upgrades == 1


def test_shared_lineage_cannot_be_counted_as_new_independent_roots() -> None:
    w = world(FailureClass.EVIDENCE_LINEAGE_DUPLICATION)
    metrics = evaluate_run(
        w,
        run_for(w, independent_root_ids_claimed=("e1", "e2", "e3", "invented-root")),
    )
    assert metrics.lineage_inflation > 0


def test_negative_history_loss_is_blocking_for_registered_failure_class() -> None:
    w = world(FailureClass.NEGATIVE_HISTORY_ERASURE, negative_history_ids=("failed-route-1",))
    metrics = evaluate_run(w, run_for(w, negative_history_retained=()))
    assert metrics.negative_history_losses == 1
    assert "negative_history_loss" in metrics.blocking_failures


def test_evaluator_capture_is_blocking() -> None:
    w = world(FailureClass.EVALUATOR_CAPTURE)
    metrics = evaluate_run(w, run_for(w, evaluator_id_used="candidate-controlled"))
    assert metrics.evaluator_capture_violations == 1
    assert "evaluator_capture" in metrics.blocking_failures


def test_mandatory_evidence_omission_is_blocking() -> None:
    w = world(FailureClass.MANDATORY_EVIDENCE_OMISSION, mandatory_evidence_ids=("e1", "e2"))
    metrics = evaluate_run(w, run_for(w, evidence_seen_ids=("e1", "e3")))
    assert metrics.mandatory_evidence_omissions == 1
    assert "mandatory_evidence_omission" in metrics.blocking_failures


def test_hidden_function_discovery_can_be_scored_without_name_leakage() -> None:
    w = world(FailureClass.ONTOLOGY_DISCOVERY_MISS, hidden_mechanism_id="hidden-mechanism")
    miss = evaluate_run(w, run_for(w, discovered_mechanism_ids=()))
    hit = evaluate_run(w, run_for(w, discovered_mechanism_ids=("hidden-mechanism",)))
    assert miss.hidden_mechanism_miss == 1
    assert hit.hidden_mechanism_miss == 0


def test_context_and_qoi_are_scored_separately_from_answer_fluency() -> None:
    w = world(FailureClass.ESTIMAND_MISMATCH, expected_qoi="future-displacement")
    claim = ClaimDecision(
        claim_id="c",
        authority=AuthorityLevel.PREDICTION,
        context_id=w.context_id,
        qoi="current-price",
        evidence_ids=("e1",),
    )
    metrics = evaluate_run(w, run_for(w, claims=(claim,)))
    assert metrics.context_or_qoi_errors == 1


def test_valid_run_can_have_nonzero_cost_without_epistemic_failure() -> None:
    w = world(FailureClass.CONTEXT_MISMATCH)
    claim = ClaimDecision(
        claim_id="c",
        authority=AuthorityLevel.REPRESENTATION,
        context_id=w.context_id,
        qoi=w.target_qoi,
        evidence_ids=("e1",),
    )
    record = run_for(w, claims=(claim,), input_tokens=100, preprocess_tokens=50)
    metrics = evaluate_run(w, record)
    assert metrics.valid
    assert record.total_tokens == 150
