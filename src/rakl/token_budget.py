from __future__ import annotations

import hashlib
import json
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Mapping

from .reference_profile import LLMReferenceProfile


TOKEN_COUNTER_PROTOCOL = "rakl-token-counter-v1"


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class TokenCountAuthority(str, Enum):
    EXACT_EXECUTED_COUNTER = "EXACT_EXECUTED_COUNTER"
    DECLARED_ESTIMATE = "DECLARED_ESTIMATE"


class TokenCountVerdict(str, Enum):
    COUNTED = "COUNTED"
    CANNOT_CHECK = "CANNOT_CHECK"


class PacketBudgetVerdict(str, Enum):
    WITHIN_BUDGET = "WITHIN_BUDGET"
    OVER_BUDGET = "OVER_BUDGET"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class TokenCounterContract:
    counter_id: str
    counter_revision: str
    argv: tuple[str, ...]
    timeout_seconds: float = 30.0

    def __post_init__(self) -> None:
        if not self.counter_id.strip():
            raise ValueError("counter_id cannot be empty")
        if not self.counter_revision.strip():
            raise ValueError("counter_revision cannot be empty")
        if not self.argv or not self.argv[0]:
            raise ValueError("argv must contain an executable")
        if not Path(self.argv[0]).is_absolute():
            raise ValueError("token-counter executable must be an absolute path")
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")

    @property
    def argv_sha256(self) -> str:
        return _sha256(_canonical_bytes(list(self.argv)))

    def to_dict(self) -> dict[str, object]:
        return {
            "counter_id": self.counter_id,
            "counter_revision": self.counter_revision,
            "argv": list(self.argv),
            "argv_sha256": self.argv_sha256,
            "timeout_seconds": self.timeout_seconds,
            "shell": False,
            "protocol": TOKEN_COUNTER_PROTOCOL,
        }


@dataclass(frozen=True)
class TokenCountCertificate:
    payload_sha256: str
    payload_size_bytes: int
    measured_tokens: int
    counter_id: str
    counter_revision: str
    counter_argv_sha256: str
    authority: TokenCountAuthority = TokenCountAuthority.EXACT_EXECUTED_COUNTER
    authority_scope: str = "ENGINEERING_TOKEN_MEASUREMENT_ONLY"

    def __post_init__(self) -> None:
        if self.measured_tokens < 0:
            raise ValueError("measured_tokens cannot be negative")

    def to_dict(self) -> dict[str, object]:
        return {
            "payload_sha256": self.payload_sha256,
            "payload_size_bytes": self.payload_size_bytes,
            "measured_tokens": self.measured_tokens,
            "counter_id": self.counter_id,
            "counter_revision": self.counter_revision,
            "counter_argv_sha256": self.counter_argv_sha256,
            "authority": self.authority.value,
            "authority_scope": self.authority_scope,
        }


@dataclass(frozen=True)
class TokenCountReport:
    verdict: TokenCountVerdict
    certificate: TokenCountCertificate | None
    reason: str | None
    exit_code: int | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict.value,
            "certificate": None if self.certificate is None else self.certificate.to_dict(),
            "reason": self.reason,
            "exit_code": self.exit_code,
        }


@dataclass(frozen=True)
class PacketBudgetReport:
    verdict: PacketBudgetVerdict
    profile_id: str
    exact_packet_tokens: int | None
    max_input_and_protocol_tokens: int
    certificate: TokenCountCertificate | None
    reason: str | None
    authority_scope: str = "ENGINEERING_CONTEXT_BUDGET_ONLY"

    def to_dict(self) -> dict[str, object]:
        return {
            "verdict": self.verdict.value,
            "profile_id": self.profile_id,
            "exact_packet_tokens": self.exact_packet_tokens,
            "max_input_and_protocol_tokens": self.max_input_and_protocol_tokens,
            "certificate": None if self.certificate is None else self.certificate.to_dict(),
            "reason": self.reason,
            "authority_scope": self.authority_scope,
        }


