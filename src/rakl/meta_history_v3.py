from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from . import meta_history_v2 as _v2
from .meta_history_v2 import *  # noqa: F401,F403


def _verdict(issues, reallocations):
    unresolved = [issue for issue in issues if not issue.resolved]
    if any(issue.kind == HistoricalIssueKind.RECONCILIATION_CHRONOLOGY_INVALID for issue in unresolved):
        return HistoricalLedgerVerdict.TRIAL_INVALID
    if any(
        issue.kind
        in {
            HistoricalIssueKind.INVALID_JSON,
            HistoricalIssueKind.SOURCE_MISSING,
            HistoricalIssueKind.SOURCE_BLOB_MISMATCH,
            HistoricalIssueKind.UNCLASSIFIED_FIBER_RECORD,
            HistoricalIssueKind.RECONCILIATION_SCOPE_UNVERIFIABLE,
        }
        for issue in unresolved
    ):
        return HistoricalLedgerVerdict.CANNOT_CHECK
    if unresolved:
        return HistoricalLedgerVerdict.CONFLICTED
    if reallocations or any(issue.resolved for issue in issues):
        return HistoricalLedgerVerdict.CONSISTENT_WITH_RECONCILIATION_HISTORY
    return HistoricalLedgerVerdict.CONSISTENT


def compile_meta_fiber_history(research_dir: Path) -> HistoricalMetaLedgerReport:
    """Compile history while recovering legacy declarations embedded in updates.

    Early immutable backlog deltas sometimes introduced a new fiber under the
    key ``updates`` and marked it NEW_*. Later deltas also occasionally recorded
    an already-implemented first appearance with a full ``problem`` field. If a
    canonical id otherwise has no definition, the earliest update carrying a
    problem/question is treated as its declaration. This is a structural
    recovery rule, not semantic identity inference.
    """
    base = _v2.compile_meta_fiber_history(Path(research_dir))
    events = list(base.events)
    defined = {event.canonical_fiber_id for event in events if event.role == FiberEventRole.DEFINITION}

    promoted_ids: set[str] = set()
    by_id: dict[str, list[tuple[int, HistoricalFiberEvent]]] = {}
    for index, event in enumerate(events):
        if event.role == FiberEventRole.UPDATE and event.question:
            by_id.setdefault(event.canonical_fiber_id, []).append((index, event))
    for fiber_id, candidates in by_id.items():
        if fiber_id in defined:
            continue
        index, event = min(candidates, key=lambda pair: (pair[1].sequence, pair[1].source_path, pair[1].location))
        events[index] = replace(event, role=FiberEventRole.DEFINITION)
        promoted_ids.add(fiber_id)
        defined.add(fiber_id)

    issues = [
        issue
        for issue in base.issues
        if not (
            issue.kind in {HistoricalIssueKind.ORPHAN_REFERENCE, HistoricalIssueKind.RECONCILIATION_TARGET_ORPHAN}
            and issue.fiber_id in promoted_ids
        )
    ]

    # Promotion can expose a collision that the v2 pass could not see because
    # the record was historically encoded as an update. Recheck those slots.
    promoted_slots = {
        int(_v2._NUMERIC.fullmatch(fiber_id).group("slot"))
        for fiber_id in promoted_ids
        if _v2._NUMERIC.fullmatch(fiber_id)
    }
    for slot in sorted(promoted_slots):
        canonical_ids = {
            event.canonical_fiber_id
            for event in events
            if event.role == FiberEventRole.DEFINITION
            and _v2._NUMERIC.fullmatch(event.canonical_fiber_id)
            and int(_v2._NUMERIC.fullmatch(event.canonical_fiber_id).group("slot")) == slot
        }
        if len(canonical_ids) > 1 and not any(
            issue.kind == HistoricalIssueKind.CANONICAL_SLOT_COLLISION
            and f"slot {slot} " in issue.message
            for issue in issues
        ):
            issues.append(
                HistoricalLedgerIssue(
                    HistoricalIssueKind.CANONICAL_SLOT_COLLISION,
                    f"Canonical slot {slot} remains multiply allocated: {', '.join(sorted(canonical_ids))}",
                )
            )

    for fiber_id in promoted_ids:
        questions = {
            " ".join(event.question.split())
            for event in events
            if event.role == FiberEventRole.DEFINITION
            and event.canonical_fiber_id == fiber_id
            and event.question
        }
        if len(questions) > 1:
            issues.append(
                HistoricalLedgerIssue(
                    HistoricalIssueKind.DEFINITION_CONFLICT,
                    f"Multiple distinct question/problem definitions found for {fiber_id}",
                    fiber_id=fiber_id,
                )
            )

    event_tuple = tuple(sorted(events, key=lambda e: (e.sequence, e.source_path, e.location, e.role.value, e.raw_fiber_id)))
    issue_tuple = tuple(sorted(issues, key=lambda i: (i.kind.value, i.source_path or "", i.fiber_id or "", i.message)))
    return HistoricalMetaLedgerReport(
        verdict=_verdict(issue_tuple, base.reallocations),
        artifacts=base.artifacts,
        events=event_tuple,
        reallocations=base.reallocations,
        issues=issue_tuple,
        canonical_fibers=_v2._canonical_states(event_tuple),
        ledger_digest=_v2._digest(base.artifacts, event_tuple, base.reallocations, issue_tuple),
    )
