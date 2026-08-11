"""Thin proposal-only alias for issue #130 closeout stub."""

from .issue_closeout_stubs import CloseoutStubReport, StubStatus, freeze_stub

__all__ = ["CloseoutStubReport", "StubStatus", "freeze_stub", "freeze_report"]


def freeze_report(*reasons: str) -> CloseoutStubReport:
    return freeze_stub(130, *reasons)
