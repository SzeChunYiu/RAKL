from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
from typing import Any, Iterator, Mapping

from . import meta_history_v3 as _v3
from .meta_history_v3 import *  # noqa: F401,F403


_LEGACY_UPDATE_KEYS = {
    "from",
    "to",
    "previous_state",
    "closed_coordinates",
    "remaining_blockers",
    "reopen_trigger",
    "purpose",
}


def _records(value: Any, parent_key: str | None = None, location: str = "$") -> Iterator[tuple[Mapping[str, Any], str | None, str]]:
    if isinstance(value, Mapping):
        yield value, parent_key, location
        for key, child in value.items():
            yield from _records(child, key, f"{location}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _records(child, parent_key, f"{location}[{index}]")


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
    """Compile immutable meta-fiber history across legacy structured schemas.

    This adapter handles two historically observed serialization differences
    without inferring semantic identity:

    * early ``new_fibers`` records sometimes used ``id`` rather than
      ``fiber_id``; the enclosing declaration field is the identity witness;
    * some child fibers first appeared in ``fiber_updates`` with an explicit
      ``purpose`` rather than ``question``/``problem``.  If no earlier
      definition exists, that exact first-purpose record is a declaration.

    Unknown shapes still fail closed.  Full identifiers are never merged by
    lexical or semantic similarity.
    """
    research_dir = Path(research_dir)
    base = _v3.compile_meta_fiber_history(research_dir)
    events = list(base.events)
    issues = list(base.issues)

    parsed: dict[str, Any] = {}
    for artifact in base.artifacts:
        if artifact.kind not in {"backlog", "reconciliation"}:
            continue
        path = research_dir.parent / artifact.path
        try:
            parsed[artifact.path] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            # The lower layer already records the authoritative fail-closed
            # source/JSON issue.  Do not duplicate it here.
            continue

    defined = {event.canonical_fiber_id for event in events if event.role == FiberEventRole.DEFINITION}
    added_definition_ids: set[str] = set()
    recognized_unclassified: set[tuple[str, str]] = set()

    for source_path, payload in parsed.items():
        sequence = next((a.sequence for a in base.artifacts if a.path == source_path), (9999, 0, 99, source_path))
        for record, parent_key, location in _records(payload):
            raw_id = _v3._v2._fiber(record.get("fiber_id"))
            if raw_id is not None and any(key in record for key in _LEGACY_UPDATE_KEYS):
                recognized_unclassified.add((source_path, raw_id))

            # Legacy declaration schema: {"new_fibers": [{"id": ...}]}.
            legacy_id = _v3._v2._fiber(record.get("id")) if parent_key == "new_fibers" else None
            if legacy_id is not None and legacy_id not in defined:
                state = _v3._v2._state(record)
                question = _v3._v2._question(record)
                events.append(
                    HistoricalFiberEvent(
                        source_path=source_path,
                        sequence=sequence,
                        role=FiberEventRole.DEFINITION,
                        raw_fiber_id=legacy_id,
                        canonical_fiber_id=legacy_id,
                        question=question,
                        state=state,
                        location=f"{location}.id",
                    )
                )
                defined.add(legacy_id)
                added_definition_ids.add(legacy_id)

            # Legacy child schema: first explicit purpose can carry the missing
            # declaration, but only when the same full id has no prior definition.
            if raw_id is not None and raw_id not in defined:
                purpose = record.get("purpose")
                if isinstance(purpose, str) and purpose.strip():
                    matching = [
                        event
                        for event in events
                        if event.source_path == source_path
                        and event.raw_fiber_id == raw_id
                        and event.role == FiberEventRole.UPDATE
                    ]
                    canonical_id = matching[0].canonical_fiber_id if matching else raw_id
                    events.append(
                        HistoricalFiberEvent(
                            source_path=source_path,
                            sequence=sequence,
                            role=FiberEventRole.DEFINITION,
                            raw_fiber_id=raw_id,
                            canonical_fiber_id=canonical_id,
                            question=purpose.strip(),
                            state=_v3._v2._state(record),
                            location=f"{location}.fiber_id:legacy-purpose-declaration",
                        )
                    )
                    defined.add(canonical_id)
                    added_definition_ids.add(canonical_id)

    # Remove only lower-layer diagnostics that the explicit legacy schema rules
    # above now classify.  All unrelated unknown records remain fail-closed.
    filtered: list[HistoricalLedgerIssue] = []
    for issue in issues:
        if (
            issue.kind == HistoricalIssueKind.UNCLASSIFIED_FIBER_RECORD
            and issue.source_path is not None
            and issue.fiber_id is not None
            and (issue.source_path, issue.fiber_id) in recognized_unclassified
        ):
            continue
        if (
            issue.kind in {HistoricalIssueKind.ORPHAN_REFERENCE, HistoricalIssueKind.RECONCILIATION_TARGET_ORPHAN}
            and issue.fiber_id in added_definition_ids
        ):
            continue
        if issue.kind == HistoricalIssueKind.CANONICAL_SLOT_COLLISION:
            # Recomputed below after all recovered declarations are present.
            continue
        filtered.append(issue)
    issues = filtered

    # Recompute canonical-slot collisions after schema recovery.
    by_slot: dict[int, set[str]] = {}
    for event in events:
        if event.role != FiberEventRole.DEFINITION:
            continue
        match = _v3._v2._NUMERIC.fullmatch(event.canonical_fiber_id)
        if match:
            by_slot.setdefault(int(match.group("slot")), set()).add(event.canonical_fiber_id)
    for slot, ids in sorted(by_slot.items()):
        if len(ids) > 1:
            issues.append(
                HistoricalLedgerIssue(
                    HistoricalIssueKind.CANONICAL_SLOT_COLLISION,
                    f"Canonical slot {slot} remains multiply allocated: {', '.join(sorted(ids))}",
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
        canonical_fibers=_v3._v2._canonical_states(event_tuple),
        ledger_digest=_v3._v2._digest(base.artifacts, event_tuple, base.reallocations, issue_tuple),
    )
