from rakl.engineering_deployment import (
    BackendCapabilities,
    DeploymentMode,
    EngineeringSupportProfile,
    SupportVerdict,
    assess_engineering_support,
)
from rakl.engineering_telemetry import OperationalCorrelationContext


def test_operational_context_is_correlated_but_authority_neutral():
    ctx = OperationalCorrelationContext(
        project_id="p",
        snapshot_id="s",
        workflow_id="w",
        activity_id="a",
        controller_decision_id="d",
    )
    assert ctx.attributes()["orion.snapshot.id"] == "s"
    assert "orion.episode.id" not in ctx.attributes()
    assert not ctx.grants_scientific_authority


def profile():
    return EngineeringSupportProfile(
        profile_id="prod:multi-host",
        mode=DeploymentMode.MULTI_HOST,
        max_concurrent_workers=8,
        requires_shared_blob_store=True,
        requires_serializable_metadata=True,
        requires_durable_workflow_history=True,
        requires_point_in_time_recovery=True,
        requires_authz=True,
        requires_build_attestation=True,
        external_effect_classes=("LLM_PROVIDER", "GITHUB_WRITE"),
    )


def test_support_first_gate_rejects_reference_backend_for_multi_host():
    caps = BackendCapabilities(
        backend_id="sqlite+localfs",
        multi_process_safe=True,
        multi_host_safe=False,
        shared_blob_store=False,
        serializable_metadata=False,
        durable_workflow_history=False,
        point_in_time_recovery=False,
        authz=None,
        build_attestation=None,
    )
    result = assess_engineering_support(profile(), caps)
    assert result.verdict is SupportVerdict.UNSUPPORTED
    assert "multi_host_safe" in result.missing


def test_support_gate_cannot_check_unknown_required_coordinates():
    caps = BackendCapabilities(
        backend_id="candidate",
        multi_process_safe=True,
        multi_host_safe=True,
        shared_blob_store=True,
        serializable_metadata=True,
        durable_workflow_history=True,
        point_in_time_recovery=True,
        authz=None,
        build_attestation=True,
    )
    result = assess_engineering_support(profile(), caps)
    assert result.verdict is SupportVerdict.CANNOT_CHECK
    assert result.unknown == ("authz",)


def test_support_profile_rejects_parallel_single_process_and_untracked_external_effects():
    import pytest
    with pytest.raises(ValueError, match="exactly one worker"):
        EngineeringSupportProfile(
            "bad", DeploymentMode.SINGLE_PROCESS, 2, False, False, False, False, False, False
        )
    with pytest.raises(ValueError, match="durable workflow"):
        EngineeringSupportProfile(
            "bad-effects", DeploymentMode.SINGLE_PROCESS, 1, False, False, False, False, False, False,
            external_effect_classes=("MODEL_PROVIDER",),
        )
