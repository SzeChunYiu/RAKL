from __future__ import annotations

from rakl.research_cycle import (
    ResearchArtifactRef,
    ResearchStage,
    ResearchStep,
    StorageTier,
    TraceVerdict,
    stage_contracts,
    validate_research_trace,
    validate_stage_contracts,
)


def _full_trace():
    artifacts = []
    steps = []
    previous = None
    for index, contract in enumerate(stage_contracts()):
        output_id = f"a{index:02d}"
        artifacts.append(
            ResearchArtifactRef(
                artifact_id=output_id,
                kind=contract.typed_outputs[0],
                storage_tier=contract.storage_tier,
                canonical=contract.storage_tier is StorageTier.TIER0_CANONICAL_ARCHIVE,
            )
        )
        steps.append(
            ResearchStep(
                step_id=f"s{index:02d}",
                cycle_index=0,
                stage=contract.stage,
                input_ids=() if previous is None else (previous,),
                output_ids=(output_id,),
                llm_used=contract.llm_may_propose,
                external_verification_observed=(True if contract.external_verification_required else False),
                mandatory_context_complete=(True if contract.stage is ResearchStage.COMPILE_WORKING_CONTEXT else None),
                token_cost=(64 if contract.llm_may_propose else 0),
            )
        )
        previous = output_id
    return tuple(artifacts), tuple(steps)


def test_all_atomic_stage_contracts_are_complete():
    assert validate_stage_contracts() == ()
    assert len(stage_contracts()) == len(ResearchStage) == 17


def test_full_atomic_research_trace_is_valid():
    artifacts, steps = _full_trace()
    report = validate_research_trace(artifacts, steps)
    assert report.verdict is TraceVerdict.VALID_SCOPED_TRACE
    assert report.total_llm_tokens > 0
    assert dict(report.stage_counts)[ResearchStage.CANONICAL_UPDATE.value] == 1
    assert not report.grants_scientific_truth
    assert not report.grants_independent_review_credit


def test_canonical_update_without_prior_verification_fails():
    artifacts, steps = _full_trace()
    steps = tuple(step for step in steps if step.stage is not ResearchStage.VERIFY_PROPOSAL)
    report = validate_research_trace(artifacts, steps)
    assert report.verdict is TraceVerdict.INVALID_TRACE
    assert any("canonical_update_without_prior_verification" in reason for reason in report.reasons)


def test_llm_cannot_be_used_as_ingest_authority():
    artifacts, steps = _full_trace()
    poisoned = []
    for step in steps:
        if step.stage is ResearchStage.INGEST_EVIDENCE:
            step = ResearchStep(
                step_id=step.step_id,
                cycle_index=step.cycle_index,
                stage=step.stage,
                input_ids=step.input_ids,
                output_ids=step.output_ids,
                llm_used=True,
                external_verification_observed=step.external_verification_observed,
                token_cost=10,
            )
        poisoned.append(step)
    report = validate_research_trace(artifacts, tuple(poisoned))
    assert report.verdict is TraceVerdict.INVALID_TRACE
    assert any("llm_used_in_nonproposal_stage" in reason for reason in report.reasons)


def test_missing_mandatory_context_fails_closed():
    artifacts, steps = _full_trace()
    poisoned = []
    for step in steps:
        if step.stage is ResearchStage.COMPILE_WORKING_CONTEXT:
            step = ResearchStep(
                step_id=step.step_id,
                cycle_index=step.cycle_index,
                stage=step.stage,
                input_ids=step.input_ids,
                output_ids=step.output_ids,
                llm_used=step.llm_used,
                external_verification_observed=step.external_verification_observed,
                mandatory_context_complete=False,
            )
        poisoned.append(step)
    report = validate_research_trace(artifacts, tuple(poisoned))
    assert report.verdict is TraceVerdict.INVALID_TRACE
    assert any("mandatory_context_incomplete" in reason for reason in report.reasons)


def test_lossy_view_requires_raw_rehydration_for_strong_authority():
    raw = ResearchArtifactRef(
        artifact_id="raw",
        kind="raw_source",
        storage_tier=StorageTier.TIER0_CANONICAL_ARCHIVE,
        canonical=True,
    )
    summary = ResearchArtifactRef(
        artifact_id="summary",
        kind="lossy_summary",
        storage_tier=StorageTier.TIER1_REBUILDABLE_VIEW,
        source_ids=("raw",),
        lossy=True,
        erasure_tags=("verbatim_detail",),
    )
    report_artifact = ResearchArtifactRef(
        artifact_id="verification",
        kind="verification_report",
        storage_tier=StorageTier.TIER0_CANONICAL_ARCHIVE,
        canonical=True,
    )
    step = ResearchStep(
        step_id="verify",
        cycle_index=0,
        stage=ResearchStage.VERIFY_PROPOSAL,
        input_ids=("summary",),
        output_ids=("verification",),
        llm_used=False,
        external_verification_observed=True,
        strong_authority_operation=True,
        raw_evidence_rehydrated=False,
    )
    report = validate_research_trace((raw, summary, report_artifact), (step,), require_full_cycle=False)
    assert report.verdict is TraceVerdict.INVALID_TRACE
    assert any("lossy_view_used_without_rehydration" in reason for reason in report.reasons)