def count_tokens_exact(payload: bytes, contract: TokenCounterContract) -> TokenCountReport:
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        return TokenCountReport(
            verdict=TokenCountVerdict.CANNOT_CHECK,
            certificate=None,
            reason="payload_not_utf8",
        )

    request = _canonical_bytes(
        {
            "protocol": TOKEN_COUNTER_PROTOCOL,
            "payload_sha256": _sha256(payload),
            "text": text,
        }
    )
    try:
        completed = subprocess.run(
            list(contract.argv),
            input=request,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=contract.timeout_seconds,
            check=False,
            shell=False,
        )
    except subprocess.TimeoutExpired:
        return TokenCountReport(
            verdict=TokenCountVerdict.CANNOT_CHECK,
            certificate=None,
            reason="counter_timeout",
        )
    except OSError:
        return TokenCountReport(
            verdict=TokenCountVerdict.CANNOT_CHECK,
            certificate=None,
            reason="counter_start_failure",
        )

    if completed.returncode != 0:
        return TokenCountReport(
            verdict=TokenCountVerdict.CANNOT_CHECK,
            certificate=None,
            reason="counter_nonzero_exit",
            exit_code=completed.returncode,
        )
    try:
        response = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return TokenCountReport(
            verdict=TokenCountVerdict.CANNOT_CHECK,
            certificate=None,
            reason="counter_malformed_json",
            exit_code=completed.returncode,
        )
    if not isinstance(response, dict):
        return TokenCountReport(
            verdict=TokenCountVerdict.CANNOT_CHECK,
            certificate=None,
            reason="counter_response_not_object",
            exit_code=completed.returncode,
        )
    tokens = response.get("tokens")
    if type(tokens) is not int or tokens < 0:
        return TokenCountReport(
            verdict=TokenCountVerdict.CANNOT_CHECK,
            certificate=None,
            reason="counter_invalid_token_count",
            exit_code=completed.returncode,
        )

    certificate = TokenCountCertificate(
        payload_sha256=_sha256(payload),
        payload_size_bytes=len(payload),
        measured_tokens=tokens,
        counter_id=contract.counter_id,
        counter_revision=contract.counter_revision,
        counter_argv_sha256=contract.argv_sha256,
    )
    return TokenCountReport(
        verdict=TokenCountVerdict.COUNTED,
        certificate=certificate,
        reason=None,
        exit_code=completed.returncode,
    )


def certify_packet_budget(
    packet_bytes: bytes,
    profile: LLMReferenceProfile,
    *,
    counter: TokenCounterContract | None,
) -> PacketBudgetReport:
    limit = profile.input_budget_tokens + profile.reserved_protocol_tokens
    if counter is None:
        return PacketBudgetReport(
            verdict=PacketBudgetVerdict.CANNOT_CHECK,
            profile_id=profile.profile_id,
            exact_packet_tokens=None,
            max_input_and_protocol_tokens=limit,
            certificate=None,
            reason="exact_counter_required_for_strict_certification",
        )
    counted = count_tokens_exact(packet_bytes, counter)
    if counted.verdict != TokenCountVerdict.COUNTED or counted.certificate is None:
        return PacketBudgetReport(
            verdict=PacketBudgetVerdict.CANNOT_CHECK,
            profile_id=profile.profile_id,
            exact_packet_tokens=None,
            max_input_and_protocol_tokens=limit,
            certificate=None,
            reason=counted.reason or "token_counter_failed",
        )
    tokens = counted.certificate.measured_tokens
    return PacketBudgetReport(
        verdict=(
            PacketBudgetVerdict.WITHIN_BUDGET
            if tokens <= limit
            else PacketBudgetVerdict.OVER_BUDGET
        ),
        profile_id=profile.profile_id,
        exact_packet_tokens=tokens,
        max_input_and_protocol_tokens=limit,
        certificate=counted.certificate,
        reason=None if tokens <= limit else "exact_packet_exceeds_profile_input_and_protocol_budget",
    )
