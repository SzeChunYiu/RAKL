from __future__ import annotations

from dataclasses import replace
from hashlib import sha256

import pytest

from rakl.experience_benchmark import (
    ExperienceBenchmarkArm,
    ExperienceBenchmarkPacket,
    ExperienceBenchmarkPhase,
    ExperienceBenchmarkRun,
    ExperienceBenchmarkVerdict,
    assess_experience_benchmark,
    benchmark_protocol_subject_hash,
    benchmark_result_subject_hash,
)
from rakl.matched_microtrial import MatchedModelConfig, TrialResourceCeiling, TrialResourceUsage
from rakl.v3_authority import (
    AttestationPurpose,
    AuthorityTrustPolicy,
    EvidenceArtifact,
    ProtectedAuthorityContext,
    issue_protected_attestation,
)


KEY = b"benchmark-protected-evaluator-key-material"
SIGNER = "benchmark-evaluator"


def _artifact(artifact_id: str, payload: bytes, at: str, producer: str = "benchmark-owner") -> EvidenceArtifact:
    return EvidenceArtifact(artifact_id, payload, sha256(payload).hexdigest(), at, producer)


def _usage() -> TrialResourceUsage:
    return TrialResourceUsage(
        model_input_tokens=100,
        model_output_tokens=20,
        preprocessing_model_tokens=40,
        preprocessing_tool_calls=2,
        external_retrieval_calls=1,
        wall_time_ms=1000,
    )


def _run(
    run_id: str,
    task_id: str,
    arm: ExperienceBenchmarkArm,
    phase: ExperienceBenchmarkPhase,
    before: str,
    after: str,
    *,
    success: bool,
    score: float,
    failure: tuple[str, ...] = (),
) -> ExperienceBenchmarkRun:
    output = f"output:{run_id}".encode()
    return ExperienceBenchmarkRun(
        run_id=run_id,
        task_id=task_id,
        arm=arm,
        phase=phase,
        state_before_hash=before,
        state_after_hash=after,
        success=success,
        score=score,
        failure_signature=failure,
        resource_usage=_usage(),
        output_hash=sha256(output).hexdigest(),
        output_artifact_id=f"output:{run_id}",
        executed_at="2026-08-11T09:00:00+00:00",
    )


