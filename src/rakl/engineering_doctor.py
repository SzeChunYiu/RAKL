"""Typed operator diagnostics for the engineering reference substrate."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Tuple


class DiagnosticSeverity(str, Enum):
    INFO = "INFO"
    RETRY = "RETRY"
    RECOVERY = "RECOVERY"
    INTEGRITY = "INTEGRITY"
    CAPACITY = "CAPACITY"
    CANNOT_CHECK = "CANNOT_CHECK"


@dataclass(frozen=True)
class DiagnosticIssue:
    code: str
    severity: DiagnosticSeverity
    detail: str


@dataclass(frozen=True)
class EngineeringDoctorReport:
    healthy: bool
    issues: Tuple[DiagnosticIssue, ...]

    @property
    def requires_manual_recovery(self) -> bool:
        return any(item.severity is DiagnosticSeverity.RECOVERY for item in self.issues)


def classify_transition_status(status: object, reason: str = "") -> DiagnosticIssue | None:
    value = str(getattr(status, "value", status))
    if value == "COMMITTED":
        return None
    if value == "RETRY_REQUIRED":
        return DiagnosticIssue("transition_retry_required", DiagnosticSeverity.RETRY, reason)
    if value == "RECOVERY_REQUIRED":
        return DiagnosticIssue("transition_recovery_required", DiagnosticSeverity.RECOVERY, reason)
    if value == "CANNOT_CHECK":
        return DiagnosticIssue("transition_cannot_check", DiagnosticSeverity.CANNOT_CHECK, reason)
    if value == "ABORTED":
        return DiagnosticIssue("transition_aborted", DiagnosticSeverity.INFO, reason)
    return DiagnosticIssue("transition_unknown_status", DiagnosticSeverity.CANNOT_CHECK, value)


def build_doctor_report(issues: Iterable[DiagnosticIssue]) -> EngineeringDoctorReport:
    unique: list[DiagnosticIssue] = []
    seen: set[tuple[str, str, str]] = set()
    for item in issues:
        key = (item.code, item.severity.value, item.detail)
        if key not in seen:
            seen.add(key)
            unique.append(item)
    blocking = {DiagnosticSeverity.RECOVERY, DiagnosticSeverity.INTEGRITY, DiagnosticSeverity.CANNOT_CHECK}
    return EngineeringDoctorReport(
        healthy=not any(item.severity in blocking for item in unique),
        issues=tuple(unique),
    )
