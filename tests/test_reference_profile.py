import pytest

from rakl.reference_profile import (
    ModelCapabilityDeclaration,
    ProfileVerdict,
    assess_reference_profile,
    get_reference_profile,
)


def test_ordinary_8k_passes_without_native_tool_calls():
    profile = get_reference_profile("ordinary-8k")
    report = assess_reference_profile(
        profile,
        ModelCapabilityDeclaration(
            model_id="ordinary-model",
            context_window_tokens=8192,
            instruction_following=True,
            parseable_json=True,
            native_tool_calls=False,
        ),
    )
    assert report.verdict == ProfileVerdict.PASS


def test_undersized_model_is_incompatible():
    profile = get_reference_profile("ordinary-8k")
    report = assess_reference_profile(
        profile,
        ModelCapabilityDeclaration(
            model_id="small-model",
            context_window_tokens=4096,
            instruction_following=True,
            parseable_json=True,
            native_tool_calls=False,
        ),
    )
    assert report.verdict == ProfileVerdict.INCOMPATIBLE
    assert any(reason.startswith("context_window_too_small") for reason in report.incompatible_reasons)


def test_unknown_context_is_cannot_check():
    profile = get_reference_profile("ordinary-8k")
    report = assess_reference_profile(
        profile,
        ModelCapabilityDeclaration(
            model_id="unknown-model",
            context_window_tokens=None,
            instruction_following=True,
            parseable_json=True,
            native_tool_calls=False,
        ),
    )
    assert report.verdict == ProfileVerdict.CANNOT_CHECK
    assert "context_window_tokens" in report.unknown_requirements


def test_agentic_profile_requires_native_tool_calls():
    profile = get_reference_profile("agentic-32k")
    report = assess_reference_profile(
        profile,
        ModelCapabilityDeclaration(
            model_id="no-tools",
            context_window_tokens=32768,
            instruction_following=True,
            parseable_json=True,
            native_tool_calls=False,
        ),
    )
    assert report.verdict == ProfileVerdict.INCOMPATIBLE
    assert "native_tool_calls_required" in report.incompatible_reasons


def test_unknown_profile_rejected():
    with pytest.raises(KeyError):
        get_reference_profile("imaginary-profile")