def _packet() -> tuple[ExperienceBenchmarkPacket, ProtectedAuthorityContext]:
    model = MatchedModelConfig(
        model_id="model-x",
        model_revision="rev-1",
        temperature=0.0,
        max_output_tokens=100,
        seed=7,
        system_prompt="frozen prompt",
    )
    ceiling = TrialResourceCeiling(
        max_model_input_tokens=1000,
        max_model_output_tokens=100,
        max_preprocessing_model_tokens=1000,
        max_preprocessing_tool_calls=10,
        max_external_retrieval_calls=10,
        max_wall_time_ms=10000,
    )
    evaluator = _artifact("evaluator", b"evaluator-v1", "2026-08-11T08:00:00+00:00", SIGNER)
    tool = _artifact("tool-policy", b"tools-frozen", "2026-08-11T08:00:00+00:00")
    schema = _artifact("output-schema", b"output-v1", "2026-08-11T08:00:00+00:00")
    tasks = tuple(
        _artifact(f"task:{task_id}", f"task-bytes:{task_id}".encode(), "2026-08-11T08:00:00+00:00")
        for task_id in ("D1", "D2", "T1", "T2")
    )
    runs = (
        _run("b-d1", "D1", ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE, "S0", "S0", success=False, score=0.2, failure=("repeat",)),
        _run("l-d1", "D1", ExperienceBenchmarkArm.LEARNING_ENABLED, ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE, "S0", "S1", success=False, score=0.3, failure=("repeat",)),
        _run("b-d2", "D2", ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE, "S0", "S0", success=False, score=0.2, failure=("repeat",)),
        _run("l-d2", "D2", ExperienceBenchmarkArm.LEARNING_ENABLED, ExperienceBenchmarkPhase.DEVELOPMENT_SEQUENCE, "S1", "S2", success=True, score=0.8),
        _run("b-t1", "T1", ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkPhase.FRESH_TRANSFER, "S0", "S0", success=False, score=0.2, failure=("transfer-a",)),
        _run("l-t1", "T1", ExperienceBenchmarkArm.LEARNING_ENABLED, ExperienceBenchmarkPhase.FRESH_TRANSFER, "S2", "T1-result", success=True, score=0.9),
        _run("b-t2", "T2", ExperienceBenchmarkArm.RESET_BASELINE, ExperienceBenchmarkPhase.FRESH_TRANSFER, "S0", "S0", success=False, score=0.3, failure=("transfer-a",)),
        _run("l-t2", "T2", ExperienceBenchmarkArm.LEARNING_ENABLED, ExperienceBenchmarkPhase.FRESH_TRANSFER, "S2", "T2-result", success=True, score=0.8),
    )
    outputs = tuple(
        _artifact(run.output_artifact_id, f"output:{run.run_id}".encode(), run.executed_at)
        for run in runs
    )
    packet = ExperienceBenchmarkPacket(
        benchmark_id="experience-v3-1",
        model=model,
        resource_ceiling=ceiling,
        tool_policy_id="tools-frozen",
        output_schema_id="output-v1",
        evaluator_protocol_hash=evaluator.payload_sha256,
        initial_state_hash="S0",
        development_task_ids=("D1", "D2"),
        transfer_task_ids=("T1", "T2"),
        learned_state_after_development_hash="S2",
        frozen_before_runs=True,
        runs=runs,
        evaluator_artifact_id=evaluator.artifact_id,
        tool_policy_artifact_id=tool.artifact_id,
        output_schema_artifact_id=schema.artifact_id,
        task_artifact_ids=tuple((task_id, f"task:{task_id}") for task_id in ("D1", "D2", "T1", "T2")),
        packet_frozen_at="2026-08-11T08:10:00+00:00",
        freeze_attestation_id="freeze",
        match_attestation_id="match",
    )
    protocol_artifacts = (evaluator, tool, schema) + tasks
    freeze = issue_protected_attestation(
        attestation_id="freeze",
        purpose=AttestationPurpose.BENCHMARK_FREEZE,
        subject_hash=benchmark_protocol_subject_hash(packet),
        subject_frozen_at=packet.packet_frozen_at,
        evaluator_artifact_id=evaluator.artifact_id,
        evaluator_artifact_sha256=evaluator.payload_sha256,
        evidence_bindings=tuple((item.artifact_id, item.payload_sha256) for item in protocol_artifacts),
        proposer_id="benchmark-candidate",
        signer_id=SIGNER,
        issued_at="2026-08-11T08:20:00+00:00",
        verdict="PASS",
        signing_key=KEY,
    )
    match = issue_protected_attestation(
        attestation_id="match",
        purpose=AttestationPurpose.BENCHMARK_MATCH,
        subject_hash=benchmark_result_subject_hash(packet),
        subject_frozen_at="2026-08-11T09:00:00+00:00",
        evaluator_artifact_id=evaluator.artifact_id,
        evaluator_artifact_sha256=evaluator.payload_sha256,
        evidence_bindings=tuple((item.artifact_id, item.payload_sha256) for item in protocol_artifacts + outputs),
        proposer_id="benchmark-candidate",
        signer_id=SIGNER,
        issued_at="2026-08-11T09:10:00+00:00",
        verdict="PASS",
        signing_key=KEY,
    )
    return packet, ProtectedAuthorityContext(
        artifacts=protocol_artifacts + outputs,
        attestations=(freeze, match),
        policy=AuthorityTrustPolicy(((SIGNER, KEY),)),
    )


