from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProfileVerdict(str, Enum):
    PASS = "PASS"
    INCOMPATIBLE = "INCOMPATIBLE"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class LLMReferenceProfile:
    """Capability contract for a model used behind the RAKL runtime.

    Profiles are provider-neutral.  They describe the minimum model-side capability;
    storage, retrieval, tool mediation, evidence governance, and promotion remain the
    responsibility of the RAKL runtime rather than the model.
    """

    profile_id: str
    min_context_tokens: int
    input_budget_tokens: int
    reserved_output_tokens: int
    reserved_protocol_tokens: int
    requires_instruction_following: bool = True
    requires_parseable_json: bool = True
    requires_native_tool_calls: bool = False

    def __post_init__(self) -> None:
        if not self.profile_id:
            raise ValueError("profile_id cannot be empty")
        if self.min_context_tokens <= 0:
            raise ValueError("min_context_tokens must be positive")
        if min(self.input_budget_tokens, self.reserved_output_tokens, self.reserved_protocol_tokens) < 0:
            raise ValueError("profile token budgets cannot be negative")
        total = self.input_budget_tokens + self.reserved_output_tokens + self.reserved_protocol_tokens
        if total > self.min_context_tokens:
            raise ValueError("profile budgets exceed minimum context window")

    def to_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "min_context_tokens": self.min_context_tokens,
            "input_budget_tokens": self.input_budget_tokens,
            "reserved_output_tokens": self.reserved_output_tokens,
            "reserved_protocol_tokens": self.reserved_protocol_tokens,
            "requires_instruction_following": self.requires_instruction_following,
            "requires_parseable_json": self.requires_parseable_json,
            "requires_native_tool_calls": self.requires_native_tool_calls,
        }


@dataclass(frozen=True)
class ModelCapabilityDeclaration:
    model_id: str
    context_window_tokens: int | None
    instruction_following: bool | None
    parseable_json: bool | None
    native_tool_calls: bool | None = None

    def __post_init__(self) -> None:
        if not self.model_id:
            raise ValueError("model_id cannot be empty")
        if self.context_window_tokens is not None and self.context_window_tokens <= 0:
            raise ValueError("context_window_tokens must be positive when declared")


@dataclass(frozen=True)
class ProfileAssessment:
    profile_id: str
    model_id: str
    verdict: ProfileVerdict
    incompatible_reasons: tuple[str, ...]
    unknown_requirements: tuple[str, ...]

    @property
    def compatible(self) -> bool:
        return self.verdict == ProfileVerdict.PASS

    def to_dict(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "model_id": self.model_id,
            "verdict": self.verdict.value,
            "incompatible_reasons": list(self.incompatible_reasons),
            "unknown_requirements": list(self.unknown_requirements),
        }


REFERENCE_PROFILES: dict[str, LLMReferenceProfile] = {
    "ordinary-8k": LLMReferenceProfile(
        profile_id="ordinary-8k",
        min_context_tokens=8192,
        input_budget_tokens=6144,
        reserved_output_tokens=1536,
        reserved_protocol_tokens=512,
        requires_native_tool_calls=False,
    ),
    "standard-32k": LLMReferenceProfile(
        profile_id="standard-32k",
        min_context_tokens=32768,
        input_budget_tokens=24576,
        reserved_output_tokens=6144,
        reserved_protocol_tokens=2048,
        requires_native_tool_calls=False,
    ),
    "agentic-32k": LLMReferenceProfile(
        profile_id="agentic-32k",
        min_context_tokens=32768,
        input_budget_tokens=24576,
        reserved_output_tokens=6144,
        reserved_protocol_tokens=2048,
        requires_native_tool_calls=True,
    ),
}


def get_reference_profile(profile_id: str) -> LLMReferenceProfile:
    try:
        return REFERENCE_PROFILES[profile_id]
    except KeyError as exc:
        raise KeyError(f"unknown RAKL reference profile: {profile_id}") from exc


def assess_reference_profile(
    profile: LLMReferenceProfile,
    capabilities: ModelCapabilityDeclaration,
) -> ProfileAssessment:
    incompatible: list[str] = []
    unknown: list[str] = []

    if capabilities.context_window_tokens is None:
        unknown.append("context_window_tokens")
    elif capabilities.context_window_tokens < profile.min_context_tokens:
        incompatible.append(
            f"context_window_too_small:{capabilities.context_window_tokens}<{profile.min_context_tokens}"
        )

    if profile.requires_instruction_following:
        if capabilities.instruction_following is None:
            unknown.append("instruction_following")
        elif not capabilities.instruction_following:
            incompatible.append("instruction_following_required")

    if profile.requires_parseable_json:
        if capabilities.parseable_json is None:
            unknown.append("parseable_json")
        elif not capabilities.parseable_json:
            incompatible.append("parseable_json_required")

    if profile.requires_native_tool_calls:
        if capabilities.native_tool_calls is None:
            unknown.append("native_tool_calls")
        elif not capabilities.native_tool_calls:
            incompatible.append("native_tool_calls_required")

    if incompatible:
        verdict = ProfileVerdict.INCOMPATIBLE
    elif unknown:
        verdict = ProfileVerdict.CANNOT_CHECK
    else:
        verdict = ProfileVerdict.PASS

    return ProfileAssessment(
        profile_id=profile.profile_id,
        model_id=capabilities.model_id,
        verdict=verdict,
        incompatible_reasons=tuple(sorted(incompatible)),
        unknown_requirements=tuple(sorted(unknown)),
    )