def test_matched_experience_benchmark_measures_learning_and_transfer() -> None:
    packet, context = _packet()
    report = assess_experience_benchmark(packet, context)
    assert report.verdict is ExperienceBenchmarkVerdict.VALID_MEASUREMENT
    assert report.validation.matched
    assert report.development_success_delta == 0.5
    assert report.transfer_success_delta == 1.0
    assert report.transfer_score_delta == pytest.approx(0.6)
    assert report.transfer_repeat_failure_delta == pytest.approx(-0.5)
    # With only 2 transfer tasks, inference returns INSUFFICIENT_N (bootstrap unstable)
    # This is correct edge-case behavior; the inference module is separately tested.
    assert report.transfer_success_inference_status.value == "INSUFFICIENT_N"
    assert report.transfer_score_inference_status.value == "INSUFFICIENT_N"
    assert report.transfer_success_excludes_null is False
    assert report.transfer_score_excludes_null is False
    # INSUFFICIENT_N means transfer_gain_observed is False (cannot distinguish)
    assert not report.transfer_gain_observed
    assert not report.grants_global_capability_claim


def test_fresh_transfer_cannot_learn_from_previous_transfer_case() -> None:
    packet, context = _packet()
    runs = tuple(
        replace(run, state_before_hash="T1-result")
        if run.run_id == "l-t2"
        else run
        for run in packet.runs
    )
    contaminated = replace(packet, runs=runs)
    report = assess_experience_benchmark(contaminated, context)
    assert report.verdict is ExperienceBenchmarkVerdict.INVALID
    assert not report.validation.matched
    assert any("fresh_transfer_not_started_from_frozen_learned_state:l-t2" == item for item in report.validation.problems)


def test_labels_and_booleans_cannot_claim_frozen_or_matched_without_receipts() -> None:
    packet, _ = _packet()
    report = assess_experience_benchmark(replace(packet, frozen_before_runs=True))
    assert report.verdict is ExperienceBenchmarkVerdict.INVALID
    assert any("resolved_protected_attestation_missing" in item for item in report.validation.problems)


def test_experience_benchmark_inference_surfaced_for_insufficient_n() -> None:
    """Verify that INSUFFICIENT_N status is correctly surfaced to the report.

    The inference module's bootstrap/perm logic is fully tested in test_inference.py.
    This test verifies that experience_benchmark correctly propagates the edge-case
    status when n<3 transfer tasks are provided.
    """
    packet, context = _packet()
    report = assess_experience_benchmark(packet, context)
    # 2 transfer tasks should trigger INSUFFICIENT_N
    assert report.transfer_success_inference_status.value == "INSUFFICIENT_N"
    assert report.transfer_score_inference_status.value == "INSUFFICIENT_N"
    # INSUFFICIENT_N means excludes_null=False and transfer_gain_observed=False
    assert report.transfer_success_excludes_null is False
    assert report.transfer_score_excludes_null is False
    assert not report.transfer_gain_observed


def test_forged_output_bytes_and_posthoc_freeze_are_rejected() -> None:
    packet, context = _packet()
    first_output = next(item for item in context.artifacts if item.artifact_id == "output:b-d1")
    corrupted = replace(first_output, payload=b"different bytes")
    corrupt_context = replace(
        context,
        artifacts=tuple(corrupted if item.artifact_id == corrupted.artifact_id else item for item in context.artifacts),
    )
    corrupt_report = assess_experience_benchmark(packet, corrupt_context)
    assert corrupt_report.verdict is ExperienceBenchmarkVerdict.INVALID
    assert any("run_output_bytes_hash_mismatch:b-d1" == item for item in corrupt_report.validation.problems)

    posthoc_runs = tuple(replace(run, executed_at="2026-08-11T08:00:00+00:00") for run in packet.runs)
    posthoc = replace(packet, runs=posthoc_runs)
    posthoc_report = assess_experience_benchmark(posthoc, context)
    assert posthoc_report.verdict is ExperienceBenchmarkVerdict.INVALID
    assert any("run_not_after_frozen_packet" in item for item in posthoc_report.validation.problems)
